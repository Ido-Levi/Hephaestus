import React, { useState, useMemo, useEffect } from 'react';
import { useWorkflow } from '@/context/WorkflowContext';
import { ChevronDown, Workflow, Activity, Layers } from 'lucide-react';

interface WorkflowSelectorProps {
  onDefinitionChange?: (definitionId: string | null) => void;
}

export const WorkflowSelector: React.FC<WorkflowSelectorProps> = ({ onDefinitionChange }) => {
  const { executions, definitions, selectedExecutionId, selectedExecution, selectExecution, loading } = useWorkflow();
  const [selectedDefinitionId, setSelectedDefinitionId] = useState<string | null>(null);

  // Group executions by definition_id
  const executionsByDefinition = useMemo(() => {
    const grouped: { [key: string]: typeof executions } = {};
    executions.forEach(execution => {
      const defId = execution.definition_id || 'unknown';
      if (!grouped[defId]) {
        grouped[defId] = [];
      }
      grouped[defId].push(execution);
    });
    return grouped;
  }, [executions]);

  // Auto-select definition when execution is selected
  useEffect(() => {
    if (selectedExecutionId) {
      const execution = executions.find(e => e.id === selectedExecutionId);
      if (execution && execution.definition_id !== selectedDefinitionId) {
        const newDefId = execution.definition_id || null;
        setSelectedDefinitionId(newDefId);
        onDefinitionChange?.(newDefId);
      }
    }
  }, [selectedExecutionId, executions, selectedDefinitionId, onDefinitionChange]);

  // Get executions for selected definition
  const filteredExecutions = useMemo(() => {
    if (!selectedDefinitionId) return [];
    return executionsByDefinition[selectedDefinitionId] || [];
  }, [selectedDefinitionId, executionsByDefinition]);

  // Separate active and inactive executions
  const activeExecutions = filteredExecutions.filter(e => e.status === 'active');
  const inactiveExecutions = filteredExecutions.filter(e => e.status !== 'active');

  if (loading) {
    return (
      <div className="flex items-center text-sm text-gray-400">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400 mr-2"></div>
        Loading workflows...
      </div>
    );
  }

  if (definitions.length === 0 && executions.length === 0) {
    return (
      <div className="flex items-center text-sm text-gray-400">
        <Workflow className="w-4 h-4 mr-2" />
        No workflows available
      </div>
    );
  }

  const handleDefinitionChange = (defId: string) => {
    const newDefId = defId || null;
    setSelectedDefinitionId(newDefId);
    onDefinitionChange?.(newDefId);
    // Clear execution selection when definition changes
    if (defId) {
      // Auto-select the first execution if there's only one
      const execs = executionsByDefinition[defId] || [];
      if (execs.length === 1) {
        selectExecution(execs[0].id);
      } else if (execs.length === 0) {
        // Definition has no executions - clear selection but disable auto-select
        selectExecution(null, true);
      } else if (selectedExecutionId) {
        // If current selection is not in this definition, clear it
        const currentExecInNewDef = execs.find(e => e.id === selectedExecutionId);
        if (!currentExecInNewDef) {
          selectExecution(null, true);
        }
      }
    } else {
      selectExecution(null);
    }
  };

  return (
    <div className="flex items-center gap-3">
      {selectedExecution && (
        <div className="flex items-center text-xs">
          {selectedExecution.status === 'active' && (
            <span className="flex items-center px-2 py-0.5 bg-green-50 text-green-700 rounded-full">
              <Activity className="w-3 h-3 mr-1" />
              {selectedExecution.stats?.active_tasks || 0} active
            </span>
          )}
        </div>
      )}

      {/* Workflow Type Selector */}
      <div className="relative">
        <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
          <Layers className="w-3 h-3" />
          <span>Type</span>
        </div>
        <select
          value={selectedDefinitionId || ''}
          onChange={(e) => handleDefinitionChange(e.target.value)}
          className="appearance-none bg-white border border-gray-200 text-gray-800 text-sm rounded-lg px-3 py-2 pr-8 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer min-w-[150px]"
        >
          <option value="">Select Type</option>
          {definitions.map((def) => (
            <option key={def.id} value={def.id}>
              {def.name} ({executionsByDefinition[def.id]?.length || 0})
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-2 bottom-2.5 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>

      {/* Workflow Execution Selector */}
      <div className="relative">
        <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
          <Workflow className="w-3 h-3" />
          <span>Execution</span>
        </div>
        <select
          value={selectedExecutionId || ''}
          onChange={(e) => selectExecution(e.target.value || null)}
          disabled={!selectedDefinitionId || filteredExecutions.length === 0}
          className="appearance-none bg-white border border-gray-200 text-gray-800 text-sm rounded-lg px-3 py-2 pr-8 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer min-w-[200px] disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          <option value="">
            {!selectedDefinitionId
              ? 'Select type first'
              : filteredExecutions.length === 0
                ? 'No executions'
                : 'Select Execution'}
          </option>
          {activeExecutions.length > 0 && (
            <optgroup label="Active">
              {activeExecutions.map((execution) => (
                <option key={execution.id} value={execution.id}>
                  {execution.description || `Execution ${execution.id.slice(0, 8)}`}
                </option>
              ))}
            </optgroup>
          )}
          {inactiveExecutions.length > 0 && (
            <optgroup label="Inactive">
              {inactiveExecutions.map((execution) => (
                <option key={execution.id} value={execution.id}>
                  {execution.description || `Execution ${execution.id.slice(0, 8)}`} ({execution.status})
                </option>
              ))}
            </optgroup>
          )}
        </select>
        <ChevronDown className="absolute right-2 bottom-2.5 w-4 h-4 text-gray-400 pointer-events-none" />
      </div>
    </div>
  );
};

export default WorkflowSelector;
