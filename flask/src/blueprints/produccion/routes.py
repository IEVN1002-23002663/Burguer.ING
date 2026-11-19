
from flask import Blueprint, request, jsonify
from database import mysql
from decimal import Decimal


produccion_bp = Blueprint(
    'produccion',
    __name__,
    url_prefix='/api/produccion'
)


# ==========================================
# GET: Consultar todas las producciones
# ==========================================

@produccion_bp.route('/', methods=['GET'])
def obtener_producciones():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                p.id_produccion,
                p.id_pedido,
                p.id_usuario,
                u.nombre AS usuario,
                p.fecha_inicio,
                p.fecha_fin,
                p.estado,
                p.inventario_descontado
            FROM producciones p
            LEFT JOIN usuarios u
                ON p.id_usuario = u.id_usuario
            ORDER BY p.fecha_inicio DESC
        """)

        columnas = [col[0] for col in cursor.description]
        producciones = []

        for fila in cursor.fetchall():
            registro = dict(zip(columnas, fila))

            if registro['fecha_inicio']:
                registro['fecha_inicio'] = str(registro['fecha_inicio'])

            if registro['fecha_fin']:
                registro['fecha_fin'] = str(registro['fecha_fin'])

            registro['inventario_descontado'] = bool(
                registro['inventario_descontado']
            )

            producciones.append(registro)

        return jsonify(producciones), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar las producciones.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Consultar una producción
# ==========================================

@produccion_bp.route('/<int:id_produccion>', methods=['GET'])
def obtener_produccion(id_produccion):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                p.id_produccion,
                p.id_pedido,
                p.id_usuario,
                u.nombre AS usuario,
                p.fecha_inicio,
                p.fecha_fin,
                p.estado,
                p.inventario_descontado
            FROM producciones p
            LEFT JOIN usuarios u
                ON p.id_usuario = u.id_usuario
            WHERE p.id_produccion = %s
        """, (id_produccion,))

        fila = cursor.fetchone()

        if not fila:
            return jsonify({
                'mensaje': 'La producción no existe.'
            }), 404

        columnas = [col[0] for col in cursor.description]
        produccion = dict(zip(columnas, fila))

        if produccion['fecha_inicio']:
            produccion['fecha_inicio'] = str(
                produccion['fecha_inicio']
            )

        if produccion['fecha_fin']:
            produccion['fecha_fin'] = str(
                produccion['fecha_fin']
            )

        produccion['inventario_descontado'] = bool(
            produccion['inventario_descontado']
        )

        cursor.execute("""
            SELECT
                dp.id_detalle_produccion,
                dp.id_detalle_pedido,
                dp.cantidad_preparada,
                dp.estado,
                dpe.id_producto,
                dpe.nombre_producto
            FROM detalle_producciones dp
            INNER JOIN detalle_pedidos dpe
                ON dp.id_detalle_pedido = dpe.id_detalle_pedido
            WHERE dp.id_produccion = %s
            ORDER BY dp.id_detalle_produccion
        """, (id_produccion,))

        columnas_detalle = [
            col[0] for col in cursor.description
        ]

        detalles = []

        for detalle in cursor.fetchall():
            registro = dict(zip(columnas_detalle, detalle))
            registro['cantidad_preparada'] = float(
                registro['cantidad_preparada']
            )
            detalles.append(registro)

        produccion['detalles'] = detalles

        return jsonify(produccion), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar la producción.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# POST: Iniciar producción de un pedido
# ==========================================

