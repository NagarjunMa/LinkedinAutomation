"use client";

import React from 'react';

interface StyledButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  isDark: boolean;
  className?: string;
}

export const StyledButton: React.FC<StyledButtonProps> = ({
  children,
  onClick,
  isDark,
  className = ""
}) => {
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
          border: none;
          font-family: inherit;
          font-weight: 700;
          letter-spacing: 0.1em;
          color: ${isDark ? '#3b3b3b' : '#f0eff2'};
          background-color: ${isDark ? '#f0eff2' : '#3b3b3b'};
        }

        .styled-button-wrapper .btn:hover {
          transform: translateY(-3px);
          box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }

        .styled-button-wrapper .btn:active {
          transform: translateY(-1px);
          box-shadow: 0 5px 10px rgba(0, 0, 0, 0.2);
        }

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
          background-color: ${isDark ? '#f0eff2' : '#3b3b3b'};
        }

        .styled-button-wrapper .btn:hover::after {
          transform: scaleX(1.4) scaleY(1.6);
          opacity: 0;
        }
      `}</style>
      <button className="btn" onClick={onClick}>
        {children}
      </button>
    </div>
  );
};