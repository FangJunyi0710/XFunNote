import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { listNotebooks, queryEntries } from '@/api/notebooks';
import type { NotebookSchema, NotebookType } from '@/types/notebook';

const NOTEBOOK_ROUTES: Record<string, { path: string; icon: string; label: string }> = {
  plan: { path: '/notebooks/plan', icon: '📋', label: '计划' },
  diary: { path: '/notebooks/diary', icon: '📝', label: '日记' },
  word: { path: '/notebooks/word', icon: '📖', label: '单词' },
  accumulation: { path: '/notebooks/accumulation', icon: '📚', label: '积累' },
  aimemory: { path: '/notebooks/aimemory', icon: '🧠', label: 'AI 记忆' },
};

export const Home: React.FC = () => {
  const [notebooks, setNotebooks] = useState<(NotebookSchema & { count?: number })[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const schemas = await listNotebooks();
        const withCounts = await Promise.all(
          schemas.map(async (s) => {
            try {
              const res = await queryEntries(s.table_name as NotebookType, {
                page_size: 1,
              });
              return { ...s, count: res.total };
            } catch {
              return { ...s, count: 0 };
            }
          }),
        );
        setNotebooks(withCounts);
      } catch (e) {
        console.error('加载首页失败', e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 标题 */}
      <div>
        <h1 className="text-2xl font-bold">XFunNote</h1>
        <p className="text-muted-foreground text-sm mt-1">小方的万用本 — 个人数据与 AI 操作系统</p>
      </div>

      {/* 快捷入口 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { to: '/ai', icon: '🤖', label: 'AI 对话', desc: '与 AI 智能助手交流' },
          { to: '/views', icon: '👁️', label: '视图管理', desc: '管理自定义视图' },
          { to: '/management', icon: '⚙️', label: '数据库管理', desc: '初始化、备份、重置' },
        ].map((item) => (
          <Link key={item.to} to={item.to}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
              <CardContent className="p-4 flex items-center gap-3">
                <span className="text-2xl">{item.icon}</span>
                <div>
                  <div className="font-medium text-sm">{item.label}</div>
                  <div className="text-xs text-muted-foreground">{item.desc}</div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* 笔记本概览 */}
      <div>
        <h2 className="text-lg font-semibold mb-3">笔记本概览</h2>
        {loading ? (
          <div className="text-sm text-muted-foreground">加载中...</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {notebooks.map((nb) => {
              const route = NOTEBOOK_ROUTES[nb.table_name];
              if (!route) return null;
              return (
                <Link key={nb.table_name} to={route.path}>
                  <Card className="hover:shadow-md transition-shadow cursor-pointer">
                    <CardHeader className="p-4 pb-2">
                      <CardTitle className="text-base flex items-center gap-2">
                        <span>{route.icon}</span>
                        <span>{route.label}</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                        {nb.description}
                      </p>
                      <div className="text-sm font-medium">
                        {nb.count !== undefined ? `${nb.count} 条` : '-'}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
