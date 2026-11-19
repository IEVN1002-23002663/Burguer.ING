# Burguer.ING — Código completo de archivos Angular
Este documento contiene el contenido completo de los archivos del proyecto revisado, para copiar o comparar con tu VS Code.
**Recomendación:** para instalar usa el ZIP; para revisar código por archivo usa este documento.

## `angular.json`

```json
{
  "$schema": "./node_modules/@angular/cli/lib/config/schema.json",
  "version": 1,
  "newProjectRoot": "projects",
  "projects": {
    "burguer-ing-angular": {
      "projectType": "application",
      "root": "",
      "sourceRoot": "src",
      "prefix": "app",
      "architect": {
        "build": {
          "builder": "@angular/build:application",
          "options": {
            "browser": "src/main.ts",
            "polyfills": ["zone.js"],
            "tsConfig": "tsconfig.app.json",
            "index": "src/index.html",
            "assets": [
              { "glob": "**/*", "input": "public" }
            ],
            "styles": ["src/styles.css"]
          },
          "configurations": {
            "production": {
              "budgets": [
                { "type": "initial", "maximumWarning": "1.5mb", "maximumError": "3mb" },
                { "type": "anyComponentStyle", "maximumWarning": "12kb", "maximumError": "20kb" }
              ],
              "outputHashing": "all"
            },
            "development": {
              "optimization": false,
              "extractLicenses": false,
              "sourceMap": true
            }
          },
          "defaultConfiguration": "development"
        },
        "serve": {
          "builder": "@angular/build:dev-server",
          "configurations": {
            "production": { "buildTarget": "burguer-ing-angular:build:production" },
            "development": { "buildTarget": "burguer-ing-angular:build:development" }
          },
          "defaultConfiguration": "development"
        }
      }
    }
  },
  "cli": { "analytics": false }
}

```

## `package.json`

```json
{
  "name": "burguer-ing-angular",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "start": "ng serve --host 127.0.0.1 --port 4200",
    "build": "ng build",
    "watch": "ng build --watch --configuration development"
  },
  "dependencies": {
    "@angular/common": "^20.3.0",
    "@angular/compiler": "^20.3.0",
    "@angular/core": "^20.3.0",
    "@angular/forms": "^20.3.0",
    "@angular/platform-browser": "^20.3.0",
    "@angular/router": "^20.3.0",
    "flowbite": "^3.1.2",
    "rxjs": "~7.8.2",
    "tslib": "^2.8.1",
    "zone.js": "~0.15.1"
  },
  "devDependencies": {
    "@angular/build": "^20.3.0",
    "@angular/cli": "^20.3.0",
    "@angular/compiler-cli": "^20.3.0",
    "@tailwindcss/postcss": "^4.1.0",
    "postcss": "^8.5.0",
    "tailwindcss": "^4.1.0",
    "typescript": "~5.9.2"
  }
}

```

## `src/app/app.config.ts`

```typescript
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor]))
  ]
};

```

## `src/app/app.html`

```html
<router-outlet />

```

## `src/app/app.routes.ts`

```typescript
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { Shell } from './layout/shell';
import { Login } from './pages/login/login';
import { Dashboard } from './pages/dashboard/dashboard';
import { Usuarios } from './pages/usuarios/usuarios';
import { Proveedores } from './pages/proveedores/proveedores';
import { Compras } from './pages/compras/compras';
import { MateriasPrimas } from './pages/materias-primas/materias-primas';
import { Inventario } from './pages/inventario/inventario';

import { ProductosPendiente } from './pages/productos/productos';

import { RecetasProduccionPendiente } from './pages/recetas-produccion/recetas-produccion';

import { PedidosPendiente } from './pages/pedidos/pedidos';

import { VentasPendiente } from './pages/ventas/ventas';

import { GastosFinanzasPendiente } from './pages/gastos-finanzas/gastos-finanzas';

export const routes: Routes = [
  { path: 'login', component: Login },
  {
    path: '',
    component: Shell,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      { path: 'dashboard', component: Dashboard },
      { path: 'usuarios', component: Usuarios },
      { path: 'proveedores', component: Proveedores },
      { path: 'compras', component: Compras },
      { path: 'materias-primas', component: MateriasPrimas },
      { path: 'inventario', component: Inventario },
      { path: 'productos', component: ProductosPendiente },
      { path: 'recetas-produccion', component: RecetasProduccionPendiente },
      { path: 'pedidos', component: PedidosPendiente },
      { path: 'ventas', component: VentasPendiente },
      { path: 'gastos-finanzas', component: GastosFinanzasPendiente }
    ]
  },
  { path: '**', redirectTo: '' }
];

```

## `src/app/app.ts`

```typescript
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.html'
})
export class App {}

```

## `src/app/core/guards/auth.guard.ts`

```typescript
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  return auth.autenticado || router.createUrlTree(['/login']);
};

```

## `src/app/core/interceptors/auth.interceptor.ts`

```typescript
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

```

## `src/app/core/models/models.ts`

```typescript
export interface Usuario {
  id_usuario: number;
  id_rol: number;
  rol: string;
  nombre: string;
  correo: string;
  estado: number;
  fecha_registro: string;
}

export interface AuthUsuario {
  id_usuario: number;
  id_rol: number;
  rol: string;
  nombre: string;
  correo: string;
}

export interface LoginResponse {
  mensaje: string;
  token: string;
  usuario: AuthUsuario;
}

export interface Proveedor {
  id_proveedor: number;
  nombre: string;
  contacto: string | null;
  telefono: string | null;
  correo: string | null;
  direccion: string | null;
  estado: number;
}

export interface CategoriaInsumo {
  id_categoria_insumo: number;
  nombre: string;
  descripcion: string | null;
}

export interface MateriaPrima {
  id_materia_prima: number;
  id_categoria_insumo: number;
  categoria: string;
  nombre: string;
  unidad_medida: string;
  stock_actual: number;
  stock_minimo: number;
  costo_unitario: number;
  estado: number;
}

export interface CompraDetalle {
  id_detalle_compra?: number;
  id_materia_prima: number;
  materia_prima?: string;
  cantidad: number;
  unidad_medida?: string;
  costo_unitario: number;
  subtotal?: number;
}

export interface Compra {
  id_compra: number;
  id_proveedor: number;
  proveedor: string;
  id_usuario: number;
  usuario: string;
  fecha_compra: string;
  fecha_recepcion: string | null;
  total: number;
  estado: 'Pendiente' | 'Recibida' | 'Cancelada';
  observaciones: string | null;
  detalles?: CompraDetalle[];
}

export interface Movimiento {
  id_movimiento: number;
  id_usuario: number | null;
  usuario: string | null;
  tipo_movimiento: string;
  cantidad: number;
  motivo: string | null;
  fecha_movimiento: string;
  materia_prima?: string;
  unidad_medida?: string;
  id_materia_prima?: number;
}

export interface Alerta {
  id_materia_prima: number;
  nombre: string;
  unidad_medida: string;
  stock_actual: number;
  stock_minimo: number;
  categoria: string;
}

export interface AlertasResponse {
  total_alertas: number;
  alertas: Alerta[];
}

export interface MovimientosResponse {
  materia_prima: { id_materia_prima: number; nombre: string; unidad_medida: string };
  movimientos: Movimiento[];
}

export interface ReporteResumen {
  ventas: { cantidad: number; monto: number };
  compras_recibidas: { cantidad: number; monto: number };
  gastos: { cantidad: number; monto: number };
  inventario: { materias_primas_stock_bajo: number; valor_estimado: number };
  diferencia_referencial: number;
  nota: string;
}

export interface VentaDia {
  fecha: string;
  cantidad_ventas: number;
  subtotal: number;
  descuentos: number;
  total: number;
}

export interface ApiMensaje { mensaje: string; [key: string]: unknown; }

```

## `src/app/core/services/api.service.ts`

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  readonly baseUrl = 'http://127.0.0.1:5000/api';

  get<T>(path: string): Observable<T> {
    return this.http.get<T>(`${this.baseUrl}${path}`);
  }
  post<T>(path: string, body: unknown): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${path}`, body);
  }
  put<T>(path: string, body: unknown): Observable<T> {
    return this.http.put<T>(`${this.baseUrl}${path}`, body);
  }
  patch<T>(path: string, body: unknown = {}): Observable<T> {
    return this.http.patch<T>(`${this.baseUrl}${path}`, body);
  }
  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}${path}`);
  }
}

```

## `src/app/core/services/auth.service.ts`

```typescript
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

```

## `src/app/layout/shell.html`

```html
  <div class="layout-shell">
    @if (menuAbierto) {
      <div class="fixed inset-0 bg-black/50 z-20 lg:hidden" (click)="menuAbierto=false"></div>
    }
    <aside class="sidebar" [class.is-open]="menuAbierto">
      <a routerLink="/dashboard" class="logo-band" (click)="menuAbierto=false">
        <span class="logo-square">◎</span>
        <span class="logo-name">Burguer<span class="logo-ing">.ING</span></span>
      </a>
      <div class="branch-box">
        <small>SUCURSAL MATRIZ</small>
        <strong class="flex justify-between items-center">León, Guanajuato <span class="bg-emerald-400 w-2 h-2 rounded-full"></span></strong>
      </div>
      <nav class="nav-list" aria-label="Módulos administrativos">
        @for (link of links; track link.ruta) {
          <a class="nav-link" [routerLink]="link.ruta" routerLinkActive="active" (click)="menuAbierto=false">
            <app-icon [name]="link.icono" [size]="17" class="ico" />
            <span>{{link.titulo}}</span>
          </a>
        }
      </nav>
      <div class="sidebar-footer">
        <div class="text-[11px] text-zinc-400 mb-3 px-2">Panel escolar · Angular + Flask</div>
        <button (click)="cerrarSesion()" class="nav-link w-full text-left">
          <app-icon name="logout" [size]="17" /> Cerrar sesión
        </button>
      </div>
    </aside>
    <div class="main-content">
      <header class="topbar">
        <div class="flex items-center gap-3 flex-1 min-w-0">
          <button type="button" aria-label="Abrir menú" class="lg:hidden p-2" (click)="menuAbierto=!menuAbierto">
            <app-icon name="menu" [size]="22" />
          </button>
          <div class="relative w-full max-w-[485px] hidden sm:block">
            <app-icon name="search" [size]="17" class="absolute left-4 top-[13px] text-zinc-400" />
            <input class="bg-zinc-100 border-none rounded-xl px-11 py-3 w-full text-xs outline-none" placeholder="Buscar en Burguer.ING..." [(ngModel)]="busqueda" (keyup.enter)="buscar()" />
          </div>
        </div>
        <div class="flex items-center gap-3 sm:gap-5">
          <span class="hidden md:flex text-xs font-bold bg-zinc-100 rounded-xl px-4 py-2 items-center gap-2">
            <app-icon name="shop" [size]="16" /> Panel administrativo
          </span>
          <span class="hidden sm:inline-block text-zinc-400"><app-icon name="bell" [size]="19" /></span>
          <div class="flex items-center gap-3 border-l pl-3 sm:pl-5 border-zinc-200">
            <span class="h-9 w-9 bg-[#e5232a] rounded-full text-white grid place-items-center font-extrabold text-xs">{{ iniciales }}</span>
            <div class="hidden sm:block leading-tight">
              <div class="text-xs font-bold text-neutral-950">{{ auth.usuario()?.nombre || 'Usuario' }}</div>
              <div class="text-[11px] text-red-600 font-semibold">{{ auth.usuario()?.rol }}</div>
            </div>
          </div>
          <button aria-label="Cerrar sesión" class="text-zinc-400" (click)="cerrarSesion()"><app-icon name="logout" [size]="18" /></button>
        </div>
      </header>
      <main class="page-space"><router-outlet /></main>
    </div>
  </div>

