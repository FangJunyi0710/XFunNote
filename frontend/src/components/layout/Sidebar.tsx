import React from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useThemeStore } from '@/stores/themeStore';

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
  const { mode, resolved, setMode, toggle } = useThemeStore();

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
