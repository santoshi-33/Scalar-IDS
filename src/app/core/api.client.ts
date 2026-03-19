export type PredictionRow = {
  label: string;
  probability?: number | null;
};

export type PredictCsvResponse = {
  rows: PredictionRow[];
  summary: Record<string, number>;
};

export type DetectionEntry = {
  at: string;
  predicted_type: string;
  confidence?: number | null;
  actual_type?: string | null;
  status?: string | null;
  protocol?: string | null;
  duration?: number | null;
};

export type TrafficStats = {
  total_traffic: number;
  attacks_detected: number;
  attack_rate: number;
  detection_accuracy?: number | null;
  attack_type_distribution: Record<string, number>;
  timeline: Array<{ t: string; benign: number; attack: number }>;
};

export class ApiClient {
  constructor(private readonly baseUrl: string) {}

  async health(): Promise<{ ok: boolean; model_loaded: boolean; detail?: string | null }> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) throw new Error(`Health failed: ${res.status}`);
    return await res.json();
  }

  async predictCsv(file: File): Promise<PredictCsvResponse> {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${this.baseUrl}/predict-csv`, { method: 'POST', body: form });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Predict failed: ${res.status}`);
    }
    return await res.json();
  }

  async detections(limit = 25): Promise<DetectionEntry[]> {
    const res = await fetch(`${this.baseUrl}/detections?limit=${encodeURIComponent(limit)}`);
    if (!res.ok) throw new Error(`Detections failed: ${res.status}`);
    return await res.json();
  }

  async stats(minutes = 30): Promise<TrafficStats> {
    const res = await fetch(`${this.baseUrl}/stats?minutes=${encodeURIComponent(minutes)}`);
    if (!res.ok) throw new Error(`Stats failed: ${res.status}`);
    return await res.json();
  }

  async simulate(n = 10): Promise<DetectionEntry[]> {
    const res = await fetch(`${this.baseUrl}/simulate?n=${encodeURIComponent(n)}`, { method: 'POST' });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Simulate failed: ${res.status}`);
    }
    return await res.json();
  }
}