```

## `src/app/layout/shell.ts`

```typescript
import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../core/services/auth.service';
import { Icon } from '../shared/icon';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, FormsModule, Icon],
  templateUrl: './shell.html'
})
export class Shell {
  readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  menuAbierto = false;
  busqueda = '';
  readonly links = [
    { ruta: '/dashboard', titulo: 'Dashboard', icono: 'dashboard' },
    { ruta: '/usuarios', titulo: 'Usuarios', icono: 'users' },
    { ruta: '/proveedores', titulo: 'Proveedores', icono: 'truck' },
    { ruta: '/compras', titulo: 'Compras', icono: 'cart' },
    { ruta: '/materias-primas', titulo: 'Materias primas', icono: 'box' },
    { ruta: '/inventario', titulo: 'Inventario', icono: 'warehouse' },
    // Rutas de tus compañeros: habilitadas, pero con páginas vacías.
    { ruta: '/productos', titulo: 'Productos', icono: 'shop' },
    { ruta: '/recetas-produccion', titulo: 'Recetas y producción', icono: 'clipboard' },
    { ruta: '/pedidos', titulo: 'Pedidos', icono: 'cart' },
    { ruta: '/ventas', titulo: 'Ventas', icono: 'chart' },
    { ruta: '/gastos-finanzas', titulo: 'Gastos y finanzas', icono: 'money' }
  ];

  get iniciales(): string {
    const nombre = this.auth.usuario()?.nombre || 'IN';
    return nombre.split(' ').slice(0, 2).map(x => x.charAt(0)).join('').toUpperCase();
  }

  buscar(): void {
    const valor = this.busqueda.toLowerCase();
    const link = this.links.find(x => x.titulo.toLowerCase().includes(valor));
    if (link && valor.trim()) void this.router.navigateByUrl(link.ruta);
  }

  cerrarSesion(): void {
    this.auth.cerrar();
    void this.router.navigateByUrl('/login');
  }
}

```

## `src/app/pages/compras/compras.html`

```html
  <div class="page-header">
    <div><h1 class="page-title">Compras de Materias Primas</h1><p class="page-subtitle">Al marcar una compra como <strong>Recibida</strong>, se actualiza el inventario automáticamente.</p></div>
    <button class="btn btn-red" (click)="abrirNueva()"><app-icon name="plus" [size]="17" /> Nueva Compra</button>
  </div>
  @if (mensaje) { <div class="notice notice-ok mb-4">{{mensaje}}</div> }
  @if (error) { <div class="notice notice-error mb-4">{{error}}</div> }
  <div class="panel data-table-wrap">
    <table class="data-table">
      <thead><tr><th>Folio</th><th>Fecha</th><th>Proveedor</th><th>Importe total</th><th>Recepción</th><th class="text-right">Acciones</th></tr></thead>
      <tbody>
        @for (c of compras; track c.id_compra) {
          <tr>
            <td class="font-mono font-bold">CMP-{{c.id_compra.toString().padStart(4,'0')}}</td>
            <td>{{c.fecha_compra.slice(0,10)}}</td><td class="font-semibold">{{c.proveedor}}</td>
            <td class="font-extrabold">{{moneda(c.total)}}</td>
            <td><span class="chip" [class.chip-yellow]="c.estado==='Pendiente'" [class.chip-green]="c.estado==='Recibida'" [class.chip-gray]="c.estado==='Cancelada'">{{c.estado}}</span></td>
            <td><div class="actions-inline flex-wrap">
              <button class="table-action" (click)="verDetalle(c)">Detalles</button>
              @if (c.estado==='Pendiente') {
                <button class="btn btn-green btn-small" (click)="recibir(c)"><app-icon name="check" [size]="14" /> Recibir en almacén</button>
                <button class="table-action text-red-600" (click)="cancelar(c)">Cancelar</button>
              } @else { <span class="text-xs text-zinc-400">{{c.estado==='Recibida'?'Stock ingresado':'Sin recepción'}}</span> }
            </div></td>
          </tr>
        } @empty { <tr><td colspan="6" class="text-center p-10 text-zinc-400">{{cargando?'Cargando compras...':'No hay compras registradas.'}}</td></tr> }
      </tbody>
    </table>
  </div>
  <p class="text-xs text-zinc-500 mt-3">Las compras pendientes no incrementan las existencias. Solo la opción «Recibir en almacén» genera movimientos.</p>
  @if (detalleActual) {
    <div class="modal-backdrop" (click)="detalleActual=null"><div class="modal-panel" role="dialog" aria-modal="true" (click)="$event.stopPropagation()">
      <div class="modal-header"><div><h2 class="panel-title">Compra CMP-{{detalleActual.id_compra}}</h2><div class="text-xs text-zinc-500">{{detalleActual.proveedor}} · {{detalleActual.estado}}</div></div><button (click)="detalleActual=null" aria-label="Cerrar"><app-icon name="close" [size]="19" /></button></div>
      <div class="modal-body"><div class="data-table-wrap"><table class="data-table"><thead><tr><th>Materia prima</th><th>Cantidad</th><th>Costo</th><th>Subtotal</th></tr></thead><tbody>
        @for (d of detalleActual.detalles || []; track d.id_detalle_compra) {
          <tr><td>{{d.materia_prima}}</td><td>{{d.cantidad}} {{d.unidad_medida}}</td><td>{{moneda(d.costo_unitario)}}</td><td>{{moneda(d.subtotal||0)}}</td></tr>
        }
      </tbody></table></div><div class="text-right font-extrabold mt-5">Total: {{moneda(detalleActual.total)}}</div></div>
      <div class="modal-footer"><button class="btn btn-outline" (click)="detalleActual=null">Cerrar</button></div>
    </div></div>
  }
  @if (modalNueva) {
    <div class="modal-backdrop" (click)="modalNueva=false"><div class="modal-panel" role="dialog" aria-modal="true" (click)="$event.stopPropagation()">
      <div class="modal-header"><h2 class="panel-title">Nueva compra de insumos</h2><button (click)="modalNueva=false" aria-label="Cerrar"><app-icon name="close" [size]="19" /></button></div>
      <form (ngSubmit)="guardar()"><div class="modal-body space-y-4">
        @if (errorModal) { <div class="notice notice-error">{{errorModal}}</div> }
        <div class="form-field"><label>Proveedor *</label><select class="form-control" name="proveedor" [(ngModel)]="idProveedor" required><option [ngValue]="0">Selecciona un proveedor</option>
          @for (p of proveedoresActivos; track p.id_proveedor){<option [ngValue]="p.id_proveedor">{{p.nombre}}</option>}
        </select></div>
        <div class="form-field"><label>Observaciones</label><textarea class="form-control" name="observaciones" [(ngModel)]="observaciones" rows="2"></textarea></div>
        <div class="flex items-center justify-between border-t border-zinc-100 pt-4"><h3 class="font-bold">Materias primas a comprar</h3><button class="btn btn-outline btn-small" type="button" (click)="agregarLinea()"><app-icon name="plus" [size]="14" /> Agregar</button></div>
        @for (d of lineas; track $index; let i=$index) {
          <div class="border border-zinc-200 rounded-xl p-3 bg-zinc-50 space-y-3">
            <div class="flex justify-between"><strong class="text-xs">Insumo {{i+1}}</strong><button class="table-action text-red-600" type="button" (click)="quitarLinea(i)" [disabled]="lineas.length===1">Quitar</button></div>
            <div class="form-field"><label>Materia prima *</label><select class="form-control" [name]="'materia'+i" [(ngModel)]="d.id_materia_prima" (ngModelChange)="materiaSeleccionada(d)" required>
              <option [ngValue]="0">Selecciona ingrediente</option>
              @for (m of materiasActivas; track m.id_materia_prima) {<option [ngValue]="m.id_materia_prima">{{m.nombre}} ({{m.unidad_medida}})</option>}
            </select></div>
            <div class="form-grid">
              <div class="form-field"><label>Cantidad ({{unidad(d.id_materia_prima)}}) *</label><input class="form-control" type="number" min="0.001" step="0.001" [name]="'cantidad'+i" [(ngModel)]="d.cantidad" required /></div>
              <div class="form-field"><label>Costo unitario *</label><input class="form-control" type="number" min="0" step="0.0001" [name]="'costo'+i" [(ngModel)]="d.costo_unitario" required /></div>
            </div><div class="text-right text-xs font-bold">Subtotal: {{moneda(d.cantidad*d.costo_unitario)}}</div>
          </div>
        }
        <div class="text-right text-lg font-extrabold">Total: {{moneda(totalFormulario)}}</div>
        <div class="alert-banner">La compra se guardará en estado Pendiente. Para ingresar el stock, después deberás pulsar «Recibir en almacén».</div>
      </div>
      <div class="modal-footer"><button class="btn btn-outline" type="button" (click)="modalNueva=false">Cancelar</button><button class="btn btn-red" type="submit" [disabled]="guardando">{{guardando?'Guardando...':'Registrar compra'}}</button></div></form>
    </div></div>
  }

```

## `src/app/pages/compras/compras.ts`

```typescript
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { ApiMensaje, Compra, CompraDetalle, MateriaPrima, Proveedor } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

