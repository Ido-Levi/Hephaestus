import React, { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Search, Filter, X, Loader2, TrendingUp } from 'lucide-react';
import { apiService } from '@/services/api';
import { TicketSearchResult } from '@/types';
import TicketCard from './TicketCard';
import TicketDetailModal from './TicketDetailModal';
import { useDebounce } from '@/hooks/useDebounce';

interface TicketSearchProps {
  workflowId: string;
  initialTag?: string | null;
  onTagUsed?: () => void;
}

const TicketSearch: React.FC<TicketSearchProps> = ({ workflowId, initialTag, onTagUsed }) => {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<'hybrid' | 'semantic' | 'keyword'>('hybrid');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [results, setResults] = useState<TicketSearchResult[]>([]);

  // Filters
  const [filters, setFilters] = useState({
    status: [] as string[],
    ticket_type: [] as string[],
    priority: [] as string[],
    tags: [] as string[],
    is_blocked: undefined as boolean | undefined,
    is_resolved: undefined as boolean | undefined,
  });

  const debouncedQuery = useDebounce(query, 500);

  const searchMutation = useMutation({
    mutationFn: (searchQuery: string) =>
      apiService.searchTickets({
        workflow_id: workflowId,
        query: searchQuery,
        search_type: searchType,
        filters: {
          ...filters,
          status: filters.status.length > 0 ? filters.status : undefined,
          ticket_type: filters.ticket_type.length > 0 ? filters.ticket_type : undefined,
          priority: filters.priority.length > 0 ? filters.priority : undefined,
          tags: filters.tags.length > 0 ? filters.tags : undefined,
        },
        limit: 50,
      }),
    onSuccess: (data) => {
      setResults(data);
    },
  });

  useEffect(() => {
    if (debouncedQuery.trim()) {
      searchMutation.mutate(debouncedQuery);
    } else {
      setResults([]);
    }
  }, [debouncedQuery, searchType, filters]);

  // Handle initialTag from parent component (when navigating from tag click)
  useEffect(() => {
    if (initialTag && !filters.tags.includes(initialTag)) {
      setFilters((prev) => ({
        ...prev,
        tags: [...prev.tags, initialTag],
      }));
      setShowFilters(true);
      if (onTagUsed) {
        onTagUsed();
      }
    }
  }, [initialTag, onTagUsed]);

  const handleFilterChange = (filterType: keyof typeof filters, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [filterType]: value,
    }));
  };

  const toggleFilterValue = (filterType: 'status' | 'ticket_type' | 'priority' | 'tags', value: string) => {
    setFilters((prev) => {
      const currentValues = prev[filterType];
      const newValues = currentValues.includes(value)
        ? currentValues.filter((v) => v !== value)
        : [...currentValues, value];
      return { ...prev, [filterType]: newValues };
    });
  };

  const clearFilters = () => {
    setFilters({
      status: [],
      ticket_type: [],
      priority: [],
      tags: [],
      is_blocked: undefined,
      is_resolved: undefined,
    });
  };

  const handleTagClick = (tag: string) => {
    // Add tag to filter if not already present
    if (!filters.tags.includes(tag)) {
      setFilters((prev) => ({
        ...prev,
        tags: [...prev.tags, tag],
      }));
    }
    // Expand filters panel to show the active filter
    setShowFilters(true);
  };

  const hasActiveFilters =
    filters.status.length > 0 ||
    filters.ticket_type.length > 0 ||
    filters.priority.length > 0 ||
    filters.tags.length > 0 ||
    filters.is_blocked !== undefined ||
    filters.is_resolved !== undefined;

  return (
    <>
      <div className="space-y-6">
        {/* Search Bar */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <div className="flex items-center space-x-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search tickets by title, description, tags..."
                className="w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-3 border rounded-lg flex items-center space-x-2 transition-colors ${
                showFilters || hasActiveFilters
                  ? 'bg-blue-50 border-blue-500 text-blue-700'
                  : 'bg-white hover:bg-gray-50'
              }`}
            >
              <Filter className="w-5 h-5" />
              <span>Filters</span>
              {hasActiveFilters && (
                <span className="ml-1 px-2 py-0.5 bg-blue-600 text-white text-xs rounded-full">
                  {filters.status.length +
                    filters.ticket_type.length +
                    filters.priority.length +
                    filters.tags.length +
                    (filters.is_blocked !== undefined ? 1 : 0) +
                    (filters.is_resolved !== undefined ? 1 : 0)}
                </span>
              )}
            </button>
          </div>

          {/* Search Type Selector */}
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">Search Type:</span>
            <div className="flex space-x-2">
              {(['hybrid', 'semantic', 'keyword'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => setSearchType(type)}
                  className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                    searchType === type
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-6 pt-6 border-t space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Advanced Filters</h3>
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="text-sm text-blue-600 hover:text-blue-700 flex items-center"
                  >
                    <X className="w-4 h-4 mr-1" />
                    Clear All
                  </button>
                )}
              </div>

              <div className="grid grid-cols-3 gap-4">
                {/* Status Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Status
                  </label>
                  <div className="space-y-2">
                    {['backlog', 'todo', 'in_progress', 'review', 'done'].map((status) => (
                      <label key={status} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={filters.status.includes(status)}
                          onChange={() => toggleFilterValue('status', status)}
                          className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm capitalize">{status.replace('_', ' ')}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Type Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Type
                  </label>
                  <div className="space-y-2">
                    {['bug', 'feature', 'improvement', 'task', 'spike'].map((type) => (
                      <label key={type} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={filters.ticket_type.includes(type)}
                          onChange={() => toggleFilterValue('ticket_type', type)}
                          className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm capitalize">{type}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Priority Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority
                  </label>
                  <div className="space-y-2">
                    {['critical', 'high', 'medium', 'low'].map((priority) => (
                      <label key={priority} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={filters.priority.includes(priority)}
                          onChange={() => toggleFilterValue('priority', priority)}
                          className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm capitalize">{priority}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Tags Filter */}
              {filters.tags.length > 0 && (
                <div className="pt-4 border-t">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Active Tag Filters
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {filters.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-full"
                      >
                        {tag}
                        <button
                          onClick={() => toggleFilterValue('tags', tag)}
                          className="ml-2 hover:text-blue-900 transition-colors"
                          title="Remove tag filter"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Additional Filters */}
              <div className="flex items-center space-x-6 pt-4 border-t">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.is_blocked === true}
                    onChange={(e) =>
                      handleFilterChange('is_blocked', e.target.checked ? true : undefined)
                    }
                    className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm">Only Blocked</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.is_resolved === true}
                    onChange={(e) =>
                      handleFilterChange('is_resolved', e.target.checked ? true : undefined)
                    }
                    className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm">Only Resolved</span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="bg-white rounded-lg border shadow-sm p-6">
          {searchMutation.isPending ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">
                  {results.length} {results.length === 1 ? 'result' : 'results'} found
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {results.map((result) => (
                  <div key={result.ticket_id} className="relative">
                    {result.relevance_score > 0 && (
                      <div className="absolute -top-2 -right-2 z-10 px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full flex items-center">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        {(result.relevance_score * 100).toFixed(0)}%
                      </div>
                    )}
                    <TicketCard
                      ticket={{
                        id: result.ticket_id,
                        ticket_id: result.ticket_id,
                        workflow_id: '',
                        title: result.title,
                        description: result.description,
                        ticket_type: result.ticket_type,
                        priority: result.priority,
                        status: result.status,
                        created_by_agent_id: '',
                        assigned_agent_id: result.assigned_agent_id,
                        created_at: result.created_at,
                        updated_at: result.created_at,
                        started_at: null,
                        completed_at: null,
                        parent_ticket_id: null,
                        related_task_ids: [],
                        related_ticket_ids: [],
                        tags: result.tags || [],
                        blocked_by_ticket_ids: [],
                        is_blocked: false,
                        is_resolved: false,
                        resolved_at: null,
                        comment_count: 0,
                        commit_count: 0,
                      }}
                      onClick={() => setSelectedTicketId(result.ticket_id)}
                      draggable={false}
                      onTagClick={handleTagClick}
                    />
                  </div>
                ))}
              </div>
            </div>
          ) : query.trim() ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <Search className="w-12 h-12 mb-4" />
              <p className="text-lg">No tickets found</p>
              <p className="text-sm">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <Search className="w-12 h-12 mb-4" />
              <p className="text-lg">Start typing to search tickets</p>
              <p className="text-sm">Search by title, description, tags, or content</p>
            </div>
          )}
        </div>
      </div>

      {/* Ticket Detail Modal */}
      {selectedTicketId && (
        <TicketDetailModal
          ticketId={selectedTicketId}
          onClose={() => setSelectedTicketId(null)}
          onNavigateToSearchTab={handleTagClick}
        />
      )}
    </>
  );
};

export default TicketSearch;
