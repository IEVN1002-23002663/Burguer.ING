
/*
 * Modelos para los módulos del segundo equipo.
 * Burguer.ING
 *
 * Productos
 * Recetas y producción
 * Pedidos
 * Ventas
 * Gastos y finanzas
 */

// =======================================
// PRODUCTOS Y CATEGORÍAS
// =======================================

export interface CategoriaProducto {
  id_categoria_producto: number;
  nombre: string;
  descripcion: string | null;
}

export interface Producto {
  id_producto: number;
  id_categoria_producto: number;
  categoria: string;
  nombre: string;
  descripcion: string | null;
  precio: number;
  costo_variable_extra: number;
  imagen: string | null;
  disponible: boolean | number;
}

// =======================================
// RECETAS
// =======================================

export interface IngredienteReceta {
  id_detalle_receta?: number;
  id_materia_prima: number;
  materia_prima?: string;
  unidad_medida?: string;
  cantidad: number;
}

export interface Receta {
  id_receta: number;
  id_producto: number;
  producto: string;
  instrucciones: string | null;
  rendimiento: number;
  ingredientes: IngredienteReceta[];
}

// =======================================
// PRODUCCIÓN
// =======================================

export interface DetalleProduccion {
  id_detalle_produccion: number;
  id_detalle_pedido: number;
  cantidad_preparada: number;
  estado: string;
  id_producto: number;
  nombre_producto: string;
}

export interface Produccion {
  id_produccion: number;
  id_pedido: number;
  id_usuario: number;
  usuario: string | null;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  estado: string;
  inventario_descontado: boolean;
  detalles?: DetalleProduccion[];
}

// =======================================
// CARRITO DE COMPRAS
// =======================================

export interface CarritoItem {
  id_detalle_carrito: number;
  id_producto: number;
  nombre: string;
  descripcion: string | null;
  imagen: string | null;
  precio: number;
  cantidad: number;
  subtotal: number;
}

export interface Carrito {
  id_carrito: number | null;
  id_cliente: number;
  productos: CarritoItem[];
  subtotal: number;
}

// =======================================
// PEDIDOS
// =======================================

export interface PedidoResumen {
  id_pedido: number;
  id_cliente?: number | null;
  cliente?: string;
  fecha_pedido: string;
  tipo_entrega: string;
  subtotal: number;
  porcentaje_descuento: number;
  monto_descuento: number;
  costo_entrega: number;
  total: number;
  estado: string;
  observaciones: string | null;
}

export interface DetallePedido {
  id_detalle_pedido: number;
  id_producto: number;
  nombre_producto: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export interface PedidoDetalle extends PedidoResumen {
  id_cliente: number | null;
  id_usuario: number | null;
  id_direccion: number | null;
  productos: DetallePedido[];
  historial: {
    estado: string;
    comentario: string | null;
    fecha_cambio: string;
  }[];
}

// =======================================
// CLIENTES Y DIRECCIONES
// =======================================

export interface ClientePedido {
  id_cliente: number;
  nombre: string;
  correo: string;
  estado_acreditacion: string;
  porcentaje_descuento: number;
}

export interface DireccionPedido {
  id_direccion: number;
  calle: string;
  numero: string | null;
  colonia: string;
  codigo_postal: string | null;
  referencias: string | null;
}

// =======================================
// PAGOS
// =======================================

export interface Pago {
  id_pago: number;
  id_pedido: number;
  metodo_pago: string;
  monto: number;
  estado: string;
  referencia: string | null;
  fecha_pago: string;
}

export interface PagosPedido {
  id_pedido: number;
  total_pedido: number;
  total_pagado: number;
  saldo_pendiente: number;
  pagos: Pago[];
}

// =======================================
// VENTAS
// =======================================

export interface Venta {
  id_venta: number;
  id_pedido: number;
  id_usuario: number | null;
  usuario: string | null;
  fecha_venta: string;
  subtotal: number;
  descuento: number;
  total: number;
  tipo_entrega: string;
  estado_pedido: string;
  id_cliente?: number | null;
  productos?: DetallePedido[];
  pagos?: Pago[];
}

// =======================================
// GASTOS
// =======================================

export interface Gasto {
  id_gasto: number;
  id_usuario: number;
  usuario: string | null;
  concepto: string;
  categoria: string;
  monto: number;
  fecha_gasto: string;
  descripcion: string | null;
}

// =======================================
// REPORTES FINANCIEROS
// =======================================

export interface ResumenFinanciero {
  ventas: {
    cantidad: number;
    monto: number;
  };

  compras_recibidas: {
    cantidad: number;
    monto: number;
  };

  gastos: {
    cantidad: number;
    monto: number;
  };

  inventario: {
    materias_primas_stock_bajo: number;
    valor_estimado: number;
  };

  diferencia_referencial: number;
  nota: string;
}

export interface ReporteVentaDia {
  fecha: string;
  cantidad_ventas: number;
  subtotal: number;
  descuentos: number;
  total: number;
}

export interface ReporteGastosCategoria {
  categoria: string;
  cantidad_gastos: number;
  total: number;
}
