import React from 'react';
import ReactDOM from 'react-dom/client';
import App from '@/App';
import ErrorBoundary from '@/components/ui/ErrorBoundary';
import { useTokenStore } from '@/stores/tokenStore';
import '@/index.css';

// 本地模式（Android JS 桥）：用桥暴露的 bootstrap root token 自动完成本地登录。
// Web（无桥）不受影响，仍走手动输入 token 流程。
const bootstrapLocalAuth = () => {
  const bridge = (window as unknown as { XFunBridge?: { getBootstrapToken?: () => string } }).XFunBridge;
  if (!bridge?.getBootstrapToken) return;
  const token = bridge.getBootstrapToken();
  if (!token) return;

  const user = 'default';
  let s = useTokenStore.getState();
  s.addUser(user);
  s.setActiveUser(user);

  s = useTokenStore.getState();
  const existing = s.getCurrentUserTokens().find((t) => t.key === token);
  if (existing) {
    s.setActiveToken(existing.id);
  } else {
    const id = s.addToken(token);
    if (id) s.setActiveToken(id);
  }
};
bootstrapLocalAuth();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
