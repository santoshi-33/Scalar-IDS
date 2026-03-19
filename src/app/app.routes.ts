import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    title: 'Scalora IDS',
    loadComponent: () => import('./pages/landing.page').then((m) => m.LandingPage)
  },
  {
    path: 'login',
    title: 'Sign in · Scalora IDS',
    loadComponent: () => import('./pages/login.page').then((m) => m.LoginPage)
  },
  {
    path: 'upload',
    title: 'Upload · Scalora IDS',
    loadComponent: () => import('./pages/upload.page').then((m) => m.UploadPage)
  },
  {
    path: 'history',
    title: 'History · Scalora IDS',
    loadComponent: () => import('./pages/history.page').then((m) => m.HistoryPage)
  },
  {
    path: '**',
    title: 'Not found · Scalora IDS',
    loadComponent: () => import('./pages/not-found.page').then((m) => m.NotFoundPage)
  }
];
