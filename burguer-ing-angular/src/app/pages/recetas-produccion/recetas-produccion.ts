

import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

import { MateriaPrima } from '../../core/models/models';

import {
  Producto,
  Produccion,
  Receta
} from '../../core/models/equipo-operaciones.models';

import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

interface IngredienteFormulario {
  id_materia_prima: number;
  cantidad: number;
}

interface RecetaFormulario {
  id_producto: number;
  instrucciones: string;
  rendimiento: number;
  ingredientes: IngredienteFormulario[];
}

@Component({
  selector: 'app-recetas-produccion',
  standalone: true,
  imports: [CommonModule, FormsModule, Icon],
  templateUrl: './recetas-produccion.html'
})
export class RecetasProduccionPendiente implements OnInit {

  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);

  tab: 'recetas' | 'produccion' = 'recetas';

  recetas: Receta[] = [];
  productos: Producto[] = [];
  materias: MateriaPrima[] = [];
  producciones: Produccion[] = [];

  busqueda = '';

  cargando = false;
  guardando = false;

  error = '';
  mensaje = '';
  errorModal = '';

  modalReceta = false;

  idRecetaEditando: number | null = null;

  formulario: RecetaFormulario = this.formularioVacio();

  idPedidoProduccion: number | null = null;
  idUsuarioProduccion: number | null = null;

  produccionSeleccionada: Produccion | null = null;

  ngOnInit(): void {
    this.idUsuarioProduccion =
      this.auth.usuario()?.id_usuario ?? null;

    this.cargar();
  }

  // =========================================
  // FORMULARIO VACÍO
  // =========================================

  private formularioVacio(): RecetaFormulario {
    return {
      id_producto: 0,
      instrucciones: '',
      rendimiento: 1,
      ingredientes: [
        {
          id_materia_prima: 0,
          cantidad: 1
        }
      ]
    };
  }

  // =========================================
  // FILTRAR RECETAS
  // =========================================

  get recetasFiltradas(): Receta[] {
    const texto = this.busqueda.trim().toLowerCase();

    return this.recetas.filter(receta =>
      !texto ||
      receta.producto.toLowerCase().includes(texto)
    );
  }

  // =========================================
  // PRODUCTOS SIN RECETA
  // =========================================

  get productosSinReceta(): Producto[] {

    const asociados = new Set(
      this.recetas.map(receta => receta.id_producto)
    );

    return this.productos.filter(producto =>

      Boolean(producto.disponible) &&

      !asociados.has(producto.id_producto) &&

      !['bebidas', 'refrescos'].includes(
        producto.categoria.toLowerCase()
      )
    );
  }

  // =========================================
  // PRODUCCIONES ACTIVAS
  // =========================================

  get enProceso(): number {
    return this.producciones.filter(
      p => p.estado === 'En proceso'
    ).length;
  }

  // =========================================
  // CARGAR DATOS DESDE FLASK
  // =========================================

  cargar(): void {

    this.cargando = true;
    this.error = '';

    forkJoin({

      recetas: this.api.get<Receta[]>(
        '/recetas/'
      ),

      productos: this.api.get<Producto[]>(
        '/productos/'
      ),

      materias: this.api.get<MateriaPrima[]>(
        '/materias-primas/'
      ),

      producciones: this.api.get<Produccion[]>(
        '/produccion/'
      )

    }).subscribe({

      next: datos => {

        this.recetas = datos.recetas;
        this.productos = datos.productos;
        this.materias = datos.materias;
        this.producciones = datos.producciones;

        this.cargando = false;
      },

      error: err => {

        this.error = mensajeError(err);
        this.cargando = false;
      }
    });
  }

  // =========================================
  // BUSCAR MATERIA PRIMA
  // =========================================

  private materia(id: number): MateriaPrima | undefined {

    return this.materias.find(
      m => m.id_materia_prima === id
    );
  }

  // =========================================
  // COSTO ESTIMADO DE LA RECETA
  // =========================================

  costoPorUnidad(receta: Receta): number {

    const total = receta.ingredientes.reduce(
      (acumulado, ingrediente) => {

        const costo = Number(
          this.materia(ingrediente.id_materia_prima)
            ?.costo_unitario ?? 0
        );

        return acumulado +
          costo * Number(ingrediente.cantidad);

      },
      0
    );

    return total / Math.max(
      1,
      Number(receta.rendimiento)
    );
  }

  // =========================================
  // PRECIO DEL PRODUCTO
  // =========================================

  precioVenta(receta: Receta): number {

    const producto = this.productos.find(
      p => p.id_producto === receta.id_producto
    );

    return Number(producto?.precio ?? 0);
  }

  // =========================================
  // MARGEN ESTIMADO
  // =========================================

  margen(receta: Receta): number {

    return this.precioVenta(receta) -
      this.costoPorUnidad(receta);
  }

  // =========================================
  // CAPACIDAD ESTIMADA POR INVENTARIO
  // =========================================

  unidadesPosibles(receta: Receta): number {

    if (!receta.ingredientes.length) {
      return 0;
    }

    const capacidades = receta.ingredientes.map(
      ingrediente => {

        const materia = this.materia(
          ingrediente.id_materia_prima
        );

        if (
          !materia ||
          !Boolean(materia.estado) ||
          Number(ingrediente.cantidad) <= 0
        ) {
          return 0;
        }

        return Math.floor(
          Number(materia.stock_actual) *
          Number(receta.rendimiento) /
          Number(ingrediente.cantidad)
        );
      }
    );

    return Math.max(
      0,
      Math.min(...capacidades)
    );
  }

  // =========================================
  // NUEVA RECETA
  // =========================================

  nuevaReceta(): void {

    this.idRecetaEditando = null;

    this.formulario = this.formularioVacio();

    this.errorModal = '';
    this.modalReceta = true;
  }

  // =========================================
  // EDITAR RECETA
  // =========================================

  editarReceta(receta: Receta): void {

    this.idRecetaEditando = receta.id_receta;

    this.formulario = {

      id_producto: receta.id_producto,

      instrucciones: receta.instrucciones ?? '',

      rendimiento: Number(receta.rendimiento),

      ingredientes: receta.ingredientes.map(
        ingrediente => ({

          id_materia_prima:
            ingrediente.id_materia_prima,

          cantidad:
            Number(ingrediente.cantidad)

        })
      )
    };

    this.errorModal = '';
    this.modalReceta = true;
  }

  // =========================================
  // AGREGAR INGREDIENTE AL FORMULARIO
  // =========================================

  agregarIngrediente(): void {

    this.formulario.ingredientes.push({
      id_materia_prima: 0,
      cantidad: 1
    });
  }

  // =========================================
  // QUITAR INGREDIENTE DEL FORMULARIO
  // =========================================

  quitarIngrediente(indice: number): void {

    this.formulario.ingredientes.splice(
      indice,
      1
    );
  }

  // =========================================
  // GUARDAR RECETA
  // =========================================

  guardarReceta(): void {

    this.errorModal = '';

    const f = this.formulario;

    if (
      !f.id_producto ||
      !Number.isInteger(f.rendimiento) ||
      f.rendimiento < 1
    ) {

      this.errorModal =
        'Selecciona el producto e indica un rendimiento entero mayor a cero.';

      return;
    }

    if (
      !f.ingredientes.length ||

      f.ingredientes.some(
        ingrediente =>

          !ingrediente.id_materia_prima ||

          !Number.isFinite(
            Number(ingrediente.cantidad)
          ) ||

          Number(ingrediente.cantidad) <= 0
      )
    ) {

      this.errorModal =
        'Agrega al menos un ingrediente válido con cantidad mayor a cero.';

      return;
    }

    const ids = f.ingredientes.map(
      i => i.id_materia_prima
    );

    if (new Set(ids).size !== ids.length) {

      this.errorModal =
        'No puedes repetir la misma materia prima dentro de una receta.';

      return;
    }

    const datos = {

      id_producto: f.id_producto,

      instrucciones: f.instrucciones.trim(),

      rendimiento: Number(f.rendimiento),

      ingredientes: f.ingredientes.map(
        ingrediente => ({

          id_materia_prima:
            Number(ingrediente.id_materia_prima),

          cantidad:
            Number(ingrediente.cantidad)

        })
      )
    };

    this.guardando = true;

    const solicitud = this.idRecetaEditando !== null

      ? this.api.put<{ mensaje: string }>(
          `/recetas/${this.idRecetaEditando}`,
          datos
        )

      : this.api.post<{ mensaje: string }>(
          '/recetas/',
          datos
        );

    solicitud.subscribe({

      next: respuesta => {

        this.mensaje = respuesta.mensaje;

        this.guardando = false;
        this.modalReceta = false;

        this.cargar();
      },

      error: err => {

        this.guardando = false;
        this.errorModal = mensajeError(err);
      }
    });
  }

  // =========================================
  // ELIMINAR RECETA
  // =========================================

  eliminarReceta(receta: Receta): void {

    const confirmado = confirm(
      `¿Eliminar la receta de "${receta.producto}"? ` +
      'El producto seguirá registrado.'
    );

    if (!confirmado) {
      return;
    }

    this.api.delete<{ mensaje: string }>(
      `/recetas/${receta.id_receta}`
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

  // =========================================
  // INICIAR PRODUCCIÓN
  // =========================================

  iniciarProduccion(): void {

    this.error = '';

    if (
      !this.idPedidoProduccion ||
      !this.idUsuarioProduccion
    ) {

      this.error =
        'Indica un pedido existente y un usuario responsable.';

      return;
    }

    this.guardando = true;

    this.api.post<{
      mensaje: string;
      id_produccion: number;
    }>(
      '/produccion/iniciar',
      {
        id_pedido: this.idPedidoProduccion,
        id_usuario: this.idUsuarioProduccion
      }
    ).subscribe({

      next: respuesta => {

        this.guardando = false;

        this.mensaje =
          `${respuesta.mensaje} Producción #${respuesta.id_produccion}`;

        this.idPedidoProduccion = null;

        this.cargar();
      },

      error: err => {

        this.guardando = false;
        this.error = mensajeError(err);
      }
    });
  }

  // =========================================
  // TERMINAR PRODUCCIÓN
  // =========================================

  terminarProduccion(produccion: Produccion): void {

    const confirmado = confirm(
      `¿Terminar la producción #${produccion.id_produccion}?`
    );

    if (!confirmado) {
      return;
    }

    this.error = '';

    this.api.patch<{ mensaje: string }>(
      `/produccion/${produccion.id_produccion}/completar`,
      {}
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

  // =========================================
  // CONSULTAR DETALLE DE PRODUCCIÓN
  // =========================================

  verProduccion(produccion: Produccion): void {

    this.api.get<Produccion>(
      `/produccion/${produccion.id_produccion}`
    ).subscribe({

      next: respuesta => {

        this.produccionSeleccionada = respuesta;
      },

      error: err => {

        this.error = mensajeError(err);
      }
    });
  }
}
