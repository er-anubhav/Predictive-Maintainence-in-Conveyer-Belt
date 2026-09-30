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

const API_BASE = import.meta.env.VITE_API_URL || '';

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
    try {
      const res = await fetch(`${API_BASE}/api/v1/health`);
      if (res.ok) return await handleResponse<HealthResponse>(res);
    } catch {
      // try root fallback
    }
    const resRoot = await fetch(`${API_BASE}/health`);
    return await handleResponse<HealthResponse>(resRoot);
  },

  async getMines(): Promise<Mine[]> {
    const res = await fetch(`${API_BASE}/api/v1/mines`);
    return await handleResponse<Mine[]>(res);
  },

  async getConveyors(mineId?: number): Promise<Conveyor[]> {
    const url = mineId !== undefined ? `${API_BASE}/api/v1/conveyors?mine_id=${mineId}` : `${API_BASE}/api/v1/conveyors`;
    const res = await fetch(url);
    return await handleResponse<Conveyor[]>(res);
  },

  async getConveyorDetail(conveyorId: number): Promise<ConveyorDetail> {
    const res = await fetch(`${API_BASE}/api/v1/conveyors/${conveyorId}`);
    return await handleResponse<ConveyorDetail>(res);
  },

  async getDevices(conveyorId?: number): Promise<SensorNode[]> {
    const url = conveyorId !== undefined ? `${API_BASE}/api/v1/devices?conveyor_id=${conveyorId}` : `${API_BASE}/api/v1/devices`;
    const res = await fetch(url);
    return await handleResponse<SensorNode[]>(res);
  },

  async getDevice(deviceId: string | number): Promise<SensorNode> {
    const res = await fetch(`${API_BASE}/api/v1/devices/${deviceId}`);
    return await handleResponse<SensorNode>(res);
  },

  async getTelemetry(sensorNodeId: string | number, limit: number = 50): Promise<Telemetry[]> {
    const res = await fetch(`${API_BASE}/api/v1/telemetry/${sensorNodeId}?limit=${limit}`);
    return await handleResponse<Telemetry[]>(res);
  },

  async getGatewayHealth(): Promise<GatewayHealth> {
    const gatewayBase = import.meta.env.VITE_GATEWAY_URL || '/api/gateway';
    const res = await fetch(`${gatewayBase}/health`);
    return await handleResponse<GatewayHealth>(res);
  },

  async getGatewayMetrics(): Promise<GatewayMetrics> {
    const gatewayBase = import.meta.env.VITE_GATEWAY_URL || '/api/gateway';
    const res = await fetch(`${gatewayBase}/metrics`);
    return await handleResponse<GatewayMetrics>(res);
  },

  async getMultimodalLatest(nodeCode?: string): Promise<UnifiedConveyorEvent> {
    const url = nodeCode ? `${API_BASE}/api/v1/multimodal/latest?node_code=${nodeCode}` : `${API_BASE}/api/v1/multimodal/latest`;
    const res = await fetch(url);
    return await handleResponse<UnifiedConveyorEvent>(res);
  },

  async setCameraFlip(flipHorizontal?: boolean, flipVertical?: boolean): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/multimodal/camera/flip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ flip_horizontal: flipHorizontal, flip_vertical: flipVertical }),
    });
    return await handleResponse<any>(res);
  },

  async triggerCameraSnapshot(scenario: string = 'NORMAL'): Promise<SensorEvidence> {
    const res = await fetch(`${API_BASE}/api/v1/multimodal/camera/snapshot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario }),
    });
    return await handleResponse<SensorEvidence>(res);
  },

  async simulateScenario(scenario: string, nodeCode: string = 'NODE-001'): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/multimodal/simulate-scenario`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, node_code: nodeCode, conveyor_id: 'Conveyor-01' }),
    });
    return await handleResponse<any>(res);
  },
};
