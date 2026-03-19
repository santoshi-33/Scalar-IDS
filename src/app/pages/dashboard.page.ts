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
  readonly activeClass = signal<string | null>(null);
  readonly search = signal('');
  readonly sortBy = signal<'time' | 'confidence' | 'label'>('time');
  readonly sortDir = signal<'asc' | 'desc'>('desc');

  readonly attackRatePct = computed(() => Math.round(((this.stats()?.attack_rate ?? 0) * 100 + Number.EPSILON) * 10) / 10);
  readonly accuracyPct = computed(() => {
    const v = this.stats()?.detection_accuracy;
    if (v === null || v === undefined) return null;
    return Math.round((v * 100 + Number.EPSILON) * 10) / 10;
  });

  readonly donutStyle = computed(() => {
    const pct = Math.max(0, Math.min(100, this.attackRatePct()));
    return `conic-gradient(var(--brand-2) ${pct}%, rgba(236,255,247,0.12) 0)`;
  });

  readonly legendEntries = computed(() => {
    const dist = this.stats()?.attack_type_distribution ?? {};
    return Object.entries(dist).sort((a, b) => b[1] - a[1]);
  });

  readonly filteredDetections = computed(() => {
    const q = this.search().trim().toLowerCase();
    const cls = this.activeClass();
    const by = this.sortBy();
    const dir = this.sortDir();

    let list = this.detections().filter((d) => !cls || d.predicted_type === cls);
    if (q) {
      list = list.filter((d) => {
        const fields = [
          d.predicted_type,
          d.actual_type ?? '',
          d.protocol ?? '',
          d.status ?? '',
          d.at,
        ];
        return fields.some((f) => f.toLowerCase().includes(q));
      });
    }

    const sorted = [...list].sort((a, b) => {
      if (by === 'time') {
        return new Date(a.at).getTime() - new Date(b.at).getTime();
      }
      if (by === 'confidence') {
        return (a.confidence ?? -1) - (b.confidence ?? -1);
      }
      return a.predicted_type.localeCompare(b.predicted_type);
    });
    return dir === 'asc' ? sorted : sorted.reverse();
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

  setSearch(value: string) {
    this.search.set(value);
  }

  toggleClassFilter(label: string) {
    this.activeClass.set(this.activeClass() === label ? null : label);
  }

  clearFilters() {
    this.activeClass.set(null);
    this.search.set('');
  }

  setSort(by: 'time' | 'confidence' | 'label') {
    if (this.sortBy() === by) {
      this.sortDir.set(this.sortDir() === 'asc' ? 'desc' : 'asc');
      return;
    }
    this.sortBy.set(by);
    this.sortDir.set(by === 'time' ? 'desc' : 'asc');
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

