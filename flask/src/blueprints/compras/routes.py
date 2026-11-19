
from flask import Blueprint, request, jsonify
from database import mysql
from decimal import Decimal, InvalidOperation


compras_bp = Blueprint(
    'compras',
    __name__,
    url_prefix='/api/compras'
)


# ==========================================
# CONSULTAR TODAS LAS COMPRAS
# ==========================================

@compras_bp.route('/', methods=['GET'])
def obtener_compras():

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                c.id_compra,
                c.id_proveedor,
                p.nombre,
                c.id_usuario,
                u.nombre,
                c.fecha_compra,
                c.fecha_recepcion,
                c.total,
                c.estado,
                c.observaciones
            FROM compras c
            INNER JOIN proveedores p
                ON c.id_proveedor = p.id_proveedor
            INNER JOIN usuarios u
                ON c.id_usuario = u.id_usuario
            ORDER BY c.id_compra DESC
        """

        cursor.execute(sql)
        resultados = cursor.fetchall()

        compras = []

        for fila in resultados:
            compras.append({
                'id_compra': fila[0],
                'id_proveedor': fila[1],
                'proveedor': fila[2],
                'id_usuario': fila[3],
                'usuario': fila[4],
                'fecha_compra': str(fila[5]),
                'fecha_recepcion': str(fila[6]) if fila[6] else None,
                'total': float(fila[7]),
                'estado': fila[8],
                'observaciones': fila[9]
            })

        return jsonify(compras), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar las compras',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# CONSULTAR COMPRA POR ID
# ==========================================

@compras_bp.route('/<int:id_compra>', methods=['GET'])
def obtener_compra(id_compra):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql_compra = """
            SELECT
                c.id_compra,
                c.id_proveedor,
                p.nombre,
                c.id_usuario,
                u.nombre,
                c.fecha_compra,
                c.fecha_recepcion,
                c.total,
                c.estado,
                c.observaciones
            FROM compras c
            INNER JOIN proveedores p
                ON c.id_proveedor = p.id_proveedor
            INNER JOIN usuarios u
                ON c.id_usuario = u.id_usuario
            WHERE c.id_compra = %s
        """

        cursor.execute(sql_compra, (id_compra,))
        fila = cursor.fetchone()

        if fila is None:
            return jsonify({
                'mensaje': 'Compra no encontrada'
            }), 404

        sql_detalles = """
            SELECT
                dc.id_detalle_compra,
                dc.id_materia_prima,
                m.nombre,
                dc.cantidad,
                m.unidad_medida,
                dc.costo_unitario,
                dc.subtotal
            FROM detalle_compras dc
            INNER JOIN materias_primas m
                ON dc.id_materia_prima = m.id_materia_prima
            WHERE dc.id_compra = %s
        """

        cursor.execute(sql_detalles, (id_compra,))
        resultados = cursor.fetchall()

        detalles = []

        for detalle in resultados:
            detalles.append({
                'id_detalle_compra': detalle[0],
                'id_materia_prima': detalle[1],
                'materia_prima': detalle[2],
                'cantidad': float(detalle[3]),
                'unidad_medida': detalle[4],
                'costo_unitario': float(detalle[5]),
                'subtotal': float(detalle[6])
            })

        compra = {
            'id_compra': fila[0],
            'id_proveedor': fila[1],
            'proveedor': fila[2],
            'id_usuario': fila[3],
            'usuario': fila[4],
            'fecha_compra': str(fila[5]),
            'fecha_recepcion': str(fila[6]) if fila[6] else None,
            'total': float(fila[7]),
            'estado': fila[8],
            'observaciones': fila[9],
            'detalles': detalles
        }

        return jsonify(compra), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar la compra',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# REGISTRAR COMPRA
# ==========================================

@compras_bp.route('/', methods=['POST'])
def registrar_compra():

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos en formato JSON'
            }), 400

        id_proveedor = datos.get('id_proveedor')
        id_usuario = datos.get('id_usuario')
        observaciones = datos.get('observaciones')
        detalles = datos.get('detalles')

        if not id_proveedor or not id_usuario or not detalles:
            return jsonify({
                'mensaje': 'El proveedor, usuario y detalles son obligatorios'
            }), 400

        if not isinstance(detalles, list) or len(detalles) == 0:
            return jsonify({
                'mensaje': 'La compra debe contener al menos un producto'
            }), 400

        # Validar y calcular los detalles antes de insertar
        detalles_validados = []
        total = Decimal('0.00')

        for detalle in detalles:

            if not isinstance(detalle, dict):
                return jsonify({
                    'mensaje': 'Cada detalle debe ser un objeto JSON'
                }), 400

            id_materia = detalle.get('id_materia_prima')
            cantidad = detalle.get('cantidad')
            costo = detalle.get('costo_unitario')

            if id_materia is None or cantidad is None or costo is None:
                return jsonify({
                    'mensaje': 'Cada detalle requiere materia prima, cantidad y costo unitario'
                }), 400

            try:
                cantidad = Decimal(str(cantidad))
                costo = Decimal(str(costo))
            except (InvalidOperation, ValueError):
                return jsonify({
                    'mensaje': 'La cantidad y el costo deben ser numéricos'
                }), 400

            if (
                not cantidad.is_finite()
                or not costo.is_finite()
                or cantidad <= 0
                or costo < 0
            ):
                return jsonify({
                    'mensaje': 'La cantidad debe ser mayor a cero y el costo no puede ser negativo'
                }), 400

            subtotal = (cantidad * costo).quantize(Decimal('0.01'))
            total += subtotal

            detalles_validados.append({
                'id_materia_prima': id_materia,
                'cantidad': cantidad,
                'costo_unitario': costo,
                'subtotal': subtotal
            })

        cursor = mysql.connection.cursor()

        # Verificar proveedor
        cursor.execute(
            """
            SELECT id_proveedor
            FROM proveedores
            WHERE id_proveedor = %s AND estado = 1
            """,
            (id_proveedor,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                'mensaje': 'El proveedor no existe o está inactivo'
            }), 400

        # Verificar usuario
        cursor.execute(
            """
            SELECT id_usuario
            FROM usuarios
            WHERE id_usuario = %s AND estado = 1
            """,
            (id_usuario,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                'mensaje': 'El usuario no existe o está inactivo'
            }), 400

        # Verificar materias primas
        for detalle in detalles_validados:

            cursor.execute(
                """
                SELECT id_materia_prima
                FROM materias_primas
                WHERE id_materia_prima = %s AND estado = 1
                """,
                (detalle['id_materia_prima'],)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    'mensaje': 'Una de las materias primas no existe o está inactiva',
                    'id_materia_prima': detalle['id_materia_prima']
                }), 400

        # Registrar encabezado
        cursor.execute(
            """
            INSERT INTO compras
            (
                id_proveedor,
                id_usuario,
                fecha_compra,
                total,
                estado,
                observaciones
            )
            VALUES (%s, %s, NOW(), %s, 'Pendiente', %s)
            """,
            (
                id_proveedor,
                id_usuario,
                total,
                observaciones
            )
        )

        id_compra = cursor.lastrowid

        # Registrar detalles
        for detalle in detalles_validados:

            cursor.execute(
                """
                INSERT INTO detalle_compras
                (
                    id_compra,
                    id_materia_prima,
                    cantidad,
                    costo_unitario,
                    subtotal
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    id_compra,
                    detalle['id_materia_prima'],
                    detalle['cantidad'],
                    detalle['costo_unitario'],
                    detalle['subtotal']
                )
            )

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Compra registrada correctamente',
            'id_compra': id_compra,
            'total': float(total),
            'estado': 'Pendiente'
        }), 201

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al registrar la compra',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# RECIBIR COMPRA Y ACTUALIZAR INVENTARIO
# ==========================================

