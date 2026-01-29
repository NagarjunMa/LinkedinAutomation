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
      const savedTheme = localStorage.getItem('prism-theme') as Theme | null;

      if (savedTheme) {
        setThemeState(savedTheme);
        applyTheme(savedTheme);
      } else {
        // Check system preference as fallback
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        setThemeState(systemTheme);
        applyTheme(systemTheme);
        localStorage.setItem('prism-theme', systemTheme);
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

      // Clear manual style overrides to let CSS classes take over
      const root = document.documentElement;
      root.style.removeProperty('--app-bg');
      root.style.removeProperty('--app-text');
      root.style.removeProperty('--app-card');
      root.style.removeProperty('--app-card-border');
      root.style.removeProperty('--app-muted');
      root.style.removeProperty('--app-accent');
    }
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    applyTheme(newTheme);
    if (typeof window !== 'undefined') {
      localStorage.setItem('prism-theme', newTheme);
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