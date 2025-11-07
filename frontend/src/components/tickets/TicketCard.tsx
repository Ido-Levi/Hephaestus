import React from 'react';
import { Bug, Lightbulb, Wrench, CheckSquare, Beaker, FileText, Lock, CheckCircle, MessageCircle, GitCommit, User, Clock } from 'lucide-react';
import { TicketDetail } from '@/types';
import { cn } from '@/lib/utils';
import { Tooltip } from '@/components/ui/tooltip';

interface TicketCardProps {
  ticket: TicketDetail;
  onClick: () => void;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: (e: React.DragEvent) => void;
  draggable?: boolean;
  onTagClick?: (tag: string) => void;
}

const getTicketTypeIcon = (type: string) => {
  switch (type) {
    case 'bug':
      return <Bug className="w-4 h-4 text-red-600" />;
    case 'feature':
      return <Lightbulb className="w-4 h-4 text-yellow-600" />;
    case 'improvement':
      return <Wrench className="w-4 h-4 text-blue-600" />;
    case 'task':
      return <CheckSquare className="w-4 h-4 text-green-600" />;
    case 'spike':
      return <Beaker className="w-4 h-4 text-purple-600" />;
    case 'documentation':
      return <FileText className="w-4 h-4 text-gray-600" />;
    default:
      return <CheckSquare className="w-4 h-4 text-gray-600" />;
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low':
      return 'bg-gray-100 text-gray-800 border-gray-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const formatTooltipContent = (ticket: TicketDetail): string => {
  const descriptionPreview = ticket.description.length > 100
    ? `${ticket.description.substring(0, 100)}...`
    : ticket.description;

  return `${ticket.title}\n\n${descriptionPreview}`;
};

const TicketCard: React.FC<TicketCardProps> = ({
  ticket,
  onClick,
  onDragStart,
  onDragEnd,
  draggable = true,
  onTagClick,
}) => {
  const isPendingReview = ticket.approval_status === 'pending_review';

  return (
    <Tooltip content={formatTooltipContent(ticket)}>
      <div
        className={cn(
          'bg-white rounded-lg border border-gray-200 p-3 mb-2 shadow-sm hover:shadow-md transition-all cursor-pointer group',
          isPendingReview && 'border-l-4 border-l-orange-500 bg-orange-50 ring-2 ring-orange-200',
          ticket.is_blocked && 'border-l-4 border-l-red-500 bg-red-50',
          ticket.is_resolved && 'bg-green-50 border-l-4 border-l-green-500'
        )}
        onClick={onClick}
        draggable={draggable && !ticket.is_blocked}
        onDragStart={onDragStart}
        onDragEnd={onDragEnd}
      >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-gray-500">
            {ticket.id.split('-')[1]?.substring(0, 8) || ticket.id.substring(0, 8)}
          </span>
          {getTicketTypeIcon(ticket.ticket_type)}
        </div>
        <div className="flex items-center space-x-1">
          {isPendingReview && (
            <div className="p-1 bg-orange-100 rounded animate-pulse" title="Pending Human Review">
              <Clock className="w-3 h-3 text-orange-600" />
            </div>
          )}
          {ticket.is_blocked && (
            <div className="p-1 bg-red-100 rounded" title="Blocked">
              <Lock className="w-3 h-3 text-red-600" />
            </div>
          )}
          {ticket.is_resolved && (
            <div className="p-1 bg-green-100 rounded" title="Resolved">
              <CheckCircle className="w-3 h-3 text-green-600" />
            </div>
          )}
        </div>
      </div>

      {/* Pending Review Banner */}
      {isPendingReview && (
        <div className="mb-2 px-2 py-1 bg-orange-100 border border-orange-300 rounded text-xs font-semibold text-orange-800 text-center">
          ⏳ Needs Human Review
        </div>
      )}

      {/* Title */}
      <h3 className="text-sm font-medium text-gray-900 mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors">
        {ticket.title}
      </h3>

      {/* Tags */}
      {ticket.tags && ticket.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {ticket.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              onClick={(e) => {
                if (onTagClick) {
                  e.stopPropagation();
                  onTagClick(tag);
                }
              }}
              className={cn(
                'text-xs px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full transition-all',
                onTagClick &&
                  'cursor-pointer hover:bg-blue-100 hover:text-blue-700 hover:ring-1 hover:ring-blue-400'
              )}
              title={onTagClick ? `Filter by tag: ${tag}` : tag}
            >
              {tag}
            </span>
          ))}
          {ticket.tags.length > 3 && (
            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">
              +{ticket.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
        {/* Priority */}
        <span
          className={cn(
            'text-xs px-2 py-0.5 rounded border font-medium',
            getPriorityColor(ticket.priority)
          )}
        >
          {ticket.priority}
        </span>

        {/* Agent & Metadata */}
        <div className="flex items-center space-x-3 text-xs text-gray-500">
          {ticket.assigned_agent_id && (
            <div className="flex items-center" title={ticket.assigned_agent_id}>
              <User className="w-3 h-3 mr-1" />
              <span className="max-w-[60px] truncate">
                {ticket.assigned_agent_id.split('-')[0]}
              </span>
            </div>
          )}
          {ticket.comment_count > 0 && (
            <div className="flex items-center" title={`${ticket.comment_count} comments`}>
              <MessageCircle className="w-3 h-3 mr-1" />
              <span>{ticket.comment_count}</span>
            </div>
          )}
          {ticket.commit_count > 0 && (
            <div className="flex items-center" title={`${ticket.commit_count} commits`}>
              <GitCommit className="w-3 h-3 mr-1" />
              <span>{ticket.commit_count}</span>
            </div>
          )}
        </div>
      </div>
      </div>
    </Tooltip>
  );
};

export default TicketCard;
