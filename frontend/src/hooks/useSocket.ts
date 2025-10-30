import { useEffect, useRef } from 'react';
import { useWebSocket } from '@/context/WebSocketContext';

export function useSocket() {
  const { socket } = useWebSocket();
  return socket;
}