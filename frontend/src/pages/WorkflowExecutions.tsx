import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWorkflow } from '@/context/WorkflowContext';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api';
import { WorkflowExecution } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';
import { Workflow, Plus, ExternalLink, X, Layers, CheckCircle2, Clock, AlertCircle, ListTodo, Rocket } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import TaskDetailModal from '@/components/TaskDetailModal';
import LaunchWorkflowModal from '@/components/LaunchWorkflowModal';

// Helper function
const formatDuration = (startTime: string) => {
  const start = new Date(startTime);
  const now = new Date();
  const diffMs = now.getTime() - start.getTime();
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

// Workflow Detail Modal
const WorkflowDetailModal: React.FC<{
  execution: WorkflowExecution;
  onClose: () => void;
}> = ({ execution, onClose }) => {
  const navigate = useNavigate();
  const { selectExecution } = useWorkflow();
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  // Fetch detailed execution info with phases
  const { data: details } = useQuery({
    queryKey: ['workflow-execution-detail', execution.id],
    queryFn: () => apiService.getWorkflowExecution(execution.id),
    refetchInterval: 5000,
  });

  // Fetch tasks for this workflow
  const { data: tasksResponse } = useQuery({
    queryKey: ['workflow-tasks', execution.id],
    queryFn: () => apiService.getTasks(0, 50, undefined, execution.id),
    refetchInterval: 5000,
  });

  const handleGoToOverview = () => {
    selectExecution(execution.id);
    navigate('/overview');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-lg shadow-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold text-gray-800">{execution.description || execution.definition_name}</h2>
            <p className="text-sm text-gray-500">{execution.definition_name}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Status and Stats */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-gray-800">{execution.stats?.total_tasks || 0}</div>
            <div className="text-xs text-gray-500">Total Tasks</div>
          </div>
          <div className="bg-green-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-600">{execution.stats?.done_tasks || 0}</div>
            <div className="text-xs text-gray-500">Completed</div>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-600">{execution.stats?.active_tasks || 0}</div>
            <div className="text-xs text-gray-500">Active</div>
          </div>
          <div className="bg-red-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-red-600">{execution.stats?.failed_tasks || 0}</div>
            <div className="text-xs text-gray-500">Failed</div>
          </div>
        </div>

        {/* Phases Summary */}
        {details?.phases && details.phases.length > 0 && (
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <Layers className="w-4 h-4" />
                Phases ({details.phases.length})
              </h3>
              <button
                onClick={() => {
                  selectExecution(execution.id);
                  navigate('/phases');
                  onClose();
                }}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                View Details →
              </button>
            </div>
            <div className="flex gap-2">
              {details.phases.map((phase: any) => (
                <div key={phase.id} className="flex-1 bg-gray-50 rounded-lg p-2 text-center">
                  <div className="text-xs font-medium text-gray-700">P{phase.order}</div>
                  <div className="text-lg font-bold text-gray-800">{phase.completed_tasks}/{phase.total_tasks}</div>
                  <div className="text-[10px] text-gray-500">{phase.name.substring(0, 10)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tasks List */}
        {tasksResponse && Array.isArray(tasksResponse) && tasksResponse.length > 0 && (
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <ListTodo className="w-4 h-4" />
                Tasks ({tasksResponse.length})
              </h3>
              <button
                onClick={() => {
                  selectExecution(execution.id);
                  navigate('/tasks');
                  onClose();
                }}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                View All →
              </button>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
              {tasksResponse.map((task: any) => (
                <div
                  key={task.id}
                  onClick={() => setSelectedTaskId(task.id)}
                  className="bg-gray-50 rounded-lg p-2 flex items-center justify-between hover:bg-blue-50 hover:border-blue-200 border border-transparent transition-colors cursor-pointer"
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-800 truncate">
                      {task.enriched_description || task.raw_description || task.description}
                    </div>
                    <div className="text-xs text-gray-500 flex items-center gap-2 mt-0.5">
                      <span>P{task.phase_id}</span>
                      <span>•</span>
                      <span className="capitalize">{task.priority}</span>
                    </div>
                  </div>
                  <div className="ml-2 flex-shrink-0">
                    <StatusBadge status={task.status} size="sm" />
                  </div>
                </div>
              ))}
            </div>

            {/* Task Detail Modal */}
            {selectedTaskId && (
              <TaskDetailModal
                taskId={selectedTaskId}
                onClose={() => setSelectedTaskId(null)}
                onNavigateToTask={(taskId) => {
                  setSelectedTaskId(taskId);
                }}
              />
            )}
          </div>
        )}

        {/* Info */}
        <div className="text-xs text-gray-500 mb-4">
          <div>Started: {new Date(execution.created_at).toLocaleString()}</div>
          <div>Duration: {formatDuration(execution.created_at)}</div>
          {execution.working_directory && <div>Working Dir: {execution.working_directory}</div>}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg transition-colors"
          >
            Close
          </button>
          <button
            onClick={handleGoToOverview}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Go to Overview
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// Workflow Card Component
const WorkflowCard: React.FC<{
  execution: WorkflowExecution;
  onSelect: () => void;
  onViewDetails: () => void;
  isSelected: boolean;
}> = ({ execution, onSelect, onViewDetails, isSelected }) => {
  const statusColors: Record<string, string> = {
    active: 'bg-green-500',
    paused: 'bg-yellow-500',
    completed: 'bg-blue-500',
    failed: 'bg-red-500',
  };

  const handleClick = () => {
    onSelect();
    onViewDetails();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className={`bg-white rounded-lg shadow-md p-4 border-2 transition-all cursor-pointer ${
        isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-transparent hover:border-gray-200'
      }`}
      onClick={handleClick}
    >
      {/* Header with status badge */}
      <div className="flex justify-between items-start mb-3">
        <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[execution.status]} text-white`}>
          {execution.status.toUpperCase()}
        </span>
        <span className="text-gray-500 text-sm">{execution.definition_name}</span>
      </div>

      {/* Title/Description */}
      <h3 className="text-lg font-semibold text-gray-800 mb-2">
        {execution.description || execution.definition_name}
      </h3>

      {/* Activity by Phase - show active work distribution */}
      <div className="mb-3">
        <div className="text-sm text-gray-500 mb-1">Current Activity</div>
        <div className="flex gap-2 text-xs">
          <span className="bg-gray-100 px-2 py-1 rounded text-gray-700">
            {execution.stats?.active_tasks || 0} active tasks
          </span>
          <span className="bg-gray-100 px-2 py-1 rounded text-gray-700">
            {execution.stats?.active_agents || 0} agents
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-2 mb-3 text-center">
        <div className="bg-gray-50 rounded p-2">
          <div className="text-lg font-bold text-gray-800">{execution.stats?.total_tasks || 0}</div>
          <div className="text-xs text-gray-500">Tasks</div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <div className="text-lg font-bold text-gray-800">{execution.stats?.active_agents || 0}</div>
          <div className="text-xs text-gray-500">Agents</div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <div className="text-lg font-bold text-gray-800">{execution.stats?.done_tasks || 0}</div>
          <div className="text-xs text-gray-500">Done</div>
        </div>
        <div className="bg-gray-50 rounded p-2">
          <div className="text-lg font-bold text-green-600">
            {formatDuration(execution.created_at)}
          </div>
          <div className="text-xs text-gray-500">Running</div>
        </div>
      </div>

      {/* Started time and view link */}
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>Started: {new Date(execution.created_at).toLocaleString()}</span>
        <span className="text-blue-600 flex items-center gap-1">
          View Details <ExternalLink className="w-3 h-3" />
        </span>
      </div>
    </motion.div>
  );
};

// Main Page Component
export default function WorkflowExecutions() {
  const { executions, definitions, loading, selectedExecutionId, selectExecution } = useWorkflow();
  const [showModal, setShowModal] = useState(false);
  const [filter, setFilter] = useState<'all' | 'active'>('all');
  const [detailExecution, setDetailExecution] = useState<WorkflowExecution | null>(null);

  const activeExecutions = executions.filter(e => e.status === 'active');
  const inactiveExecutions = executions.filter(e => e.status !== 'active');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center">
            <Workflow className="w-8 h-8 mr-3 text-blue-600" />
            Workflows
          </h1>
          <p className="text-gray-600 mt-1">Manage workflow definitions and executions</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
        >
          <Rocket className="w-4 h-4" />
          Launch Workflow
        </button>
      </div>

      {/* Workflow Definitions Section */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <Layers className="w-5 h-5 text-purple-600" />
          Loaded Workflow Definitions ({definitions.length})
        </h2>
        {definitions.length === 0 ? (
          <p className="text-gray-500 text-sm">No workflow definitions loaded</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {definitions.map((def) => (
              <div key={def.id} className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                <div className="font-medium text-gray-800">{def.name}</div>
                <div className="text-sm text-gray-600">{def.description}</div>
                <div className="text-xs text-purple-600 mt-1">
                  {def.phases_count} phases • ID: {def.id}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            filter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          All ({executions.length})
        </button>
        <button
          onClick={() => setFilter('active')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            filter === 'active'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Active ({activeExecutions.length})
        </button>
      </div>

      {/* Active Section */}
      {activeExecutions.length > 0 && (filter === 'all' || filter === 'active') && (
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Active ({activeExecutions.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeExecutions.map((execution) => (
              <WorkflowCard
                key={execution.id}
                execution={execution}
                onSelect={() => selectExecution(execution.id)}
                onViewDetails={() => setDetailExecution(execution)}
                isSelected={selectedExecutionId === execution.id}
              />
            ))}
          </div>
        </div>
      )}

      {/* Inactive Section */}
      {inactiveExecutions.length > 0 && filter === 'all' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-500 mb-4">
            Completed/Failed ({inactiveExecutions.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {inactiveExecutions.map((execution) => (
              <WorkflowCard
                key={execution.id}
                execution={execution}
                onSelect={() => selectExecution(execution.id)}
                onViewDetails={() => setDetailExecution(execution)}
                isSelected={selectedExecutionId === execution.id}
              />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {executions.length === 0 && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Workflow className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <div className="text-gray-500 mb-4">No workflow executions yet</div>
          <button
            onClick={() => setShowModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Start Your First Workflow
          </button>
        </div>
      )}

      {/* Launch Workflow Modal */}
      <LaunchWorkflowModal
        open={showModal}
        onClose={() => setShowModal(false)}
        onLaunch={(workflowId) => {
          // Select the newly launched workflow
          selectExecution(workflowId);
        }}
      />

      {/* Detail Modal */}
      <AnimatePresence>
        {detailExecution && (
          <WorkflowDetailModal
            execution={detailExecution}
            onClose={() => setDetailExecution(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
