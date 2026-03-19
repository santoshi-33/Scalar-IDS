import { Injectable } from '@angular/core';
import { ApiClient } from './api.client';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly client = new ApiClient(this.baseUrl());

  private baseUrl(): string {
    return (globalThis as any).__IDS_API__ ?? 'http://localhost:8000';
  }

  health() {
    return this.client.health();
  }

  predictCsv(file: File) {
    return this.client.predictCsv(file);
  }

  detections(limit = 25) {
    return this.client.detections(limit);
  }

  stats(minutes = 30) {
    return this.client.stats(minutes);
  }

  simulate(n = 10) {
    return this.client.simulate(n);
  }
}

