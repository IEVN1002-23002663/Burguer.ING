import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { AlertasResponse, ApiMensaje, MateriaPrima, Movimiento, MovimientosResponse } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

@Component({
  selector: 'app-inventario', standalone: true, imports:[FormsModule,Icon],
  templateUrl: './inventario.html'
})
export class Inventario implements OnInit {
  private readonly api=inject(ApiService);
  private readonly auth=inject(AuthService);
  materias:MateriaPrima[]=[];
  movimientos:Movimiento[]=[];
  totalAlertas=0;
  busqueda='';
  cargando=false;
  cargandoMovimientos=false;
  guardando=false;
  modalAbierto=false;
  error='';errorModal='';mensaje='';
  tipoMovimiento:'AjusteEntrada'|'AjusteSalida'|'Merma'='AjusteEntrada';
  idMateria=0;cantidadMovimiento=1;motivo='';
  ngOnInit():void{this.cargar();}
  get materiasActivas():MateriaPrima[]{return this.materias.filter(m=>m.estado===1);}
  get materiasFiltradas():MateriaPrima[]{return this.materias.filter(m=>m.nombre.toLowerCase().includes(this.busqueda.toLowerCase()));}
  get valorInventario():number{return this.materiasActivas.reduce((a,m)=>a+m.stock_actual*m.costo_unitario,0);}
  get agotados():number{return this.materiasActivas.filter(m=>m.stock_actual===0).length;}
  get unidadSeleccionada():string{return this.materias.find(m=>m.id_materia_prima===this.idMateria)?.unidad_medida||'unidades';}
  moneda(v:number):string{return new Intl.NumberFormat('es-MX',{style:'currency',currency:'MXN'}).format(v);}
  cantidad(x:number,u:string):string{return new Intl.NumberFormat('es-MX',{maximumFractionDigits:3}).format(x)+' '+u;}
  esEntrada(m:Movimiento):boolean{return ['EntradaCompra','AjusteEntrada'].includes(m.tipo_movimiento);}
  etiquetaMovimiento(tipo:string):string{
    const nombres:Record<string,string>={EntradaCompra:'Entrada (compra)',SalidaProduccion:'Salida (producción)',AjusteEntrada:'Ajuste (+)',AjusteSalida:'Ajuste (−)',Merma:'Merma'};
    return nombres[tipo]||tipo;
  }
  cargar():void{
    this.cargando=true;this.error='';
    forkJoin({materias:this.api.get<MateriaPrima[]>('/inventario/'),alertas:this.api.get<AlertasResponse>('/inventario/alertas')}).subscribe({
      next:r=>{this.materias=r.materias;this.totalAlertas=r.alertas.total_alertas;this.cargando=false;this.cargarMovimientos();},
      error:e=>{this.cargando=false;this.error=mensajeError(e);}
    });
  }
  cargarMovimientos():void{
    if(!this.materias.length){this.movimientos=[];return;}
    this.cargandoMovimientos=true;
    // El Flask existente solo ofrece movimientos por materia prima.
    // Reunimos las consultas para construir el kardex global sin modificar el backend.
    forkJoin(this.materias.map(m=>this.api.get<MovimientosResponse>(`/inventario/${m.id_materia_prima}/movimientos`))).subscribe({
      next:resultados=>{
        this.movimientos=resultados.flatMap(r=>r.movimientos.map(m=>({...m,materia_prima:r.materia_prima.nombre,unidad_medida:r.materia_prima.unidad_medida,id_materia_prima:r.materia_prima.id_materia_prima})))
          .sort((a,b)=>b.fecha_movimiento.localeCompare(a.fecha_movimiento)||b.id_movimiento-a.id_movimiento).slice(0,35);
        this.cargandoMovimientos=false;
      },
      error:e=>{this.cargandoMovimientos=false;this.error=mensajeError(e);}
    });
  }
  abrirModal():void {this.tipoMovimiento='AjusteEntrada';this.idMateria=this.materiasActivas[0]?.id_materia_prima||0;this.cantidadMovimiento=1;this.motivo='';this.errorModal='';this.modalAbierto=true;}
  guardarMovimiento():void {
    this.errorModal='';
    if(!this.idMateria||!(this.cantidadMovimiento>0)||!this.motivo.trim()){this.errorModal='Selecciona materia prima, cantidad y motivo.';return;}
    const usuario=this.auth.usuario();
    this.guardando=true;
    const body={id_materia_prima:this.idMateria,cantidad:this.cantidadMovimiento,motivo:this.motivo.trim(),id_usuario:usuario?.id_usuario??null};
    const req=this.tipoMovimiento==='Merma'
      ?this.api.post<ApiMensaje>('/inventario/merma',body)
      :this.api.post<ApiMensaje>('/inventario/ajuste',{...body,tipo_movimiento:this.tipoMovimiento});
    req.subscribe({
      next:r=>{this.guardando=false;this.modalAbierto=false;this.mensaje=r.mensaje;this.cargar();},
      error:e=>{this.guardando=false;this.errorModal=mensajeError(e);}
    });
  }
}
