/**
 * Task 21: BulletHighlight component tests
 *
 * 3 tests:
 * 1. renders critical severity via data-severity attribute
 * 2. renders warning severity via data-severity attribute
 * 3. renders info severity via data-severity attribute
 *
 * Severity is conveyed via data-severity on the root <li> element.
 * BulletHighlight uses Radix Tooltip — must wrap in TooltipProvider.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { BulletHighlight } from '@/components/resume/bullet-highlight';
import { ResumeRenderer } from '@/components/resume/resume-renderer';
import type { Bullet, BulletFlag } from '@/app/lib/api';

function renderBullet(bullet: Bullet, flag?: BulletFlag) {
  const onClick = vi.fn();
  return render(
    <TooltipProvider>
      <BulletHighlight bullet={bullet} flags={flag ? [flag] : []} onClick={onClick} />
    </TooltipProvider>
  );
}

const baseBullet: Bullet = { id: 'b1', text: 'Did stuff', raw_text: 'Did stuff' };

describe('BulletHighlight', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders critical severity via data-severity', () => {
    const flag: BulletFlag = {
      bullet_id: 'b1',
      severity: 'critical',
      reason: 'No quantification',
      category: 'quantification',
    };
    const { container } = renderBullet(baseBullet, flag);
    const li = container.querySelector('li');
    expect(li).not.toBeNull();
    expect(li!.getAttribute('data-severity')).toBe('critical');
  });

  it('renders warning severity via data-severity', () => {
    const flag: BulletFlag = {
      bullet_id: 'b1',
      severity: 'warning',
      reason: 'Weak action verb',
      category: 'verb',
    };
    const { container } = renderBullet(baseBullet, flag);
    const li = container.querySelector('li');
    expect(li).not.toBeNull();
    expect(li!.getAttribute('data-severity')).toBe('warning');
  });

  it('renders info severity via data-severity', () => {
    const flag: BulletFlag = {
      bullet_id: 'b1',
      severity: 'info',
      reason: 'Minor clarity issue',
      category: 'clarity',
    };
    const { container } = renderBullet(baseBullet, flag);
    const li = container.querySelector('li');
    expect(li).not.toBeNull();
    expect(li!.getAttribute('data-severity')).toBe('info');
  });

  it('renders unflagged bullets and calls onClick with the bullet id', () => {
    const onClick = vi.fn();
    const { container } = render(
      <TooltipProvider>
        <BulletHighlight bullet={baseBullet} onClick={onClick} />
      </TooltipProvider>
    );

    const li = container.querySelector('li');
    expect(li).not.toBeNull();
    expect(li!.getAttribute('data-severity')).toBe('none');
    fireEvent.click(screen.getByRole('button', { name: baseBullet.text }));
    expect(onClick).toHaveBeenCalledWith('b1');
  });

  it('preserves a critical finding when a later informational finding shares the bullet', () => {
    const flags: BulletFlag[] = [
      { bullet_id: 'b1', severity: 'critical', category: 'clarity', reason: 'Explain ownership.' },
      { bullet_id: 'b1', severity: 'info', category: 'verb', reason: 'Action is clear.' },
    ];
    render(<TooltipProvider><ResumeRenderer doc={{ contact: { name: 'Synthetic', links: [] },
      experience: [{ role: 'Engineer', company: 'Example', bullets: [baseBullet] }],
      projects: [], education: [], skills: { hard: [], soft: [] },
    } as any} flags={flags} onBulletClick={vi.fn()} /></TooltipProvider>);
    expect(screen.getByTestId('bullet-b1')).toHaveAttribute('data-severity', 'critical');
  });
});
