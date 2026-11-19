import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { ApiMensaje, Usuario } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

type FormUsuario = { nombre: string; correo: string; password: string; id_rol: number };

@Component({
  selector: 'app-usuarios',
  standalone: true,
  imports: [FormsModule, Icon],
  templateUrl: './usuarios.html'
})
export class Usuarios implements OnInit {
  private readonly api = inject(ApiService);
  usuarios: Usuario[] = [];
  filtro = '';
  rolSeleccionado = 'Todos';
  readonly filtrosRoles = ['Todos','Administrador','Empleado','Cliente'];
  cargando = false;
  guardando = false;
  mensaje = '';
  error = '';
  errorModal = '';
  modalAbierto = false;
  editandoId: number | null = null;
  form: FormUsuario = this.formVacio();

  ngOnInit(): void { this.cargar(); }
  get usuariosFiltrados(): Usuario[] {
    const texto = this.filtro.toLocaleLowerCase('es-MX').trim();
    return this.usuarios.filter(u => (this.rolSeleccionado === 'Todos' || u.rol === this.rolSeleccionado)
      && (!texto || `${u.nombre} ${u.correo}`.toLocaleLowerCase('es-MX').includes(texto)));
  }
  private formVacio(): FormUsuario { return { nombre:'', correo:'', password:'', id_rol:2 }; }
  cargar(): void {
    this.cargando=true; this.error='';
    this.api.get<Usuario[]>('/usuarios/').subscribe({
      next: r => { this.usuarios=r; this.cargando=false; },
      error: e => { this.error=mensajeError(e); this.cargando=false; }
    });
  }
  abrirCrear(): void { this.editandoId=null; this.form=this.formVacio(); this.errorModal=''; this.modalAbierto=true; }
  abrirEditar(u: Usuario): void { this.editandoId=u.id_usuario; this.form={nombre:u.nombre,correo:u.correo,password:'',id_rol:u.id_rol}; this.errorModal=''; this.modalAbierto=true; }
  cerrarModal(): void { this.modalAbierto=false; }
  guardar(): void {
    this.errorModal='';
    if (!this.form.nombre.trim() || !this.form.correo.includes('@') || (!this.editandoId && this.form.password.length<8)) {
      this.errorModal='Verifica nombre, correo y contraseña (mínimo 8 caracteres).'; return;
    }
    if (this.form.password && this.form.password.length<8) { this.errorModal='La contraseña debe tener al menos 8 caracteres.'; return; }
    const body = {...this.form, nombre: this.form.nombre.trim(), correo: this.form.correo.trim()};
    if (!body.password) delete (body as Partial<FormUsuario>).password;
    this.guardando=true;
    const req = this.editandoId
      ? this.api.put<ApiMensaje>(`/usuarios/${this.editandoId}`, body)
      : this.api.post<ApiMensaje>('/usuarios/', body);
    req.subscribe({
      next: r => { this.guardando=false; this.modalAbierto=false; this.mensaje=r.mensaje; this.cargar(); },
      error: e => { this.guardando=false; this.errorModal=mensajeError(e); }
    });
  }
  cambiarEstado(u: Usuario): void {
    const nuevo = u.estado === 1 ? 0 : 1;
    if (!confirm(`¿${nuevo?'Activar':'Desactivar'} al usuario ${u.nombre}?`)) return;
    this.api.patch<ApiMensaje>(`/usuarios/${u.id_usuario}/estado`, {estado:nuevo}).subscribe({
      next: r => { this.mensaje=r.mensaje; this.cargar(); }, error: e => this.error=mensajeError(e)
    });
  }
}
