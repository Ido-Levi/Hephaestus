import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  FileCode,
  GitMerge,
  Loader2,
  Play,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import { apiService } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';

interface PendingDiff {
  id: string;
  file_path: string;
  status: string;
  batch_id?: string;
  merge_agent_id: string;
  worktree_agent_id: string;
  resolution_choice?: string;
  resolution_reasoning?: string;
  created_at?: string;
  resolved_at?: string;
}

interface DiffResolutionStats {
  total_pending: number;
  total_processing: number;
  total_resolved: number;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500',
  processing: 'bg-blue-500',
  resolved: 'bg-green-500',
  failed: 'bg-red-500',
};

const statusIcons: Record<string, React.ElementType> = {
  pending: Clock,
  processing: Loader2,
  resolved: CheckCircle,
  failed: XCircle,
};

export default function DiffResolutionPanel() {
  const queryClient = useQueryClient();
  const [selectedDiff, setSelectedDiff] = useState<PendingDiff | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  // Fetch pending diffs
  const { data: diffsData, isLoading, error, refetch } = useQuery({
    queryKey: ['pending-diffs', statusFilter],
    queryFn: () => apiService.getPendingDiffs(statusFilter, 100),
    refetchInterval: 5000,
  });

  // Mutation to resolve batch
  const resolveBatchMutation = useMutation({
    mutationFn: () => apiService.resolveDiffBatch('diff-resolver-agent'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-diffs'] });
    },
  });

  // Mutation to apply resolved diffs
  const applyDiffsMutation = useMutation({
    mutationFn: (diffIds: string[]) => apiService.applyResolvedDiffs('diff-resolver-agent', diffIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-diffs'] });
    },
  });

  const stats: DiffResolutionStats = {
    total_pending: diffsData?.total_pending || 0,
    total_processing: diffsData?.total_processing || 0,
    total_resolved: diffsData?.total_resolved || 0,
  };

  const diffs = diffsData?.diffs || [];
  const resolvedDiffs = diffs.filter((d) => d.status === 'resolved');

  const handleResolveBatch = () => {
    resolveBatchMutation.mutate();
  };

  const handleApplyResolved = () => {
    const diffIds = resolvedDiffs.map((d) => d.id);
    if (diffIds.length > 0) {
      applyDiffsMutation.mutate(diffIds);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-500">
        <AlertCircle className="w-6 h-6 mr-2" />
        Failed to load diff resolutions
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center">
            <GitMerge className="w-6 h-6 mr-2 text-purple-600" />
            Diff Resolution
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            AI-powered conflict resolution for merge conflicts
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Pending</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.total_pending}</p>
              </div>
              <Clock className="w-8 h-8 text-yellow-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Processing</p>
                <p className="text-2xl font-bold text-blue-600">{stats.total_processing}</p>
              </div>
              <Loader2 className="w-8 h-8 text-blue-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Resolved</p>
                <p className="text-2xl font-bold text-green-600">{stats.total_resolved}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button
          onClick={handleResolveBatch}
          disabled={stats.total_pending === 0 || resolveBatchMutation.isPending}
          className="bg-purple-600 hover:bg-purple-700"
        >
          {resolveBatchMutation.isPending ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Play className="w-4 h-4 mr-2" />
          )}
          Resolve Next Batch (3)
        </Button>
        <Button
          onClick={handleApplyResolved}
          disabled={resolvedDiffs.length === 0 || applyDiffsMutation.isPending}
          variant="outline"
        >
          {applyDiffsMutation.isPending ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <CheckCircle className="w-4 h-4 mr-2" />
          )}
          Apply {resolvedDiffs.length} Resolved
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['all', 'pending', 'processing', 'resolved', 'failed'].map((filter) => (
          <Button
            key={filter}
            variant={statusFilter === (filter === 'all' ? undefined : filter) ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter(filter === 'all' ? undefined : filter)}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
          </Button>
        ))}
      </div>

      {/* Diff List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Diffs ({diffs.length})</CardTitle>
          <CardDescription>Click on a diff to see details</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            {diffs.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-gray-500">
                No diffs found
              </div>
            ) : (
              <div className="space-y-2">
                {diffs.map((diff) => {
                  const StatusIcon = statusIcons[diff.status] || AlertCircle;
                  const isProcessing = diff.status === 'processing';

                  return (
                    <div
                      key={diff.id}
                      className={cn(
                        'p-3 rounded-lg border cursor-pointer transition-colors',
                        selectedDiff?.id === diff.id
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                      onClick={() => setSelectedDiff(diff)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <FileCode className="w-4 h-4 text-gray-400" />
                          <span className="font-mono text-sm truncate max-w-[300px]">
                            {diff.file_path}
                          </span>
                        </div>
                        <Badge
                          className={cn(
                            'text-white',
                            statusColors[diff.status] || 'bg-gray-500'
                          )}
                        >
                          <StatusIcon
                            className={cn('w-3 h-3 mr-1', isProcessing && 'animate-spin')}
                          />
                          {diff.status}
                        </Badge>
                      </div>
                      <div className="mt-2 text-xs text-gray-500 flex items-center gap-4">
                        <span>Agent: {diff.worktree_agent_id.slice(0, 8)}...</span>
                        {diff.created_at && (
                          <span>
                            Created {formatDistanceToNow(new Date(diff.created_at), { addSuffix: true })}
                          </span>
                        )}
                        {diff.resolution_choice && (
                          <Badge variant="outline" className="text-xs">
                            {diff.resolution_choice}
                          </Badge>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Selected Diff Details */}
      {selectedDiff && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <FileCode className="w-5 h-5 mr-2" />
              {selectedDiff.file_path}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Status</p>
                  <Badge className={cn('mt-1', statusColors[selectedDiff.status] || 'bg-gray-500')}>
                    {selectedDiff.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Resolution</p>
                  <p className="mt-1">{selectedDiff.resolution_choice || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Merge Agent</p>
                  <p className="mt-1 font-mono text-sm">{selectedDiff.merge_agent_id}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Worktree Agent</p>
                  <p className="mt-1 font-mono text-sm">{selectedDiff.worktree_agent_id}</p>
                </div>
              </div>
              {selectedDiff.resolution_reasoning && (
                <>
                  <hr className="border-gray-200" />
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-2">AI Reasoning</p>
                    <p className="text-sm bg-gray-50 p-3 rounded-lg">
                      {selectedDiff.resolution_reasoning}
                    </p>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mutation Results */}
      {resolveBatchMutation.isSuccess && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800">
            ✓ {resolveBatchMutation.data.message}
          </p>
        </div>
      )}
      {resolveBatchMutation.isError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">
            ✗ Failed to resolve batch: {(resolveBatchMutation.error as Error).message}
          </p>
        </div>
      )}
      {applyDiffsMutation.isSuccess && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800">
            ✓ {applyDiffsMutation.data.message}
            {applyDiffsMutation.data.commit_sha && (
              <span className="font-mono text-xs ml-2">
                ({applyDiffsMutation.data.commit_sha.slice(0, 8)})
              </span>
            )}
          </p>
        </div>
      )}
    </div>
  );
}
