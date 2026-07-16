import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useSidebarStore } from '@/stores/sidebarStore';

export const Layout: React.FC = () => {
  const { setWindowWidth } = useSidebarStore();

  useEffect(() => {
    const onResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [setWindowWidth]);

  return (
    <div className="h-screen overflow-hidden bg-background">
      <Sidebar />
      <main className="h-full overflow-y-auto">
        <div className="max-w-5xl mx-auto px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
