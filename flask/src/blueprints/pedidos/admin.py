
from flask import jsonify, request
from database import mysql

from .routes import pedidos_bp


# ==========================================
# GET: TODOS LOS PEDIDOS
# ==========================================

@pedidos_bp.route('/pedidos/', methods=['GET'])
def listar_pedidos_administracion():

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                p.id_pedido,
                p.id_cliente,
                u.nombre,
                p.fecha_pedido,
                p.tipo_entrega,
                p.subtotal,
                p.porcentaje_descuento,
                p.monto_descuento,
                p.costo_entrega,
                p.total,
                p.estado,
                p.observaciones

            FROM pedidos p

            LEFT JOIN clientes c
                ON p.id_cliente = c.id_cliente

            LEFT JOIN usuarios u
                ON c.id_usuario = u.id_usuario

            ORDER BY
                p.fecha_pedido DESC,
                p.id_pedido DESC
        """)

        pedidos = []

        for fila in cursor.fetchall():

            pedidos.append({
                'id_pedido': fila[0],
                'id_cliente': fila[1],
                'cliente': fila[2],
                'fecha_pedido': str(fila[3]) if fila[3] else None,
                'tipo_entrega': fila[4],
                'subtotal': float(fila[5]),
                'porcentaje_descuento': float(fila[6]),
                'monto_descuento': float(fila[7]),
                'costo_entrega': float(fila[8]),
                'total': float(fila[9]),
                'estado': fila[10],
                'observaciones': fila[11]
            })

        return jsonify(pedidos), 200

    except Exception as error:

        return jsonify({
            'mensaje': 'No se pudieron consultar los pedidos.',
            'error': str(error)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: CLIENTES PARA PEDIDOS
# ==========================================

@pedidos_bp.route('/pedidos/clientes', methods=['GET'])
def listar_clientes_para_pedidos():

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                c.id_cliente,
                u.nombre,
                u.correo,
                c.estado_acreditacion,

                CASE
                    WHEN c.estado_acreditacion = 'Validada'
                         AND d.estado = 1
                    THEN d.porcentaje
                    ELSE 0
                END

            FROM clientes c

            INNER JOIN usuarios u
                ON c.id_usuario = u.id_usuario

            LEFT JOIN descuentos d
                ON c.id_descuento = d.id_descuento

            WHERE u.estado = 1

            ORDER BY u.nombre
        """)

        clientes = []

        for fila in cursor.fetchall():

            clientes.append({
                'id_cliente': fila[0],
                'nombre': fila[1],
                'correo': fila[2],
                'estado_acreditacion': fila[3],
                'porcentaje_descuento': float(fila[4] or 0)
            })

        return jsonify(clientes), 200

    except Exception as error:

        return jsonify({
            'mensaje': 'No se pudieron consultar los clientes.',
            'error': str(error)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: DIRECCIONES DE UN CLIENTE
# ==========================================

@pedidos_bp.route(
    '/direcciones/cliente/<int:id_cliente>',
    methods=['GET']
)
def consultar_direcciones(id_cliente):

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT
                id_direccion,
                calle,
                numero,
                colonia,
                codigo_postal,
                referencias

            FROM direcciones

            WHERE id_cliente = %s

            ORDER BY id_direccion DESC
        """, (id_cliente,))

        direcciones = []

        for fila in cursor.fetchall():

            direcciones.append({
                'id_direccion': fila[0],
                'calle': fila[1],
                'numero': fila[2],
                'colonia': fila[3],
                'codigo_postal': fila[4],
                'referencias': fila[5]
            })

        return jsonify(direcciones), 200

    except Exception as error:

        return jsonify({
            'mensaje': 'No se pudieron consultar las direcciones.',
            'error': str(error)
        }), 500

    finally:
        cursor.close()


# ==========================================
# POST: REGISTRAR DIRECCIÓN
# ==========================================

@pedidos_bp.route(
    '/direcciones/cliente/<int:id_cliente>',
    methods=['POST']
)
def agregar_direccion(id_cliente):

    datos = request.get_json(silent=True) or {}

    calle = str(datos.get('calle') or '').strip()
    numero = str(datos.get('numero') or '').strip()
    colonia = str(datos.get('colonia') or '').strip()
    codigo_postal = str(datos.get('codigo_postal') or '').strip()
    referencias = str(datos.get('referencias') or '').strip()

    if not calle or not colonia:
        return jsonify({
            'mensaje': 'La calle y colonia son obligatorias.'
        }), 400

    if (
        len(calle) > 120 or
        len(numero) > 20 or
        len(colonia) > 100 or
        len(codigo_postal) > 10 or
        len(referencias) > 255
    ):
        return jsonify({
            'mensaje': 'Uno de los campos supera la longitud permitida.'
        }), 400

    cursor = mysql.connection.cursor()

    try:

        cursor.execute("""
            SELECT id_cliente
            FROM clientes
            WHERE id_cliente = %s
        """, (id_cliente,))

        if not cursor.fetchone():

            return jsonify({
                'mensaje': 'El cliente no existe.'
            }), 404

        cursor.execute("""
            INSERT INTO direcciones (
                id_cliente,
                calle,
                numero,
                colonia,
                codigo_postal,
                referencias
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            id_cliente,
            calle,
            numero or None,
            colonia,
            codigo_postal or None,
            referencias or None
        ))

        nuevo_id = cursor.lastrowid

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Dirección registrada correctamente.',
            'id_direccion': nuevo_id
        }), 201

    except Exception as error:

        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'No se pudo registrar la dirección.',
            'error': str(error)
        }), 500

    finally:
        cursor.close()
