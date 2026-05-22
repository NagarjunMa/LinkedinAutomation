"use client";

import React, { useEffect } from 'react';
import { motion, useAnimation, useInView } from 'framer-motion';

interface SectionHeaderProps {
  title: string;
  subtitle: string;
  label?: string;
  number?: string; // e.g. "01"
}

const fadeInUp = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
  }
};

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  label,
  number,
}) => {
  const controls = useAnimation();
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.3 });

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
      {/* Eyebrow label with optional number */}
      {(label || number) && (
        <span
          className="block mb-5 text-foreground/45 uppercase text-[11px] font-medium"
          style={{
            fontFamily: 'var(--font-humane), sans-serif',
            letterSpacing: '0.18em',
          }}
        >
          {number ? `${number} / ${label}` : label}
        </span>
      )}

      {/* Section H2 — Fraunces serif, left-aligned */}
      <h2
        className="mb-6 font-normal leading-[1.1] text-foreground"
        style={{
          fontFamily: 'var(--font-fraunces), Georgia, serif',
          fontSize: 'clamp(40px, 6vw, 88px)',
          letterSpacing: '-0.01em',
        }}
      >
        {title}
      </h2>

      <p
        className="text-foreground/60 leading-relaxed text-[15px]"
        style={{ fontFamily: 'var(--font-humane), sans-serif' }}
      >
        {subtitle}
      </p>
    </motion.div>
  );
};
