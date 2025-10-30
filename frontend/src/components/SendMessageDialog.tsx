import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { MessageCircle, Loader2, Check, AlertCircle, Bot } from 'lucide-react';
import { apiService } from '@/services/api';
import { Agent } from '@/types';
import StatusBadge from './StatusBadge';

interface SendMessageDialogProps {
  open: boolean;
  onClose: () => void;
  agent: Agent | null;
}

export default function SendMessageDialog({
  open,
  onClose,
  agent,
}: SendMessageDialogProps) {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [statusMessage, setStatusMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim()) {
      setStatus('error');
      setStatusMessage('Message cannot be empty');
      return;
    }

    if (!agent) {
      setStatus('error');
      setStatusMessage('No agent selected');
      return;
    }

    if (agent.status === 'terminated') {
      setStatus('error');
      setStatusMessage('Cannot send message to terminated agent');
      return;
    }

    setIsLoading(true);
    setStatus('idle');

    try {
      const response = await apiService.sendMessage(message, agent.id);

      if (response.success) {
        setStatus('success');
        setStatusMessage(`Message sent to Agent ${agent.id.substring(0, 8)}`);

        // Reset form and close after brief delay
        setTimeout(() => {
          setMessage('');
          setStatus('idle');
          setStatusMessage('');
          onClose();
        }, 1500);
      } else {
        setStatus('error');
        setStatusMessage(response.message || 'Failed to send message');
      }
    } catch (error: any) {
      setStatus('error');
      setStatusMessage(error.response?.data?.detail || 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setMessage('');
      setStatus('idle');
      setStatusMessage('');
      onClose();
    }
  };

  if (!agent) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <MessageCircle className="w-5 h-5 mr-2 text-blue-600" />
            Send Message to Agent
          </DialogTitle>
          <DialogDescription>
            Send a direct message to this specific agent
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            {/* Agent Info */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center">
                  <Bot className="w-5 h-5 text-gray-600 mr-2" />
                  <div>
                    <p className="font-semibold text-gray-800">
                      Agent {agent.id.substring(0, 8)}
                    </p>
                    <p className="text-xs text-gray-500">{agent.cli_type}</p>
                  </div>
                </div>
                <StatusBadge status={agent.status} size="sm" />
              </div>

              {agent.current_task && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Current Task:</p>
                  <p className="text-sm text-gray-700 line-clamp-2">
                    {agent.current_task.description}
                  </p>
                  {agent.current_task.phase_info && (
                    <p className="text-xs text-gray-500 mt-1">
                      Phase {agent.current_task.phase_info.order}:{' '}
                      {agent.current_task.phase_info.name}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Message Input */}
            <div className="space-y-2">
              <label htmlFor="message" className="text-sm font-medium text-gray-700">
                Message
              </label>
              <textarea
                id="message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                  // Allow all keys to work normally in textarea
                  e.stopPropagation();
                }}
                placeholder="Type your message here..."
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                disabled={isLoading}
              />
              <p className="text-xs text-gray-500">
                {message.length} characters
              </p>
            </div>

            {/* Status Message */}
            {status !== 'idle' && (
              <div
                className={`flex items-center p-3 rounded-lg ${
                  status === 'success'
                    ? 'bg-green-50 border border-green-200 text-green-800'
                    : 'bg-red-50 border border-red-200 text-red-800'
                }`}
              >
                {status === 'success' ? (
                  <Check className="w-4 h-4 mr-2 flex-shrink-0" />
                ) : (
                  <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                )}
                <p className="text-sm">{statusMessage}</p>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={
                isLoading ||
                !message.trim() ||
                agent.status === 'terminated'
              }
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Send Message
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}