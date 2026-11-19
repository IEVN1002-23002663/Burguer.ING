
from flask import request, jsonify
from database import mysql
from decimal import Decimal

from . import finanzas_bp


def obtener_filtros(nombre_fecha):
    """
    Construye filtros de fecha para consultas SQL.
    La fecha final se incluye completa, incluso si la
    columna almacena hora.
    """

    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')

    condiciones = []
    parametros = []

    if fecha_inicio:
        condiciones.append(f"{nombre_fecha} >= %s")
        parametros.append(fecha_inicio)

    if fecha_fin:
        condiciones.append(
            f"{nombre_fecha} < DATE_ADD(%s, INTERVAL 1 DAY)"
        )
        parametros.append(fecha_fin)

    if condiciones:
        return ' WHERE ' + ' AND '.join(condiciones), parametros

    return '', parametros


def convertir_fila_decimal(fila, campos):
    resultado = list(fila)

    for indice in campos:
        if resultado[indice] is not None:
            resultado[indice] = float(resultado[indice])

    return resultado


# ==========================================
# GET: Resumen financiero general
# ==========================================

@finanzas_bp.route('/reportes/resumen', methods=['GET'])
def obtener_resumen():
    cursor = mysql.connection.cursor()

    try:
        where_ventas, params_ventas = obtener_filtros(
            'fecha_venta'
        )

        where_compras, params_compras = obtener_filtros(
            'fecha_compra'
        )

        where_gastos, params_gastos = obtener_filtros(
            'fecha_gasto'
        )

        # Total de ventas registradas.
        cursor.execute(f"""
            SELECT
                COUNT(*),
                COALESCE(SUM(total), 0)
            FROM ventas
            {where_ventas}
        """, tuple(params_ventas))

        total_ventas, monto_ventas = cursor.fetchone()

        # Compras recibidas.
        condiciones_compras = (
            where_compras + (
                ' AND estado = %s'
                if where_compras
                else ' WHERE estado = %s'
            )
        )

        cursor.execute(f"""
            SELECT
                COUNT(*),
                COALESCE(SUM(total), 0)
            FROM compras
            {condiciones_compras}
        """, tuple(params_compras + ['Recibida']))

        total_compras, monto_compras = cursor.fetchone()

        # Gastos registrados.
        cursor.execute(f"""
            SELECT
                COUNT(*),
                COALESCE(SUM(monto), 0)
            FROM gastos
            {where_gastos}
        """, tuple(params_gastos))

        total_gastos, monto_gastos = cursor.fetchone()

        # Inventario con existencias bajas.
        cursor.execute("""
            SELECT COUNT(*)
            FROM materias_primas
            WHERE estado = 1
              AND stock_actual <= stock_minimo
        """)

        materias_stock_bajo = cursor.fetchone()[0]

        # Valor estimado del inventario.
        cursor.execute("""
            SELECT COALESCE(
                SUM(stock_actual * costo_unitario),
                0
            )
            FROM materias_primas
            WHERE estado = 1
        """)

        valor_inventario = cursor.fetchone()[0]

        monto_ventas = Decimal(str(monto_ventas))
        monto_compras = Decimal(str(monto_compras))
        monto_gastos = Decimal(str(monto_gastos))

        # Diferencia informativa, no equivale a utilidad neta.
        diferencia = monto_ventas - monto_compras - monto_gastos

        return jsonify({
            'ventas': {
                'cantidad': total_ventas,
                'monto': float(monto_ventas)
            },
            'compras_recibidas': {
                'cantidad': total_compras,
                'monto': float(monto_compras)
            },
            'gastos': {
                'cantidad': total_gastos,
                'monto': float(monto_gastos)
            },
            'inventario': {
                'materias_primas_stock_bajo': materias_stock_bajo,
                'valor_estimado': float(valor_inventario)
            },
            'diferencia_referencial': float(diferencia),
            'nota': (
                'La diferencia referencial resta compras recibidas y gastos '
                'a las ventas del periodo. No representa utilidad contable, '
                'porque las compras pueden permanecer en inventario.'
            )
        }), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al generar el resumen financiero.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Reporte de ventas
