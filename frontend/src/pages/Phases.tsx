import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Layers, Users, ListTodo, RefreshCw, ArrowRight, Eye, FileCode } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { cn } from '@/lib/utils';
import { useSocket } from '@/hooks/useSocket';
import { useWorkflow } from '@/context/WorkflowContext';
import { apiService } from '@/services/api';
import WorkflowSelector from '@/components/WorkflowSelector';

interface Phase {
  id: string;
  order: number;
  name: string;
  description: string;
  active_agents: number;
  total_tasks: number;
  completed_tasks: number;
  active_tasks: number;
  pending_tasks: number;
  cli_config?: {
    cli_tool?: string | null;
    cli_model?: string | null;
    glm_api_token_env?: string | null;
  };
}

interface WorkflowInfo {
  id: string | null;
  name: string;
  status: string;
  total_phases: number;
  phases: Phase[];
}

interface PhaseActivity {
  type: 'cross_phase_task' | 'task_completed' | 'agent_started' | 'agent_stopped';
  timestamp: string;
  from_phase?: number;
  to_phase?: number;
  agent_id?: string;
  task_id?: string;
  description: string;
}

export default function Phases() {
  const [activities, setActivities] = useState<PhaseActivity[]>([]);
  const [phaseData, setPhaseData] = useState<{[key: string]: any}>({});
  const [loadingPhase, setLoadingPhase] = useState<{[key: string]: boolean}>({});
  const [selectedDefinitionId, setSelectedDefinitionId] = useState<string | null>(null);
  const navigate = useNavigate();
  const socket = useSocket();
  const { selectedExecutionId, definitions } = useWorkflow();

  // Get the selected definition
  const selectedDefinition = definitions.find(d => d.id === selectedDefinitionId);

  const { data: workflowData, isLoading: loading, refetch } = useQuery({
    queryKey: ['workflow-execution', selectedExecutionId],
    queryFn: () => selectedExecutionId ? apiService.getWorkflowExecution(selectedExecutionId) : null,
    enabled: !!selectedExecutionId,
    refetchInterval: 5000,
  });

  // Transform workflowData to match expected format
  const workflow: WorkflowInfo | null = workflowData ? {
    id: workflowData.id,
    name: workflowData.definition_name || 'Workflow',
    status: workflowData.status,
    total_phases: workflowData.phases?.length || 0,
    phases: workflowData.phases || [],
  } : null;

  useEffect(() => {
    // Set up WebSocket listeners for real-time updates
    if (socket) {
      socket.on('phase_activity', (activity: PhaseActivity) => {
        setActivities((prev) => [activity, ...prev].slice(0, 50)); // Keep last 50 activities
      });

      socket.on('phase_update', () => {
        refetch(); // Refresh phase data
      });
    }

    return () => {
      if (socket) {
        socket.off('phase_activity');
        socket.off('phase_update');
      }
    };
  }, [socket, refetch]);

  const getPhaseColor = (order: number, total: number) => {
    const opacity = 0.3 + (0.7 * ((order - 1) / Math.max(total - 1, 1)));
    return `rgba(59, 130, 246, ${opacity})`;
  };

  const navigateToTasks = (phaseId: string) => {
    navigate(`/tasks?phase=${phaseId}`);
  };

  const fetchPhaseDetails = async (phaseId: string) => {
    if (phaseData[phaseId]) return; // Already loaded

    setLoadingPhase(prev => ({ ...prev, [phaseId]: true }));
    try {
      const response = await fetch(`http://localhost:8000/api/phases/${phaseId}/yaml`);
      const data = await response.json();
      setPhaseData(prev => ({ ...prev, [phaseId]: data }));
    } catch (error) {
      console.error('Failed to fetch phase details:', error);
      setPhaseData(prev => ({ ...prev, [phaseId]: { error: 'Failed to load phase details' } }));
    } finally {
      setLoadingPhase(prev => ({ ...prev, [phaseId]: false }));
    }
  };

  if (!selectedExecutionId) {
    // Show definition info if a definition is selected but no execution
    if (selectedDefinition) {
      return (
        <div className="container mx-auto p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <Layers className="h-8 w-8" />
                Workflow: {selectedDefinition.name}
              </h1>
              <p className="text-muted-foreground mt-1">
                {selectedDefinition.phases_count} phases - No active executions
              </p>
            </div>
            <div className="flex items-center gap-4">
              <WorkflowSelector onDefinitionChange={setSelectedDefinitionId} />
              <Button onClick={() => refetch()} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Loaded Workflow Definitions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileCode className="h-5 w-5 text-purple-600" />
                Loaded Workflow Definitions
              </CardTitle>
              <CardDescription>Available workflow types in the system</CardDescription>
            </CardHeader>
            <CardContent>
              {definitions.length === 0 ? (
                <p className="text-sm text-muted-foreground">No workflow definitions loaded</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {definitions.map((def) => (
                    <div
                      key={def.id}
                      className={cn(
                        "border rounded-lg p-3 transition-colors",
                        selectedDefinitionId === def.id
                          ? "bg-purple-100 border-purple-300"
                          : "bg-purple-50 border-purple-200"
                      )}
                    >
                      <div className="font-medium text-gray-800">{def.name}</div>
                      <div className="text-sm text-gray-600 line-clamp-2">{def.description}</div>
                      <div className="text-xs text-purple-600 mt-1">
                        {def.phases_count} phases
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Definition Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>{selectedDefinition.name}</CardTitle>
              <CardDescription>{selectedDefinition.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <Layers className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium">This workflow has {selectedDefinition.phases_count} phases</p>
                <p className="text-sm mt-2">
                  No executions available. Start a new execution to see phase details with task statistics.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Live Activity Feed */}
          <Card>
            <CardHeader>
              <CardTitle>Live Activity Feed</CardTitle>
              <CardDescription>Real-time phase activities from Hephaestus</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[300px] w-full rounded-md border p-4">
                <div className="text-center text-muted-foreground py-8">
                  No activities yet. Activities will appear here as agents work.
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      );
    }

    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Layers className="h-8 w-8" />
              Phases
            </h1>
            <p className="text-muted-foreground mt-1">View workflow phases</p>
          </div>
          <WorkflowSelector onDefinitionChange={setSelectedDefinitionId} />
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <p className="text-gray-500 text-lg">Select a workflow type to view phases</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Layers className="h-8 w-8" />
              Phases
            </h1>
            <p className="text-muted-foreground mt-1">View workflow phases</p>
          </div>
          <WorkflowSelector onDefinitionChange={setSelectedDefinitionId} />
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading workflow...</div>
        </div>
      </div>
    );
  }

  if (!workflow || workflow.total_phases === 0) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Layers className="h-8 w-8" />
              Phases
            </h1>
            <p className="text-muted-foreground mt-1">View workflow phases</p>
          </div>
          <WorkflowSelector onDefinitionChange={setSelectedDefinitionId} />
        </div>
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <Layers className="h-12 w-12 text-muted-foreground" />
          <div className="text-lg text-muted-foreground">No phases in this workflow</div>
          <p className="text-sm text-muted-foreground">This workflow does not have any phases configured</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Layers className="h-8 w-8" />
            Workflow: {workflow.name}
          </h1>
          <p className="text-muted-foreground mt-1">
            {workflow.total_phases} phases - Status: {workflow.status}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <WorkflowSelector onDefinitionChange={setSelectedDefinitionId} />
          <Button onClick={() => refetch()} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Loaded Workflow Definitions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileCode className="h-5 w-5 text-purple-600" />
            Loaded Workflow Definitions
          </CardTitle>
          <CardDescription>Available workflow types in the system</CardDescription>
        </CardHeader>
        <CardContent>
          {definitions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No workflow definitions loaded</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {definitions.map((def) => (
                <div
                  key={def.id}
                  className={cn(
                    "border rounded-lg p-3 transition-colors",
                    workflow?.id && workflowData?.definition_id === def.id
                      ? "bg-purple-100 border-purple-300"
                      : "bg-purple-50 border-purple-200"
                  )}
                >
                  <div className="font-medium text-gray-800">{def.name}</div>
                  <div className="text-sm text-gray-600 line-clamp-2">{def.description}</div>
                  <div className="text-xs text-purple-600 mt-1">
                    {def.phases_count} phases
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Active Phase Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Active Phase Distribution</CardTitle>
          <CardDescription>Current activity across all phases</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative h-12 bg-muted rounded-lg overflow-hidden">
            <div className="absolute inset-0 flex">
              {workflow.phases.map((phase) => {
                const _width = `${100 / workflow.total_phases}%`;
                const isActive = phase.active_agents > 0;
                return (
                  <div
                    key={phase.id}
                    className="relative flex-1 border-r border-background last:border-r-0"
                    style={{
                      backgroundColor: isActive ? getPhaseColor(phase.order, workflow.total_phases) : 'transparent',
                    }}
                  >
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-xs">
                      <span className="font-medium">P{phase.order}</span>
                      <span className="text-[10px]">
                        {phase.active_agents}/{phase.total_tasks}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="flex justify-between mt-2 text-xs text-muted-foreground">
            <span>agents/tasks</span>
          </div>
        </CardContent>
      </Card>

      {/* Phase Cards */}
      <Card>
        <CardHeader>
          <CardTitle>Phases</CardTitle>
          <CardDescription>Detailed view of each phase</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="w-full whitespace-nowrap rounded-md">
            <div className="flex gap-4 pb-4">
              {workflow.phases.map((phase) => (
                <Card
                  key={phase.id}
                  className="w-[280px] flex-shrink-0"
                  style={{
                    borderColor: getPhaseColor(phase.order, workflow.total_phases),
                    borderWidth: '2px',
                  }}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          style={{
                            backgroundColor: getPhaseColor(phase.order, workflow.total_phases),
                            color: phase.order > workflow.total_phases / 2 ? 'white' : 'rgb(30, 58, 138)',
                          }}
                        >
                          Phase {phase.order}
                        </Badge>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0"
                              onClick={() => fetchPhaseDetails(phase.id)}
                            >
                              <Eye className="h-3 w-3" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
                            <DialogHeader>
                              <DialogTitle>Phase {phase.order}: {phase.name}</DialogTitle>
                              <DialogDescription>
                                Detailed phase configuration and requirements
                              </DialogDescription>
                            </DialogHeader>
                            <div className="mt-4">
                              {loadingPhase[phase.id] ? (
                                <div className="flex items-center justify-center h-32">
                                  <div className="text-sm text-muted-foreground">Loading phase details...</div>
                                </div>
                              ) : phaseData[phase.id]?.error ? (
                                <div className="text-red-500 text-sm">{phaseData[phase.id].error}</div>
                              ) : phaseData[phase.id] ? (
                                <ScrollArea className="h-[400px] w-full">
                                  <div className="space-y-6 pr-4">
                                    {/* Description */}
                                    <div>
                                      <h4 className="font-semibold text-lg mb-2">Description</h4>
                                      <p className="text-sm text-muted-foreground leading-relaxed">
                                        {phaseData[phase.id].description}
                                      </p>
                                    </div>

                                    {/* Done Definitions */}
                                    <div>
                                      <h4 className="font-semibold text-lg mb-2">Done Definitions</h4>
                                      <ul className="space-y-1">
                                        {phaseData[phase.id].done_definitions?.map((def: string, index: number) => (
                                          <li key={index} className="flex items-start gap-2 text-sm">
                                            <span className="text-green-500 mt-1">✓</span>
                                            <span>{def}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    </div>

                                    {/* Additional Notes */}
                                    <div>
                                      <h4 className="font-semibold text-lg mb-2">Additional Notes</h4>
                                      <p className="text-sm text-muted-foreground leading-relaxed bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md">
                                        {phaseData[phase.id].additional_notes}
                                      </p>
                                    </div>

                                    {/* Expected Outputs */}
                                    <div>
                                      <h4 className="font-semibold text-lg mb-2">Expected Outputs</h4>
                                      <p className="text-sm text-muted-foreground leading-relaxed bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
                                        {phaseData[phase.id].outputs}
                                      </p>
                                    </div>

                                    {/* Next Steps */}
                                    <div>
                                      <h4 className="font-semibold text-lg mb-2">Next Steps</h4>
                                      <p className="text-sm text-muted-foreground leading-relaxed bg-purple-50 dark:bg-purple-900/20 p-3 rounded-md">
                                        {phaseData[phase.id].next_steps}
                                      </p>
                                    </div>
                                  </div>
                                </ScrollArea>
                              ) : (
                                <div className="text-sm text-muted-foreground">Click to load phase details...</div>
                              )}
                            </div>
                          </DialogContent>
                        </Dialog>
                      </div>
                      {phase.active_agents > 0 && (
                        <Badge variant="default" className="bg-green-500">
                          Active
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-lg mt-2">{phase.name}</CardTitle>
                    <CardDescription className="text-xs line-clamp-2">
                      {phase.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">
                          <strong>{phase.active_agents}</strong> active agents
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ListTodo className="h-4 w-4 text-muted-foreground" />
                        <div className="text-sm space-y-1">
                          <div>Total: <strong>{phase.total_tasks}</strong></div>
                          <div>Done: <strong>{phase.completed_tasks}</strong></div>
                          <div>Active: <strong>{phase.active_tasks}</strong></div>
                        </div>
                      </div>
                    </div>

                    {/* CLI Configuration Display */}
                    {(phase.cli_config?.cli_tool || phase.cli_config?.cli_model) && (
                      <div className="pt-2 border-t space-y-1">
                        <div className="text-xs font-medium text-muted-foreground">Agent Config:</div>
                        {phase.cli_config.cli_tool && (
                          <div className="text-xs">
                            Tool: <code className="bg-muted px-1 py-0.5 rounded">{phase.cli_config.cli_tool}</code>
                          </div>
                        )}
                        {phase.cli_config.cli_model && (
                          <div className="text-xs">
                            Model: <code className="bg-muted px-1 py-0.5 rounded">{phase.cli_config.cli_model}</code>
                          </div>
                        )}
                      </div>
                    )}

                    <Button
                      onClick={() => navigateToTasks(phase.id)}
                      variant="outline"
                      size="sm"
                      className="w-full"
                    >
                      View Tasks
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Live Activity Feed */}
      <Card>
        <CardHeader>
          <CardTitle>Live Activity Feed</CardTitle>
          <CardDescription>Real-time phase activities from Hephaestus</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[300px] w-full rounded-md border p-4">
            {activities.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                No activities yet. Activities will appear here as agents work.
              </div>
            ) : (
              <div className="space-y-2">
                {activities.map((activity, index) => (
                  <div
                    key={`${activity.timestamp}-${index}`}
                    className={cn(
                      "flex items-start gap-2 text-sm py-2 px-3 rounded-md",
                      "hover:bg-muted/50 transition-colors",
                      activity.type === 'cross_phase_task' && "border-l-2 border-blue-500"
                    )}
                  >
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(activity.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="flex-1">
                      {activity.type === 'cross_phase_task' && (
                        <>
                          Agent {activity.agent_id?.slice(0, 8)} (P{activity.from_phase}) →
                          task in P{activity.to_phase}
                        </>
                      )}
                      {activity.type === 'task_completed' && (
                        <>Task completed in P{activity.to_phase}</>
                      )}
                      {activity.type === 'agent_started' && (
                        <>Agent {activity.agent_id?.slice(0, 8)} started in P{activity.to_phase}</>
                      )}
                      {activity.type === 'agent_stopped' && (
                        <>Agent {activity.agent_id?.slice(0, 8)} stopped in P{activity.from_phase}</>
                      )}
                      {activity.description && (
                        <span className="text-muted-foreground ml-1">• {activity.description}</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}