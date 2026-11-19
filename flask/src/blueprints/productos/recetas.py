
from flask import request, jsonify
from database import mysql
from decimal import Decimal, InvalidOperation
from . import productos_bp


def convertir_decimal(valor):
    try:
        numero = Decimal(str(valor))

        if not numero.is_finite():
            return None

        return numero
    except (InvalidOperation, TypeError, ValueError):
        return None


def validar_ingredientes(ingredientes):
    if not isinstance(ingredientes, list) or not ingredientes:
        return False, 'Debes enviar al menos un ingrediente.'

    ids = set()

    for ingrediente in ingredientes:
        if not isinstance(ingrediente, dict):
            return False, 'Cada ingrediente debe ser un objeto.'

        id_materia = ingrediente.get('id_materia_prima')
        cantidad = convertir_decimal(ingrediente.get('cantidad'))

        if not id_materia or cantidad is None or cantidad <= 0:
            return False, 'Cada ingrediente necesita una materia prima y una cantidad mayor que cero.'

        if id_materia in ids:
            return False, 'No repitas una materia prima en la misma receta.'

        ids.add(id_materia)

        ingrediente['cantidad_validada'] = cantidad

    return True, None


# ==========================================
# GET: Consultar todas las recetas
# ==========================================

@productos_bp.route('/recetas/', methods=['GET'])
def obtener_recetas():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                r.id_receta,
                r.id_producto,
                p.nombre AS producto,
                r.instrucciones,
                r.rendimiento
            FROM recetas r
            INNER JOIN productos p
                ON r.id_producto = p.id_producto
            ORDER BY p.nombre
        """)

        columnas = [col[0] for col in cursor.description]
        filas = cursor.fetchall()

        recetas = []

        for fila in filas:
            receta = dict(zip(columnas, fila))

            cursor.execute("""
                SELECT
                    dr.id_detalle_receta,
                    dr.id_materia_prima,
                    mp.nombre AS materia_prima,
                    mp.unidad_medida,
                    dr.cantidad
                FROM detalle_recetas dr
                INNER JOIN materias_primas mp
                    ON dr.id_materia_prima = mp.id_materia_prima
                WHERE dr.id_receta = %s
                ORDER BY mp.nombre
            """, (receta['id_receta'],))

            columnas_detalle = [
                col[0] for col in cursor.description
            ]

            receta['ingredientes'] = []

            for detalle in cursor.fetchall():
                ingrediente = dict(
                    zip(columnas_detalle, detalle)
                )
                ingrediente['cantidad'] = float(
                    ingrediente['cantidad']
                )
                receta['ingredientes'].append(ingrediente)

            recetas.append(receta)

        return jsonify(recetas), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar las recetas.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Consultar receta por producto
# ==========================================

@productos_bp.route(
    '/recetas/producto/<int:id_producto>',
    methods=['GET']
)
def obtener_receta_producto(id_producto):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                r.id_receta,
                r.id_producto,
                p.nombre AS producto,
                r.instrucciones,
                r.rendimiento
            FROM recetas r
            INNER JOIN productos p
                ON r.id_producto = p.id_producto
            WHERE r.id_producto = %s
        """, (id_producto,))

        fila = cursor.fetchone()

        if not fila:
            return jsonify({
                'mensaje': 'Este producto todavía no tiene una receta.'
            }), 404

        columnas = [col[0] for col in cursor.description]
        receta = dict(zip(columnas, fila))

        cursor.execute("""
            SELECT
                dr.id_detalle_receta,
                dr.id_materia_prima,
                mp.nombre AS materia_prima,
                mp.unidad_medida,
                dr.cantidad
            FROM detalle_recetas dr
            INNER JOIN materias_primas mp
                ON dr.id_materia_prima = mp.id_materia_prima
            WHERE dr.id_receta = %s
            ORDER BY mp.nombre
        """, (receta['id_receta'],))

        columnas_detalle = [
            col[0] for col in cursor.description
        ]

        ingredientes = []

        for detalle in cursor.fetchall():
            ingrediente = dict(zip(columnas_detalle, detalle))
            ingrediente['cantidad'] = float(
                ingrediente['cantidad']
            )
            ingredientes.append(ingrediente)

        receta['ingredientes'] = ingredientes

        return jsonify(receta), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar la receta.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# POST: Crear receta con ingredientes
# ==========================================

