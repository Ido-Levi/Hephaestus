import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Target, CheckCircle, XCircle, RefreshCw, Navigation } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';
import ClickableAgentCard from '@/components/ClickableAgentCard';
import AgentDetailModal from '@/components/AgentDetailModal';

interface SteeringEvent {
  id: string;
  agent_id: string;
  guardian_analysis_id?: string;
  timestamp: string;
  steering_type: string;
  message: string;
  was_successful?: boolean;
}

interface SteeringEventsCardProps {
  events: SteeringEvent[];
}

const getSteeringTypeIcon = (type: string) => {
  switch (type?.toLowerCase()) {
    case 'focus_redirect':
    case 'redirect':
      return RefreshCw;
    case 'correction':
    case 'course_correction':
      return Navigation;
    default:
      return Target;
  }
};

const getSteeringTypeBadge = (type: string) => {
  const baseType = type?.toLowerCase() || 'unknown';

  switch (baseType) {
    case 'focus_redirect':
    case 'redirect':
      return { label: 'Focus Redirect', className: 'bg-blue-100 text-blue-700' };
    case 'correction':
    case 'course_correction':
      return { label: 'Course Correction', className: 'bg-yellow-100 text-yellow-700' };
    case 'stuck':
      return { label: 'Unstuck', className: 'bg-orange-100 text-orange-700' };
    case 'constraint_violation':
      return { label: 'Constraint Fix', className: 'bg-red-100 text-red-700' };
    default:
      return { label: type || 'Steering', className: 'bg-gray-100 text-gray-700' };
  }
};

export default function SteeringEventsCard({ events }: SteeringEventsCardProps) {
  const navigate = useNavigate();
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  if (!events || events.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="w-5 h-5 mr-2 text-blue-600" />
            Recent Steering Events
          </CardTitle>
          <CardDescription>
            Agent trajectory interventions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-gray-500 text-center py-8">
            <Navigation className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm">No steering events recently</p>
            <p className="text-xs text-gray-400 mt-1">Agents are on track</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Target className="w-5 h-5 mr-2 text-blue-600" />
          Recent Steering Events
        </CardTitle>
        <CardDescription>
          Agent trajectory interventions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-3">
            {events.map((event) => {
              const TypeIcon = getSteeringTypeIcon(event.steering_type);
              const typeBadge = getSteeringTypeBadge(event.steering_type);

              return (
                <div
                  key={event.id}
                  className={cn(
                    "border rounded-lg p-3 transition-colors",
                    event.was_successful === false ? "border-red-200 bg-red-50" : "border-gray-200"
                  )}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center">
                      <TypeIcon className="w-4 h-4 mr-2 text-blue-600" />
                      <span className="text-xs text-gray-500">
                        {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                      </span>
                    </div>
                    {event.was_successful !== undefined && (
                      event.was_successful ? (
                        <CheckCircle className="w-4 h-4 text-green-600" title="Successful" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-600" title="Failed" />
                      )
                    )}
                  </div>

                  <div className="mb-2">
                    <ClickableAgentCard
                      agentId={event.agent_id}
                      onClick={() => setSelectedAgentId(event.agent_id)}
                      compact
                      showTaskInfo={false}
                    />
                  </div>

                  <div className="flex items-end justify-end mb-2">
                    <Badge variant="outline" className={cn("text-xs", typeBadge.className)}>
                      {typeBadge.label}
                    </Badge>
                  </div>

                  <div className="text-xs text-gray-600 leading-relaxed line-clamp-2">
                    {event.message}
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
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