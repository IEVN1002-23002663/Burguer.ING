export interface Usuario {
  id_usuario: number;
  id_rol: number;
  rol: string;
  nombre: string;
  correo: string;
  estado: number;
  fecha_registro: string;
}

export interface AuthUsuario {
  id_usuario: number;
  id_rol: number;
  rol: string;
  nombre: string;
  correo: string;
  id_cliente?: number | null;
}

export interface LoginResponse {
  mensaje: string;
  token: string;
  usuario: AuthUsuario;
}

export interface Proveedor {
  id_proveedor: number;
  nombre: string;
  contacto: string | null;
  telefono: string | null;
  correo: string | null;
  direccion: string | null;
  estado: number;
}

export interface CategoriaInsumo {
  id_categoria_insumo: number;
  nombre: string;
  descripcion: string | null;
}

export interface MateriaPrima {
  id_materia_prima: number;
  id_categoria_insumo: number;
  categoria: string;
  nombre: string;
  unidad_medida: string;
  stock_actual: number;
  stock_minimo: number;
  costo_unitario: number;
  estado: number;
}

export interface CompraDetalle {
  id_detalle_compra?: number;
  id_materia_prima: number;
  materia_prima?: string;
  cantidad: number;
  unidad_medida?: string;
  costo_unitario: number;
  subtotal?: number;
}

export interface Compra {
  id_compra: number;
  id_proveedor: number;
  proveedor: string;
  id_usuario: number;
  usuario: string;
  fecha_compra: string;
  fecha_recepcion: string | null;
  total: number;
  estado: 'Pendiente' | 'Recibida' | 'Cancelada';
  observaciones: string | null;
  detalles?: CompraDetalle[];
}

export interface Movimiento {
  id_movimiento: number;
  id_usuario: number | null;
  usuario: string | null;
  tipo_movimiento: string;
  cantidad: number;
  motivo: string | null;
  fecha_movimiento: string;
  materia_prima?: string;
  unidad_medida?: string;
  id_materia_prima?: number;
}

export interface Alerta {
  id_materia_prima: number;
  nombre: string;
  unidad_medida: string;
  stock_actual: number;
  stock_minimo: number;
  categoria: string;
}

export interface AlertasResponse {
  total_alertas: number;
  alertas: Alerta[];
}

export interface MovimientosResponse {
  materia_prima: { id_materia_prima: number; nombre: string; unidad_medida: string };
  movimientos: Movimiento[];
}

export interface ReporteResumen {
  ventas: { cantidad: number; monto: number };
  compras_recibidas: { cantidad: number; monto: number };
  gastos: { cantidad: number; monto: number };
  inventario: { materias_primas_stock_bajo: number; valor_estimado: number };
  diferencia_referencial: number;
  nota: string;
}

export interface VentaDia {
  fecha: string;
  cantidad_ventas: number;
  subtotal: number;
  descuentos: number;
  total: number;
}

export interface ApiMensaje { mensaje: string; [key: string]: unknown; }
