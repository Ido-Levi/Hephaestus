import React from 'react';
import clsx from 'clsx';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const getStatusColor = () => {
    const normalized = status.toLowerCase();

    if (
      [
        'done',
        'completed',
        'healthy',
        'validated',
        'verified',
      ].includes(normalized)
    ) {
      return 'bg-green-100 text-green-800';
    }

    if (
      [
        'in_progress',
        'working',
        'assigned',
        'running',
      ].includes(normalized)
    ) {
      return 'bg-blue-100 text-blue-800';
    }

    if (
      [
        'pending',
        'idle',
        'pending_validation',
        'unverified',
      ].includes(normalized)
    ) {
      return 'bg-yellow-100 text-yellow-800';
    }

    if (
      [
        'failed',
        'error',
        'terminated',
        'rejected',
        'disputed',
      ].includes(normalized)
    ) {
      return 'bg-red-100 text-red-800';
    }

    if (
      ['stuck', 'warning', 'attention'].includes(normalized)
    ) {
      return 'bg-orange-100 text-orange-800';
    }

    if (normalized === 'blocked') {
      return 'bg-red-100 text-red-800 border border-red-300';
    }

    if (normalized === 'duplicated') {
      return 'bg-purple-100 text-purple-800';
    }

    if (normalized === 'queued') {
      return 'bg-cyan-100 text-cyan-800';
    }

    return 'bg-gray-100 text-gray-800';
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-medium',
        getStatusColor(),
        sizeClasses[size]
      )}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
};

export default StatusBadge;
