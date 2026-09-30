import {
  Mine,
  Conveyor,
  ConveyorDetail,
  SensorNode,
  Telemetry,
  GatewayHealth,
  GatewayMetrics,
  UnifiedConveyorEvent,
} from '../types/api';

export const mockMines: Mine[] = [
  {
    id: 1,
    name: 'Demo Iron Ore Mine',
    location: 'Odisha Sector 4, Mining Block B',
    created_at: '2026-09-21T08:08:42.695534Z',
  },
  {
    id: 2,
    name: 'POC Integration Mine',
    location: 'Sector POC',
    created_at: '2026-09-30T14:39:01.507508Z',
  },
];

export const mockSensorNodes: SensorNode[] = [
  {
    id: 1,
    conveyor_id: 1,
    node_code: 'NODE-001',
    location: 'Drive Pulley Head (Splice Zone A)',
    firmware_version: 'v0.6.1-esp32',
    status: 'ONLINE',
    last_seen: new Date().toISOString(),
    created_at: '2026-09-21T08:08:42.705000Z',
  },
  {
    id: 2,
    conveyor_id: 1,
    node_code: 'NODE-002',
    location: 'Take-up Carriage Zone',
    firmware_version: 'v0.6.1-esp32',
    status: 'ONLINE',
    last_seen: new Date().toISOString(),
    created_at: '2026-09-21T08:08:42.705000Z',
  },
];

export const mockConveyors: Conveyor[] = [
  {
    id: 1,
    mine_id: 1,
    name: 'Conveyor-01 (Primary Overland)',
    belt_type: 'Steel Cord ST-2500',
    length: 120.0,
    width: 1.4,
    status: 'OPERATIONAL',
    created_at: '2026-09-21T08:08:42.701288Z',
  },
];

export const mockConveyorDetail: ConveyorDetail = {
  ...mockConveyors[0],
  sensor_nodes: mockSensorNodes,
};

export function generateMockTelemetry(count: number = 30): Telemetry[] {
  const points: Telemetry[] = [];
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const time = new Date(now - i * 2000).toISOString();
    const noise = Math.sin(i * 0.4) * 0.08;
    points.push({
      id: 1000 - i,
      sensor_node_id: 1,
      node_code: 'NODE-001',
      sequence: 999990 - i,
      timestamp: time,
      vibration_rms: Number((0.42 + noise).toFixed(3)),
      vibration_peak: Number((1.25 + noise * 1.5).toFixed(3)),
      vibration_kurtosis: Number((3.1 + noise * 0.5).toFixed(2)),
      crest_factor: 2.95,
      dominant_frequency_hz: 48.5,
      spectral_energy: 1.42,
      acoustic_rms: 0.12,
      temperature: Number((36.5 + Math.cos(i * 0.2) * 1.2).toFixed(1)),
      belt_speed: 2.45,
      load: Number((42.0 + Math.sin(i * 0.3) * 3.5).toFixed(1)),
      tracking_position: Number((1.8 + Math.cos(i * 0.5) * 0.8).toFixed(1)),
      anomaly_score: Number((0.18 + Math.abs(noise)).toFixed(4)),
      operating_state: 'HEALTHY',
      multimodal_state: 'HEALTHY',
      fusion_reasons: 'All modalities within baseline bounds',
      camera_status: 'ONLINE',
      camera_is_simulated: false,
      source: 'DEMO_SIMULATED',
      is_simulated: true,
      decision_layer_version: 'v0.6.1-heuristic',
    });
  }
  return points;
}

export const mockGatewayHealth: GatewayHealth = {
  status: 'ok',
  backend_connected: true,
  queue_size: 0,
  last_forwarded_at: new Date().toISOString(),
  uptime_seconds: 1420.5,
};

export const mockGatewayMetrics: GatewayMetrics = {
  packets_received: 248,
  packets_queued: 248,
  packets_forwarded: 248,
  packets_failed: 0,
  duplicate_packets: 3,
  current_queue_size: 0,
};

export const mockMultimodalEvent: UnifiedConveyorEvent = {
  timestamp: new Date().toISOString(),
  conveyor_id: 'Conveyor-01',
  operating_state: 'HEALTHY',
  system_mode: 'DEMO_SIMULATED',
  overall_state: 'HEALTHY',
  reasons: [
    'Vibration Isolation Forest score 0.18 within nominal threshold (< 0.65)',
    'Splice acoustic reflection stable',
    'Belt lateral tracking deviation 1.8mm within +/-15mm clearance',
  ],
  supporting_evidence: [],
  confidence: 0.94,
  confidence_method: 'HEURISTIC_FUSION_WEIGHTED',
};
