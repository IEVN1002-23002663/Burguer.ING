
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../core/services/api.service';
import { ApiMensaje, Usuario } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

// ==========================================
// FORMULARIO DE USUARIOS
// ==========================================

type FormUsuario = {
  nombre: string;
  correo: string;
  password: string;
  id_rol: number;
};

// ==========================================
// INTERFAZ DE ACREDITACIONES
// ==========================================

interface Acreditacion {
  id_cliente: number;
  id_usuario: number;
  nombre: string;
  correo: string;
  tipo_acreditacion: string;
  folio_acreditacion: string;
  estado_acreditacion: 'Sin acreditar' | 'Aprobada' | 'Denegada';
  fecha_validacion: string | null;
  validado_por: number | null;
  administrador: string | null;
}

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [FormsModule, Icon],
  templateUrl: './usuarios.html'
})
export class Usuarios implements OnInit {

  private readonly api = inject(ApiService);

  // ==========================================
  // USUARIOS
  // ==========================================

  usuarios: Usuario[] = [];

  filtro = '';

  rolSeleccionado = 'Todos';

  readonly filtrosRoles = [
    'Todos',
    'Administrador',
    'Empleado',
    'Cliente'
  ];

  cargando = false;
  guardando = false;

  mensaje = '';
  error = '';

  errorModal = '';

  modalAbierto = false;

  editandoId: number | null = null;

  form: FormUsuario = this.formVacio();

  // ==========================================
  // ACREDITACIONES
  // ==========================================

  acreditaciones: Acreditacion[] = [];

  cargandoAcreditaciones = false;

  errorAcreditaciones = '';

  procesandoAcreditacion: number | null = null;

  // ==========================================
  // INICIALIZACIÓN
  // ==========================================

  ngOnInit(): void {
    this.cargar();
    this.cargarAcreditaciones();
  }

  // ==========================================
  // FILTRAR USUARIOS
  // ==========================================

  get usuariosFiltrados(): Usuario[] {

    const texto = this.filtro
      .toLocaleLowerCase('es-MX')
      .trim();

    return this.usuarios.filter(u =>
      (
        this.rolSeleccionado === 'Todos' ||
        u.rol === this.rolSeleccionado
      ) &&
      (
        !texto ||
        `${u.nombre} ${u.correo}`
          .toLocaleLowerCase('es-MX')
          .includes(texto)
      )
    );
  }

  // ==========================================
  // FORMULARIO VACÍO
  // ==========================================

  private formVacio(): FormUsuario {
    return {
      nombre: '',
      correo: '',
      password: '',
      id_rol: 2
    };
  }

  // ==========================================
  // CARGAR USUARIOS
  // ==========================================

  cargar(): void {

    this.cargando = true;
    this.error = '';

    this.api.get<Usuario[]>('/usuarios/').subscribe({

      next: respuesta => {

        this.usuarios = respuesta;

        this.cargando = false;

      },

      error: error => {

        this.error = mensajeError(error);

        this.cargando = false;

      }

    });

  }

  // ==========================================
  // ABRIR MODAL PARA CREAR
  // ==========================================

  abrirCrear(): void {

    this.editandoId = null;

    this.form = this.formVacio();

    this.errorModal = '';

    this.modalAbierto = true;

  }

  // ==========================================
  // ABRIR MODAL PARA EDITAR
  // ==========================================

  abrirEditar(u: Usuario): void {

    this.editandoId = u.id_usuario;

    this.form = {
      nombre: u.nombre,
      correo: u.correo,
      password: '',
      id_rol: u.id_rol
    };

    this.errorModal = '';

    this.modalAbierto = true;

  }

  // ==========================================
  // CERRAR MODAL
  // ==========================================

  cerrarModal(): void {
    this.modalAbierto = false;
  }

  // ==========================================
  // GUARDAR USUARIO
  // ==========================================

