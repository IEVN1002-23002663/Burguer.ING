
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';

interface Pedido {
  id: number;
  fecha: string;
  productos: string[];
  total: number;
  estado: 'Pendiente' | 'En preparación' | 'Listo para recoger' | 'Entregado';
  tipoEntrega: string;
}

@Component({
  selector: 'app-mis-pedidos',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mis-pedidos.html'
})
export class MisPedidos {

  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);

  pedidos: Pedido[] = [];
  cargando = true;
  error = '';

  filtroEstado = 'Todos';

  estados = [
    'Todos',
    'Pendiente',
    'En preparación',
    'Listo para recoger',
    'Entregado'
  ];

  constructor() {
    this.cargarPedidos();
  }

  cargarPedidos(): void {
    this.cargando = true;
    this.error = '';

    const usuario = this.auth.usuario();

    if (!usuario?.id_cliente) {
      this.error = 'No se encontró el identificador de tu cuenta de cliente.';
      this.cargando = false;
      return;
    }

    this.api.get<any>(`/pedidos/cliente/${usuario.id_cliente}`).subscribe({
      next: (respuesta) => {
        console.log('Respuesta de pedidos:', respuesta);

        const lista = Array.isArray(respuesta)
          ? respuesta
          : respuesta?.pedidos ??
            respuesta?.data ??
            respuesta?.resultado ??
            [];

        this.pedidos = lista.map((pedido: any) =>
          this.mapearPedido(pedido)
        );

        this.cargando = false;
      },

      error: (error) => {
        console.error('Error al cargar pedidos:', error);
        this.error = 'No se pudieron cargar tus pedidos.';
        this.cargando = false;
      }
    });
  }

  private mapearPedido(pedido: any): Pedido {

    const productosOrigen =
      pedido.productos ??
      pedido.detalles ??
      pedido.detalle_pedidos ??
      pedido.detallePedido ??
      pedido.items ??
      pedido.productos_pedido ??
      [];

    const productos: string[] = Array.isArray(productosOrigen)
      ? productosOrigen.map((producto: any) => {

          if (typeof producto === 'string') {
            return producto;
          }

          const nombre =
            producto.nombre_producto ??
            producto.nombre ??
            producto.producto ??
            producto.descripcion ??
            'Producto';

          const cantidad = Number(producto.cantidad ?? 1);

          return `${nombre} x${cantidad}`;
        })
      : [];

    return {
      id: Number(
        pedido.id_pedido ??
        pedido.id ??
        pedido.numero_pedido ??
        0
      ),

      fecha: this.formatearFecha(
        pedido.fecha_pedido ??
        pedido.fecha ??
        pedido.created_at
      ),

      productos,

      total: Number(
        pedido.total ??
        pedido.total_pedido ??
        pedido.monto_total ??
        0
      ),

      estado: this.normalizarEstado(
        pedido.estado ??
        pedido.estado_pedido ??
        ''
      ),

      tipoEntrega: this.normalizarEntrega(
        pedido.tipo_entrega ??
        pedido.tipoEntrega ??
        pedido.modalidad_entrega ??
        ''
      )
    };
  }

  private formatearFecha(fecha: any): string {

    if (!fecha) {
      return 'Fecha no disponible';
    }

    const valor = new Date(fecha);

    if (isNaN(valor.getTime())) {
      return String(fecha);
    }

    return valor.toLocaleDateString('es-MX', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  }

  private normalizarEstado(estado: string): Pedido['estado'] {

    const valor = (estado ?? '').toLowerCase().trim();

    if (valor.includes('prepar')) {
      return 'En preparación';
    }

    if (valor.includes('listo')) {
      return 'Listo para recoger';
    }

    if (valor.includes('entregado') || valor.includes('completado')) {
      return 'Entregado';
    }

    return 'Pendiente';
  }

  private normalizarEntrega(tipo: string): string {

    const valor = (tipo ?? '').toLowerCase().trim();

    if (
      valor.includes('domicilio') ||
      valor.includes('entrega')
    ) {
      return 'Entrega a domicilio';
    }

    return 'Recoger en sucursal';
  }

  // CONTADORES

  get totalPedidos(): number {
    return this.pedidos.length;
  }

  get pedidosPendientes(): number {
    return this.pedidos.filter(
      p => p.estado === 'Pendiente'
    ).length;
  }

  get pedidosPreparacion(): number {
    return this.pedidos.filter(
      p => p.estado === 'En preparación'
    ).length;
  }

  get pedidosListos(): number {
    return this.pedidos.filter(
      p => p.estado === 'Listo para recoger'
    ).length;
  }

  // FILTRO

  get pedidosFiltrados(): Pedido[] {

    if (this.filtroEstado === 'Todos') {
      return this.pedidos;
    }

    return this.pedidos.filter(
      pedido => pedido.estado === this.filtroEstado
    );
  }

  cambiarFiltro(estado: string): void {
    this.filtroEstado = estado;
  }

  // COLORES

  obtenerColorEstado(estado: string): string {

    switch (estado) {

      case 'Pendiente':
        return 'bg-amber-100 text-amber-800 border-amber-200';

      case 'En preparación':
        return 'bg-blue-100 text-blue-800 border-blue-200';

      case 'Listo para recoger':
        return 'bg-green-100 text-green-800 border-green-200';

      case 'Entregado':
        return 'bg-zinc-100 text-zinc-700 border-zinc-200';

      default:
        return 'bg-zinc-100 text-zinc-700 border-zinc-200';
    }
  }

  // ICONOS

  obtenerIconoEstado(estado: string): string {

    switch (estado) {

      case 'Pendiente':
        return '⏳';

      case 'En preparación':
        return '👨‍🍳';

      case 'Listo para recoger':
        return '🛍️';

      case 'Entregado':
        return '✅';

      default:
        return '📦';
    }
  }
}
