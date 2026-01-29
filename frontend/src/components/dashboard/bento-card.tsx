"use client";

import React from 'react';
import { motion } from 'framer-motion';

export interface BentoCardProps {
    children: React.ReactNode;
    className?: string;
    delay?: number;
    title?: string;
    action?: React.ReactNode;
}

export const BentoCard: React.FC<BentoCardProps> = ({ children, className = '', delay = 0, title, action }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: delay * 0.1 }}
            className={`
        relative overflow-hidden
        bg-app-card border border-app-text/5 backdrop-blur-sm
        p-6 sm:p-8 flex flex-col justify-between
        ${className}
      `}
        >
            <div className="flex justify-between items-start mb-6 sm:mb-8">
                <h3 className="text-sm sm:text-base font-bold uppercase tracking-widest text-app-text/90">{title}</h3>
                {action}
            </div>
            {children}
        </motion.div>
    );
};
