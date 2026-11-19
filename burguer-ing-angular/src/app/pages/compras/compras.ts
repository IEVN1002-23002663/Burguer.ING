import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { ApiMensaje, Compra, CompraDetalle, MateriaPrima, Proveedor } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

@Component({
  selector: 'app-compras', standalone: true, imports:[FormsModule,Icon],
  templateUrl: './compras.html'
})
export class Compras implements OnInit {
  private readonly api = inject(ApiService);
  private readonly auth = inject(AuthService);
  compras: Compra[]=[];
  proveedores:Proveedor[]=[];
  materias:MateriaPrima[]=[];
  detalleActual:Compra|null=null;
  modalNueva=false;
  idProveedor=0;
  observaciones='';
  lineas:CompraDetalle[]=[];
  cargando=false;
  guardando=false;
  mensaje='';
  error='';
  errorModal='';
  ngOnInit():void{this.cargar();}
  get proveedoresActivos():Proveedor[]{return this.proveedores.filter(p=>p.estado===1);}
  get materiasActivas():MateriaPrima[]{return this.materias.filter(m=>m.estado===1);}
  get totalFormulario():number{return this.lineas.reduce((a,d)=>a+(Number(d.cantidad)||0)*(Number(d.costo_unitario)||0),0);}
  moneda(v:number):string{return new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN'}).format(v);}
  unidad(id:number):string{return this.materias.find(m=>m.id_materia_prima===id)?.unidad_medida||'unidad';}
  cargar():void{
    this.cargando=true;this.error='';
    forkJoin({compras:this.api.get<Compra[]>('/compras/'),proveedores:this.api.get<Proveedor[]>('/proveedores/'),materias:this.api.get<MateriaPrima[]>('/materias-primas/')}).subscribe({
      next:r=>{this.compras=r.compras;this.proveedores=r.proveedores;this.materias=r.materias;this.cargando=false;},
      error:e=>{this.error=mensajeError(e);this.cargando=false;}
    });
  }
  abrirNueva():void{this.idProveedor=0;this.observaciones='';this.lineas=[this.nuevaLinea()];this.errorModal='';this.modalNueva=true;}
  private nuevaLinea():CompraDetalle{return{id_materia_prima:0,cantidad:1,costo_unitario:0};}
  agregarLinea():void{this.lineas.push(this.nuevaLinea());}
  quitarLinea(i:number):void{if(this.lineas.length>1)this.lineas.splice(i,1);}
  materiaSeleccionada(d:CompraDetalle):void{d.costo_unitario=this.materias.find(m=>m.id_materia_prima===d.id_materia_prima)?.costo_unitario||0;}
  guardar():void{
    this.errorModal='';
    if(!this.idProveedor){this.errorModal='Selecciona un proveedor.';return;}
    if(this.lineas.some(l=>!l.id_materia_prima||!(l.cantidad>0)||l.costo_unitario<0)){
      this.errorModal='Revisa materia prima, cantidad y costo de cada línea.';return;
    }
    if(new Set(this.lineas.map(l=>l.id_materia_prima)).size!==this.lineas.length){this.errorModal='No repitas el mismo insumo; suma las cantidades en una sola línea.';return;}
    const usuario=this.auth.usuario();
    if(!usuario){this.errorModal='La sesión no tiene usuario. Vuelve a iniciar sesión.';return;}
    this.guardando=true;
    this.api.post<ApiMensaje>('/compras/',{
      id_proveedor:this.idProveedor,id_usuario:usuario.id_usuario,observaciones:this.observaciones,
      detalles:this.lineas.map(({id_materia_prima,cantidad,costo_unitario})=>({id_materia_prima,cantidad,costo_unitario}))
    }).subscribe({
      next:r=>{this.guardando=false;this.modalNueva=false;this.mensaje=r.mensaje;this.cargar();},
      error:e=>{this.guardando=false;this.errorModal=mensajeError(e);}
    });
  }
  verDetalle(c:Compra):void{
    this.api.get<Compra>(`/compras/${c.id_compra}`).subscribe({next:r=>this.detalleActual=r,error:e=>this.error=mensajeError(e)});
  }
  recibir(c:Compra):void{
    if(!confirm(`¿Recibir la compra CMP-${c.id_compra}? Esto sumará los insumos al inventario.`))return;
    this.api.patch<ApiMensaje>(`/compras/${c.id_compra}/recibir`).subscribe({next:r=>{this.mensaje=r.mensaje;this.cargar();},error:e=>this.error=mensajeError(e)});
  }
  cancelar(c:Compra):void{
    if(!confirm(`¿Cancelar la compra CMP-${c.id_compra}?`))return;
    this.api.patch<ApiMensaje>(`/compras/${c.id_compra}/cancelar`).subscribe({next:r=>{this.mensaje=r.mensaje;this.cargar();},error:e=>this.error=mensajeError(e)});
  }
}
