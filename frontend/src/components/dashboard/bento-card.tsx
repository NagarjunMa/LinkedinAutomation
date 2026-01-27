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

export const BentoCard: React.FC<BentoCardProps> = ({ children, className = '', delay = 0, title, action }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.2, delay, ease: [0.22, 1, 0.36, 1] }}
        className={`bg-white/40 border border-[#3b3b3b]/10 flex flex-col backdrop-blur-sm group transition-all duration-700 rounded-lg overflow-hidden ${className}`}
    >
        {(title || action) && (
            <div className="px-8 py-6 border-b border-[#3b3b3b]/5 flex justify-between items-center">
                {title && <h3 className="text-[10px] font-bold tracking-[0.2em] uppercase text-[#3b3b3b]/60">{title}</h3>}
                {action}
            </div>
        )}
        <div className="p-8 flex-1">
            {children}
        </div>
    </motion.div>
);