@Component({
  selector: 'app-compras', standalone: true, imports:[FormsModule,Icon],
  templateUrl: './compras.html'
})
export class Compras implements OnInit {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  compras: Compra[]=[];
  proveedores:Proveedor[]=[];
  materias:MateriaPrima[]=[];
  detalleActual:Compra|null=null;
  modalNueva=false;
  idProveedor=0;
  observaciones='';
  lineas:CompraDetalle[]=[];
  cargando=false;
  guardando=false;
  mensaje='';
  error='';
  errorModal='';
  ngOnInit():void{this.cargar();}
  get proveedoresActivos():Proveedor[]{return this.proveedores.filter(p=>p.estado===1);}
  get materiasActivas():MateriaPrima[]{return this.materias.filter(m=>m.estado===1);}
  get totalFormulario():number{return this.lineas.reduce((a,d)=>a+(Number(d.cantidad)||0)*(Number(d.costo_unitario)||0),0);}
  moneda(v:number):string{return new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN'}).format(v);}
  unidad(id:number):string{return this.materias.find(m=>m.id_materia_prima===id)?.unidad_medida||'unidad';}
  cargar():void{
    this.cargando=true;this.error='';
    forkJoin({compras:this.api.get<Compra[]>('/compras/'),proveedores:this.api.get<Proveedor[]>('/proveedores/'),materias:this.api.get<MateriaPrima[]>('/materias-primas/')}).subscribe({
      next:r=>{this.compras=r.compras;this.proveedores=r.proveedores;this.materias=r.materias;this.cargando=false;},
      error:e=>{this.error=mensajeError(e);this.cargando=false;}
    });
  }
  abrirNueva():void{this.idProveedor=0;this.observaciones='';this.lineas=[this.nuevaLinea()];this.errorModal='';this.modalNueva=true;}
  private nuevaLinea():CompraDetalle{return{id_materia_prima:0,cantidad:1,costo_unitario:0};}
  agregarLinea():void{this.lineas.push(this.nuevaLinea());}
  quitarLinea(i:number):void{if(this.lineas.length>1)this.lineas.splice(i,1);}
  materiaSeleccionada(d:CompraDetalle):void{d.costo_unitario=this.materias.find(m=>m.id_materia_prima===d.id_materia_prima)?.costo_unitario||0;}
  guardar():void{
    this.errorModal='';
    if(!this.idProveedor){this.errorModal='Selecciona un proveedor.';return;}
    if(this.lineas.some(l=>!l.id_materia_prima||!(l.cantidad>0)||l.costo_unitario<0)){
      this.errorModal='Revisa materia prima, cantidad y costo de cada línea.';return;
    }
    if(new Set(this.lineas.map(l=>l.id_materia_prima)).size!==this.lineas.length){this.errorModal='No repitas el mismo insumo; suma las cantidades en una sola línea.';return;}
    const usuario=this.auth.usuario();
    if(!usuario){this.errorModal='La sesión no tiene usuario. Vuelve a iniciar sesión.';return;}
    this.guardando=true;
    this.api.post<ApiMensaje>('/compras/',{
      id_proveedor:this.idProveedor,id_usuario:usuario.id_usuario,observaciones:this.observaciones,
      detalles:this.lineas.map(({id_materia_prima,cantidad,costo_unitario})=>({id_materia_prima,cantidad,costo_unitario}))
    }).subscribe({
      next:r=>{this.guardando=false;this.modalNueva=false;this.mensaje=r.mensaje;this.cargar();},
      error:e=>{this.guardando=false;this.errorModal=mensajeError(e);}
    });
  }
  verDetalle(c:Compra):void{
    this.api.get<Compra>(`/compras/${c.id_compra}`).subscribe({next:r=>this.detalleActual=r,error:e=>this.error=mensajeError(e)});
  }
  recibir(c:Compra):void{
    if(!confirm(`¿Recibir la compra CMP-${c.id_compra}? Esto sumará los insumos al inventario.`))return;
    this.api.patch<ApiMensaje>(`/compras/${c.id_compra}/recibir`).subscribe({next:r=>{this.mensaje=r.mensaje;this.cargar();},error:e=>this.error=mensajeError(e)});
  }
  cancelar(c:Compra):void{
    if(!confirm(`¿Cancelar la compra CMP-${c.id_compra}?`))return;
    this.api.patch<ApiMensaje>(`/compras/${c.id_compra}/cancelar`).subscribe({next:r=>{this.mensaje=r.mensaje;this.cargar();},error:e=>this.error=mensajeError(e)});
  }
}

```

## `src/app/pages/dashboard/dashboard.html`

```html
  <div class="page-header">
    <div>
      <h1 class="page-title">Dashboard Ejecutivo — Burguer.ING</h1>
      <p class="page-subtitle">Resumen integral de operaciones, inventario y rentabilidad en León, Guanajuato.</p>
    </div>
    <div class="flex gap-2 flex-wrap">
      <button class="btn btn-dark" (click)="cargar()"><app-icon name="refresh" [size]="15" /> Actualizar datos</button>
      <a routerLink="/compras" class="btn btn-red"><app-icon name="cart" [size]="16" /> Ver Compras</a>
    </div>
  </div>
  @if (error) { <div class="notice notice-error mb-5">{{error}}</div> }
  @if (cargando) { <div class="loading-line">Consultando datos reales de Flask...</div> }
  <div class="kpi-grid mb-6">
    <section class="panel kpi">
      <div class="flex justify-between items-start"><div class="kpi-label">Ingresos totales</div><div class="kpi-icon bg-emerald-100 text-emerald-700"><app-icon name="money" [size]="19" /></div></div>
      <div class="kpi-number">{{ moneda(resumen?.ventas?.monto || 0) }}</div>
      <div class="kpi-caption metric-green">{{resumen?.ventas?.cantidad || 0}} ventas registradas</div>
    </section>
    <section class="panel kpi">
      <div class="flex justify-between items-start"><div class="kpi-label">Diferencia referencial</div><div class="kpi-icon bg-red-100 text-red-600"><app-icon name="chart" [size]="19" /></div></div>
      <div class="kpi-number" [class.metric-red]="(resumen?.diferencia_referencial || 0)<0">{{ moneda(resumen?.diferencia_referencial || 0) }}</div>
      <div class="kpi-caption">Ventas − compras − gastos · No es utilidad neta</div>
    </section>
    <section class="panel kpi">
      <div class="flex justify-between items-start"><div class="kpi-label">Compras pendientes</div><div class="kpi-icon bg-blue-100 text-blue-700"><app-icon name="cart" [size]="19" /></div></div>
      <div class="kpi-number">{{comprasPendientes}}</div><div class="kpi-caption">Pendientes de recibir en almacén</div>
    </section>
    <section class="panel kpi border-amber-300">
      <div class="flex justify-between items-start"><div class="kpi-label text-amber-800">Alertas inventario</div><div class="kpi-icon bg-amber-500 text-white"><app-icon name="warning" [size]="19" /></div></div>
      <div class="kpi-number metric-orange">{{resumen?.inventario?.materias_primas_stock_bajo || 0}} <span class="text-base font-normal">insumos</span></div><div class="kpi-caption metric-orange">Stock mínimo alcanzado</div>
    </section>
  </div>
  <div class="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-6 mb-6">
    <section class="panel p-5">
      <div class="flex justify-between gap-3 items-start mb-6">
        <div><div class="panel-title">Ventas por día (MXN)</div><div class="text-xs text-zinc-500 mt-1">Ingresos registrados en el sistema</div></div>
        <span class="chip chip-gray">Datos reales</span>
      </div>
      @if (ventasDias.length) {
        <div class="h-[260px] flex gap-3 items-end border-b border-zinc-200 px-2 pb-1">
          @for (dia of ventasDias; track dia.fecha) {
            <div class="flex flex-1 flex-col h-full items-center justify-end min-w-0 gap-2" [title]="dia.fecha+' · '+moneda(dia.total)">
              <span class="text-[10px] text-zinc-600 font-bold">{{monedaCorta(dia.total)}}</span>
              <div class="w-[70%] max-w-[90px] rounded-t-lg bg-[#e5232a] min-h-[4px]" [style.height.%]="altoBarra(dia.total)"></div>
            </div>
          }
        </div>
        <div class="flex gap-3 px-2 pt-2 text-[10px] text-zinc-500">
          @for (dia of ventasDias; track dia.fecha) { <div class="flex-1 min-w-0 text-center truncate">{{dia.fecha.slice(5)}}</div> }
        </div>
      } @else { <div class="empty-state">Todavía no hay ventas registradas para graficar.</div> }
    </section>
    <section class="panel p-5">
      <div class="panel-title">Productos por categoría</div>
      <div class="text-xs text-zinc-500 mt-1 mb-6">Distribución del catálogo (no representa ventas)</div>
      @if (categorias.length) {
        <div class="w-[230px] h-[230px] mx-auto rounded-full relative" [style.background]="gradienteDonut">
          <div class="absolute inset-[48px] rounded-full bg-white flex items-center justify-center flex-col"><div class="text-3xl font-extrabold">{{totalProductos}}</div><div class="text-xs text-zinc-500">productos</div></div>
        </div>
        <div class="flex flex-wrap justify-center gap-3 mt-6">
          @for (cat of categorias; track cat.nombre) {
            <span class="text-[11px] text-zinc-500 flex items-center gap-2"><span class="w-3 h-3 rounded-sm" [style.background]="cat.color"></span>{{cat.nombre}} ({{cat.cantidad}})</span>
          }
        </div>
      } @else { <div class="empty-state">Sin productos disponibles para esta gráfica.</div> }
    </section>
  </div>
  <div class="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-6">
    <section class="panel overflow-hidden">
      <div class="p-5 border-b border-zinc-100 flex items-center justify-between"><div class="panel-title">Compras recientes</div><a routerLink="/compras" class="btn-link-red text-xs">Gestionar todas</a></div>
      <div class="data-table-wrap">
        <table class="data-table"><thead><tr><th>Compra</th><th>Proveedor</th><th>Total</th><th>Estado</th></tr></thead>
          <tbody>
            @for (compra of recientes; track compra.id_compra) {
              <tr><td class="font-bold">CMP-{{compra.id_compra}}</td><td>{{compra.proveedor}}</td><td class="font-bold">{{moneda(compra.total)}}</td><td><span class="chip" [class.chip-yellow]="compra.estado==='Pendiente'" [class.chip-green]="compra.estado==='Recibida'" [class.chip-gray]="compra.estado==='Cancelada'">{{compra.estado}}</span></td></tr>
            } @empty { <tr><td colspan="4" class="text-center text-zinc-400">Sin compras registradas</td></tr> }
          </tbody>
        </table>
      </div>
    </section>
    <section class="panel p-5">
      <div class="panel-title mb-4">Materias primas por reabastecer</div>
      @for (materia of bajas; track materia.id_materia_prima) {
        <div class="alert-banner mb-2"><strong>{{materia.nombre}}</strong><div class="mt-1">Disponible: {{materia.stock_actual}} {{materia.unidad_medida}} · Mínimo: {{materia.stock_minimo}}</div></div>
      } @empty { <div class="empty-state">No hay alertas de inventario.</div> }
      <div class="border-t border-zinc-100 mt-4 pt-3 text-xs text-zinc-500 flex justify-between"><span>Usuarios registrados</span><strong>{{totalUsuarios}}</strong></div>
      <a routerLink="/inventario" class="btn btn-outline w-full mt-4">Ver inventario <app-icon name="arrow" [size]="16" /></a>
    </section>
  </div>

```

## `src/app/pages/dashboard/dashboard.ts`

```typescript
import { Component, OnInit, inject } from '@angular/core';
import { forkJoin } from 'rxjs';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Compra, MateriaPrima, ReporteResumen, Usuario, VentaDia } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

interface ProductoSimple { id_producto: number; categoria: string; }
interface CategoriaDistribucion { nombre: string; cantidad: number; porcentaje: number; color: string; }

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, Icon],
  templateUrl: './dashboard.html'
})
export class Dashboard implements OnInit {
  private readonly api = inject(ApiService);
  cargando = false;
  error = '';
  resumen: ReporteResumen | null = null;
  compras: Compra[] = [];
  materias: MateriaPrima[] = [];
  ventasDias: VentaDia[] = [];
  categorias: CategoriaDistribucion[] = [];
  totalProductos = 0;
  totalUsuarios = 0;
  gradienteDonut = 'conic-gradient(#e5232a 0 100%)';
  private readonly colores = ['#e5232a','#f5a000','#181818','#2563eb','#10b981','#a855f7'];

  ngOnInit(): void { this.cargar(); }
  get comprasPendientes(): number { return this.compras.filter(c => c.estado === 'Pendiente').length; }
  get recientes(): Compra[] { return this.compras.slice(0, 4); }
  get bajas(): MateriaPrima[] { return this.materias.filter(m => m.estado === 1 && m.stock_actual <= m.stock_minimo).slice(0, 4); }
  moneda(valor: number): string { return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(valor); }
  monedaCorta(valor: number): string { return valor >= 1000 ? '$'+(valor/1000).toFixed(1)+'k' : '$'+valor.toFixed(0); }
  altoBarra(valor: number): number {
    const max = Math.max(1,...this.ventasDias.map(d => d.total));
    return Math.max(2, (valor / max) * 83);
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    forkJoin({
      resumen: this.api.get<ReporteResumen>('/reportes/resumen'),
      ventas: this.api.get<VentaDia[]>('/reportes/ventas'),
      compras: this.api.get<Compra[]>('/compras/'),
      inventario: this.api.get<MateriaPrima[]>('/inventario/'),
      usuarios: this.api.get<Usuario[]>('/usuarios/'),
      productos: this.api.get<ProductoSimple[]>('/productos/')
    }).subscribe({
      next: r => {
        this.resumen = r.resumen;
        this.compras = r.compras;
        this.materias = r.inventario;
        this.totalUsuarios = r.usuarios.length;
        this.ventasDias = [...r.ventas].slice(0, 7).reverse();
        this.crearCategorias(r.productos);
        this.cargando = false;
      },
      error: e => { this.cargando = false; this.error = mensajeError(e); }
    });
  }

