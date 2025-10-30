import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Activity, Minus, Bot } from 'lucide-react';
import { cn } from '@/lib/utils';
import AgentDetailModal from '@/components/AgentDetailModal';

interface AgentAlignment {
  agent_id: string;
  alignment_score?: number;
  current_phase?: string;
  needs_steering: boolean;
  last_update: string;
}

interface TrajectoryTimelineProps {
  alignments: AgentAlignment[];
}

export default function TrajectoryTimeline({ alignments }: TrajectoryTimelineProps) {
  const navigate = useNavigate();
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  if (!alignments || alignments.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="w-5 h-5 mr-2 text-blue-600" />
            Trajectory Alignment Timeline
          </CardTitle>
          <CardDescription>
            Agent alignment trends over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-gray-500 text-center py-8">
            No trajectory data available
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate overall system alignment trend
  const avgAlignment = alignments.reduce((sum, a) => sum + (a.alignment_score || 0), 0) / alignments.length;
  const highAligned = alignments.filter(a => (a.alignment_score || 0) > 0.8).length;
  const needSteering = alignments.filter(a => a.needs_steering).length;

  const getTrendIcon = () => {
    if (avgAlignment > 0.8) return { icon: TrendingUp, color: 'text-green-600' };
    if (avgAlignment > 0.5) return { icon: Minus, color: 'text-yellow-600' };
    return { icon: TrendingDown, color: 'text-red-600' };
  };

  const trend = getTrendIcon();
  const TrendIcon = trend.icon;

  // Simple bar chart visualization
  const maxBarHeight = 100;

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center">
              <Activity className="w-5 h-5 mr-2 text-blue-600" />
              Trajectory Alignment Timeline
            </CardTitle>
            <CardDescription>
              System-wide agent alignment visualization
            </CardDescription>
          </div>
          <div className="text-right">
            <div className="flex items-center justify-end">
              <TrendIcon className={cn("w-5 h-5 mr-1", trend.color)} />
              <span className={cn("text-2xl font-bold", trend.color)}>
                {Math.round(avgAlignment * 100)}%
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Average Alignment
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Stats Summary */}
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-green-600">{highAligned}</div>
              <div className="text-xs text-green-700">Well Aligned</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-yellow-600">{needSteering}</div>
              <div className="text-xs text-yellow-700">Need Steering</div>
            </div>
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-2xl font-bold text-blue-600">{alignments.length}</div>
              <div className="text-xs text-blue-700">Total Agents</div>
            </div>
          </div>

          {/* Bar Chart Visualization */}
          <div className="space-y-1">
            <div className="text-xs text-gray-500 mb-2">Individual Agent Alignments</div>
            <div className="flex items-end justify-between space-x-1" style={{ height: `${maxBarHeight}px` }}>
              {alignments.map((agent, idx) => {
                const score = (agent.alignment_score || 0) * 100;
                const height = (score / 100) * maxBarHeight;

                return (
                  <div
                    key={agent.agent_id}
                    className="flex-1 flex flex-col items-center justify-end group relative"
                  >
                    {/* Tooltip */}
                    <div className="absolute bottom-full mb-2 hidden group-hover:block z-10">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedAgentId(agent.agent_id);
                        }}
                        className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-xl border border-gray-700 hover:bg-gray-800 transition-all"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <Bot className="w-3 h-3" />
                          <span className="font-mono">{agent.agent_id.substring(0, 8)}</span>
                        </div>
                        <div className="flex items-center justify-between gap-2">
                          <span>Alignment: {Math.round(score)}%</span>
                          {agent.needs_steering && (
                            <span className="text-yellow-300 text-xs">⚠️ Steering</span>
                          )}
                        </div>
                        <p className="text-xs text-gray-400 mt-1">Click to view</p>
                      </button>
                      <div className="w-2 h-2 bg-gray-900 transform rotate-45 mx-auto -mt-1"></div>
                    </div>

                    {/* Bar */}
                    <div
                      className={cn(
                        "w-full rounded-t transition-all duration-300 hover:opacity-80",
                        score > 80 ? "bg-green-500" :
                        score > 40 ? "bg-yellow-500" :
                        "bg-red-500"
                      )}
                      style={{ height: `${height}px`, minHeight: '4px' }}
                    />
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between text-xs text-gray-400 mt-2">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center justify-center space-x-4 text-xs">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded mr-1"></div>
              <span className="text-gray-600">Aligned (&gt;80%)</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-yellow-500 rounded mr-1"></div>
              <span className="text-gray-600">Partial (40-80%)</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-red-500 rounded mr-1"></div>
              <span className="text-gray-600">Misaligned (&lt;40%)</span>
            </div>
          </div>
        </div>
      </CardContent>
      <AgentDetailModal
        agentId={selectedAgentId}
        onClose={() => setSelectedAgentId(null)}
        onViewOutput={(agentId) => {
          navigate('/observability', { state: { focusAgentId: agentId } });
        }}
      />
    </Card>
  );
}