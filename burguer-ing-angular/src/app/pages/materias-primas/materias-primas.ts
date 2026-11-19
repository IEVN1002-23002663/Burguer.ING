import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { ApiMensaje, CategoriaInsumo, MateriaPrima } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

type MateriaForm = {
  id_categoria_insumo: number;
  nombre: string;
  unidad_medida: string;
  stock_minimo: number;
  costo_unitario: number;
};

@Component({
  selector: 'app-materias-primas', standalone: true, imports:[FormsModule,Icon],
  templateUrl: './materias-primas.html'
})
export class MateriasPrimas implements OnInit {
  private readonly api = inject(ApiService);
  materias: MateriaPrima[] = [];
  categorias: CategoriaInsumo[] = [];
  filtro = '';
  categoriaFiltro = 0;
  cargando = false;
  guardando = false;
  modalAbierto = false;
  editandoId: number|null = null;
  error = '';
  errorModal = '';
  mensaje = '';
  form: MateriaForm = this.formVacio();

  ngOnInit(): void { this.cargar(); }
  get materiasFiltradas(): MateriaPrima[] {
    const f=this.filtro.toLowerCase().trim();
    return this.materias.filter(m=>(this.categoriaFiltro===0||m.id_categoria_insumo===this.categoriaFiltro)
      && (!f||m.nombre.toLowerCase().includes(f)||String(m.id_materia_prima).includes(f)));
  }
  moneda(x:number):string {return new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN',maximumFractionDigits:4}).format(x);}
  cantidad(x:number,unidad:string):string {
    const t=new Intl.NumberFormat('es-MX',{maximumFractionDigits:3}).format(x)+' '+unidad;
    return unidad==='g'&&x>=1000?`${t} (${(x/1000).toFixed(2)} kg)`:t;
  }
  private formVacio():MateriaForm {return {id_categoria_insumo:0,nombre:'',unidad_medida:'g',stock_minimo:0,costo_unitario:0};}
  cargar():void {
    this.cargando=true;this.error='';
    forkJoin({materias:this.api.get<MateriaPrima[]>('/materias-primas/'),categorias:this.api.get<CategoriaInsumo[]>('/categorias-insumos/')}).subscribe({
      next:r=>{this.materias=r.materias;this.categorias=r.categorias;this.cargando=false;},
      error:e=>{this.cargando=false;this.error=mensajeError(e);}
    });
  }
  abrirCrear():void {this.editandoId=null;this.form=this.formVacio();this.form.id_categoria_insumo=this.categorias[0]?.id_categoria_insumo||0;this.errorModal='';this.modalAbierto=true;}
  abrirEditar(m:MateriaPrima):void {this.editandoId=m.id_materia_prima;this.form={id_categoria_insumo:m.id_categoria_insumo,nombre:m.nombre,unidad_medida:m.unidad_medida,stock_minimo:m.stock_minimo,costo_unitario:m.costo_unitario};this.errorModal='';this.modalAbierto=true;}
  guardar():void {
    this.errorModal='';
    if(!this.form.nombre.trim()||!this.form.id_categoria_insumo||this.form.stock_minimo<0||this.form.costo_unitario<0){this.errorModal='Revisa el nombre, la categoría y los valores numéricos.';return;}
    this.guardando=true;
    const req=this.editandoId?this.api.put<ApiMensaje>(`/materias-primas/${this.editandoId}`,this.form):this.api.post<ApiMensaje>('/materias-primas/',this.form);
    req.subscribe({next:r=>{this.guardando=false;this.modalAbierto=false;this.mensaje=r.mensaje;this.cargar();},error:e=>{this.guardando=false;this.errorModal=mensajeError(e);}});
  }
  cambiarEstado(m:MateriaPrima):void {
    const estado=m.estado===1?0:1;
    if(!confirm(`¿${estado?'Activar':'Desactivar'} ${m.nombre}?`))return;
    this.api.patch<ApiMensaje>(`/materias-primas/${m.id_materia_prima}/estado`,{estado}).subscribe({next:r=>{this.mensaje=r.mensaje;this.cargar();},error:e=>this.error=mensajeError(e)});
  }
}