  private crearCategorias(productos: ProductoSimple[]): void {
    this.totalProductos = productos.length;
    const grupos = new Map<string,number>();
    for (const producto of productos) grupos.set(producto.categoria || 'Sin categoría', (grupos.get(producto.categoria || 'Sin categoría') || 0) + 1);
    let acumulado = 0;
    const tramos: string[] = [];
    this.categorias = [...grupos.entries()].map(([nombre,cantidad],i) => {
      const porcentaje = this.totalProductos ? cantidad / this.totalProductos * 100 : 0;
      const color = this.colores[i % this.colores.length];
      tramos.push(`${color} ${acumulado}% ${acumulado + porcentaje}%`);
      acumulado += porcentaje;
      return { nombre, cantidad, porcentaje, color };
    });
    this.gradienteDonut = `conic-gradient(${tramos.join(', ')})`;
  }
}

```

## `src/app/pages/gastos-finanzas/gastos-finanzas.html`

```html
<!-- Pantalla lista para que otro integrante desarrolle este módulo. -->
<section class="page-header">
  <div>
    <h1 class="page-title">Gastos y finanzas</h1>
  </div>
</section>
<div class="panel" style="min-height: 65vh;"></div>

```

## `src/app/pages/gastos-finanzas/gastos-finanzas.ts`

```typescript
import { Component } from '@angular/core';

// Módulo reservado para otro integrante del equipo.
// Podrán agregar servicios, formularios y peticiones HTTP aquí.
@Component({
  selector: 'app-gastos-finanzas',
  standalone: true,
  templateUrl: './gastos-finanzas.html'
})
export class GastosFinanzasPendiente {}

```

## `src/app/pages/inventario/inventario.html`

```html
  <div class="page-header">
    <div><h1 class="page-title">Control de Inventario y Kardex</h1><p class="page-subtitle">Existencias actualizadas, alertas de reabastecimiento y trazabilidad de entradas/salidas.</p></div>
    <button class="btn btn-dark" (click)="abrirModal()"><app-icon name="filter" [size]="16" /> Registrar Ajuste de Inventario</button>
  </div>
  @if (mensaje) { <div class="notice notice-ok mb-4">{{mensaje}}</div> }
  @if (error) { <div class="notice notice-error mb-4">{{error}}</div> }
  <div class="kpi-grid mb-6">
    <div class="panel kpi"><div class="text-xs font-bold text-zinc-500">Valor Estimado del Inventario</div><div class="kpi-number">{{moneda(valorInventario)}}</div><div class="kpi-caption metric-green">Costo valuado al precio registrado</div></div>
    <div class="panel kpi"><div class="text-xs font-bold text-zinc-500">Insumos Registrados</div><div class="kpi-number">{{materias.length}}</div><div class="kpi-caption">Control de existencias</div></div>
    <div class="panel kpi border-amber-300"><div class="text-xs font-bold metric-orange">Alertas Stock Mínimo</div><div class="kpi-number metric-orange">{{totalAlertas}}</div><div class="kpi-caption metric-orange">Requieren orden de compra</div></div>
    <div class="panel kpi border-red-200"><div class="text-xs font-bold metric-red">Materias Primas Agotadas</div><div class="kpi-number metric-red">{{agotados}}</div><div class="kpi-caption metric-red">Existencia en 0</div></div>
  </div>
  <div class="grid grid-cols-1 xl:grid-cols-[1.4fr_1fr] gap-6">
    <section class="panel overflow-hidden">
      <div class="p-5 flex justify-between items-center border-b border-zinc-100 gap-3"><div class="panel-title">Existencias por Ingrediente</div><span class="text-xs text-zinc-400">{{cargando?'Actualizando...':'Datos de MySQL'}}</span></div>
      <div class="p-4"><input class="form-control" [(ngModel)]="busqueda" placeholder="Buscar materia prima..." /></div>
      <div class="data-table-wrap max-h-[570px] overflow-y-auto">
        <table class="data-table"><thead><tr><th>Ingrediente</th><th>Stock actual</th><th>Mínimo</th><th>Valor</th><th>Estado</th></tr></thead>
          <tbody>
            @for (m of materiasFiltradas; track m.id_materia_prima) {
              <tr><td class="font-bold min-w-[160px]">{{m.nombre}}</td>
              <td class="font-bold" [class.metric-green]="m.stock_actual>m.stock_minimo" [class.metric-orange]="m.stock_actual<=m.stock_minimo">{{cantidad(m.stock_actual,m.unidad_medida)}}</td>
              <td class="text-zinc-500">{{cantidad(m.stock_minimo,m.unidad_medida)}}</td>
              <td>{{moneda(m.stock_actual*m.costo_unitario)}}</td>
              <td><span class="chip" [class.chip-red]="m.stock_actual<=0" [class.chip-yellow]="m.stock_actual>0&&m.stock_actual<=m.stock_minimo" [class.chip-green]="m.stock_actual>m.stock_minimo">{{m.stock_actual<=0?'Agotado':m.stock_actual<=m.stock_minimo?'Stock bajo':'Óptimo'}}</span></td></tr>
            } @empty { <tr><td colspan="5" class="empty-state">Sin materias primas.</td></tr> }
          </tbody>
        </table>
      </div>
    </section>
    <section class="panel overflow-hidden">
      <div class="p-5 flex justify-between border-b border-zinc-100"><span class="panel-title">Historial de Movimientos</span><span class="text-[#e5232a] text-xs font-semibold">Kardex</span></div>
      <div class="p-4 max-h-[700px] overflow-y-auto space-y-3">
        @for (mov of movimientos;track mov.id_movimiento) {
          <div class="border border-zinc-100 rounded-xl p-4 bg-zinc-50">
            <div class="flex justify-between gap-3"><div><div class="text-xs font-bold" [class.text-emerald-700]="esEntrada(mov)" [class.text-red-600]="!esEntrada(mov)">{{etiquetaMovimiento(mov.tipo_movimiento)}}</div><div class="font-extrabold text-sm mt-1">{{mov.materia_prima}}</div></div>
              <span class="chip h-fit" [class.chip-green]="esEntrada(mov)" [class.chip-red]="!esEntrada(mov)">{{esEntrada(mov)?'+':'−'}}{{cantidad(mov.cantidad,mov.unidad_medida||'')}}</span></div>
            <div class="text-[11px] mt-2 text-zinc-500">{{mov.motivo||'Sin motivo'}} · {{mov.fecha_movimiento}}</div>
          </div>
        } @empty { <div class="empty-state">{{cargandoMovimientos?'Cargando historial...':'Todavía no hay movimientos registrados.'}}</div> }
      </div>
    </section>
  </div>
  @if (modalAbierto) {
    <div class="modal-backdrop" (click)="modalAbierto=false"><div class="modal-panel" role="dialog" aria-modal="true" (click)="$event.stopPropagation()">
      <div class="modal-header"><h2 class="panel-title">Registrar movimiento de inventario</h2><button (click)="modalAbierto=false" aria-label="Cerrar"><app-icon name="close" [size]="19" /></button></div>
      <form (ngSubmit)="guardarMovimiento()"><div class="modal-body space-y-4">
        @if (errorModal) { <div class="notice notice-error">{{errorModal}}</div> }
        <div class="form-field"><label>Tipo de movimiento *</label><select class="form-control" name="tipo" [(ngModel)]="tipoMovimiento"><option value="AjusteEntrada">Ajuste de entrada (+)</option><option value="AjusteSalida">Ajuste de salida (−)</option><option value="Merma">Merma (−)</option></select></div>
        <div class="form-field"><label>Materia prima *</label><select class="form-control" name="materia" [(ngModel)]="idMateria" required>
          <option [ngValue]="0">Selecciona materia prima</option>
          @for (m of materiasActivas;track m.id_materia_prima){<option [ngValue]="m.id_materia_prima">{{m.nombre}} — {{m.stock_actual}} {{m.unidad_medida}}</option>}
        </select></div>
        <div class="form-field"><label>Cantidad ({{unidadSeleccionada}}) *</label><input class="form-control" name="cantidad" [(ngModel)]="cantidadMovimiento" type="number" step="0.001" min="0.001" required /></div>
        <div class="form-field"><label>Motivo *</label><textarea class="form-control" name="motivo" [(ngModel)]="motivo" rows="2" required placeholder="Ej. Conteo físico / Producto dañado"></textarea></div>
        <div class="alert-banner">Los movimientos actualizan el stock inmediatamente. No uses ajustes para registrar una compra: esa operación se hace desde Compras.</div>
      </div>
      <div class="modal-footer"><button class="btn btn-outline" type="button" (click)="modalAbierto=false">Cancelar</button><button class="btn btn-red" type="submit" [disabled]="guardando">{{guardando?'Guardando...':'Registrar movimiento'}}</button></div></form>
    </div></div>
  }

```

## `src/app/pages/inventario/inventario.ts`

```typescript
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { AlertasResponse, ApiMensaje, MateriaPrima, Movimiento, MovimientosResponse } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

