import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';
import { Subscription } from 'rxjs';

import {
  CarritoService,
  ItemCarrito
} from '../../../core/services/carrito.service';

import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-carrito',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './carrito.html'
})
export class Carrito implements OnDestroy {

  items: ItemCarrito[] = [];

  cedula = '';
  cedulaValidada = false;
  descuentoAplicado = false;

  mensajeCedula = '';
  mensajePedido = '';

  cargandoPedido = false;
  cargandoAcreditacion = true;

  private carritoSubscription?: Subscription;
  private acreditacionSubscription?: Subscription;

  constructor(
    private carritoService: CarritoService,
    private api: ApiService,
    private auth: AuthService,
    private router: Router
  ) {
    this.carritoSubscription =
      this.carritoService.carrito$.subscribe(items => {
        this.items = items;
      });

    this.consultarAcreditacion();
  }

  ngOnDestroy(): void {
    this.carritoSubscription?.unsubscribe();
    this.acreditacionSubscription?.unsubscribe();
  }

  // ==========================================
  // CONSULTAR ACREDITACIÓN DEL CLIENTE
  // ==========================================

  consultarAcreditacion(): void {

    const usuario = this.auth.usuario();

    if (!usuario?.id_cliente) {
      this.descuentoAplicado = false;
      this.cargandoAcreditacion = false;
      return;
    }

    this.cargandoAcreditacion = true;

    this.acreditacionSubscription?.unsubscribe();

    this.acreditacionSubscription = this.api
      .get<any>(`/carrito/${usuario.id_cliente}`)
      .subscribe({

        next: (respuesta) => {

          this.descuentoAplicado =
            respuesta?.cedula_aprobada === true;

          this.cedulaValidada = this.descuentoAplicado;

          if (this.descuentoAplicado) {
            this.mensajeCedula =
              'Tu cédula ya fue aprobada. Tienes activo tu descuento del 15%.';
          } else {
            this.mensajeCedula =
              'Tu acreditación todavía no está aprobada. Consulta su estado en Mi Perfil.';
          }

          this.cargandoAcreditacion = false;
        },

        error: (error) => {

          console.error(
            'Error al consultar la acreditación:',
            error
          );

          this.descuentoAplicado = false;
          this.cedulaValidada = false;

          this.mensajeCedula =
            'No se pudo consultar tu acreditación. Intenta actualizar la página.';

          this.cargandoAcreditacion = false;
        }

      });
  }

  // ==========================================
  // CANTIDADES Y PRODUCTOS
  // ==========================================

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

    // No se elimina la acreditación del cliente.
    // La aprobación permanece guardada en la base de datos.
  }

  // ==========================================
  // TOTALES
  // ==========================================

  get subtotal(): number {
    return this.carritoService.subtotal;
  }

  get cantidadTotal(): number {
    return this.carritoService.cantidadTotal;
  }

  get descuento(): number {

    if (!this.descuentoAplicado) {
      return 0;
    }

    return Math.round(
      (this.subtotal * 0.15 + Number.EPSILON) * 100
    ) / 100;
  }

  get total(): number {
    return Math.max(0, this.subtotal - this.descuento);
  }

  // ==========================================
  // CONFIRMAR PEDIDO
  // ==========================================

  confirmarPedido(): void {

    this.mensajePedido = '';

    if (this.items.length === 0) {
      this.mensajePedido = 'Tu carrito está vacío.';
      return;
    }

    const usuario = this.auth.usuario();

    if (!usuario?.id_cliente) {

      this.router.navigate(['/login'], {
        queryParams: {
          returnUrl: '/carrito'
        }
      });

      return;
    }

    // Flask vuelve a comprobar la acreditación
    // y calcula el descuento definitivo al crear el pedido.

    this.router.navigate(['/checkout']);
  }

}