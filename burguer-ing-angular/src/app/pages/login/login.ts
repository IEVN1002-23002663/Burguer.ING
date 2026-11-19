import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule, RouterLink, Icon],
  templateUrl: './login.html'
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  correo = '';
  password = '';
  cargando = false;
  error = '';

  entrar(): void {
    this.error = '';
    if (!this.correo.trim() || !this.password) {
      this.error = 'Escribe tu correo y contraseña.';
      return;
    }
    this.cargando = true;
    this.auth.iniciar(this.correo.trim(), this.password).subscribe({
      next: () => { this.cargando = false; void this.router.navigateByUrl('/dashboard'); },
      error: error => { this.cargando = false; this.error = mensajeError(error); }
    });
  }
}
