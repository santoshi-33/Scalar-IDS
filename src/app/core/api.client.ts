export type PredictionRow = {
  label: string;
  probability?: number | null;
};

export type PredictCsvResponse = {
  rows: PredictionRow[];
  summary: Record<string, number>;
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
}