@Component({
  selector: 'app-inventario', standalone: true, imports:[FormsModule,Icon],
  templateUrl: './inventario.html'
})
export class Inventario implements OnInit {
  private readonly api=inject(ApiService);
  private readonly auth=inject(AuthService);
  materias:MateriaPrima[]=[];
  movimientos:Movimiento[]=[];
  totalAlertas=0;
  busqueda='';
  cargando=false;
  cargandoMovimientos=false;
  guardando=false;
  modalAbierto=false;
  error='';errorModal='';mensaje='';
  tipoMovimiento:'AjusteEntrada'|'AjusteSalida'|'Merma'='AjusteEntrada';
  idMateria=0;cantidadMovimiento=1;motivo='';
  ngOnInit():void{this.cargar();}
  get materiasActivas():MateriaPrima[]{return this.materias.filter(m=>m.estado===1);}
  get materiasFiltradas():MateriaPrima[]{return this.materias.filter(m=>m.nombre.toLowerCase().includes(this.busqueda.toLowerCase()));}
  get valorInventario():number{return this.materiasActivas.reduce((a,m)=>a+m.stock_actual*m.costo_unitario,0);}
  get agotados():number{return this.materiasActivas.filter(m=>m.stock_actual===0).length;}
  get unidadSeleccionada():string{return this.materias.find(m=>m.id_materia_prima===this.idMateria)?.unidad_medida||'unidades';}
  moneda(v:number):string{return new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN'}).format(v);}
  cantidad(x:number,u:string):string{return new Intl.NumberFormat('es-MX',{maximumFractionDigits:3}).format(x)+' '+u;}
  esEntrada(m:Movimiento):boolean{return ['EntradaCompra','AjusteEntrada'].includes(m.tipo_movimiento);}
  etiquetaMovimiento(tipo:string):string{
    const nombres:Record<string,string>={EntradaCompra:'Entrada (compra)',SalidaProduccion:'Salida (producción)',AjusteEntrada:'Ajuste (+)',AjusteSalida:'Ajuste (−)',Merma:'Merma'};
    return nombres[tipo]||tipo;
  }
  cargar():void{
    this.cargando=true;this.error='';
    forkJoin({materias:this.api.get<MateriaPrima[]>('/inventario/'),alertas:this.api.get<AlertasResponse>('/inventario/alertas')}).subscribe({
      next:r=>{this.materias=r.materias;this.totalAlertas=r.alertas.total_alertas;this.cargando=false;this.cargarMovimientos();},
      error:e=>{this.cargando=false;this.error=mensajeError(e);}
    });
  }
  cargarMovimientos():void{
    if(!this.materias.length){this.movimientos=[];return;}
    this.cargandoMovimientos=true;
    // El Flask existente solo ofrece movimientos por materia prima.
    // Reunimos las consultas para construir el kardex global sin modificar el backend.
    forkJoin(this.materias.map(m=>this.api.get<MovimientosResponse>(`/inventario/${m.id_materia_prima}/movimientos`))).subscribe({
      next:resultados=>{
        this.movimientos=resultados.flatMap(r=>r.movimientos.map(m=>({...m,materia_prima:r.materia_prima.nombre,unidad_medida:r.materia_prima.unidad_medida,id_materia_prima:r.materia_prima.id_materia_prima})))
          .sort((a,b)=>b.fecha_movimiento.localeCompare(a.fecha_movimiento)||b.id_movimiento-a.id_movimiento).slice(0,35);
        this.cargandoMovimientos=false;
      },
      error:e=>{this.cargandoMovimientos=false;this.error=mensajeError(e);}
    });
  }
  abrirModal():void {this.tipoMovimiento='AjusteEntrada';this.idMateria=this.materiasActivas[0]?.id_materia_prima||0;this.cantidadMovimiento=1;this.motivo='';this.errorModal='';this.modalAbierto=true;}
  guardarMovimiento():void {
    this.errorModal='';
    if(!this.idMateria||!(this.cantidadMovimiento>0)||!this.motivo.trim()){this.errorModal='Selecciona materia prima, cantidad y motivo.';return;}
    const usuario=this.auth.usuario();
    this.guardando=true;
    const body={id_materia_prima:this.idMateria,cantidad:this.cantidadMovimiento,motivo:this.motivo.trim(),id_usuario:usuario?.id_usuario??null};
    const req=this.tipoMovimiento==='Merma'
      ?this.api.post<ApiMensaje>('/inventario/merma',body)
      :this.api.post<ApiMensaje>('/inventario/ajuste',{...body,tipo_movimiento:this.tipoMovimiento});
    req.subscribe({
      next:r=>{this.guardando=false;this.modalAbierto=false;this.mensaje=r.mensaje;this.cargar();},
      error:e=>{this.guardando=false;this.errorModal=mensajeError(e);}
    });
  }
}

```

## `src/app/pages/login/login.html`

```html
  <div class="min-h-screen grid lg:grid-cols-2 bg-[#f5f5f5]">
    <div class="hidden lg:flex bg-[#171717] text-white p-16 flex-col justify-between relative overflow-hidden">
      <div class="flex items-center gap-3 text-2xl font-extrabold"><span class="logo-square">◎</span> Burguer<span class="logo-ing">.ING</span></div>
      <div class="relative z-10">
        <div class="text-[#f8a31b] font-bold tracking-[.2em] uppercase text-sm mb-5">Sistema Integral de Gestión</div>
        <h1 class="heading-font text-6xl font-extrabold leading-[1.15] mb-6">Controla tu<br/>restaurante.<br/><span class="text-[#ed262d]">Sin complicaciones.</span></h1>
        <p class="text-zinc-400 max-w-lg leading-7">Inventario, compras, proveedores, usuarios y operaciones en un solo lugar.</p>
      </div>
      <div class="text-zinc-500 text-sm">León, Guanajuato · Proyecto escolar</div>
      <div class="absolute rounded-full w-96 h-96 border-[70px] border-[#e5232a]/10 -right-32 -bottom-32"></div>
    </div>
    <div class="flex items-center justify-center p-5 md:p-14">
      <div class="w-full max-w-md">
        <div class="lg:hidden flex items-center gap-2 mb-10 text-2xl font-extrabold"><span class="logo-square">◎</span> Burguer.ING</div>
        <h2 class="heading-font text-3xl font-extrabold mb-2">Bienvenido de nuevo</h2>
        <p class="text-zinc-500 mb-8 text-sm">Accede al panel de administración de Burguer.ING.</p>
        <form (ngSubmit)="entrar()" class="panel p-8 space-y-5">
          @if (error) { <div class="notice notice-error">{{error}}</div> }
          <div class="form-field"><label for="correo">Correo electrónico</label>
            <input id="correo" class="form-control" type="email" name="correo" autocomplete="username" placeholder="admin@burguering.com" [(ngModel)]="correo" required />
          </div>
          <div class="form-field"><label for="password">Contraseña</label>
            <input id="password" class="form-control" type="password" name="password" autocomplete="current-password" [(ngModel)]="password" required />
          </div>
          <button class="btn btn-red w-full" type="submit" [disabled]="cargando">
            {{ cargando ? 'Iniciando sesión...' : 'Entrar al sistema' }} <app-icon name="arrow" [size]="18" />
          </button>
          <p class="text-xs text-zinc-400 text-center">Utiliza las cuentas que registraste en Flask/MySQL.</p>
        </form>
        <div class="text-xs text-zinc-500 mt-6 text-center">La sesión utiliza el endpoint <code>/api/usuarios/login</code>.</div>
      </div>
    </div>
  </div>

```

## `src/app/pages/login/login.ts`

```typescript
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

```

## `src/app/pages/materias-primas/materias-primas.html`

```html
  <div class="page-header">
    <div><h1 class="page-title">Catálogo de Materias Primas</h1><p class="page-subtitle">Insumos base, costos unitarios, unidades y parámetros de stock mínimo.</p></div>
    <button class="btn btn-red" (click)="abrirCrear()"><app-icon name="plus" [size]="17" /> Agregar Materia Prima</button>
  </div>
  @if (mensaje) { <div class="notice notice-ok mb-4">{{mensaje}}</div> }
  @if (error) { <div class="notice notice-error mb-4">{{error}}</div> }
  <div class="panel p-4 mb-6 flex flex-wrap justify-between gap-3 items-center">
    <div class="relative w-full max-w-[340px]"><app-icon name="search" [size]="16" class="absolute left-3 top-3 text-zinc-400" /><input class="search-input" [(ngModel)]="filtro" placeholder="Buscar ingrediente o ID..." /></div>
    <div class="filter-row"><button class="filter-pill" [class.selected]="categoriaFiltro===0" (click)="categoriaFiltro=0">Todas</button>
      @for (cat of categorias; track cat.id_categoria_insumo) {
        <button class="filter-pill" [class.selected]="categoriaFiltro===cat.id_categoria_insumo" (click)="categoriaFiltro=cat.id_categoria_insumo">{{cat.nombre}}</button>
      }
    </div>
  </div>
  <div class="panel data-table-wrap">
    <table class="data-table"><thead><tr><th>ID</th><th>Ingrediente</th><th>Categoría</th><th>Costo compra</th><th>Disponible</th><th>Stock mín.</th><th>Estado</th><th class="text-right">Acciones</th></tr></thead>
      <tbody>
        @for (m of materiasFiltradas; track m.id_materia_prima) {
          <tr>
            <td class="font-mono text-xs">MP-{{m.id_materia_prima.toString().padStart(2,'0')}}</td>
            <td class="font-semibold text-zinc-900 min-w-[155px]">{{m.nombre}}</td>
            <td><span class="chip chip-gray">{{m.categoria}}</span></td>
            <td>{{moneda(m.costo_unitario)}} / {{m.unidad_medida}}</td>
            <td [class.metric-green]="m.stock_actual>m.stock_minimo" [class.metric-orange]="m.stock_actual<=m.stock_minimo" class="font-bold">{{cantidad(m.stock_actual,m.unidad_medida)}}</td>
            <td class="text-zinc-500">{{cantidad(m.stock_minimo,m.unidad_medida)}}</td>
            <td><span class="chip" [class.chip-green]="m.estado===1" [class.chip-gray]="m.estado===0">{{m.estado===1?'Activo':'Inactivo'}}</span></td>
            <td><div class="actions-inline"><button class="table-action" title="Editar" (click)="abrirEditar(m)"><app-icon name="edit" [size]="16" /></button><button class="table-action" [title]="m.estado===1?'Desactivar':'Activar'" (click)="cambiarEstado(m)"><app-icon [name]="m.estado===1?'close':'check'" [size]="16" /></button></div></td>
          </tr>
        } @empty { <tr><td colspan="8" class="text-center p-10 text-zinc-400">{{cargando?'Cargando materias primas...':'No se encontraron materias primas.'}}</td></tr> }
      </tbody>
    </table>
  </div>
  <p class="text-[11px] text-zinc-500 mt-4">El stock actual solo se modifica en Compras o Inventario. Los campos proveedor y caducidad de tu referencia visual no existen en el esquema MySQL actual.</p>
  @if (modalAbierto) {
    <div class="modal-backdrop" (click)="modalAbierto=false">
      <div class="modal-panel" role="dialog" aria-modal="true" (click)="$event.stopPropagation()">
        <div class="modal-header"><h2 class="panel-title">{{editandoId?'Editar materia prima':'Agregar materia prima'}}</h2><button (click)="modalAbierto=false" aria-label="Cerrar"><app-icon name="close" [size]="19" /></button></div>
        <form (ngSubmit)="guardar()"><div class="modal-body space-y-4">
          @if (errorModal) { <div class="notice notice-error">{{errorModal}}</div> }
          <div class="form-field"><label>Nombre de ingrediente *</label><input class="form-control" name="nombre" [(ngModel)]="form.nombre" maxlength="120" required /></div>
          <div class="form-grid">
            <div class="form-field"><label>Categoría *</label><select class="form-control" name="categoria" [(ngModel)]="form.id_categoria_insumo" required>
              @for (cat of categorias;track cat.id_categoria_insumo){<option [ngValue]="cat.id_categoria_insumo">{{cat.nombre}}</option>}
            </select></div>
            <div class="form-field"><label>Unidad *</label><select class="form-control" name="unidad" [(ngModel)]="form.unidad_medida" required><option value="g">Gramos (g)</option><option value="ml">Mililitros (ml)</option><option value="pza">Piezas (pza)</option><option value="reb">Rebanadas (reb)</option></select></div>
            <div class="form-field"><label>Stock mínimo *</label><input class="form-control" name="stock_minimo" [(ngModel)]="form.stock_minimo" type="number" min="0" step="0.001" required /></div>
            <div class="form-field"><label>Costo por unidad (MXN) *</label><input class="form-control" name="costo_unitario" [(ngModel)]="form.costo_unitario" type="number" min="0" step="0.0001" required /></div>
          </div>
          <div class="alert-banner">El stock inicial de nuevos insumos será 0. Se aumenta mediante una compra recibida o un ajuste de entrada.</div>
        </div>
        <div class="modal-footer"><button class="btn btn-outline" type="button" (click)="modalAbierto=false">Cancelar</button><button class="btn btn-red" type="submit" [disabled]="guardando">{{guardando?'Guardando...':'Guardar insumo'}}</button></div></form>
      </div>
    </div>
  }

```

## `src/app/pages/materias-primas/materias-primas.ts`

```typescript
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { ApiMensaje, CategoriaInsumo, MateriaPrima } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

type MateriaForm = {
  id_categoria_insumo: number;
  nombre: string;
  unidad_medida: string;
  stock_minimo: number;
  costo_unitario: number;
};

@Component({
  selector: 'app-materias-primas', standalone: true, imports:[FormsModule,Icon],
  templateUrl: './materias-primas.html'
})
export class MateriasPrimas implements OnInit {
  private readonly api = inject(ApiService);
  materias: MateriaPrima[] = [];
  categorias: CategoriaInsumo[] = [];
  filtro = '';
  categoriaFiltro = 0;
  cargando = false;
  guardando = false;
  modalAbierto = false;
  editandoId: number|null = null;
  error = '';
  errorModal = '';
  mensaje = '';
  form: MateriaForm = this.formVacio();

