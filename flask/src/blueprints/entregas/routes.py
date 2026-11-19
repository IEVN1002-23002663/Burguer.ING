
from flask import Blueprint, request, jsonify
from database import mysql


entregas_bp = Blueprint(
    'entregas',
    __name__,
    url_prefix='/api/entregas'
)


# ==========================================
# GET: Consultar todas las entregas
# ==========================================

@entregas_bp.route('/', methods=['GET'])
def obtener_entregas():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                e.id_entrega,
                e.id_pedido,
                e.repartidor,
                e.estado,
                e.fecha_salida,
                e.fecha_entrega,
                e.observaciones,
                p.id_cliente,
                p.total,
                p.estado AS estado_pedido
            FROM entregas e
            INNER JOIN pedidos p
                ON e.id_pedido = p.id_pedido
            ORDER BY e.id_entrega DESC
        """)

        columnas = [col[0] for col in cursor.description]
        entregas = []

        for fila in cursor.fetchall():
            entrega = dict(zip(columnas, fila))

            if entrega['fecha_salida']:
                entrega['fecha_salida'] = str(
                    entrega['fecha_salida']
                )

            if entrega['fecha_entrega']:
                entrega['fecha_entrega'] = str(
                    entrega['fecha_entrega']
                )

            entrega['total'] = float(entrega['total'])
            entregas.append(entrega)

        return jsonify(entregas), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar las entregas.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Consultar una entrega
# ==========================================

@entregas_bp.route('/<int:id_entrega>', methods=['GET'])
def obtener_entrega(id_entrega):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                e.id_entrega,
                e.id_pedido,
                e.repartidor,
                e.estado,
                e.fecha_salida,
                e.fecha_entrega,
                e.observaciones,
                p.id_cliente,
                p.tipo_entrega,
                p.total,
                p.estado AS estado_pedido
            FROM entregas e
            INNER JOIN pedidos p
                ON e.id_pedido = p.id_pedido
            WHERE e.id_entrega = %s
        """, (id_entrega,))

        fila = cursor.fetchone()

        if not fila:
            return jsonify({
                'mensaje': 'La entrega no existe.'
            }), 404

        columnas = [col[0] for col in cursor.description]
        entrega = dict(zip(columnas, fila))

        if entrega['fecha_salida']:
            entrega['fecha_salida'] = str(
                entrega['fecha_salida']
            )

        if entrega['fecha_entrega']:
            entrega['fecha_entrega'] = str(
                entrega['fecha_entrega']
            )

        entrega['total'] = float(entrega['total'])

        return jsonify(entrega), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar la entrega.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# POST: Crear entrega y asignar repartidor
# ==========================================

