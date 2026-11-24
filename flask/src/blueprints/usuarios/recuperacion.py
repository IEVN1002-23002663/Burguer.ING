# Recuperación simplificada: exclusivamente para demostración local.
import os
from flask import current_app, jsonify, request, g
from werkzeug.security import generate_password_hash
from database import mysql
from .routes import usuarios_bp
from .login import roles_requeridos, token_requerido

ERROR_CUENTA = 'El nombre completo y el correo no coinciden con una cuenta activa.'


def demo_local():
    # No habilitar en un servidor publicado ni detrás de un proxy.
    return (os.environ.get('RESET_DEMO') == '1'
            and request.remote_addr in ('127.0.0.1', '::1')
            and request.host in ('127.0.0.1:5000', 'localhost:5000')
            and request.headers.get('Origin') in
            (None, 'http://localhost:4200', 'http://127.0.0.1:4200'))


def datos_cuenta(datos):
    nombre = datos.get('nombre')
    correo = datos.get('correo')
    if not isinstance(nombre, str) or not isinstance(correo, str):
        return None
    nombre, correo = nombre.strip(), correo.strip().lower()
    if not nombre or len(nombre) > 100 or not correo or len(correo) > 120 or '@' not in correo:
        return None
    return nombre, correo


@usuarios_bp.route('/solicitar-recuperacion', methods=['POST'])
def solicitar_recuperacion():
    if not demo_local():
        return jsonify(mensaje='Recuperación simplificada disponible solo en modo demo local.'), 403
    datos = request.get_json(silent=True)
    identidad = datos_cuenta(datos) if isinstance(datos, dict) else None
    if not identidad:
        return jsonify(mensaje='Ingresa tu nombre completo y correo válido.'), 400
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT id_usuario FROM usuarios
                          WHERE TRIM(nombre) = %s AND correo = %s AND estado = 1
                          LIMIT 1''', identidad)
        cuenta = cursor.fetchone()
        if not cuenta:
            return jsonify(mensaje=ERROR_CUENTA), 400
        return jsonify(mensaje='Cuenta encontrada. Ingresa tu nueva contraseña.'), 200
    except Exception:
        current_app.logger.exception('Error al verificar cuenta')
        return jsonify(mensaje='No fue posible verificar la cuenta.'), 500
    finally:
        if cursor is not None:
            cursor.close()


@usuarios_bp.route('/restablecer-password', methods=['POST'])
def restablecer_password():
    if not demo_local():
        return jsonify(mensaje='Recuperación simplificada disponible solo en modo demo local.'), 403
    datos = request.get_json(silent=True)
    identidad = datos_cuenta(datos) if isinstance(datos, dict) else None
    if not identidad:
        return jsonify(mensaje=ERROR_CUENTA), 400
    password = datos.get('password')
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        return jsonify(mensaje='La contraseña debe tener entre 8 y 128 caracteres.'), 400
    if password != datos.get('confirmarPassword'):
        return jsonify(mensaje='Las contraseñas no coinciden.'), 400
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        # Validar nuevamente en el servidor; no confiar en el paso de Angular.
        cursor.execute('''SELECT id_usuario FROM usuarios
                          WHERE TRIM(nombre) = %s AND correo = %s AND estado = 1
                          LIMIT 1 FOR UPDATE''', identidad)
        cuenta = cursor.fetchone()
        if not cuenta:
            mysql.connection.rollback()
            return jsonify(mensaje=ERROR_CUENTA), 400
        cursor.execute('UPDATE usuarios SET password = %s WHERE id_usuario = %s',
                       (generate_password_hash(password), cuenta[0]))
        mysql.connection.commit()
        return jsonify(mensaje='Contraseña actualizada correctamente. Ya puedes iniciar sesión.'), 200
    except Exception:
        mysql.connection.rollback()
        current_app.logger.exception('Error al restablecer contraseña')
        return jsonify(mensaje='No fue posible actualizar la contraseña.'), 500
    finally:
        if cursor is not None:
            cursor.close()


# Protege las rutas existentes que permitirían eludir la recuperación
# cambiando contraseñas, roles o correos sin autorización.
@usuarios_bp.before_request
def proteger_gestion_de_cuentas():

    if request.method == 'OPTIONS':
        return None

    endpoint = (request.endpoint or '').rsplit('.', 1)[-1]
    if endpoint in {'obtener_usuarios', 'obtener_usuario', 'registrar_usuario', 'actualizar_usuario', 'cambiar_estado'}:
        return roles_requeridos('Administrador')(lambda: None)()
    if endpoint in {'obtener_perfil_cliente', 'actualizar_perfil_cliente', 'obtener_direcciones_cliente',
                    'registrar_direccion_cliente', 'actualizar_direccion_cliente', 'eliminar_direccion_cliente'}:
        @token_requerido
        def verificar_propietario():
            id_cliente = (request.view_args or {}).get('id_cliente')
            cursor = mysql.connection.cursor()
            try:
                cursor.execute('SELECT id_usuario FROM clientes WHERE id_cliente = %s', (id_cliente,))
                fila = cursor.fetchone()
                if not fila or (fila[0] != g.usuario.get('id_usuario') and g.usuario.get('rol') != 'Administrador'):
                    return jsonify(mensaje='No tienes permiso para acceder a este cliente.'), 403
            finally:
                cursor.close()
        return verificar_propietario()
    return None