  ngOnInit(): void { this.cargar(); }
  get materiasFiltradas(): MateriaPrima[] {
    const f=this.filtro.toLowerCase().trim();
    return this.materias.filter(m=>(this.categoriaFiltro===0||m.id_categoria_insumo===this.categoriaFiltro)
      && (!f||m.nombre.toLowerCase().includes(f)||String(m.id_materia_prima).includes(f)));
  }
  moneda(x:number):string {return new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN',maximumFractionDigits:4}).format(x);}
  cantidad(x:number,unidad:string):string {
    const t=new Intl.NumberFormat('es-MX',{maximumFractionDigits:3}).format(x)+' '+unidad;
    return unidad==='g'&&x>=1000?`${t} (${(x/1000).toFixed(2)} kg)`:t;
  }
  private formVacio():MateriaForm {return {id_categoria_insumo:0,nombre:'',unidad_medida:'g',stock_minimo:0,costo_unitario:0};}
  cargar():void {
    this.cargando=true;this.error='';
    forkJoin({materias:this.api.get<MateriaPrima[]>('/materias-primas/'),categorias:this.api.get<CategoriaInsumo[]>('/categorias-insumos/')}).subscribe({
      next:r=>{this.materias=r.materias;this.categorias=r.categorias;this.cargando=false;},
      error:e=>{this.cargando=false;this.error=mensajeError(e);}
    });
  }
  abrirCrear():void {this.editandoId=null;this.form=this.formVacio();this.form.id_categoria_insumo=this.categorias[0]?.id_categoria_insumo||0;this.errorModal='';this.modalAbierto=true;}
  abrirEditar(m:MateriaPrima):void {this.editandoId=m.id_materia_prima;this.form={id_categoria_insumo:m.id_categoria_insumo,nombre:m.nombre,unidad_medida:m.unidad_medida,stock_minimo:m.stock_minimo,costo_unitario:m.costo_unitario};this.errorModal='';this.modalAbierto=true;}
  guardar():void {
    this.errorModal='';
    if(!this.form.nombre.trim()||!this.form.id_categoria_insumo||this.form.stock_minimo<0||this.form.costo_unitario<0){this.errorModal='Revisa el nombre, la categoría y los valores numéricos.';return;}
    this.guardando=true;
    const req=this.editandoId?this.api.put<ApiMensaje>(`/materias-primas/${this.editandoId}`,this.form):this.api.post<ApiMensaje>('/materias-primas/',this.form);
    req.subscribe({next:r=>{this.guardando=false;this.modalAbierto=false;this.mensaje=r.mensaje;this.cargar();},error:e=>{this.guardando=false;this.errorModal=mensajeError(e);}});
  }
  cambiarEstado(m:MateriaPrima):void {
    const estado=m.estado===1?0:1;
    if(!confirm(`¿${estado?'Activar':'Desactivar'} ${m.nombre}?`))return;
    this.api.patch<ApiMensaje>(`/materias-primas/${m.id_materia_prima}/estado`,{estado}).subscribe({next:r=>{this.mensaje=r.mensaje;this.cargar();},error:e=>this.error=mensajeError(e)});
  }
}

```

## `src/app/pages/pedidos/pedidos.html`

```html
<!-- Pantalla lista para que otro integrante desarrolle este módulo. -->
<section class="page-header">
  <div>
    <h1 class="page-title">Pedidos</h1>
  </div>
</section>
<div class="panel" style="min-height: 65vh;"></div>

```

## `src/app/pages/pedidos/pedidos.ts`

```typescript
import { Component } from '@angular/core';

// Módulo reservado para otro integrante del equipo.
// Podrán agregar servicios, formularios y peticiones HTTP aquí.
@Component({
  selector: 'app-pedidos',
  standalone: true,
  templateUrl: './pedidos.html'
})
export class PedidosPendiente {}

```

## `src/app/pages/productos/productos.html`

```html
<!-- Pantalla lista para que otro integrante desarrolle este módulo. -->
<section class="page-header">
  <div>
    <h1 class="page-title">Productos</h1>
  </div>
</section>
<div class="panel" style="min-height: 65vh;"></div>

```

## `src/app/pages/productos/productos.ts`

```typescript
import { Component } from '@angular/core';

// Módulo reservado para otro integrante del equipo.
// Podrán agregar servicios, formularios y peticiones HTTP aquí.
@Component({
  selector: 'app-productos',
  standalone: true,
  templateUrl: './productos.html'
})
export class ProductosPendiente {}

```

## `src/app/pages/proveedores/proveedores.html`

```html
  <div class="page-header">
    <div><h1 class="page-title">Proveedores</h1><p class="page-subtitle">Directorio de socios comerciales y abastecimiento en León, Guanajuato.</p></div>
    <button class="btn btn-red" (click)="abrirCrear()"><app-icon name="plus" [size]="17" /> Registrar Proveedor</button>
  </div>
  @if (mensaje) { <div class="notice notice-ok mb-4">{{mensaje}}</div> }
  @if (error) { <div class="notice notice-error mb-4">{{error}}</div> }
  <div class="panel p-4 mb-6"><div class="relative max-w-[470px]">
    <app-icon name="search" [size]="16" class="absolute left-3 top-3 text-zinc-400" />
    <input class="search-input" placeholder="Buscar empresa, contacto o correo..." [(ngModel)]="busqueda" />
  </div></div>
  <div class="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
    @for (p of proveedoresFiltrados; track p.id_proveedor) {
      <article class="panel p-5 min-h-[262px] flex flex-col">
        <div class="flex justify-between items-center mb-4"><span class="chip chip-gray">PROV-{{p.id_proveedor.toString().padStart(2,'0')}}</span><span class="chip" [class.chip-green]="p.estado===1" [class.chip-gray]="p.estado===0">{{p.estado===1?'Activo':'Inactivo'}}</span></div>
        <h2 class="font-extrabold heading-font text-lg mb-1">{{p.nombre}}</h2>
        <p class="text-[#e5232a] font-semibold text-xs mb-3">{{p.contacto || 'Contacto sin registrar'}}</p>
        <div class="text-xs text-zinc-500 space-y-2 mb-5">
          <p>Teléfono: {{p.telefono || 'No registrado'}}</p>
          <p class="break-all">Correo: {{p.correo || 'No registrado'}}</p>
          <p>Dirección: {{p.direccion || 'No registrada'}}</p>
        </div>
        <div class="rounded-lg p-3 bg-zinc-50 text-xs text-zinc-500 mb-5">Los productos suministrados se identifican en el módulo Compras.</div>
        <div class="mt-auto pt-4 border-t border-zinc-100 flex justify-end gap-3">
          <button class="table-action flex items-center gap-1" (click)="abrirEditar(p)"><app-icon name="edit" [size]="15" /> Editar</button>
          <button class="table-action flex items-center gap-1" [class.text-red-600]="p.estado===1" (click)="cambiarEstado(p)">
            <app-icon [name]="p.estado===1?'close':'check'" [size]="15" /> {{p.estado===1?'Desactivar':'Activar'}}
          </button>
        </div>
      </article>
    } @empty { <div class="panel empty-state col-span-full">{{cargando?'Consultando proveedores...':'No se encontraron proveedores.'}}</div> }
  </div>
  @if (modalAbierto) {
    <div class="modal-backdrop" (click)="modalAbierto=false">
      <div class="modal-panel" role="dialog" aria-modal="true" (click)="$event.stopPropagation()">
        <div class="modal-header"><h2 class="panel-title">{{editandoId?'Editar proveedor':'Registrar proveedor'}}</h2><button (click)="modalAbierto=false" aria-label="Cerrar"><app-icon name="close" [size]="19" /></button></div>
        <form (ngSubmit)="guardar()">
          <div class="modal-body space-y-4">
            @if (errorModal) { <div class="notice notice-error">{{errorModal}}</div> }
            <div class="form-field"><label>Nombre de empresa *</label><input class="form-control" name="nombre" [(ngModel)]="form.nombre" maxlength="120" required /></div>
            <div class="form-grid">
              <div class="form-field"><label>Contacto</label><input class="form-control" name="contacto" [(ngModel)]="form.contacto" /></div>
              <div class="form-field"><label>Teléfono</label><input class="form-control" name="telefono" [(ngModel)]="form.telefono" /></div>
            </div>
            <div class="form-field"><label>Correo</label><input class="form-control" type="email" name="correo" [(ngModel)]="form.correo" /></div>
            <div class="form-field"><label>Dirección</label><textarea class="form-control" name="direccion" [(ngModel)]="form.direccion" rows="2"></textarea></div>
          </div>
          <div class="modal-footer"><button class="btn btn-outline" type="button" (click)="modalAbierto=false">Cancelar</button><button type="submit" class="btn btn-red" [disabled]="guardando">{{guardando?'Guardando...':'Guardar proveedor'}}</button></div>
        </form>
      </div>
    </div>
  }

```

## `src/app/pages/proveedores/proveedores.ts`

```typescript
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { ApiMensaje, Proveedor } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

type ProveedorForm = Pick<Proveedor,'nombre'|'contacto'|'telefono'|'correo'|'direccion'>;

@Component({
  selector: 'app-proveedores', standalone: true, imports: [FormsModule,Icon],
  templateUrl: './proveedores.html'
})
export class Proveedores implements OnInit {
  private readonly api = inject(ApiService);
  proveedores: Proveedor[] = [];
  busqueda = '';
  modalAbierto = false;
  editandoId: number|null = null;
  form: ProveedorForm = this.vacio();
  cargando = false;
  guardando = false;
  mensaje = '';
  error = '';
  errorModal = '';
  ngOnInit(): void { this.cargar(); }
  get proveedoresFiltrados(): Proveedor[] {
    const texto = this.busqueda.toLowerCase().trim();
    return this.proveedores.filter(p => `${p.nombre} ${p.contacto||''} ${p.correo||''}`.toLowerCase().includes(texto));
  }
  private vacio(): ProveedorForm { return {nombre:'',contacto:'',telefono:'',correo:'',direccion:''}; }
  cargar(): void {
    this.cargando = true; this.error='';
    this.api.get<Proveedor[]>('/proveedores/').subscribe({
      next: r => {this.proveedores=r;this.cargando=false;},
      error: e => {this.error=mensajeError(e);this.cargando=false;}
    });
  }
  abrirCrear(): void { this.editandoId=null;this.form=this.vacio();this.errorModal='';this.modalAbierto=true; }
  abrirEditar(p: Proveedor): void {
    this.editandoId=p.id_proveedor;
    this.form={nombre:p.nombre,contacto:p.contacto||'',telefono:p.telefono||'',correo:p.correo||'',direccion:p.direccion||''};
    this.errorModal='';this.modalAbierto=true;
  }
  guardar(): void {
    this.errorModal='';
    if (!this.form.nombre.trim()) {this.errorModal='El nombre es obligatorio.';return;}
    this.guardando=true;
    const req = this.editandoId
      ? this.api.put<ApiMensaje>(`/proveedores/${this.editandoId}`,this.form)
      : this.api.post<ApiMensaje>('/proveedores/',this.form);
    req.subscribe({
      next:r=>{this.guardando=false;this.modalAbierto=false;this.mensaje=r.mensaje;this.cargar();},
      error:e=>{this.guardando=false;this.errorModal=mensajeError(e);}
    });
  }
  cambiarEstado(p:Proveedor):void {
    const estado=p.estado===1?0:1;
    if(!confirm(`¿${estado?'Activar':'Desactivar'} al proveedor ${p.nombre}?`))return;
    this.api.patch<ApiMensaje>(`/proveedores/${p.id_proveedor}/estado`,{estado}).subscribe({
      next:r=>{this.mensaje=r.mensaje;this.cargar();},error:e=>this.error=mensajeError(e)
    });
  }
}

```

## `src/app/pages/recetas-produccion/recetas-produccion.html`

```html
<!-- Pantalla lista para que otro integrante desarrolle este módulo. -->
<section class="page-header">
  <div>
    <h1 class="page-title">Recetas y producción</h1>
  </div>
</section>
<div class="panel" style="min-height: 65vh;"></div>

```

## `src/app/pages/recetas-produccion/recetas-produccion.ts`

```typescript
import { Component } from '@angular/core';

// Módulo reservado para otro integrante del equipo.
// Podrán agregar servicios, formularios y peticiones HTTP aquí.
@Component({
  selector: 'app-recetas-produccion',
  standalone: true,
  templateUrl: './recetas-produccion.html'
})
export class RecetasProduccionPendiente {}

```

## `src/app/pages/usuarios/usuarios.html`

```html
  <div class="page-header">
    <div><h1 class="page-title">Usuarios y Roles</h1><p class="page-subtitle">Administración de accesos para administradores, personal y clientes.</p></div>
    <button class="btn btn-red" (click)="abrirCrear()"><app-icon name="plus" [size]="17" /> Agregar Usuario</button>
  </div>
  @if (mensaje) { <div class="notice notice-ok mb-4">{{mensaje}}</div> }
  @if (error) { <div class="notice notice-error mb-4">{{error}}</div> }
  <div class="panel p-4 mb-6 flex flex-wrap justify-between items-center gap-4">
    <div class="relative w-full max-w-[350px]">
      <app-icon name="search" [size]="16" class="absolute left-3 top-3 text-zinc-400" />
      <input class="search-input" [(ngModel)]="filtro" placeholder="Buscar por nombre o correo..." aria-label="Buscar usuarios" />
    </div>
    <div class="filter-row">
      @for (rol of filtrosRoles; track rol) {
        <button type="button" class="filter-pill" [class.selected]="rolSeleccionado===rol" (click)="rolSeleccionado=rol">{{rol}}</button>
      }
    </div>
  </div>
  <div class="panel data-table-wrap">
    <table class="data-table">
      <thead><tr><th>Usuario</th><th>Correo electrónico</th><th>Rol</th><th>Estado</th><th>Registro</th><th class="text-right">Acciones</th></tr></thead>
      <tbody>
        @for (u of usuariosFiltrados; track u.id_usuario) {
          <tr>
            <td class="font-bold text-zinc-900">{{u.nombre}}</td><td>{{u.correo}}</td>
            <td><span class="chip" [class.chip-red]="u.rol==='Administrador'" [class.chip-yellow]="u.rol==='Empleado'" [class.chip-blue]="u.rol==='Cliente'">{{u.rol}}</span></td>
            <td><span class="chip" [class.chip-green]="u.estado===1" [class.chip-gray]="u.estado===0">{{u.estado===1?'Activo':'Inactivo'}}</span></td>
            <td class="text-zinc-500">{{u.fecha_registro?.slice(0,10)}}</td>
            <td><div class="actions-inline">
              <button class="table-action" (click)="abrirEditar(u)" title="Editar usuario" aria-label="Editar usuario"><app-icon name="edit" [size]="17" /></button>
              <button class="table-action" (click)="cambiarEstado(u)" [title]="u.estado===1?'Desactivar':'Activar'" [attr.aria-label]="u.estado===1?'Desactivar usuario':'Activar usuario'"><app-icon [name]="u.estado===1?'close':'check'" [size]="17" /></button>
            </div></td>
          </tr>
        } @empty { <tr><td colspan="6" class="text-center text-zinc-400 p-10">{{cargando?'Cargando usuarios...':'No se encontraron usuarios.'}}</td></tr> }
      </tbody>
    </table>
  </div>
  @if (modalAbierto) {
    <div class="modal-backdrop" (click)="cerrarModal()">
      <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="usuario-title" (click)="$event.stopPropagation()">
        <div class="modal-header"><h2 id="usuario-title" class="panel-title">{{editandoId?'Editar usuario':'Agregar usuario'}}</h2><button (click)="cerrarModal()" aria-label="Cerrar"><app-icon name="close" [size]="19" /></button></div>
        <form (ngSubmit)="guardar()">
          <div class="modal-body space-y-4">
            @if (errorModal) { <div class="notice notice-error">{{errorModal}}</div> }
            <div class="form-field"><label>Nombre completo *</label><input class="form-control" [(ngModel)]="form.nombre" name="nombre" maxlength="100" required /></div>
            <div class="form-field"><label>Correo electrónico *</label><input class="form-control" type="email" [(ngModel)]="form.correo" name="correo" maxlength="120" required /></div>
            <div class="form-field"><label>Rol *</label><select class="form-control" [(ngModel)]="form.id_rol" name="id_rol" required>
              <option [ngValue]="1">Administrador</option><option [ngValue]="2">Empleado</option><option [ngValue]="3">Cliente</option>
            </select></div>
            @if (form.id_rol===3) { <div class="alert-banner">El endpoint actual crea la cuenta de usuario. Para pedidos del cliente también será necesario un registro relacionado en la tabla <code>clientes</code>.</div> }
            <div class="form-field"><label>Contraseña {{editandoId?'(dejar vacía para conservarla)':'*'}}</label><input class="form-control" type="password" [(ngModel)]="form.password" name="password" [required]="!editandoId" minlength="8" /></div>
          </div>
          <div class="modal-footer"><button type="button" class="btn btn-outline" (click)="cerrarModal()">Cancelar</button><button class="btn btn-red" type="submit" [disabled]="guardando">{{guardando?'Guardando...':'Guardar usuario'}}</button></div>
        </form>
      </div>
    </div>
  }

```

## `src/app/pages/usuarios/usuarios.ts`

```typescript
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { ApiMensaje, Usuario } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

type FormUsuario = { nombre: string; correo: string; password: string; id_rol: number };

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [FormsModule, Icon],
  templateUrl: './usuarios.html'
})
export class Usuarios implements OnInit {
  private readonly api = inject(ApiService);
  usuarios: Usuario[] = [];
  filtro = '';
  rolSeleccionado = 'Todos';
  readonly filtrosRoles = ['Todos','Administrador','Empleado','Cliente'];
  cargando = false;
  guardando = false;
  mensaje = '';
  error = '';
  errorModal = '';
  modalAbierto = false;
  editandoId: number | null = null;
  form: FormUsuario = this.formVacio();