  guardar(): void {

    this.errorModal = '';

    if (
      !this.form.nombre.trim() ||
      !this.form.correo.includes('@') ||
      (!this.editandoId && this.form.password.length < 8)
    ) {

      this.errorModal =
        'Verifica nombre, correo y contraseña (mínimo 8 caracteres).';

      return;

    }

    if (
      this.form.password &&
      this.form.password.length < 8
    ) {

      this.errorModal =
        'La contraseña debe tener al menos 8 caracteres.';

      return;

    }

    const body = {
      ...this.form,
      nombre: this.form.nombre.trim(),
      correo: this.form.correo.trim()
    };

    if (!body.password) {
      delete (body as Partial<FormUsuario>).password;
    }

    this.guardando = true;

    const req = this.editandoId
      ? this.api.put<ApiMensaje>(
          `/usuarios/${this.editandoId}`,
          body
        )
      : this.api.post<ApiMensaje>(
          '/usuarios/',
          body
        );

    req.subscribe({

      next: respuesta => {

        this.guardando = false;

        this.modalAbierto = false;

        this.mensaje = respuesta.mensaje;

        this.cargar();

      },

      error: error => {

        this.guardando = false;

        this.errorModal = mensajeError(error);

      }

    });

  }

  // ==========================================
  // ACTIVAR O DESACTIVAR USUARIO
  // ==========================================

  cambiarEstado(u: Usuario): void {

    const nuevo = u.estado === 1 ? 0 : 1;

    if (
      !confirm(
        `¿${nuevo ? 'Activar' : 'Desactivar'} al usuario ${u.nombre}?`
      )
    ) {
      return;
    }

    this.api.patch<ApiMensaje>(
      `/usuarios/${u.id_usuario}/estado`,
      { estado: nuevo }
    ).subscribe({

      next: respuesta => {

        this.mensaje = respuesta.mensaje;

        this.cargar();

      },

      error: error => {

        this.error = mensajeError(error);

      }

    });

  }

  // ==========================================
  // CARGAR ACREDITACIONES
  // ==========================================

  cargarAcreditaciones(): void {

    this.cargandoAcreditaciones = true;

    this.errorAcreditaciones = '';

    this.api.get<Acreditacion[]>(
      '/usuarios/acreditaciones'
    ).subscribe({

      next: respuesta => {

        this.acreditaciones = respuesta;

        this.cargandoAcreditaciones = false;

      },

      error: error => {

        this.errorAcreditaciones = mensajeError(error);

        this.cargandoAcreditaciones = false;

      }

    });

  }

  // ==========================================
  // CONTAR CÉDULAS PENDIENTES
  // ==========================================

  get acreditacionesPendientes(): number {

    return this.acreditaciones.filter(
      a => a.estado_acreditacion === 'Sin acreditar'
    ).length;

  }

  // ==========================================
  // APROBAR O DENEGAR CÉDULA
  // ==========================================

  validarAcreditacion(
    acreditacion: Acreditacion,
    estado: 'Aprobada' | 'Denegada'
  ): void {

    if (this.procesandoAcreditacion !== null) {
      return;
    }

    const accion = estado === 'Aprobada'
      ? 'aprobar'
      : 'denegar';

    const confirmar = confirm(
      `¿Estás seguro de ${accion} la cédula de ${acreditacion.nombre}?`
    );

    if (!confirmar) {
      return;
    }

    this.procesandoAcreditacion = acreditacion.id_cliente;

    this.errorAcreditaciones = '';

    this.api.patch<ApiMensaje>(
      `/usuarios/cliente/${acreditacion.id_cliente}/acreditacion`,
      {
        estado_acreditacion: estado
      }
    ).subscribe({

      next: respuesta => {

        this.mensaje = respuesta.mensaje;

        this.procesandoAcreditacion = null;

        this.cargarAcreditaciones();

      },

      error: error => {

        this.errorAcreditaciones = mensajeError(error);

        this.procesandoAcreditacion = null;

      }

    });

  }

}
