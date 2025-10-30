import React, { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import {
  ClipboardList,
  CheckCircle,
  Clock,
  XCircle,
  Search,
  RefreshCw,
  Filter,
  Calendar,
  Layers,
  User,
  ChevronDown,
  ChevronUp,
  Eye,
  ShieldCheck,
  FileText,
  GitBranch,
  ExternalLink,
  Download,
} from 'lucide-react';
import { isAxiosError } from 'axios';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import { format, formatDistanceToNow } from 'date-fns';

import { apiService } from '@/services/api';
import {
  ResultSummary,
  ResultStatus,
  ResultContentResponse,
  ResultValidationDetail,
} from '@/types';
import StatusBadge from '@/components/StatusBadge';
import TaskDetailModal from '@/components/TaskDetailModal';
import { useWebSocket } from '@/context/WebSocketContext';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

type ScopeFilter = 'all' | 'workflow' | 'task';
type DateRangeFilter = 'all' | '24h' | '7d' | '30d';

const statusBuckets: Record<
  'validated' | 'pending' | 'rejected',
  ResultStatus[]
> = {
  validated: ['validated', 'verified'],
  pending: ['pending_validation', 'unverified'],
  rejected: ['rejected', 'disputed'],
};

const statusOptions: Array<{ value: ResultStatus | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'validated', label: 'Validated' },
  { value: 'pending_validation', label: 'Pending Validation' },
  { value: 'unverified', label: 'Unverified' },
  { value: 'verified', label: 'Verified' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'disputed', label: 'Disputed' },
];

const metricCards = [
  {
    key: 'total',
    label: 'Total Results',
    icon: ClipboardList,
    accent: 'border-blue-500',
  },
  {
    key: 'validated',
    label: 'Validated',
    icon: CheckCircle,
    accent: 'border-green-500',
  },
  {
    key: 'pending',
    label: 'Pending Review',
    icon: Clock,
    accent: 'border-amber-500',
  },
  {
    key: 'rejected',
    label: 'Rejected / Disputed',
    icon: XCircle,
    accent: 'border-red-500',
  },
];

const RESULTS_QUERY_KEY = 'results';

const truncateText = (value: string | undefined | null, max = 120): string => {
  if (!value) return '';
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
};