  ngOnInit(): void { this.cargar(); }
  get usuariosFiltrados(): Usuario[] {
    const texto = this.filtro.toLocaleLowerCase('es-MX').trim();
    return this.usuarios.filter(u => (this.rolSeleccionado === 'Todos' || u.rol === this.rolSeleccionado)
      && (!texto || `${u.nombre} ${u.correo}`.toLocaleLowerCase('es-MX').includes(texto)));
  }
  private formVacio(): FormUsuario { return { nombre:'', correo:'', password:'', id_rol:2 }; }
  cargar(): void {
    this.cargando=true; this.error='';
    this.api.get<Usuario[]>('/usuarios/').subscribe({
      next: r => { this.usuarios=r; this.cargando=false; },
      error: e => { this.error=mensajeError(e); this.cargando=false; }
    });
  }
  abrirCrear(): void { this.editandoId=null; this.form=this.formVacio(); this.errorModal=''; this.modalAbierto=true; }
  abrirEditar(u: Usuario): void { this.editandoId=u.id_usuario; this.form={nombre:u.nombre,correo:u.correo,password:'',id_rol:u.id_rol}; this.errorModal=''; this.modalAbierto=true; }
  cerrarModal(): void { this.modalAbierto=false; }
  guardar(): void {
    this.errorModal='';
    if (!this.form.nombre.trim() || !this.form.correo.includes('@') || (!this.editandoId && this.form.password.length<8)) {
      this.errorModal='Verifica nombre, correo y contraseña (mínimo 8 caracteres).'; return;
    }
    if (this.form.password && this.form.password.length<8) { this.errorModal='La contraseña debe tener al menos 8 caracteres.'; return; }
    const body = {...this.form, nombre: this.form.nombre.trim(), correo: this.form.correo.trim()};
    if (!body.password) delete (body as Partial<FormUsuario>).password;
    this.guardando=true;
    const req = this.editandoId
      ? this.api.put<ApiMensaje>(`/usuarios/${this.editandoId}`, body)
      : this.api.post<ApiMensaje>('/usuarios/', body);
    req.subscribe({
      next: r => { this.guardando=false; this.modalAbierto=false; this.mensaje=r.mensaje; this.cargar(); },
      error: e => { this.guardando=false; this.errorModal=mensajeError(e); }
    });
  }
  cambiarEstado(u: Usuario): void {
    const nuevo = u.estado === 1 ? 0 : 1;
    if (!confirm(`¿${nuevo?'Activar':'Desactivar'} al usuario ${u.nombre}?`)) return;
    this.api.patch<ApiMensaje>(`/usuarios/${u.id_usuario}/estado`, {estado:nuevo}).subscribe({
      next: r => { this.mensaje=r.mensaje; this.cargar(); }, error: e => this.error=mensajeError(e)
    });
  }
}

```

## `src/app/pages/ventas/ventas.html`

```html
<!-- Pantalla lista para que otro integrante desarrolle este módulo. -->
<section class="page-header">
  <div>
    <h1 class="page-title">Ventas</h1>
  </div>
</section>
<div class="panel" style="min-height: 65vh;"></div>

```

## `src/app/pages/ventas/ventas.ts`

```typescript
import { Component } from '@angular/core';

// Módulo reservado para otro integrante del equipo.
// Podrán agregar servicios, formularios y peticiones HTTP aquí.
@Component({
  selector: 'app-ventas',
  standalone: true,
  templateUrl: './ventas.html'
})
export class VentasPendiente {}

```

## `src/app/shared/errors.ts`

```typescript
import { HttpErrorResponse } from '@angular/common/http';

export function mensajeError(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return 'No hay conexión con Flask. Comprueba que esté encendido en el puerto 5000 y que CORS esté configurado.';
    }
    const body = error.error as { mensaje?: string; error?: string } | null;
    return body?.mensaje || `Error HTTP ${error.status}. Revisa la ruta de Flask.`;
  }
  return 'Ocurrió un error inesperado.';
}

```

## `src/app/shared/icon.html`

```html
<svg [attr.width]="size" [attr.height]="size" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"
    stroke-linejoin="round" aria-hidden="true"><path [attr.d]="icons[name] || icons['box']" /></svg>

