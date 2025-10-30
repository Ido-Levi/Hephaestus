import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Bot,
  Terminal,
  MessageSquare,
  Eye,
  Copy,
  Send,
  ChevronDown,
  ChevronUp,
  Activity
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { apiService } from '@/services/api';
import { Agent } from '@/types';
import ClickableTaskCard from './ClickableTaskCard';
import TaskDetailModal from './TaskDetailModal';

interface AgentDetailModalProps {
  agentId: string | null;
  onClose: () => void;
  onNavigateToTask?: (taskId: string) => void;
  onViewOutput?: (agentId: string) => void;
}

const AgentDetailModal: React.FC<AgentDetailModalProps> = ({
  agentId,
  onClose,
  onNavigateToTask,
  onViewOutput
}) => {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [messageText, setMessageText] = useState('');
  const [expandedSections, setExpandedSections] = useState({
    task: true,
    details: false,
    message: false,
  });

  const { data: agent, isLoading } = useQuery<Agent>({
    queryKey: ['agent', agentId],
    queryFn: () => agentId ? apiService.getAgents().then(agents => agents.find(a => a.id === agentId)!) : Promise.reject(),
    enabled: !!agentId,
    refetchInterval: 3000,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleSendMessage = async () => {
    if (!agent || !messageText.trim()) return;

    try {
      await apiService.sendMessage('main-session-agent', agent.id, messageText);
      setMessageText('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'working':
        return 'text-green-600 bg-green-100';
      case 'stuck':
        return 'text-red-600 bg-red-100';
      case 'idle':
        return 'text-gray-600 bg-gray-100';
      case 'terminated':
        return 'text-gray-500 bg-gray-200';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (!agentId) return null;

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
          className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-6 py-4 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Bot className="w-6 h-6 text-blue-600" />
                <div>
                  <h3 className="text-xl font-semibold text-gray-800">
                    Agent Monitor
                  </h3>
                  <p className="text-sm text-gray-600 font-mono">
                    {agent?.id || agentId}
                  </p>
                </div>

                {agent && (
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${getStatusColor(agent.status)}`}>
                    {agent.status}
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-2">
                {agent && onViewOutput && (
                  <button
                    onClick={() => onViewOutput(agent.id)}
                    className="flex items-center px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
                    title="View live agent output"
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    Live Output
                  </button>
                )}

                <button
                  onClick={() => agent && copyToClipboard(agent.id)}
                  className="p-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                  title="Copy agent ID"
                >
                  <Copy className="w-4 h-4" />
                </button>

                <button
                  onClick={onClose}
                  className="p-2 rounded-lg text-gray-500 hover:text-gray-700 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Agent Info */}
            {agent && (
              <div className="mt-3 grid grid-cols-4 gap-4 text-sm">
                <div className="text-gray-600">
                  <span className="block text-xs text-gray-500">CLI Type</span>
                  <span className="font-medium">{agent.cli_type}</span>
                </div>

                <div className="text-gray-600">
                  <span className="block text-xs text-gray-500">Health</span>
                  <span className={`font-medium ${agent.health_check_failures > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {agent.health_check_failures > 0 ? `${agent.health_check_failures} failures` : 'Healthy'}
                  </span>
                </div>

                <div className="text-gray-600">
                  <span className="block text-xs text-gray-500">Created</span>
                  <span className="font-medium">{formatDistanceToNow(new Date(agent.created_at), { addSuffix: true })}</span>
                </div>

                {agent.last_activity && (
                  <div className="text-gray-600">
                    <span className="block text-xs text-gray-500">Last Active</span>
                    <span className="font-medium">{formatDistanceToNow(new Date(agent.last_activity), { addSuffix: true })}</span>
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

            {agent && (
              <div className="p-6 space-y-6">
                {/* Current Task */}
                <div className="space-y-4">
                  <button
                    onClick={() => toggleSection('task')}
                    className="flex items-center space-x-2 text-lg font-semibold text-gray-800 hover:text-blue-600 transition-colors"
                  >
                    <Activity className="w-5 h-5" />
                    <span>Active assignment</span>
                    {expandedSections.task ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  <AnimatePresence>
                    {expandedSections.task && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                      >
                        {agent.current_task_id ? (
                          <ClickableTaskCard
                            taskId={agent.current_task_id}
                            onClick={() => {
                              setSelectedTaskId(agent.current_task_id);
                            }}
                            compact={false}
                          />
                        ) : (
                          <div className="p-4 bg-gray-50 rounded-lg text-center text-gray-500 text-sm">
                            No active assignment
                          </div>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Agent Details */}
                <div className="space-y-4">
                  <button
                    onClick={() => toggleSection('details')}
                    className="flex items-center space-x-2 text-lg font-semibold text-gray-800 hover:text-blue-600 transition-colors"
                  >
                    <Terminal className="w-5 h-5" />
                    <span>TMUX SESSION</span>
                    {expandedSections.details ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  <AnimatePresence>
                    {expandedSections.details && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                      >
                        <div className="p-4 bg-gray-900 rounded-lg">
                          <code className="text-green-400 text-sm font-mono">
                            {agent.tmux_session_name || `agent_${agent.id.substring(0, 8)}`}
                          </code>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Send Message */}
                <div className="space-y-4">
                  <button
                    onClick={() => toggleSection('message')}
                    className="flex items-center space-x-2 text-lg font-semibold text-gray-800 hover:text-blue-600 transition-colors"
                  >
                    <MessageSquare className="w-5 h-5" />
                    <span>Send Message to Agent</span>
                    {expandedSections.message ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  <AnimatePresence>
                    {expandedSections.message && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="space-y-3"
                      >
                        <textarea
                          value={messageText}
                          onChange={(e) => setMessageText(e.target.value)}
                          placeholder="Type your message here..."
                          className="w-full p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows={4}
                        />
                        <button
                          onClick={handleSendMessage}
                          disabled={!messageText.trim()}
                          className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                        >
                          <Send className="w-4 h-4" />
                          Send Message
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>

      {/* Task Detail Modal */}
      <TaskDetailModal
        taskId={selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
        onNavigateToTask={(taskId) => {
          setSelectedTaskId(taskId);
          if (onNavigateToTask) {
            onNavigateToTask(taskId);
          }
        }}
      />
    </AnimatePresence>
  );
};

export default AgentDetailModal;
