
from flask import Blueprint, request, jsonify
from database import mysql
from werkzeug.security import generate_password_hash


usuarios_bp = Blueprint(
    'usuarios',
    __name__,
    url_prefix='/api/usuarios'
)


# ==========================================
# CONSULTAR TODOS LOS USUARIOS
# ==========================================

@usuarios_bp.route('/', methods=['GET'])
def obtener_usuarios():

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                u.id_usuario,
                u.nombre,
                u.correo,
                u.estado,
                u.fecha_registro,
                r.id_rol,
                r.nombre AS rol
            FROM usuarios u
            INNER JOIN roles r
                ON u.id_rol = r.id_rol
            ORDER BY u.id_usuario ASC
        """

        cursor.execute(sql)
        resultados = cursor.fetchall()

        usuarios = []

        for fila in resultados:
            usuarios.append({
                'id_usuario': fila[0],
                'nombre': fila[1],
                'correo': fila[2],
                'estado': fila[3],
                'fecha_registro': str(fila[4]),
                'id_rol': fila[5],
                'rol': fila[6]
            })

        return jsonify(usuarios), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar los usuarios',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# CONSULTAR USUARIO POR ID
# ==========================================

@usuarios_bp.route('/<int:id_usuario>', methods=['GET'])
def obtener_usuario(id_usuario):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                u.id_usuario,
                u.nombre,
                u.correo,
                u.estado,
                u.fecha_registro,
                r.id_rol,
                r.nombre
            FROM usuarios u
            INNER JOIN roles r
                ON u.id_rol = r.id_rol
            WHERE u.id_usuario = %s
        """

        cursor.execute(sql, (id_usuario,))
        usuario = cursor.fetchone()

        if usuario is None:
            return jsonify({
                'mensaje': 'Usuario no encontrado'
            }), 404

        resultado = {
            'id_usuario': usuario[0],
            'nombre': usuario[1],
            'correo': usuario[2],
            'estado': usuario[3],
            'fecha_registro': str(usuario[4]),
            'id_rol': usuario[5],
            'rol': usuario[6]
        }

        return jsonify(resultado), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar el usuario',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# REGISTRAR USUARIO
# ==========================================

@usuarios_bp.route('/', methods=['POST'])
def registrar_usuario():

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar información en formato JSON'
            }), 400

        nombre = datos.get('nombre')
        correo = datos.get('correo')
        password = datos.get('password')
        id_rol = datos.get('id_rol')

        if not nombre or not correo or not password or not id_rol:
            return jsonify({
                'mensaje': 'Todos los campos son obligatorios'
            }), 400

        if len(password) < 8:
            return jsonify({
                'mensaje': 'La contraseña debe tener al menos 8 caracteres'
            }), 400

        if len(nombre) > 100 or len(correo) > 120:
            return jsonify({
                'mensaje': 'El nombre o correo supera la longitud permitida'
            }), 400

        password_hash = generate_password_hash(password)

        cursor = mysql.connection.cursor()

        sql = """
            INSERT INTO usuarios
            (id_rol, nombre, correo, password, estado)
            VALUES (%s, %s, %s, %s, 1)
        """

        cursor.execute(sql, (
            id_rol,
            nombre,
            correo,
            password_hash
        ))

        mysql.connection.commit()

        id_nuevo = cursor.lastrowid

        return jsonify({
            'mensaje': 'Usuario registrado correctamente',
            'id_usuario': id_nuevo
        }), 201

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al registrar el usuario',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# ACTUALIZAR USUARIO
# ==========================================

@usuarios_bp.route('/<int:id_usuario>', methods=['PUT'])
def actualizar_usuario(id_usuario):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar información en formato JSON'
            }), 400

        nombre = datos.get('nombre')
        correo = datos.get('correo')
        id_rol = datos.get('id_rol')

        if not nombre or not correo or not id_rol:
            return jsonify({
                'mensaje': 'Nombre, correo y rol son obligatorios'
            }), 400

        if len(nombre) > 100 or len(correo) > 120:
            return jsonify({
                'mensaje': 'El nombre o correo supera la longitud permitida'
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute(
            'SELECT id_usuario FROM usuarios WHERE id_usuario = %s',
            (id_usuario,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                'mensaje': 'Usuario no encontrado'
            }), 404

        sql = """
            UPDATE usuarios
            SET nombre = %s,
                correo = %s,
                id_rol = %s
            WHERE id_usuario = %s
        """

        cursor.execute(sql, (
            nombre,
            correo,
            id_rol,
            id_usuario
        ))

        # Actualizar contraseña solamente si se envía una nueva
        password = datos.get('password')

        if password:
            if len(password) < 8:
                return jsonify({
                    'mensaje': 'La contraseña debe tener al menos 8 caracteres'
                }), 400

            password_hash = generate_password_hash(password)

            cursor.execute(
                """
                UPDATE usuarios
                SET password = %s
                WHERE id_usuario = %s
                """,
                (password_hash, id_usuario)
            )

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Usuario actualizado correctamente'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al actualizar el usuario',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# CAMBIAR ESTADO DEL USUARIO
# ==========================================

@usuarios_bp.route('/<int:id_usuario>/estado', methods=['PATCH'])
def cambiar_estado(id_usuario):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos or 'estado' not in datos:
            return jsonify({
                'mensaje': 'Debes indicar el estado del usuario'
            }), 400

        estado = datos['estado']

        if estado not in (0, 1):
            return jsonify({
                'mensaje': 'El estado debe ser 1 (activo) o 0 (inactivo)'
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            UPDATE usuarios
            SET estado = %s
            WHERE id_usuario = %s
            """,
            (estado, id_usuario)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                'SELECT id_usuario FROM usuarios WHERE id_usuario = %s',
                (id_usuario,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    'mensaje': 'Usuario no encontrado'
                }), 404

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Estado del usuario actualizado correctamente',
            'estado': estado
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al cambiar el estado',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()
