import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { useWebSocket } from '@/context/WebSocketContext';
import { useWorkflow } from '@/context/WorkflowContext';
import {
  X,
  FileText,
  Clock,
  User,
  Bot,
  Copy,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  Settings,
  Link,
  Link2,
  ChevronDown,
  ChevronUp,
  Eye,
  GitBranch,
  Target,
  Navigation,
  ArrowUp,
  ArrowDown,
  GitPullRequest,
  Users,
  Zap,
  XCircle,
  RotateCcw,
  Ticket,
  Workflow
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

import { apiService } from '@/services/api';
import { Task, TaskFullDetails, TicketDetail } from '@/types';
import { useTaskRuntime } from '@/hooks/useTaskRuntime';
import StatusBadge from '@/components/StatusBadge';
import { PhaseBadge } from '@/components/PhaseBadge';
import RealTimeAgentOutput from '@/components/RealTimeAgentOutput';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import AlignmentGraph from '@/components/trajectory/AlignmentGraph';
import TaskBreadcrumb from '@/components/TaskBreadcrumb';
import TaskTreeStats from '@/components/TaskTreeStats';
import TicketCard from '@/components/tickets/TicketCard';
import TicketDetailModal from '@/components/tickets/TicketDetailModal';

interface TaskDetailModalProps {
  taskId: string | null;
  onClose: () => void;
  onNavigateToTask?: (taskId: string) => void;
  onNavigateToGraph?: (taskId: string) => void;
}

const TaskDetailModal: React.FC<TaskDetailModalProps> = ({
  taskId,
  onClose,
  onNavigateToTask,
  onNavigateToGraph,
}) => {
  const navigate = useNavigate();
  const { selectExecution } = useWorkflow();
  const [showAgentOutput, setShowAgentOutput] = useState(false);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState({
    prompts: true,
    phase: false,
    linkedTasks: false,
    trajectory: true,
    steering: false,
    duplicate: true,
    duplicatedFromThis: false,
    relatedTasks: false,
    relatedTickets: false,
  });

  const {
    data: taskDetails,
    isLoading,
    error
  } = useQuery<TaskFullDetails | null>({
    queryKey: ['task-full-details', taskId],
    queryFn: () => taskId ? apiService.getTaskFullDetails(taskId) : null,
    enabled: !!taskId,
    refetchInterval: 5000, // Refresh every 5 seconds for runtime updates
  });

  // Fetch guardian analyses for the task's agent
  const { data: guardianAnalyses } = useQuery({
    queryKey: ['guardian-analyses', taskDetails?.agent_info?.id],
    queryFn: () => taskDetails?.agent_info?.id ? apiService.getGuardianAnalyses(taskDetails.agent_info.id) : null,
    enabled: !!taskDetails?.agent_info?.id,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Fetch steering interventions for the task's agent
  const { data: steeringInterventions } = useQuery({
    queryKey: ['steering-interventions', taskDetails?.agent_info?.id],
    queryFn: () => taskDetails?.agent_info?.id ? apiService.getSteeringInterventions(taskDetails.agent_info.id) : null,
    enabled: !!taskDetails?.agent_info?.id,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Fetch related tickets
  const { data: relatedTickets, isLoading: relatedTicketsLoading } = useQuery<TicketDetail[]>({
    queryKey: ['related-tickets', taskDetails?.related_ticket_ids],
    queryFn: async () => {
      if (!taskDetails?.related_ticket_ids || taskDetails.related_ticket_ids.length === 0) {
        return [];
      }

      // Fetch each ticket's details
      const ticketPromises = taskDetails.related_ticket_ids.map(async (ticketId) => {
        try {
          const result = await apiService.getTicket(ticketId);
          return result.ticket;
        } catch (error) {
          console.error(`Failed to fetch ticket ${ticketId}:`, error);
          return null;
        }
      });

      const tickets = await Promise.all(ticketPromises);
      return tickets.filter((ticket): ticket is TicketDetail => ticket !== null);
    },
    enabled: !!taskDetails?.related_ticket_ids && taskDetails.related_ticket_ids.length > 0,
  });

  // Fetch original task if this is a duplicate
  const { data: originalTask } = useQuery<Task>({
    queryKey: ['task', taskDetails?.duplicate_of_task_id],
    queryFn: async () => {
      if (!taskDetails?.duplicate_of_task_id) {
        throw new Error('No duplicate ID');
      }
      return apiService.getTaskById(taskDetails.duplicate_of_task_id);
    },
    enabled: !!taskDetails?.duplicate_of_task_id && taskDetails?.status === 'duplicated',
  });

  const runtime = useTaskRuntime(
    taskDetails?.started_at || null,
    taskDetails?.completed_at || null,
    taskDetails?.runtime_seconds
  );

  const queryClient = useQueryClient();
  const { subscribe } = useWebSocket();

  // Subscribe to WebSocket events for real-time updates
  useEffect(() => {
    if (!taskDetails?.agent_info?.id) return;

    const agentId = taskDetails.agent_info.id;

    const unsubscribeGuardian = subscribe('guardian_analysis', (data: any) => {
      // Check if the analysis is for this task's agent
      if (data.agent_id === agentId) {
        queryClient.invalidateQueries({ queryKey: ['guardian-analyses', agentId] });
      }
    });

    const unsubscribeSteering = subscribe('steering_intervention', (data: any) => {
      // Check if the intervention is for this task's agent
      if (data.agent_id === agentId) {
        queryClient.invalidateQueries({ queryKey: ['steering-interventions', agentId] });
      }
    });

    return () => {
      unsubscribeGuardian();
      unsubscribeSteering();
    };
  }, [taskDetails?.agent_info?.id, subscribe, queryClient]);

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Could add toast notification here
      console.log(`Copied ${label} to clipboard`);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const copyTaskDetails = async () => {
    if (!taskDetails) return;

    const details = `
Task: ${taskDetails.id}
Status: ${taskDetails.status}
Priority: ${taskDetails.priority}
Runtime: ${runtime.runtimeDisplay}

Description:
${taskDetails.user_prompt}

Done Definition:
${taskDetails.done_definition}

${taskDetails.phase_info ? `
Phase: ${taskDetails.phase_info.name} (${taskDetails.phase_info.order})
Phase Description: ${taskDetails.phase_info.description}
` : ''}

${taskDetails.agent_info ? `
Agent: ${taskDetails.agent_info.id}
Agent Status: ${taskDetails.agent_info.status}
` : ''}

${taskDetails.child_tasks.length > 0 ? `
Linked Tasks (${taskDetails.child_tasks.length}):
${taskDetails.child_tasks.map((t: any) => `- ${t.description} (${t.status})`).join('\n')}
` : ''}
    `.trim();

    await copyToClipboard(details, 'task details');
  };

  const handleBumpPriority = async () => {
    if (!taskDetails) return;

    const confirmed = window.confirm(
      'Start this task immediately? This will bypass the agent limit (e.g., 2/2 → 3/2) and create a new agent right away.'
    );

    if (!confirmed) return;

    try {
      await apiService.bumpTaskPriority(taskDetails.id);
      // Close modal and let parent handle refresh
      onClose();
    } catch (error) {
      console.error('Failed to bump task priority:', error);
      alert('Failed to bump task priority. Please try again.');
    }
  };

  const handleTerminateAgent = async () => {
    if (!taskDetails?.agent_info) return;

    const confirmed = window.confirm(
      'Are you sure you want to terminate this agent? This will mark its task as failed and free up a slot for queued tasks.'
    );

    if (!confirmed) return;

    try {
      await apiService.terminateAgent(taskDetails.agent_info.id);
      // Close modal and let parent handle refresh
      onClose();
    } catch (error) {
      console.error('Failed to terminate agent:', error);
      alert('Failed to terminate agent. Please try again.');
    }
  };

  const handleRestartTask = async () => {
    if (!taskDetails) return;

    const confirmed = window.confirm(
      'Restart this task? This will:\n• Clear all completion data and trajectory analysis\n• Create a fresh agent (or queue if at capacity)\n• Start the task from scratch'
    );

    if (!confirmed) return;

    try {
      await apiService.restartTask(taskDetails.id);
      // Close modal and let parent handle refresh
      onClose();
    } catch (error) {
      console.error('Failed to restart task:', error);
      alert('Failed to restart task. Please try again.');
    }
  };

  if (!taskId) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                <div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-white">
                    Task Details
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 font-mono">
                    {taskDetails?.id || taskId}
                  </p>
                </div>

                {taskDetails && (
                  <div className="flex items-center space-x-2">
                    <StatusBadge status={taskDetails.status} />
                    {taskDetails.phase_info && (
                      <PhaseBadge
                        phaseOrder={taskDetails.phase_info.order}
                        phaseName={taskDetails.phase_info.name}
                        totalPhases={5}
                      />
                    )}
                    {taskDetails.ticket_id && (
                      <div className="flex items-center gap-1.5 bg-gradient-to-r from-purple-100 to-indigo-100 dark:from-purple-900/40 dark:to-indigo-900/40 text-purple-700 dark:text-purple-300 px-3 py-1.5 rounded-lg border border-purple-200 dark:border-purple-700 shadow-sm">
                        <Ticket className="w-3.5 h-3.5 flex-shrink-0" />
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTicketId(taskDetails.ticket_id!);
                          }}
                          className="text-xs font-mono hover:text-purple-900 dark:hover:text-purple-100 transition-colors font-medium"
                          title={`View ticket: ${taskDetails.ticket_id}`}
                        >
                          {taskDetails.ticket_id!.slice(0, 14)}...
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            copyToClipboard(taskDetails.ticket_id!, 'ticket ID');
                          }}
                          className="p-1 hover:bg-purple-200 dark:hover:bg-purple-800/50 rounded transition-colors flex-shrink-0"
                          title="Copy ticket ID"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2">
                {taskDetails?.status === 'queued' && (
                  <button
                    onClick={handleBumpPriority}
                    className="flex items-center px-3 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors text-sm"
                    title="Start immediately (bypasses agent limit)"
                  >
                    <Zap className="w-4 h-4 mr-1" />
                    Start Now
                  </button>
                )}

                {(taskDetails?.status === 'done' || taskDetails?.status === 'failed') && (
                  <button
                    onClick={handleRestartTask}
                    className="flex items-center px-3 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors text-sm"
                    title="Restart this task from scratch"
                  >
                    <RotateCcw className="w-4 h-4 mr-1" />
                    Restart Task
                  </button>
                )}

                {taskDetails?.agent_info && (
                  <>
                    <button
                      onClick={() => setShowAgentOutput(true)}
                      className="flex items-center px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
                      title="View live agent output"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      Live Output
                    </button>

                    {taskDetails.agent_info.status !== 'terminated' && (
                      <button
                        onClick={handleTerminateAgent}
                        className="flex items-center px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm"
                        title="Terminate this agent"
                      >
                        <XCircle className="w-4 h-4 mr-1" />
                        Terminate Agent
                      </button>
                    )}
                  </>
                )}

                <button
                  onClick={copyTaskDetails}
                  className="p-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 transition-colors"
                  title="Copy task details"
                >
                  <Copy className="w-4 h-4" />
                </button>

                {onNavigateToGraph && (
                  <button
                    onClick={() => onNavigateToGraph(taskId)}
                    className="p-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 transition-colors"
                    title="View in graph"
                  >
                    <GitBranch className="w-4 h-4" />
                  </button>
                )}

                <button
                  onClick={onClose}
                  className="p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Breadcrumb Navigation */}
            {taskDetails && (
              <div className="mt-3">
                <TaskBreadcrumb
                  currentTaskId={taskId}
                  onNavigateToTask={(id) => onNavigateToTask?.(id)}
                />
              </div>
            )}

            {/* Runtime and Basic Info */}
            {taskDetails && (
              <div className="mt-3 grid grid-cols-4 gap-4 text-sm">
                <div className="flex items-center text-gray-600 dark:text-gray-400">
                  <Clock className="w-4 h-4 mr-2" />
                  <span className={runtime.isRunning ? 'text-green-600 dark:text-green-400 font-medium' : ''}>
                    {runtime.runtimeDisplay}
                  </span>
                  {runtime.isRunning && (
                    <div className="w-2 h-2 bg-green-400 rounded-full ml-2 animate-pulse" />
                  )}
                </div>

                <div className="text-gray-600 dark:text-gray-400">
                  Priority: <span className={`font-medium ${
                    taskDetails.priority === 'high' ? 'text-red-600' :
                    taskDetails.priority === 'medium' ? 'text-yellow-600' : 'text-green-600'
                  }`}>{taskDetails.priority}</span>
                </div>

                <div className="text-gray-600 dark:text-gray-400">
                  Created: {formatDistanceToNow(new Date(taskDetails.created_at), { addSuffix: true })}
                </div>

                {taskDetails.workflow_id && (
                  <div className="flex items-center text-gray-600 dark:text-gray-400 col-span-4">
                    <Workflow className="w-4 h-4 mr-2 text-blue-500" />
                    <span className="text-xs">Workflow: </span>
                    <button
                      onClick={() => {
                        selectExecution(taskDetails.workflow_id!);
                        navigate('/workflows');
                        onClose();
                      }}
                      className="ml-1 text-xs font-mono text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                      title={`Go to workflow: ${taskDetails.workflow_id}`}
                    >
                      {taskDetails.workflow_id.slice(0, 12)}...
                      <ExternalLink className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => copyToClipboard(taskDetails.workflow_id!, 'workflow ID')}
                      className="ml-2 text-gray-400 hover:text-gray-600"
                      title="Copy workflow ID"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                  </div>
                )}

                {taskDetails.estimated_complexity && (
                  <div className="text-gray-600 dark:text-gray-400">
                    Complexity: {taskDetails.estimated_complexity}/10
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {isLoading && (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              </div>
            )}

            {error && (
              <div className="p-6 text-center">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <p className="text-red-600 dark:text-red-400">Failed to load task details</p>
              </div>
            )}

            {taskDetails && (
              <div className="p-6 space-y-6">
                {/* Duplicate Information - Sticky banner when THIS task is duplicated */}
                {taskDetails.status === 'duplicated' && taskDetails.duplicate_of_task_id && (
                  <div className="sticky top-0 z-10 -mx-6 -mt-6 mb-4 px-6 py-4 bg-purple-50 dark:bg-purple-900/20 border-b-2 border-purple-200 dark:border-purple-700">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="w-5 h-5 text-purple-600 dark:text-purple-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <h4 className="font-medium text-purple-800 dark:text-purple-200 mb-2">
                          This task is a duplicate
                        </h4>

                        <div className="space-y-3">
                          {/* Similarity Score */}
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-600 dark:text-gray-400">Similarity:</span>
                            <div className="flex items-center space-x-2">
                              <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                                <div
                                  className="h-full bg-purple-600 dark:bg-purple-400"
                                  style={{ width: `${(taskDetails.similarity_score || 0) * 100}%` }}
                                />
                              </div>
                              <span className="text-sm font-bold text-purple-700 dark:text-purple-300">
                                {((taskDetails.similarity_score || 0) * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>

                          {/* Original Task */}
                          {originalTask && (
                            <div
                              className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-purple-200 dark:border-purple-600 cursor-pointer hover:shadow-md transition-all"
                              onClick={() => onNavigateToTask?.(originalTask.id)}
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <span className="text-xs font-medium text-purple-600 dark:text-purple-400">Original Task:</span>
                                    <StatusBadge status={originalTask.status} size="sm" />
                                  </div>
                                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                                    {originalTask.description || 'No description'}
                                  </p>
                                  <div className="flex items-center space-x-3 text-xs text-gray-500">
                                    <span>ID: {originalTask.id.slice(0, 8)}...</span>
                                    <span>Created {formatDistanceToNow(new Date(originalTask.created_at), { addSuffix: true })}</span>
                                    {originalTask.assigned_agent_id && (
                                      <span>Agent: {originalTask.assigned_agent_id.slice(0, 8)}...</span>
                                    )}
                                  </div>
                                </div>
                                <ExternalLink className="w-4 h-4 text-purple-600 dark:text-purple-400 ml-3" />
                              </div>
                            </div>
                          )}

                          <div className="p-3 bg-purple-100 dark:bg-purple-800/30 rounded-lg">
                            <p className="text-sm text-purple-700 dark:text-purple-300">
                              This task was not created because it was determined to be a duplicate of the original task shown above.
                              Tasks are considered duplicates when their semantic similarity exceeds the configured threshold.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* System & User Prompts */}
                <div className="space-y-4">
                  <button
                    onClick={() => toggleSection('prompts')}
                    className="flex items-center space-x-2 text-lg font-semibold text-gray-800 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    <Settings className="w-5 h-5" />
                    <span>Prompts</span>
                    {expandedSections.prompts ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  <AnimatePresence>
                    {expandedSections.prompts && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="grid grid-cols-1 lg:grid-cols-2 gap-4"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center">
                              <User className="w-4 h-4 mr-2" />
                              User Prompt
                            </h4>
                            <button
                              onClick={() => copyToClipboard(taskDetails.user_prompt, 'user prompt')}
                              className="p-1 rounded text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          </div>
                          <div className="h-32 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border overflow-y-auto">
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                              {taskDetails.user_prompt}
                            </p>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center">
                              <Bot className="w-4 h-4 mr-2" />
                              System Prompt
                            </h4>
                            <button
                              onClick={() => copyToClipboard(taskDetails.system_prompt || 'No system prompt', 'system prompt')}
                              className="p-1 rounded text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          </div>
                          <div className="h-32 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border overflow-y-auto">
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                              {taskDetails.system_prompt || 'No system prompt available'}
                            </p>
                          </div>
                        </div>

                        <div className="lg:col-span-2 space-y-2">
                          <div className="flex items-center justify-between">
                            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center">
                              <CheckCircle className="w-4 h-4 mr-2" />
                              Done Definition
                            </h4>
                            <button
                              onClick={() => copyToClipboard(taskDetails.done_definition, 'done definition')}
                              className="p-1 rounded text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                            >
                              <Copy className="w-3 h-3" />
                            </button>
                          </div>
                          <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-700">
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                              {taskDetails.done_definition}
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Trajectory Analysis - Moved above Phase Information */}
                {guardianAnalyses && guardianAnalyses.length > 0 && (
                  <div className="space-y-4">
                    <button
                      onClick={() => toggleSection('trajectory')}
                      className="flex items-center space-x-2 text-lg font-semibold text-gray-800 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      <Target className="w-5 h-5" />
                      <span>Trajectory Analysis</span>
                      {expandedSections.trajectory ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.trajectory && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="space-y-4"
                        >
                          {/* Alignment Graph Over Time */}
                          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border">
                            <h4 className="font-medium text-gray-800 dark:text-gray-200 mb-3">Alignment Score Over Time</h4>
                            <AlignmentGraph trajectoryHistory={guardianAnalyses.slice().reverse().map((analysis: any) => ({
                              timestamp: analysis.timestamp,
                              alignment_score: analysis.alignment_score || 0,
                              current_phase: analysis.current_phase,
                              phase_changed: analysis.phase_changed || false
                            }))} />
                          </div>

                          {/* Current Alignment */}
                          {guardianAnalyses[0] && (
                            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border">
                              <div className="flex items-center justify-between mb-3">
                                <h4 className="font-medium text-gray-800 dark:text-gray-200">Current Alignment</h4>
                                <span className={cn(
                                  "text-lg font-bold",
                                  (guardianAnalyses[0].alignment_score || 0) > 0.8 ? "text-green-600" :
                                  (guardianAnalyses[0].alignment_score || 0) > 0.4 ? "text-yellow-600" :
                                  "text-red-600"
                                )}>
                                  {Math.round((guardianAnalyses[0].alignment_score || 0) * 100)}%
                                </span>
                              </div>
                              <Progress
                                value={(guardianAnalyses[0].alignment_score || 0) * 100}
                                className={cn(
                                  "h-2 mb-3",
                                  (guardianAnalyses[0].alignment_score || 0) > 0.8 ? "[&>div]:bg-green-500" :
                                  (guardianAnalyses[0].alignment_score || 0) > 0.4 ? "[&>div]:bg-yellow-500" :
                                  "[&>div]:bg-red-500"
                                )}
                              />
                              <div className="space-y-2 text-sm">
                                <div>
                                  <span className="text-gray-500 dark:text-gray-400">Phase:</span>
                                  <span className="ml-2 font-medium">{guardianAnalyses[0].current_phase || 'Unknown'}</span>
                                </div>
                                <div>
                                  <span className="text-gray-500 dark:text-gray-400">Accumulated Goal:</span>
                                  <div className="mt-1 text-gray-700 dark:text-gray-300">
                                    {guardianAnalyses[0].accumulated_goal || 'Not specified'}
                                  </div>
                                </div>
                                <div>
                                  <span className="text-gray-500 dark:text-gray-400">Current Focus:</span>
                                  <div className="mt-1 text-gray-700 dark:text-gray-300">
                                    {guardianAnalyses[0].current_focus || 'Not specified'}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Trajectory History */}
                          <div className="space-y-2">
                            <h4 className="font-medium text-gray-800 dark:text-gray-200">Trajectory History</h4>
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                              {guardianAnalyses.map((analysis: any) => (
                                <div
                                  key={analysis.id}
                                  className={cn(
                                    "border rounded-lg p-3 transition-colors",
                                    analysis.needs_steering ? "border-yellow-300 bg-yellow-50 dark:bg-yellow-900/20" : "border-gray-200"
                                  )}
                                >
                                  <div className="flex items-start justify-between mb-1">
                                    <div className="flex items-center space-x-2">
                                      {analysis.trajectory_aligned ? (
                                        <CheckCircle className="w-4 h-4 text-green-600" />
                                      ) : analysis.alignment_score > 0.5 ? (
                                        <AlertCircle className="w-4 h-4 text-yellow-600" />
                                      ) : (
                                        <AlertCircle className="w-4 h-4 text-red-600" />
                                      )}
                                      <span className="text-xs text-gray-500">
                                        {formatDistanceToNow(new Date(analysis.timestamp), { addSuffix: true })}
                                      </span>
                                    </div>
                                    <Badge
                                      variant="outline"
                                      className={cn(
                                        "text-xs",
                                        analysis.alignment_score > 0.8 ? "bg-green-100 text-green-700" :
                                        analysis.alignment_score > 0.4 ? "bg-yellow-100 text-yellow-700" :
                                        "bg-red-100 text-red-700"
                                      )}
                                    >
                                      {Math.round((analysis.alignment_score || 0) * 100)}%
                                    </Badge>
                                  </div>
                                  <p className="text-sm text-gray-700 dark:text-gray-300">
                                    {analysis.trajectory_summary || analysis.progress_assessment || 'No summary available'}
                                  </p>
                                  {analysis.needs_steering && (
                                    <div className="mt-2 flex items-center text-xs text-yellow-600">
                                      <Navigation className="w-3 h-3 mr-1" />
                                      <span>Steering needed: {analysis.steering_type}</span>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Phase Information */}
                {taskDetails.phase_info && (
                  <div className="space-y-4">
                    <button
                      onClick={() => toggleSection('phase')}
                      className="flex items-center space-x-2 text-lg font-semibold text-gray-800 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      <div className="w-5 h-5 bg-blue-500 rounded flex items-center justify-center text-white text-xs font-bold">
                        {taskDetails.phase_info.order}
                      </div>
                      <span>Phase Information</span>
                      {expandedSections.phase ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.phase && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-700"
                        >
                          <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
                            Phase {taskDetails.phase_info.order}: {taskDetails.phase_info.name}
                          </h4>
                          <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
                            {taskDetails.phase_info.description}
                          </p>

                          {taskDetails.phase_info.done_definitions.length > 0 && (
                            <div>
                              <p className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
                                Done Definitions:
                              </p>
                              <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                                {taskDetails.phase_info.done_definitions.map((def: any, index: any) => (
                                  <li key={index} className="flex items-start">
                                    <span className="text-blue-500 mr-2">•</span>
                                    <span>{def}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {taskDetails.phase_info.additional_notes && (
                            <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-600">
                              <p className="text-sm text-blue-700 dark:text-blue-300">
                                <strong>Notes:</strong> {taskDetails.phase_info.additional_notes}
                              </p>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Steering Interventions */}
                {steeringInterventions && steeringInterventions.length > 0 && (
                  <div className="space-y-4">
                    <button
                      onClick={() => toggleSection('steering')}
                      className="flex items-center space-x-2 text-lg font-semibold text-gray-800 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      <Navigation className="w-5 h-5" />
                      <span>Steering Interventions ({steeringInterventions.length})</span>
                      {expandedSections.steering ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.steering && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="space-y-2"
                        >
                          <div className="space-y-2 max-h-64 overflow-y-auto">
                            {steeringInterventions.map((intervention: any) => (
                              <div
                                key={intervention.id}
                                className={cn(
                                  "border rounded-lg p-3",
                                  intervention.was_successful === false ? "border-red-300 bg-red-50 dark:bg-red-900/20" : "border-gray-200"
                                )}
                              >
                                <div className="flex items-start justify-between mb-2">
                                  <div className="flex items-center space-x-2">
                                    <Target className="w-4 h-4 text-blue-600" />
                                    <span className="text-xs text-gray-500">
                                      {formatDistanceToNow(new Date(intervention.timestamp), { addSuffix: true })}
                                    </span>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    {intervention.steering_type && (
                                      <Badge variant="outline" className="text-xs">
                                        {intervention.steering_type}
                                      </Badge>
                                    )}
                                    {intervention.was_successful !== undefined && (
                                      intervention.was_successful ? (
                                        <CheckCircle className="w-4 h-4 text-green-600" />
                                      ) : (
                                        <X className="w-4 h-4 text-red-600" />
                                      )
                                    )}
                                  </div>
                                </div>
                                <p className="text-sm text-gray-700 dark:text-gray-300">
                                  {intervention.message}
                                </p>
                              </div>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Related Tasks - Moved after Trajectory Analysis */}
                {((taskDetails.related_tasks_details && taskDetails.related_tasks_details.length > 0) ||
                  (taskDetails.related_task_ids && taskDetails.related_task_ids.length > 0)) && (
                  <div className="space-y-4">
                    <button
                      onClick={() => toggleSection('relatedTasks')}
                      className="flex items-center space-x-2 text-lg font-semibold text-gray-800 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors w-full"
                    >
                      <Link className="w-5 h-5" />
                      <span>
                        Related Tasks ({taskDetails.related_tasks_details?.length || taskDetails.related_task_ids?.length || 0})
                      </span>
                      {expandedSections.relatedTasks ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.relatedTasks && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="space-y-3"
                        >
                          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-700">
                            <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
                              These tasks have similar content but are not duplicates:
                            </p>
                            <div className="space-y-2">
                              {taskDetails.related_tasks_details ? (
                                // New format with similarity scores
                                taskDetails.related_tasks_details.map((relatedTask: any) => (
                                <div
                                  key={relatedTask.id}
                                  className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 transition-all cursor-pointer"
                                  onClick={() => onNavigateToTask?.(relatedTask.id)}
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <p className="text-sm text-gray-800 dark:text-gray-200 mb-1">
                                        {relatedTask.description}
                                      </p>
                                      <div className="flex items-center space-x-3 text-xs text-gray-600 dark:text-gray-400">
                                        <StatusBadge status={relatedTask.status as any} size="sm" />
                                        {relatedTask.similarity_score > 0 && (
                                          <span className="flex items-center bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full">
                                            <span className="font-medium">{(relatedTask.similarity_score * 100).toFixed(1)}%</span> similar
                                          </span>
                                        )}
                                        {relatedTask.created_at && (
                                          <span className="flex items-center">
                                            <Clock className="w-3 h-3 mr-1" />
                                            {formatDistanceToNow(new Date(relatedTask.created_at), { addSuffix: true })}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                    <ExternalLink className="w-4 h-4 text-gray-400 ml-2 mt-1" />
                                  </div>
                                </div>
                              ))
                              ) : (
                                // Old format with just IDs
                                taskDetails.related_task_ids?.map((relatedId: string) => (
                                  <button
                                    key={relatedId}
                                    onClick={() => onNavigateToTask?.(relatedId)}
                                    className="w-full p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 transition-all text-left"
                                  >
                                    <div className="flex items-center justify-between">
                                      <span className="text-sm text-gray-800 dark:text-gray-200">
                                        Task ID: {relatedId.slice(0, 8)}...
                                      </span>
                                      <ExternalLink className="w-4 h-4 text-gray-400" />
                                    </div>
                                  </button>
                                ))
                              )}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Linked Tasks */}
                {(taskDetails.parent_task || taskDetails.child_tasks.length > 0) && (
                  <div className="space-y-4">
                    <button
                      onClick={() => toggleSection('linkedTasks')}
                      className="flex items-center space-x-2 text-lg font-semibold text-gray-800 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors w-full"
                    >
                      <GitPullRequest className="w-5 h-5" />
                      <span>Task Hierarchy</span>
                      <div className="flex items-center space-x-2 ml-2">
                        {taskDetails.parent_task && (
                          <span className="flex items-center text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                            <ArrowUp className="w-3 h-3 mr-1" />
                            1 parent
                          </span>
                        )}
                        {taskDetails.child_tasks.length > 0 && (
                          <span className="flex items-center text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                            <ArrowDown className="w-3 h-3 mr-1" />
                            {taskDetails.child_tasks.length} {taskDetails.child_tasks.length === 1 ? 'child' : 'children'}
                          </span>
                        )}
                      </div>
                      {expandedSections.linkedTasks ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.linkedTasks && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="space-y-3"
                        >
                          {taskDetails.parent_task && (
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
                                <ArrowUp className="w-4 h-4 mr-2 text-blue-600" />
                                Parent Task
                              </h4>
                              <div
                                className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border-2 border-blue-200 dark:border-blue-700 hover:border-blue-400 dark:hover:border-blue-500 transition-all cursor-pointer shadow-sm hover:shadow-md"
                                onClick={() => onNavigateToTask?.(taskDetails.parent_task!.id)}
                              >
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-1">
                                      {taskDetails.parent_task.description}
                                    </p>
                                    <div className="flex items-center space-x-3 text-xs text-gray-600 dark:text-gray-400">
                                      <span className="flex items-center">
                                        <Clock className="w-3 h-3 mr-1" />
                                        Created {taskDetails.parent_task.created_at
                                          ? formatDistanceToNow(new Date(taskDetails.parent_task.created_at), { addSuffix: true })
                                          : 'unknown time ago'
                                        }
                                      </span>
                                      <span className="text-blue-600 dark:text-blue-400">
                                        This task was created by parent
                                      </span>
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-2 ml-4">
                                    <StatusBadge status={taskDetails.parent_task.status as any} size="sm" />
                                    <div className="p-1.5 bg-blue-100 dark:bg-blue-900/50 rounded-full">
                                      <ExternalLink className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {taskDetails.child_tasks.length > 0 && (
                            <div>
                              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
                                <ArrowDown className="w-4 h-4 mr-2 text-green-600" />
                                Child Tasks ({taskDetails.child_tasks.length})
                                <span className="ml-2 text-xs text-gray-500 font-normal">
                                  Tasks created by this agent
                                </span>
                              </h4>
                              <div className="grid gap-2">
                                {taskDetails.child_tasks.map((child: any) => (
                                  <div
                                    key={child.id}
                                    className="p-3 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/10 dark:to-emerald-900/10 rounded-lg border border-green-200 dark:border-green-800 hover:border-green-400 dark:hover:border-green-600 transition-all cursor-pointer hover:shadow-sm"
                                    onClick={() => onNavigateToTask?.(child.id)}
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex-1">
                                        <p className="text-sm font-medium text-gray-800 dark:text-gray-200 flex items-center">
                                          <Users className="w-3 h-3 mr-2 text-green-600" />
                                          {child.description}
                                        </p>
                                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                          Created {formatDistanceToNow(new Date(child.created_at!), { addSuffix: true })}
                                        </p>
                                      </div>
                                      <div className="flex items-center space-x-2">
                                        <span className={`text-xs px-2 py-1 rounded ${
                                          child.priority === 'high' ? 'bg-red-100 text-red-700' :
                                          child.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                          'bg-gray-100 text-gray-700'
                                        }`}>
                                          {child.priority}
                                        </span>
                                        <StatusBadge status={child.status as any} size="sm" />
                                        <div className="p-1 bg-green-100 dark:bg-green-900/50 rounded-full">
                                          <ExternalLink className="w-3 h-3 text-green-600 dark:text-green-400" />
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Task Tree Statistics */}
                          <TaskTreeStats
                            taskId={taskDetails.id}
                            parentTaskId={taskDetails.parent_task?.id}
                            childTasksCount={taskDetails.child_tasks.length}
                          />
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Tasks Duplicated From This Task - Collapsible for normal tasks */}
                {taskDetails.duplicated_tasks && taskDetails.duplicated_tasks.length > 0 && taskDetails.status !== 'duplicated' && (
                  <div className="space-y-4">
                    <button
                      onClick={() => toggleSection('duplicatedFromThis')}
                      className="flex items-center space-x-2 text-lg font-semibold text-gray-800 dark:text-white hover:text-purple-600 dark:hover:text-purple-400 transition-colors w-full"
                    >
                      <Link2 className="w-5 h-5" />
                      <span>Duplicated Tasks ({taskDetails.duplicated_tasks.length})</span>
                      {expandedSections.duplicatedFromThis ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.duplicatedFromThis && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="space-y-3"
                        >
                          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-700">
                            <p className="text-sm text-purple-700 dark:text-purple-300 mb-3">
                              The following tasks were marked as duplicates of this task:
                            </p>
                            <div className="space-y-2">
                              {taskDetails.duplicated_tasks.map((dupTask) => (
                                <div
                                  key={dupTask.id}
                                  className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-purple-200 dark:border-purple-600 cursor-pointer hover:shadow-md transition-all"
                                  onClick={() => onNavigateToTask?.(dupTask.id)}
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <div className="flex items-center space-x-2 mb-1">
                                        <StatusBadge status="duplicated" size="sm" />
                                        <span className="text-sm font-bold text-purple-700 dark:text-purple-300">
                                          {((dupTask.similarity_score || 0) * 100).toFixed(1)}% similar
                                        </span>
                                      </div>
                                      <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                                        {dupTask.description}
                                      </p>
                                      <div className="flex items-center space-x-3 text-xs text-gray-500">
                                        <span>ID: {dupTask.id.slice(0, 8)}...</span>
                                        <span>Created {formatDistanceToNow(new Date(dupTask.created_at), { addSuffix: true })}</span>
                                        {dupTask.created_by_agent_id && (
                                          <span>By agent: {dupTask.created_by_agent_id.slice(0, 8)}...</span>
                                        )}
                                      </div>
                                    </div>
                                    <ExternalLink className="w-4 h-4 text-purple-600 dark:text-purple-400 ml-3" />
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Related Tickets */}
                {taskDetails.related_ticket_ids && taskDetails.related_ticket_ids.length > 0 && (
                  <div className="space-y-4">
                    <button
                      onClick={() => toggleSection('relatedTickets')}
                      className="flex items-center space-x-2 text-lg font-semibold text-gray-800 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors w-full"
                    >
                      <Ticket className="w-5 h-5" />
                      <span>Related Tickets ({taskDetails.related_ticket_ids.length})</span>
                      {expandedSections.relatedTickets ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
                    </button>

                    <AnimatePresence>
                      {expandedSections.relatedTickets && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="space-y-3"
                        >
                          {relatedTicketsLoading ? (
                            <div className="flex items-center justify-center py-8">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                            </div>
                          ) : relatedTickets && relatedTickets.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                              {relatedTickets.map((ticket) => (
                                <TicketCard
                                  key={ticket.id}
                                  ticket={ticket}
                                  onClick={() => setSelectedTicketId(ticket.id)}
                                  draggable={false}
                                />
                              ))}
                            </div>
                          ) : (
                            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                              <p className="text-sm">No related tickets found</p>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}

                {/* Additional Information */}
                {(taskDetails.completion_notes || taskDetails.failure_reason) && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {taskDetails.completion_notes ? 'Completion Notes' : 'Failure Reason'}
                    </h4>
                    <div className={`p-3 rounded-lg ${
                      taskDetails.completion_notes
                        ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700'
                        : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700'
                    }`}>
                      <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                        {taskDetails.completion_notes || taskDetails.failure_reason}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>

      {/* Agent Output Modal */}
      {showAgentOutput && taskDetails?.agent_info && (
        <RealTimeAgentOutput
          agent={{
            id: taskDetails.agent_info.id,
            status: taskDetails.agent_info.status as any,
            cli_type: taskDetails.agent_info.cli_type,
            current_task_id: taskDetails.id,
            tmux_session_name: null,
            health_check_failures: 0,
            created_at: taskDetails.agent_info.created_at || '',
            last_activity: taskDetails.agent_info.last_activity,
          }}
          onClose={() => setShowAgentOutput(false)}
        />
      )}

      {/* Ticket Detail Modal */}
      {selectedTicketId && (
        <TicketDetailModal
          ticketId={selectedTicketId}
          onClose={() => setSelectedTicketId(null)}
        />
      )}
    </AnimatePresence>
  );
};

export default TaskDetailModal;