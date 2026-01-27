"use client";

import React, { useEffect } from 'react';
import { motion, useAnimation, useInView } from 'framer-motion';

interface SectionHeaderProps {
  title: string;
  subtitle: string;
  label?: string;
}

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
  }
};

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  label
}) => {
  const controls = useAnimation();
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.5 });

  useEffect(() => {
    if (isInView) {
      controls.start('visible');
    }
  }, [isInView, controls]);

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={controls}
      variants={fadeInUp}
      className="mb-16 max-w-2xl text-left"
    >
      {label && (
        <span className="text-xs font-bold tracking-[0.2em] uppercase opacity-60 mb-4 block">
          {label}
        </span>
      )}
      <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-6 leading-tight">
        {title}
      </h2>
      <p className="text-lg opacity-70 leading-relaxed">
        {subtitle}
      </p>
    </motion.div>
  );
};