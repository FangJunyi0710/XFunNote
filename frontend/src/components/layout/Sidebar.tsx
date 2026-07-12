import React from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

const mainNav: NavItem[] = [
  { label: '首页', path: '/', icon: '🏠' },
  { label: '计划', path: '/notebooks/plan', icon: '📋' },
  { label: '日记', path: '/notebooks/diary', icon: '📝' },
  { label: '单词', path: '/notebooks/word', icon: '📖' },
  { label: '积累', path: '/notebooks/accumulation', icon: '📚' },
  { label: 'AI 记忆', path: '/notebooks/aimemory', icon: '🧠' },
  { label: 'AI 对话', path: '/ai', icon: '🤖' },
  { label: '管理', path: '/management', icon: '⚙️' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-56 h-screen border-r bg-card flex flex-col shrink-0">
      {/* 标题 */}
      <div className="h-14 flex items-center px-5 border-b">
        <span className="text-lg font-bold tracking-tight">XFunNote</span>
      </div>

      {/* 导航 */}
      <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
        {mainNav.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-foreground/70 hover:bg-accent hover:text-accent-foreground',
              )
            }
          >
            <span className="text-base">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* 底部版本 */}
      <div className="px-5 py-3 border-t text-xs text-muted-foreground">
        v0.1.0
      </div>
    </aside>
  );
};
