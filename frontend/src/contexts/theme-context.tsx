"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

export type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  isDark: boolean;
  isLight: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>('light');
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Initialize theme on client side only
    if (typeof window !== 'undefined') {
      // Check for saved theme preference first
      const savedTheme = localStorage.getItem('jobflow-theme') as Theme | null;

      if (savedTheme) {
        setThemeState(savedTheme);
        applyTheme(savedTheme);
      } else {
        // Check system preference as fallback
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        setThemeState(systemTheme);
        applyTheme(systemTheme);
        localStorage.setItem('jobflow-theme', systemTheme);
      }

      setIsInitialized(true);
    }
  }, []);

  const applyTheme = (newTheme: Theme) => {
    if (typeof document !== 'undefined') {
      // Remove all existing theme classes
      document.body.classList.remove('landing-light', 'landing-dark');
      document.documentElement.classList.remove('light', 'dark');

      // Add new theme classes
      document.body.classList.add(`landing-${newTheme}`);
      document.documentElement.classList.add(newTheme);

      // Update data attribute for shadcn components
      document.documentElement.setAttribute('data-theme', newTheme);

      // Update CSS custom properties
      const root = document.documentElement;
      if (newTheme === 'dark') {
        root.style.setProperty('--app-bg', '#3b3b3b');
        root.style.setProperty('--app-text', '#f0eff2');
        root.style.setProperty('--app-card', 'rgba(0, 0, 0, 0.2)');
        root.style.setProperty('--app-card-border', 'rgba(240, 239, 242, 0.1)');
        root.style.setProperty('--app-muted', 'rgba(240, 239, 242, 0.6)');
        root.style.setProperty('--app-accent', 'rgba(240, 239, 242, 0.8)');
      } else {
        root.style.setProperty('--app-bg', '#f0eff2');
        root.style.setProperty('--app-text', '#3b3b3b');
        root.style.setProperty('--app-card', 'rgba(255, 255, 255, 0.5)');
        root.style.setProperty('--app-card-border', 'rgba(59, 59, 59, 0.1)');
        root.style.setProperty('--app-muted', 'rgba(59, 59, 59, 0.6)');
        root.style.setProperty('--app-accent', 'rgba(59, 59, 59, 0.8)');
      }
    }
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    applyTheme(newTheme);
    if (typeof window !== 'undefined') {
      localStorage.setItem('jobflow-theme', newTheme);
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };

  const value: ThemeContextType = {
    theme,
    toggleTheme,
    setTheme,
    isDark: theme === 'dark',
    isLight: theme === 'light',
  };

  // Don't render children until theme is initialized on client side
  if (!isInitialized) {
    return <div className="min-h-screen bg-background" />; // Temporary loading state
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}