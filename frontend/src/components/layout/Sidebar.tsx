import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useThemeStore } from '@/stores/themeStore';
import { useSidebarStore } from '@/stores/sidebarStore';
import { NOTEBOOK_ROUTES } from '@/config/notebook';

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

const topNav: NavItem[] = [{ label: '首页', path: '/', icon: '🏠' }];

const notebookNav: NavItem[] = Object.values(NOTEBOOK_ROUTES).map((route) => ({
  label: route.label,
  path: route.path,
  icon: route.icon,
}));

const bottomNav: NavItem[] = [
  { label: 'AI 对话', path: '/ai', icon: '🤖' },
  { label: '管理', path: '/management', icon: '⚙️' },
  { label: 'Token 管理', path: '/token-input', icon: '🔑' },
];

/** 折叠箭头图标，通过 rotate 实现平滑过渡 */
const ChevronIcon: React.FC<{ collapsed: boolean }> = ({ collapsed }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    className="w-5 h-5 transition-transform duration-200"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ transform: collapsed ? 'rotate(0deg)' : 'rotate(180deg)' }}
  >
    <path d="M15 18l-6-6 6-6" />
  </svg>
);

function navLinkClass(isActive: boolean, extra = '') {
  return cn(
    'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
    isActive
      ? 'bg-primary/10 text-primary font-medium'
      : 'text-foreground/70 hover:bg-accent hover:text-accent-foreground',
    extra,
  );
}

export const Sidebar: React.FC = () => {
  const { mode, toggle } = useThemeStore();
  const { isCollapsed, toggleCollapsed, windowWidth } = useSidebarStore();
  const [notebookOpen, setNotebookOpen] = useState(true);

  const isMobile = windowWidth < 640;

  const handleNavClick = () => {
    if (isMobile) {
      toggleCollapsed();
    }
  };

  return (
    <>
      {/* 折叠态浮动按钮 */}
      {isCollapsed && (
        <button
          onClick={toggleCollapsed}
          className="fixed left-3 top-3 z-50 w-10 h-10 flex items-center justify-center rounded-full bg-transparent transition-colors text-muted-foreground"
          title="展开侧边栏"
        >
          <ChevronIcon collapsed={true} />
        </button>
      )}

      {/* 移动端展开时的遮罩 */}
      {!isCollapsed && isMobile && (
        <div
          className="fixed inset-0 z-30 bg-black/50"
          onClick={toggleCollapsed}
        />
      )}

      <aside
        className={cn(
          'fixed left-0 top-0 z-40 h-screen border-r bg-card flex flex-col transition-transform duration-300 w-56',
          isCollapsed ? '-translate-x-full' : 'translate-x-0',
        )}
      >
        <div className="flex flex-col h-full">
          {/* 标题栏：折叠按钮 + XFunNote */}
          <div className="h-14 flex items-center px-3 border-b gap-2">
            <button
              onClick={toggleCollapsed}
              className="shrink-0 w-8 h-8 flex items-center justify-center rounded-md hover:bg-accent transition-colors text-muted-foreground"
              title="折叠侧边栏"
            >
              <ChevronIcon collapsed={false} />
            </button>

            <span className="text-lg font-bold tracking-tight whitespace-nowrap">
              XFunNote
            </span>
          </div>

          {/* 导航 */}
          <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
            {topNav.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={handleNavClick}
                className={({ isActive }) => navLinkClass(isActive)}
              >
                <span className="text-base shrink-0">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}

            {/* 本子分组 */}
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
                className="grid transition-all duration-200"
                style={{
                  gridTemplateRows: notebookOpen ? '1fr' : '0fr',
                }}
              >
                <div className="overflow-hidden min-h-0">
                  <div className="space-y-0.5 pt-1">
                    {notebookNav.map((item) => (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        onClick={handleNavClick}
                        className={({ isActive }) => navLinkClass(isActive, 'pl-7')}
                      >
                        <span className="text-base">{item.icon}</span>
                        <span>{item.label}</span>
                      </NavLink>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 底部固定项 */}
            <div className="pt-2 space-y-0.5">
              {bottomNav.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={handleNavClick}
                  className={({ isActive }) => navLinkClass(isActive)}
                >
                  <span className="text-base">{item.icon}</span>
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          </nav>

          {/* 底部 */}
          <div className="px-5 py-3 border-t flex items-center justify-between">
            <span className="text-xs text-muted-foreground">v0.1.0</span>
            <button
              onClick={toggle}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors whitespace-nowrap"
              title={`切换主题（当前: ${mode === 'dark' ? '深色' : '浅色'}）`}
            >
              {mode === 'dark' ? '☀️ 浅色' : '🌙 深色'}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
