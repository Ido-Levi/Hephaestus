import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { WorkflowDefinition, WorkflowExecution } from '@/types';

export type { WorkflowDefinition, WorkflowExecution };

interface WorkflowContextType {
  definitions: WorkflowDefinition[];
  executions: WorkflowExecution[];
  selectedExecutionId: string | null;
  selectedExecution: WorkflowExecution | null;
  selectExecution: (id: string | null, disableAutoSelect?: boolean) => void;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

const WorkflowContext = createContext<WorkflowContextType | undefined>(undefined);

export const WorkflowProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(() => {
    // Try to restore from localStorage
    const saved = localStorage.getItem('selectedWorkflowExecutionId');
    return saved || null;
  });
  const queryClient = useQueryClient();
  const autoSelectDisabledRef = useRef(false);

  const {
    data: definitions = [],
    isLoading: defsLoading,
    error: defsError
  } = useQuery({
    queryKey: ['workflow-definitions'],
    queryFn: apiService.listWorkflowDefinitions,
  });

  const {
    data: executions = [],
    isLoading: execsLoading,
    error: execsError,
    refetch
  } = useQuery({
    queryKey: ['workflow-executions'],
    queryFn: () => apiService.listWorkflowExecutions('all'),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Auto-select first active execution if none selected or current selection no longer exists
  useEffect(() => {
    // Skip auto-select if it's been explicitly disabled (e.g., user selected a definition with no executions)
    if (autoSelectDisabledRef.current) {
      return;
    }

    if (executions.length > 0) {
      const currentExists = executions.some(e => e.id === selectedExecutionId);

      if (!selectedExecutionId || !currentExists) {
        const activeExecution = executions.find(e => e.status === 'active');
        if (activeExecution) {
          setSelectedExecutionId(activeExecution.id);
        } else if (executions.length > 0) {
          // Fall back to first execution if no active ones
          setSelectedExecutionId(executions[0].id);
        }
      }
    }
  }, [executions, selectedExecutionId]);

  // Persist selection to localStorage
  useEffect(() => {
    if (selectedExecutionId) {
      localStorage.setItem('selectedWorkflowExecutionId', selectedExecutionId);
    } else {
      localStorage.removeItem('selectedWorkflowExecutionId');
    }
  }, [selectedExecutionId]);

  const selectedExecution = executions.find(e => e.id === selectedExecutionId) || null;

  const selectExecution = useCallback((id: string | null, disableAutoSelect?: boolean) => {
    // If explicitly disabling auto-select (e.g., user selected a definition with no executions)
    if (disableAutoSelect) {
      autoSelectDisabledRef.current = true;
    } else if (id) {
      // Re-enable auto-select when a valid execution is selected
      autoSelectDisabledRef.current = false;
    }

    setSelectedExecutionId(id);
    // Invalidate queries that depend on workflow selection
    queryClient.invalidateQueries({ queryKey: ['tasks'] });
    queryClient.invalidateQueries({ queryKey: ['tickets'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    queryClient.invalidateQueries({ queryKey: ['blocked-tasks'] });
    queryClient.invalidateQueries({ queryKey: ['queue-status'] });
    queryClient.invalidateQueries({ queryKey: ['workflow-execution'] });
  }, [queryClient]);

  return (
    <WorkflowContext.Provider
      value={{
        definitions,
        executions,
        selectedExecutionId,
        selectedExecution,
        selectExecution,
        loading: defsLoading || execsLoading,
        error: defsError || execsError || null,
        refetch,
      }}
    >
      {children}
    </WorkflowContext.Provider>
  );
};

export const useWorkflow = () => {
  const context = useContext(WorkflowContext);
  if (!context) {
    throw new Error('useWorkflow must be used within a WorkflowProvider');
  }
  return context;
};
