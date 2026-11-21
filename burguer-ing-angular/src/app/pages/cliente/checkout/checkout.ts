
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router } from '@angular/router';

import { CarritoService } from '../../../core/services/carrito.service';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';

interface PerfilCheckout {
  nombre: string;
  telefono: string | number | null;
}

interface DireccionCheckout {
  id_direccion: number;
  calle: string;
  numero: string;
  colonia: string;
  codigo_postal: string;
  referencias: string | null;
}

interface RespuestaDirecciones {
  direcciones?: DireccionCheckout[];
}

interface RespuestaPedido {
  id_pedido: number;
  total: number;
  mensaje?: string;
}

@Component({
  selector: 'app-checkout',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './checkout.html'
})
export class Checkout implements OnInit {

  // ==========================================
  // CONFIGURACIÓN
  // ==========================================

  readonly COSTO_ENVIO = 50;

  // ==========================================
  // DATOS DEL CLIENTE
  // ==========================================

  nombre = '';
  telefono = '';

  cargandoPerfil = false;
  mensajePerfil = '';

  // ==========================================
  // DIRECCIONES GUARDADAS
  // ==========================================

  direcciones: DireccionCheckout[] = [];

  idDireccionSeleccionada: number | null = null;

  cargandoDirecciones = false;
  mensajeDirecciones = '';

  // ==========================================
  // TIPO DE ENTREGA
  // ==========================================

  tipoEntrega: 'Recoger' | 'Domicilio' = 'Recoger';

  // ==========================================
  // DATOS DE PAGO DE DEMOSTRACIÓN
  // ==========================================

  titularTarjeta = '';
  numeroTarjeta = '';
  expiracion = '';
  cvv = '';

  // ==========================================
  // ESTADO DEL PEDIDO
  // ==========================================

  procesando = false;
  mensaje = '';

  pagoAprobado = false;
  pedidoConfirmado = false;

  numeroPedido: number | null = null;
  totalPedido = 0;
  cantidadTotal = 0;

  constructor(
    public carritoService: CarritoService,
    private api: ApiService,
    private auth: AuthService,
    private router: Router
  ) {

    this.carritoService.carrito$.subscribe(items => {

      this.cantidadTotal = items.reduce(
        (total, item) => total + item.cantidad,
        0
      );

    });

  }

  // ==========================================
  // INICIALIZACIÓN
  // ==========================================

  ngOnInit(): void {

    const usuario = this.auth.usuario();

    if (!usuario || usuario.id_cliente == null) {

      this.router.navigate(['/login'], {
        queryParams: {
          returnUrl: '/checkout'
        }
      });

      return;
    }

    // Nombre inicial desde la sesión.
    this.nombre = usuario.nombre || '';

    // Cargar información del cliente.
    this.cargarPerfil(usuario.id_cliente);

    // Cargar direcciones guardadas.
    this.cargarDirecciones(usuario.id_cliente);

  }

  // ==========================================
  // SUBTOTAL
  // ==========================================

  get subtotal(): number {

    return this.carritoService.subtotal;

  }

  // ==========================================
  // COSTO DE ENTREGA
  // ==========================================

  get costoEntrega(): number {

    return this.tipoEntrega === 'Domicilio'
      ? this.COSTO_ENVIO
      : 0;

  }

  // ==========================================
  // TOTAL DEL PEDIDO
  // ==========================================

  get total(): number {

    return Number(
      (this.subtotal + this.costoEntrega).toFixed(2)
    );

  }

  // ==========================================
  // DIRECCIÓN CONFIRMADA
  // ==========================================

  get direccionConfirmada(): DireccionCheckout | null {

    if (
      this.tipoEntrega !== 'Domicilio' ||
      this.idDireccionSeleccionada === null
    ) {
      return null;
    }

    return this.direcciones.find(
      direccion =>
        Number(direccion.id_direccion) ===
        Number(this.idDireccionSeleccionada)
    ) ?? null;

  }

  // ==========================================
  // CARGAR PERFIL
  // ==========================================

  cargarPerfil(idCliente: number): void {

    this.cargandoPerfil = true;
    this.mensajePerfil = '';

    this.api.get<PerfilCheckout>(
      `/usuarios/cliente/${idCliente}/perfil`
    ).subscribe({

      next: (perfil) => {

        this.nombre = perfil.nombre || this.nombre;

        this.telefono = String(
          perfil.telefono ?? ''
        );

        this.cargandoPerfil = false;

      },

      error: (error) => {

        this.cargandoPerfil = false;

        this.mensajePerfil =
          error?.error?.mensaje ||
          'No se pudieron cargar tus datos personales.';

      }

    });

  }

  // ==========================================
  // CARGAR DIRECCIONES
  // ==========================================

