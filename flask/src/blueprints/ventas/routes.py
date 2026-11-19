
from flask import jsonify
from database import mysql
from . import ventas_bp


# ==========================================
# GET: Consultar todas las ventas
# ==========================================

@ventas_bp.route('/ventas/', methods=['GET'])
def obtener_ventas():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                v.id_venta,
                v.id_pedido,
                v.id_usuario,
                u.nombre AS usuario,
                v.fecha_venta,
                v.subtotal,
                v.descuento,
                v.total,
                p.tipo_entrega,
                p.estado AS estado_pedido
            FROM ventas v
            LEFT JOIN usuarios u
                ON v.id_usuario = u.id_usuario
            INNER JOIN pedidos p
                ON v.id_pedido = p.id_pedido
            ORDER BY v.fecha_venta DESC
        """)

        columnas = [col[0] for col in cursor.description]
        ventas = []

        for fila in cursor.fetchall():
            venta = dict(zip(columnas, fila))

            for campo in ('subtotal', 'descuento', 'total'):
                venta[campo] = float(venta[campo])

            if venta['fecha_venta']:
                venta['fecha_venta'] = str(venta['fecha_venta'])

            ventas.append(venta)

        return jsonify(ventas), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar las ventas.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Consultar una venta por ID
# ==========================================

@ventas_bp.route('/ventas/<int:id_venta>', methods=['GET'])
def obtener_venta(id_venta):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                v.id_venta,
                v.id_pedido,
                v.id_usuario,
                u.nombre AS usuario,
                v.fecha_venta,
                v.subtotal,
                v.descuento,
                v.total,
                p.tipo_entrega,
                p.estado AS estado_pedido,
                p.id_cliente
            FROM ventas v
            LEFT JOIN usuarios u
                ON v.id_usuario = u.id_usuario
            INNER JOIN pedidos p
                ON v.id_pedido = p.id_pedido
            WHERE v.id_venta = %s
        """, (id_venta,))

        fila = cursor.fetchone()

        if not fila:
            return jsonify({
                'mensaje': 'La venta no existe.'
            }), 404

        columnas = [col[0] for col in cursor.description]
        venta = dict(zip(columnas, fila))

        for campo in ('subtotal', 'descuento', 'total'):
            venta[campo] = float(venta[campo])

        if venta['fecha_venta']:
            venta['fecha_venta'] = str(venta['fecha_venta'])

        cursor.execute("""
            SELECT
                id_detalle_pedido,
                id_producto,
                nombre_producto,
                cantidad,
                precio_unitario,
                subtotal
            FROM detalle_pedidos
            WHERE id_pedido = %s
            ORDER BY id_detalle_pedido
        """, (venta['id_pedido'],))

        columnas_detalle = [col[0] for col in cursor.description]
        detalles = []

        for fila_detalle in cursor.fetchall():
            detalle = dict(zip(columnas_detalle, fila_detalle))
            detalle['precio_unitario'] = float(
                detalle['precio_unitario']
            )
            detalle['subtotal'] = float(detalle['subtotal'])
            detalles.append(detalle)

        venta['productos'] = detalles

        cursor.execute("""
            SELECT
                id_pago,
                metodo_pago,
                monto,
                estado,
                referencia,
                fecha_pago
            FROM pagos
            WHERE id_pedido = %s
            ORDER BY fecha_pago, id_pago
        """, (venta['id_pedido'],))

        pagos = []

        for fila_pago in cursor.fetchall():
            pagos.append({
                'id_pago': fila_pago[0],
                'metodo_pago': fila_pago[1],
                'monto': float(fila_pago[2]),
                'estado': fila_pago[3],
                'referencia': fila_pago[4],
                'fecha_pago': (
                    str(fila_pago[5]) if fila_pago[5] else None
                )
            })

        venta['pagos'] = pagos

        return jsonify(venta), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar la venta.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()
