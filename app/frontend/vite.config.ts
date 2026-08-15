import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';
import fs from 'fs';

const CDN_HOST = 'https://cdn-tos.bytedance.net/aime/apps/cdn';
const CDN_STATIC_EXTENSIONS = new Set([
  '.js',
  '.mjs',
  '.cjs',
  '.css',
  '.map',
  '.json',
  '.txt',
  '.wasm',
  '.png',
  '.jpg',
  '.jpeg',
  '.gif',
  '.webp',
  '.avif',
  '.svg',
  '.ico',
  '.bmp',
  '.cur',
  '.woff',
  '.woff2',
  '.ttf',
  '.otf',
  '.eot',
  '.mp3',
  '.mp4',
  '.webm',
  '.ogg',
  '.wav',
]);

// vite.config.ts 位于 app/frontend/，仓库根是它的上上层
const REPO_ROOT = path.resolve(__dirname, '../..');
// Vite 的 outDir 相对 frontend 是 '../dist'，映射到仓库根就是 'app/dist'。
// renderBuiltUrl 传入的 filename 是相对 outDir 的路径；比较 upload_to_cdn 时要先
// 转成相对 app.json 所在目录的路径：app/dist/<filename>。
const DIST_REPO_PREFIX = 'app/dist';
const CDN_BUILD_RECORD_REL_PATH = 'app/data/cdn_build_record.json';

interface AppJsonService {
  upload_to_cdn?: string[];
}

interface AppJson {
  id?: string;
  services?: AppJsonService[];
}

function loadAppJson(): AppJson {
  const p = path.resolve(REPO_ROOT, 'app.json');
  if (!fs.existsSync(p)) return {};
  try {
    return JSON.parse(fs.readFileSync(p, 'utf-8')) as AppJson;
  } catch {
    return {};
  }
}

// 从 app.json 收集 CDN 化的路径规则，返回相对 app.json 所在目录的前缀数组。
// 不限制必须是 app/dist；upload_to_cdn 配了什么就按什么前缀匹配。
function collectCdnPrefixes(app: AppJson): string[] {
  const raw = (app.services ?? []).flatMap((s) => s.upload_to_cdn ?? []);
  const cleaned: string[] = [];
  for (const item of raw) {
    if (typeof item !== 'string') continue;
    const normalized = item.trim().replace(/^\.\/+/, '').replace(/\/+$/, '');
    if (!normalized) continue;
    cleaned.push(normalized);
  }
  return cleaned;
}

const APP_JSON = loadAppJson();
const APP_ID = APP_JSON.id ?? '';
const CDN_PREFIXES = collectCdnPrefixes(APP_JSON);

function shouldCdn(filename: string): boolean {
  // filename 是相对 dist 的产物路径，如 'assets/index-xxx.js'
  if (!APP_ID) return false; // 没有 app_id 不做重写，避免生成半吊子 URL
  if (!CDN_STATIC_EXTENSIONS.has(path.extname(filename).toLowerCase())) return false;
  const repoRelativePath = `${DIST_REPO_PREFIX}/${filename}`;
  return CDN_PREFIXES.some(
    (prefix) => repoRelativePath === prefix || repoRelativePath.startsWith(prefix + '/')
  );
}

function buildCdnUrl(filename: string): string {
  // Vite 当前产物的仓库相对路径 = app/dist/<filename>
  return `${CDN_HOST}/${APP_ID}/${DIST_REPO_PREFIX}/${filename}`;
}

function writeCdnBuildRecord(mode: string): void {
  const recordPath = path.resolve(REPO_ROOT, CDN_BUILD_RECORD_REL_PATH);
  try {
    fs.mkdirSync(path.dirname(recordPath), { recursive: true });
    fs.writeFileSync(recordPath, JSON.stringify({ mode }, null, 2) + '\n', 'utf-8');
  } catch (err) {
    console.warn('[aime] write cdn_build_record failed:', err);
  }
}

