import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Target, AlertCircle, Users, GitMerge, Info, CheckCircle, History, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { apiService } from '@/services/api';
import { cn } from '@/lib/utils';

interface ConductorAnalysis {
  id: string;
  timestamp: string;
  coherence_score: number;
  num_agents: number;
  system_status: string;
  detected_duplicates: Array<{
    agent1_id: string;
    agent2_id: string;
    similarity_score: number;
    work_description: string;
  }>;
  recommendations?: string;
}

interface ConductorSummaryCardProps {
  analysis?: ConductorAnalysis | null;
}

export default function ConductorSummaryCard({ analysis }: ConductorSummaryCardProps) {
  const [showHistory, setShowHistory] = useState(false);
  const [historyData, setHistoryData] = useState<ConductorAnalysis[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    if (showHistory && historyData.length === 0) {
      loadHistory();
    }
  }, [showHistory]);

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await apiService.getConductorAnalyses(20);
      // Filter out the current analysis if it's in the history
      const filtered = analysis
        ? data.filter((item: ConductorAnalysis) => item.id !== analysis.id)
        : data;
      setHistoryData(filtered);
    } catch (error) {
      console.error('Failed to load conductor analyses history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };
  if (!analysis) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Target className="w-5 h-5 mr-2 text-blue-600" />
            Current System Focus
          </CardTitle>
          <CardDescription>
            Latest conductor analysis and system coordination
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-gray-500 text-center py-8">
            No conductor analysis available yet
          </div>
        </CardContent>
      </Card>
    );
  }

  const coherencePercent = Math.round((analysis.coherence_score || 0) * 100);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center">
              <Target className="w-5 h-5 mr-2 text-blue-600" />
              Current System Focus
            </CardTitle>
            <CardDescription>
              Latest conductor analysis from {formatDistanceToNow(new Date(analysis.timestamp), { addSuffix: true })}
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="bg-blue-50">
              <Users className="w-3 h-3 mr-1" />
              {analysis.num_agents} agents
            </Badge>
            <Badge
              variant="outline"
              className={
                coherencePercent >= 80 ? "bg-green-50 text-green-700" :
                coherencePercent >= 50 ? "bg-yellow-50 text-yellow-700" :
                "bg-red-50 text-red-700"
              }
            >
              {coherencePercent}% coherent
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* System Status */}
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-sm mb-1">System Status</h4>
              <p className="text-sm text-gray-700 leading-relaxed">
                {analysis.system_status || "No status message available"}
              </p>
            </div>
          </div>
        </div>

        {/* Duplicate Work Detection */}
        {analysis.detected_duplicates && analysis.detected_duplicates.length > 0 && (
          <Alert className="border-yellow-200 bg-yellow-50">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <AlertDescription>
              <div className="font-medium text-yellow-800 mb-2">
                Detected Duplicate Work ({analysis.detected_duplicates.length})
              </div>
              <ScrollArea className="h-24">
                <div className="space-y-2">
                  {analysis.detected_duplicates.map((dup, idx) => (
                    <div key={idx} className="text-sm text-yellow-700 flex items-start">
                      <GitMerge className="w-3 h-3 mr-2 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="font-medium">{dup.agent1_id}</span> and{' '}
                        <span className="font-medium">{dup.agent2_id}</span>
                        {dup.work_description && (
                          <div className="text-xs text-yellow-600 mt-0.5">
                            {dup.work_description} ({Math.round(dup.similarity_score * 100)}% similar)
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </AlertDescription>
          </Alert>
        )}

        {/* Recommendations */}
        {analysis.recommendations && (
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-medium text-sm mb-2 text-blue-900">
              System Recommendations
            </h4>
            <p className="text-sm text-blue-800 leading-relaxed">
              {analysis.recommendations}
            </p>
          </div>
        )}

        {/* No Issues */}
        {(!analysis.detected_duplicates || analysis.detected_duplicates.length === 0) &&
         !analysis.recommendations && (
          <div className="text-center py-4 text-green-600">
            <CheckCircle className="w-8 h-8 mx-auto mb-2" />
            <p className="text-sm font-medium">All agents working efficiently</p>
            <p className="text-xs text-gray-500 mt-1">No duplicate work or issues detected</p>
          </div>
        )}

        {/* History Toggle Button */}
        <div className="border-t pt-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowHistory(!showHistory)}
            className="w-full justify-between text-gray-600 hover:text-gray-900"
          >
            <div className="flex items-center">
              <History className="w-4 h-4 mr-2" />
              <span>System Focus History</span>
            </div>
            {showHistory ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* History Content */}
        {showHistory && (
          <div className="mt-4 space-y-2">
            {loadingHistory ? (
              <div className="text-center py-4 text-gray-500">
                Loading history...
              </div>
            ) : historyData.length > 0 ? (
              <ScrollArea className="h-64">
                <div className="space-y-3">
                  {historyData.map((item) => {
                    const coherence = Math.round((item.coherence_score || 0) * 100);
                    return (
                      <div
                        key={item.id}
                        className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Clock className="w-3 h-3 text-gray-400" />
                              <span className="text-xs text-gray-500">
                                {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
                              </span>
                              <span className="text-xs text-gray-400">
                                ({format(new Date(item.timestamp), 'PPpp')})
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 leading-relaxed">
                              {item.system_status || 'No status message'}
                            </p>
                          </div>
                          <div className="flex flex-col gap-1 ml-2">
                            <Badge variant="outline" className="text-xs">
                              {item.num_agents} agents
                            </Badge>
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-xs",
                                coherence >= 80 ? "text-green-600" :
                                coherence >= 50 ? "text-yellow-600" :
                                "text-red-600"
                              )}
                            >
                              {coherence}%
                            </Badge>
                          </div>
                        </div>
                        {item.detected_duplicates && item.detected_duplicates.length > 0 && (
                          <div className="mt-2 text-xs text-yellow-600">
                            ⚠️ {item.detected_duplicates.length} duplicate work detected
                          </div>
                        )}
                        {item.recommendations && (
                          <div className="mt-2 text-xs text-blue-600">
                            💡 Recommendations available
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            ) : (
              <div className="text-center py-4 text-gray-500">
                No history available
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}