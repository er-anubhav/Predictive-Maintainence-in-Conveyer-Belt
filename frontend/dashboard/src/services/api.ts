import {
  Mine,
  Conveyor,
  ConveyorDetail,
  SensorNode,
  Telemetry,
  HealthResponse,
  GatewayHealth,
  GatewayMetrics,
  UnifiedConveyorEvent,
  SensorEvidence,
} from '../types/api';
import {
  mockMines,
  mockConveyors,
  mockConveyorDetail,
  mockSensorNodes,
  generateMockTelemetry,
  mockGatewayHealth,
  mockGatewayMetrics,
  mockMultimodalEvent,
} from './mockData';

export function getApiBase(): string {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('SIH_API_URL');
    if (saved && saved.trim()) return saved.trim().replace(/\/+$/, '');
  }
  return import.meta.env.VITE_API_URL || '';
}

export function setApiBase(url: string): void {
  if (typeof window !== 'undefined') {
    if (!url || !url.trim()) {
      localStorage.removeItem('SIH_API_URL');
    } else {
      localStorage.setItem('SIH_API_URL', url.trim().replace(/\/+$/, ''));
    }
  }
}

let activeDemoMode = false;
export function isFallbackActive(): boolean {
  return activeDemoMode;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`API Error ${res.status} (${res.statusText}): ${errorText}`);
  }
  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const text = await res.text().catch(() => '');
    throw new Error(`Expected JSON response, but received ${contentType || 'non-JSON'}: ${text.slice(0, 100)}`);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const base = getApiBase();
    try {
      const res = await fetch(`${base}/api/v1/health`);
      if (res.ok) {
        const data = await handleResponse<HealthResponse>(res);
        activeDemoMode = false;
        return data;
      }
    } catch {
      // try root
    }

    try {
      const resRoot = await fetch(`${base}/health`);
      if (resRoot.ok) {
        const data = await handleResponse<HealthResponse>(resRoot);
        activeDemoMode = false;
        return data;
      }
    } catch {
      // both failed
    }

    activeDemoMode = true;
    return {
      status: 'demo_mode',
      service: 'conveyor-maintenance-api (Cloud Demo Standalone)',
      version: '1.0.0-demo',
      environment: 'demo_simulation',
      timestamp: new Date().toISOString(),
    };
  },

  async getMines(): Promise<Mine[]> {
    const base = getApiBase();
    try {
      const res = await fetch(`${base}/api/v1/mines`);
      return await handleResponse<Mine[]>(res);
    } catch {
      return mockMines;
    }
  },

  async getConveyors(mineId?: number): Promise<Conveyor[]> {
    const base = getApiBase();
    const url = mineId !== undefined ? `${base}/api/v1/conveyors?mine_id=${mineId}` : `${base}/api/v1/conveyors`;
    try {
      const res = await fetch(url);
      return await handleResponse<Conveyor[]>(res);
    } catch {
      return mockConveyors;
    }
  },

  async getConveyorDetail(conveyorId: number): Promise<ConveyorDetail> {
    const base = getApiBase();
    try {
      const res = await fetch(`${base}/api/v1/conveyors/${conveyorId}`);
      return await handleResponse<ConveyorDetail>(res);
    } catch {
      return mockConveyorDetail;
    }
  },

  async getDevices(conveyorId?: number): Promise<SensorNode[]> {
    const base = getApiBase();
    const url = conveyorId !== undefined ? `${base}/api/v1/devices?conveyor_id=${conveyorId}` : `${base}/api/v1/devices`;
    try {
      const res = await fetch(url);
      return await handleResponse<SensorNode[]>(res);
    } catch {
      return mockSensorNodes;
    }
  },

  async getDevice(deviceId: string | number): Promise<SensorNode> {
    const base = getApiBase();
    try {
      const res = await fetch(`${base}/api/v1/devices/${deviceId}`);
      return await handleResponse<SensorNode>(res);
    } catch {
      return mockSensorNodes[0];
    }
  },

  async getTelemetry(sensorNodeId: string | number, limit: number = 50): Promise<Telemetry[]> {
    const base = getApiBase();
    try {
      const res = await fetch(`${base}/api/v1/telemetry/${sensorNodeId}?limit=${limit}`);
      return await handleResponse<Telemetry[]>(res);
    } catch {
      return generateMockTelemetry(limit);
    }
  },

  async getGatewayHealth(): Promise<GatewayHealth> {
    const gatewayBase = import.meta.env.VITE_GATEWAY_URL || '/api/gateway';
    try {
      const res = await fetch(`${gatewayBase}/health`);
      return await handleResponse<GatewayHealth>(res);
    } catch {
      return mockGatewayHealth;
    }
  },

  async getGatewayMetrics(): Promise<GatewayMetrics> {
    const gatewayBase = import.meta.env.VITE_GATEWAY_URL || '/api/gateway';
    try {
      const res = await fetch(`${gatewayBase}/metrics`);
      return await handleResponse<GatewayMetrics>(res);
    } catch {
      return mockGatewayMetrics;
    }
  },

  async getMultimodalLatest(nodeCode?: string): Promise<UnifiedConveyorEvent> {
    const base = getApiBase();
    const url = nodeCode ? `${base}/api/v1/multimodal/latest?node_code=${nodeCode}` : `${base}/api/v1/multimodal/latest`;
    try {
      const res = await fetch(url);
      return await handleResponse<UnifiedConveyorEvent>(res);
    } catch {
      return mockMultimodalEvent;
    }
  },

  async setCameraFlip(flipHorizontal?: boolean, flipVertical?: boolean): Promise<any> {
    const base = getApiBase();
    try {
      const res = await fetch(`${base}/api/v1/multimodal/camera/flip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flip_horizontal: flipHorizontal, flip_vertical: flipVertical }),
      });
      return await handleResponse<any>(res);
    } catch {
      return { status: 'mock_flipped', flip_horizontal: flipHorizontal, flip_vertical: flipVertical };
    }
  },

  async triggerCameraSnapshot(scenario: string = 'NORMAL'): Promise<SensorEvidence> {
    const base = getApiBase();
    try {
      const res = await fetch(`${base}/api/v1/multimodal/camera/snapshot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario }),
      });
      return await handleResponse<SensorEvidence>(res);
    } catch {
      return {
        timestamp: new Date().toISOString(),
        conveyor_id: 'Conveyor-01',
        sensor_id: 'CAM-01',
        modality: 'camera',
        status: 'OK',
        anomaly: false,
        heuristic_severity: 0.1,
        value: { frame_ref: 'camera/demo_frame.jpg' },
        quality: 'GOOD',
        reason: 'Visual inspection nominal',
        method: 'OPENCV_INSPECTION',
        confidence: 0.95,
        confidence_method: 'EDGE_CONTOUR_ANALYSIS',
        is_simulated: true,
        source: 'DEMO_SIMULATED',
      };
    }
  },

  async simulateScenario(scenario: string, nodeCode: string = 'NODE-001'): Promise<any> {
    const base = getApiBase();
    try {
      const res = await fetch(`${base}/api/v1/multimodal/simulate-scenario`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario, node_code: nodeCode, conveyor_id: 'Conveyor-01' }),
      });
      return await handleResponse<any>(res);
    } catch {
      return { status: 'success', scenario, message: `Scenario ${scenario} simulated in demo preview.` };
    }
  },
};
