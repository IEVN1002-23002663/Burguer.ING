
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CarritoService } from '../../../core/services/carrito.service';
import { ApiService } from '../../../core/services/api.service';

interface Producto {
  id: number;
  nombre: string;
  categoria: string;
  tipo: 'Hamburguesas' | 'Acompañamientos' | 'Bebidas' | 'Otros';
  especialidad: string;
  precio: number;
  imagen: string;
  descripcion: string;
  ingredientes: string[];
  disponible: boolean;
}

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

@Component({
  selector: 'app-menu-cliente',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './menu.html'
})
export class MenuCliente implements OnInit {

  constructor(
    private carritoService: CarritoService,
    private api: ApiService
  ) {}

  categorias: string[] = [
    'Todas',
    'Hamburguesas',
    'Acompañamientos',
    'Bebidas',
    'Otros'
  ];

  categoriaSeleccionada = 'Todas';

  productoSeleccionado: Producto | null = null;

  productos: Producto[] = [];

  cargando = true;
  error = '';

  ngOnInit(): void {
    this.cargarProductos();
  }

  cargarProductos(): void {
    this.cargando = true;
    this.error = '';

    this.api.get<ProductoBD[]>('/productos/').subscribe({
      next: (respuesta) => {
        this.productos = respuesta
          .filter(p => p.disponible)
          .map(p => this.convertirProducto(p));

        this.cargando = false;
      },
      error: (err) => {
        console.error('Error al cargar productos:', err);
        this.error = 'No fue posible cargar el catálogo.';
        this.cargando = false;
      }
    });
  }

  private convertirProducto(p: ProductoBD): Producto {

    let tipo: Producto['tipo'];

    switch (p.id_categoria_producto) {
      case 1:
        tipo = 'Hamburguesas';
        break;

      case 5:
        tipo = 'Acompañamientos';
        break;

      case 3:
        tipo = 'Bebidas';
        break;

      default:
        tipo = 'Otros';
        break;
    }

    return {
      id: p.id_producto,
      nombre: p.nombre,
      categoria: p.categoria,
      tipo: tipo,
      especialidad: p.categoria.toUpperCase(),
      precio: Number(p.precio),
      imagen: p.imagen
        ? '/imagenes/' + p.imagen
        : '/imagenes/image.jpg',
      descripcion: p.descripcion || '',
      ingredientes: this.obtenerIngredientes(p.id_producto),
      disponible: p.disponible
    };
  }

  private obtenerIngredientes(id: number): string[] {

    const ingredientes: Record<number, string[]> = {
      1: ['Pan brioche', 'Carne de res', 'Queso amarillo', 'Lechuga', 'Vegetales'],
      2: ['Pan brioche', 'Doble carne', 'Queso amarillo', 'Tocino', 'Cebolla'],
      3: ['Papas fritas'],
      5: ['Refresco individual'],
      7: ['Carne de res', 'Queso amarillo', 'Tocino', 'Cebolla'],
      8: ['Carne de res', 'Doble queso', 'Tocino', 'Lechuga', 'Tomate'],
      9: ['Carne de res', 'Queso amarillo', 'Jalapeños', 'Cebolla'],
      10: ['Pollo', 'Salsa BBQ'],
      11: ['Alitas de pollo', 'Salsa BBQ'],
      12: ['Pan para hot dog', 'Salchicha', 'Aderezos']
    };

    return ingredientes[id] || ['Consulta la descripción del producto'];
  }

  get productosFiltrados(): Producto[] {

    if (this.categoriaSeleccionada === 'Todas') {
      return this.productos;
    }

    return this.productos.filter(
      producto => producto.tipo === this.categoriaSeleccionada
    );
  }

  seleccionarCategoria(categoria: string): void {
    this.categoriaSeleccionada = categoria;
  }

  abrirDetalles(producto: Producto): void {
    this.productoSeleccionado = producto;
  }

  cerrarDetalles(): void {
    this.productoSeleccionado = null;
  }

  precioDescuento(precio: number): number {
    return precio * 0.85;
  }

  agregarAlCarrito(producto: Producto): void {

    this.carritoService.agregar({
      id: producto.id,
      nombre: producto.nombre,
      precio: producto.precio,
      imagen: producto.imagen
    });

    alert(`${producto.nombre} agregado al carrito`);
  }
}
