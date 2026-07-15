import { create } from 'zustand';

interface SidebarState {
  isCollapsed: boolean;
  windowWidth: number;
  hideContent: boolean;
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

function shouldHideContent(isCollapsed: boolean, windowWidth: number): boolean {
  return !isCollapsed && windowWidth < 640;
}

export const useSidebarStore = create<SidebarState>((set) => ({
  isCollapsed: loadCollapsed(),
  windowWidth: typeof window !== 'undefined' ? window.innerWidth : 1200,
  hideContent: shouldHideContent(loadCollapsed(), window.innerWidth),

  toggleCollapsed: () =>
    set((state) => {
      const next = !state.isCollapsed;
      try {
        sessionStorage.setItem('xfun-sidebar-collapsed', String(next));
      } catch {
        // ignore
      }
      return {
        isCollapsed: next,
        hideContent: shouldHideContent(next, state.windowWidth),
      };
    }),

  setWindowWidth: (width: number) =>
    set((state) => ({
      windowWidth: width,
      hideContent: shouldHideContent(state.isCollapsed, width),
    })),
}));
