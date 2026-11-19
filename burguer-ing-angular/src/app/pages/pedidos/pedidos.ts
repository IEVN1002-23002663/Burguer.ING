
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/services/api.service';

import {
  Carrito,
  ClientePedido,
  DireccionPedido,
  PedidoDetalle,
  PedidoResumen,
  Producto
} from '../../core/models/equipo-operaciones.models';

import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

interface DireccionForm {
  calle: string;
  numero: string;
  colonia: string;
  codigo_postal: string;
  referencias: string;
}

@Component({
  selector: 'app-pedidos',
  standalone: true,
  imports: [CommonModule, FormsModule, Icon],
  templateUrl: './pedidos.html'
})
export class PedidosPendiente implements OnInit {

  private readonly api = inject(ApiService);

  // =========================================
  // DATOS DEL MÓDULO
  // =========================================

  tab: 'historial' | 'carrito' = 'historial';

  clientes: ClientePedido[] = [];
  productos: Producto[] = [];
  direcciones: DireccionPedido[] = [];
  todosPedidos: PedidoResumen[] = [];

  carrito: Carrito | null = null;
  detalle: PedidoDetalle | null = null;

  // =========================================
  // SELECCIÓN DE CLIENTE Y PRODUCTO
  // =========================================

  idCliente: number | null = 1;
  idProductoAgregar: number | null = null;
  cantidadAgregar = 1;

  idPedidoBuscar: number | null = null;

  busqueda = '';
  filtroEstado = 'Todos';

  // =========================================
  // DATOS DE ENTREGA
  // =========================================

  // Flask admite "Recoger" y "Domicilio".
  tipoEntrega: 'Recoger' | 'Domicilio' = 'Recoger';

  idDireccion: number | null = null;
  observaciones = '';

  creandoDireccion = false;

  nuevaDireccion: DireccionForm = this.direccionVacia();

  // =========================================
  // ESTADOS DE INTERFAZ
  // =========================================

  cargando = false;
  procesando = false;

  listadoGeneralDisponible = true;

  error = '';
  mensaje = '';

  // =========================================
  // INICIALIZACIÓN
  // =========================================

  ngOnInit(): void {
    this.cargarProductos();
    this.cargarClientes();
    this.cargarTodos();
    this.consultarCliente();
  }

  private direccionVacia(): DireccionForm {
    return {
      calle: '',
      numero: '',
      colonia: '',
      codigo_postal: '',
      referencias: ''
    };
  }

  // =========================================
  // CLIENTE SELECCIONADO
  // =========================================

  get clienteSeleccionado(): ClientePedido | undefined {

    return this.clientes.find(
      c => c.id_cliente === this.idCliente
    );
  }

  // =========================================
  // DESCUENTO ESTIMADO
  // =========================================

  get descuentoEstimado(): number {

    const cliente = this.clienteSeleccionado;

    if (
      !cliente ||
      cliente.estado_acreditacion !== 'Validada'
    ) {
      return 0;
    }

    return Number(this.carrito?.subtotal || 0) *
      Number(cliente.porcentaje_descuento || 0) / 100;
  }

  get totalEstimado(): number {

    return Math.max(
      0,
      Number(this.carrito?.subtotal || 0) -
      this.descuentoEstimado
    );
  }

  // =========================================
  // ESTADOS DISPONIBLES
  // =========================================

  get estados(): string[] {

    return [...new Set(
      this.todosPedidos.map(p => p.estado)
    )].sort();
  }

  // =========================================
  // FILTRO DE PEDIDOS
  // =========================================

  get pedidosFiltrados(): PedidoResumen[] {

    const texto = this.busqueda.toLowerCase().trim();

    return this.todosPedidos.filter(pedido => {

      const coincideEstado =
        this.filtroEstado === 'Todos' ||
        pedido.estado === this.filtroEstado;

      const contenido = `
        ${pedido.id_pedido}
        ${pedido.cliente || ''}
        ${pedido.id_cliente ?? ''}
        ${pedido.tipo_entrega}
      `.toLowerCase();

      const coincideBusqueda =
        !texto || contenido.includes(texto);

      return coincideEstado && coincideBusqueda;
    });
  }

  // =========================================
  // CONSULTAR PRODUCTOS DISPONIBLES
  // =========================================

  cargarProductos(): void {

    this.api.get<Producto[]>(
      '/productos/'
    ).subscribe({

      next: respuesta => {

        this.productos = respuesta.filter(
          producto => Boolean(producto.disponible)
        );
      },

      error: err => {
        this.error = mensajeError(err);
      }

    });
  }

