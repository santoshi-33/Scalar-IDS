import { Component } from '@angular/core';
import { AppShell } from './shell/shell';

@Component({
  selector: 'app-root',
  imports: [AppShell],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {}
