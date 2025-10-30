import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Activity, Bot, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SystemHealthProps {
  systemHealth?: {
    coherence_score: number;
    average_alignment: number;
    active_agents: number;
    running_tasks: number;
    status: string;
  };
}

export default function SystemHealthCard({ systemHealth }: SystemHealthProps) {
  if (!systemHealth) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="w-5 h-5 mr-2 text-blue-600" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-gray-500 text-center py-8">
            No data available
          </div>
        </CardContent>
      </Card>
    );
  }

  const coherencePercent = Math.round((systemHealth.coherence_score || 0) * 100);
  const alignmentPercent = Math.round((systemHealth.average_alignment || 0) * 100);

  const getHealthStatus = () => {
    if (coherencePercent >= 80 && alignmentPercent >= 80) {
      return { icon: CheckCircle, text: "All systems nominal", color: "text-green-600" };
    } else if (coherencePercent >= 50 && alignmentPercent >= 50) {
      return { icon: AlertCircle, text: "Minor issues detected", color: "text-yellow-600" };
    }
    return { icon: AlertCircle, text: "Attention required", color: "text-red-600" };
  };

  const healthStatus = getHealthStatus();
  const StatusIcon = healthStatus.icon;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Activity className="w-5 h-5 mr-2 text-blue-600" />
          System Health
        </CardTitle>
        <CardDescription>
          Real-time system performance metrics
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Coherence Score */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Coherence Score</span>
            <span className={cn(
              "text-lg font-bold",
              coherencePercent >= 80 ? "text-green-600" :
              coherencePercent >= 50 ? "text-yellow-600" :
              "text-red-600"
            )}>
              {coherencePercent}%
            </span>
          </div>
          <Progress
            value={coherencePercent}
            className={cn(
              "h-3",
              coherencePercent >= 80 ? "[&>div]:bg-green-500" :
              coherencePercent >= 50 ? "[&>div]:bg-yellow-500" :
              "[&>div]:bg-red-500"
            )}
          />
        </div>

        {/* Average Alignment */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Average Alignment</span>
            <span className={cn(
              "text-lg font-bold",
              alignmentPercent >= 80 ? "text-green-600" :
              alignmentPercent >= 50 ? "text-yellow-600" :
              "text-red-600"
            )}>
              {alignmentPercent}%
            </span>
          </div>
          <Progress
            value={alignmentPercent}
            className={cn(
              "h-3",
              alignmentPercent >= 80 ? "[&>div]:bg-green-500" :
              alignmentPercent >= 50 ? "[&>div]:bg-yellow-500" :
              "[&>div]:bg-red-500"
            )}
          />
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <Bot className="w-4 h-4 text-blue-600 mr-1" />
              <span className="text-2xl font-bold">{systemHealth.active_agents}</span>
            </div>
            <div className="text-xs text-gray-600">Active Agents</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center mb-1">
              <TrendingUp className="w-4 h-4 text-blue-600 mr-1" />
              <span className="text-2xl font-bold">{systemHealth.running_tasks}</span>
            </div>
            <div className="text-xs text-gray-600">Running Tasks</div>
          </div>
        </div>

        {/* Status */}
        <div className={cn("flex items-center p-3 rounded-lg bg-gray-50", healthStatus.color)}>
          <StatusIcon className="w-5 h-5 mr-2" />
          <span className="font-medium">{healthStatus.text}</span>
        </div>
      </CardContent>
    </Card>
  );
}