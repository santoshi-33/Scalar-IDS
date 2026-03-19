import { Component, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

type HistoryEntry = {
  at: string;
  filename: string;
  summary: Record<string, number>;
};

@Component({
  selector: 'app-history-page',
  imports: [CommonModule, RouterLink],
  templateUrl: './history.page.html',
  styleUrl: './history.page.scss'
})
export class HistoryPage {
  readonly Object = Object;
  readonly entries = signal<HistoryEntry[]>(this.load());
  readonly empty = computed(() => this.entries().length === 0);

  clear() {
    localStorage.removeItem('ids_history');
    this.entries.set([]);
  }

  private load(): HistoryEntry[] {
    try {
      const raw = localStorage.getItem('ids_history') ?? '[]';
      const list = JSON.parse(raw) as HistoryEntry[];
      return Array.isArray(list) ? list : [];
    } catch {
      return [];
    }
  }
}

