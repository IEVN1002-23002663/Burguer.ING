
from flask import Blueprint, request, jsonify
from database import mysql


proveedores_bp = Blueprint(
    'proveedores',
    __name__,
    url_prefix='/api/proveedores'
)


# ==========================================
# CONSULTAR TODOS LOS PROVEEDORES
# ==========================================

@proveedores_bp.route('/', methods=['GET'])
def obtener_proveedores():

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                id_proveedor,
                nombre,
                contacto,
                telefono,
                correo,
                direccion,
                estado
            FROM proveedores
            ORDER BY id_proveedor ASC
        """

        cursor.execute(sql)
        resultados = cursor.fetchall()

        proveedores = []

        for fila in resultados:
            proveedores.append({
                'id_proveedor': fila[0],
                'nombre': fila[1],
                'contacto': fila[2],
                'telefono': fila[3],
                'correo': fila[4],
                'direccion': fila[5],
                'estado': fila[6]
            })

        return jsonify(proveedores), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar los proveedores',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# CONSULTAR PROVEEDOR POR ID
# ==========================================

@proveedores_bp.route('/<int:id_proveedor>', methods=['GET'])
def obtener_proveedor(id_proveedor):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                id_proveedor,
                nombre,
                contacto,
                telefono,
                correo,
                direccion,
                estado
            FROM proveedores
            WHERE id_proveedor = %s
        """

        cursor.execute(sql, (id_proveedor,))
        fila = cursor.fetchone()

        if fila is None:
            return jsonify({
                'mensaje': 'Proveedor no encontrado'
            }), 404

        proveedor = {
            'id_proveedor': fila[0],
            'nombre': fila[1],
            'contacto': fila[2],
            'telefono': fila[3],
            'correo': fila[4],
            'direccion': fila[5],
            'estado': fila[6]
        }

        return jsonify(proveedor), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar el proveedor',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# REGISTRAR PROVEEDOR
# ==========================================

@proveedores_bp.route('/', methods=['POST'])
def registrar_proveedor():

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos en formato JSON'
            }), 400

        nombre = datos.get('nombre')
        contacto = datos.get('contacto')
        telefono = datos.get('telefono')
        correo = datos.get('correo')
        direccion = datos.get('direccion')

        if not nombre:
            return jsonify({
                'mensaje': 'El nombre del proveedor es obligatorio'
            }), 400

        if len(nombre) > 120:
            return jsonify({
                'mensaje': 'El nombre no puede superar los 120 caracteres'
            }), 400

        cursor = mysql.connection.cursor()

        sql = """
            INSERT INTO proveedores
            (nombre, contacto, telefono, correo, direccion, estado)
            VALUES (%s, %s, %s, %s, %s, 1)
        """

        cursor.execute(sql, (
            nombre,
            contacto,
            telefono,
            correo,
            direccion
        ))

        mysql.connection.commit()

        id_nuevo = cursor.lastrowid

        return jsonify({
            'mensaje': 'Proveedor registrado correctamente',
            'id_proveedor': id_nuevo
        }), 201

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al registrar el proveedor',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# ACTUALIZAR PROVEEDOR
# ==========================================

@proveedores_bp.route('/<int:id_proveedor>', methods=['PUT'])
def actualizar_proveedor(id_proveedor):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos en formato JSON'
            }), 400

        nombre = datos.get('nombre')
        contacto = datos.get('contacto')
        telefono = datos.get('telefono')
        correo = datos.get('correo')
        direccion = datos.get('direccion')

        if not nombre:
            return jsonify({
                'mensaje': 'El nombre del proveedor es obligatorio'
            }), 400

        if len(nombre) > 120:
            return jsonify({
                'mensaje': 'El nombre no puede superar los 120 caracteres'
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute(
            'SELECT id_proveedor FROM proveedores WHERE id_proveedor = %s',
            (id_proveedor,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                'mensaje': 'Proveedor no encontrado'
            }), 404

        sql = """
            UPDATE proveedores
            SET nombre = %s,
                contacto = %s,
                telefono = %s,
                correo = %s,
                direccion = %s
            WHERE id_proveedor = %s
        """

        cursor.execute(sql, (
            nombre,
            contacto,
            telefono,
            correo,
            direccion,
            id_proveedor
        ))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Proveedor actualizado correctamente'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al actualizar el proveedor',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# CAMBIAR ESTADO DEL PROVEEDOR
# ==========================================

@proveedores_bp.route('/<int:id_proveedor>/estado', methods=['PATCH'])
def cambiar_estado_proveedor(id_proveedor):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos or 'estado' not in datos:
            return jsonify({
                'mensaje': 'Debes indicar el estado del proveedor'
            }), 400

        estado = datos['estado']

        if type(estado) is not int or estado not in (0, 1):
            return jsonify({
                'mensaje': 'El estado debe ser 1 (activo) o 0 (inactivo)'
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            UPDATE proveedores
            SET estado = %s
            WHERE id_proveedor = %s
            """,
            (estado, id_proveedor)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                'SELECT id_proveedor FROM proveedores WHERE id_proveedor = %s',
                (id_proveedor,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    'mensaje': 'Proveedor no encontrado'
                }), 404

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Estado del proveedor actualizado correctamente',
            'estado': estado
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al cambiar el estado del proveedor',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()
