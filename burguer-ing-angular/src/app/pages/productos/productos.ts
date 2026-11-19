
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import { ApiService } from '../../core/services/api.service';
import {
  CategoriaProducto,
  Producto
} from '../../core/models/equipo-operaciones.models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

interface ProductoForm {
  id_categoria_producto: number;
  nombre: string;
  descripcion: string;
  precio: number;
  costo_variable_extra: number;
  imagen: string;
}

interface CategoriaForm {
  nombre: string;
  descripcion: string;
}

@Component({
  selector: 'app-productos',
  standalone: true,
  imports: [CommonModule, FormsModule, Icon],
  templateUrl: './productos.html'
})
export class ProductosPendiente implements OnInit {

  private readonly api = inject(ApiService);

  productos: Producto[] = [];
  categorias: CategoriaProducto[] = [];
  imagenesFallidas = new Set<number>();

  busqueda = '';
  categoriaFiltro = 0;
  mostrarOcultos = false;

  cargando = false;
  guardando = false;
  modalProducto = false;
  modalCategoria = false;

  mensaje = '';
  error = '';
  errorModal = '';

  editandoId: number | null = null;
  editandoCategoria: number | null = null;

  formulario: ProductoForm = this.formularioVacio();

  formularioCategoria: CategoriaForm = {
    nombre: '',
    descripcion: ''
  };

  ngOnInit(): void {
    this.cargar();
  }

  // ============================================
  // FORMULARIO VACÍO
  // ============================================

  private formularioVacio(): ProductoForm {
    return {
      id_categoria_producto: 0,
      nombre: '',
      descripcion: '',
      precio: 0,
      costo_variable_extra: 0,
      imagen: ''
    };
  }

  // ============================================
  // ORDENAR CATEGORÍAS
  // ============================================

  get categoriasOrdenadas(): CategoriaProducto[] {

    const orden = [
      'Hamburguesas',
      'Papas',
      'Boneless',
      'Alitas',
      'Hot Dogs'
    ];

    return [...this.categorias].sort((a, b) => {

      const aPos = orden.findIndex(
        n => n.toLowerCase() === a.nombre.toLowerCase()
      );

      const bPos = orden.findIndex(
        n => n.toLowerCase() === b.nombre.toLowerCase()
      );

      return (
        (aPos === -1 ? 99 : aPos) -
        (bPos === -1 ? 99 : bPos)
      ) || a.nombre.localeCompare(b.nombre, 'es');

    });
  }

  // ============================================
  // MOSTRAR SOLO CATEGORÍAS CON PRODUCTOS ACTIVOS
  // ============================================

  get categoriasVisibles(): CategoriaProducto[] {

    if (this.mostrarOcultos) {
      return this.categoriasOrdenadas;
    }

    return this.categoriasOrdenadas.filter(categoria =>

      this.productos.some(producto =>

        producto.id_categoria_producto ===
          categoria.id_categoria_producto &&

        Boolean(producto.disponible)

      )

    );
  }

  // ============================================
  // FILTRAR PRODUCTOS
  // ============================================

  get filtrados(): Producto[] {

    const texto = this.busqueda.trim().toLowerCase();

    return this.productos.filter(producto => {

      // Normalmente NO mostrar los desactivados.
      const visible =
        this.mostrarOcultos ||
        Boolean(producto.disponible);

      // Filtrar categoría.
      const categoriaCorrecta =
        this.categoriaFiltro === 0 ||
        producto.id_categoria_producto ===
          this.categoriaFiltro;

      // Buscar por nombre, categoría o descripción.
      const contenido = `
        ${producto.nombre}
        ${producto.categoria}
        ${producto.descripcion || ''}
      `.toLowerCase();

      const coincideBusqueda =
        !texto || contenido.includes(texto);

      return (
        visible &&
        categoriaCorrecta &&
        coincideBusqueda
      );

    });
  }

  // ============================================
  // ESTADÍSTICAS
  // ============================================

  get disponibles(): number {
    return this.productos.filter(
      p => Boolean(p.disponible)
    ).length;
  }

  get ocultos(): number {
    return this.productos.filter(
      p => !Boolean(p.disponible)
    ).length;
  }

  // ============================================
  // MOSTRAR / OCULTAR DESACTIVADOS
  // ============================================

  alternarOcultos(): void {

    this.mostrarOcultos = !this.mostrarOcultos;

    // Volver a "Todos" para evitar un filtro
    // seleccionado que ya no sea visible.
    this.categoriaFiltro = 0;
  }

  // ============================================
  // FOTOGRAFÍAS DE LOS PRODUCTOS
  // ============================================

  // Las fotos se encuentran en:
  // public/imagenes/

  rutaImagen(producto: Producto): string {

    const archivo =
      producto.imagen?.trim() ||
      this.nombreAutomatico(producto.nombre);

    return this.construirRuta(archivo);
  }

  rutaImagenFormulario(): string {

    const archivo =
      this.formulario.imagen.trim() ||
      this.nombreAutomatico(this.formulario.nombre);

    return this.construirRuta(archivo);
  }

  private construirRuta(archivo: string): string {

    const nombre = archivo
      .replace(/\\/g, '/')
      .split('/')
      .pop() || '';

    return '/imagenes/' + encodeURIComponent(nombre);
  }

