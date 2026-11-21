
from flask import Blueprint, request, jsonify
from database import mysql
from werkzeug.security import generate_password_hash


usuarios_bp = Blueprint(
    'usuarios',
    __name__,
    url_prefix='/api/usuarios'
)


# =====================================================
# CONSULTAR TODOS LOS USUARIOS
# =====================================================

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


# =====================================================
# CONSULTAR USUARIO POR ID
# =====================================================

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


# =====================================================
# REGISTRAR USUARIO
# =====================================================

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

        id_nuevo = cursor.lastrowid

        mysql.connection.commit()

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


# =====================================================
# ACTUALIZAR USUARIO
# =====================================================

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
        password = datos.get('password')

        if not nombre or not correo or not id_rol:
            return jsonify({
                'mensaje': 'Nombre, correo y rol son obligatorios'
            }), 400

        if len(nombre) > 100 or len(correo) > 120:
            return jsonify({
                'mensaje': 'El nombre o correo supera la longitud permitida'
            }), 400

        if password and len(password) < 8:
            return jsonify({
                'mensaje': 'La contraseña debe tener al menos 8 caracteres'
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

        # Actualizar contraseña solamente si se envía una nueva.
        if password:
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


# =====================================================
# CAMBIAR ESTADO DEL USUARIO
# =====================================================

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


# =====================================================
# REGISTRO PUBLICO DE CLIENTES
# =====================================================

@usuarios_bp.route('/registro-cliente', methods=['POST'])
def registrar_cliente_publico():

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar información en formato JSON'
            }), 400

        nombre = (datos.get('nombre') or '').strip()
        correo = (datos.get('correo') or '').strip().lower()
        password = datos.get('password') or ''

        if not nombre or not correo or not password:
            return jsonify({
                'mensaje': 'Nombre, correo y contraseña son obligatorios'
            }), 400

        if len(nombre) > 100 or len(correo) > 120:
            return jsonify({
                'mensaje': 'El nombre o correo supera la longitud permitida'
            }), 400

        if len(password) < 8:
            return jsonify({
                'mensaje': 'La contraseña debe tener al menos 8 caracteres'
            }), 400

        cursor = mysql.connection.cursor()

        # Comprobar que el correo no exista.
        cursor.execute(
            'SELECT id_usuario FROM usuarios WHERE correo = %s',
            (correo,)
        )

        if cursor.fetchone():
            return jsonify({
                'mensaje': 'Ese correo ya está registrado'
            }), 409

        # Buscar el rol Cliente.
        cursor.execute(
            """
            SELECT id_rol
            FROM roles
            WHERE LOWER(nombre) = LOWER(%s)
            LIMIT 1
            """,
            ('Cliente',)
        )

        rol_cliente = cursor.fetchone()

        if not rol_cliente:
            return jsonify({
                'mensaje': 'No se encontró el rol Cliente'
            }), 500

        id_rol_cliente = rol_cliente[0]
        password_hash = generate_password_hash(password)

        # Crear el usuario.
        cursor.execute(
            """
            INSERT INTO usuarios
            (id_rol, nombre, correo, password, estado)
            VALUES (%s, %s, %s, %s, 1)
            """,
            (id_rol_cliente, nombre, correo, password_hash)
        )

        id_usuario = cursor.lastrowid

        # Crear su registro asociado como cliente.
        cursor.execute(
            """
            INSERT INTO clientes
            (id_usuario, estado_acreditacion)
            VALUES (%s, %s)
            """,
            (id_usuario, 'Sin acreditar')
        )

        id_cliente = cursor.lastrowid

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Cuenta de cliente creada correctamente',
            'id_usuario': id_usuario,
            'id_cliente': id_cliente
        }), 201

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al registrar al cliente',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# =====================================================
# CONSULTAR PERFIL DEL CLIENTE
# =====================================================

