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
  { ruta: '/admin/dashboard', titulo: 'Dashboard', icono: 'dashboard' },
  { ruta: '/admin/usuarios', titulo: 'Usuarios', icono: 'users' },
  { ruta: '/admin/proveedores', titulo: 'Proveedores', icono: 'truck' },
  { ruta: '/admin/compras', titulo: 'Compras', icono: 'cart' },
  { ruta: '/admin/materias-primas', titulo: 'Materias primas', icono: 'box' },
  { ruta: '/admin/inventario', titulo: 'Inventario', icono: 'warehouse' },
  { ruta: '/admin/productos', titulo: 'Productos', icono: 'shop' },
  { ruta: '/admin/recetas-produccion', titulo: 'Recetas y producción', icono: 'clipboard' },
  { ruta: '/admin/pedidos', titulo: 'Pedidos', icono: 'cart' },
  { ruta: '/admin/ventas', titulo: 'Ventas', icono: 'chart' },
  { ruta: '/admin/gastos-finanzas', titulo: 'Gastos y finanzas', icono: 'money' }
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
