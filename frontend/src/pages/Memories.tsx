import React, { useEffect, useState, useRef } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Database, User, Clock, Search } from 'lucide-react';
import { apiService } from '@/services/api';
import { Memory } from '@/types';
import { useWebSocket } from '@/context/WebSocketContext';
import { useWorkflow } from '@/context/WorkflowContext';
import ExecutionSelector from '@/components/ExecutionSelector';
import { formatDistanceToNow } from 'date-fns';
import AgentDetailModal from '@/components/AgentDetailModal';
import ClickableAgentCard from '@/components/ClickableAgentCard';
import ClickableTaskCard from '@/components/ClickableTaskCard';
import TaskDetailModal from '@/components/TaskDetailModal';

const MemoryTypeIcon: React.FC<{ type: string }> = ({ type }) => {
  const getIcon = () => {
    switch (type) {
      case 'error_fix':
        return '🔧';
      case 'discovery':
        return '💡';
      case 'decision':
        return '🎯';
      case 'learning':
        return '📚';
      case 'warning':
        return '⚠️';
      case 'codebase_knowledge':
        return '📝';
      default:
        return '💾';
    }
  };

  return <span className="text-xl">{getIcon()}</span>;
};

const MemoryItem: React.FC<{ memory: Memory; isNew?: boolean }> = ({ memory, isNew }) => {
  const navigate = useNavigate();
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  return (
    <motion.div
      initial={isNew ? { opacity: 0, x: -20, backgroundColor: '#DBEAFE' } : false}
      animate={{ opacity: 1, x: 0, backgroundColor: isNew ? '#DBEAFE' : '#FFFFFF' }}
      transition={{ duration: 0.5, backgroundColor: { duration: 2 } }}
      className="bg-white rounded-lg shadow-md p-4 mb-4 cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div className="flex items-start space-x-3">
        <MemoryTypeIcon type={memory.memory_type} />
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className={`text-sm text-gray-800 ${!isExpanded ? 'line-clamp-2' : ''}`}>
                {memory.content}
              </p>
              {isExpanded && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-3 pt-3 border-t"
                >
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <p className="text-gray-600 font-medium">Type</p>
                      <p className="text-gray-800">{memory.memory_type.replace('_', ' ')}</p>
                    </div>
                    <div>
                      <p className="text-gray-600 font-medium mb-2">Agent</p>
                      <ClickableAgentCard
                        agentId={memory.agent_id}
                        onClick={() => setSelectedAgentId(memory.agent_id)}
                        compact
                      />
                    </div>
                    {memory.related_task_id && (
                      <div>
                        <p className="text-gray-600 font-medium mb-2">Related Task</p>
                        <ClickableTaskCard
                          taskId={memory.related_task_id}
                          onClick={() => setSelectedTaskId(memory.related_task_id)}
                          compact
                        />
                      </div>
                    )}
                    {memory.tags && memory.tags.length > 0 && (
                      <div>
                        <p className="text-gray-600 font-medium">Tags</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {memory.tags.map((tag, index) => (
                            <span
                              key={index}
                              className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {memory.related_files && memory.related_files.length > 0 && (
                      <div className="col-span-2">
                        <p className="text-gray-600 font-medium">Related Files</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {memory.related_files.map((file, index) => (
                            <span
                              key={index}
                              className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-mono"
                            >
                              {file}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </div>
            <span
              className={`ml-3 px-2 py-1 text-xs rounded-full ${
                memory.memory_type === 'error_fix'
                  ? 'bg-red-100 text-red-700'
                  : memory.memory_type === 'discovery'
                  ? 'bg-blue-100 text-blue-700'
                  : memory.memory_type === 'learning'
                  ? 'bg-green-100 text-green-700'
                  : memory.memory_type === 'warning'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              {memory.memory_type.replace('_', ' ')}
            </span>
          </div>
          <div className="flex items-center mt-2 space-x-3 text-xs text-gray-500">
            <span className="flex items-center">
              <Clock className="w-3 h-3 mr-1" />
              {formatDistanceToNow(new Date(memory.created_at), { addSuffix: true })}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedAgentId(memory.agent_id);
              }}
              className="flex items-center hover:text-blue-600 transition-colors"
            >
              <User className="w-3 h-3 mr-1" />
              Agent {memory.agent_id.substring(0, 8)}
            </button>
          </div>
        </div>
      </div>

      {/* Modals */}
      <AgentDetailModal
        agentId={selectedAgentId}
        onClose={() => setSelectedAgentId(null)}
        onNavigateToTask={(taskId) => {
          setSelectedAgentId(null);
          setSelectedTaskId(taskId);
        }}
        onViewOutput={(agentId) => {
          navigate('/observability', { state: { focusAgentId: agentId } });
        }}
      />
      <TaskDetailModal
        taskId={selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
        onNavigateToTask={(taskId) => setSelectedTaskId(taskId)}
      />
    </motion.div>
  );
};

const Memories: React.FC = () => {
  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [newMemoryIds, setNewMemoryIds] = useState<Set<string>>(new Set());
  const { subscribe } = useWebSocket();
  const { selectedExecution } = useWorkflow();
  const observerTarget = useRef<HTMLDivElement>(null);

  const MEMORIES_PER_PAGE = 30;

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useInfiniteQuery({
    queryKey: ['memories', filter, debouncedSearch],
    queryFn: ({ pageParam = 0 }) =>
      apiService.getMemories(
        pageParam,
        MEMORIES_PER_PAGE,
        filter === 'all' ? undefined : filter,
        debouncedSearch || undefined
      ),
    getNextPageParam: (lastPage, allPages) => {
      // If we got fewer items than requested, we've reached the end
      if (lastPage.memories.length < MEMORIES_PER_PAGE) {
        return undefined;
      }
      return allPages.length * MEMORIES_PER_PAGE;
    },
    initialPageParam: 0,
    refetchInterval: 10000,
  });

  // Flatten all pages into a single array
  const memories = data?.pages.flatMap(page => page.memories) ?? [];
  const totalCount = data?.pages[0]?.total ?? 0;
  const typeCounts = data?.pages[0]?.type_counts ?? {};

  // Intersection observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1, rootMargin: '100px' } // Start loading 100px before reaching the target
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => {
      if (observerTarget.current) {
        observer.unobserve(observerTarget.current);
      }
    };
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  // Subscribe to WebSocket updates
  useEffect(() => {
    const unsubscribe = subscribe('memory_added', (message) => {
      refetch();
      setNewMemoryIds(prev => new Set(prev).add(message.memory_id));
      setTimeout(() => {
        setNewMemoryIds(prev => {
          const next = new Set(prev);
          next.delete(message.memory_id);
          return next;
        });
      }, 3000);
    });

    return unsubscribe;
  }, [subscribe, refetch]);

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
        <p className="text-red-600">Failed to load memories</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Memories</h1>
          <p className="text-gray-600 mt-1">
            {selectedExecution ? (
              <>Memories for: {selectedExecution.description || selectedExecution.definition_name}</>
            ) : (
              'Shared knowledge base from all agents'
            )}
          </p>
        </div>
        <ExecutionSelector />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-6 gap-4">
        {['error_fix', 'discovery', 'decision', 'learning', 'warning', 'codebase_knowledge'].map(
          (type) => {
            const count = typeCounts[type] ?? 0;
            return (
              <div key={type} className="bg-white rounded-lg shadow-md p-3 text-center">
                <MemoryTypeIcon type={type} />
                <p className="text-xs text-gray-600 mt-1">{type.replace('_', ' ')}</p>
                <p className="text-lg font-bold text-gray-800">{count}</p>
              </div>
            );
          }
        )}
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search memories..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Type:</span>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">All</option>
              <option value="error_fix">Error Fix</option>
              <option value="discovery">Discovery</option>
              <option value="decision">Decision</option>
              <option value="learning">Learning</option>
              <option value="warning">Warning</option>
              <option value="codebase_knowledge">Codebase</option>
            </select>
          </div>
        </div>
      </div>

      {/* Memories List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-800">
            Memories ({totalCount})
          </h2>
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-500">Live Updates</span>
          </div>
        </div>

        {memories.length > 0 ? (
          <div>
            {memories.map((memory) => (
              <MemoryItem
                key={memory.id}
                memory={memory}
                isNew={newMemoryIds.has(memory.id)}
              />
            ))}

            {/* Infinite scroll trigger */}
            <div ref={observerTarget} className="h-4 flex items-center justify-center">
              {isFetchingNextPage && (
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-12 text-center text-gray-500">
            No memories found
          </div>
        )}
      </div>
    </div>
  );
};

export default Memories;