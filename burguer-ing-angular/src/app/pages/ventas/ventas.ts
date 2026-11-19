
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

import {
  PagosPedido,
  Venta
} from '../../core/models/equipo-operaciones.models';

import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

type MetodoPago = 'Efectivo' | 'Tarjeta' | 'Transferencia';

interface RespuestaPago {
  mensaje: string;
  id_pago: number;
  id_pedido: number;
  monto_pagado: number;
  total_pagado: number;
  saldo_pendiente: number;
  pedido_pagado: boolean;
  venta_creada: boolean;
  id_venta: number | null;
}

@Component({
  selector: 'app-ventas',
  standalone: true,
  imports: [CommonModule, FormsModule, Icon],
  templateUrl: './ventas.html'
})
export class VentasPendiente implements OnInit {

  private readonly api = inject(ApiService);

  readonly auth = inject(AuthService);

  // ======================================
  // DATOS
  // ======================================

  ventas: Venta[] = [];

  detalle: Venta | null = null;

  pagosPedido: PagosPedido | null = null;

  busqueda = '';

  idPedidoPago: number | null = null;

  metodoPago: MetodoPago = 'Efectivo';

  montoPago: number | null = null;

  referencia = '';

  // ======================================
  // ESTADOS
  // ======================================

  cargando = false;
  consultando = false;
  procesando = false;

  error = '';
  mensaje = '';

  ngOnInit(): void {
    this.cargarVentas();
  }

  // ======================================
  // BUSCAR VENTAS
  // ======================================

  get ventasFiltradas(): Venta[] {

    const texto = this.busqueda.trim().toLowerCase();

    return this.ventas.filter(venta => {

      const informacion = [
        venta.id_venta,
        venta.id_pedido,
        venta.usuario || '',
        venta.tipo_entrega,
        venta.fecha_venta
      ].join(' ').toLowerCase();

      return !texto || informacion.includes(texto);

    });
  }

  // ======================================
  // INGRESOS
  // ======================================

  get ingresos(): number {

    return this.ventas.reduce(
      (total, venta) =>
        total + Number(venta.total || 0),
      0
    );
  }

  // ======================================
  // DESCUENTOS
  // ======================================

  get descuentos(): number {

    return this.ventas.reduce(
      (total, venta) =>
        total + Number(venta.descuento || 0),
      0
    );
  }

  // ======================================
  // TICKET PROMEDIO
  // ======================================

  get ticketPromedio(): number {

    return this.ventas.length
      ? this.ingresos / this.ventas.length
      : 0;
  }

  get saldoPendiente(): number {

    return Math.max(
      0,
      Number(this.pagosPedido?.saldo_pendiente || 0)
    );
  }

  // ======================================
  // CONSULTAR TODAS LAS VENTAS
  // ======================================

  cargarVentas(): void {

    this.cargando = true;
    this.error = '';

    this.api.get<Venta[]>(
      '/ventas/'
    ).subscribe({

      next: respuesta => {

        this.ventas = respuesta;
        this.cargando = false;

      },

      error: err => {

        this.error = mensajeError(err);
        this.cargando = false;

      }

    });
  }

  // ======================================
  // CAMBIAR PEDIDO SELECCIONADO
  // ======================================

  cambioPedido(): void {

    this.pagosPedido = null;
    this.montoPago = null;
    this.error = '';

  }

  // ======================================
  // CONSULTAR SALDO DE UN PEDIDO
  // ======================================

  consultarSaldo(): void {

    this.error = '';
    this.mensaje = '';
    this.pagosPedido = null;

    if (
      !this.idPedidoPago ||
      !Number.isInteger(this.idPedidoPago) ||
      this.idPedidoPago < 1
    ) {

      this.error =
        'Escribe un número de pedido válido.';

      return;
    }

    this.consultando = true;

    this.api.get<PagosPedido>(

      `/pagos/pedido/${this.idPedidoPago}`

    ).subscribe({

      next: respuesta => {

        this.pagosPedido = respuesta;

        this.montoPago = Math.max(
          0,
          Number(respuesta.saldo_pendiente)
        );

        this.consultando = false;

      },

      error: err => {

        this.error = mensajeError(err);
        this.consultando = false;

      }

    });
  }

  // ======================================
  // REGISTRAR PAGO SIMULADO
  // ======================================

  registrarPago(): void {

    this.error = '';
    this.mensaje = '';

    if (
      !this.idPedidoPago ||
      !this.pagosPedido ||
      Number(this.pagosPedido.id_pedido) !==
        Number(this.idPedidoPago)
    ) {

      this.error =
        'Primero consulta el saldo del pedido que deseas cobrar.';

      return;
    }

    const monto = Number(this.montoPago);

    const saldo = this.saldoPendiente;

    if (!Number.isFinite(monto) || monto <= 0) {

      this.error =
        'El monto del pago debe ser mayor a cero.';

      return;
    }

    if (
      Math.round(monto * 100) >
      Math.round(saldo * 100)
    ) {

      this.error =
        'El monto no puede superar el saldo pendiente.';

      return;
    }

    const confirmado = confirm(

      `¿Registrar pago SIMULADO de $${monto.toFixed(2)} ` +
      `al pedido #${this.idPedidoPago}?`

    );

    if (!confirmado) {
      return;
    }

    this.procesando = true;

    this.api.post<RespuestaPago>(
      '/pagos/',
      {

        id_pedido: this.idPedidoPago,

        metodo_pago: this.metodoPago,

        monto: Number(monto.toFixed(2)),

        referencia:
          this.referencia.trim() || null,

        id_usuario:
          this.auth.usuario()?.id_usuario ?? null

      }
    ).subscribe({

      next: respuesta => {

        this.procesando = false;

        this.referencia = '';

        if (respuesta.venta_creada) {

          this.mensaje =
            `${respuesta.mensaje} ` +
            `Se generó la venta #${respuesta.id_venta}.`;

        } else {

          this.mensaje =
            `${respuesta.mensaje} ` +
            `Saldo pendiente: ` +
            `$${respuesta.saldo_pendiente.toFixed(2)}.`;

        }

        // Consultar nuevamente los pagos
        this.actualizarSaldoTrasPago();

        // Actualizar historial de ventas
        this.cargarVentas();

      },

      error: err => {

        this.procesando = false;
        this.error = mensajeError(err);

      }

    });
  }

  // ======================================
  // ACTUALIZAR SALDO DESPUÉS DEL PAGO
  // ======================================

  private actualizarSaldoTrasPago(): void {

    if (!this.idPedidoPago) {
      return;
    }

    this.api.get<PagosPedido>(

      `/pagos/pedido/${this.idPedidoPago}`

    ).subscribe({

      next: respuesta => {

        this.pagosPedido = respuesta;

        this.montoPago = Math.max(
          0,
          Number(respuesta.saldo_pendiente)
        );

      },

      error: err => {

        this.error = mensajeError(err);

      }

    });
  }

  // ======================================
  // VER DETALLE DE UNA VENTA
  // ======================================

  verVenta(idVenta: number): void {

    this.detalle = null;
    this.error = '';

    this.api.get<Venta>(

      `/ventas/${idVenta}`

    ).subscribe({

      next: respuesta => {

        this.detalle = respuesta;

      },

      error: err => {

        this.error = mensajeError(err);

      }

    });
  }
}
