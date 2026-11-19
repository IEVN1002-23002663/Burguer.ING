
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';

import {
  Gasto,
  ReporteGastosCategoria,
  ReporteVentaDia,
  ResumenFinanciero
} from '../../core/models/equipo-operaciones.models';

import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

interface GastoForm {
  id_usuario: number | null;
  concepto: string;
  categoria: string;
  monto: number | null;
  fecha_gasto: string;
  descripcion: string;
}

@Component({
  selector: 'app-gastos-finanzas',
  standalone: true,
  imports: [CommonModule, FormsModule, Icon],
  templateUrl: './gastos-finanzas.html'
})
export class GastosFinanzasPendiente implements OnInit {

  private readonly api = inject(ApiService);
  readonly auth = inject(AuthService);

  // ======================================
  // DATOS DEL MÓDULO
  // ======================================

  resumen: ResumenFinanciero | null = null;

  gastos: Gasto[] = [];

  ventasDiarias: ReporteVentaDia[] = [];

  gastosCategorias: ReporteGastosCategoria[] = [];

  // ======================================
  // FILTROS
  // ======================================

  inicio = '';
  fin = '';

  inicioAplicado = '';
  finAplicado = '';

  busqueda = '';

  // ======================================
  // ESTADOS
  // ======================================

  cargando = false;
  guardando = false;

  eliminandoId: number | null = null;

  modal = false;

  editandoId: number | null = null;

  error = '';
  mensaje = '';
  errorModal = '';

  // ======================================
  // CATEGORÍAS DE GASTOS
  // ======================================

  readonly categorias = [
    'Renta',
    'Salarios',
    'Electricidad',
    'Agua',
    'Gas',
    'Internet',
    'Publicidad',
    'Mantenimiento',
    'Otros'
  ];

  form: GastoForm = this.formularioVacio();

  // ======================================
  // INICIALIZACIÓN
  // ======================================

  ngOnInit(): void {
    this.cargar();
  }

  // ======================================
  // FECHA ACTUAL
  // ======================================

  private hoy(): string {

    const fecha = new Date();

    const anio = fecha.getFullYear();

    const mes = String(
      fecha.getMonth() + 1
    ).padStart(2, '0');

    const dia = String(
      fecha.getDate()
    ).padStart(2, '0');

    return `${anio}-${mes}-${dia}`;
  }

  // ======================================
  // FORMULARIO VACÍO
  // ======================================

  private formularioVacio(): GastoForm {

    return {

      id_usuario:
        this.auth.usuario()?.id_usuario ?? null,

      concepto: '',

      categoria: 'Otros',

      monto: null,

      fecha_gasto: this.hoy(),

      descripcion: ''
    };
  }

  // ======================================
  // CATEGORÍAS DEL FORMULARIO
  // ======================================

  get categoriasFormulario(): string[] {

    const seleccion = this.form.categoria;

    return seleccion &&
      !this.categorias.includes(seleccion)

      ? [seleccion, ...this.categorias]

      : this.categorias;
  }

  // ======================================
  // FILTRAR GASTOS
  // ======================================

  get gastosFiltrados(): Gasto[] {

    const texto = this.busqueda
      .trim()
      .toLowerCase();

    return this.gastos.filter(gasto => {

      const fecha = String(
        gasto.fecha_gasto
      ).slice(0, 10);

      const dentroDelPeriodo =

        (
          !this.inicioAplicado ||
          fecha >= this.inicioAplicado
        )

        &&

        (
          !this.finAplicado ||
          fecha <= this.finAplicado
        );

      const contenido = [

        gasto.id_gasto,

        gasto.concepto,

        gasto.categoria,

        gasto.usuario || '',

        gasto.descripcion || ''

      ].join(' ').toLowerCase();

      return dentroDelPeriodo &&
        (
          !texto ||
          contenido.includes(texto)
        );
    });
  }

  // ======================================
  // TOTAL DE GASTOS VISIBLES
  // ======================================

  get totalGastosVisibles(): number {

    return this.gastosFiltrados.reduce(

      (suma, gasto) =>
        suma + Number(gasto.monto || 0),

      0
    );
  }

  // ======================================
  // GRÁFICA DE VENTAS
  // ======================================

  get mayorVenta(): number {

    return Math.max(
      1,

      ...this.ventasDiarias.map(
        d => Number(d.total) || 0
      )
    );
  }

  alturaBarra(total: number): number {

    const valor = Number(total) || 0;

    return valor > 0

      ? Math.max(
          5,
          (valor / this.mayorVenta) * 100
        )

      : 0;
  }

  // ======================================
  // CONSTRUIR FILTROS PARA FLASK
  // ======================================

  private queryFechas(
    inicio: string,
    fin: string
  ): string {

    const parametros = new URLSearchParams();

    if (inicio) {
      parametros.set('fecha_inicio', inicio);
    }

    if (fin) {
      parametros.set('fecha_fin', fin);
    }

    const query = parametros.toString();

    return query ? `?${query}` : '';
  }

  // ======================================
  // CARGAR DATOS DESDE FLASK
  // ======================================

