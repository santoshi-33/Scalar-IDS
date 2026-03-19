import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-login-page',
  imports: [FormsModule, RouterLink],
  templateUrl: './login.page.html',
  styleUrl: './login.page.scss'
})
export class LoginPage {
  readonly email = signal('');
  readonly password = signal('');
  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  constructor(private readonly router: Router) {}

  async signIn() {
    this.error.set(null);
    this.submitting.set(true);
    try {
      await new Promise((r) => setTimeout(r, 350));
      if (!this.email().includes('@') || this.password().length < 4) {
        this.error.set('Enter a valid email and a password (min 4 chars).');
        return;
      }
      await this.router.navigateByUrl('/upload');
    } finally {
      this.submitting.set(false);
    }
  }
}