function aimeInspectorBabelPlugin(): any {
  return {
    name: 'aime-inspector',
    visitor: {
      JSXOpeningElement(nodePath: any, state: any) {
        const filename = state.filename || '';
        if (!filename || filename.includes('node_modules')) return;
        const node = nodePath.node;
        if (!node.loc) return;
        const relative = path.relative(__dirname, filename).replace(/\\/g, '/');
        if (relative.startsWith('..') || relative.includes('node_modules')) return;
        const { line, column } = node.loc.start;
        const nameNode = node.name;
        let componentName = '';
        if (nameNode.type === 'JSXIdentifier') {
          componentName = nameNode.name;
        } else if (nameNode.type === 'JSXMemberExpression') {
          componentName = `${nameNode.object?.name || ''}.${nameNode.property?.name || ''}`;
        }
        const makeAttr = (name: string, value: string) => ({
          type: 'JSXAttribute',
          name: { type: 'JSXIdentifier', name },
          value: { type: 'StringLiteral', value },
        });
        node.attributes.push(
          makeAttr('data-aime-path-name', relative),
          makeAttr('data-aime-line', String(line)),
          makeAttr('data-aime-column', String(column)),
          makeAttr('data-aime-component-name', componentName),
        );
      },
    },
  };
}

export default defineConfig(({ mode }) => {
  // 只有显式传入 --mode cdn 才启用 CDN URL 改写；其它模式（默认 production / development）
  // 一律走相对路径，由 Flask 直发 dist，避免"资源没上传就把 URL 改成 CDN 绝对地址"。
  const cdnEnabled = mode === 'cdn';
  // 容器开发进程由 Dev Agent 注入真实 Runtime Service 地址；正式构建和普通本地
  // 开发仍保持模板默认端口。不要把容器端口写进业务源码。
  const serviceTarget =
    process.env.AIME_DEV_SERVICE_URL ?? 'http://127.0.0.1:3000';
  const devAllowedHosts = [
    ...(process.env.AIME_DEV_ALLOWED_HOSTS ?? '')
      .split(',')
      .map((host) => host.trim())
      .filter(Boolean),
    '.codeagent.svc.cluster.local',
  ];
  return {
    plugins: [
      react({ babel: { plugins: [aimeInspectorBabelPlugin] } }),
      tailwindcss(),
      {
        name: 'aime-cdn-build-record',
        apply: 'build',
        closeBundle() {
          writeCdnBuildRecord(cdnEnabled ? 'cdn' : 'production');
          if (!cdnEnabled && CDN_PREFIXES.length > 0) {
            console.warn(
              '[aime] app.json 配置了 upload_to_cdn，但当前执行的是普通前端构建。' +
              '如需保留 CDN 构建、上传和降级逻辑，请通过 app/utils/cdn_build.py 触发构建，' +
              '不要直接 pnpm run build 覆盖 CDN 产物。'
            );
          }
        },
      },
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@components': path.resolve(__dirname, 'src/components'),
        '@styles': path.resolve(__dirname, 'src/styles'),
      },
    },
    css: {
      preprocessorOptions: {
        less: {
          javascriptEnabled: true,
        },
      },
    },
    server: {
      port: 5173,
      allowedHosts: devAllowedHosts,
      proxy: {
        '/api': {
          target: serviceTarget,
          changeOrigin: true,
        },
      },
    },
    // 仅在 CDN 模式下改写 URL；其它模式使用 Vite/Rollup 默认（相对路径），
    // 避免开发者手工 build 时误把 URL 指向未上传的 CDN 资源。
    experimental: cdnEnabled
      ? {
          renderBuiltUrl(filename) {
            if (shouldCdn(filename)) {
              return buildCdnUrl(filename);
            }
            return { relative: true };
          },
        }
      : undefined,
    build: {
      outDir: '../dist',
      emptyOutDir: true,
      // 仅拆分被「应用外壳 + 几乎所有页面」共用的低频 vendor，提升缓存命中率。
      // 重型库（react-markdown / katex 全家桶等）只被各自懒加载的组件/页面引用，
      // 交给 React.lazy 的自动分包即可进入对应异步 chunk，不进入首屏，
      // 不要在此手动建独立 chunk —— 那会被 Vite 提升为入口 modulepreload，反而拉进首屏。
      rollupOptions: {
        output: {
          entryFileNames: 'assets/[name]-[hash:16].js',
          chunkFileNames: 'assets/[name]-[hash:16].js',
          assetFileNames: 'assets/[name]-[hash:16][extname]',
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            arco: ['@arco-design/web-react'],
          },
        },
      },
    },
  };
});
