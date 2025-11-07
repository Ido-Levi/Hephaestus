import React, { useState } from 'react';
import { CheckCircle, XCircle, Clock } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { apiService } from '@/services/api';
import { cn } from '@/lib/utils';

interface TicketApprovalUIProps {
  ticketId: string;
  onApproved?: () => void;
  onRejected?: () => void;
}

const TicketApprovalUI: React.FC<TicketApprovalUIProps> = ({
  ticketId,
  onApproved,
  onRejected,
}) => {
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const queryClient = useQueryClient();

  const approveMutation = useMutation({
    mutationFn: () => apiService.approveTicket(ticketId),
    onSuccess: () => {
      toast.success('Ticket approved!');
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] });
      queryClient.invalidateQueries({ queryKey: ['pending-review-count'] });
      onApproved?.();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to approve ticket');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (reason: string) => apiService.rejectTicket(ticketId, reason),
    onSuccess: () => {
      toast.success('Ticket rejected');
      queryClient.invalidateQueries({ queryKey: ['ticket', ticketId] });
      queryClient.invalidateQueries({ queryKey: ['pending-review-count'] });
      onRejected?.();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to reject ticket');
    },
  });

  const handleApprove = () => {
    if (confirm('Approve this ticket? The agent will continue with ticket creation.')) {
      approveMutation.mutate();
    }
  };

  const handleReject = () => {
    if (!rejectionReason.trim()) {
      toast.error('Please provide a rejection reason');
      return;
    }

    if (confirm('Reject this ticket? It will be deleted and the agent will receive an error.')) {
      rejectMutation.mutate(rejectionReason);
    }
  };

  const isLoading = approveMutation.isPending || rejectMutation.isPending;

  return (
    <div className="bg-orange-50 border-2 border-orange-300 rounded-lg p-6 mb-6">
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
            <Clock className="w-6 h-6 text-orange-600 animate-pulse" />
          </div>
        </div>

        <div className="flex-1">
          <h3 className="text-lg font-bold text-orange-900 mb-2">
            Ticket Pending Human Review
          </h3>
          <p className="text-sm text-orange-800 mb-4">
            An agent has requested to create this ticket. Please review the details below and
            decide whether to approve or reject it. The agent is waiting for your decision.
          </p>

          <div className="flex items-center space-x-3">
            {!showRejectForm ? (
              <>
                <button
                  onClick={handleApprove}
                  disabled={isLoading}
                  className={cn(
                    "flex items-center px-6 py-3 rounded-lg font-medium transition-all",
                    "bg-green-600 text-white hover:bg-green-700",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  <CheckCircle className="w-5 h-5 mr-2" />
                  Approve Ticket
                </button>

                <button
                  onClick={() => setShowRejectForm(true)}
                  disabled={isLoading}
                  className={cn(
                    "flex items-center px-6 py-3 rounded-lg font-medium transition-all",
                    "bg-red-600 text-white hover:bg-red-700",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  <XCircle className="w-5 h-5 mr-2" />
                  Reject Ticket
                </button>
              </>
            ) : (
              <div className="w-full space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rejection Reason (required)
                  </label>
                  <textarea
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder="Explain why this ticket should be rejected..."
                    className="w-full px-3 py-2 border rounded-lg resize-none focus:ring-2 focus:ring-orange-500"
                    rows={3}
                    disabled={isLoading}
                  />
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={handleReject}
                    disabled={isLoading || !rejectionReason.trim()}
                    className={cn(
                      "flex items-center px-4 py-2 rounded-lg font-medium transition-all",
                      "bg-red-600 text-white hover:bg-red-700",
                      "disabled:opacity-50 disabled:cursor-not-allowed"
                    )}
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Confirm Rejection
                  </button>

                  <button
                    onClick={() => {
                      setShowRejectForm(false);
                      setRejectionReason('');
                    }}
                    disabled={isLoading}
                    className={cn(
                      "px-4 py-2 rounded-lg font-medium transition-all",
                      "bg-gray-200 text-gray-700 hover:bg-gray-300",
                      "disabled:opacity-50 disabled:cursor-not-allowed"
                    )}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TicketApprovalUI;
