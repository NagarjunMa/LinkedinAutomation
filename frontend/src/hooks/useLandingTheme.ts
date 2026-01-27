"use client";

import { useState, useEffect } from 'react';

export const useLandingTheme = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // Check for saved theme preference or default to 'light'
    const savedTheme = localStorage.getItem('landing-theme') as 'light' | 'dark';
    if (savedTheme) {
      setTheme(savedTheme);
      updateBodyClass(savedTheme);
    } else {
      updateBodyClass('light');
    }
  }, []);

  const updateBodyClass = (newTheme: 'light' | 'dark') => {
    if (typeof document !== 'undefined') {
      document.body.classList.remove('landing-light', 'landing-dark');
      document.body.classList.add(`landing-${newTheme}`);
    }
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    updateBodyClass(newTheme);
    localStorage.setItem('landing-theme', newTheme);
  };

  const isDark = theme === 'dark';

  return { theme, toggleTheme, isDark };
};