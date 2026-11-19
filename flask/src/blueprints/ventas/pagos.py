
from flask import request, jsonify
from database import mysql
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from . import ventas_bp


def convertir_decimal(valor):
    try:
        numero = Decimal(str(valor))

        if not numero.is_finite():
            return None

        return numero
    except (InvalidOperation, TypeError, ValueError):
        return None


def dinero(valor):
    return valor.quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )


# ==========================================
# POST: Registrar un pago
# ==========================================

@ventas_bp.route('/pagos/', methods=['POST'])
def registrar_pago():
    datos = request.get_json()

    if not datos:
        return jsonify({
            'mensaje': 'Debes enviar los datos del pago.'
        }), 400

    id_pedido = datos.get('id_pedido')
    metodo_pago = datos.get('metodo_pago')
    monto = convertir_decimal(datos.get('monto'))
    referencia = datos.get('referencia')
    id_usuario = datos.get('id_usuario')

    metodos_validos = (
        'Efectivo',
        'Tarjeta',
        'Transferencia'
    )

    if not id_pedido or not metodo_pago or monto is None:
        return jsonify({
            'mensaje': 'El pedido, método de pago y monto son obligatorios.'
        }), 400

    if metodo_pago not in metodos_validos:
        return jsonify({
            'mensaje': 'El método de pago no es válido.'
        }), 400

    if monto <= 0:
        return jsonify({
            'mensaje': 'El monto debe ser mayor que cero.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        # Bloquear el pedido durante el registro del pago.
        cursor.execute("""
            SELECT
                id_pedido,
                subtotal,
                monto_descuento,
                total,
                estado
            FROM pedidos
            WHERE id_pedido = %s
            FOR UPDATE
        """, (id_pedido,))

        pedido = cursor.fetchone()

        if not pedido:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El pedido no existe.'
            }), 404

        subtotal = Decimal(str(pedido[1]))
        descuento = Decimal(str(pedido[2]))
        total = Decimal(str(pedido[3]))
        estado_pedido = pedido[4]

        if estado_pedido in ('Cancelado', 'Anulado'):
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'No se puede registrar un pago para un pedido cancelado.'
            }), 400

        # Validar usuario responsable, si se proporcionó.
        if id_usuario is not None:
            cursor.execute("""
                SELECT id_usuario
                FROM usuarios
                WHERE id_usuario = %s
                  AND estado = 1
            """, (id_usuario,))

            if not cursor.fetchone():
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': 'El usuario no existe o está inactivo.'
                }), 400

        # Consultar pagos completados anteriormente.
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0)
            FROM pagos
            WHERE id_pedido = %s
              AND estado = 'Completado'
        """, (id_pedido,))

        total_pagado = Decimal(str(cursor.fetchone()[0]))
        saldo_pendiente = dinero(total - total_pagado)

        if saldo_pendiente <= 0:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El pedido ya está completamente pagado.'
            }), 409

        if monto > saldo_pendiente:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El monto supera el saldo pendiente.',
                'saldo_pendiente': float(saldo_pendiente)
            }), 400

        # Registrar el pago.
        cursor.execute("""
            INSERT INTO pagos (
                id_pedido,
                metodo_pago,
                monto,
                estado,
                referencia,
                fecha_pago
            )
            VALUES (%s, %s, %s, 'Completado', %s, NOW())
        """, (
            id_pedido,
            metodo_pago,
            monto,
            referencia
        ))

        id_pago = cursor.lastrowid
        nuevo_total_pagado = dinero(total_pagado + monto)
        nuevo_saldo = dinero(total - nuevo_total_pagado)

        # Si el pedido quedó completamente pagado, crear la venta.
        venta_creada = False
        id_venta = None

        if nuevo_saldo == 0:
            cursor.execute("""
                SELECT id_venta
                FROM ventas
                WHERE id_pedido = %s
            """, (id_pedido,))

            venta_existente = cursor.fetchone()

            if not venta_existente:
                cursor.execute("""
                    INSERT INTO ventas (
                        id_pedido,
                        id_usuario,
                        fecha_venta,
                        subtotal,
                        descuento,
                        total
                    )
                    VALUES (%s, %s, NOW(), %s, %s, %s)
                """, (
                    id_pedido,
                    id_usuario,
                    subtotal,
                    descuento,
                    total
                ))

                id_venta = cursor.lastrowid
                venta_creada = True
            else:
                id_venta = venta_existente[0]

            cursor.execute("""
                UPDATE pedidos
                SET estado = 'Pagado'
                WHERE id_pedido = %s
            """, (id_pedido,))

            cursor.execute("""
                INSERT INTO historial_pedidos (
                    id_pedido,
                    id_usuario,
                    estado,
                    comentario,
                    fecha_cambio
                )
                VALUES (
                    %s, %s, 'Pagado',
                    'Pedido pagado completamente',
                    NOW()
                )
            """, (id_pedido, id_usuario))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Pago registrado correctamente.',
            'id_pago': id_pago,
            'id_pedido': id_pedido,
            'monto_pagado': float(monto),
            'total_pagado': float(nuevo_total_pagado),
            'saldo_pendiente': float(nuevo_saldo),
            'pedido_pagado': nuevo_saldo == 0,
            'venta_creada': venta_creada,
            'id_venta': id_venta
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo registrar el pago.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Consultar pagos de un pedido
# ==========================================

@ventas_bp.route(
    '/pagos/pedido/<int:id_pedido>',
    methods=['GET']
)
def obtener_pagos_pedido(id_pedido):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_pedido, total
            FROM pedidos
            WHERE id_pedido = %s
        """, (id_pedido,))

        pedido = cursor.fetchone()

        if not pedido:
            return jsonify({
                'mensaje': 'El pedido no existe.'
            }), 404

        cursor.execute("""
            SELECT
                id_pago,
                id_pedido,
                metodo_pago,
                monto,
                estado,
                referencia,
                fecha_pago
            FROM pagos
            WHERE id_pedido = %s
            ORDER BY fecha_pago DESC, id_pago DESC
        """, (id_pedido,))

        columnas = [col[0] for col in cursor.description]
        pagos = []

        for fila in cursor.fetchall():
            pago = dict(zip(columnas, fila))
            pago['monto'] = float(pago['monto'])

            if pago['fecha_pago']:
                pago['fecha_pago'] = str(pago['fecha_pago'])

            pagos.append(pago)

        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0)
            FROM pagos
            WHERE id_pedido = %s
              AND estado = 'Completado'
        """, (id_pedido,))

        total_pagado = Decimal(str(cursor.fetchone()[0]))
        total_pedido = Decimal(str(pedido[1]))
        saldo_pendiente = dinero(total_pedido - total_pagado)

        return jsonify({
            'id_pedido': id_pedido,
            'total_pedido': float(total_pedido),
            'total_pagado': float(total_pagado),
            'saldo_pendiente': float(saldo_pendiente),
            'pagos': pagos
        }), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar los pagos.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()
