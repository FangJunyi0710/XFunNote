import { create } from 'zustand';

interface SidebarState {
  isCollapsed: boolean;
  windowWidth: number;
  toggleCollapsed: () => void;
  setWindowWidth: (width: number) => void;
}

function loadCollapsed(): boolean {
  try {
    const val = sessionStorage.getItem('xfun-sidebar-collapsed');
    if (val === null) return false;
    return val === 'true';
  } catch {
    return false;
  }
}

export const useSidebarStore = create<SidebarState>((set) => ({
  isCollapsed: loadCollapsed(),
  windowWidth: typeof window !== 'undefined' ? window.innerWidth : 1200,

  toggleCollapsed: () =>
    set((state) => {
      const next = !state.isCollapsed;
      try {
        sessionStorage.setItem('xfun-sidebar-collapsed', String(next));
      } catch {
        // ignore
      }
      return { isCollapsed: next };
    }),

  setWindowWidth: (width: number) =>
    set(() => ({
      windowWidth: width,
    })),
}));
