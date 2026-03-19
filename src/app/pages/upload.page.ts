import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ApiService } from '../core/api';
import type { PredictCsvResponse } from '../core/api.client';

@Component({
  selector: 'app-upload-page',
  imports: [CommonModule],
  templateUrl: './upload.page.html',
  styleUrl: './upload.page.scss'
})
export class UploadPage {
  readonly Object = Object;
  readonly file = signal<File | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly result = signal<PredictCsvResponse | null>(null);

  constructor(private readonly api: ApiService) {}

  onPick(ev: Event) {
    const input = ev.target as HTMLInputElement;
    const f = input.files?.[0] ?? null;
    this.file.set(f);
  }

  async run() {
    this.error.set(null);
    this.result.set(null);
    const f = this.file();
    if (!f) {
      this.error.set('Please choose a CSV file first.');
      return;
    }
    this.loading.set(true);
    try {
      const res = await this.api.predictCsv(f);
      this.result.set(res);

      // store a lightweight history entry locally
      const entry = {
        at: new Date().toISOString(),
        filename: f.name,
        summary: res.summary
      };
      const raw = localStorage.getItem('ids_history') ?? '[]';
      const list = JSON.parse(raw) as any[];
      list.unshift(entry);
      localStorage.setItem('ids_history', JSON.stringify(list.slice(0, 25)));
    } catch (e: any) {
      this.error.set(e?.message ?? 'Prediction failed');
    } finally {
      this.loading.set(false);
    }
  }
}

