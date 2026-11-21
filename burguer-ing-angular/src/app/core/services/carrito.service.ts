import { Injectable, inject, effect } from '@angular/core';
import { BehaviorSubject, forkJoin } from 'rxjs';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';

export interface ProductoCarrito {
  id: number;
  nombre: string;
  precio: number;
  imagen: string;
}

export interface ItemCarrito {
  producto: ProductoCarrito;
  cantidad: number;
}

interface RespuestaCarrito {
  id_carrito: number | null;
  id_cliente: number;
  productos: {
    id_detalle_carrito?: number;
    id_producto: number;
    nombre: string;
    descripcion?: string;
    imagen: string;
    precio: number;
    cantidad: number;
    subtotal: number;
  }[];
  subtotal: number;
}

@Injectable({
  providedIn: 'root'
})
export class CarritoService {

  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);

  private readonly claveCarritoInvitado = 'burguer_carrito_invitado';

  private items: ItemCarrito[] = [];

  private carritoSubject = new BehaviorSubject<ItemCarrito[]>([]);
  carrito$ = this.carritoSubject.asObservable();

  error = '';
  private migrando = false;

  constructor() {
    effect(() => {
      const usuario = this.auth.usuario();

      if (usuario?.id_cliente) {
        this.migrarCarritoInvitado(usuario.id_cliente);
      } else {
        this.items = this.leerCarritoInvitado();
        this.error = '';
        this.actualizarVista();
      }
    });
  }

  // ==============================
  // CARRITO LOCAL DE INVITADOS
  // ==============================

  private leerCarritoInvitado(): ItemCarrito[] {
    try {
      const guardado = localStorage.getItem(this.claveCarritoInvitado);

      if (!guardado) return [];

      return JSON.parse(guardado) as ItemCarrito[];
    } catch (error) {
      console.error('Error al leer carrito local:', error);
      return [];
    }
  }

  private guardarCarritoInvitado(): void {
    try {
      localStorage.setItem(
        this.claveCarritoInvitado,
        JSON.stringify(this.items)
      );
    } catch (error) {
      console.error('Error al guardar carrito local:', error);
    }
  }

  private actualizarVista(): void {
    this.carritoSubject.next([...this.items]);
  }

  private guardarYActualizar(): void {
    this.guardarCarritoInvitado();
    this.actualizarVista();
  }

  sincronizar(): void {
    const idCliente = this.auth.usuario()?.id_cliente;

    if (idCliente) {
      this.cargarCarrito();
    } else {
      this.items = this.leerCarritoInvitado();
      this.actualizarVista();
    }
  }

  // ==============================
  // CARGAR CARRITO DEL SERVIDOR
  // ==============================

  private cargarCarrito(): void {
    const idCliente = this.auth.usuario()?.id_cliente;

    if (!idCliente) {
      this.items = this.leerCarritoInvitado();
      this.actualizarVista();
      return;
    }

    this.api.get<RespuestaCarrito>(
      `/carrito/${idCliente}`
    ).subscribe({
      next: respuesta => {

        this.items = respuesta.productos.map(producto => ({
          producto: {
            id: producto.id_producto,
            nombre: producto.nombre,
            precio: Number(producto.precio),
            imagen: producto.imagen || ''
          },
          cantidad: Number(producto.cantidad)
        }));

        this.error = '';
        this.actualizarVista();
      },
      error: err => {
        console.error('Error al cargar carrito:', err);
        this.error = 'No se pudo cargar el carrito.';
      }
    });
  }

  obtenerItems(): ItemCarrito[] {
    return [...this.items];
  }

  // ==============================
  // MIGRAR CARRITO DE INVITADO
  // AL CARRITO DEL CLIENTE
  // ==============================

  private migrarCarritoInvitado(idCliente: number): void {

    if (this.migrando) return;

    const carritoInvitado = this.leerCarritoInvitado();

    if (carritoInvitado.length === 0) {
      this.cargarCarrito();
      return;
    }

    this.migrando = true;

    const solicitudes = carritoInvitado.map(item =>
      this.api.post<any>(
        `/carrito/${idCliente}/productos`,
        {
          id_producto: item.producto.id,
          cantidad: item.cantidad
        }
      )
    );

    forkJoin(solicitudes).subscribe({
      next: () => {

        localStorage.removeItem(this.claveCarritoInvitado);

        this.migrando = false;
        this.error = '';

        this.cargarCarrito();
      },
      error: err => {

        console.error('Error al migrar carrito:', err);

        this.migrando = false;
        this.error = 'No se pudo sincronizar el carrito de invitado.';

        // Se conserva el carrito local para no perder los productos.
        this.items = carritoInvitado;
        this.actualizarVista();
      }
    });
  }

  // ==============================
  // AGREGAR PRODUCTO
  // ==============================

  agregar(producto: ProductoCarrito): void {

    const idCliente = this.auth.usuario()?.id_cliente;

    // INVITADO: GUARDAR EN LOCALSTORAGE
    if (!idCliente) {

      const existente = this.items.find(
        item => item.producto.id === producto.id
      );

      if (existente) {
        existente.cantidad++;
      } else {
        this.items.push({
          producto: { ...producto },
          cantidad: 1
        });
      }

      this.error = '';
      this.guardarYActualizar();
      return;
    }

    // CLIENTE: GUARDAR EN MYSQL
    this.api.post<any>(
      `/carrito/${idCliente}/productos`,
      {
        id_producto: producto.id,
        cantidad: 1
      }
    ).subscribe({
      next: () => {
        this.error = '';
        this.cargarCarrito();
      },
      error: err => {
        console.error('Error al agregar producto:', err);
        this.error = 'No se pudo agregar el producto.';
      }
    });
  }

  // ==============================
  // AUMENTAR CANTIDAD
  // ==============================

  aumentar(id: number): void {

    const idCliente = this.auth.usuario()?.id_cliente;

    const item = this.items.find(
      item => item.producto.id === id
    );

    if (!item) return;

    // INVITADO
    if (!idCliente) {
      item.cantidad++;
      this.guardarYActualizar();
      return;
    }

    // CLIENTE
    this.actualizarCantidadEnServidor(
      idCliente,
      id,
      item.cantidad + 1
    );
  }

  // ==============================
  // DISMINUIR CANTIDAD
  // ==============================

  disminuir(id: number): void {

    const idCliente = this.auth.usuario()?.id_cliente;

    const item = this.items.find(
      item => item.producto.id === id
    );

    if (!item) return;

    // INVITADO
    if (!idCliente) {

      if (item.cantidad <= 1) {
        this.eliminar(id);
        return;
      }

      item.cantidad--;

      this.guardarYActualizar();
      return;
    }

    // CLIENTE
    const nuevaCantidad = item.cantidad - 1;

    if (nuevaCantidad <= 0) {
      this.eliminar(id);
      return;
    }

    this.actualizarCantidadEnServidor(
      idCliente,
      id,
      nuevaCantidad
    );
  }

  // ==============================
  // ACTUALIZAR CANTIDAD MYSQL
  // ==============================

  private actualizarCantidadEnServidor(
    idCliente: number,
    idProducto: number,
    cantidad: number
  ): void {

    this.api.put<any>(
      `/carrito/${idCliente}/productos/${idProducto}`,
      { cantidad }
    ).subscribe({
      next: () => {
        this.error = '';
        this.cargarCarrito();
      },
      error: err => {
        console.error('Error al actualizar cantidad:', err);
        this.error = 'No se pudo actualizar la cantidad.';
      }
    });
  }

  // ==============================
  // ELIMINAR PRODUCTO
  // ==============================

  eliminar(id: number): void {

    const idCliente = this.auth.usuario()?.id_cliente;

    // INVITADO
    if (!idCliente) {

      this.items = this.items.filter(
        item => item.producto.id !== id
      );

      this.guardarYActualizar();
      return;
    }

    // CLIENTE
    this.api.delete<any>(
      `/carrito/${idCliente}/productos/${id}`
    ).subscribe({
      next: () => {
        this.error = '';
        this.cargarCarrito();
      },
      error: err => {
        console.error('Error al eliminar producto:', err);
        this.error = 'No se pudo eliminar el producto.';
      }
    });
  }

  // ==============================
  // VACIAR CARRITO
  // ==============================

  vaciar(): void {

    const idCliente = this.auth.usuario()?.id_cliente;

    // INVITADO
    if (!idCliente) {
      this.items = [];
      localStorage.removeItem(this.claveCarritoInvitado);
      this.actualizarVista();
      return;
    }

    // CLIENTE
    const productos = [...this.items];

    if (productos.length === 0) {
      this.items = [];
      this.actualizarVista();
      return;
    }

    const solicitudes = productos.map(item =>
      this.api.delete<any>(
        `/carrito/${idCliente}/productos/${item.producto.id}`
      )
    );

    forkJoin(solicitudes).subscribe({
      next: () => {
        this.error = '';
        this.cargarCarrito();
      },
      error: err => {
        console.error('Error al vaciar carrito:', err);
        this.error = 'No se pudo vaciar el carrito.';
        this.cargarCarrito();
      }
    });
  }

  // ==============================
  // TOTALES
  // ==============================

  get cantidadTotal(): number {
    return this.items.reduce(
      (total, item) => total + item.cantidad,
      0
    );
  }

  get subtotal(): number {
    return this.items.reduce(
      (total, item) =>
        total + (item.producto.precio * item.cantidad),
      0
    );
  }
}