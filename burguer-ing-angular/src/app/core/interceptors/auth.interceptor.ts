import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const router = inject(Router);
  const token = localStorage.getItem('burguer_token');
  const autenticada = token && request.url.includes('/api/');

  const req = autenticada
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;

  return next(req).pipe(
    catchError(error => {
      // Los endpoints actuales de Flask no están todos protegidos;
      // un error de contraseña incorrecta no debe cerrar una sesión previa.
      if (error.status === 401 && !request.url.endsWith('/usuarios/login')) {
        localStorage.removeItem('burguer_token');
        localStorage.removeItem('burguer_usuario');
        void router.navigateByUrl('/login');
      }
      return throwError(() => error);
    })
  );
};
