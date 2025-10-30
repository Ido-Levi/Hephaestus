import React from 'react';
import { Handle, Position } from 'reactflow';
import { Lock, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Ticket } from '@/types';

interface TicketGraphNodeProps {
  data: {
    ticket: Ticket;
    onClick: (ticketId: string) => void;
  };
}

const TicketGraphNode: React.FC<TicketGraphNodeProps> = ({ data }) => {
  const { ticket, onClick } = data;

  // Determine node border color based on status
  const getBorderColor = () => {
    if (ticket.is_resolved) return 'border-green-500';
    if (ticket.is_blocked) return 'border-red-500';
    if (ticket.blocks_ticket_ids && ticket.blocks_ticket_ids.length > 0) return 'border-orange-500';
    return 'border-blue-500';
  };

  const getStatusIcon = () => {
    if (ticket.is_resolved) return <CheckCircle className="w-4 h-4 text-green-600" />;
    if (ticket.is_blocked) return <Lock className="w-4 h-4 text-red-600" />;
    if (ticket.blocks_ticket_ids && ticket.blocks_ticket_ids.length > 0) return <AlertCircle className="w-4 h-4 text-orange-600" />;
    return null;
  };

  const getPriorityColor = () => {
    switch (ticket.priority) {
      case 'critical': return 'bg-red-100 text-red-700';
      case 'high': return 'bg-orange-100 text-orange-700';
      case 'medium': return 'bg-yellow-100 text-yellow-700';
      case 'low': return 'bg-gray-100 text-gray-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <>
      {/* Input handle (top) for incoming edges */}
      <Handle type="target" position={Position.Top} className="w-3 h-3" />

      <div
        onClick={() => onClick(ticket.id)}
        className={cn(
          'px-4 py-3 rounded-lg border-2 bg-white shadow-lg hover:shadow-xl transition-all cursor-pointer min-w-[200px] max-w-[280px]',
          getBorderColor()
        )}
      >
        {/* Header with ticket ID and status icon */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono text-gray-500 truncate">{ticket.id}</span>
          {getStatusIcon()}
        </div>

        {/* Title */}
        <div className="font-semibold text-sm text-gray-900 mb-2 line-clamp-2">
          {ticket.title}
        </div>

        {/* Footer with priority and type */}
        <div className="flex items-center justify-between space-x-2">
          <span className={cn('px-2 py-0.5 text-xs rounded capitalize', getPriorityColor())}>
            {ticket.priority}
          </span>
          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded capitalize">
            {ticket.ticket_type}
          </span>
        </div>

        {/* Status badge */}
        <div className="mt-2 text-xs text-gray-600 capitalize">
          {ticket.status.replace(/_/g, ' ')}
        </div>
      </div>

      {/* Output handle (bottom) for outgoing edges */}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </>
  );
};

export default TicketGraphNode;
