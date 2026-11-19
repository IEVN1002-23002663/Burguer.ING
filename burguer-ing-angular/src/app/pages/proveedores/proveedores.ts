import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { ApiMensaje, Proveedor } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

type ProveedorForm = Pick<Proveedor,'nombre'|'contacto'|'telefono'|'correo'|'direccion'>;

@Component({
  selector: 'app-proveedores', standalone: true, imports: [FormsModule,Icon],
  templateUrl: './proveedores.html'
})
export class Proveedores implements OnInit {
  private readonly api = inject(ApiService);
  proveedores: Proveedor[] = [];
  busqueda = '';
  modalAbierto = false;
  editandoId: number|null = null;
  form: ProveedorForm = this.vacio();
  cargando = false;
  guardando = false;
  mensaje = '';
  error = '';
  errorModal = '';
  ngOnInit(): void { this.cargar(); }
  get proveedoresFiltrados(): Proveedor[] {
    const texto = this.busqueda.toLowerCase().trim();
    return this.proveedores.filter(p => `${p.nombre} ${p.contacto||''} ${p.correo||''}`.toLowerCase().includes(texto));
  }
  private vacio(): ProveedorForm { return {nombre:'',contacto:'',telefono:'',correo:'',direccion:''}; }
  cargar(): void {
    this.cargando = true; this.error='';
    this.api.get<Proveedor[]>('/proveedores/').subscribe({
      next: r => {this.proveedores=r;this.cargando=false;},
      error: e => {this.error=mensajeError(e);this.cargando=false;}
    });
  }
  abrirCrear(): void { this.editandoId=null;this.form=this.vacio();this.errorModal='';this.modalAbierto=true; }
  abrirEditar(p: Proveedor): void {
    this.editandoId=p.id_proveedor;
    this.form={nombre:p.nombre,contacto:p.contacto||'',telefono:p.telefono||'',correo:p.correo||'',direccion:p.direccion||''};
    this.errorModal='';this.modalAbierto=true;
  }
  guardar(): void {
    this.errorModal='';
    if (!this.form.nombre.trim()) {this.errorModal='El nombre es obligatorio.';return;}
    this.guardando=true;
    const req = this.editandoId
      ? this.api.put<ApiMensaje>(`/proveedores/${this.editandoId}`,this.form)
      : this.api.post<ApiMensaje>('/proveedores/',this.form);
    req.subscribe({
      next:r=>{this.guardando=false;this.modalAbierto=false;this.mensaje=r.mensaje;this.cargar();},
      error:e=>{this.guardando=false;this.errorModal=mensajeError(e);}
    });
  }
  cambiarEstado(p:Proveedor):void {
    const estado=p.estado===1?0:1;
    if(!confirm(`¿${estado?'Activar':'Desactivar'} al proveedor ${p.nombre}?`))return;
    this.api.patch<ApiMensaje>(`/proveedores/${p.id_proveedor}/estado`,{estado}).subscribe({
      next:r=>{this.mensaje=r.mensaje;this.cargar();},error:e=>this.error=mensajeError(e)
    });
  }
}
