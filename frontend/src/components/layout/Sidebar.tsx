import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useThemeStore } from '@/stores/themeStore';

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

const topNav: NavItem[] = [{ label: '首页', path: '/', icon: '🏠' }];

const notebookNav: NavItem[] = [
  { label: '计划', path: '/notebooks/plan', icon: '📋' },
  { label: '日记', path: '/notebooks/diary', icon: '📝' },
  { label: '单词', path: '/notebooks/word', icon: '📖' },
  { label: '积累', path: '/notebooks/accumulation', icon: '📚' },
  { label: 'AI 记忆', path: '/notebooks/aimemory', icon: '🧠' },
  { label: '时间线', path: '/notebooks/timeline', icon: '📅' },
  { label: '日程', path: '/notebooks/schedule', icon: '📋' },
];

const bottomNav: NavItem[] = [
  { label: 'AI 对话', path: '/ai', icon: '🤖' },
  { label: '管理', path: '/management', icon: '⚙️' },
  { label: 'Token 管理', path: '/token-input', icon: '🔑' },
];

export const Sidebar: React.FC = () => {
  const { mode, resolved, setMode, toggle } = useThemeStore();
  const [notebookOpen, setNotebookOpen] = useState(true);

  return (
    <aside className="w-56 h-screen border-r bg-card flex flex-col shrink-0">
      {/* 标题 */}
      <div className="h-14 flex items-center px-5 border-b">
        <button
          onClick={() => {
            const modes: Array<'light' | 'dark' | 'system'> = ['light', 'dark', 'system'];
            const idx = modes.indexOf(mode);
            setMode(modes[(idx + 1) % 3]);
          }}
          className="text-lg font-bold tracking-tight hover:text-primary transition-colors"
          title={`当前: ${mode === 'system' ? '跟随系统' : mode === 'light' ? '浅色' : '深色'}，点击切换`}
        >
          XFunNote
        </button>
      </div>

      {/* 导航 */}
      <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
        {/* 顶部固定项：首页 */}
        {topNav.map((item) => (
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

        {/* 本子分组（可折叠） */}
        <div className="pt-2">
          <button
            onClick={() => setNotebookOpen((v) => !v)}
            className="flex items-center gap-2 w-full px-3 py-2.5 rounded-md text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <span
              className="inline-block transition-transform duration-200 text-xs"
              style={{ transform: notebookOpen ? 'rotate(90deg)' : 'rotate(0deg)' }}
            >
              ▸
            </span>
            笔记本
          </button>

          <div
            className="overflow-hidden transition-all duration-200"
            style={{
              maxHeight: notebookOpen ? notebookNav.length * 40 + 50 : 0,
              opacity: notebookOpen ? 1 : 0,
            }}
          >
            <div className="space-y-0.5 pt-1">
              {notebookNav.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors pl-7',
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
            </div>
          </div>
        </div>

        {/* 底部固定项 */}
        <div className="pt-2 space-y-0.5">
          {bottomNav.map((item) => (
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
        </div>
      </nav>

      {/* 底部版本 + 主题切换 */}
      <div className="px-5 py-3 border-t flex items-center justify-between">
        <span className="text-xs text-muted-foreground">v0.1.0</span>
        <button
          onClick={toggle}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          title={`切换主题（当前: ${resolved === 'dark' ? '深色' : '浅色'}）`}
        >
          {resolved === 'dark' ? '☀️ 浅色' : '🌙 深色'}
        </button>
      </div>
    </aside>
  );
};