@entregas_bp.route('/', methods=['POST'])
def crear_entrega():
    datos = request.get_json()

    if not datos:
        return jsonify({
            'mensaje': 'Debes enviar los datos de la entrega.'
        }), 400

    id_pedido = datos.get('id_pedido')
    repartidor = datos.get('repartidor')
    observaciones = datos.get('observaciones')

    if not id_pedido or not isinstance(repartidor, str) or not repartidor.strip():
        return jsonify({
            'mensaje': 'El pedido y el nombre del repartidor son obligatorios.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        # Bloquear el pedido para evitar entregas duplicadas.
        cursor.execute("""
            SELECT
                id_pedido,
                tipo_entrega,
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

        tipo_entrega = pedido[1]
        estado_pedido = pedido[2]

        if tipo_entrega != 'Domicilio':
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'Solo se pueden registrar entregas para pedidos a domicilio.'
            }), 400

        if estado_pedido in ('Cancelado', 'Anulado', 'Entregado'):
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El pedido no puede generar una nueva entrega.'
            }), 400

        # Verificar que la producción esté completada.
        cursor.execute("""
            SELECT estado
            FROM producciones
            WHERE id_pedido = %s
            FOR UPDATE
        """, (id_pedido,))

        produccion = cursor.fetchone()

        if not produccion or produccion[0] != 'Completada':
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El pedido debe tener su producción completada antes de crear la entrega.'
            }), 400

        # Evitar más de una entrega para el mismo pedido.
        cursor.execute("""
            SELECT id_entrega
            FROM entregas
            WHERE id_pedido = %s
        """, (id_pedido,))

        if cursor.fetchone():
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'Este pedido ya tiene una entrega registrada.'
            }), 409

        cursor.execute("""
            INSERT INTO entregas (
                id_pedido,
                repartidor,
                estado,
                observaciones
            )
            VALUES (%s, %s, 'Pendiente', %s)
        """, (
            id_pedido,
            repartidor.strip(),
            observaciones
        ))

        id_entrega = cursor.lastrowid

        cursor.execute("""
            INSERT INTO historial_pedidos (
                id_pedido,
                id_usuario,
                estado,
                comentario,
                fecha_cambio
            )
            VALUES (
                %s, NULL, 'Pendiente',
                'Entrega asignada al repartidor',
                NOW()
            )
        """, (id_pedido,))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Entrega registrada correctamente.',
            'id_entrega': id_entrega,
            'id_pedido': id_pedido,
            'repartidor': repartidor.strip(),
            'estado': 'Pendiente'
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo registrar la entrega.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# PATCH: Registrar salida del repartidor
# ==========================================

@entregas_bp.route(
    '/<int:id_entrega>/salida',
    methods=['PATCH']
)
def registrar_salida(id_entrega):
    datos = request.get_json() or {}
    observaciones = datos.get('observaciones')

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_pedido, estado
            FROM entregas
            WHERE id_entrega = %s
            FOR UPDATE
        """, (id_entrega,))

        entrega = cursor.fetchone()

        if not entrega:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'La entrega no existe.'
            }), 404

        id_pedido = entrega[0]
        estado = entrega[1]

        if estado != 'Pendiente':
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'La entrega no está pendiente o ya salió.'
            }), 400

        cursor.execute("""
            UPDATE entregas
            SET estado = 'En camino',
                fecha_salida = NOW(),
                observaciones = COALESCE(%s, observaciones)
            WHERE id_entrega = %s
        """, (observaciones, id_entrega))

        cursor.execute("""
            UPDATE pedidos
            SET estado = 'En camino'
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
                %s, NULL, 'En camino',
                'El pedido salió para su entrega',
                NOW()
            )
        """, (id_pedido,))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Salida registrada correctamente.',
            'id_entrega': id_entrega,
            'estado': 'En camino'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo registrar la salida.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# PATCH: Confirmar entrega
# ==========================================

@entregas_bp.route(
    '/<int:id_entrega>/completar',
    methods=['PATCH']
)
def completar_entrega(id_entrega):
    datos = request.get_json() or {}
    observaciones = datos.get('observaciones')

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_pedido, estado
            FROM entregas
            WHERE id_entrega = %s
            FOR UPDATE
        """, (id_entrega,))

        entrega = cursor.fetchone()

        if not entrega:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'La entrega no existe.'
            }), 404

        id_pedido = entrega[0]
        estado = entrega[1]

        if estado == 'Entregada':
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'La entrega ya fue completada.'
            }), 409

        if estado != 'En camino':
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'Primero debes registrar la salida del repartidor.'
            }), 400

        cursor.execute("""
            UPDATE entregas
            SET estado = 'Entregada',
                fecha_entrega = NOW(),
                observaciones = COALESCE(%s, observaciones)
            WHERE id_entrega = %s
        """, (observaciones, id_entrega))

        cursor.execute("""
            UPDATE pedidos
            SET estado = 'Entregado'
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
                %s, NULL, 'Entregado',
                'El pedido fue entregado al cliente',
                NOW()
            )
        """, (id_pedido,))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Entrega completada correctamente.',
            'id_entrega': id_entrega,
            'estado': 'Entregada'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo completar la entrega.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Consultar historial de un pedido
# ==========================================

@entregas_bp.route(
    '/historial/<int:id_pedido>',
    methods=['GET']
)
def obtener_historial_pedido(id_pedido):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_pedido
            FROM pedidos
            WHERE id_pedido = %s
        """, (id_pedido,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'El pedido no existe.'
            }), 404

        cursor.execute("""
            SELECT
                h.id_historial,
                h.id_pedido,
                h.id_usuario,
                u.nombre AS usuario,
                h.estado,
                h.comentario,
                h.fecha_cambio
            FROM historial_pedidos h
            LEFT JOIN usuarios u
                ON h.id_usuario = u.id_usuario
            WHERE h.id_pedido = %s
            ORDER BY h.fecha_cambio ASC, h.id_historial ASC
        """, (id_pedido,))

        columnas = [col[0] for col in cursor.description]
        historial = []

        for fila in cursor.fetchall():
            registro = dict(zip(columnas, fila))

            if registro['fecha_cambio']:
                registro['fecha_cambio'] = str(
                    registro['fecha_cambio']
                )

            historial.append(registro)

        return jsonify({
            'id_pedido': id_pedido,
            'historial': historial
        }), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar el historial.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()
