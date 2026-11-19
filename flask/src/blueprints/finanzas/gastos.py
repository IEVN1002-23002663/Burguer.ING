
from flask import request, jsonify
from database import mysql
from decimal import Decimal, InvalidOperation


from . import finanzas_bp


def convertir_decimal(valor):
    try:
        numero = Decimal(str(valor))

        if not numero.is_finite():
            return None

        return numero
    except (InvalidOperation, TypeError, ValueError):
        return None


# ==========================================
# GET: Consultar todos los gastos
# ==========================================

@finanzas_bp.route('/gastos/', methods=['GET'])
def obtener_gastos():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                g.id_gasto,
                g.id_usuario,
                u.nombre AS usuario,
                g.concepto,
                g.categoria,
                g.monto,
                g.fecha_gasto,
                g.descripcion
            FROM gastos g
            LEFT JOIN usuarios u
                ON g.id_usuario = u.id_usuario
            ORDER BY g.fecha_gasto DESC, g.id_gasto DESC
        """)

        columnas = [col[0] for col in cursor.description]
        gastos = []

        for fila in cursor.fetchall():
            gasto = dict(zip(columnas, fila))
            gasto['monto'] = float(gasto['monto'])

            if gasto['fecha_gasto']:
                gasto['fecha_gasto'] = str(gasto['fecha_gasto'])

            gastos.append(gasto)

        return jsonify(gastos), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar los gastos.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Consultar un gasto por ID
# ==========================================

@finanzas_bp.route('/gastos/<int:id_gasto>', methods=['GET'])
def obtener_gasto(id_gasto):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                g.id_gasto,
                g.id_usuario,
                u.nombre AS usuario,
                g.concepto,
                g.categoria,
                g.monto,
                g.fecha_gasto,
                g.descripcion
            FROM gastos g
            LEFT JOIN usuarios u
                ON g.id_usuario = u.id_usuario
            WHERE g.id_gasto = %s
        """, (id_gasto,))

        fila = cursor.fetchone()

        if not fila:
            return jsonify({
                'mensaje': 'El gasto no existe.'
            }), 404

        columnas = [col[0] for col in cursor.description]
        gasto = dict(zip(columnas, fila))

        gasto['monto'] = float(gasto['monto'])

        if gasto['fecha_gasto']:
            gasto['fecha_gasto'] = str(gasto['fecha_gasto'])

        return jsonify(gasto), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar el gasto.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# POST: Registrar un gasto
# ==========================================

@finanzas_bp.route('/gastos/', methods=['POST'])
def crear_gasto():
    datos = request.get_json()

    if not datos:
        return jsonify({
            'mensaje': 'Debes enviar los datos del gasto.'
        }), 400

    id_usuario = datos.get('id_usuario')
    concepto = datos.get('concepto')
    categoria = datos.get('categoria')
    monto = convertir_decimal(datos.get('monto'))
    fecha_gasto = datos.get('fecha_gasto')
    descripcion = datos.get('descripcion')

    if (
        not isinstance(concepto, str)
        or not concepto.strip()
        or not isinstance(categoria, str)
        or not categoria.strip()
        or monto is None
        or not fecha_gasto
    ):
        return jsonify({
            'mensaje': 'Concepto, categoría, monto y fecha son obligatorios.'
        }), 400

    if monto <= 0:
        return jsonify({
            'mensaje': 'El monto debe ser mayor que cero.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        if id_usuario is not None:
            cursor.execute("""
                SELECT id_usuario
                FROM usuarios
                WHERE id_usuario = %s
                  AND estado = 1
            """, (id_usuario,))

            if not cursor.fetchone():
                return jsonify({
                    'mensaje': 'El usuario no existe o está inactivo.'
                }), 400

        cursor.execute("""
            INSERT INTO gastos (
                id_usuario,
                concepto,
                categoria,
                monto,
                fecha_gasto,
                descripcion
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            id_usuario,
            concepto.strip(),
            categoria.strip(),
            monto,
            fecha_gasto,
            descripcion
        ))

        id_gasto = cursor.lastrowid
        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Gasto registrado correctamente.',
            'id_gasto': id_gasto
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo registrar el gasto.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# PUT: Actualizar un gasto
# ==========================================

@finanzas_bp.route('/gastos/<int:id_gasto>', methods=['PUT'])
def actualizar_gasto(id_gasto):
    datos = request.get_json()

    if not datos:
        return jsonify({
            'mensaje': 'Debes enviar los datos.'
        }), 400

    id_usuario = datos.get('id_usuario')
    concepto = datos.get('concepto')
    categoria = datos.get('categoria')
    monto = convertir_decimal(datos.get('monto'))
    fecha_gasto = datos.get('fecha_gasto')
    descripcion = datos.get('descripcion')

    if (
        not isinstance(concepto, str)
        or not concepto.strip()
        or not isinstance(categoria, str)
        or not categoria.strip()
        or monto is None
        or not fecha_gasto
    ):
        return jsonify({
            'mensaje': 'Concepto, categoría, monto y fecha son obligatorios.'
        }), 400

    if monto <= 0:
        return jsonify({
            'mensaje': 'El monto debe ser mayor que cero.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_gasto
            FROM gastos
            WHERE id_gasto = %s
        """, (id_gasto,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'El gasto no existe.'
            }), 404

        if id_usuario is not None:
            cursor.execute("""
                SELECT id_usuario
                FROM usuarios
                WHERE id_usuario = %s
                  AND estado = 1
            """, (id_usuario,))

            if not cursor.fetchone():
                return jsonify({
                    'mensaje': 'El usuario no existe o está inactivo.'
                }), 400

        cursor.execute("""
            UPDATE gastos
            SET
                id_usuario = %s,
                concepto = %s,
                categoria = %s,
                monto = %s,
                fecha_gasto = %s,
                descripcion = %s
            WHERE id_gasto = %s
        """, (
            id_usuario,
            concepto.strip(),
            categoria.strip(),
            monto,
            fecha_gasto,
            descripcion,
            id_gasto
        ))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Gasto actualizado correctamente.'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo actualizar el gasto.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# DELETE: Eliminar un gasto
# ==========================================

@finanzas_bp.route('/gastos/<int:id_gasto>', methods=['DELETE'])
def eliminar_gasto(id_gasto):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            DELETE FROM gastos
            WHERE id_gasto = %s
        """, (id_gasto,))

        if cursor.rowcount == 0:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El gasto no existe.'
            }), 404

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Gasto eliminado correctamente.'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo eliminar el gasto.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()
