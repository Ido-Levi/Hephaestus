import React from 'react';
import { cn } from '@/lib/utils';

interface PhaseBadgeProps {
  phaseOrder: number;
  phaseName: string;
  totalPhases?: number;
  className?: string;
}

export function PhaseBadge({ phaseOrder, phaseName, totalPhases = 3, className }: PhaseBadgeProps) {
  // Dynamic intensity based on phase order
  const getPhaseIntensity = () => {
    const opacity = 0.3 + (0.7 * ((phaseOrder - 1) / Math.max(totalPhases - 1, 1)));
    return `rgba(59, 130, 246, ${opacity})`;
  };

  const backgroundColor = getPhaseIntensity();
  const textColor = phaseOrder > totalPhases / 2 ? 'white' : 'rgb(30, 58, 138)'; // Darker text for lighter backgrounds

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium",
        className
      )}
      style={{
        backgroundColor,
        color: textColor,
      }}
      title={`Phase ${phaseOrder}: ${phaseName}`}
    >
      <span className="font-bold">P{phaseOrder}</span>
      <span className="truncate max-w-[150px]">{phaseName}</span>
    </span>
  );
}