import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useSidebarStore } from '@/stores/sidebarStore';

export const Layout: React.FC = () => {
  const { hideContent, setWindowWidth } = useSidebarStore();

  useEffect(() => {
    const onResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [setWindowWidth]);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {hideContent ? (
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm px-4 text-center">
            侧边栏已展开，折叠后可查看内容
          </div>
        ) : (
          <div className="max-w-5xl mx-auto px-6 py-6">
            <Outlet />
          </div>
        )}
      </main>
    </div>
  );
};
