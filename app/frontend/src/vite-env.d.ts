/// <reference types="vite/client" />

// CSS / LESS Module 类型声明：scoped 类名会被打包器映射为字符串字典。
// 缺少此声明时，`import styles from './x.module.less'` 会被 tsc 报
// TS2307 "Cannot find module ... or its corresponding type declarations"。
declare module '*.module.less' {
  const classes: { readonly [key: string]: string };
  export default classes;
}

declare module '*.module.css' {
  const classes: { readonly [key: string]: string };
  export default classes;
}

// 普通样式文件按副作用导入（无默认导出）
declare module '*.less';
declare module '*.css';
