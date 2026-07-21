import * as React from 'react';
import { webSocketService } from '../services/websocket/connection';

export function useRealtime() {
  const emit = React.useCallback((event: string, data: any) => {
    webSocketService.emit(event, data);
  }, []);

  return {
    emit,
    isMocking: true, // Mock telemetry is active in the background
  };
}
