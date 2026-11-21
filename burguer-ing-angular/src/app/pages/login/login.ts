import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
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
  private readonly route = inject(ActivatedRoute);

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

      next: respuesta => {

        this.cargando = false;

        const rol = (respuesta.usuario.rol || '')
          .toLowerCase()
          .trim();

        // ADMINISTRADOR
        if (
          rol.includes('admin') ||
          rol.includes('administrador')
        ) {
          void this.router.navigateByUrl('/admin/dashboard');
          return;
        }

        // CLIENTE
        if (rol.includes('cliente')) {

          const returnUrl =
            this.route.snapshot.queryParamMap.get('returnUrl');

          // Solo permitir destinos internos válidos
          // y evitar redirigir clientes al panel administrativo.
          if (
            returnUrl &&
            returnUrl.startsWith('/') &&
            !returnUrl.startsWith('/admin')
          ) {
            void this.router.navigateByUrl(returnUrl);
          } else {
            void this.router.navigateByUrl('/inicio');
          }

          return;
        }

        this.error =
          `Inicio de sesión exitoso, pero no se reconoció el rol: ${respuesta.usuario.rol}`;

      },

      error: error => {
        this.cargando = false;
        this.error = mensajeError(error);
      }

    });
  }
}