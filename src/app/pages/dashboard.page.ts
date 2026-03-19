import { CommonModule } from '@angular/common';
import { Component, DestroyRef, computed, inject, signal } from '@angular/core';

import { ApiService } from '../core/api';
import type { DetectionEntry, TrafficStats } from '../core/api.client';

type LoadState = 'idle' | 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-dashboard-page',
  imports: [CommonModule],
  templateUrl: './dashboard.page.html',
  styleUrl: './dashboard.page.scss'
})
export class DashboardPage {
  private readonly api = inject(ApiService);
  private readonly destroyRef = inject(DestroyRef);

  readonly Math = Math;

  readonly state = signal<LoadState>('idle');
  readonly refreshing = signal(false);
  readonly error = signal<string | null>(null);

  readonly stats = signal<TrafficStats | null>(null);
  readonly detections = signal<DetectionEntry[]>([]);
  readonly minutes = signal(30);
  readonly polling = signal(true);

  readonly attackRatePct = computed(() => Math.round(((this.stats()?.attack_rate ?? 0) * 100 + Number.EPSILON) * 10) / 10);
  readonly accuracyPct = computed(() => {
    const v = this.stats()?.detection_accuracy;
    if (v === null || v === undefined) return null;
    return Math.round((v * 100 + Number.EPSILON) * 10) / 10;
  });

  readonly donutStyle = computed(() => {
    const pct = Math.max(0, Math.min(100, this.attackRatePct()));
    return `conic-gradient(#ef4444 ${pct}%, rgba(234,240,255,0.10) 0)`;
  });

  constructor() {
    this.refresh();

    const id = setInterval(() => {
      if (!this.polling()) return;
      void this.refresh();
    }, 3000);
    this.destroyRef.onDestroy(() => clearInterval(id));
  }

  async refresh() {
    this.error.set(null);
    this.refreshing.set(true);
    this.state.set('loading');
    try {
      const [s, d] = await Promise.all([this.api.stats(this.minutes()), this.api.detections(25)]);
      this.stats.set(s);
      this.detections.set(d);
      this.state.set('ready');
    } catch (e: any) {
      this.state.set('error');
      this.error.set(e?.message ?? 'Failed to load dashboard');
    }
    finally {
      this.refreshing.set(false);
    }
  }

  async simulate() {
    this.error.set(null);
    try {
      await this.api.simulate(12);
      await this.refresh();
    } catch (e: any) {
      this.error.set(e?.message ?? 'Simulation failed');
    }
  }

  togglePolling() {
    this.polling.set(!this.polling());
  }

  setWindow(min: number) {
    this.minutes.set(min);
    void this.refresh();
  }

  fmtPct(v: number | null | undefined) {
    if (v === null || v === undefined) return '—';
    return `${Math.round((v * 100 + Number.EPSILON) * 10) / 10}%`;
  }

  shortTime(iso: string) {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}