  cargarDirecciones(idCliente: number): void {

    this.cargandoDirecciones = true;
    this.mensajeDirecciones = '';

    this.api.get<DireccionCheckout[] | RespuestaDirecciones>(
      `/usuarios/cliente/${idCliente}/direcciones`
    ).subscribe({

      next: (respuesta) => {

        if (Array.isArray(respuesta)) {

          this.direcciones = respuesta;

        } else {

          this.direcciones = respuesta.direcciones || [];

        }

        // Seleccionar automáticamente si solo hay una dirección.
        if (this.direcciones.length === 1) {

          this.idDireccionSeleccionada =
            this.direcciones[0].id_direccion;

        }

        this.cargandoDirecciones = false;

      },

      error: (error) => {

        this.cargandoDirecciones = false;

        this.mensajeDirecciones =
          error?.error?.mensaje ||
          'No se pudieron cargar tus direcciones guardadas.';

      }

    });

  }

  // ==========================================
  // SELECCIONAR DIRECCIÓN
  // ==========================================

  seleccionarDireccion(idDireccion: number): void {

    this.idDireccionSeleccionada = idDireccion;
    this.mensaje = '';

  }

  // ==========================================
  // PAGAR Y CONFIRMAR
  // ==========================================

  pagar(): void {

    this.mensaje = '';

    if (this.procesando) {
      return;
    }

    const usuario = this.auth.usuario();

    if (!usuario || usuario.id_cliente == null) {

      this.router.navigate(['/login'], {
        queryParams: {
          returnUrl: '/checkout'
        }
      });

      return;
    }

    const idCliente = usuario.id_cliente;

    // Validar carrito.
    if (this.cantidadTotal === 0) {

      this.mensaje = 'Tu carrito está vacío.';
      return;

    }

    // Validar carga del perfil.
    if (this.cargandoPerfil) {

      this.mensaje =
        'Espera a que se carguen tus datos personales.';

      return;

    }

    if (!this.nombre.trim() || !this.telefono.trim()) {

      this.mensaje =
        'No se encontraron tus datos personales. Revisa tu perfil.';

      return;

    }

    // Validar direcciones.
    if (this.tipoEntrega === 'Domicilio') {

      if (this.cargandoDirecciones) {

        this.mensaje =
          'Espera a que se carguen tus direcciones.';

        return;

      }

      if (this.direcciones.length === 0) {

        this.mensaje =
          'Primero registra una dirección desde Mi Perfil.';

        return;

      }

      if (this.idDireccionSeleccionada == null) {

        this.mensaje =
          'Selecciona una dirección de entrega.';

        return;

      }

      const direccionValida = this.direcciones.some(
        direccion =>
          Number(direccion.id_direccion) ===
          Number(this.idDireccionSeleccionada)
      );

      if (!direccionValida) {

        this.mensaje =
          'La dirección seleccionada ya no está disponible.';

        return;

      }

    }

    // Validar datos de pago de demostración.
    if (
      !this.titularTarjeta.trim() ||
      this.numeroTarjeta.replace(/\s/g, '').length < 16 ||
      !this.expiracion.trim() ||
      this.cvv.length < 3
    ) {

      this.mensaje =
        'Verifica los datos de tu tarjeta.';

      return;

    }

    this.procesando = true;

    // Simulación de pago.
    // No se realiza ningún cobro bancario real.
    setTimeout(() => {

      const aprobado = Math.random() < 0.85;

      if (!aprobado) {

        this.procesando = false;

        this.mensaje =
          'El pago fue rechazado. Intenta nuevamente con otra tarjeta.';

        return;

      }

      this.confirmarPedidoBackend(idCliente);

    }, 1500);

  }

  // ==========================================
  // CONFIRMAR PEDIDO EN FLASK
  // ==========================================

  private confirmarPedidoBackend(idCliente: number): void {

    const datosPedido = {

      tipo_entrega: this.tipoEntrega,

      id_direccion:
        this.tipoEntrega === 'Domicilio'
          ? this.idDireccionSeleccionada
          : null,

      observaciones: 'Pago simulado con tarjeta'

    };

    this.api.post<RespuestaPedido>(
      `/pedidos/confirmar/${idCliente}`,
      datosPedido
    ).subscribe({

      next: (respuesta) => {

        this.procesando = false;

        this.pagoAprobado = true;
        this.pedidoConfirmado = true;

        this.numeroPedido = respuesta.id_pedido;

        // Utilizar el total definitivo del backend.
        this.totalPedido = Number(
          respuesta.total ?? this.total
        );

        // Vaciar carrito después de confirmar el pedido.
        this.carritoService.vaciar();

      },

      error: (error) => {

        this.procesando = false;

        this.mensaje =
          error?.error?.mensaje ||
          error?.error?.message ||
          'No se pudo confirmar el pedido. Intenta nuevamente.';

      }

    });

  }

  // ==========================================
  // VOLVER AL CARRITO
  // ==========================================

  volverAlCarrito(): void {

    this.router.navigate(['/carrito']);

  }

}
