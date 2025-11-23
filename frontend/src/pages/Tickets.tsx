import React, { useState, useEffect, useRef } from 'react';
import { Plus, LayoutGrid, Search, BarChart3, Loader2, Network, ChevronDown } from 'lucide-react';
import KanbanBoard from '@/components/tickets/KanbanBoard';
import TicketSearch from '@/components/tickets/TicketSearch';
import TicketStats from '@/components/tickets/TicketStats';
import TicketGraph from '@/components/tickets/TicketGraph';
import PendingReviewIndicator from '@/components/tickets/PendingReviewIndicator';
import { useWorkflow } from '@/context/WorkflowContext';

const Tickets: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'kanban' | 'search' | 'stats' | 'graph'>('kanban');
  const [searchTabTag, setSearchTabTag] = useState<string | null>(null);
  const [showWorkflowDropdown, setShowWorkflowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { executions, selectedExecutionId, selectExecution, loading } = useWorkflow();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowWorkflowDropdown(false);
      }
    };

    if (showWorkflowDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showWorkflowDropdown]);

  // Get current selected workflow
  const selectedWorkflow = executions.find(e => e.id === selectedExecutionId);
  const selectedWorkflowId = selectedExecutionId;

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
          {/* Workflow Selector Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowWorkflowDropdown(!showWorkflowDropdown)}
              className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm min-w-[200px]"
            >
              <span className="flex-1 text-left text-sm text-gray-700 truncate">
                {selectedWorkflow?.description || selectedWorkflow?.definition_name || 'Select Workflow'}
              </span>
              <ChevronDown className={`w-4 h-4 ml-2 text-gray-500 transition-transform ${showWorkflowDropdown ? 'rotate-180' : ''}`} />
            </button>

            {showWorkflowDropdown && (
              <div className="absolute right-0 mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
                {executions.length === 0 ? (
                  <div className="px-4 py-3 text-sm text-gray-500">No workflows available</div>
                ) : (
                  executions.map((execution) => (
                    <button
                      key={execution.id}
                      onClick={() => {
                        selectExecution(execution.id);
                        setShowWorkflowDropdown(false);
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
                          execution.status === 'active' ? 'bg-green-100 text-green-700' :
                          execution.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {execution.status}
                        </span>
                        <span className="truncate">{execution.id.slice(0, 12)}...</span>
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>

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
