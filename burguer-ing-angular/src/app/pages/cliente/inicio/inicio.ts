
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

import { CarritoService } from '../../../core/services/carrito.service';
import { ApiService } from '../../../core/services/api.service';

// ==========================================
// PRODUCTO RECIBIDO DESDE MYSQL
// ==========================================

interface ProductoBD {
  id_producto: number;
  id_categoria_producto: number;
  categoria: string;
  nombre: string;
  descripcion: string;
  precio: number;
  costo_variable_extra: number;
  imagen: string | null;
  disponible: boolean;
}

// ==========================================
// PRODUCTO PARA MOSTRAR EN INICIO
// ==========================================

interface Producto {
  id: number;
  nombre: string;
  categoria: string;
  especialidad: string;
  precio: number;
  imagen: string;
  descripcion: string;
  ingredientes: string[];
  disponible: boolean;
}

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './inicio.html'
})
export class Inicio implements OnInit {

  constructor(
    private carritoService: CarritoService,
    private api: ApiService
  ) {}

  // ==========================================
  // HAMBURGUESAS
  // ==========================================

  hamburguesas: Producto[] = [];

  hamburguesaSeleccionada: Producto | null = null;

  cargando = true;
  error = '';

  mensajeCarrito = '';

  // ==========================================
  // INICIALIZAR COMPONENTE
  // ==========================================

  ngOnInit(): void {
    this.cargarHamburguesas();
  }

  // ==========================================
  // CARGAR SOLAMENTE LAS TRES ESPECIALIDADES
  // CIVIL, SISTEMAS E INDUSTRIAL
  // ==========================================

  cargarHamburguesas(): void {

    this.cargando = true;
    this.error = '';

    this.api.get<ProductoBD[]>('/productos/').subscribe({

      next: (respuesta) => {

        // Primero obtenemos únicamente hamburguesas disponibles.
        const productosDisponibles = (respuesta || []).filter(
          producto =>
            producto.disponible &&
            producto.id_categoria_producto === 1
        );

        // Orden específico de las tres hamburguesas de Inicio.
        const especialidades = [
          'civil',
          'sistemas',
          'industrial'
        ];

        // Buscar un producto de cada especialidad.
        this.hamburguesas = especialidades
          .map(especialidad => {

            const producto = productosDisponibles.find(p => {

              const nombre = this.normalizarTexto(p.nombre);

              return nombre.includes(especialidad);

            });

            return producto
              ? this.convertirProducto(producto)
              : null;

          })
          .filter(
            (producto): producto is Producto =>
              producto !== null
          );

        this.cargando = false;

        if (this.hamburguesas.length === 0) {
          this.error =
            'No se encontraron hamburguesas de las especialidades solicitadas.';
        }

      },

      error: (err) => {

        console.error('Error al cargar hamburguesas:', err);

        this.error =
          'No fue posible cargar las hamburguesas del catálogo.';

        this.cargando = false;

      }

    });

  }

  // ==========================================
  // NORMALIZAR TEXTO
  // ==========================================

  private normalizarTexto(texto: string): string {

    return (texto || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();

  }

  // ==========================================
  // CONVERTIR PRODUCTO DE MYSQL
  // MISMA LÓGICA QUE MENU.TS
  // ==========================================

  private convertirProducto(p: ProductoBD): Producto {

    return {

      id: p.id_producto,

      nombre: p.nombre,

      categoria: p.categoria,

      especialidad: p.categoria.toUpperCase(),

      precio: Number(p.precio),

      // MISMA RUTA DE IMAGEN QUE EN MENU.TS
      imagen: p.imagen
        ? '/imagenes/' + p.imagen
        : '/imagenes/image.jpg',

      descripcion: p.descripcion || '',

      ingredientes: this.obtenerIngredientes(p.id_producto),

      disponible: p.disponible

    };

  }

  // ==========================================
  // INGREDIENTES
  // MISMA LISTA QUE MENU.TS
  // ==========================================

  private obtenerIngredientes(id: number): string[] {

    const ingredientes: Record<number, string[]> = {

      1: [
        'Pan brioche',
        'Carne de res',
        'Queso amarillo',
        'Lechuga',
        'Vegetales'
      ],

      2: [
        'Pan brioche',
        'Doble carne',
        'Queso amarillo',
        'Tocino',
        'Cebolla'
      ],

      3: [
        'Papas fritas'
      ],

      5: [
        'Refresco individual'
      ],

      7: [
        'Carne de res',
        'Queso amarillo',
        'Tocino',
        'Cebolla'
      ],

      8: [
        'Carne de res',
        'Doble queso',
        'Tocino',
        'Lechuga',
        'Tomate'
      ],

      9: [
        'Carne de res',
        'Queso amarillo',
        'Jalapeños',
        'Cebolla'
      ],

      10: [
        'Pollo',
        'Salsa BBQ'
      ],

      11: [
        'Alitas de pollo',
        'Salsa BBQ'
      ],

      12: [
        'Pan para hot dog',
        'Salchicha',
        'Aderezos'
      ]

    };

    return ingredientes[id] ||
      ['Consulta la descripción del producto'];

  }

  // ==========================================
  // ABRIR DETALLES
  // ==========================================

  abrirDetalles(producto: Producto): void {

    this.hamburguesaSeleccionada = producto;

  }

  // ==========================================
  // CERRAR DETALLES
  // ==========================================

  cerrarDetalles(): void {

    this.hamburguesaSeleccionada = null;

  }

  // ==========================================
  // PRECIO CON DESCUENTO
  // ==========================================

  precioDescuento(precio: number): number {

    return Math.round(precio * 0.85 * 100) / 100;

  }

  // ==========================================
  // AGREGAR AL CARRITO
  // ==========================================

  agregarAlCarrito(producto: Producto): void {

    this.carritoService.agregar({

      id: producto.id,

      nombre: producto.nombre,

      precio: producto.precio,

      imagen: producto.imagen

    });

    this.mensajeCarrito =
      `${producto.nombre} se agregó al carrito.`;

    this.cerrarDetalles();

    setTimeout(() => {

      this.mensajeCarrito = '';

    }, 3000);

  }

}
