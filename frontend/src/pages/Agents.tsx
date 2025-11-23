import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Bot, Terminal, Activity, AlertCircle, FileText, Clock, MessageCircle, XCircle } from 'lucide-react';
import { apiService } from '@/services/api';
import { Agent } from '@/types';
import StatusBadge from '@/components/StatusBadge';
import RealTimeAgentOutput from '@/components/RealTimeAgentOutput';
import TaskDetailModal from '@/components/TaskDetailModal';
import SendMessageDialog from '@/components/SendMessageDialog';
import { useWebSocket } from '@/context/WebSocketContext';
import { formatDistanceToNow } from 'date-fns';

const AgentCard: React.FC<{
  agent: Agent;
  onClick: () => void;
  onViewTask?: (taskId: string) => void;
  onSendMessage?: () => void;
  onTerminate?: () => void;
  isActive?: boolean;
}> = ({
  agent,
  onClick,
  onViewTask,
  onSendMessage,
  onTerminate,
  isActive,
}) => {
  const healthPercentage = Math.max(0, 100 - agent.health_check_failures * 33);

  // Format runtime for current task
  const formatRuntime = (seconds: number) => {
    if (seconds === 0) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  const handleTaskClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (agent.current_task && onViewTask) {
      onViewTask(agent.current_task.id);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      className={`bg-white rounded-lg shadow-md p-6 transition-all ${
        isActive ? 'ring-2 ring-primary animate-pulse-slow' : ''
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center">
          <Bot className="w-6 h-6 text-gray-600 mr-2" />
          <div>
            <p className="font-semibold text-gray-800">Agent {agent.id.substring(0, 8)}</p>
            <p className="text-xs text-gray-500">{agent.cli_type}</p>
          </div>
        </div>
        <StatusBadge status={agent.status} size="sm" />
      </div>

      {/* Current Task Section */}
      {agent.current_task ? (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <FileText className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">Working on Task</span>
                {agent.current_task.phase_info && (
                  <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                    Phase {agent.current_task.phase_info.order}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-700 line-clamp-2 mb-2">
                {agent.current_task.description}
              </p>
              <div className="flex items-center space-x-4 text-xs text-gray-600">
                <div className="flex items-center">
                  <span className={`inline-block w-2 h-2 rounded-full mr-1 ${
                    agent.current_task.status === 'in_progress' ? 'bg-yellow-400' :
                    agent.current_task.status === 'done' ? 'bg-green-400' :
                    agent.current_task.status === 'failed' ? 'bg-red-400' : 'bg-gray-400'
                  }`} />
                  {agent.current_task.status.replace('_', ' ')}
                </div>
                <div className="flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  {formatRuntime(agent.current_task.runtime_seconds)}
                  {agent.current_task.status === 'in_progress' && (
                    <span className="ml-1 text-green-600">• running</span>
                  )}
                </div>
                <div className={`px-1.5 py-0.5 rounded text-xs ${
                  agent.current_task.priority === 'high' ? 'bg-red-100 text-red-700' :
                  agent.current_task.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {agent.current_task.priority}
                </div>
              </div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex space-x-2">
              <button
                onClick={handleTaskClick}
                className="flex-1 px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors"
              >
                <FileText className="w-3 h-3 inline mr-1" />
                View Task
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onClick();
                }}
                className="flex-1 px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition-colors"
              >
                <Terminal className="w-3 h-3 inline mr-1" />
                View Output
              </button>
            </div>
            {agent.status !== 'terminated' && (
              <>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSendMessage?.();
                  }}
                  className="w-full px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition-colors"
                >
                  <MessageCircle className="w-3 h-3 inline mr-1" />
                  Send Message
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onTerminate?.();
                  }}
                  className="w-full px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition-colors"
                >
                  <XCircle className="w-3 h-3 inline mr-1" />
                  Terminate Agent
                </button>
              </>
            )}
          </div>
        </div>
      ) : (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center text-gray-500 text-sm mb-2">
            <FileText className="w-4 h-4 mr-2" />
            No current task
          </div>
          <div className="space-y-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onClick();
              }}
              className="w-full px-3 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-700 transition-colors"
            >
              <Terminal className="w-3 h-3 inline mr-1" />
              View Output
            </button>
            {agent.status !== 'terminated' && (
              <>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSendMessage?.();
                  }}
                  className="w-full px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 transition-colors"
                >
                  <MessageCircle className="w-3 h-3 inline mr-1" />
                  Send Message
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onTerminate?.();
                  }}
                  className="w-full px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition-colors"
                >
                  <XCircle className="w-3 h-3 inline mr-1" />
                  Terminate Agent
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Agent Health and Stats */}
      <div className="space-y-3">
        <div>
          <p className="text-xs text-gray-600 mb-1">Health</p>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${healthPercentage}%` }}
              className={`h-2 rounded-full ${
                healthPercentage > 66
                  ? 'bg-green-500'
                  : healthPercentage > 33
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
            />
          </div>
        </div>

        {agent.last_activity && (
          <div className="flex items-center text-xs text-gray-500">
            <Activity className="w-3 h-3 mr-1" />
            {agent.status === 'working' ? 'Active' : 'Idle'} for{' '}
            {formatDistanceToNow(new Date(agent.last_activity))}
          </div>
        )}

        {agent.tmux_session_name && (
          <div className="flex items-center text-xs text-gray-500">
            <Terminal className="w-3 h-3 mr-1" />
            {agent.tmux_session_name}
          </div>
        )}
      </div>
    </motion.div>
  );
};


