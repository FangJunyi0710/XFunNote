import fs from 'fs';
import { type ServerOptions, ViteDevServer, defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import http from 'http';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';

// 获取当前文件所在目录，并定位到项目根目录（与 frontend/ 同级）
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootPath = path.resolve(__dirname, '../');

// 加载 .env 文件（若文件不存在则忽略）
dotenv.config({ path: path.join(rootPath, '.env') });

// 从环境变量读取，提供默认值
export const VITE_HTTPS_PORT = parseInt(process.env.VITE_HTTPS_PORT || '443', 10);
export const VITE_HTTP_PORT = parseInt(process.env.VITE_HTTP_PORT || '80', 10);
export const VITE_HOST = process.env.VITE_HOST || 'localhost';
export const BACKEND_PORT = parseInt(process.env.BACKEND_PORT || '8000', 10);

/**
 * 加载 HTTPS 证书配置
 * 优先使用环境变量 SSL_CERT_PATH / SSL_KEY_PATH（相对项目根目录）
 * 若未设置则回退到 frontend/certs/ 目录下的 cert.pem / key.pem
 */
function loadHttpsConfig(): ServerOptions['https'] {
  const certPathEnv = process.env.SSL_CERT_PATH;
  const keyPathEnv = process.env.SSL_KEY_PATH;

  let certPath: string;
  let keyPath: string;

  if (certPathEnv && keyPathEnv) {
    certPath = path.resolve(rootPath, certPathEnv);
    keyPath = path.resolve(rootPath, keyPathEnv);
    console.log(`[vite] 使用环境变量指定的证书路径: ${certPath} 和 ${keyPath}`);
    if (fs.existsSync(certPath) && fs.existsSync(keyPath)) {
      console.log(`[vite] 检测到证书文件，启用 HTTPS`);
      return {
        key: fs.readFileSync(keyPath),
        cert: fs.readFileSync(certPath),
      };
    }
  }

  console.warn('[vite] 未找到证书文件，回退到 HTTP 模式');
  return undefined;
}

// 加载证书配置，同时记录是否启用 HTTPS
const httpsConfig = loadHttpsConfig();
const isHttps = !!httpsConfig;

// 自定义插件：仅在 HTTPS 模式下启动 HTTP → HTTPS 重定向服务
const redirectPlugin = isHttps
  ? {
      name: 'redirect-server',
      configureServer(server: ViteDevServer) {
        const redirectPort = VITE_HTTP_PORT;
        const httpsPort = VITE_HTTPS_PORT;
        const httpsHost = VITE_HOST;

        const redirectServer = http.createServer((req, res) => {
          const httpsUrl = `https://${httpsHost}:${httpsPort}${req.url}`;
          res.writeHead(301, { Location: httpsUrl, Connection: 'close' });
          res.end();
        });

        redirectServer.listen(redirectPort, '0.0.0.0', () => {
          console.log(
            `[redirect] HTTP 重定向服务启动于 http://0.0.0.0:${redirectPort} -> https://${httpsHost}:${httpsPort}`
          );
        });

        const closeServer = (serverInstance: { close: (cb: (err?: Error) => void) => void } | null) =>
          new Promise<string>((resolve, reject) => {
            if (!serverInstance) {
              resolve('no server');
              return;
            }
            serverInstance.close((err?: Error) => {
              if (err) reject(err);
              else resolve('closed');
            });
          });

        const shutdown = async () => {
          console.log('[vite] 收到关闭信号，正在关闭...');
          try {
            await Promise.all([
              closeServer(server.httpServer),
              closeServer(redirectServer),
            ]);
            console.log('[vite] 所有服务器已关闭');
            process.exit(0);
          } catch (err) {
            console.error('[vite] 关闭服务器时出错:', err);
            process.exit(1);
          }
        };

        process.once('SIGINT', shutdown);
        process.once('SIGTERM', shutdown);

        if (server.httpServer) {
          server.httpServer.once('close', () => {
            console.log('[vite] Vite 服务器已关闭');
          });
          redirectServer.once('close', () => {
            console.log('[redirect] HTTP 重定向服务已关闭');
          });
        }
      },
    }
  : null;

export default defineConfig({
  plugins: [
    react(),
    ...(redirectPlugin ? [redirectPlugin] : []),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: isHttps ? VITE_HTTPS_PORT : VITE_HTTP_PORT,
    https: httpsConfig,
    allowedHosts: ['localhost', '127.0.0.1', '::1', VITE_HOST],
    proxy: {
      '/api': {
        target: `http://localhost:${BACKEND_PORT}`,
        changeOrigin: true,
      },
    },
  },
});