  // =========================================
  // CONSULTAR CLIENTES
  // =========================================

  cargarClientes(): void {

    this.api.get<ClientePedido[]>(
      '/pedidos/clientes'
    ).subscribe({

      next: respuesta => {
        this.clientes = respuesta;
      },

      error: () => {

        // Si todavía no existe la ruta administrativa
        // en Flask, permite seleccionar por ID.

        this.clientes = [];
      }

    });
  }

  // =========================================
  // LISTAR TODOS LOS PEDIDOS
  // =========================================

  cargarTodos(): void {

    this.cargando = true;

    this.api.get<PedidoResumen[]>(
      '/pedidos/'
    ).subscribe({

      next: respuesta => {

        this.todosPedidos = respuesta;

        this.listadoGeneralDisponible = true;
        this.cargando = false;
      },

      error: err => {

        this.listadoGeneralDisponible = false;
        this.cargando = false;

        // El Flask original solo listaba
        // pedidos de un cliente específico.

        if (err.status === 404 || err.status === 405) {

          this.cargarPedidosCliente();

        } else {

          this.error = mensajeError(err);

        }
      }

    });
  }

  // =========================================
  // CAMBIAR CLIENTE
  // =========================================

  consultarCliente(): void {

    this.error = '';
    this.mensaje = '';

    this.carrito = null;
    this.direcciones = [];
    this.idDireccion = null;

    if (
      !this.idCliente ||
      !Number.isInteger(this.idCliente) ||
      this.idCliente < 1
    ) {

      this.error = 'Selecciona un cliente válido.';
      return;
    }

    this.cargarCarrito();
    this.cargarDirecciones();

    if (!this.listadoGeneralDisponible) {
      this.cargarPedidosCliente();
    }
  }

  // =========================================
  // PEDIDOS DE UN CLIENTE
  // =========================================

  cargarPedidosCliente(): void {

    if (!this.idCliente) {
      return;
    }

    this.api.get<PedidoResumen[]>(
      `/pedidos/cliente/${this.idCliente}`
    ).subscribe({

      next: respuesta => {
        this.todosPedidos = respuesta;
      },

      error: err => {
        this.error = mensajeError(err);
      }

    });
  }

  // =========================================
  // CONSULTAR CARRITO
  // =========================================

  cargarCarrito(): void {

    if (!this.idCliente) {
      return;
    }

    this.api.get<Carrito>(
      `/carrito/${this.idCliente}`
    ).subscribe({

      next: respuesta => {
        this.carrito = respuesta;
      },

      error: err => {
        this.error = mensajeError(err);
      }

    });
  }

  // =========================================
  // CONSULTAR DIRECCIONES
  // =========================================

  cargarDirecciones(): void {

    if (!this.idCliente) {
      return;
    }

    this.api.get<DireccionPedido[]>(
      `/direcciones/cliente/${this.idCliente}`
    ).subscribe({

      next: respuesta => {
        this.direcciones = respuesta;
      },

      error: () => {
        this.direcciones = [];
      }

    });
  }

  // =========================================
  // GUARDAR DIRECCIÓN NUEVA
  // =========================================

  guardarDireccion(): void {

    if (
      !this.idCliente ||
      !this.nuevaDireccion.calle.trim() ||
      !this.nuevaDireccion.colonia.trim()
    ) {

      this.error = 'Escribe la calle y la colonia.';
      return;
    }

    this.procesando = true;
    this.error = '';

    this.api.post<{
      mensaje: string;
      id_direccion: number;
    }>(
      `/direcciones/cliente/${this.idCliente}`,
      this.nuevaDireccion
    ).subscribe({

      next: respuesta => {

        this.procesando = false;

        this.mensaje = respuesta.mensaje;
        this.creandoDireccion = false;

        this.nuevaDireccion = this.direccionVacia();
        this.idDireccion = respuesta.id_direccion;

        this.cargarDirecciones();
      },

      error: err => {

        this.procesando = false;
        this.error = mensajeError(err);
      }

    });
  }

  // =========================================
  // AGREGAR PRODUCTO AL CARRITO
  // =========================================

