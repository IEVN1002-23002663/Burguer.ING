import { Component, inject, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { mensajeError } from '../../shared/errors';

@Component({
  selector: 'app-recuperar-password',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './recuperar-password.html'
})
export class RecuperarPassword {
  private readonly api = inject(ApiService);
  private readonly cdr = inject(ChangeDetectorRef);
  paso = 1;
  nombre = '';
  correo = '';
  password = '';
  confirmarPassword = '';
  cargando = false;
  error = '';
  mensaje = '';
  mostrarPassword = false;

  solicitar(): void {
    if (this.cargando) return;
    this.error = ''; this.mensaje = '';
    if (!this.nombre.trim() || !this.correo.trim()) {
      this.error = 'Completa tu nombre y correo.'; return;
    }
    this.correo = this.correo.trim().toLowerCase();
    this.cargando = true;
    this.api.post<{mensaje: string}>('/usuarios/solicitar-recuperacion', {
      nombre: this.nombre.trim(), correo: this.correo
    }).subscribe({
      next: r => { this.paso = 2; this.mensaje = r.mensaje; this.cargando = false; this.cdr.markForCheck(); },
      error: e => { this.error = mensajeError(e); this.cargando = false; this.cdr.markForCheck(); }
    });
  }

  restablecer(): void {
    if (this.cargando) return;
    this.error = ''; this.mensaje = '';
    if (this.password.length < 8 || this.password.length > 128) {
      this.error = 'Ingresa una contraseña de 8 a 128 caracteres.'; return;
    }
    if (this.password !== this.confirmarPassword) {
      this.error = 'Las contraseñas no coinciden.'; return;
    }
    this.cargando = true;
    this.api.post<{mensaje: string}>('/usuarios/restablecer-password', {
      nombre: this.nombre.trim(), correo: this.correo, password: this.password,
      confirmarPassword: this.confirmarPassword
    }).subscribe({
      next: r => {
        this.paso = 3; this.mensaje = r.mensaje; this.cargando = false;
        this.password = ''; this.confirmarPassword = ''; this.cdr.markForCheck();
      },
      error: e => { this.error = mensajeError(e); this.cargando = false; this.cdr.markForCheck(); }
    });
  }

  volver(): void {
    if (this.cargando) return;
    this.paso = 1; this.password = ''; this.confirmarPassword = '';
    this.error = ''; this.mensaje = '';
  }
}
