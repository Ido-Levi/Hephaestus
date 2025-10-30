import { useState, useEffect, useRef, useCallback } from 'react';

interface TaskRuntimeData {
  runtimeSeconds: number;
  runtimeDisplay: string;
  isRunning: boolean;
}

export const useTaskRuntime = (
  startedAt: string | null,
  completedAt: string | null,
  initialRuntimeSeconds?: number
) => {
  const [runtime, setRuntime] = useState<TaskRuntimeData>(() => {
    // Calculate initial runtime
    let seconds = 0;
    let isRunning = false;

    if (startedAt) {
      const startTime = new Date(startedAt);
      const endTime = completedAt ? new Date(completedAt) : new Date();
      seconds = Math.max(0, Math.floor((endTime.getTime() - startTime.getTime()) / 1000));
      isRunning = !completedAt;
    } else if (initialRuntimeSeconds) {
      seconds = initialRuntimeSeconds;
    }

    return {
      runtimeSeconds: seconds,
      runtimeDisplay: formatRuntime(seconds),
      isRunning,
    };
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const updateRuntime = useCallback(() => {
    if (!startedAt) return;

    const startTime = new Date(startedAt);
    const endTime = completedAt ? new Date(completedAt) : new Date();
    const seconds = Math.max(0, Math.floor((endTime.getTime() - startTime.getTime()) / 1000));
    const isRunning = !completedAt;

    setRuntime({
      runtimeSeconds: seconds,
      runtimeDisplay: formatRuntime(seconds),
      isRunning,
    });
  }, [startedAt, completedAt]);

  // Start/stop timer based on task state
  useEffect(() => {
    updateRuntime();

    if (startedAt && !completedAt) {
      // Task is running - update every second
      intervalRef.current = setInterval(updateRuntime, 1000);
    } else {
      // Task is not running or completed - stop timer
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [updateRuntime, startedAt, completedAt]);

  return runtime;
};

function formatRuntime(totalSeconds: number): string {
  if (totalSeconds === 0) {
    return 'Not started';
  }

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  } else {
    return `${seconds}s`;
  }
}

// Utility function for standalone use
export const formatRuntimeDuration = formatRuntime;