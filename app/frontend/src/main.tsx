import ReactDOM from 'react-dom/client';
import App from './App';
import { prefetchJwt } from './auth';
import './aime-element-picker';
import { initPageControl } from './page-control-runtime';
import './components/aime-message';
import '@arco-design/web-react/dist/css/arco.css';
import './styles/global.css';
import './styles/tailwind.css';

// 启动即预热鉴权链路，使鉴权 chunk 的下载与 React 启动并行。
prefetchJwt();

// 页面运行在 AIME Canvas iframe 中时，建立 page-control WebSocket 长链。
initPageControl();

const rootEl = document.getElementById('root');
if (rootEl) {
  const root = ReactDOM.createRoot(rootEl);
  root.render(<App />);
}
