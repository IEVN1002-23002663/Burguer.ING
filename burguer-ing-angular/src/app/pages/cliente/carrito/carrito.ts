import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';
import { CarritoService, ItemCarrito } from '../../../core/services/carrito.service';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-carrito',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './carrito.html'
})
export class Carrito {

  items: ItemCarrito[] = [];

  cedula = '';
  cedulaValidada = false;
  descuentoAplicado = false;

  mensajeCedula = '';
  mensajePedido = '';
  cargandoPedido = false;

  constructor(
    private carritoService: CarritoService,
    private api: ApiService,
    private auth: AuthService,
    private router: Router
  ) {
    this.carritoService.carrito$.subscribe(items => {
      this.items = items;
    });
  }

  aumentar(id: number): void {
    this.carritoService.aumentar(id);
    this.mensajePedido = '';
  }

  disminuir(id: number): void {
    this.carritoService.disminuir(id);
    this.mensajePedido = '';
  }

  eliminar(id: number): void {
    this.carritoService.eliminar(id);
    this.mensajePedido = '';
  }

  vaciar(): void {
    this.carritoService.vaciar();
    this.mensajePedido = '';
    this.descuentoAplicado = false;
    this.cedulaValidada = false;
    this.cedula = '';
    this.mensajeCedula = '';
  }

  get subtotal(): number {
    return this.carritoService.subtotal;
  }

  get cantidadTotal(): number {
    return this.carritoService.cantidadTotal;
  }

  get descuento(): number {
    return this.descuentoAplicado ? this.subtotal * 0.15 : 0;
  }

  get total(): number {
    return this.subtotal - this.descuento;
  }

  validarCedula(): void {
    this.mensajeCedula = '';
    this.cedulaValidada = false;
    this.descuentoAplicado = false;

    const valor = this.cedula.trim();

    if (!valor) {
      this.mensajeCedula =
        'Ingresa tu Cédula Profesional o Título de Ingeniería.';
      return;
    }

    if (valor.length < 5) {
      this.mensajeCedula = 'Ingresa un número de cédula válido.';
      return;
    }

    // Validación provisional únicamente visual.
    // Flask/MySQL realizará el cálculo definitivo.

    this.cedulaValidada = true;
    this.descuentoAplicado = true;

    this.mensajeCedula =
      'Validación provisional exitosa. Descuento visual del 15%.';
  }

  confirmarPedido(): void {

    this.mensajePedido = '';

    if (this.items.length === 0) {
      this.mensajePedido = 'Tu carrito está vacío.';
      return;
    }

    const usuario = this.auth.usuario();

    if (!usuario || !usuario.id_cliente) {
      this.router.navigate(['/login'], {
        queryParams: {
          returnUrl: '/carrito'
        }
      });

      return;
    }

    // En lugar de crear el pedido inmediatamente,
    // ahora dirigimos al usuario al checkout.

    this.router.navigate(['/checkout']);
  }
}