@usuarios_bp.route(
    '/cliente/<int:id_cliente>/perfil',
    methods=['GET']
)
def obtener_perfil_cliente(id_cliente):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                u.id_usuario,
                u.nombre,
                u.correo,
                u.fecha_registro,
                c.id_cliente,
                c.telefono,
                c.tipo_acreditacion,
                c.folio_acreditacion,
                c.estado_acreditacion
            FROM clientes c
            INNER JOIN usuarios u
                ON c.id_usuario = u.id_usuario
            WHERE c.id_cliente = %s
        """, (id_cliente,))

        cliente = cursor.fetchone()

        if not cliente:
            return jsonify({
                'mensaje': 'Perfil de cliente no encontrado.'
            }), 404

        cursor.execute("""
            SELECT COUNT(*)
            FROM pedidos
            WHERE id_cliente = %s
        """, (id_cliente,))

        pedidos = cursor.fetchone()

        return jsonify({
            'id_usuario': cliente[0],
            'id_cliente': cliente[4],
            'nombre': cliente[1],
            'correo': cliente[2],
            'fecha_registro': str(cliente[3]) if cliente[3] else None,
            'telefono': cliente[5] or '',
            'tipo_acreditacion': cliente[6] or '',
            'folio_acreditacion': cliente[7] or '',
            'cedula': cliente[7] or '',
            'estado_acreditacion': cliente[8],
            'pedidos_realizados': pedidos[0] if pedidos else 0
        }), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar el perfil del cliente.',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# =====================================================
# ACTUALIZAR PERFIL DEL CLIENTE
# =====================================================

@usuarios_bp.route(
    '/cliente/<int:id_cliente>/perfil',
    methods=['PUT']
)
def actualizar_perfil_cliente(id_cliente):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos del perfil.'
            }), 400

        nombre = datos.get('nombre')
        correo = datos.get('correo')
        telefono = datos.get('telefono') or ''

        # Aceptar ambos nombres para el campo de acreditación.
        folio = datos.get(
            'folio_acreditacion',
            datos.get('cedula', '')
        ) or ''

        tipo_acreditacion = datos.get('tipo_acreditacion') or ''

        if not isinstance(nombre, str) or not nombre.strip():
            return jsonify({
                'mensaje': 'El nombre es obligatorio.'
            }), 400

        if not isinstance(correo, str) or not correo.strip():
            return jsonify({
                'mensaje': 'El correo electrónico es obligatorio.'
            }), 400

        nombre = nombre.strip()
        correo = correo.strip().lower()

        if not isinstance(telefono, str):
            return jsonify({
                'mensaje': 'El teléfono no es válido.'
            }), 400

        if not isinstance(folio, str):
            return jsonify({
                'mensaje': 'El número de acreditación no es válido.'
            }), 400

        if not isinstance(tipo_acreditacion, str):
            return jsonify({
                'mensaje': 'El tipo de acreditación no es válido.'
            }), 400

        telefono = telefono.strip()
        folio = folio.strip()
        tipo_acreditacion = tipo_acreditacion.strip()

        if '@' not in correo:
            return jsonify({
                'mensaje': 'Ingresa un correo electrónico válido.'
            }), 400

        if len(nombre) > 100 or len(correo) > 120:
            return jsonify({
                'mensaje': 'El nombre o correo supera la longitud permitida.'
            }), 400

        if len(telefono) > 20:
            return jsonify({
                'mensaje': 'El teléfono supera los 20 caracteres.'
            }), 400

        if len(folio) > 50:
            return jsonify({
                'mensaje': 'El número de acreditación supera los 50 caracteres.'
            }), 400

        if len(tipo_acreditacion) > 30:
            return jsonify({
                'mensaje': 'El tipo de acreditación supera los 30 caracteres.'
            }), 400

        cursor = mysql.connection.cursor()

        # Obtener el usuario asociado al cliente.
        cursor.execute("""
            SELECT id_usuario
            FROM clientes
            WHERE id_cliente = %s
        """, (id_cliente,))

        cliente = cursor.fetchone()

        if not cliente:
            return jsonify({
                'mensaje': 'Cliente no encontrado.'
            }), 404

        id_usuario = cliente[0]

        # Comprobar que el correo no pertenezca a otra cuenta.
        cursor.execute("""
            SELECT id_usuario
            FROM usuarios
            WHERE correo = %s
              AND id_usuario <> %s
        """, (correo, id_usuario))

        if cursor.fetchone():
            return jsonify({
                'mensaje': 'Ese correo ya está registrado por otra cuenta.'
            }), 409

        # Actualizar nombre y correo del usuario.
        cursor.execute("""
            UPDATE usuarios
            SET nombre = %s,
                correo = %s
            WHERE id_usuario = %s
        """, (nombre, correo, id_usuario))

        # Actualizar teléfono y folio de acreditación.
        # No modificar tipo_acreditacion cuando no se envía.
        if 'tipo_acreditacion' in datos:
            cursor.execute("""
                UPDATE clientes
                SET telefono = %s,
                    tipo_acreditacion = %s,
                    folio_acreditacion = %s
                WHERE id_cliente = %s
            """, (
                telefono or None,
                tipo_acreditacion or None,
                folio or None,
                id_cliente
            ))
        else:
            cursor.execute("""
                UPDATE clientes
                SET telefono = %s,
                    folio_acreditacion = %s
                WHERE id_cliente = %s
            """, (
                telefono or None,
                folio or None,
                id_cliente
            ))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Perfil actualizado correctamente.'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'No se pudo actualizar el perfil.',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# =====================================================
# CONSULTAR DIRECCIONES DEL CLIENTE
# =====================================================

@usuarios_bp.route(
    '/cliente/<int:id_cliente>/direcciones',
    methods=['GET']
)
def obtener_direcciones_cliente(id_cliente):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT id_cliente
            FROM clientes
            WHERE id_cliente = %s
        """, (id_cliente,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'Cliente no encontrado.'
            }), 404

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

        resultados = cursor.fetchall()

        direcciones = []

        for fila in resultados:
            direcciones.append({
                'id_direccion': fila[0],
                'calle': fila[1],
                'numero': fila[2] or '',
                'colonia': fila[3],
                'codigo_postal': fila[4] or '',
                'referencias': fila[5] or ''
            })

        return jsonify(direcciones), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar las direcciones.',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# =====================================================
# REGISTRAR DIRECCIÓN DEL CLIENTE
# =====================================================

