import React, { useEffect } from 'react';
import { Clock, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useWebSocket } from '@/context/WebSocketContext';
import { apiService } from '@/services/api';
import { cn } from '@/lib/utils';

interface PendingReviewIndicatorProps {
  onClick?: () => void;
}

const PendingReviewIndicator: React.FC<PendingReviewIndicatorProps> = ({ onClick }) => {
  const { subscribe } = useWebSocket();

  const { data, refetch } = useQuery({
    queryKey: ['pending-review-count'],
    queryFn: () => apiService.getPendingReviewCount(),
    refetchInterval: 5000, // Poll every 5 seconds as backup
  });

  // Subscribe to real-time updates
  useEffect(() => {
    const unsubscribe1 = subscribe('ticket_pending_review', () => {
      refetch();
    });
    const unsubscribe2 = subscribe('ticket_approved', () => {
      refetch();
    });
    const unsubscribe3 = subscribe('ticket_rejected', () => {
      refetch();
    });

    return () => {
      unsubscribe1();
      unsubscribe2();
      unsubscribe3();
    };
  }, [subscribe, refetch]);

  const count = data?.count || 0;

  if (count === 0) {
    return null;
  }

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center space-x-2 px-3 py-2 rounded-lg transition-all",
        "bg-orange-100 border border-orange-300 text-orange-800",
        "hover:bg-orange-200 hover:shadow-md",
        "animate-pulse"
      )}
      title="Click to view tickets pending review"
    >
      <Clock className="w-5 h-5" />
      <span className="font-medium">{count} ticket{count !== 1 ? 's' : ''} pending review</span>
      <AlertCircle className="w-4 h-4" />
    </button>
  );
};

export default PendingReviewIndicator;
