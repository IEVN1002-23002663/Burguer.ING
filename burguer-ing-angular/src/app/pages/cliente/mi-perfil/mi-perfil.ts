import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';

interface PerfilCliente {
  id_usuario: number;
  id_cliente: number;
  nombre: string;
  correo: string;
  fecha_registro: string | null;
  telefono: string;
  tipo_acreditacion: string;
  folio_acreditacion: string;
  cedula: string;
  estado_acreditacion: string;
  pedidos_realizados: number;
}

interface DireccionCliente {
  id_direccion: number;
  calle: string;
  numero: string;
  colonia: string;
  codigo_postal: string;
  referencias: string;
}

interface RespuestaApi {
  mensaje: string;
  id_direccion?: number;
}

@Component({
  selector: 'app-mi-perfil',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './mi-perfil.html'
})
export class MiPerfil implements OnInit {

  // DATOS DEL PERFIL
  nombre = '';
  correo = '';
  telefono = '';
  cedula = '';

  pedidosRealizados = 0;
  fechaRegistro = 'Cuenta de cliente';
  estadoAcreditacion = 'Sin acreditar';

  // DIRECCIONES
  direcciones: DireccionCliente[] = [];

  direccionForm: Omit<DireccionCliente, 'id_direccion'> = {
    calle: '',
    numero: '',
    colonia: '',
    codigo_postal: '',
    referencias: ''
  };

  idDireccionEditando: number | null = null;
  mostrarFormularioDireccion = false;

  // ESTADOS DE LA INTERFAZ
  cargando = false;
  guardando = false;
  guardandoDireccion = false;

  mensaje = '';
  mensajeError = '';

  mensajeDireccion = '';
  errorDireccion = '';

  constructor(
    private api: ApiService,
    public auth: AuthService
  ) {}

  ngOnInit(): void {
    this.cargarPerfil();
    this.cargarDirecciones();
  }

  // =====================================================
  // OBTENER ID DEL CLIENTE
  // =====================================================

  private obtenerIdCliente(): number | null {

    const usuario = this.auth.usuario();

    if (!usuario || usuario.id_cliente == null) {
      return null;
    }

    return usuario.id_cliente;
  }

  // =====================================================
  // CONSULTAR PERFIL
  // =====================================================

  cargarPerfil(): void {

    const idCliente = this.obtenerIdCliente();

    if (idCliente === null) {
      this.mensajeError =
        'No se encontró el identificador del cliente. Cierra sesión e inicia nuevamente.';
      return;
    }

    this.cargando = true;
    this.mensajeError = '';

    this.api.get<PerfilCliente>(
      `/usuarios/cliente/${idCliente}/perfil`
    ).subscribe({

      next: (respuesta) => {

        this.nombre = respuesta.nombre || '';
        this.correo = respuesta.correo || '';
        this.telefono = respuesta.telefono || '';

        this.cedula =
          respuesta.folio_acreditacion ||
          respuesta.cedula ||
          '';

        this.pedidosRealizados =
          respuesta.pedidos_realizados || 0;

        this.fechaRegistro =
          respuesta.fecha_registro
            ? `Cliente desde ${respuesta.fecha_registro}`
            : 'Cuenta de cliente';

        this.estadoAcreditacion =
          respuesta.estado_acreditacion || 'Sin acreditar';

        this.cargando = false;
      },

      error: (error) => {

        this.cargando = false;

        this.mensajeError =
          error?.error?.mensaje ||
          'No se pudieron cargar los datos del perfil.';
      }

    });
  }

  // =====================================================
  // GUARDAR CAMBIOS DEL PERFIL
  // =====================================================

  guardarCambios(): void {

    this.mensaje = '';
    this.mensajeError = '';

    const idCliente = this.obtenerIdCliente();

    if (idCliente === null) {
      this.mensajeError =
        'No se encontró la sesión del cliente.';
      return;
    }

    if (!this.nombre.trim() || !this.correo.trim()) {
      this.mensajeError =
        'El nombre y el correo electrónico son obligatorios.';
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.correo.trim())) {
      this.mensajeError =
        'Ingresa un correo electrónico válido.';
      return;
    }

