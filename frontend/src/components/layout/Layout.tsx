import React, { useEffect, useRef } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useSidebarStore } from '@/stores/sidebarStore';

export const Layout: React.FC = () => {
  const { isCollapsed, setWindowWidth, toggleCollapsed, setDragOffset, dragOffset, isMobile } = useSidebarStore();
  const touchStartX = useRef(0);
  const touchStartY = useRef(0);
  const sidebarWidth = useRef(0);
  const ignoreTouch = useRef(false);

  useEffect(() => {
    const onResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [setWindowWidth]);

  // 触摸手势：跟随手指拖动 sidebar，松手时判断
  useEffect(() => {
    const handleTouchStart = (e: TouchEvent) => {
      ignoreTouch.current = false;
      const touch = e.touches[0];
      if (!touch) {
        ignoreTouch.current = true;
        return;
      }
      touchStartX.current = touch.clientX;
      touchStartY.current = touch.clientY;
      // 获取 sidebar 元素的实际宽度
      const el = document.querySelector('aside');
      if (el) {
        sidebarWidth.current = el.offsetWidth;
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (ignoreTouch.current) return;
      const touch = e.touches[0];
      if (!touch) {
        ignoreTouch.current = true;
        return;
      }
      const diffX = touch.clientX - touchStartX.current;
      const diffY = touch.clientY - touchStartY.current;
      const w = sidebarWidth.current;

      // 竖直偏移超过水平偏移的 x 倍，此次触摸忽略
      if (Math.abs(diffY) > Math.abs(diffX) * 0.8) {
        ignoreTouch.current = true;
        setDragOffset(0);
        return;
      }

      if (isCollapsed) {
        // 折叠态：只允许向右拖，限制最大为 sidebar 宽度
        if (diffX > 0) {
          setDragOffset(Math.min(diffX, w));
        }
      } else {
        // 展开态：只允许向左拖，限制最小为 -sidebar 宽度
        if (diffX < 0) {
          setDragOffset(Math.max(diffX, -w));
        }
      }
    };

    const handleTouchEnd = () => {
      if (ignoreTouch.current) {
        ignoreTouch.current = false;
        return;
      }

      const { dragOffset = 0 } = useSidebarStore.getState();
      const w = sidebarWidth.current;

      if (isCollapsed && dragOffset > w * 0.3) {
        toggleCollapsed();
      } else if (!isCollapsed && dragOffset < -w * 0.1) {
        toggleCollapsed();
      } else {
        setDragOffset(0);
      }
    };

    document.addEventListener('touchstart', handleTouchStart, { passive: true });
    document.addEventListener('touchmove', handleTouchMove, { passive: true });
    document.addEventListener('touchend', handleTouchEnd);

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [isCollapsed, toggleCollapsed, setDragOffset]);

  return (
    <div className="h-screen overflow-hidden bg-background relative">
      <Sidebar />
      <main id="main-scroll-container" className="h-full overflow-y-auto absolute"
        style={isMobile ? {
          width: '100%',
          marginLeft: Math.max(0, (isCollapsed ? 0 : 224) + (dragOffset || 0)) + 'px',
          transition: dragOffset === 0 ? 'margin-left 0.3s ease' : 'none',
        }:{
          left: Math.max(0, (isCollapsed ? 0 : 224) + (dragOffset || 0)) + 'px',
          right: 0,
          transition: dragOffset === 0 ? 'left 0.3s ease' : 'none',
        }}
      >
        <div className="max-w-7xl mx-auto px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