@produccion_bp.route('/iniciar', methods=['POST'])
def iniciar_produccion():
    datos = request.get_json()

    if not datos:
        return jsonify({
            'mensaje': 'Debes enviar los datos.'
        }), 400

    id_pedido = datos.get('id_pedido')
    id_usuario = datos.get('id_usuario')

    if not id_pedido or not id_usuario:
        return jsonify({
            'mensaje': 'Debes indicar el pedido y el usuario responsable.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        # Bloquear el pedido para evitar iniciar dos producciones
        # simultáneamente para el mismo pedido.
        cursor.execute("""
            SELECT id_pedido
            FROM pedidos
            WHERE id_pedido = %s
            FOR UPDATE
        """, (id_pedido,))

        if not cursor.fetchone():
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El pedido no existe.'
            }), 404

        # Validar usuario responsable.
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

        # Verificar que el pedido no tenga producción previa.
        cursor.execute("""
            SELECT id_produccion
            FROM producciones
            WHERE id_pedido = %s
        """, (id_pedido,))

        if cursor.fetchone():
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'Este pedido ya tiene una producción registrada.'
            }), 409

        # Consultar los productos solicitados.
        cursor.execute("""
            SELECT
                id_detalle_pedido,
                id_producto,
                cantidad,
                nombre_producto
            FROM detalle_pedidos
            WHERE id_pedido = %s
            FOR UPDATE
        """, (id_pedido,))

        detalles_pedido = cursor.fetchall()

        if not detalles_pedido:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El pedido no contiene productos.'
            }), 400

        # Preparar los consumos necesarios por cada línea del pedido.
        consumos = []

        for detalle in detalles_pedido:
            id_detalle_pedido = detalle[0]
            id_producto = detalle[1]
            cantidad_pedida = Decimal(str(detalle[2]))

            # Consultar receta del producto.
            cursor.execute("""
                SELECT id_receta, rendimiento
                FROM recetas
                WHERE id_producto = %s
            """, (id_producto,))

            receta = cursor.fetchone()

            if not receta:
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': (
                        f'El producto {detalle[3]} no tiene una receta registrada.'
                    )
                }), 400

            id_receta = receta[0]
            rendimiento = Decimal(str(receta[1]))

            if rendimiento <= 0:
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': 'Una receta tiene un rendimiento no válido.'
                }), 400

            # Consultar ingredientes de la receta.
            cursor.execute("""
                SELECT
                    id_materia_prima,
                    cantidad
                FROM detalle_recetas
                WHERE id_receta = %s
            """, (id_receta,))

            ingredientes = cursor.fetchall()

            if not ingredientes:
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': (
                        f'La receta del producto {detalle[3]} no tiene ingredientes.'
                    )
                }), 400

            for ingrediente in ingredientes:
                id_materia_prima = ingrediente[0]
                cantidad_receta = Decimal(str(ingrediente[1]))

                cantidad_necesaria = (
                    cantidad_receta * cantidad_pedida / rendimiento
                )

                consumos.append({
                    'id_detalle_pedido': id_detalle_pedido,
                    'id_materia_prima': id_materia_prima,
                    'cantidad': cantidad_necesaria
                })

        # Agrupar consumos por materia prima para comprobar existencias.
        totales = {}

        for consumo in consumos:
            id_materia = consumo['id_materia_prima']

            if id_materia not in totales:
                totales[id_materia] = Decimal('0')

            totales[id_materia] += consumo['cantidad']

        # Bloquear y validar cada materia prima.
        for id_materia, cantidad_total in totales.items():
            cursor.execute("""
                SELECT nombre, stock_actual, estado
                FROM materias_primas
                WHERE id_materia_prima = %s
                FOR UPDATE
            """, (id_materia,))

            materia = cursor.fetchone()

            if not materia:
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': f'La materia prima {id_materia} no existe.'
                }), 400

            nombre_materia = materia[0]
            stock_actual = Decimal(str(materia[1]))
            estado = materia[2]

            if estado != 1:
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': f'{nombre_materia} está inactiva.'
                }), 400

            if stock_actual < cantidad_total:
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': (
                        f'Inventario insuficiente de {nombre_materia}. '
                        f'Se necesitan {cantidad_total} y hay {stock_actual}.'
                    )
                }), 400

        # Crear la producción.
        cursor.execute("""
            INSERT INTO producciones (
                id_pedido,
                id_usuario,
                fecha_inicio,
                estado,
                inventario_descontado
            )
            VALUES (%s, %s, NOW(), 'En proceso', 1)
        """, (id_pedido, id_usuario))

        id_produccion = cursor.lastrowid

        # Crear un detalle de producción por cada línea del pedido.
        detalles_produccion = {}

        for detalle in detalles_pedido:
            id_detalle_pedido = detalle[0]
            cantidad_pedida = detalle[2]

            cursor.execute("""
                INSERT INTO detalle_producciones (
                    id_produccion,
                    id_detalle_pedido,
                    cantidad_preparada,
                    estado
                )
                VALUES (%s, %s, %s, 'En proceso')
            """, (
                id_produccion,
                id_detalle_pedido,
                cantidad_pedida
            ))

            detalles_produccion[id_detalle_pedido] = cursor.lastrowid

        # Descontar ingredientes y registrar movimientos.
        for consumo in consumos:
            id_materia = consumo['id_materia_prima']
            cantidad = consumo['cantidad']
            id_detalle_produccion = detalles_produccion[
                consumo['id_detalle_pedido']
            ]

            cursor.execute("""
                UPDATE materias_primas
                SET stock_actual = stock_actual - %s
                WHERE id_materia_prima = %s
                  AND stock_actual >= %s
            """, (
                cantidad,
                id_materia,
                cantidad
            ))

            if cursor.rowcount != 1:
                raise Exception(
                    'No se pudo descontar una materia prima. '
                    'Verifica las existencias.'
                )

            cursor.execute("""
                INSERT INTO movimientos_inventario (
                    id_materia_prima,
                    id_usuario,
                    id_detalle_produccion,
                    tipo_movimiento,
                    cantidad,
                    motivo
                )
                VALUES (%s, %s, %s, 'SalidaProduccion', %s, %s)
            """, (
                id_materia,
                id_usuario,
                id_detalle_produccion,
                cantidad,
                f'Consumo para producción del pedido {id_pedido}'
            ))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Producción iniciada correctamente.',
            'id_produccion': id_produccion,
            'id_pedido': id_pedido,
            'estado': 'En proceso',
            'inventario_descontado': True
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo iniciar la producción.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# PATCH: Completar producción
# ==========================================

@produccion_bp.route(
    '/<int:id_produccion>/completar',
    methods=['PATCH']
)
def completar_produccion(id_produccion):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT estado, inventario_descontado
            FROM producciones
            WHERE id_produccion = %s
            FOR UPDATE
        """, (id_produccion,))

        produccion = cursor.fetchone()

        if not produccion:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'La producción no existe.'
            }), 404

        estado = produccion[0]
        inventario_descontado = produccion[1]

        if estado == 'Completada':
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'La producción ya está completada.'
            }), 409

        if estado != 'En proceso':
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'La producción no se encuentra en proceso.'
            }), 400

        if not inventario_descontado:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'No se ha descontado el inventario.'
            }), 400

        cursor.execute("""
            UPDATE producciones
            SET estado = 'Completada',
                fecha_fin = NOW()
            WHERE id_produccion = %s
        """, (id_produccion,))

        cursor.execute("""
            UPDATE detalle_producciones
            SET estado = 'Completada'
            WHERE id_produccion = %s
        """, (id_produccion,))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Producción completada correctamente.',
            'id_produccion': id_produccion,
            'estado': 'Completada'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo completar la producción.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()
