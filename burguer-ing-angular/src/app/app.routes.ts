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
