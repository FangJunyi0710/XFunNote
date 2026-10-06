import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useThemeStore } from '@/stores/themeStore';
import { useSidebarStore } from '@/stores/sidebarStore';
import { NOTEBOOK_ROUTES, isSystemTable } from '@/config/notebook';
import { ArrowIcon, MoonIcon, SunIcon } from '@/components/ui/icons';
import pkg from '../../../package.json';

interface NavItem {
  label: string;
  path: string;
}

const topNav: NavItem[] = [{ label: '首页', path: '/' }];

const notebookNav: NavItem[] = Object.entries(NOTEBOOK_ROUTES)
  .filter(([key]) => !isSystemTable(key))
  .map(([, route]) => ({ label: route.label, path: route.path }));

const systemTableNav: NavItem[] = Object.entries(NOTEBOOK_ROUTES)
  .filter(([key]) => isSystemTable(key))
  .map(([, route]) => ({ label: route.label, path: route.path }));

const bottomNav: NavItem[] = [
  // { label: '管理', path: '/management' },
  { label: 'Token 管理', path: '/token-input' },
];



const navLinkClass = (isActive: boolean, extra = '') => cn(
    'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors',
    isActive
      ? 'bg-primary/10 text-primary font-medium'
      : 'text-foreground/70 hover:bg-accent hover:text-accent-foreground',
    extra,
  );

export const Sidebar: React.FC = () => {
  const { mode, toggle } = useThemeStore();
  const { isCollapsed, toggleCollapsed, dragOffset, isMobile, touchDetected } = useSidebarStore();
  const [notebookOpen, setNotebookOpen] = useState(true);
  const [systemTableOpen, setSystemTableOpen] = useState(false);
  const handleNavClick = () => {
    if (isMobile) {
      toggleCollapsed();
    }
  };

  return (
    <>
      {/* 折叠态浮动按钮（移动端隐藏，靠触摸滑出） */}
      {!touchDetected && isCollapsed && (
        <button
          onClick={toggleCollapsed}
          className="fixed left-3 top-3 z-50 w-10 h-10 flex items-center justify-center rounded-full bg-transparent transition-colors text-muted-foreground"
          title="展开侧边栏"
        >
          <ArrowIcon direction='right' />
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
        className={cn('absolute left-0 top-0 z-40 h-screen border-r bg-card flex flex-col w-56 transition-transform duration-300 ease-in-out', dragOffset && 'duration-0')}
        style={{
          transform: isCollapsed
            ? `translateX(calc(-100% + ${dragOffset}px))`
            : `translateX(${dragOffset}px)`,
        }}
      >
        <div className="flex flex-col h-full">
          {/* 标题栏：折叠按钮 + XFunNote */}
          <div className="h-14 flex items-center px-3 border-b gap-2">
            <button
              onClick={toggleCollapsed}
              className="shrink-0 w-8 h-8 flex items-center justify-center rounded-md hover:bg-accent transition-colors text-muted-foreground"
              title="折叠侧边栏"
            >
              <ArrowIcon direction='left' />
            </button>

            <NavLink
              to="/"
              onClick={handleNavClick}
              className="text-lg font-bold tracking-tight whitespace-nowrap transition-colors"
            >
              XFunNote
            </NavLink>
          </div>

          {/* 导航 */}
          <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
            {topNav.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={handleNavClick}
                className={({ isActive }) => navLinkClass(isActive)}
              >
                <span>{item.label}</span>
              </NavLink>
            ))}

            {/* 本子分组 */}
            <div className="pt-2">
              <button
                onClick={() => setNotebookOpen(v => !v)}
                className="flex items-center gap-2 w-full px-3 py-2.5 rounded-md text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                <ArrowIcon direction='right' className={cn('transition-transform duration-100 origin-center',
                  notebookOpen && 'rotate-90'
                )} />
                笔记本
              </button>

              <div className={cn("grid transition-all duration-200", notebookOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]')}>
                <div className="overflow-hidden min-h-0">
                  <div className="space-y-0.5 pt-1">
                    {notebookNav.map(item => (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        onClick={handleNavClick}
                        className={({ isActive }) => navLinkClass(isActive, 'pl-7')}
                      >
                        <span>{item.label}</span>
                      </NavLink>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 系统表分组 */}
            <div className="pt-2">
              <button
                onClick={() => setSystemTableOpen(v => !v)}
                className="flex items-center gap-2 w-full px-3 py-2.5 rounded-md text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                <ArrowIcon direction='right' className={cn('transition-transform duration-100 origin-center',
                  systemTableOpen && 'rotate-90'
                )} />
                系统表
              </button>

              <div className={cn("grid transition-all duration-200", systemTableOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]')}>
                <div className="overflow-hidden min-h-0">
                  <div className="space-y-0.5 pt-1">
                    {systemTableNav.map(item => (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        onClick={handleNavClick}
                        className={({ isActive }) => navLinkClass(isActive, 'pl-7')}
                      >
                        <span>{item.label}</span>
                      </NavLink>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 底部固定项 */}
            <div className="pt-2 space-y-0.5">
              {bottomNav.map(item => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={handleNavClick}
                  className={({ isActive }) => navLinkClass(isActive)}
                >
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          </nav>

          {/* 底部 */}
          <div className="px-5 py-3 border-t flex items-center justify-between">
            <span className="text-xs text-muted-foreground">v{pkg.version}</span>
            <button
              onClick={toggle}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors whitespace-nowrap"
              title={`切换主题（当前: ${mode === 'dark' ? '深色' : '浅色'}）`}
            >
              {mode === 'dark' ? <MoonIcon/> : <SunIcon/>}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
