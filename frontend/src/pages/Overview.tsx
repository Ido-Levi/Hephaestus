import React, { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import {
  Compass,
  Target,
  Activity,
  Bot,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Clock,
  Layers,
  MessageSquare
} from 'lucide-react';
import { apiService } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';
import { useWebSocket } from '@/context/WebSocketContext';
import SystemHealthCard from '@/components/overview/SystemHealthCard';
import ConductorSummaryCard from '@/components/overview/ConductorSummaryCard';
import SteeringEventsCard from '@/components/overview/SteeringEventsCard';
import TrajectoryTimeline from '@/components/overview/TrajectoryTimeline';
import PhaseDistributionCard from '@/components/overview/PhaseDistributionCard';
import SystemMetricsGraphs from '@/components/overview/SystemMetricsGraphs';
import BroadcastMessageDialog from '@/components/BroadcastMessageDialog';
import AgentDetailModal from '@/components/AgentDetailModal';
import TaskDetailModal from '@/components/TaskDetailModal';

export default function Overview() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { subscribe } = useWebSocket();
  const [showBroadcastDialog, setShowBroadcastDialog] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const { data: systemData, isLoading, error, refetch } = useQuery({
    queryKey: ['system-overview'],
    queryFn: apiService.getSystemOverview,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Subscribe to WebSocket events for real-time updates
  useEffect(() => {
    const unsubscribeGuardian = subscribe('guardian_analysis', () => {
      // Invalidate queries to refetch latest data
      queryClient.invalidateQueries({ queryKey: ['system-overview'] });
    });

    const unsubscribeConductor = subscribe('conductor_analysis', () => {
      queryClient.invalidateQueries({ queryKey: ['system-overview'] });
    });

    const unsubscribeSteering = subscribe('steering_intervention', () => {
      queryClient.invalidateQueries({ queryKey: ['system-overview'] });
    });

    return () => {
      unsubscribeGuardian();
      unsubscribeConductor();
      unsubscribeSteering();
    };
  }, [subscribe, queryClient]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Loading system overview...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500">Error loading system overview</div>
      </div>
    );
  }

  // Count active agents
  const activeAgentCount = systemData?.agent_alignments?.filter((a: any) => a.agent_id).length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <Compass className="w-8 h-8 mr-3 text-blue-600" />
            System Overview
          </h1>
          <p className="text-gray-600 mt-1">
            Real-time monitoring and trajectory analysis
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {systemData?.timestamp && (
            <Badge variant="outline" className="text-xs">
              Last update: {formatDistanceToNow(new Date(systemData.timestamp), { addSuffix: true })}
            </Badge>
          )}
          {activeAgentCount > 0 && (
            <Button
              onClick={() => setShowBroadcastDialog(true)}
              variant="outline"
              size="sm"
              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              Broadcast
            </Button>
          )}
          <button
            onClick={() => refetch()}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* System Health */}
        <div className="lg:col-span-1">
          <SystemHealthCard systemHealth={systemData?.system_health} />
        </div>

        {/* Phase Distribution */}
        <div className="lg:col-span-1 xl:col-span-2">
          <PhaseDistributionCard phases={systemData?.phase_distribution || []} />
        </div>

        {/* Conductor Summary - Full Width */}
        <div className="lg:col-span-2 xl:col-span-3">
          <ConductorSummaryCard analysis={systemData?.latest_conductor_analysis} />
        </div>

        {/* Recent Steering Events */}
        <div className="lg:col-span-1">
          <SteeringEventsCard events={systemData?.recent_steering_events || []} />
        </div>

        {/* Trajectory Timeline */}
        <div className="lg:col-span-1 xl:col-span-2">
          <TrajectoryTimeline alignments={systemData?.agent_alignments || []} />
        </div>
      </div>

      {/* System Metrics Graphs */}
      {systemData?.metrics_history && systemData.metrics_history.length > 0 && (
        <div className="mt-6">
          <SystemMetricsGraphs
            metricsHistory={systemData.metrics_history}
            phases={systemData?.phase_distribution?.map((p: any) => p.name) || []}
          />
        </div>
      )}

      {/* Agent Alignment Details */}
      {systemData?.agent_alignments && systemData.agent_alignments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bot className="w-5 h-5 mr-2 text-blue-600" />
              Agent Trajectory Status
            </CardTitle>
            <CardDescription>
              Individual agent alignment and steering needs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {systemData.agent_alignments.map((agent: any) => (
                <button
                  key={agent.agent_id}
                  onClick={() => setSelectedAgentId(agent.agent_id)}
                  className={cn(
                    "border rounded-lg p-4 text-left transition-all hover:shadow-lg hover:scale-105",
                    agent.needs_steering ? "border-yellow-400 bg-yellow-50 hover:bg-yellow-100" : "border-gray-200 hover:bg-gray-50"
                  )}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <Bot className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="font-mono text-xs text-gray-500">{agent.agent_id.substring(0, 8)}</p>
                        <p className="text-sm font-medium text-gray-800 truncate">Click to view details</p>
                      </div>
                    </div>
                    {agent.needs_steering && (
                      <Badge variant="outline" className="bg-yellow-100 text-yellow-800 flex-shrink-0">
                        Needs Steering
                      </Badge>
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500">Alignment</span>
                      <span className={cn(
                        "text-sm font-semibold",
                        agent.alignment_score > 0.8 ? "text-green-600" :
                        agent.alignment_score > 0.4 ? "text-yellow-600" :
                        "text-red-600"
                      )}>
                        {Math.round((agent.alignment_score || 0) * 100)}%
                      </span>
                    </div>
                    <Progress
                      value={(agent.alignment_score || 0) * 100}
                      className={cn(
                        "h-2",
                        agent.alignment_score > 0.8 ? "[&>div]:bg-green-500" :
                        agent.alignment_score > 0.4 ? "[&>div]:bg-yellow-500" :
                        "[&>div]:bg-red-500"
                      )}
                    />
                    <div className="text-xs text-gray-500">
                      Phase: {agent.current_phase || 'Unknown'}
                    </div>
                    <div className="text-xs text-gray-400">
                      Updated {formatDistanceToNow(new Date(agent.last_update), { addSuffix: true })}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Broadcast Message Dialog */}
      <BroadcastMessageDialog
        open={showBroadcastDialog}
        onClose={() => setShowBroadcastDialog(false)}
        activeAgentCount={activeAgentCount}
      />

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
    </div>
  );
}