# ==========================================

@finanzas_bp.route('/reportes/ventas', methods=['GET'])
def reporte_ventas():
    cursor = mysql.connection.cursor()

    try:
        where, parametros = obtener_filtros('fecha_venta')

        cursor.execute(f"""
            SELECT
                DATE(fecha_venta) AS fecha,
                COUNT(*) AS cantidad_ventas,
                SUM(subtotal) AS subtotal,
                SUM(descuento) AS descuentos,
                SUM(total) AS total
            FROM ventas
            {where}
            GROUP BY DATE(fecha_venta)
            ORDER BY fecha DESC
        """, tuple(parametros))

        registros = []

        for fila in cursor.fetchall():
            registros.append({
                'fecha': str(fila[0]),
                'cantidad_ventas': fila[1],
                'subtotal': float(fila[2]),
                'descuentos': float(fila[3]),
                'total': float(fila[4])
            })

        return jsonify(registros), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al generar el reporte de ventas.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Reporte de compras
# ==========================================

@finanzas_bp.route('/reportes/compras', methods=['GET'])
def reporte_compras():
    cursor = mysql.connection.cursor()

    try:
        where, parametros = obtener_filtros('fecha_compra')

        condiciones = (
            where + (
                ' AND estado = %s'
                if where
                else ' WHERE estado = %s'
            )
        )

        cursor.execute(f"""
            SELECT
                DATE(fecha_compra) AS fecha,
                COUNT(*) AS cantidad_compras,
                SUM(total) AS total
            FROM compras
            {condiciones}
            GROUP BY DATE(fecha_compra)
            ORDER BY fecha DESC
        """, tuple(parametros + ['Recibida']))

        registros = []

        for fila in cursor.fetchall():
            registros.append({
                'fecha': str(fila[0]),
                'cantidad_compras': fila[1],
                'total': float(fila[2])
            })

        return jsonify(registros), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al generar el reporte de compras.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Reporte de gastos
# ==========================================

@finanzas_bp.route('/reportes/gastos', methods=['GET'])
def reporte_gastos():
    cursor = mysql.connection.cursor()

    try:
        where, parametros = obtener_filtros('fecha_gasto')

        cursor.execute(f"""
            SELECT
                categoria,
                COUNT(*) AS cantidad_gastos,
                SUM(monto) AS total
            FROM gastos
            {where}
            GROUP BY categoria
            ORDER BY total DESC
        """, tuple(parametros))

        registros = []

        for fila in cursor.fetchall():
            registros.append({
                'categoria': fila[0],
                'cantidad_gastos': fila[1],
                'total': float(fila[2])
            })

        return jsonify(registros), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al generar el reporte de gastos.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Reporte de inventario
# ==========================================

@finanzas_bp.route('/reportes/inventario', methods=['GET'])
def reporte_inventario():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                mp.id_materia_prima,
                mp.nombre,
                ci.nombre AS categoria,
                mp.unidad_medida,
                mp.stock_actual,
                mp.stock_minimo,
                mp.costo_unitario,
                (mp.stock_actual * mp.costo_unitario) AS valor_inventario,
                CASE
                    WHEN mp.stock_actual <= mp.stock_minimo THEN 1
                    ELSE 0
                END AS stock_bajo
            FROM materias_primas mp
            INNER JOIN categorias_insumos ci
                ON mp.id_categoria_insumo = ci.id_categoria_insumo
            WHERE mp.estado = 1
            ORDER BY mp.nombre
        """)

        inventario = []

        for fila in cursor.fetchall():
            inventario.append({
                'id_materia_prima': fila[0],
                'nombre': fila[1],
                'categoria': fila[2],
                'unidad_medida': fila[3],
                'stock_actual': float(fila[4]),
                'stock_minimo': float(fila[5]),
                'costo_unitario': float(fila[6]),
                'valor_inventario': float(fila[7]),
                'stock_bajo': bool(fila[8])
            })

        return jsonify(inventario), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al generar el reporte de inventario.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()
