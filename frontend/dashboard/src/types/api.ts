export interface Mine {
  id: number;
  name: string;
  location: string;
  created_at: string;
}

export interface SensorNode {
  id: number;
  conveyor_id: number;
  node_code: string;
  location: string;
  firmware_version: string;
  status: string;
  last_seen: string | null;
  created_at: string;
}

export interface Conveyor {
  id: number;
  mine_id: number;
  name: string;
  belt_type: string;
  length: number;
  width: number;
  status: string;
  created_at: string;
}

export interface ConveyorDetail extends Conveyor {
  sensor_nodes: SensorNode[];
}

export interface Telemetry {
  id: number;
  sensor_node_id: number;
  node_code?: string;
  sequence?: number | null;
  timestamp: string;
  vibration_rms: number;
  vibration_peak: number;
  vibration_kurtosis: number;
  crest_factor?: number | null;
  dominant_frequency_hz?: number | null;
  spectral_energy?: number | null;
  acoustic_rms: number;
  temperature: number;
  belt_speed: number;
  load: number;
  tracking_position: number;
  model_version?: string | null;
  commissioning_version?: string | null;
  decision_layer_version?: string | null;
  anomaly_score?: number | null;
  composite_z_deviation?: number | null;
  persistence_3of5?: boolean | null;
  persistence_5of9?: boolean | null;
  alert_state?: string | null;
  data_quality?: number | null;
  operating_state?: string | null;
  multimodal_state?: string | null;
  fusion_reasons?: string | null;
  camera_status?: string | null;
  camera_frame_ref?: string | null;
  camera_is_simulated?: boolean | null;
  source?: string | null;
  is_simulated?: boolean | null;
}

export interface SensorEvidence {
  timestamp: string;
  conveyor_id: string;
  sensor_id: string;
  modality: string;
  status: string;
  anomaly: boolean;
  heuristic_severity: number;
  value: Record<string, any>;
  quality: string;
  reason: string;
  method: string;
  confidence: number | null;
  confidence_method: string | null;
  is_simulated: boolean;
  source?: string;
}

export interface HardwareHealthStatus {
  esp32: 'ONLINE' | 'OFFLINE';
  vibration: 'GOOD' | 'DEGRADED' | 'INVALID';
  temperature: 'GOOD' | 'DEGRADED' | 'INVALID';
  rpm: 'GOOD' | 'DEGRADED' | 'INVALID';
  tracking: 'GOOD' | 'DEGRADED' | 'INVALID';
  camera: 'ONLINE' | 'OFFLINE' | 'STALE';
}

export interface UnifiedConveyorEvent {
  timestamp: string;
  conveyor_id: string;
  operating_state: string;
  system_mode?: 'REAL_HARDWARE' | 'DEMO_SIMULATED';
  hardware_health?: HardwareHealthStatus | null;
  vibration?: SensorEvidence | null;
  temperature?: SensorEvidence | null;
  speed?: SensorEvidence | null;
  load?: SensorEvidence | null;
  tracking?: SensorEvidence | null;
  camera?: SensorEvidence | null;
  overall_state: string;
  reasons: string[];
  supporting_evidence: SensorEvidence[];
  confidence: number | null;
  confidence_method: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface GatewayHealth {
  status: string;
  backend_connected: boolean;
  queue_size: number;
  last_forwarded_at: string | null;
  uptime_seconds: number;
}

export interface GatewayMetrics {
  packets_received: number;
  packets_queued: number;
  packets_forwarded: number;
  packets_failed: number;
  duplicate_packets: number;
  current_queue_size: number;
}


