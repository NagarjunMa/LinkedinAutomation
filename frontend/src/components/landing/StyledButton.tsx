"use client";

import React from 'react';

interface StyledButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  isDark?: boolean;
  className?: string;
  variant?: 'primary' | 'secondary';
}

export const StyledButton: React.FC<StyledButtonProps> = ({
  children,
  onClick,
  isDark = false,
  className = "",
  variant = 'primary'
}) => {
  // Colors based on variant and theme
  const getColors = () => {
    if (variant === 'secondary') {
      return {
        bg: 'transparent',
        text: isDark ? '#f0eff2' : '#3b3b3b',
        border: isDark ? 'rgba(240, 239, 242, 0.2)' : 'rgba(59, 59, 59, 0.2)',
        hoverBg: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)'
      };
    }
    // Primary
    return {
      bg: isDark ? '#f0eff2' : '#3b3b3b',
      text: isDark ? '#3b3b3b' : '#f0eff2',
      border: 'transparent',
      hoverBg: isDark ? '#f0eff2' : '#3b3b3b'
    };
  };

  const colors = getColors();

  return (
    <div className={`styled-button-wrapper ${className}`}>
      <style jsx>{`
        .styled-button-wrapper .btn {
          position: relative;
          font-size: 13px;
          text-transform: uppercase;
          text-decoration: none;
          padding: 1em 2.5em;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          border-radius: 6em;
          transition: all 0.2s;
          border: ${variant === 'secondary' ? `1px solid ${colors.border}` : 'none'};
          font-family: inherit;
          font-weight: 700;
          letter-spacing: 0.1em;
          color: ${colors.text};
          background-color: ${colors.bg};
        }

        .styled-button-wrapper .btn:hover {
          transform: translateY(-3px);
          box-shadow: 0 10px 20px rgba(0, 0, 0, ${variant === 'secondary' ? '0.05' : '0.2'});
          background-color: ${variant === 'secondary' ? colors.hoverBg : colors.bg};
          border-color: ${variant === 'secondary' ? colors.text : 'transparent'};
        }

        .styled-button-wrapper .btn:active {
          transform: translateY(-1px);
          box-shadow: 0 5px 10px rgba(0, 0, 0, ${variant === 'secondary' ? '0.05' : '0.2'});
        }

        /* Ripple effect only for primary */
        ${variant === 'primary' ? `
        .styled-button-wrapper .btn::after {
          content: "";
          display: inline-block;
          height: 100%;
          width: 100%;
          border-radius: 100px;
          position: absolute;
          top: 0;
          left: 0;
          z-index: -1;
          transition: all 0.4s;
          background-color: ${colors.bg};
        }

        .styled-button-wrapper .btn:hover::after {
          transform: scaleX(1.4) scaleY(1.6);
          opacity: 0;
        }
        ` : ''}
      `}</style>
      <button className="btn" onClick={onClick}>
        {children}
      </button>
    </div>
  );
};