import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, ExternalLink, AlertTriangle, Loader2, Ban, ChevronDown, ChevronUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '@/services/api';
import { useWorkflow } from '@/context/WorkflowContext';
import { BlockedTask, BlockerTicket } from '@/types';
import StatusBadge from '@/components/StatusBadge';
import { formatDistanceToNow } from 'date-fns';

interface BlockedTasksViewProps {
  onViewTicketDetails?: (ticketId: string) => void;
}

const BlockedTasksView: React.FC<BlockedTasksViewProps> = ({ onViewTicketDetails }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const navigate = useNavigate();
  const { selectedExecutionId } = useWorkflow();

  const { data: blockedTasks, isLoading } = useQuery({
    queryKey: ['blocked-tasks', selectedExecutionId],
    queryFn: () => apiService.getBlockedTasks(selectedExecutionId || undefined),
    refetchInterval: 5000, // Poll every 5 seconds
    enabled: !!selectedExecutionId,
  });

  const handleViewTicket = (ticketId: string) => {
    if (onViewTicketDetails) {
      onViewTicketDetails(ticketId);
    } else {
      // Navigate to Tickets page - the ticket will be visible there
      navigate('/tickets');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading blocked tasks...</p>
        </div>
      </div>
    );
  }

  if (!blockedTasks || blockedTasks.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg shadow-md p-8 text-center"
      >
        <div className="flex flex-col items-center">
          <div className="bg-green-100 p-4 rounded-full mb-4">
            <Lock className="w-10 h-10 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Blocked Tasks</h3>
          <p className="text-gray-600 max-w-md">
            All tasks are ready to run. There are no tasks currently blocked by ticket dependencies.
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-red-50 border border-red-200 rounded-lg overflow-hidden"
    >
      {/* Compact Collapsible Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full bg-red-100 hover:bg-red-150 px-4 py-2.5 transition-colors border-b border-red-200"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Lock className="w-4 h-4 text-red-600" />
            <span className="text-sm font-semibold text-red-900">
              {blockedTasks.length} Blocked Task{blockedTasks.length !== 1 ? 's' : ''}
            </span>
            <span className="text-xs text-red-600">
              (waiting for ticket resolution)
            </span>
          </div>
          <div className="flex items-center space-x-1 text-red-700">
            <span className="text-xs font-medium">{isExpanded ? 'Hide' : 'Show'}</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </button>

      {/* Collapsible Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="divide-y divide-red-200">
              {blockedTasks.map((task, index) => (
                <BlockedTaskCard
                  key={task.task_id}
                  task={task}
                  index={index}
                  onViewTicket={handleViewTicket}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

interface BlockedTaskCardProps {
  task: BlockedTask;
  index: number;
  onViewTicket: (ticketId: string) => void;
}

const BlockedTaskCard: React.FC<BlockedTaskCardProps> = ({ task, index, onViewTicket }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [showFullDescription, setShowFullDescription] = React.useState(false);

  const truncatedDescription = task.description.length > 120
    ? task.description.substring(0, 120) + '...'
    : task.description;

  return (
    <div className="bg-white hover:bg-gray-50 transition-colors px-4 py-3">
      <div className="flex items-start justify-between gap-3">
        {/* Left: Task Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-gray-400">{task.task_id.substring(0, 8)}</span>
            <StatusBadge status="blocked" size="sm" />
            <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
              task.priority === 'high' ? 'bg-red-100 text-red-700' :
              task.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {task.priority}
            </span>
          </div>

          <p className="text-sm text-gray-800 mb-2">
            {showFullDescription ? task.description : truncatedDescription}
            {task.description.length > 120 && (
              <button
                onClick={() => setShowFullDescription(!showFullDescription)}
                className="text-blue-600 hover:text-blue-700 ml-1 text-xs font-medium"
              >
                {showFullDescription ? 'less' : 'more'}
              </button>
            )}
          </p>

          <div className="flex items-center gap-2 text-xs text-gray-500">
            <AlertTriangle className="w-3 h-3 text-orange-500" />
            <span>Blocked by {task.blocking_tickets.length} ticket{task.blocking_tickets.length !== 1 ? 's' : ''}</span>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              {isExpanded ? 'Hide' : 'View Details'}
            </button>
          </div>
        </div>
      </div>

      {/* Expanded Blocker Details */}
      <AnimatePresence>
        {isExpanded && task.blocking_tickets.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="mt-3 pt-3 border-t border-gray-200 space-y-1.5"
          >
            {task.blocking_tickets.map((blocker) => (
              <BlockerTicketRow
                key={blocker.ticket_id}
                blocker={blocker}
                onViewTicket={onViewTicket}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

interface BlockerTicketRowProps {
  blocker: BlockerTicket;
  onViewTicket: (ticketId: string) => void;
}

const BlockerTicketRow: React.FC<BlockerTicketRowProps> = ({ blocker, onViewTicket }) => {
  return (
    <button
      onClick={() => onViewTicket(blocker.ticket_id)}
      className="w-full bg-gray-50 rounded px-2 py-1.5 flex items-center justify-between hover:bg-blue-50 hover:border-blue-300 transition-all border border-gray-200 text-left"
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <Lock className="w-3 h-3 text-gray-400 flex-shrink-0" />
        <span className="text-xs font-mono text-gray-500 flex-shrink-0">
          {blocker.ticket_id.substring(0, 8)}
        </span>
        <span className="text-xs text-gray-700 truncate">{blocker.title}</span>
        <StatusBadge status={blocker.status} size="sm" />
      </div>
      <ExternalLink className="w-3 h-3 text-blue-600 flex-shrink-0 ml-2" />
    </button>
  );
};

export default BlockedTasksView;
