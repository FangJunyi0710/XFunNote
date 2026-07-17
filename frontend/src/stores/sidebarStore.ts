import { create } from 'zustand';

const MOBILE_BREAKPOINT = 768;

interface SidebarState {
  isCollapsed: boolean;
  windowWidth: number;
  dragOffset: number;
  isMobile: boolean;
  toggleCollapsed: () => void;
  setWindowWidth: (width: number) => void;
  setDragOffset: (offset: number) => void;
}

function loadCollapsed(): boolean {
  const val = sessionStorage.getItem('xfun-sidebar-collapsed');
  if (val === null) {
    // 没有缓存时：移动端默认折叠，PC 端默认展开
    return typeof window !== 'undefined' ? window.innerWidth < MOBILE_BREAKPOINT : false;
  }
  return val === 'true';
}

export const useSidebarStore = create<SidebarState>((set) => ({
  isCollapsed: loadCollapsed(),
  windowWidth: typeof window !== 'undefined' ? window.innerWidth : 1200,
  dragOffset: 0,
  isMobile: typeof window !== 'undefined' ? window.innerWidth < MOBILE_BREAKPOINT : false,

  toggleCollapsed: () =>
    set((state) => {
      const next = !state.isCollapsed;
      try {
        sessionStorage.setItem('xfun-sidebar-collapsed', String(next));
      } catch {
        // ignore
      }
      return { isCollapsed: next, dragOffset: 0 };
    }),

  setWindowWidth: (width: number) =>
    set(() => ({
      windowWidth: width,
      isMobile: width < MOBILE_BREAKPOINT,
    })),

  setDragOffset: (offset: number) =>
    set(() => ({
      dragOffset: offset,
    })),
}));
