import { create } from 'zustand';

type ThemeMode = 'light' | 'dark';

interface ThemeState {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
}

function getSystemTheme(): ThemeMode {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(resolved: ThemeMode) {
  document.documentElement.classList.toggle('dark', resolved === 'dark');
}

function loadStoredMode(): ThemeMode {
  const stored = localStorage.getItem('xfun-theme');
  return stored === 'light' || stored === 'dark' ? stored : getSystemTheme();
}

export const useThemeStore = create<ThemeState>((set, get) => {
  const initial = loadStoredMode();
  applyTheme(initial);

  // 监听系统主题变化（仅当 localStorage 无值时跟随系统）
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (!localStorage.getItem('xfun-theme')) {
      const resolved = getSystemTheme();
      applyTheme(resolved);
      set({ mode: resolved });
    }
  });

  return {
    mode: initial,

    setMode: (mode) => {
      localStorage.setItem('xfun-theme', mode);
      applyTheme(mode);
      set({ mode });
    },

    toggle: () => {
      const next = get().mode === 'light' ? 'dark' : 'light';
      get().setMode(next);
    },
  };
});
