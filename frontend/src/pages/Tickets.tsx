import React, { useState, useEffect } from 'react';
import { Plus, LayoutGrid, Search, BarChart3, Loader2, Network } from 'lucide-react';
import KanbanBoard from '@/components/tickets/KanbanBoard';
import TicketSearch from '@/components/tickets/TicketSearch';
import TicketStats from '@/components/tickets/TicketStats';
import TicketGraph from '@/components/tickets/TicketGraph';
import PendingReviewIndicator from '@/components/tickets/PendingReviewIndicator';

const Tickets: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'kanban' | 'search' | 'stats' | 'graph'>('kanban');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTabTag, setSearchTabTag] = useState<string | null>(null);

  // Fetch the active workflow ID on mount
  useEffect(() => {
    const fetchWorkflow = async () => {
      try {
        // Fetch workflows and use the first active one
        const response = await fetch('http://localhost:8000/api/workflows', {
          headers: {
            'X-Agent-ID': 'ui-user',
          },
        });
        const workflows = await response.json();

        if (workflows && workflows.length > 0) {
          // Use the first active workflow
          const activeWorkflow = workflows.find((w: any) => w.status === 'active') || workflows[0];
          setSelectedWorkflowId(activeWorkflow.id);
        }
      } catch (error) {
        console.error('Failed to fetch workflows:', error);
        // Fallback to hardcoded ID for backwards compatibility
        setSelectedWorkflowId('workflow-e2e-test');
      } finally {
        setLoading(false);
      }
    };

    fetchWorkflow();
  }, []);

  const handleNewTicket = () => {
    // TODO: Open create ticket modal
    console.log('Create new ticket');
  };

  const handleNavigateToSearchTab = (tag: string) => {
    setSearchTabTag(tag);
    setActiveTab('search');
  };

  const tabs = [
    { id: 'kanban', label: 'Kanban Board', icon: LayoutGrid },
    { id: 'search', label: 'Search', icon: Search },
    { id: 'stats', label: 'Statistics', icon: BarChart3 },
    { id: 'graph', label: 'Graph', icon: Network },
  ] as const;

  // Show loading state while fetching workflow
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading workflow...</p>
        </div>
      </div>
    );
  }

  // Show error if no workflow found
  if (!selectedWorkflowId) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <p className="text-lg font-semibold mb-2">No workflow found</p>
          <p className="text-sm">Please create a workflow first</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Ticket Tracking</h1>
          <p className="text-sm text-gray-600 mt-1">
            Manage and track tickets across your workflow
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Pending Review Indicator */}
          <PendingReviewIndicator />

          <button
            onClick={handleNewTicket}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
          >
            <Plus className="w-5 h-5 mr-2" />
            New Ticket
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`
                flex items-center px-1 py-4 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <Icon className="w-5 h-5 mr-2" />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'kanban' && (
          <KanbanBoard
            workflowId={selectedWorkflowId}
            onNavigateToSearchTab={handleNavigateToSearchTab}
          />
        )}
        {activeTab === 'search' && (
          <TicketSearch
            workflowId={selectedWorkflowId}
            initialTag={searchTabTag}
            onTagUsed={() => setSearchTabTag(null)}
          />
        )}
        {activeTab === 'stats' && (
          <TicketStats workflowId={selectedWorkflowId} />
        )}
        {activeTab === 'graph' && (
          <TicketGraph
            workflowId={selectedWorkflowId}
            onNavigateToSearchTab={handleNavigateToSearchTab}
          />
        )}
      </div>
    </div>
  );
};

export default Tickets;
