import { Component, OnInit, inject } from '@angular/core';
import { forkJoin } from 'rxjs';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/services/api.service';
import { Compra, MateriaPrima, ReporteResumen, Usuario, VentaDia } from '../../core/models/models';
import { mensajeError } from '../../shared/errors';
import { Icon } from '../../shared/icon';

interface ProductoSimple { id_producto: number; categoria: string; }
interface CategoriaDistribucion { nombre: string; cantidad: number; porcentaje: number; color: string; }

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, Icon],
  templateUrl: './dashboard.html'
})
export class Dashboard implements OnInit {
  private readonly api = inject(ApiService);
  cargando = false;
  error = '';
  resumen: ReporteResumen | null = null;
  compras: Compra[] = [];
  materias: MateriaPrima[] = [];
  ventasDias: VentaDia[] = [];
  categorias: CategoriaDistribucion[] = [];
  totalProductos = 0;
  totalUsuarios = 0;
  gradienteDonut = 'conic-gradient(#e5232a 0 100%)';
  private readonly colores = ['#e5232a','#f5a000','#181818','#2563eb','#10b981','#a855f7'];

  ngOnInit(): void { this.cargar(); }
  get comprasPendientes(): number { return this.compras.filter(c => c.estado === 'Pendiente').length; }
  get recientes(): Compra[] { return this.compras.slice(0, 4); }
  get bajas(): MateriaPrima[] { return this.materias.filter(m => m.estado === 1 && m.stock_actual <= m.stock_minimo).slice(0, 4); }
  moneda(valor: number): string { return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(valor); }
  monedaCorta(valor: number): string { return valor >= 1000 ? '$'+(valor/1000).toFixed(1)+'k' : '$'+valor.toFixed(0); }
  altoBarra(valor: number): number {
    const max = Math.max(1,...this.ventasDias.map(d => d.total));
    return Math.max(2, (valor / max) * 83);
  }

  cargar(): void {
    this.cargando = true;
    this.error = '';
    forkJoin({
      resumen: this.api.get<ReporteResumen>('/reportes/resumen'),
      ventas: this.api.get<VentaDia[]>('/reportes/ventas'),
      compras: this.api.get<Compra[]>('/compras/'),
      inventario: this.api.get<MateriaPrima[]>('/inventario/'),
      usuarios: this.api.get<Usuario[]>('/usuarios/'),
      productos: this.api.get<ProductoSimple[]>('/productos/')
    }).subscribe({
      next: r => {
        this.resumen = r.resumen;
        this.compras = r.compras;
        this.materias = r.inventario;
        this.totalUsuarios = r.usuarios.length;
        this.ventasDias = [...r.ventas].slice(0, 7).reverse();
        this.crearCategorias(r.productos);
        this.cargando = false;
      },
      error: e => { this.cargando = false; this.error = mensajeError(e); }
    });
  }

  private crearCategorias(productos: ProductoSimple[]): void {
    this.totalProductos = productos.length;
    const grupos = new Map<string,number>();
    for (const producto of productos) grupos.set(producto.categoria || 'Sin categoría', (grupos.get(producto.categoria || 'Sin categoría') || 0) + 1);
    let acumulado = 0;
    const tramos: string[] = [];
    this.categorias = [...grupos.entries()].map(([nombre,cantidad],i) => {
      const porcentaje = this.totalProductos ? cantidad / this.totalProductos * 100 : 0;
      const color = this.colores[i % this.colores.length];
      tramos.push(`${color} ${acumulado}% ${acumulado + porcentaje}%`);
      acumulado += porcentaje;
      return { nombre, cantidad, porcentaje, color };
    });
    this.gradienteDonut = `conic-gradient(${tramos.join(', ')})`;
  }
}
