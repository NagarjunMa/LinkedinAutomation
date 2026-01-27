"use client";

import { useState, useEffect } from 'react';

export type Theme = 'light' | 'dark';

export const useApplicationTheme = () => {
  const [theme, setTheme] = useState<Theme>('light');

  useEffect(() => {
    // Check for saved theme preference or default to 'light'
    const savedTheme = localStorage.getItem('app-theme') as Theme;
    if (savedTheme) {
      setTheme(savedTheme);
      updateTheme(savedTheme);
    } else {
      // Check system preference
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      setTheme(systemTheme);
      updateTheme(systemTheme);
    }
  }, []);

  const updateTheme = (newTheme: Theme) => {
    if (typeof document !== 'undefined') {
      // Remove both old theme classes
      document.body.classList.remove('landing-light', 'landing-dark');
      document.documentElement.classList.remove('light', 'dark');

      // Add new theme classes
      document.body.classList.add(`landing-${newTheme}`);
      document.documentElement.classList.add(newTheme);

      // Update data attribute for shadcn components
      document.documentElement.setAttribute('data-theme', newTheme);
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    updateTheme(newTheme);
    localStorage.setItem('app-theme', newTheme);
  };

  const setThemeMode = (newTheme: Theme) => {
    setTheme(newTheme);
    updateTheme(newTheme);
    localStorage.setItem('app-theme', newTheme);
  };

  const isDark = theme === 'dark';
  const isLight = theme === 'light';

  return {
    theme,
    toggleTheme,
    setThemeMode,
    isDark,
    isLight
  };
};