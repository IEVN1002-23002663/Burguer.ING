
import { Routes } from '@angular/router';
import { authGuard, rolGuard } from './core/guards/auth.guard';

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

import { LayoutCliente } from './layout-cliente/layout-cliente';
import { Inicio } from './pages/cliente/inicio/inicio';
import { MisPedidos } from './pages/cliente/mis-pedidos/mis-pedidos';
import { MiPerfil } from './pages/cliente/mi-perfil/mi-perfil';
import { Carrito } from './pages/cliente/carrito/carrito';
import { Checkout } from './pages/cliente/checkout/checkout';
import { Registro } from './pages/registro/registro';

export const routes: Routes = [

  // LOGIN Y REGISTRO
  { path: 'login', component: Login },
  { path: 'registro', component: Registro },

  // ======================================
  // PANEL ADMINISTRATIVO
  // ======================================
  {
    path: 'admin',
    component: Shell,
    canActivate: [authGuard, rolGuard(['Administrador'])],
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

  // ======================================
  // PANEL DE EMPLEADOS
  // ======================================
  {
    path: 'empleado',
    component: Shell,
    canActivate: [authGuard, rolGuard(['Empleado'])],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'pedidos' },
      { path: 'materias-primas', component: MateriasPrimas },
      { path: 'inventario', component: Inventario },
      { path: 'productos', component: ProductosPendiente },
      { path: 'pedidos', component: PedidosPendiente }
    ]
  },

  // ======================================
  // REDIRECCIONES ADMINISTRATIVAS ANTIGUAS
  // ======================================
  { path: 'dashboard', redirectTo: 'admin/dashboard', pathMatch: 'full' },
  { path: 'usuarios', redirectTo: 'admin/usuarios', pathMatch: 'full' },
  { path: 'proveedores', redirectTo: 'admin/proveedores', pathMatch: 'full' },
  { path: 'compras', redirectTo: 'admin/compras', pathMatch: 'full' },
  { path: 'materias-primas', redirectTo: 'admin/materias-primas', pathMatch: 'full' },
  { path: 'inventario', redirectTo: 'admin/inventario', pathMatch: 'full' },
  { path: 'productos', redirectTo: 'admin/productos', pathMatch: 'full' },
  { path: 'recetas-produccion', redirectTo: 'admin/recetas-produccion', pathMatch: 'full' },
  { path: 'pedidos', redirectTo: 'admin/pedidos', pathMatch: 'full' },
  { path: 'ventas', redirectTo: 'admin/ventas', pathMatch: 'full' },
  { path: 'gastos-finanzas', redirectTo: 'admin/gastos-finanzas', pathMatch: 'full' },

  // ======================================
  // PÁGINAS PÚBLICAS DEL CLIENTE
  // ======================================
  {
    path: '',
    component: LayoutCliente,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'inicio' },

      { path: 'inicio', component: Inicio },

      {
        path: 'menu',
        loadComponent: () =>
          import('./pages/cliente/menu/menu')
            .then(m => m.MenuCliente)
      },

      { path: 'mis-pedidos', component: MisPedidos },
      { path: 'mi-perfil', component: MiPerfil },
      { path: 'carrito', component: Carrito },
      { path: 'checkout', component: Checkout }
    ]
  },

  // RUTA NO ENCONTRADA
  { path: '**', redirectTo: 'inicio' }

];
