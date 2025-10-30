import React, { useState, useMemo } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { AlertCircle, Loader2, Search, ChevronDown } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { apiService } from '@/services/api';
import { TicketDetail } from '@/types';
import TicketCard from './TicketCard';
import TicketDetailModal from './TicketDetailModal';
import { cn } from '@/lib/utils';

interface KanbanBoardProps {
  workflowId: string;
  onNavigateToSearchTab?: (tag: string) => void;
}

const KanbanBoard: React.FC<KanbanBoardProps> = ({ workflowId, onNavigateToSearchTab }) => {
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [draggedTicketId, setDraggedTicketId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [selectedAgent, setSelectedAgent] = useState<string>('all');
  const queryClient = useQueryClient();

  // Fetch board stats to get column configuration
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['ticketStats', workflowId],
    queryFn: () => apiService.getTicketStats(workflowId),
    enabled: !!workflowId,
  });

  // Fetch all tickets
  const { data: tickets, isLoading: ticketsLoading } = useQuery({
    queryKey: ['tickets', workflowId],
    queryFn: () => apiService.getTickets({ workflow_id: workflowId }),
    enabled: !!workflowId,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Mutation for changing ticket status
  const changeStatusMutation = useMutation({
    mutationFn: ({ ticketId, newStatus }: { ticketId: string; newStatus: string }) =>
      apiService.changeTicketStatus(ticketId, newStatus),
    onMutate: async ({ ticketId, newStatus }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['tickets', workflowId] });

      // Snapshot the previous value
      const previousTickets = queryClient.getQueryData<TicketDetail[]>(['tickets', workflowId]);

      // Optimistically update
      if (previousTickets) {
        queryClient.setQueryData<TicketDetail[]>(
          ['tickets', workflowId],
          previousTickets.map((t) =>
            t.id === ticketId ? { ...t, status: newStatus } : t
          )
        );
      }

      return { previousTickets };
    },
    onError: (_err, _variables, context) => {
      // Rollback on error
      if (context?.previousTickets) {
        queryClient.setQueryData(['tickets', workflowId], context.previousTickets);
      }
      toast.error('Failed to update ticket status');
    },
    onSuccess: () => {
      toast.success('Ticket status updated');
      queryClient.invalidateQueries({ queryKey: ['tickets', workflowId] });
      queryClient.invalidateQueries({ queryKey: ['ticketStats', workflowId] });
    },
  });

  const handleDragStart = (ticketId: string) => {
    setDraggedTicketId(ticketId);
  };

  const handleDragEnd = () => {
    setDraggedTicketId(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (columnId: string) => {
    if (!draggedTicketId) return;

    const ticket = tickets?.find((t) => t.id === draggedTicketId);
    if (!ticket) return;

    // Check if ticket is blocked
    if (ticket.is_blocked) {
      toast.error('Cannot move blocked ticket');
      return;
    }

    // Check if already in this column
    if (ticket.status === columnId) return;

    // Update status
    changeStatusMutation.mutate({
      ticketId: draggedTicketId,
      newStatus: columnId,
    });
  };

  // Get unique values for filters - must be called before any conditional returns
  const uniqueTypes = useMemo(() => {
    if (!tickets) return [];
    const types = new Set(tickets.map((t) => t.ticket_type));
    return Array.from(types).sort();
  }, [tickets]);

  const uniquePriorities = useMemo(() => {
    if (!tickets) return [];
    const priorities = new Set(tickets.map((t) => t.priority));
    return Array.from(priorities).sort();
  }, [tickets]);

  const uniqueAgents = useMemo(() => {
    if (!tickets) return [];
    const agents = new Set(
      tickets
        .filter((t) => t.assigned_agent_id)
        .map((t) => t.assigned_agent_id as string)
    );
    return Array.from(agents).sort();
  }, [tickets]);

  // Apply filters - must be called before any conditional returns
  const filteredTickets = useMemo(() => {
    if (!tickets) return [];
    return tickets.filter((ticket) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch =
          ticket.title.toLowerCase().includes(query) ||
          ticket.description.toLowerCase().includes(query) ||
          ticket.tags?.some((tag) => tag.toLowerCase().includes(query));
        if (!matchesSearch) return false;
      }

      // Type filter
      if (selectedType !== 'all' && ticket.ticket_type !== selectedType) {
        return false;
      }

      // Priority filter
      if (selectedPriority !== 'all' && ticket.priority !== selectedPriority) {
        return false;
      }

      // Agent filter
      if (selectedAgent !== 'all' && ticket.assigned_agent_id !== selectedAgent) {
        return false;
      }

      return true;
    });
  }, [tickets, searchQuery, selectedType, selectedPriority, selectedAgent]);

  // NOW we can have conditional returns - all hooks have been called
  if (statsLoading || ticketsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (!stats || !tickets) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <AlertCircle className="w-12 h-12 mb-4" />
        <p>No data available</p>
      </div>
    );
  }

  if (!stats.board_config) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <AlertCircle className="w-12 h-12 mb-4" />
        <p>Kanban board not configured for this workflow</p>
        <p className="text-sm mt-2">This workflow does not have ticket tracking enabled</p>
      </div>
    );
  }

  const columns = stats.board_config.columns.sort((a, b) => a.order - b.order);

  const getTicketsForColumn = (columnId: string) => {
    return filteredTickets.filter((t) => t.status === columnId);
  };

  return (
    <>
      {/* Filter Bar */}
      <div className="bg-white rounded-lg border shadow-sm p-4 mb-4 space-y-3">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tickets..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Filter Dropdowns */}
        <div className="flex items-center gap-3 text-sm">
          <span className="text-gray-600 font-medium">Filters:</span>

          {/* Type Filter */}
          <div className="relative">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="appearance-none bg-white border rounded-lg px-4 py-2 pr-10 cursor-pointer hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Types</option>
              {uniqueTypes.map((type) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>

          {/* Priority Filter */}
          <div className="relative">
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="appearance-none bg-white border rounded-lg px-4 py-2 pr-10 cursor-pointer hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Priorities</option>
              {uniquePriorities.map((priority) => (
                <option key={priority} value={priority}>
                  {priority.charAt(0).toUpperCase() + priority.slice(1)}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>

          {/* Agent Filter */}
          <div className="relative">
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="appearance-none bg-white border rounded-lg px-4 py-2 pr-10 cursor-pointer hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Agents</option>
              {uniqueAgents.map((agent) => (
                <option key={agent} value={agent}>
                  {agent}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>

          {/* Active Filters Count */}
          {(searchQuery || selectedType !== 'all' || selectedPriority !== 'all' || selectedAgent !== 'all') && (
            <span className="text-blue-600 font-medium">
              ({filteredTickets.length} of {tickets.length} tickets)
            </span>
          )}
        </div>
      </div>

      {/* Kanban Columns */}
      <div className="flex space-x-4 overflow-x-auto pb-4">
        {columns.map((column) => {
          const columnTickets = getTicketsForColumn(column.id);
          const ticketCount = columnTickets.length;

          return (
            <div
              key={column.id}
              className="flex-shrink-0 w-80"
              onDragOver={handleDragOver}
              onDrop={() => handleDrop(column.id)}
            >
              {/* Column Header */}
              <div
                className="sticky top-0 z-10 bg-white rounded-t-lg border-2 border-b-0 p-3 mb-2"
                style={{ borderColor: column.color }}
              >
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-semibold text-gray-900">{column.name}</h3>
                  <span
                    className="text-sm font-medium px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: `${column.color}20`,
                      color: column.color,
                    }}
                  >
                    {ticketCount}
                  </span>
                </div>
              </div>

              {/* Column Content */}
              <div
                className={cn(
                  'min-h-[500px] rounded-b-lg border-2 border-t-0 p-3 bg-gray-50 transition-colors',
                  draggedTicketId && 'border-dashed bg-blue-50'
                )}
                style={{ borderColor: draggedTicketId ? '#3b82f6' : column.color }}
              >
                {columnTickets.length === 0 ? (
                  <div className="text-center text-gray-400 text-sm mt-8">
                    No tickets
                  </div>
                ) : (
                  columnTickets.map((ticket) => (
                    <TicketCard
                      key={ticket.id}
                      ticket={ticket}
                      onClick={() => setSelectedTicketId(ticket.id)}
                      onDragStart={() => handleDragStart(ticket.id)}
                      onDragEnd={handleDragEnd}
                      draggable={!ticket.is_blocked}
                      onTagClick={onNavigateToSearchTab}
                    />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Ticket Detail Modal */}
      {selectedTicketId && (
        <TicketDetailModal
          ticketId={selectedTicketId}
          onClose={() => setSelectedTicketId(null)}
          onNavigateToSearchTab={onNavigateToSearchTab}
        />
      )}
    </>
  );
};

export default KanbanBoard;
