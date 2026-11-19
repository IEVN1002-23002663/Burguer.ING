import { Injectable, inject, signal } from '@angular/core';
import { tap } from 'rxjs';
import { ApiService } from './api.service';
import { AuthUsuario, LoginResponse } from '../models/models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = inject(ApiService);
  readonly usuario = signal<AuthUsuario | null>(this.recuperarUsuario());

  private recuperarUsuario(): AuthUsuario | null {
    try {
      return JSON.parse(localStorage.getItem('burguer_usuario') || 'null') as AuthUsuario | null;
    } catch { return null; }
  }

  get token(): string | null {
    return localStorage.getItem('burguer_token');
  }

  get autenticado(): boolean {
    return !!this.token && !!this.usuario();
  }

  iniciar(correo: string, password: string) {
    return this.api.post<LoginResponse>('/usuarios/login', { correo, password }).pipe(
      tap(respuesta => {
        localStorage.setItem('burguer_token', respuesta.token);
        localStorage.setItem('burguer_usuario', JSON.stringify(respuesta.usuario));
        this.usuario.set(respuesta.usuario);
      })
    );
  }

  cerrar(): void {
    localStorage.removeItem('burguer_token');
    localStorage.removeItem('burguer_usuario');
    this.usuario.set(null);
  }
}
