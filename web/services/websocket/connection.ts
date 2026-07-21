import { io, Socket } from 'socket.io-client';
import { useSensorsStore } from '../../store/useSensorsStore';
import { useAlertsStore } from '../../store/useAlertsStore';
import { useWorkersStore } from '../../store/useWorkersStore';
import { useNotificationsStore } from '../../store/useNotificationsStore';

class WebSocketService {
  private socket: Socket | null = null;
  private isMockMode: boolean = true;
  private mockInterval: NodeJS.Timeout | null = null;

  public connect(url: string = 'http://localhost:8000') {
    if (this.isMockMode) {
      this.startMockTelemetry();
      return;
    }

    this.socket = io(url, {
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
    });

    this.socket.on('connect', () => {
      console.log('[WEBSOCKET] Connected to real-time stream:', url);
    });

    this.socket.on('sensor_update', (data: { id: string; value: number }) => {
      useSensorsStore.getState().updateSensorValue(data.id, data.value);
    });

    this.socket.on('alert_new', (alert: any) => {
      useAlertsStore.getState().addAlert(alert);
      useNotificationsStore.getState().addNotification({
        title: 'New Hazard Raised',
        message: alert.message,
        category: 'ALERT',
      });
    });

    this.socket.on('worker_vitals', (data: { id: string; hr: number; o2: number; temp: number }) => {
      useWorkersStore.getState().updateWorkerBiometrics(data.id, data.hr, data.o2, data.temp);
    });
  }

  public disconnect() {
    if (this.isMockMode) {
      this.stopMockTelemetry();
      return;
    }
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // Live simulation for Palantir/Tesla Mission Control feel
  private startMockTelemetry() {
    console.log('[WEBSOCKET] Initializing mock real-time telemetry simulator');
    
    this.mockInterval = setInterval(() => {
      const sensors = useSensorsStore.getState().sensors;
      const workers = useWorkersStore.getState().workers;

      // Jitter one random sensor
      if (sensors.length > 0) {
        const randomSensorIdx = Math.floor(Math.random() * sensors.length);
        const sensor = sensors[randomSensorIdx];
        if (sensor.status !== 'OFFLINE') {
          const delta = (Math.random() - 0.5) * (sensor.type === 'PRESSURE' ? 15 : 1);
          const newValue = parseFloat((sensor.value + delta).toFixed(2));
          useSensorsStore.getState().updateSensorValue(sensor.id, newValue);
        }
      }

      // Jitter one random worker's vitals
      if (workers.length > 0) {
        const randomWorkerIdx = Math.floor(Math.random() * workers.length);
        const worker = workers[randomWorkerIdx];
        if (worker.status !== 'OFF_SHIFT') {
          const hrJitter = Math.floor((Math.random() - 0.5) * 4);
          const o2Jitter = Math.random() > 0.85 ? -1 : 0;
          const tempJitter = parseFloat(((Math.random() - 0.5) * 0.1).toFixed(2));

          const newHr = Math.max(60, Math.min(130, worker.heartRate + hrJitter));
          const newO2 = Math.max(90, Math.min(100, worker.oxygenLevel + o2Jitter));
          const newTemp = parseFloat(Math.max(36.0, Math.min(39.0, worker.bodyTemperature + tempJitter)).toFixed(2));

          useWorkersStore.getState().updateWorkerBiometrics(worker.id, newHr, newO2, newTemp);
        }
      }

      // Periodically trigger a random informational notification (every ~30s)
      if (Math.random() > 0.95) {
        const categories: ('SYSTEM' | 'MAINTENANCE' | 'PERMIT')[] = ['SYSTEM', 'MAINTENANCE', 'PERMIT'];
        const randomCategory = categories[Math.floor(Math.random() * categories.length)];
        
        let title = 'System Update';
        let message = 'Telemetry health check completed successfully.';
        
        if (randomCategory === 'MAINTENANCE') {
          title = 'Work Order Update';
          message = 'Technician assigned to inspect valve actuator FL-4.';
        } else if (randomCategory === 'PERMIT') {
          title = 'Permit Audit Log';
          message = 'Pending hot work authorization reviewed by safety team.';
        }

        useNotificationsStore.getState().addNotification({
          title,
          message,
          category: randomCategory,
        });
      }

    }, 3000); // Trigger jitter ticks every 3 seconds
  }

  private stopMockTelemetry() {
    if (this.mockInterval) {
      clearInterval(this.mockInterval);
      this.mockInterval = null;
    }
  }

  public emit(event: string, data: any) {
    if (this.isMockMode) {
      console.log(`[WEBSOCKET MOCK EMIT] Event: ${event}`, data);
      return;
    }
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }
}

export const webSocketService = new WebSocketService();
export default webSocketService;
