import { Component } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { CarritoService } from '../core/services/carrito.service';
import { AuthService } from '../core/services/auth.service';

@Component({
  selector: 'app-layout-cliente',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './layout-cliente.html'
})
export class LayoutCliente {

  menuMovilAbierto = false;
  carritoCantidad = 0;

  constructor(
    private carritoService: CarritoService,
    public auth: AuthService,
    private router: Router
  ) {
    this.carritoService.carrito$.subscribe(items => {
      this.carritoCantidad = items.reduce(
        (total, item) => total + item.cantidad,
        0
      );
    });
  }

  alternarMenu(): void {
    this.menuMovilAbierto = !this.menuMovilAbierto;
  }

  cerrarMenu(): void {
    this.menuMovilAbierto = false;
  }

  cerrarSesion(): void {
    this.auth.cerrar();
    this.cerrarMenu();
    void this.router.navigateByUrl('/inicio');
  }
}