@usuarios_bp.route(
    '/cliente/<int:id_cliente>/direcciones',
    methods=['POST']
)
def registrar_direccion_cliente(id_cliente):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos de la dirección.'
            }), 400

        calle = datos.get('calle')
        numero = datos.get('numero') or ''
        colonia = datos.get('colonia')
        codigo_postal = datos.get('codigo_postal') or ''
        referencias = datos.get('referencias') or ''

        if not isinstance(calle, str) or not calle.strip():
            return jsonify({
                'mensaje': 'La calle es obligatoria.'
            }), 400

        if not isinstance(colonia, str) or not colonia.strip():
            return jsonify({
                'mensaje': 'La colonia es obligatoria.'
            }), 400

        campos_opcionales = [numero, codigo_postal, referencias]

        if not all(isinstance(valor, str) for valor in campos_opcionales):
            return jsonify({
                'mensaje': 'Los datos de la dirección no son válidos.'
            }), 400

        calle = calle.strip()
        numero = numero.strip()
        colonia = colonia.strip()
        codigo_postal = codigo_postal.strip()
        referencias = referencias.strip()

        if (
            len(calle) > 120
            or len(numero) > 20
            or len(colonia) > 100
            or len(codigo_postal) > 10
            or len(referencias) > 255
        ):
            return jsonify({
                'mensaje': 'Uno o más campos superan la longitud permitida.'
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT id_cliente
            FROM clientes
            WHERE id_cliente = %s
        """, (id_cliente,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'Cliente no encontrado.'
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

        id_direccion = cursor.lastrowid

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Dirección registrada correctamente.',
            'id_direccion': id_direccion
        }), 201

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'No se pudo registrar la dirección.',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# =====================================================
# ACTUALIZAR DIRECCIÓN DEL CLIENTE
# =====================================================

@usuarios_bp.route(
    '/cliente/<int:id_cliente>/direcciones/<int:id_direccion>',
    methods=['PUT']
)
def actualizar_direccion_cliente(id_cliente, id_direccion):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos de la dirección.'
            }), 400

        calle = datos.get('calle')
        numero = datos.get('numero') or ''
        colonia = datos.get('colonia')
        codigo_postal = datos.get('codigo_postal') or ''
        referencias = datos.get('referencias') or ''

        if not isinstance(calle, str) or not calle.strip():
            return jsonify({
                'mensaje': 'La calle es obligatoria.'
            }), 400

        if not isinstance(colonia, str) or not colonia.strip():
            return jsonify({
                'mensaje': 'La colonia es obligatoria.'
            }), 400

        campos_opcionales = [numero, codigo_postal, referencias]

        if not all(isinstance(valor, str) for valor in campos_opcionales):
            return jsonify({
                'mensaje': 'Los datos de la dirección no son válidos.'
            }), 400

        calle = calle.strip()
        numero = numero.strip()
        colonia = colonia.strip()
        codigo_postal = codigo_postal.strip()
        referencias = referencias.strip()

        if (
            len(calle) > 120
            or len(numero) > 20
            or len(colonia) > 100
            or len(codigo_postal) > 10
            or len(referencias) > 255
        ):
            return jsonify({
                'mensaje': 'Uno o más campos superan la longitud permitida.'
            }), 400

        cursor = mysql.connection.cursor()

        # Comprobar que la dirección pertenezca al cliente.
        cursor.execute("""
            SELECT id_direccion
            FROM direcciones
            WHERE id_direccion = %s
              AND id_cliente = %s
        """, (id_direccion, id_cliente))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'Dirección no encontrada para este cliente.'
            }), 404

        cursor.execute("""
            UPDATE direcciones
            SET calle = %s,
                numero = %s,
                colonia = %s,
                codigo_postal = %s,
                referencias = %s
            WHERE id_direccion = %s
              AND id_cliente = %s
        """, (
            calle,
            numero or None,
            colonia,
            codigo_postal or None,
            referencias or None,
            id_direccion,
            id_cliente
        ))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Dirección actualizada correctamente.'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'No se pudo actualizar la dirección.',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# =====================================================
# ELIMINAR DIRECCIÓN DEL CLIENTE
# =====================================================

@usuarios_bp.route(
    '/cliente/<int:id_cliente>/direcciones/<int:id_direccion>',
    methods=['DELETE']
)
def eliminar_direccion_cliente(id_cliente, id_direccion):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT id_direccion
            FROM direcciones
            WHERE id_direccion = %s
              AND id_cliente = %s
        """, (id_direccion, id_cliente))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'Dirección no encontrada para este cliente.'
            }), 404

        cursor.execute("""
            DELETE FROM direcciones
            WHERE id_direccion = %s
              AND id_cliente = %s
        """, (id_direccion, id_cliente))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Dirección eliminada correctamente.'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        # MySQL 1451: una clave foránea impide eliminar el registro.
        if error.args and error.args[0] == 1451:
            return jsonify({
                'mensaje': (
                    'No se puede eliminar esta dirección porque está '
                    'asociada a un pedido.'
                )
            }), 409

        return jsonify({
            'mensaje': 'No se pudo eliminar la dirección.',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()
