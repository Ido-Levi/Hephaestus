import { useState, useEffect, useRef, useCallback } from 'react';
import { apiService } from '@/services/api';

interface AgentOutputData {
  output: string;
  timestamp: string;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  lastUpdateTime: Date | null;
}

interface UseRealTimeAgentOutputOptions {
  updateInterval?: number; // milliseconds
  maxRetries?: number;
  enabled?: boolean;
}

export const useRealTimeAgentOutput = (
  agentId: string | null,
  options: UseRealTimeAgentOutputOptions = {}
) => {
  const {
    updateInterval = 1000, // 1 second
    maxRetries = 3,
    enabled = true
  } = options;

  const [data, setData] = useState<AgentOutputData>({
    output: '',
    timestamp: '',
    isLoading: false,
    error: null,
    isConnected: false,
    lastUpdateTime: null,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountRef = useRef(0);
  const lastOutputRef = useRef('');
  const mountedRef = useRef(true);

  const fetchAgentOutput = useCallback(async () => {
    if (!agentId || !enabled || !mountedRef.current) {
      return;
    }

    try {
      setData(prev => ({ ...prev, isLoading: true, error: null }));

      const result = await apiService.getAgentOutput(agentId);

      if (!mountedRef.current) return;

      // Only update if output has changed to prevent unnecessary re-renders
      const hasChanged = result.output !== lastOutputRef.current;
      lastOutputRef.current = result.output;

      setData(prev => ({
        ...prev,
        output: result.output,
        timestamp: result.timestamp,
        isLoading: false,
        isConnected: true,
        lastUpdateTime: hasChanged ? new Date() : prev.lastUpdateTime,
        error: null,
      }));

      retryCountRef.current = 0; // Reset retry count on success
    } catch (error) {
      if (!mountedRef.current) return;

      console.warn(`Failed to fetch agent output for ${agentId}:`, error);
      retryCountRef.current++;

      setData(prev => ({
        ...prev,
        isLoading: false,
        isConnected: retryCountRef.current < maxRetries,
        error: retryCountRef.current >= maxRetries ?
          'Failed to connect to agent output' : null,
      }));

      // Stop polling if we've exceeded max retries
      if (retryCountRef.current >= maxRetries && intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, [agentId, enabled, maxRetries]);

  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Initial fetch
    fetchAgentOutput();

    // Start polling
    intervalRef.current = setInterval(fetchAgentOutput, updateInterval);
  }, [fetchAgentOutput, updateInterval]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    setData(prev => ({ ...prev, isConnected: false }));
  }, []);

  const retry = useCallback(() => {
    retryCountRef.current = 0;
    startPolling();
  }, [startPolling]);

  // Start/stop polling based on agentId and enabled
  useEffect(() => {
    if (agentId && enabled) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [agentId, enabled, startPolling, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    ...data,
    retry,
    startPolling,
    stopPolling,
  };
};