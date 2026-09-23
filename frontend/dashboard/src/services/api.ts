import { Mine, Conveyor, ConveyorDetail, SensorNode, Telemetry, HealthResponse } from '../types/api';

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
      if (res.ok) return handleResponse<HealthResponse>(res);
    } catch {
      // Fallback
    }
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthResponse>(res);
  },

  async getMines(): Promise<Mine[]> {
    const res = await fetch(`${API_BASE}/api/v1/mines`);
    return handleResponse<Mine[]>(res);
  },

  async getConveyors(mineId?: number): Promise<Conveyor[]> {
    const url = mineId !== undefined 
      ? `${API_BASE}/api/v1/conveyors?mine_id=${mineId}`
      : `${API_BASE}/api/v1/conveyors`;
    const res = await fetch(url);
    return handleResponse<Conveyor[]>(res);
  },

  async getConveyorDetail(conveyorId: number): Promise<ConveyorDetail> {
    const res = await fetch(`${API_BASE}/api/v1/conveyors/${conveyorId}`);
    return handleResponse<ConveyorDetail>(res);
  },

  async getDevices(conveyorId?: number): Promise<SensorNode[]> {
    const url = conveyorId !== undefined
      ? `${API_BASE}/api/v1/devices?conveyor_id=${conveyorId}`
      : `${API_BASE}/api/v1/devices`;
    const res = await fetch(url);
    return handleResponse<SensorNode[]>(res);
  },

  async getDevice(deviceId: string | number): Promise<SensorNode> {
    const res = await fetch(`${API_BASE}/api/v1/devices/${deviceId}`);
    return handleResponse<SensorNode>(res);
  },

  async getTelemetry(sensorNodeId: string | number, limit: number = 50): Promise<Telemetry[]> {
    const res = await fetch(`${API_BASE}/api/v1/telemetry/${sensorNodeId}?limit=${limit}`);
    return handleResponse<Telemetry[]>(res);
  },

  async getGatewayHealth(): Promise<import('../types/api').GatewayHealth> {
    const gatewayBase = import.meta.env.VITE_GATEWAY_URL || '/api/gateway';
    const res = await fetch(`${gatewayBase}/health`);
    return handleResponse<import('../types/api').GatewayHealth>(res);
  },

  async getGatewayMetrics(): Promise<import('../types/api').GatewayMetrics> {
    const gatewayBase = import.meta.env.VITE_GATEWAY_URL || '/api/gateway';
    const res = await fetch(`${gatewayBase}/metrics`);
    return handleResponse<import('../types/api').GatewayMetrics>(res);
  },

  async getMultimodalLatest(nodeCode?: string): Promise<import('../types/api').UnifiedConveyorEvent> {
    const url = nodeCode 
      ? `${API_BASE}/api/v1/multimodal/latest?node_code=${nodeCode}`
      : `${API_BASE}/api/v1/multimodal/latest`;
    const res = await fetch(url);
    return handleResponse<import('../types/api').UnifiedConveyorEvent>(res);
  },

  async setCameraFlip(flipHorizontal?: boolean, flipVertical?: boolean): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/multimodal/camera/flip`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        flip_horizontal: flipHorizontal,
        flip_vertical: flipVertical,
      }),
    });
    return handleResponse<any>(res);
  },

  async triggerCameraSnapshot(scenario: string = 'NORMAL'): Promise<import('../types/api').SensorEvidence> {
    const res = await fetch(`${API_BASE}/api/v1/multimodal/camera/snapshot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario }),
    });
    return handleResponse<import('../types/api').SensorEvidence>(res);
  },

  async simulateScenario(scenario: string, nodeCode: string = 'NODE-001'): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/multimodal/simulate-scenario`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, node_code: nodeCode, conveyor_id: 'Conveyor-01' }),
    });
    return handleResponse<any>(res);
  },
};


