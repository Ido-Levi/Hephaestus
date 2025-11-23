import React, { useState, useRef, useEffect } from 'react';
import { useWorkflow } from '@/context/WorkflowContext';
import { ChevronDown, Workflow, Activity } from 'lucide-react';

export const ExecutionSelector: React.FC = () => {
  const { executions, selectedExecutionId, selectedExecution, selectExecution, loading } = useWorkflow();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

  if (loading) {
    return (
      <div className="flex items-center text-sm text-gray-400">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400 mr-2"></div>
        Loading...
      </div>
    );
  }

  if (executions.length === 0) {
    return (
      <div className="flex items-center text-sm text-gray-400">
        <Workflow className="w-4 h-4 mr-2" />
        No workflows available
      </div>
    );
  }

  // Separate active and inactive executions
  const activeExecutions = executions.filter(e => e.status === 'active');
  const inactiveExecutions = executions.filter(e => e.status !== 'active');

  return (
    <div className="flex items-center gap-3">
      {selectedExecution && selectedExecution.status === 'active' && (
        <span className="flex items-center px-2 py-0.5 bg-green-50 text-green-700 rounded-full text-xs">
          <Activity className="w-3 h-3 mr-1" />
          {selectedExecution.stats?.active_tasks || 0} active
        </span>
      )}

      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm min-w-[200px]"
        >
          <Workflow className="w-4 h-4 mr-2 text-gray-500" />
          <span className="flex-1 text-left text-sm text-gray-700 truncate">
            {selectedExecution?.description || selectedExecution?.definition_name || 'Select Workflow'}
          </span>
          <ChevronDown className={`w-4 h-4 ml-2 text-gray-500 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
        </button>

        {showDropdown && (
          <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
            {/* Active Executions */}
            {activeExecutions.length > 0 && (
              <>
                <div className="px-3 py-2 text-xs font-semibold text-gray-500 bg-gray-50 border-b">
                  Active ({activeExecutions.length})
                </div>
                {activeExecutions.map((execution) => (
                  <button
                    key={execution.id}
                    onClick={() => {
                      selectExecution(execution.id);
                      setShowDropdown(false);
                    }}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 ${
                      execution.id === selectedExecutionId ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="text-sm font-medium text-gray-800 truncate">
                      {execution.description || execution.definition_name || 'Unnamed Workflow'}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-2 mt-1">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 text-green-700">
                        {execution.status}
                      </span>
                      <span className="text-gray-400">{execution.definition_name}</span>
                      <span className="text-gray-400">•</span>
                      <span className="truncate">{execution.stats?.active_tasks || 0} tasks</span>
                    </div>
                  </button>
                ))}
              </>
            )}

            {/* Inactive Executions */}
            {inactiveExecutions.length > 0 && (
              <>
                <div className="px-3 py-2 text-xs font-semibold text-gray-500 bg-gray-50 border-b">
                  Completed/Failed ({inactiveExecutions.length})
                </div>
                {inactiveExecutions.map((execution) => (
                  <button
                    key={execution.id}
                    onClick={() => {
                      selectExecution(execution.id);
                      setShowDropdown(false);
                    }}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 ${
                      execution.id === selectedExecutionId ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="text-sm font-medium text-gray-800 truncate">
                      {execution.description || execution.definition_name || 'Unnamed Workflow'}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-2 mt-1">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        execution.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                        execution.status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {execution.status}
                      </span>
                      <span className="text-gray-400">{execution.definition_name}</span>
                    </div>
                  </button>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ExecutionSelector;