const Agents: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [messageAgent, setMessageAgent] = useState<Agent | null>(null);
  const [activeAgentIds, setActiveAgentIds] = useState<Set<string>>(new Set());
  const { subscribe } = useWebSocket();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['agents'],
    queryFn: apiService.getAgents,
    refetchInterval: 5000,
  });

  useEffect(() => {
    if (data) {
      setAgents(data);
      // Track active agents
      const active = new Set(
        data.filter(a => a.status === 'working').map(a => a.id)
      );
      setActiveAgentIds(active);
    }
  }, [data]);

  // Subscribe to WebSocket updates
  useEffect(() => {
    const unsubscribeCreated = subscribe('agent_created', () => {
      refetch();
    });

    const unsubscribeStatus = subscribe('agent_status_changed', (message) => {
      setAgents(prev =>
        prev.map(agent =>
          agent.id === message.agent_id
            ? { ...agent, status: message.status }
            : agent
        )
      );

      if (message.status === 'working') {
        setActiveAgentIds(prev => new Set(prev).add(message.agent_id));
      } else {
        setActiveAgentIds(prev => {
          const next = new Set(prev);
          next.delete(message.agent_id);
          return next;
        });
      }
    });

    return () => {
      unsubscribeCreated();
      unsubscribeStatus();
    };
  }, [subscribe, refetch]);

  const activeAgents = agents.filter(a => a.status !== 'terminated');
  const terminatedAgents = agents.filter(a => a.status === 'terminated');

  const handleTerminateAgent = async (agentId: string) => {
    const confirmed = window.confirm(
      'Are you sure you want to terminate this agent? This will mark its task as failed.'
    );

    if (!confirmed) return;

    try {
      await apiService.terminateAgent(agentId);
      // Refetch agents to update the UI
      refetch();
    } catch (error) {
      console.error('Failed to terminate agent:', error);
      alert('Failed to terminate agent. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-600">Failed to load agents</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Agents</h1>
          <p className="text-gray-600 mt-1">All AI agents across all workflows</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-md p-4">
          <p className="text-sm text-gray-600">Total Active</p>
          <p className="text-2xl font-bold text-gray-800">{activeAgents.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <p className="text-sm text-gray-600">Working</p>
          <p className="text-2xl font-bold text-green-600">
            {activeAgents.filter(a => a.status === 'working').length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <p className="text-sm text-gray-600">Stuck</p>
          <p className="text-2xl font-bold text-yellow-600">
            {activeAgents.filter(a => a.status === 'stuck').length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <p className="text-sm text-gray-600">Terminated</p>
          <p className="text-2xl font-bold text-gray-500">{terminatedAgents.length}</p>
        </div>
      </div>

      {/* Active Agents */}
      <div>
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Active Agents</h2>
        {activeAgents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeAgents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onClick={() => setSelectedAgent(agent)}
                onViewTask={(taskId) => setSelectedTaskId(taskId)}
                onSendMessage={() => setMessageAgent(agent)}
                onTerminate={() => handleTerminateAgent(agent.id)}
                isActive={activeAgentIds.has(agent.id)}
              />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-12 text-center text-gray-500">
            No active agents
          </div>
        )}
      </div>

      {/* Terminated Agents (collapsed by default) */}
      {terminatedAgents.length > 0 && (
        <details>
          <summary className="text-lg font-semibold text-gray-600 cursor-pointer">
            Terminated Agents ({terminatedAgents.length})
          </summary>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4 opacity-50">
            {terminatedAgents.map((agent) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                onClick={() => setSelectedAgent(agent)}
                onViewTask={(taskId) => setSelectedTaskId(taskId)}
                onSendMessage={() => setMessageAgent(agent)}
              />
            ))}
          </div>
        </details>
      )}

      {/* Real-time Agent Output Modal */}
      <RealTimeAgentOutput agent={selectedAgent} onClose={() => setSelectedAgent(null)} />

      {/* Task Detail Modal */}
      <TaskDetailModal
        taskId={selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
        onNavigateToTask={(taskId) => setSelectedTaskId(taskId)}
      />

      {/* Send Message Dialog */}
      <SendMessageDialog
        open={messageAgent !== null}
        onClose={() => setMessageAgent(null)}
        agent={messageAgent}
      />
    </div>
  );
};

export default Agents;