  private nombreAutomatico(nombre: string): string {

    return nombre.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '') + '.jpg';
  }

  registrarImagenFallida(idProducto: number): void {
    this.imagenesFallidas.add(idProducto);
  }

  // ============================================
  // CARGAR DESDE FLASK
  // ============================================

  cargar(): void {

    this.cargando = true;
    this.error = '';

    forkJoin({

      categorias: this.api.get<CategoriaProducto[]>(
        '/categorias-productos/'
      ),

      productos: this.api.get<Producto[]>(
        '/productos/'
      )

    }).subscribe({

      next: respuesta => {

        this.categorias = respuesta.categorias;
        this.productos = respuesta.productos;

        this.imagenesFallidas.clear();
        this.cargando = false;
      },

      error: err => {

        this.error = mensajeError(err);
        this.cargando = false;

      }

    });
  }

  // ============================================
  // AGREGAR PRODUCTO
  // ============================================

  crear(): void {

    this.editandoId = null;
    this.formulario = this.formularioVacio();

    this.formulario.id_categoria_producto =
      this.categoriasOrdenadas[0]?.id_categoria_producto || 0;

    this.errorModal = '';
    this.modalProducto = true;
  }

  // ============================================
  // EDITAR PRODUCTO
  // ============================================

  editar(producto: Producto): void {

    this.editandoId = producto.id_producto;

    this.formulario = {

      id_categoria_producto:
        producto.id_categoria_producto,

      nombre: producto.nombre,

      descripcion: producto.descripcion || '',

      precio: Number(producto.precio),

      costo_variable_extra:
        Number(producto.costo_variable_extra),

      imagen: producto.imagen || ''
    };

    this.errorModal = '';
    this.modalProducto = true;
  }

  // ============================================
  // GUARDAR PRODUCTO
  // ============================================

  guardar(): void {

    this.errorModal = '';

    if (
      !this.formulario.nombre.trim() ||
      !this.formulario.id_categoria_producto ||
      !(Number(this.formulario.precio) > 0)
    ) {

      this.errorModal =
        'Indica el nombre, la categoría y un precio mayor a cero.';

      return;
    }

    if (
      Number(this.formulario.costo_variable_extra) < 0
    ) {

      this.errorModal =
        'El costo variable extra no puede ser negativo.';

      return;
    }

    const datos = {

      ...this.formulario,

      nombre: this.formulario.nombre.trim(),

      imagen:
        this.formulario.imagen.trim() || null

    };

    this.guardando = true;

    const peticion = this.editandoId !== null

      ? this.api.put<{ mensaje: string }>(
          `/productos/${this.editandoId}`,
          datos
        )

      : this.api.post<{ mensaje: string }>(
          '/productos/',
          datos
        );

    peticion.subscribe({

      next: respuesta => {

        this.guardando = false;
        this.modalProducto = false;
        this.mensaje = respuesta.mensaje;

        this.cargar();
      },

      error: err => {

        this.guardando = false;
        this.errorModal = mensajeError(err);
      }

    });
  }

  // ============================================
  // ACTIVAR O DESACTIVAR PRODUCTO
  // ============================================

  cambiarDisponibilidad(producto: Producto): void {

    const disponible = !Boolean(producto.disponible);

    this.api.patch<{ mensaje: string }>(

      `/productos/${producto.id_producto}/disponibilidad`,

      { disponible }

    ).subscribe({

      next: respuesta => {

        this.mensaje = respuesta.mensaje;
        this.cargar();
      },

      error: err => {

        this.error = mensajeError(err);

      }

    });
  }

  // ============================================
  // CREAR CATEGORÍA
  // ============================================

  nuevaCategoria(): void {

    this.editandoCategoria = null;

    this.formularioCategoria = {
      nombre: '',
      descripcion: ''
    };

    this.errorModal = '';
    this.modalCategoria = true;
  }

  // ============================================
  // EDITAR CATEGORÍA
  // ============================================

  editarCategoria(categoria: CategoriaProducto): void {

    this.editandoCategoria =
      categoria.id_categoria_producto;

    this.formularioCategoria = {

      nombre: categoria.nombre,

      descripcion:
        categoria.descripcion || ''

    };

    this.errorModal = '';
    this.modalCategoria = true;
  }

  // ============================================
  // GUARDAR CATEGORÍA
  // ============================================

  guardarCategoria(): void {

    this.errorModal = '';

    if (!this.formularioCategoria.nombre.trim()) {

      this.errorModal =
        'Escribe el nombre de la categoría.';

      return;
    }

    this.guardando = true;

    const datos = {

      ...this.formularioCategoria,

      nombre:
        this.formularioCategoria.nombre.trim()

    };

    const peticion = this.editandoCategoria !== null

      ? this.api.put<{ mensaje: string }>(
          `/categorias-productos/${this.editandoCategoria}`,
          datos
        )

      : this.api.post<{ mensaje: string }>(
          '/categorias-productos/',
          datos
        );

    peticion.subscribe({

      next: respuesta => {

        this.guardando = false;
        this.modalCategoria = false;

        this.mensaje = respuesta.mensaje;

        this.cargar();
      },

      error: err => {

        this.guardando = false;
        this.errorModal = mensajeError(err);

      }

    });
  }
}
