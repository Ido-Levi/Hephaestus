import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Layers, Users, CheckCircle, Clock, ListTodo } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Phase {
  id: string;
  order: number;
  name: string;
  description?: string;
  active_agents: number;
  total_tasks: number;
  completed_tasks: number;
  active_tasks: number;
  pending_tasks: number;
}

interface PhaseDistributionCardProps {
  phases: Phase[];
}

const getPhaseColor = (order: number, totalPhases: number): string => {
  const hue = (order - 1) * (360 / totalPhases);
  return `hsl(${hue}, 70%, 50%)`;
};

export default function PhaseDistributionCard({ phases }: PhaseDistributionCardProps) {
  if (!phases || phases.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Layers className="w-5 h-5 mr-2 text-blue-600" />
            Active Phase Distribution
          </CardTitle>
          <CardDescription>
            Task and agent distribution across workflow phases
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-gray-500 text-center py-8">
            No active phases
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalTasks = phases.reduce((sum, p) => sum + p.total_tasks, 0);
  const completedTasks = phases.reduce((sum, p) => sum + p.completed_tasks, 0);
  const totalAgents = phases.reduce((sum, p) => sum + p.active_agents, 0);

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center">
              <Layers className="w-5 h-5 mr-2 text-blue-600" />
              Active Phase Distribution
            </CardTitle>
            <CardDescription>
              Task and agent distribution across workflow phases
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="bg-blue-50">
              <ListTodo className="w-3 h-3 mr-1" />
              {totalTasks} tasks
            </Badge>
            <Badge variant="outline" className="bg-green-50">
              <Users className="w-3 h-3 mr-1" />
              {totalAgents} agents
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Overall Progress */}
          {totalTasks > 0 && (
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Overall Progress</span>
                <span className="text-sm text-gray-600">
                  {completedTasks} / {totalTasks} tasks
                </span>
              </div>
              <Progress
                value={(completedTasks / totalTasks) * 100}
                className="h-2"
              />
            </div>
          )}

          {/* Phase Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {phases.map((phase) => {
              const phaseProgress = phase.total_tasks > 0
                ? (phase.completed_tasks / phase.total_tasks) * 100
                : 0;
              const phaseColor = getPhaseColor(phase.order, phases.length);

              return (
                <div
                  key={phase.id}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                  style={{
                    borderColor: phase.active_agents > 0 ? phaseColor : '#e5e7eb',
                    backgroundColor: phase.active_agents > 0 ? `${phaseColor}10` : 'white'
                  }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <Badge
                      variant="outline"
                      style={{
                        backgroundColor: phaseColor,
                        color: 'white',
                        borderColor: phaseColor
                      }}
                    >
                      Phase {phase.order}
                    </Badge>
                    {phase.active_agents > 0 && (
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                        Active
                      </Badge>
                    )}
                  </div>

                  <h4 className="font-medium text-sm mb-2 line-clamp-1">{phase.name}</h4>

                  {/* Stats */}
                  <div className="space-y-2">
                    {/* Progress Bar */}
                    {phase.total_tasks > 0 && (
                      <div>
                        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                          <span>Progress</span>
                          <span>{Math.round(phaseProgress)}%</span>
                        </div>
                        <Progress value={phaseProgress} className="h-1.5" />
                      </div>
                    )}

                    {/* Task & Agent Counts */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="flex items-center">
                        <ListTodo className="w-3 h-3 mr-1 text-gray-500" />
                        <span className="text-gray-600">
                          {phase.active_tasks > 0 && (
                            <span className="font-medium text-blue-600">{phase.active_tasks} active</span>
                          )}
                          {phase.active_tasks > 0 && phase.pending_tasks > 0 && ', '}
                          {phase.pending_tasks > 0 && (
                            <span>{phase.pending_tasks} pending</span>
                          )}
                          {phase.active_tasks === 0 && phase.pending_tasks === 0 && (
                            <span className="text-gray-400">No tasks</span>
                          )}
                        </span>
                      </div>
                      <div className="flex items-center">
                        <Users className="w-3 h-3 mr-1 text-gray-500" />
                        <span className={cn(
                          "text-gray-600",
                          phase.active_agents > 0 && "font-medium text-green-600"
                        )}>
                          {phase.active_agents} agents
                        </span>
                      </div>
                    </div>

                    {/* Completion Status */}
                    {phase.completed_tasks > 0 && (
                      <div className="flex items-center text-xs text-green-600">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        {phase.completed_tasks} completed
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}