  cargar(): void {

    if (
      this.inicio &&
      this.fin &&
      this.inicio > this.fin
    ) {

      this.error =
        'La fecha inicial no puede ser posterior a la final.';

      return;
    }

    this.error = '';
    this.cargando = true;

    const inicioSolicitado = this.inicio;
    const finSolicitado = this.fin;

    const query = this.queryFechas(
      inicioSolicitado,
      finSolicitado
    );

    forkJoin({

      gastos: this.api.get<Gasto[]>(
        '/gastos/'
      ),

      resumen: this.api.get<ResumenFinanciero>(
        `/reportes/resumen${query}`
      ),

      ventas: this.api.get<ReporteVentaDia[]>(
        `/reportes/ventas${query}`
      ),

      categorias: this.api.get<ReporteGastosCategoria[]>(
        `/reportes/gastos${query}`
      )

    }).pipe(

      finalize(() => this.cargando = false)

    ).subscribe({

      next: respuesta => {

        this.gastos = respuesta.gastos;

        this.resumen = respuesta.resumen;

        this.ventasDiarias = respuesta.ventas;

        this.gastosCategorias = respuesta.categorias;

        this.inicioAplicado = inicioSolicitado;

        this.finAplicado = finSolicitado;
      },

      error: err => {

        this.error = mensajeError(err);

      }

    });
  }

  // ======================================
  // LIMPIAR FILTROS
  // ======================================

  limpiarFiltros(): void {

    this.inicio = '';
    this.fin = '';
    this.busqueda = '';

    this.cargar();
  }

  // ======================================
  // ABRIR FORMULARIO DE NUEVO GASTO
  // ======================================

  crear(): void {

    this.editandoId = null;

    this.form = this.formularioVacio();

    this.errorModal = '';

    this.modal = true;
  }

  // ======================================
  // EDITAR GASTO EXISTENTE
  // ======================================

  editar(gasto: Gasto): void {

    this.editandoId = gasto.id_gasto;

    this.form = {

      id_usuario: gasto.id_usuario,

      concepto: gasto.concepto,

      categoria: gasto.categoria,

      monto: Number(gasto.monto),

      fecha_gasto: String(
        gasto.fecha_gasto
      ).slice(0, 10),

      descripcion: gasto.descripcion || ''
    };

    this.errorModal = '';

    this.modal = true;
  }

  // ======================================
  // CERRAR FORMULARIO
  // ======================================

  cerrarModal(): void {

    if (this.guardando) {
      return;
    }

    this.modal = false;

    this.errorModal = '';
  }

  // ======================================
  // GUARDAR O ACTUALIZAR GASTO
  // ======================================

  guardar(): void {

    if (this.guardando) {
      return;
    }

    const concepto =
      this.form.concepto.trim();

    const categoria =
      this.form.categoria.trim();

    const monto = Math.round(
      Number(this.form.monto) * 100
    ) / 100;

    const idUsuario =
      Number(this.form.id_usuario);

    // Validar usuario

    if (
      !Number.isInteger(idUsuario) ||
      idUsuario <= 0
    ) {

      this.errorModal =
        'Inicia sesión con un usuario válido para registrar gastos.';

      return;
    }

    // Validar campos obligatorios

    if (
      !concepto ||
      !categoria ||
      !this.form.fecha_gasto
    ) {

      this.errorModal =
        'Completa concepto, categoría y fecha.';

      return;
    }

    // Validar longitudes

    if (
      concepto.length > 150 ||
      categoria.length > 80
    ) {

      this.errorModal =
        'El concepto o la categoría supera la longitud permitida.';

      return;
    }

    // Validar monto

    if (
      !Number.isFinite(monto) ||
      monto <= 0
    ) {

      this.errorModal =
        'El monto debe ser mayor a $0.00.';

      return;
    }

    // Preparar datos para Flask

    const datos = {

      id_usuario: idUsuario,

      concepto,

      categoria,

      monto,

      fecha_gasto: this.form.fecha_gasto,

      descripcion:
        this.form.descripcion.trim() || null

    };

    this.errorModal = '';

    this.guardando = true;

    // Elegir crear o actualizar

    const solicitud = this.editandoId === null

      ? this.api.post<{ mensaje: string }>(
          '/gastos/',
          datos
        )

      : this.api.put<{ mensaje: string }>(
          `/gastos/${this.editandoId}`,
          datos
        );

    solicitud.pipe(

      finalize(() => this.guardando = false)

    ).subscribe({

      next: respuesta => {

        this.modal = false;

        this.mensaje = respuesta.mensaje;

        this.cargar();
      },

      error: err => {

        this.errorModal = mensajeError(err);

      }

    });
  }

  // ======================================
  // ELIMINAR GASTO
  // ======================================

  eliminar(gasto: Gasto): void {

    if (this.eliminandoId !== null) {
      return;
    }

    const confirmado = confirm(

      `¿Eliminar definitivamente el gasto «${gasto.concepto}»?`

    );

    if (!confirmado) {
      return;
    }

    this.error = '';

    this.eliminandoId = gasto.id_gasto;

    this.api.delete<{ mensaje: string }>(

      `/gastos/${gasto.id_gasto}`

    ).pipe(

      finalize(() => this.eliminandoId = null)

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
}
