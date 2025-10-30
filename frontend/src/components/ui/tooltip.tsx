import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface TooltipProps {
  content: string;
  children: React.ReactElement;
  delay?: number;
  className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  delay = 300,
  className
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState<'top' | 'bottom'>('top');
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
      // Calculate position based on viewport
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect();
        const spaceAbove = rect.top;
        const spaceBelow = window.innerHeight - rect.bottom;

        // Show below if not enough space above (tooltip height ~80px)
        setPosition(spaceAbove < 100 && spaceBelow > 100 ? 'bottom' : 'top');
      }
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  return (
    <div
      ref={triggerRef}
      className="relative inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {isVisible && content && (
        <div
          ref={tooltipRef}
          className={cn(
            'absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg',
            'max-w-xs whitespace-pre-wrap break-words',
            'pointer-events-none',
            'animate-in fade-in-0 zoom-in-95',
            position === 'top'
              ? 'bottom-full left-1/2 -translate-x-1/2 mb-2'
              : 'top-full left-1/2 -translate-x-1/2 mt-2',
            className
          )}
          role="tooltip"
        >
          {content}
          {/* Tooltip arrow */}
          <div
            className={cn(
              'absolute left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-900 rotate-45',
              position === 'top' ? 'bottom-[-4px]' : 'top-[-4px]'
            )}
          />
        </div>
      )}
    </div>
  );
};