@productos_bp.route('/recetas/', methods=['POST'])
def crear_receta():
    datos = request.get_json()

    if not datos:
        return jsonify({'mensaje': 'Debes enviar los datos.'}), 400

    id_producto = datos.get('id_producto')
    instrucciones = datos.get('instrucciones')
    rendimiento = datos.get('rendimiento', 1)
    ingredientes = datos.get('ingredientes')

    if not id_producto:
        return jsonify({
            'mensaje': 'Debes indicar el producto.'
        }), 400

    if not isinstance(rendimiento, int) or isinstance(rendimiento, bool) or rendimiento <= 0:
        return jsonify({
            'mensaje': 'El rendimiento debe ser un entero mayor que cero.'
        }), 400

    valido, mensaje = validar_ingredientes(ingredientes)

    if not valido:
        return jsonify({'mensaje': mensaje}), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_producto
            FROM productos
            WHERE id_producto = %s
        """, (id_producto,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'El producto no existe.'
            }), 404

        cursor.execute("""
            SELECT id_receta
            FROM recetas
            WHERE id_producto = %s
        """, (id_producto,))

        if cursor.fetchone():
            return jsonify({
                'mensaje': 'Este producto ya tiene una receta.'
            }), 409

        # Validar que todas las materias primas existan y estén activas.
        for ingrediente in ingredientes:
            cursor.execute("""
                SELECT id_materia_prima
                FROM materias_primas
                WHERE id_materia_prima = %s
                  AND estado = 1
            """, (ingrediente['id_materia_prima'],))

            if not cursor.fetchone():
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': (
                        'La materia prima '
                        f"{ingrediente['id_materia_prima']} "
                        'no existe o está inactiva.'
                    )
                }), 400

        cursor.execute("""
            INSERT INTO recetas (
                id_producto,
                instrucciones,
                rendimiento
            )
            VALUES (%s, %s, %s)
        """, (id_producto, instrucciones, rendimiento))

        id_receta = cursor.lastrowid

        for ingrediente in ingredientes:
            cursor.execute("""
                INSERT INTO detalle_recetas (
                    id_receta,
                    id_materia_prima,
                    cantidad
                )
                VALUES (%s, %s, %s)
            """, (
                id_receta,
                ingrediente['id_materia_prima'],
                ingrediente['cantidad_validada']
            ))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Receta creada correctamente.',
            'id_receta': id_receta
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo crear la receta.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# PUT: Actualizar receta e ingredientes
# ==========================================

@productos_bp.route(
    '/recetas/<int:id_receta>',
    methods=['PUT']
)
def actualizar_receta(id_receta):
    datos = request.get_json()

    if not datos:
        return jsonify({'mensaje': 'Debes enviar los datos.'}), 400

    instrucciones = datos.get('instrucciones')
    rendimiento = datos.get('rendimiento', 1)
    ingredientes = datos.get('ingredientes')

    if not isinstance(rendimiento, int) or isinstance(rendimiento, bool) or rendimiento <= 0:
        return jsonify({
            'mensaje': 'El rendimiento debe ser un entero mayor que cero.'
        }), 400

    valido, mensaje = validar_ingredientes(ingredientes)

    if not valido:
        return jsonify({'mensaje': mensaje}), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_receta
            FROM recetas
            WHERE id_receta = %s
            FOR UPDATE
        """, (id_receta,))

        if not cursor.fetchone():
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'La receta no existe.'
            }), 404

        for ingrediente in ingredientes:
            cursor.execute("""
                SELECT id_materia_prima
                FROM materias_primas
                WHERE id_materia_prima = %s
                  AND estado = 1
            """, (ingrediente['id_materia_prima'],))

            if not cursor.fetchone():
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': (
                        'La materia prima '
                        f"{ingrediente['id_materia_prima']} "
                        'no existe o está inactiva.'
                    )
                }), 400

        cursor.execute("""
            UPDATE recetas
            SET instrucciones = %s,
                rendimiento = %s
            WHERE id_receta = %s
        """, (instrucciones, rendimiento, id_receta))

        # Reemplazar los ingredientes anteriores.
        cursor.execute("""
            DELETE FROM detalle_recetas
            WHERE id_receta = %s
        """, (id_receta,))

        for ingrediente in ingredientes:
            cursor.execute("""
                INSERT INTO detalle_recetas (
                    id_receta,
                    id_materia_prima,
                    cantidad
                )
                VALUES (%s, %s, %s)
            """, (
                id_receta,
                ingrediente['id_materia_prima'],
                ingrediente['cantidad_validada']
            ))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Receta actualizada correctamente.'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo actualizar la receta.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# DELETE: Eliminar receta
# ==========================================

@productos_bp.route(
    '/recetas/<int:id_receta>',
    methods=['DELETE']
)
def eliminar_receta(id_receta):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_receta
            FROM recetas
            WHERE id_receta = %s
        """, (id_receta,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'La receta no existe.'
            }), 404

        cursor.execute("""
            DELETE FROM detalle_recetas
            WHERE id_receta = %s
        """, (id_receta,))

        cursor.execute("""
            DELETE FROM recetas
            WHERE id_receta = %s
        """, (id_receta,))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Receta eliminada correctamente.'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo eliminar la receta.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()