@compras_bp.route('/<int:id_compra>/recibir', methods=['PATCH'])
def recibir_compra(id_compra):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        # Bloquear compra durante la operación
        cursor.execute(
            """
            SELECT estado
            FROM compras
            WHERE id_compra = %s
            FOR UPDATE
            """,
            (id_compra,)
        )

        compra = cursor.fetchone()

        if compra is None:
            return jsonify({
                'mensaje': 'Compra no encontrada'
            }), 404

        if compra[0] == 'Recibida':
            return jsonify({
                'mensaje': 'Esta compra ya fue recibida'
            }), 400

        if compra[0] == 'Cancelada':
            return jsonify({
                'mensaje': 'No se puede recibir una compra cancelada'
            }), 400

        # Obtener los detalles de la compra
        cursor.execute(
            """
            SELECT
                id_detalle_compra,
                id_materia_prima,
                cantidad,
                costo_unitario
            FROM detalle_compras
            WHERE id_compra = %s
            """,
            (id_compra,)
        )

        detalles = cursor.fetchall()

        if not detalles:
            return jsonify({
                'mensaje': 'La compra no tiene detalles registrados'
            }), 400

        for detalle in detalles:

            id_detalle = detalle[0]
            id_materia = detalle[1]
            cantidad = detalle[2]
            costo = detalle[3]

            # Aumentar existencias y actualizar costo unitario
            cursor.execute(
                """
                UPDATE materias_primas
                SET stock_actual = stock_actual + %s,
                    costo_unitario = %s
                WHERE id_materia_prima = %s
                """,
                (cantidad, costo, id_materia)
            )

            if cursor.rowcount == 0:
                raise Exception(
                    f'No se encontró la materia prima {id_materia}'
                )

            # Registrar movimiento de entrada
            cursor.execute(
                """
                INSERT INTO movimientos_inventario
                (
                    id_materia_prima,
                    id_detalle_compra,
                    tipo_movimiento,
                    cantidad,
                    motivo,
                    fecha_movimiento
                )
                VALUES (%s, %s, 'EntradaCompra', %s,
                        'Entrada por compra recibida', NOW())
                """,
                (id_materia, id_detalle, cantidad)
            )

        # Cambiar estado de la compra
        cursor.execute(
            """
            UPDATE compras
            SET estado = 'Recibida',
                fecha_recepcion = NOW()
            WHERE id_compra = %s
            """,
            (id_compra,)
        )

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Compra recibida correctamente',
            'id_compra': id_compra,
            'estado': 'Recibida',
            'mensaje_inventario': 'Las existencias fueron actualizadas'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al recibir la compra',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# CANCELAR COMPRA
# ==========================================

@compras_bp.route('/<int:id_compra>/cancelar', methods=['PATCH'])
def cancelar_compra(id_compra):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            SELECT estado
            FROM compras
            WHERE id_compra = %s
            FOR UPDATE
            """,
            (id_compra,)
        )

        compra = cursor.fetchone()

        if compra is None:
            return jsonify({
                'mensaje': 'Compra no encontrada'
            }), 404

        if compra[0] == 'Recibida':
            return jsonify({
                'mensaje': 'No se puede cancelar una compra que ya fue recibida'
            }), 400

        if compra[0] == 'Cancelada':
            return jsonify({
                'mensaje': 'La compra ya se encuentra cancelada'
            }), 400

        cursor.execute(
            """
            UPDATE compras
            SET estado = 'Cancelada'
            WHERE id_compra = %s
            """,
            (id_compra,)
        )

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Compra cancelada correctamente',
            'id_compra': id_compra,
            'estado': 'Cancelada'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al cancelar la compra',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()