const downloadMarkdownFile = async (resultId: string, type: 'result' | 'validation' = 'result') => {
  try {
    // Construct the API endpoint URL
    const endpoint = type === 'result'
      ? `/api/results/${resultId}/download`
      : `/api/results/${resultId}/validation/download`;

    // Fetch the file
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`);
    }

    // Extract filename from Content-Disposition header if available
    const contentDisposition = response.headers.get('content-disposition');
    let filename = type === 'result' ? 'result.md' : 'validation_report.md';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?(.+)"?/);
      if (match) {
        filename = match[1];
      }
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading file:', error);
    alert('Failed to download the file. Please try again.');
  }
};

const ResultContentDialog: React.FC<{
  resultId: string | null;
  result?: ResultSummary | null;
  onClose: () => void;
}> = ({ resultId, result, onClose }) => {
  const { data, isLoading, error } = useQuery<ResultContentResponse | null>({
    queryKey: ['result-content', resultId],
    queryFn: () => (resultId ? apiService.getResultContent(resultId) : null),
    enabled: Boolean(resultId),
  });

  return (
    <Dialog open={Boolean(resultId)} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle title={result?.summary || resultId || ''}>
            Result: {truncateText(result?.summary || resultId || '', 100)}
          </DialogTitle>
          {result && (
            <DialogDescription asChild>
              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                <Badge variant="outline" className="uppercase">
                  {result.scope}
                </Badge>
                {result.workflow_name && (
                  <span>
                    Workflow: <span className="font-semibold">{result.workflow_name}</span>
                  </span>
                )}
                {result.task_id && (
                  <span>
                    Task ID: <span className="font-mono">{result.task_id}</span>
                  </span>
                )}
                <span>
                  Submitted: {format(new Date(result.created_at), 'PPpp')}
                </span>
                {result.validated_at && (
                  <span>
                    Validated: {format(new Date(result.validated_at), 'PPpp')}
                  </span>
                )}
              </div>
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="space-y-4">
          {isLoading && (
            <div className="text-sm text-gray-500">Loading content...</div>
          )}
          {error && (
            <div className="text-sm text-red-500">
              Failed to load result content.
            </div>
          )}
          {data === null && !isLoading && !error && (
            <div className="rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-600">
              Result content is not available yet.
            </div>
          )}
          {data && (
            <ScrollArea className="max-h-[60vh] rounded border">
              <div className="markdown-body p-4 overflow-x-auto max-w-full">
                <ReactMarkdown
                  rehypePlugins={[rehypeHighlight]}
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ node, ...props }) => (
                      <a
                        {...props}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-600 underline hover:text-blue-700"
                      />
                    ),
                    pre: ({ children, ...props }) => (
                      <pre className="overflow-x-auto" {...props}>
                        {children}
                      </pre>
                    ),
                    code: ({ inline, className, children, ...props }) => (
                      inline ? (
                        <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs break-words" {...props}>
                          {children}
                        </code>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      )
                    ),
                    p: ({ children, ...props }) => (
                      <p className="break-words overflow-wrap-anywhere" {...props}>
                        {children}
                      </p>
                    ),
                    h1: ({ children, ...props }) => (
                      <h1 className="break-words" {...props}>
                        {children}
                      </h1>
                    ),
                    h2: ({ children, ...props }) => (
                      <h2 className="break-words" {...props}>
                        {children}
                      </h2>
                    ),
                    h3: ({ children, ...props }) => (
                      <h3 className="break-words" {...props}>
                        {children}
                      </h3>
                    ),
                  }}
                >
                  {data.content}
                </ReactMarkdown>
              </div>
            </ScrollArea>
          )}

          <div className="flex justify-between text-sm text-gray-600">
            {resultId && (
              <button
                onClick={() => downloadMarkdownFile(resultId, 'result')}
                className="inline-flex items-center text-blue-600 hover:text-blue-700"
              >
                <Download className="w-4 h-4 mr-1" />
                Download Markdown
              </button>
            )}
            {result?.task_id && (
              <span className="flex items-center gap-1 text-gray-500">
                <FileText className="w-4 h-4" />
                Linked Task: <span className="font-mono">{result.task_id}</span>
              </span>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const ResultValidationDialog: React.FC<{
  resultId: string | null;
  onClose: () => void;
}> = ({ resultId, onClose }) => {
  const { data, isLoading, error } = useQuery<ResultValidationDetail | null>({
    queryKey: ['result-validation', resultId],
    queryFn: () => (resultId ? apiService.getResultValidation(resultId) : null),
    enabled: Boolean(resultId),
  });

  return (
    <Dialog open={Boolean(resultId)} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Validation Report</DialogTitle>
          {data && (
            <DialogDescription asChild>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm">
                  <StatusBadge status={data.status} size="sm" />
                  {data.validator_agent_id && (
                    <span className="text-gray-600">
                      Validator: <span className="font-mono">{data.validator_agent_id}</span>
                    </span>
                  )}
                </div>
                <div className="flex flex-col text-xs text-gray-500">
                  {data.started_at && (
                    <span>
                      Started: {format(new Date(data.started_at), 'PPpp')}
                    </span>
                  )}
                  {data.completed_at && (
                    <span>
                      Completed: {format(new Date(data.completed_at), 'PPpp')}
                    </span>
                  )}
                </div>
              </div>
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="space-y-4">
          {isLoading && (
            <div className="text-sm text-gray-500">Loading validation...</div>
          )}
          {error && (
            <div className="text-sm text-red-500">
              Failed to load validation details.
            </div>
          )}
          {data === null && !isLoading && !error && (
            <div className="rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-600">
              Validation details are not available yet.
            </div>
          )}
          {data && (
            <div className="space-y-4">
              {data.feedback && (
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-gray-700">Feedback</h4>
                  <ScrollArea className="max-h-[40vh] rounded border">
                    <div className="markdown-body p-4 overflow-x-auto max-w-full">
                      <ReactMarkdown
                        rehypePlugins={[rehypeHighlight]}
                        remarkPlugins={[remarkGfm]}
                        components={{
                          a: ({ node, ...props }) => (
                            <a
                              {...props}
                              target="_blank"
                              rel="noreferrer"
                              className="text-blue-600 underline hover:text-blue-700"
                            />
                          ),
                          pre: ({ children, ...props }) => (
                            <pre className="overflow-x-auto" {...props}>
                              {children}
                            </pre>
                          ),
                          code: ({ inline, className, children, ...props }) => (
                            inline ? (
                              <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs break-words" {...props}>
                                {children}
                              </code>
                            ) : (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            )
                          ),
                          p: ({ children, ...props }) => (
                            <p className="break-words overflow-wrap-anywhere" {...props}>
                              {children}
                            </p>
                          ),
                          h1: ({ children, ...props }) => (
                            <h1 className="break-words" {...props}>
                              {children}
                            </h1>
                          ),
                          h2: ({ children, ...props }) => (
                            <h2 className="break-words" {...props}>
                              {children}
                            </h2>
                          ),
                          h3: ({ children, ...props }) => (
                            <h3 className="break-words" {...props}>
                              {children}
                            </h3>
                          ),
                        }}
                      >
                        {data.feedback}
                      </ReactMarkdown>
                    </div>
                  </ScrollArea>
                </div>
              )}
              {data.evidence && data.evidence.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-gray-700">Evidence</h4>
                  <ScrollArea className="max-h-[40vh] rounded border p-2">
                    <div className="space-y-2">
                      {data.evidence.map((item, index) => (
                      <div
                        key={`${item.criterion}-${index}`}
                        className="flex items-start justify-between rounded border px-3 py-2"
                      >
                        <div>
                          <p className="text-sm font-medium text-gray-800" title={item.criterion}>
                            {truncateText(item.criterion, 80)}
                          </p>
                          {item.notes && (
                            <p className="text-xs text-gray-500 mt-1" title={item.notes}>
                              {truncateText(item.notes, 120)}
                            </p>
                          )}
                          {item.artifact_path && (
                            <a
                              href={item.artifact_path}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="mt-1 inline-flex items-center text-xs text-blue-600 hover:text-blue-700"
                            >
                              <ExternalLink className="w-3 h-3 mr-1" />
                              Evidence artifact
                            </a>
                          )}
                        </div>
                        <Badge
                          variant={item.passed ? 'outline' : 'destructive'}
                          className={cn(
                            'ml-3 flex items-center gap-1 text-xs',
                            item.passed ? 'text-green-700 border-green-200' : 'text-red-700'
                          )}
                        >
                          {item.passed ? 'PASS' : 'FAIL'}
                        </Badge>
                      </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
              {resultId && (
                <button
                  onClick={() => downloadMarkdownFile(resultId, 'validation')}
                  className="inline-flex items-center text-sm text-blue-600 hover:text-blue-700"
                >
                  <Download className="w-4 h-4 mr-1" />
                  Download Report
                </button>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

const formatRelativeTime = (timestamp: string | null | undefined) => {
  if (!timestamp) return '—';
  return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
};

const Results: React.FC = () => {
  const [scope, setScope] = useState<ScopeFilter>('all');
  const [status, setStatus] = useState<ResultStatus | 'all'>('all');
  const [workflowId, setWorkflowId] = useState<string>('all');
  const [agentId, setAgentId] = useState<string>('all');
  const [dateRange, setDateRange] = useState<DateRangeFilter>('all');
  const [searchInput, setSearchInput] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [highlightedRows, setHighlightedRows] = useState<Set<string>>(new Set());
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);
  const [selectedValidationId, setSelectedValidationId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [connectivityWarning, setConnectivityWarning] = useState<string | null>(null);

  const queryClient = useQueryClient();
  const { subscribe } = useWebSocket();

  useEffect(() => {
    setSearchInput(activeSearch);
  }, [activeSearch]);

  const queryFilters = useMemo(
    () => ({ scope, status, workflowId, agentId, dateRange, search: activeSearch }),
    [scope, status, workflowId, agentId, dateRange, activeSearch]
  );

  const {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery<ResultSummary[]>({
    queryKey: [RESULTS_QUERY_KEY, queryFilters],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (scope !== 'all') params.scope = scope;
      if (status !== 'all') params.status = status;
      if (workflowId !== 'all') params.workflow_id = workflowId;
      if (agentId !== 'all') params.agent_id = agentId;
      if (activeSearch) params.search = activeSearch;
      if (dateRange !== 'all') {
        const now = new Date();
        let delta = 0;
        if (dateRange === '24h') delta = 24 * 60 * 60 * 1000;
        if (dateRange === '7d') delta = 7 * 24 * 60 * 60 * 1000;
        if (dateRange === '30d') delta = 30 * 24 * 60 * 60 * 1000;
        params.date_from = new Date(now.getTime() - delta).toISOString();
        params.date_to = now.toISOString();
      }

      try {
        const resultData = await apiService.getResults(params as any);
        setConnectivityWarning(null);
        return resultData;
      } catch (err) {
        if (isAxiosError(err) && !err.response) {
          setConnectivityWarning('Results API is unreachable. Showing empty state until connection is restored.');
          return [];
        }
        throw err;
      }
    },
    refetchInterval: 30000,
  });

  const results = data ?? [];

  useEffect(() => {
    const unsubscribeReported = subscribe('results_reported', (message) => {
      if (message?.result_id) {
        setHighlightedRows((prev) => {
          const next = new Set(Array.from(prev));
          next.add(message.result_id);
          return next;
        });
        setTimeout(() => {
          setHighlightedRows((prev) => {
            const next = new Set(Array.from(prev));
            next.delete(message.result_id);
            return next;
          });
        }, 4000);
      }
      queryClient.invalidateQueries({ queryKey: [RESULTS_QUERY_KEY] });
    });

    const unsubscribeValidated = subscribe('result_validation_completed', () => {
      queryClient.invalidateQueries({ queryKey: [RESULTS_QUERY_KEY] });
    });

    return () => {
      unsubscribeReported();
      unsubscribeValidated();
    };
  }, [subscribe, queryClient]);

  useEffect(() => {
    setExpandedRows(new Set());
  }, [scope, status, workflowId, agentId, dateRange, activeSearch]);

  const metrics = useMemo(() => {
    const counts = {
      total: results.length,
      validated: 0,
      pending: 0,
      rejected: 0,
    };

    results.forEach((result) => {
      if (statusBuckets.validated.includes(result.status)) {
        counts.validated += 1;
      }
      if (statusBuckets.pending.includes(result.status)) {
        counts.pending += 1;
      }
      if (statusBuckets.rejected.includes(result.status)) {
        counts.rejected += 1;
      }
    });

    return counts;
  }, [results]);

  const workflows = useMemo(() => {
    const map = new Map<string, string>();
    results.forEach((result) => {
      if (result.workflow_id) {
        map.set(result.workflow_id, result.workflow_name || result.workflow_id);
      }
    });
    return Array.from(map.entries());
  }, [results]);

  const agents = useMemo(() => {
    const map = new Map<string, string>();
    results.forEach((result) => {
      if (result.agent_id) {
        map.set(result.agent_id, result.agent_label || result.agent_id);
      }
    });
    return Array.from(map.entries());
  }, [results]);

  const handleToggleRow = (resultId: string) => {
    setExpandedRows((prev) => {
      const next = new Set(Array.from(prev));
      if (next.has(resultId)) {
        next.delete(resultId);
      } else {
        next.add(resultId);
      }
      return next;
    });
  };

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setActiveSearch(searchInput.trim());
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setActiveSearch('');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Results</h1>
            <p className="text-gray-600">
              Monitor submitted solutions, validation status, and supporting evidence
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2"
          >
            <RefreshCw className={cn('w-4 h-4', isFetching ? 'animate-spin' : '')} />
            Refresh
          </Button>
        </div>
      </div>

      {connectivityWarning && (
        <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
          {connectivityWarning}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metricCards.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.key} className={cn('border-l-4', metric.accent)}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-base font-medium text-gray-600">
                  {metric.label}
                  <Icon className="w-5 h-5 text-gray-400" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-semibold text-gray-900">
                  {metrics[metric.key as keyof typeof metrics]}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="rounded-lg border bg-white shadow-sm">
        <div className="flex flex-col gap-4 border-b px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Scope:</span>
            {(['all', 'workflow', 'task'] as ScopeFilter[]).map((option) => (
              <Button
                key={option}
                variant={scope === option ? 'default' : 'outline'}
                size="sm"
                onClick={() => setScope(option)}
              >
                {option === 'all' ? 'All' : option.charAt(0).toUpperCase() + option.slice(1)}
              </Button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            {statusOptions.map((option) => (
              <Button
                key={option.value}
                size="sm"
                variant={status === option.value ? 'default' : 'ghost'}
                onClick={() => setStatus(option.value)}
              >
                {option.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-4 border-b px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
            <label className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-gray-400" />
              <select
                value={workflowId}
                onChange={(event) => setWorkflowId(event.target.value)}
                className="rounded border border-gray-200 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="all">All workflows</option>
                {workflows.map(([id, name]) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex items-center gap-2">
              <User className="w-4 h-4 text-gray-400" />
              <select
                value={agentId}
                onChange={(event) => setAgentId(event.target.value)}
                className="rounded border border-gray-200 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="all">All agents</option>
                {agents.map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-400" />
              <select
                value={dateRange}
                onChange={(event) => setDateRange(event.target.value as DateRangeFilter)}
                className="rounded border border-gray-200 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="all">All time</option>
                <option value="24h">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
              </select>
            </label>
          </div>

          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="search"
                placeholder="Search by summary, ID, or text"
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                className="h-10 rounded-md border border-gray-200 pl-10 pr-10 text-sm focus:border-blue-500 focus:outline-none"
              />
              {activeSearch && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-gray-600"
                >
                  Clear
                </button>
              )}
            </div>
            <Button type="submit" size="sm">
              Apply
            </Button>
          </form>
        </div>

        <div className="px-6 py-4">
          <div className="hidden border-b pb-3 text-xs font-medium text-gray-500 lg:grid lg:grid-cols-12">
            <span className="col-span-2">Status</span>
            <span className="col-span-4">Summary</span>
            <span className="col-span-2">Workflow</span>
            <span className="col-span-2">Task</span>
            <span className="col-span-1">Agent</span>
            <span className="col-span-1 text-right">Actions</span>
          </div>

          {isLoading && (
            <div className="flex h-32 items-center justify-center text-gray-500">
              Loading results...
            </div>
          )}

          {error && (
            <div className="rounded border border-red-200 bg-red-50 p-4 text-red-600">
              Failed to load results. Please try refreshing.
            </div>
          )}

          {!isLoading && !error && results.length === 0 && (
            <div className="flex h-32 flex-col items-center justify-center text-gray-500">
              <ClipboardList className="mb-2 h-6 w-6 text-gray-400" />
              <p>No results match the current filters.</p>
            </div>
          )}

          <div className="space-y-3">
            <AnimatePresence>
              {results.map((result) => {
                const isExpanded = expandedRows.has(result.result_id);
                const isHighlighted = highlightedRows.has(result.result_id);
                return (
                  <motion.div
                    key={result.result_id}
                    initial={isHighlighted ? { backgroundColor: '#DBEAFE' } : false}
                    animate={{ backgroundColor: isHighlighted ? '#DBEAFE' : '#FFFFFF' }}
                    transition={{ duration: 0.5, backgroundColor: { duration: 2.5 } }}
                    className="rounded border border-gray-100 bg-white shadow-sm"
                  >
                    <div
                      className="flex flex-col gap-3 px-4 py-3 lg:grid lg:grid-cols-12 lg:items-center"
                    >
                      <div className="flex items-center justify-between lg:col-span-2">
                        <button
                          onClick={() => handleToggleRow(result.result_id)}
                          className="flex items-center gap-2 text-left text-sm font-medium text-gray-800 hover:text-blue-600"
                        >
                          <span className="lg:hidden">
                            {isExpanded ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : (
                              <ChevronDown className="h-4 w-4" />
                            )}
                          </span>
                          <StatusBadge status={result.status} size="sm" />
                        </button>
                        <Badge variant="outline" className="uppercase lg:hidden">
                          {result.scope}
                        </Badge>
                      </div>

                      <div className="lg:col-span-4">
                        <p className="text-sm font-medium text-gray-900 line-clamp-3" title={result.summary || undefined}>
                          {truncateText(result.summary, 240)}
                        </p>
                        <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                          <span>
                            Submitted {formatRelativeTime(result.created_at)}
                          </span>
                          {result.validated_at && (
                            <span>
                              Validated {formatRelativeTime(result.validated_at)}
                            </span>
                          )}
                          {result.validation_feedback && (
                            <span
                              className="hidden lg:inline text-gray-500 line-clamp-1"
                              title={result.validation_feedback}
                            >
                              Feedback: {truncateText(result.validation_feedback, 120)}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600 lg:col-span-2">
                        <Badge variant="outline" className="hidden uppercase lg:inline-flex">
                          {result.scope}
                        </Badge>
                        <div className="flex items-center gap-2">
                          <GitBranch className="w-4 h-4 text-gray-400" />
                          {result.workflow_name || result.workflow_id || '—'}
                        </div>
                      </div>

                      <div className="lg:col-span-2">
                        {result.task_id ? (
                          <div className="flex items-center gap-2 text-sm">
                            <FileText className="w-4 h-4 text-gray-400" />
                            <button
                              type="button"
                              className="text-blue-600 hover:text-blue-700"
                              onClick={(event) => {
                                event.stopPropagation();
                                setSelectedTaskId(result.task_id!);
                              }}
                            >
                              {result.task_id}
                            </button>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-500">Workflow-level</span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-sm text-gray-600 lg:col-span-1">
                        <User className="w-4 h-4 text-gray-400" />
                        {result.agent_label || result.agent_id}
                      </div>

                      <div className="flex items-center justify-end gap-2 lg:col-span-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="View result content"
                          onClick={() => {
                            setSelectedResultId(result.result_id);
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="View validation report"
                          onClick={() => setSelectedValidationId(result.result_id)}
                          disabled={statusBuckets.pending.includes(result.status)}
                          title={
                            statusBuckets.pending.includes(result.status)
                              ? 'Validation not completed yet'
                              : 'View validation detail'
                          }
                        >
                          <ShieldCheck className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    <AnimatePresence initial={false}>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.25 }}
                          className="border-t bg-gray-50"
                        >
                          <div className="grid gap-4 px-5 py-4 md:grid-cols-2">
                            <div className="space-y-2">
                              <h4 className="text-sm font-semibold text-gray-700">
                                Validation Summary
                              </h4>
                              <p className="text-sm text-gray-600 whitespace-pre-line" title={result.validation_feedback || undefined}>
                                {truncateText(result.validation_feedback || 'No validation feedback available yet.', 320)}
                              </p>
                              <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                                <span>
                                  Result ID: <span className="font-mono">{result.result_id}</span>
                                </span>
                                {result.result_type && (
                                  <span>
                                    Type: <span className="font-semibold">{result.result_type}</span>
                                  </span>
                                )}
                              </div>
                              <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                                <span>
                                  Submitted: {format(new Date(result.created_at), 'PPpp')}
                                </span>
                                {result.validated_at && (
                                  <span>
                                    Validated: {format(new Date(result.validated_at), 'PPpp')}
                                  </span>
                                )}
                              </div>
                            </div>

                            <div className="space-y-2">
                              <h4 className="text-sm font-semibold text-gray-700">
                                Evidence Snapshot
                              </h4>
                              {result.validation_evidence && result.validation_evidence.length > 0 ? (
                                <div className="space-y-2">
                                  {result.validation_evidence.slice(0, 3).map((evidence, index) => (
                                    <div
                                      key={`${result.result_id}-evidence-${index}`}
                                      className="flex items-center justify-between rounded border border-gray-200 bg-white px-3 py-2"
                                    >
                                      <div>
                                        <p className="text-sm font-medium text-gray-800" title={evidence.criterion}>
                                          {truncateText(evidence.criterion, 80)}
                                        </p>
                                        {evidence.notes && (
                                          <p className="text-xs text-gray-500" title={evidence.notes}>
                                            {truncateText(evidence.notes, 120)}
                                          </p>
                                        )}
                                      </div>
                                      <Badge
                                        variant={evidence.passed ? 'outline' : 'destructive'}
                                        className={cn(
                                          'text-xs',
                                          evidence.passed
                                            ? 'border-green-200 text-green-700'
                                            : 'text-red-700'
                                        )}
                                      >
                                        {evidence.passed ? 'PASS' : 'FAIL'}
                                      </Badge>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-gray-500">No evidence attached yet.</p>
                              )}

                              <div className="flex flex-wrap gap-4 text-xs text-blue-600">
                                <button
                                  onClick={() => downloadMarkdownFile(result.result_id, 'result')}
                                  className="inline-flex items-center gap-1 hover:text-blue-700"
                                >
                                  <Download className="h-4 w-4" />
                                  Result markdown
                                </button>
                                {!statusBuckets.pending.includes(result.status) && (
                                  <button
                                    onClick={() => downloadMarkdownFile(result.result_id, 'validation')}
                                    className="inline-flex items-center gap-1 hover:text-blue-700"
                                  >
                                    <Download className="h-4 w-4" />
                                    Validation report
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <ResultContentDialog
        resultId={selectedResultId}
        result={results.find((result) => result.result_id === selectedResultId)}
        onClose={() => setSelectedResultId(null)}
      />

      <ResultValidationDialog
        resultId={selectedValidationId}
        onClose={() => setSelectedValidationId(null)}
      />

      <TaskDetailModal
        taskId={selectedTaskId}
        onClose={() => setSelectedTaskId(null)}
        onNavigateToTask={(taskId) => setSelectedTaskId(taskId)}
      />
    </div>
  );
};

export default Results;
