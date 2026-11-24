
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

        // ======================================
        // ADMINISTRADOR
        // ======================================

        if (
          rol === 'administrador' ||
          rol === 'admin'
        ) {
          void this.router.navigateByUrl('/admin/dashboard');
          return;
        }

        // ======================================
        // EMPLEADO
        // ======================================

        if (rol === 'empleado') {
          void this.router.navigateByUrl('/empleado/pedidos');
          return;
        }

        // ======================================
        // CLIENTE
        // ======================================

        if (rol === 'cliente') {

          const returnUrl =
            this.route.snapshot.queryParamMap.get('returnUrl');

          if (
            returnUrl &&
            returnUrl.startsWith('/') &&
            !returnUrl.startsWith('/admin') &&
            !returnUrl.startsWith('/empleado')
          ) {
            void this.router.navigateByUrl(returnUrl);
          } else {
            void this.router.navigateByUrl('/inicio');
          }

          return;
        }

        // ======================================
        // ROL NO RECONOCIDO
        // ======================================

        this.auth.cerrar();

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