```

## `src/app/shared/icon.ts`

```typescript
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-icon',
  standalone: true,
  templateUrl: './icon.html'
})
export class Icon {
  @Input() name = 'box';
  @Input() size = 18;
  readonly icons: Record<string,string> = {
    dashboard: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    users: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8a4 4 0 0 0 0 8 M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
    truck: 'M3 7h11v11H3z M14 11h4l3 3v4h-7z M8 21a2 2 0 1 0 0-4a2 2 0 0 0 0 4 M18 21a2 2 0 1 0 0-4a2 2 0 0 0 0 4',
    cart: 'M2 3h2l3 12h12l3-9H5 M9 21a1 1 0 1 0 0-2a1 1 0 0 0 0 2 M18 21a1 1 0 1 0 0-2a1 1 0 0 0 0 2',
    box: 'M3 7l9-4l9 4v10l-9 4l-9-4z M3 7l9 4l9-4 M12 11v10',
    warehouse: 'M3 10l9-7l9 7v11H3z M8 21v-9h8v9 M8 16h8',
    search: 'M11 19a8 8 0 1 0 0-16a8 8 0 0 0 0 16 M21 21l-4.4-4.4',
    bell: 'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9 M10 21h4',
    logout: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4 M16 17l5-5l-5-5 M21 12H9',
    plus: 'M12 5v14 M5 12h14',
    edit: 'M12 20h9 M16 4l4 4l-11 11l-5 1l1-5z',
    trash: 'M3 6h18 M8 6V4h8v2 M6 6l1 15h10l1-15 M10 10v7 M14 10v7',
    check: 'M20 6L9 17l-5-5',
    warning: 'M12 3l10 18H2z M12 9v5 M12 18h.01',
    close: 'M18 6L6 18 M6 6l12 12',
    money: 'M12 2v20 M16 6a5 5 0 0 0-8 0c-3 5 13 3 8 10a5 5 0 0 1-8 0',
    chart: 'M3 3v18h18 M7 15l4-5l4 3l5-8',
    menu: 'M4 6h16 M4 12h16 M4 18h16',
    refresh: 'M20 11a8 8 0 1 0-2 6 M20 4v7h-7',
    calendar: 'M4 5h16v16H4z M4 10h16 M8 3v4 M16 3v4',
    shop: 'M3 9l2-5h14l2 5v3H3z M5 12v9h14v-9 M9 21v-7h6v7',
    clipboard: 'M7 5H4v16h16V5h-3 M9 3h6v4H9z M8 12h8 M8 16h8',
    arrow: 'M5 12h14 M13 6l6 6l-6 6',
    info: 'M12 21a9 9 0 1 0 0-18a9 9 0 0 0 0 18 M12 11v6 M12 7v.01',
    filter: 'M3 5h18 M7 12h10 M10 19h4'
  };
}

```

## `src/index.html`

```html
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Burguer.ING — Sistema Integral de Gestión</title>
  <base href="/">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#171717">
  <link rel="icon" type="image/svg+xml" href="favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body><app-root></app-root></body>
</html>

```

## `src/styles.css`

```css
@import "tailwindcss";
@import "flowbite/src/themes/default";
@plugin "flowbite/plugin";
@source "../node_modules/flowbite";

:root {
  font-family: 'Inter', Arial, sans-serif;
  color: #171717;
  font-synthesis: none;
  background: #f5f5f5;
}
* { box-sizing: border-box; }
body { margin: 0; }
button, input, select, textarea { font: inherit; }
button { cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .55; }
a { text-decoration: none; }
:focus-visible { outline: 3px solid #f99d9f; outline-offset: 2px; }

.heading-font { font-family: 'Poppins', 'Inter', Arial, sans-serif; letter-spacing: -.035em; }
.layout-shell { min-height: 100vh; background: #f5f5f5; }
.sidebar { background: #171717; color: #e9e9e9; width: 274px; position: fixed; left: 0; top: 0; bottom: 0; z-index: 30; display: flex; flex-direction: column; }
.logo-band { border-bottom: 1px solid #313131; padding: 20px 22px; height: 77px; display:flex; align-items:center; gap: 10px; }
.logo-square { width: 38px; height: 38px; background: #e5232a; border-radius: 10px; display:grid; place-items:center; font-size: 23px; font-weight: 900; color: white; }
.logo-name { font-size: 21px; font-weight: 800; letter-spacing: -.045em; color: #fff; }
.logo-ing { color: #ee252d; background: #2a2420; padding: 3px 7px; border: 1px solid #7e391a; border-radius: 6px; font-weight: 900; font-size: 17px; }
.branch-box { margin: 14px 16px 12px; padding: 12px 13px; border: 1px solid #3b3b3b; border-radius: 13px; background: #262626; }
.branch-box small { display: block; color: #a7a7a7; font-weight: 700; font-size: 11px; letter-spacing: .045em; }
.branch-box strong { display: block; font-size: 12px; color: #fff; }
.nav-list { padding: 4px 12px; overflow-y: auto; flex: 1; }
.nav-link { display: flex; align-items: center; gap: 13px; min-height: 45px; padding: 0 16px; color: #ececec; border-radius: 11px; font-weight: 600; font-size: 13px; margin-bottom: 2px; }
.nav-link:hover { background: #2c2c2c; }
.nav-link.active { color: #fff; background: #e42229; box-shadow: 0 6px 15px #e4222936; }
.nav-link .ico { color: #a2a2a2; }
.nav-link.active .ico { color: #fff; }
.sidebar-footer { border-top: 1px solid #303030; padding: 14px 15px 18px; }
.topbar { position: sticky; top: 0; z-index: 15; height: 77px; border-bottom: 1px solid #e1e1e1; background: #fff; display:flex; align-items:center; justify-content:space-between; gap:20px; padding: 0 32px; }
.main-content { margin-left: 274px; min-width: 0; }
.page-space { padding: 32px 34px 60px; }
.page-title { font-family: 'Poppins', Arial, sans-serif; font-weight: 800; font-size: 25px; line-height: 1.3; letter-spacing: -.05em; margin: 0 0 3px; }
.page-subtitle { color: #777d89; font-size: 14px; margin: 0; }
.page-header { display:flex; align-items:center; justify-content:space-between; gap: 16px; margin-bottom: 26px; }
.panel { border: 1px solid #e5e5e5; border-radius: 18px; background: #fff; }
.panel-inner { padding: 19px; }
.panel-title { font-family: 'Poppins', sans-serif; font-weight: 750; letter-spacing: -.025em; font-size: 16px; }
.btn { display: inline-flex; align-items: center; justify-content:center; gap: 7px; border-radius: 11px; font-weight: 700; font-size: 13px; padding: 11px 17px; border: 1px solid transparent; min-height: 41px; white-space: nowrap; }
.btn-red { color: #fff; background: #e5232a; }
.btn-red:hover { background: #c91820; }
.btn-dark { color: #fff; background: #181818; }
.btn-dark:hover { background: #363636; }
.btn-outline { color: #242424; background: #fff; border-color: #dedede; }
.btn-outline:hover { background: #f5f5f5; }
.btn-green { color:#fff; background:#0f9c71; }
.btn-green:hover { background: #0c8560; }
.btn-small { min-height: 32px; padding: 6px 10px; font-size: 12px; border-radius: 8px; }
.btn-link-red { color: #d7252c; font-weight: 650; }
.btn-link-red:hover { text-decoration: underline; }
.form-field { display:flex; flex-direction:column; gap:6px; min-width: 0; }
.form-field label { color: #474747; font-size: 12px; font-weight: 750; }
.form-control { display:block; width:100%; min-height:42px; padding: 10px 12px; border-radius: 11px; border: 1px solid #dbdbdb; outline: none; background:#fff; color:#262626; font-size: 13px; }
.form-control:focus { border-color:#e5232a; box-shadow: 0 0 0 3px #fce3e4; }
textarea.form-control { resize: vertical; }
.search-input { width:100%; max-width:480px; padding: 11px 15px 11px 40px; border: 1px solid #dedede; border-radius: 12px; color:#282828; outline: none; font-size: 13px; }
.search-input:focus { border-color:#e5232a; }
.filter-row { display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
.filter-pill { border:0; border-radius: 25px; background:#f4f4f4; padding: 8px 14px; color:#505050; font-weight: 650; font-size: 12px; }
.filter-pill:hover { background:#e9e9e9; }
.filter-pill.selected { background:#e5232a; color:#fff; }
.data-table-wrap { overflow-x: auto; }
.data-table { width: 100%; border-collapse:collapse; text-align:left; font-size: 13px; }
.data-table th { background:#fafafa; color:#777; text-transform:uppercase; font-size:11px; font-weight:800; letter-spacing:.05em; padding: 17px 17px; white-space:nowrap; border-bottom:1px solid #e8e8e8; }
.data-table td { padding: 17px; color:#343434; border-bottom:1px solid #ededed; vertical-align:middle; }
.data-table tr:last-child td { border-bottom:none; }
.data-table tbody tr:hover { background:#fcfcfc; }
.table-action { border:none; padding:5px 6px; background:transparent; font-size:12px; font-weight:700; color:#444; }
.table-action:hover { color:#df1c26; }
.chip { display:inline-flex; align-items:center; border-radius:999px; padding:5px 11px; font-size:11px; font-weight:750; white-space: nowrap; }
.chip-green { background:#d0fae4; color:#007b54; }
.chip-red { background:#ffe1e3; color:#b10f1e; }
.chip-yellow { background:#fff0c0; color:#a75b00; }
.chip-blue { background:#dce9ff; color:#1748b8; }
.chip-gray { background:#f1f1f1; color:#666; }
.kpi-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:16px; }
.kpi { padding:23px 21px; min-height:150px; }
.kpi-label { color:#989a9e; font-weight:750; font-size:12px; text-transform:uppercase; }
.kpi-number { margin-top:13px; font-size:26px; font-weight:850; letter-spacing:-.05em; }
.kpi-caption { font-size:12px; margin-top:4px; color:#707070; }
.kpi-icon { width:39px; height:39px; border-radius:10px; display:grid; place-items:center; }
.modal-backdrop { position:fixed; inset:0; background:#131313aa; backdrop-filter:blur(2px); z-index:90; display:flex; align-items:center; justify-content:center; padding:20px; }
.modal-panel { background:#fff; border-radius:18px; width:100%; max-width:650px; max-height:91vh; overflow:auto; box-shadow: 0 25px 70px #0004; }
.modal-header { display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding:19px 23px; }
.modal-body { padding:22px 23px; }
.modal-footer { padding:16px 23px; border-top:1px solid #eee; display:flex; justify-content:flex-end; gap:9px; }
.form-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }
.notice { border-radius:10px; padding:11px 15px; font-size:12px; font-weight:600; }
.notice-error { background:#fff0f0; color:#a61e27; border:1px solid #ffcece; }
.notice-ok { background:#e9faf0; color:#086a45; border:1px solid #c6efd9; }
.text-muted { color:#848484; }
.empty-state { padding:55px 20px; text-align:center; color:#8a8a8a; }
.alert-banner { background:#fff8e9; border:1px solid #ffe4a8; border-radius:12px; padding:12px; color:#965800; font-size:12px; }
.metric-green { color:#008c65; } .metric-red { color:#d91c25; } .metric-orange { color:#a95400; }
.actions-inline { display:flex; gap:10px; align-items:center; justify-content:flex-end; }
.loading-line { padding:30px; color:#888; font-size:13px; text-align:center; }

@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .page-space { padding:26px 22px 50px; }
}
@media (max-width: 900px) {
  .sidebar { transform:translateX(-100%); transition:transform .2s ease; }
  .sidebar.is-open { transform:translateX(0); }
  .main-content { margin-left:0; }
  .topbar { padding:0 16px; }
}
@media (max-width: 640px) {
  .page-space { padding:20px 12px 45px; }
  .page-header { align-items:flex-start; flex-direction:column; }
  .page-title { font-size:22px; }
  .kpi-grid { gap:9px; }
  .kpi { min-height:122px; padding:15px 13px; }
  .kpi-number { font-size:22px; }
  .form-grid { grid-template-columns:1fr; }
  .modal-body { padding:15px; }
  .modal-header { padding:15px; }
  .modal-footer { padding:12px; }
}

```
