
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  return auth.autenticado || router.createUrlTree(['/login']);
};

export const rolGuard = (rolesPermitidos: string[]): CanActivateFn => {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    if (!auth.autenticado) {
      return router.createUrlTree(['/login']);
    }

    const rolUsuario = auth.usuario()?.rol?.toLowerCase().trim();

    const permitido = rolesPermitidos.some(
      rol => rol.toLowerCase().trim() === rolUsuario
    );

    if (permitido) {
      return true;
    }

    if (rolUsuario === 'administrador') {
      return router.createUrlTree(['/admin/dashboard']);
    }

    if (rolUsuario === 'empleado') {
      return router.createUrlTree(['/empleado/pedidos']);
    }

    return router.createUrlTree(['/inicio']);
  };
};