  agregarCarrito(): void {

    if (
      !this.idCliente ||
      !this.idProductoAgregar ||
      !Number.isInteger(this.cantidadAgregar) ||
      this.cantidadAgregar < 1
    ) {

      this.error =
        'Selecciona un producto y una cantidad entera mayor a cero.';

      return;
    }

    this.procesando = true;
    this.error = '';

    this.api.post<{ mensaje: string }>(
      `/carrito/${this.idCliente}/productos`,
      {
        id_producto: this.idProductoAgregar,
        cantidad: this.cantidadAgregar
      }
    ).subscribe({

      next: respuesta => {

        this.procesando = false;
        this.mensaje = respuesta.mensaje;

        this.cargarCarrito();
      },

      error: err => {

        this.procesando = false;
        this.error = mensajeError(err);
      }

    });
  }

  // =========================================
  // CAMBIAR CANTIDAD DEL CARRITO
  // =========================================

  cambiarCantidad(
    idProducto: number,
    cantidad: number
  ): void {

    if (
      !this.idCliente ||
      !Number.isInteger(cantidad) ||
      cantidad < 1
    ) {

      this.error =
        'La cantidad debe ser un entero mayor a cero.';

      return;
    }

    this.procesando = true;

    this.api.put<{ mensaje: string }>(
      `/carrito/${this.idCliente}/productos/${idProducto}`,
      { cantidad }
    ).subscribe({

      next: respuesta => {

        this.procesando = false;
        this.mensaje = respuesta.mensaje;

        this.cargarCarrito();
      },

      error: err => {

        this.procesando = false;
        this.error = mensajeError(err);

        this.cargarCarrito();
      }

    });
  }

  // =========================================
  // QUITAR PRODUCTO DEL CARRITO
  // =========================================

  quitarProducto(idProducto: number): void {

    if (!this.idCliente) {
      return;
    }

    this.procesando = true;

    this.api.delete<{ mensaje: string }>(
      `/carrito/${this.idCliente}/productos/${idProducto}`
    ).subscribe({

      next: respuesta => {

        this.procesando = false;
        this.mensaje = respuesta.mensaje;

        this.cargarCarrito();
      },

      error: err => {

        this.procesando = false;
        this.error = mensajeError(err);
      }

    });
  }

  // =========================================
  // CONFIRMAR PEDIDO
  // =========================================

  confirmarPedido(): void {

    if (
      !this.idCliente ||
      !this.carrito?.productos.length
    ) {

      this.error =
        'Agrega al menos un producto al carrito.';

      return;
    }

    if (
      this.tipoEntrega === 'Domicilio' &&
      !this.idDireccion
    ) {

      this.error =
        'Selecciona o registra una dirección del cliente.';

      return;
    }

    const confirmado = confirm(
      '¿Confirmar este pedido y guardarlo en MySQL?'
    );

    if (!confirmado) {
      return;
    }

    this.procesando = true;
    this.error = '';

    this.api.post<{
      mensaje: string;
      id_pedido: number;
      total: number;
    }>(
      `/pedidos/confirmar/${this.idCliente}`,
      {
        tipo_entrega: this.tipoEntrega,

        id_direccion:
          this.tipoEntrega === 'Domicilio'
            ? this.idDireccion
            : null,

        observaciones: this.observaciones.trim()
      }
    ).subscribe({

      next: respuesta => {

        this.procesando = false;

        this.mensaje =
          `${respuesta.mensaje} ` +
          `Folio #${respuesta.id_pedido}. ` +
          `Total: $${Number(respuesta.total).toFixed(2)}`;

        this.observaciones = '';
        this.tab = 'historial';

        this.cargarCarrito();
        this.cargarTodos();

        this.verPedido(respuesta.id_pedido);
      },

      error: err => {

        this.procesando = false;
        this.error = mensajeError(err);
      }

    });
  }

  // =========================================
  // VER DETALLE DE PEDIDO
  // =========================================

  verPedido(idPedido: number): void {

    this.error = '';

    this.api.get<PedidoDetalle>(
      `/pedidos/${idPedido}`
    ).subscribe({

      next: respuesta => {
        this.detalle = respuesta;
      },

      error: err => {
        this.error = mensajeError(err);
      }

    });
  }

  // =========================================
  // BUSCAR PEDIDO POR FOLIO
  // =========================================

  buscarPedido(): void {

    if (
      !this.idPedidoBuscar ||
      this.idPedidoBuscar < 1
    ) {

      this.error = 'Escribe un folio válido.';
      return;
    }

    this.verPedido(this.idPedidoBuscar);
  }

  // =========================================
  // ACTUALIZAR MÓDULO
  // =========================================

  actualizar(): void {

    this.error = '';

    this.cargarTodos();
    this.cargarCarrito();
    this.cargarProductos();
  }
}
