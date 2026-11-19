
from flask import request, jsonify, current_app, g
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt

from database import mysql
from .routes import usuarios_bp


# ==========================================
# INICIO DE SESIÓN
# ==========================================

@usuarios_bp.route('/login', methods=['POST'])
def iniciar_sesion():

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos en formato JSON'
            }), 400

        correo = datos.get('correo')
        password = datos.get('password')

        if not correo or not password:
            return jsonify({
                'mensaje': 'El correo y la contraseña son obligatorios'
            }), 400

        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                u.id_usuario,
                u.nombre,
                u.correo,
                u.password,
                u.estado,
                r.id_rol,
                r.nombre
            FROM usuarios u
            INNER JOIN roles r
                ON u.id_rol = r.id_rol
            WHERE u.correo = %s
            LIMIT 1
        """

        cursor.execute(sql, (correo,))
        usuario = cursor.fetchone()

        # Verificar que el usuario exista
        if usuario is None:
            return jsonify({
                'mensaje': 'Correo o contraseña incorrectos'
            }), 401

        # Verificar que la cuenta esté activa
        if usuario[4] != 1:
            return jsonify({
                'mensaje': 'Tu cuenta se encuentra desactivada'
            }), 403

        # Verificar contraseña
        if not check_password_hash(usuario[3], password):
            return jsonify({
                'mensaje': 'Correo o contraseña incorrectos'
            }), 401

        # Crear token JWT
        fecha_actual = datetime.now(timezone.utc)

        payload = {
            'id_usuario': usuario[0],
            'nombre': usuario[1],
            'correo': usuario[2],
            'id_rol': usuario[5],
            'rol': usuario[6],
            'iat': fecha_actual,
            'exp': fecha_actual + timedelta(
                hours=current_app.config['JWT_EXPIRATION_HOURS']
            )
        }

        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )

        return jsonify({
            'mensaje': 'Inicio de sesión exitoso',
            'token': token,
            'usuario': {
                'id_usuario': usuario[0],
                'nombre': usuario[1],
                'correo': usuario[2],
                'id_rol': usuario[5],
                'rol': usuario[6]
            }
        }), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al iniciar sesión',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# DECORADOR PARA VALIDAR TOKEN JWT
# ==========================================

def token_requerido(funcion):

    @wraps(funcion)
    def decorador(*args, **kwargs):

        autorizacion = request.headers.get('Authorization')

        if not autorizacion:
            return jsonify({
                'mensaje': 'No se proporcionó un token'
            }), 401

        partes = autorizacion.split()

        if len(partes) != 2 or partes[0].lower() != 'bearer':
            return jsonify({
                'mensaje': 'Formato de token incorrecto. Usa Bearer <token>'
            }), 401

        token = partes[1]

        try:
            datos = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )

            g.usuario = datos

        except jwt.ExpiredSignatureError:
            return jsonify({
                'mensaje': 'El token ha expirado'
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                'mensaje': 'El token no es válido'
            }), 401

        return funcion(*args, **kwargs)

    return decorador


# ==========================================
# DECORADOR PARA VALIDAR ROLES
# ==========================================

def roles_requeridos(*roles):

    def decorador_rol(funcion):

        @wraps(funcion)
        @token_requerido
        def verificar_rol(*args, **kwargs):

            rol_usuario = g.usuario.get('rol')

            if rol_usuario not in roles:
                return jsonify({
                    'mensaje': 'No tienes permisos para realizar esta acción'
                }), 403

            return funcion(*args, **kwargs)

        return verificar_rol

    return decorador_rol


# ==========================================
# CONSULTAR PERFIL DEL USUARIO AUTENTICADO
# ==========================================

@usuarios_bp.route('/perfil', methods=['GET'])
@token_requerido
def obtener_perfil():

    return jsonify({
        'mensaje': 'Token válido',
        'usuario': {
            'id_usuario': g.usuario['id_usuario'],
            'nombre': g.usuario['nombre'],
            'correo': g.usuario['correo'],
            'rol': g.usuario['rol']
        }
    }), 200