    this.guardando = true;

    const datos = {
      nombre: this.nombre.trim(),
      correo: this.correo.trim(),
      telefono: this.telefono.trim(),
      cedula: this.cedula.trim()
    };

    this.api.put<RespuestaApi>(
      `/usuarios/cliente/${idCliente}/perfil`,
      datos
    ).subscribe({

      next: (respuesta) => {

        this.guardando = false;

        this.mensaje =
          respuesta.mensaje || 'Perfil actualizado correctamente.';

        // Actualizar los datos de sesión para reflejarlos
        // también en los componentes que utilizan AuthService.
        const usuarioActual = this.auth.usuario();

        if (usuarioActual) {

          const usuarioActualizado = {
            ...usuarioActual,
            nombre: this.nombre.trim(),
            correo: this.correo.trim()
          };

          this.auth.usuario.set(usuarioActualizado);

          localStorage.setItem(
            'burguer_usuario',
            JSON.stringify(usuarioActualizado)
          );
        }

        this.cargarPerfil();
      },

      error: (error) => {

        this.guardando = false;

        this.mensajeError =
          error?.error?.mensaje ||
          'No se pudieron guardar los cambios.';
      }

    });
  }

  // =====================================================
  // CONSULTAR DIRECCIONES
  // =====================================================

  cargarDirecciones(): void {

    const idCliente = this.obtenerIdCliente();

    if (idCliente === null) {
      return;
    }

    this.api.get<DireccionCliente[]>(
      `/usuarios/cliente/${idCliente}/direcciones`
    ).subscribe({

      next: (respuesta) => {
        this.direcciones = respuesta || [];
      },

      error: (error) => {

        this.errorDireccion =
          error?.error?.mensaje ||
          'No se pudieron consultar las direcciones.';
      }

    });
  }

  // =====================================================
  // MOSTRAR FORMULARIO PARA NUEVA DIRECCIÓN
  // =====================================================

  nuevaDireccion(): void {

    this.limpiarFormularioDireccion();

    this.idDireccionEditando = null;
    this.mostrarFormularioDireccion = true;

    this.mensajeDireccion = '';
    this.errorDireccion = '';
  }

  // =====================================================
  // EDITAR DIRECCIÓN
  // =====================================================

  editarDireccion(direccion: DireccionCliente): void {

    this.idDireccionEditando = direccion.id_direccion;

    this.direccionForm = {
      calle: direccion.calle || '',
      numero: direccion.numero || '',
      colonia: direccion.colonia || '',
      codigo_postal: direccion.codigo_postal || '',
      referencias: direccion.referencias || ''
    };

    this.mostrarFormularioDireccion = true;

    this.mensajeDireccion = '';
    this.errorDireccion = '';
  }

  // =====================================================
  // GUARDAR O ACTUALIZAR DIRECCIÓN
  // =====================================================

  guardarDireccion(): void {

    this.mensajeDireccion = '';
    this.errorDireccion = '';

    const idCliente = this.obtenerIdCliente();

    if (idCliente === null) {
      this.errorDireccion =
        'No se encontró la sesión del cliente.';
      return;
    }

    if (
      !this.direccionForm.calle.trim() ||
      !this.direccionForm.colonia.trim()
    ) {
      this.errorDireccion =
        'La calle y la colonia son obligatorias.';
      return;
    }

    this.guardandoDireccion = true;

    const datos = {
      calle: this.direccionForm.calle.trim(),
      numero: this.direccionForm.numero.trim(),
      colonia: this.direccionForm.colonia.trim(),
      codigo_postal: this.direccionForm.codigo_postal.trim(),
      referencias: this.direccionForm.referencias.trim()
    };

    // EDITAR DIRECCIÓN EXISTENTE
    if (this.idDireccionEditando !== null) {

      const idDireccion = this.idDireccionEditando;

      this.api.put<RespuestaApi>(
        `/usuarios/cliente/${idCliente}/direcciones/${idDireccion}`,
        datos
      ).subscribe({

        next: (respuesta) => {

          this.guardandoDireccion = false;

          this.mensajeDireccion =
            respuesta.mensaje || 'Dirección actualizada correctamente.';

          this.mostrarFormularioDireccion = false;
          this.limpiarFormularioDireccion();

          this.idDireccionEditando = null;

          this.cargarDirecciones();
        },

        error: (error) => {

          this.guardandoDireccion = false;

          this.errorDireccion =
            error?.error?.mensaje ||
            'No se pudo actualizar la dirección.';
        }

      });

      return;
    }

    // REGISTRAR NUEVA DIRECCIÓN
    this.api.post<RespuestaApi>(
      `/usuarios/cliente/${idCliente}/direcciones`,
      datos
    ).subscribe({

      next: (respuesta) => {

        this.guardandoDireccion = false;

        this.mensajeDireccion =
          respuesta.mensaje || 'Dirección registrada correctamente.';

        this.mostrarFormularioDireccion = false;

        this.limpiarFormularioDireccion();

        this.cargarDirecciones();
      },

      error: (error) => {

        this.guardandoDireccion = false;

        this.errorDireccion =
          error?.error?.mensaje ||
          'No se pudo registrar la dirección.';
      }

    });
  }

  // =====================================================
  // ELIMINAR DIRECCIÓN
  // =====================================================

  eliminarDireccion(direccion: DireccionCliente): void {

    const idCliente = this.obtenerIdCliente();

    if (idCliente === null) {
      this.errorDireccion =
        'No se encontró la sesión del cliente.';
      return;
    }

    const confirmar = window.confirm(
      `¿Deseas eliminar la dirección de ${direccion.calle} ${direccion.numero}?`
    );

    if (!confirmar) {
      return;
    }

    this.errorDireccion = '';
    this.mensajeDireccion = '';

    this.api.delete<RespuestaApi>(
      `/usuarios/cliente/${idCliente}/direcciones/${direccion.id_direccion}`
    ).subscribe({

      next: (respuesta) => {

        this.mensajeDireccion =
          respuesta.mensaje || 'Dirección eliminada correctamente.';

        this.cargarDirecciones();
      },

      error: (error) => {

        this.errorDireccion =
          error?.error?.mensaje ||
          'No se pudo eliminar la dirección.';
      }

    });
  }

  // =====================================================
  // CANCELAR FORMULARIO DE DIRECCIÓN
  // =====================================================

  cancelarDireccion(): void {

    this.mostrarFormularioDireccion = false;
    this.idDireccionEditando = null;

    this.limpiarFormularioDireccion();

    this.errorDireccion = '';
  }

  // =====================================================
  // LIMPIAR FORMULARIO
  // =====================================================

  private limpiarFormularioDireccion(): void {

    this.direccionForm = {
      calle: '',
      numero: '',
      colonia: '',
      codigo_postal: '',
      referencias: ''
    };
  }

  // =====================================================
  // INICIALES DEL CLIENTE
  // =====================================================

  get iniciales(): string {

    const partes = this.nombre
      .trim()
      .split(/\s+/)
      .filter(Boolean);

    if (partes.length === 0) {
      return 'CL';
    }

    if (partes.length === 1) {
      return partes[0].substring(0, 2).toUpperCase();
    }

    return (
      partes[0][0] +
      partes[partes.length - 1][0]
    ).toUpperCase();
  }

  // =====================================================
  // TEXTO DEL ESTADO DE ACREDITACIÓN
  // =====================================================

  get estadoCedulaTexto(): string {

    if (this.cedula.trim() === '') {
      return 'Sin registro';
    }

    if (this.estadoAcreditacion === 'Validada') {
      return 'Acreditación validada';
    }

    if (
      this.estadoAcreditacion === 'Pendiente' ||
      this.estadoAcreditacion === 'En revisión'
    ) {
      return 'Pendiente de verificación';
    }

    return this.estadoAcreditacion;
  }

}