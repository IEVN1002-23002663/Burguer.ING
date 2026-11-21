
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './registro.html'
})
export class Registro {

  private readonly api = inject(ApiService);
  private readonly router = inject(Router);

  nombre = '';
  correo = '';
  password = '';
  confirmarPassword = '';

  cargando = false;
  error = '';
  mensaje = '';

  registrar(): void {
    this.error = '';
    this.mensaje = '';

    if (
      !this.nombre.trim() ||
      !this.correo.trim() ||
      !this.password ||
      !this.confirmarPassword
    ) {
      this.error = 'Completa todos los campos.';
      return;
    }

    if (this.password.length < 8) {
      this.error = 'La contraseña debe tener al menos 8 caracteres.';
      return;
    }

    if (this.password !== this.confirmarPassword) {
      this.error = 'Las contraseñas no coinciden.';
      return;
    }

    this.cargando = true;

    this.api.post<any>('/usuarios/registro-cliente', {
      nombre: this.nombre.trim(),
      correo: this.correo.trim().toLowerCase(),
      password: this.password
    }).subscribe({
      next: respuesta => {
        this.cargando = false;
        this.mensaje = respuesta.mensaje || 'Cuenta creada correctamente.';

        void this.router.navigateByUrl('/login', {
          state: { registroExitoso: true }
        });
      },
      error: err => {
        this.cargando = false;

        this.error =
          err?.error?.mensaje ||
          'No se pudo crear la cuenta. Intenta nuevamente.';
      }
    });
  }
}
