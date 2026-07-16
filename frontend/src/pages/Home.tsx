import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { listNotebooks } from '@/api/notebooks';
import { useTokenStore } from '@/stores/tokenStore';
import { NOTEBOOK_ROUTES, getNotebookStyles } from '@/config/notebook';
import type { NotebookType } from '@/config/notebook';
import { handleError } from '@/lib/error';
import type { NotebookSchema } from '@/types/notebook';

export const Home: React.FC = () => {
  const [notebooks, setNotebooks] = useState<NotebookSchema[]>([]);
  const [loading, setLoading] = useState(true);

  // 从 zustand store 读取 API-Key 状态
  const hasActiveKey = useTokenStore((s) => !!s.activeTokenId && s.tokens.some((t) => t.id === s.activeTokenId));

  useEffect(() => {
    (async () => {
      try {
        const schemas = await listNotebooks();
        setNotebooks(schemas);
      } catch (e: unknown) {
        handleError(e, '加载首页失败');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const visibleNotebooks = notebooks.filter((nb) => NOTEBOOK_ROUTES[nb.table_name]);

  return (
    <div className="space-y-8 animate-fade-in">
      {/* 标题区 */}
      <div className="border-b pb-4">
        <h1 className="text-3xl font-bold tracking-tight">XFunNote</h1>
        <p className="text-muted-foreground text-sm mt-1">小方的万用本 — 个人数据与 AI 操作系统</p>
      </div>

      {/* API-Key 状态提示 — 未配置时才显示 */}
      {!hasActiveKey && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg border text-sm bg-warning/10 border-warning/30 text-warning">
          <span className="text-lg">⚠️</span>
          <div className="flex-1 min-w-0">
            <span>
              未配置 API Key —{' '}
              <Link to="/token-input" className="underline underline-offset-2 hover:text-primary">
                前往设置
              </Link>
            </span>
          </div>
        </div>
      )}

      {/* 笔记本概览 */}
      <section>
        <h2 className="text-lg font-semibold mb-3">笔记本概览</h2>
        {loading ? (
          <p className="text-sm text-muted-foreground">加载中...</p>
        ) : visibleNotebooks.length === 0 ? (
          <Card className="p-6 text-center">
            <p className="text-muted-foreground text-sm">暂无笔记本数据</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {visibleNotebooks.map((nb) => {
              const route = NOTEBOOK_ROUTES[nb.table_name];
              const styles = getNotebookStyles(nb.table_name as NotebookType);
              return (
                <Link key={nb.table_name} to={route.path}>
                  <Card className={`hover:shadow-lg hover:border-primary/30 transition-all cursor-pointer h-full group border-l-2 ${styles.border}`}>
                    <CardHeader className="p-5 pb-2">
                      <CardTitle className="text-base flex items-center gap-2">
                        <span className="text-xl group-hover:scale-110 transition-transform">{route.icon}</span>
                        <span>{route.label}</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-5 pt-2">
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {nb.description}
                      </p>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
};
