import { create } from 'zustand';

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeState {
  mode: ThemeMode;
  resolved: 'light' | 'dark';
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
}

function getSystemTheme(): 'light' | 'dark' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(resolved: 'light' | 'dark') {
  document.documentElement.classList.toggle('dark', resolved === 'dark');
}

function loadStoredMode(): ThemeMode {
  return (localStorage.getItem('xfun-theme') as ThemeMode) || 'system';
}

export const useThemeStore = create<ThemeState>((set, get) => {
  const stored = loadStoredMode();
  const initialResolved = stored === 'system' ? getSystemTheme() : stored;
  applyTheme(initialResolved);

  // 监听系统主题变化
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (get().mode === 'system') {
      const resolved = getSystemTheme();
      applyTheme(resolved);
      set({ resolved });
    }
  });

  return {
    mode: stored,
    resolved: initialResolved,

    setMode: (mode) => {
      localStorage.setItem('xfun-theme', mode);
      const resolved = mode === 'system' ? getSystemTheme() : mode;
      applyTheme(resolved);
      set({ mode, resolved });
    },

    toggle: () => {
      const next = get().resolved === 'light' ? 'dark' : 'light';
      get().setMode(next);
    },
  };
});
