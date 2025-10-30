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

interface UseMultiAgentOutputOptions {
  updateInterval?: number; // milliseconds
  maxRetries?: number;
  enabled?: boolean;
  staggerInterval?: number; // milliseconds between agent fetches
}

export const useMultiAgentOutput = (
  agentIds: string[],
  options: UseMultiAgentOutputOptions = {}
) => {
  const {
    updateInterval = 1000, // 1 second
    maxRetries = 3,
    enabled = true,
    staggerInterval = 100, // 100ms between each agent fetch
  } = options;

  const [outputs, setOutputs] = useState<Record<string, AgentOutputData>>({});

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryCountsRef = useRef<Record<string, number>>({});
  const lastOutputsRef = useRef<Record<string, string>>({});
  const mountedRef = useRef(true);
  const fetchQueuesRef = useRef<Set<string>>(new Set());

  // Initialize output state for new agents
  useEffect(() => {
    setOutputs(current => {
      const newOutputs = { ...current };

      // Add new agents
      agentIds.forEach(id => {
        if (!newOutputs[id]) {
          newOutputs[id] = {
            output: '',
            timestamp: '',
            isLoading: false,
            error: null,
            isConnected: false,
            lastUpdateTime: null,
          };
          retryCountsRef.current[id] = 0;
          lastOutputsRef.current[id] = '';
        }
      });

      // Remove agents that are no longer in the list
      Object.keys(newOutputs).forEach(id => {
        if (!agentIds.includes(id)) {
          delete newOutputs[id];
          delete retryCountsRef.current[id];
          delete lastOutputsRef.current[id];
        }
      });

      return newOutputs;
    });
  }, [agentIds]);

  // Fetch output for a single agent
  const fetchAgentOutput = useCallback(async (agentId: string) => {
    if (!mountedRef.current || fetchQueuesRef.current.has(agentId)) {
      return;
    }

    fetchQueuesRef.current.add(agentId);

    try {
      setOutputs(prev => ({
        ...prev,
        [agentId]: {
          ...prev[agentId],
          isLoading: true,
          error: null,
        },
      }));

      const result = await apiService.getAgentOutput(agentId);

      if (!mountedRef.current) return;

      // Only update if output has changed
      const hasChanged = result.output !== lastOutputsRef.current[agentId];
      lastOutputsRef.current[agentId] = result.output;

      setOutputs(prev => ({
        ...prev,
        [agentId]: {
          output: result.output,
          timestamp: result.timestamp,
          isLoading: false,
          isConnected: true,
          lastUpdateTime: hasChanged ? new Date() : prev[agentId]?.lastUpdateTime,
          error: null,
        },
      }));

      retryCountsRef.current[agentId] = 0;
    } catch (error) {
      if (!mountedRef.current) return;

      const retryCount = (retryCountsRef.current[agentId] || 0) + 1;
      retryCountsRef.current[agentId] = retryCount;

      setOutputs(prev => ({
        ...prev,
        [agentId]: {
          ...prev[agentId],
          isLoading: false,
          isConnected: retryCount < maxRetries,
          error: retryCount >= maxRetries ?
            `Failed to connect to agent ${agentId.substring(0, 8)}` : null,
        },
      }));
    } finally {
      fetchQueuesRef.current.delete(agentId);
    }
  }, [maxRetries]);

  // Fetch all agents with staggering
  const fetchAllAgents = useCallback(async () => {
    if (!enabled || agentIds.length === 0) return;

    // Stagger the fetches to prevent overloading the server
    for (let i = 0; i < agentIds.length; i++) {
      if (!mountedRef.current) break;

      const agentId = agentIds[i];

      // Skip if we've exceeded max retries for this agent
      if (retryCountsRef.current[agentId] >= maxRetries) {
        continue;
      }

      fetchAgentOutput(agentId);

      // Wait before fetching the next agent
      if (i < agentIds.length - 1) {
        await new Promise(resolve => setTimeout(resolve, staggerInterval));
      }
    }
  }, [agentIds, enabled, fetchAgentOutput, maxRetries, staggerInterval]);

  // Start polling
  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Initial fetch
    fetchAllAgents();

    // Start polling
    intervalRef.current = setInterval(fetchAllAgents, updateInterval);
  }, [fetchAllAgents, updateInterval]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    setOutputs(current => {
      const newOutputs = { ...current };
      Object.keys(newOutputs).forEach(id => {
        newOutputs[id] = {
          ...newOutputs[id],
          isConnected: false,
        };
      });
      return newOutputs;
    });
  }, []);

  // Retry failed agents
  const retryFailedAgents = useCallback(() => {
    // Reset retry counts for failed agents
    Object.keys(retryCountsRef.current).forEach(id => {
      if (retryCountsRef.current[id] >= maxRetries) {
        retryCountsRef.current[id] = 0;
      }
    });

    startPolling();
  }, [maxRetries, startPolling]);

  // Retry a specific agent
  const retryAgent = useCallback((agentId: string) => {
    retryCountsRef.current[agentId] = 0;
    fetchAgentOutput(agentId);
  }, [fetchAgentOutput]);

  // Start/stop polling based on enabled state
  useEffect(() => {
    if (enabled && agentIds.length > 0) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => {
      stopPolling();
    };
  }, [enabled, agentIds.length, startPolling, stopPolling]);

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

  // Get statistics
  const stats = {
    total: agentIds.length,
    connected: Object.values(outputs).filter(o => o.isConnected).length,
    failed: Object.values(outputs).filter(o => o.error).length,
    loading: Object.values(outputs).filter(o => o.isLoading).length,
  };

  return {
    outputs,
    stats,
    retryFailedAgents,
    retryAgent,
    startPolling,
    stopPolling,
  };
};

// Convenience hook for single agent (backward compatibility)
export const useRealTimeAgentOutput = (
  agentId: string | null,
  options: Omit<UseMultiAgentOutputOptions, 'staggerInterval'> = {}
) => {
  const { outputs, retryAgent, ...rest } = useMultiAgentOutput(
    agentId ? [agentId] : [],
    options
  );

  const data = agentId ? outputs[agentId] : null;

  return {
    ...(data || {
      output: '',
      timestamp: '',
      isLoading: false,
      error: null,
      isConnected: false,
      lastUpdateTime: null,
    }),
    retry: () => agentId && retryAgent(agentId),
    ...rest,
  };
};