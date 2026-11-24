import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Compra, MateriaPrima, ReporteResumen, Usuario } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

interface Periodo { fecha: string; cantidad: number; total: number; }
interface Grupo { nombre: string; cantidad: number; total?: number; id?: number; }
interface DatosDashboard {
  serie: Periodo[]; pagos: Grupo[]; productos: Grupo[];
  categorias: Grupo[]; entregas: Grupo[];
}
interface Segmento extends Grupo { color: string; porcentaje: number; }

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, Icon, FormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard implements OnInit {
  private readonly api = inject(ApiService);
  cargando = false;
  error = '';
  resumen: ReporteResumen | null = null;
  compras: Compra[] = [];
  materias: MateriaPrima[] = [];
  totalUsuarios = 0;
  fechaInicio = '';
  fechaFin = '';
  agrupacion: 'dia' | 'mes' = 'dia';
  periodoAplicado = 'Todo el historial';
  agrupacionAplicada: 'dia' | 'mes' = 'dia';
  serie: Periodo[] = [];
  pagos: Segmento[] = [];
  categorias: Segmento[] = [];
  productos: Grupo[] = [];
  entregas: Grupo[] = [];
  private readonly colores = ['#e5232a', '#f5a000', '#181818', '#2563eb', '#10b981', '#a855f7', '#64748b', '#0891b2'];

  ngOnInit(): void { this.cargar(); }
  get comprasPendientes(): number { return this.compras.filter(c => c.estado === 'Pendiente').length; }
  get recientes(): Compra[] { return this.compras.slice(0, 4); }
  get bajas(): MateriaPrima[] { return this.materias.filter(m => m.estado === 1 && m.stock_actual <= m.stock_minimo).slice(0, 4); }
  get totalPagos(): number { return this.pagos.reduce((s, p) => s + (p.total ?? 0), 0); }
  get totalUnidades(): number { return this.categorias.reduce((s, c) => s + c.cantidad, 0); }
  get maxIngreso(): number { return Math.max(1, ...this.serie.map(d => d.total)); }
  get anchoGrafica(): number { return Math.max(530, this.serie.length * 65 + 78); }
  get ticketPromedio(): number {
    const n = this.resumen?.ventas.cantidad ?? 0;
    return n ? (this.resumen?.ventas.monto ?? 0) / n : 0;
  }
  moneda(valor: number): string { return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(valor); }
  monedaCorta(valor: number): string { return valor >= 1000 ? '$'+(valor/1000).toFixed(1)+'k' : '$'+valor.toFixed(0); }
  altoBarra(valor: number): number { return Math.max(0, valor / this.maxIngreso * 100); }
  anchoBarra(valor: number, grupos: Grupo[]): number { return valor / Math.max(1, ...grupos.map(g => g.cantidad)) * 100; }
  etiquetaFecha(fecha: string): string { return this.agrupacionAplicada === 'mes' ? fecha : fecha.slice(5); }
  puntoX(i: number): number { return this.serie.length <= 1 ? this.anchoGrafica / 2 : 56 + i * (this.anchoGrafica - 82) / (this.serie.length - 1); }
  puntoY(valor: number): number { return 218 - valor / this.maxIngreso * 176; }
  get linea(): string { return this.serie.map((d, i) => `${this.puntoX(i)},${this.puntoY(d.total)}`).join(' '); }

  private fechaLocal(d: Date): string {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }
  rangoRapido(dias: number): void {
    if (this.cargando) return;
    if (!dias) { this.fechaInicio = ''; this.fechaFin = ''; }
    else {
      const hoy = new Date();
      const inicio = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate() - dias + 1);
      this.fechaInicio = this.fechaLocal(inicio);
      this.fechaFin = this.fechaLocal(hoy);
      this.agrupacion = 'dia';
    }
    this.cargar();
  }

  private segmentos(grupos: Grupo[], porMonto: boolean): Segmento[] {
    const valor = (g: Grupo) => porMonto ? (g.total ?? 0) : g.cantidad;
    const total = grupos.reduce((s, g) => s + valor(g), 0);
    return grupos.map((g, i) => ({ ...g, color: this.colores[i % this.colores.length], porcentaje: total ? valor(g) / total * 100 : 0 }));
  }
  gradiente(grupos: Segmento[]): string {
    if (!grupos.length || !grupos.some(g => g.porcentaje > 0)) return '#eee';
    let acumulado = 0;
    return `conic-gradient(${grupos.map(g => {
      const inicio = acumulado; acumulado += g.porcentaje;
      return `${g.color} ${inicio}% ${acumulado}%`;
    }).join(', ')})`;
  }

  cargar(): void {
    if (this.cargando) return;
    this.error = '';
    if (this.fechaInicio && this.fechaFin && this.fechaInicio > this.fechaFin) {
      this.error = 'La fecha inicial no puede ser posterior a la final.';
      return;
    }
    const inicio = this.fechaInicio, fin = this.fechaFin, agrupacion = this.agrupacion;
    const params = new URLSearchParams();
    if (inicio) params.set('fecha_inicio', inicio);
    if (fin) params.set('fecha_fin', fin);
    const filtro = params.toString();
    const sufijo = filtro ? '?' + filtro : '';
    params.set('agrupacion', agrupacion);
    this.cargando = true;
    forkJoin({
      resumen: this.api.get<ReporteResumen>('/reportes/resumen' + sufijo),
      dashboard: this.api.get<DatosDashboard>('/reportes/dashboard?' + params.toString()),
      compras: this.api.get<Compra[]>('/compras/'),
      inventario: this.api.get<MateriaPrima[]>('/inventario/'),
      usuarios: this.api.get<Usuario[]>('/usuarios/')
    }).subscribe({
      next: r => {
        this.resumen = r.resumen;
        this.compras = r.compras;
        this.materias = r.inventario;
        this.totalUsuarios = r.usuarios.length;
        this.serie = r.dashboard.serie;
        this.pagos = this.segmentos(r.dashboard.pagos, true);
        this.categorias = this.segmentos(r.dashboard.categorias, false);
        this.productos = r.dashboard.productos;
        this.entregas = r.dashboard.entregas;
        this.agrupacionAplicada = agrupacion;
        this.periodoAplicado = !inicio && !fin ? 'Todo el historial' : `${inicio || 'Desde el inicio'} — ${fin || 'Sin límite final'}`;
        this.cargando = false;
      },
      error: e => { this.cargando = false; this.error = mensajeError(e) + ' No se actualizaron los indicadores.'; }
    });
  }
}
