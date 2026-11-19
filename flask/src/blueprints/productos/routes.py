
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


# ==========================================
# CATEGORÍAS DE PRODUCTOS
# ==========================================

@productos_bp.route('/categorias-productos/', methods=['GET'])
def obtener_categorias_productos():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_categoria_producto, nombre, descripcion
            FROM categorias_productos
            ORDER BY nombre
        """)

        categorias = [
            {
                'id_categoria_producto': fila[0],
                'nombre': fila[1],
                'descripcion': fila[2]
            }
            for fila in cursor.fetchall()
        ]

        return jsonify(categorias), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar las categorías.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


@productos_bp.route('/categorias-productos/', methods=['POST'])
def crear_categoria_producto():
    datos = request.get_json()

    if not datos:
        return jsonify({'mensaje': 'Debes enviar los datos.'}), 400

    nombre = datos.get('nombre')
    descripcion = datos.get('descripcion')

    if not isinstance(nombre, str) or not nombre.strip():
        return jsonify({'mensaje': 'El nombre es obligatorio.'}), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO categorias_productos (nombre, descripcion)
            VALUES (%s, %s)
        """, (nombre.strip(), descripcion))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Categoría creada correctamente.',
            'id_categoria_producto': cursor.lastrowid
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo crear la categoría.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


@productos_bp.route(
    '/categorias-productos/<int:id_categoria>',
    methods=['PUT']
)
def actualizar_categoria_producto(id_categoria):
    datos = request.get_json()

    if not datos:
        return jsonify({'mensaje': 'Debes enviar los datos.'}), 400

    nombre = datos.get('nombre')
    descripcion = datos.get('descripcion')

    if not isinstance(nombre, str) or not nombre.strip():
        return jsonify({'mensaje': 'El nombre es obligatorio.'}), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            UPDATE categorias_productos
            SET nombre = %s, descripcion = %s
            WHERE id_categoria_producto = %s
        """, (nombre.strip(), descripcion, id_categoria))

        if cursor.rowcount == 0:
            cursor.execute("""
                SELECT id_categoria_producto
                FROM categorias_productos
                WHERE id_categoria_producto = %s
            """, (id_categoria,))

            if not cursor.fetchone():
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': 'La categoría no existe.'
                }), 404

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Categoría actualizada correctamente.'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo actualizar la categoría.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# PRODUCTOS
# ==========================================

@productos_bp.route('/productos/', methods=['GET'])
def obtener_productos():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                p.id_producto,
                p.id_categoria_producto,
                cp.nombre AS categoria,
                p.nombre,
                p.descripcion,
                p.precio,
                p.costo_variable_extra,
                p.imagen,
                p.disponible
            FROM productos p
            INNER JOIN categorias_productos cp
                ON p.id_categoria_producto = cp.id_categoria_producto
            ORDER BY p.nombre
        """)

        columnas = [col[0] for col in cursor.description]
        productos = []

        for fila in cursor.fetchall():
            producto = dict(zip(columnas, fila))
            producto['precio'] = float(producto['precio'])
            producto['costo_variable_extra'] = float(
                producto['costo_variable_extra']
            )
            producto['disponible'] = bool(producto['disponible'])
            productos.append(producto)

        return jsonify(productos), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar los productos.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


@productos_bp.route('/productos/<int:id_producto>', methods=['GET'])
def obtener_producto(id_producto):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                p.id_producto,
                p.id_categoria_producto,
                cp.nombre AS categoria,
                p.nombre,
                p.descripcion,
                p.precio,
                p.costo_variable_extra,
                p.imagen,
                p.disponible
            FROM productos p
            INNER JOIN categorias_productos cp
                ON p.id_categoria_producto = cp.id_categoria_producto
            WHERE p.id_producto = %s
        """, (id_producto,))

        fila = cursor.fetchone()

        if not fila:
            return jsonify({
                'mensaje': 'El producto no existe.'
            }), 404

        columnas = [col[0] for col in cursor.description]
        producto = dict(zip(columnas, fila))

        producto['precio'] = float(producto['precio'])
        producto['costo_variable_extra'] = float(
            producto['costo_variable_extra']
        )
        producto['disponible'] = bool(producto['disponible'])

        return jsonify(producto), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar el producto.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


@productos_bp.route('/productos/', methods=['POST'])
def crear_producto():
    datos = request.get_json()

    if not datos:
        return jsonify({'mensaje': 'Debes enviar los datos.'}), 400

    id_categoria = datos.get('id_categoria_producto')
    nombre = datos.get('nombre')
    descripcion = datos.get('descripcion')
    precio = convertir_decimal(datos.get('precio'))
    costo_extra = convertir_decimal(
        datos.get('costo_variable_extra', 0)
    )
    imagen = datos.get('imagen')

    if not id_categoria or not isinstance(nombre, str) or not nombre.strip():
        return jsonify({
            'mensaje': 'La categoría y el nombre son obligatorios.'
        }), 400

    if precio is None or costo_extra is None:
        return jsonify({
            'mensaje': 'El precio y el costo extra deben ser numéricos.'
        }), 400

    if precio <= 0 or costo_extra < 0:
        return jsonify({
            'mensaje': 'El precio debe ser mayor que cero y el costo extra no puede ser negativo.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_categoria_producto
            FROM categorias_productos
            WHERE id_categoria_producto = %s
        """, (id_categoria,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'La categoría indicada no existe.'
            }), 404

        cursor.execute("""
            INSERT INTO productos (
                id_categoria_producto,
                nombre,
                descripcion,
                precio,
                costo_variable_extra,
                imagen,
                disponible
            )
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """, (
            id_categoria,
            nombre.strip(),
            descripcion,
            precio,
            costo_extra,
            imagen
        ))

        id_producto = cursor.lastrowid
        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Producto creado correctamente.',
            'id_producto': id_producto
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo crear el producto.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


@productos_bp.route('/productos/<int:id_producto>', methods=['PUT'])
def actualizar_producto(id_producto):
    datos = request.get_json()

    if not datos:
        return jsonify({'mensaje': 'Debes enviar los datos.'}), 400

    id_categoria = datos.get('id_categoria_producto')
    nombre = datos.get('nombre')
    descripcion = datos.get('descripcion')
    precio = convertir_decimal(datos.get('precio'))
    costo_extra = convertir_decimal(
        datos.get('costo_variable_extra', 0)
    )
    imagen = datos.get('imagen')

    if not id_categoria or not isinstance(nombre, str) or not nombre.strip():
        return jsonify({
            'mensaje': 'La categoría y el nombre son obligatorios.'
        }), 400

    if precio is None or costo_extra is None:
        return jsonify({
            'mensaje': 'El precio y el costo extra deben ser numéricos.'
        }), 400

    if precio <= 0 or costo_extra < 0:
        return jsonify({
            'mensaje': 'El precio debe ser mayor que cero y el costo extra no puede ser negativo.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_categoria_producto
            FROM categorias_productos
            WHERE id_categoria_producto = %s
        """, (id_categoria,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'La categoría indicada no existe.'
            }), 404

        cursor.execute("""
            UPDATE productos
            SET
                id_categoria_producto = %s,
                nombre = %s,
                descripcion = %s,
                precio = %s,
                costo_variable_extra = %s,
                imagen = %s
            WHERE id_producto = %s
        """, (
            id_categoria,
            nombre.strip(),
            descripcion,
            precio,
            costo_extra,
            imagen,
            id_producto
        ))

        if cursor.rowcount == 0:
            cursor.execute("""
                SELECT id_producto
                FROM productos
                WHERE id_producto = %s
            """, (id_producto,))

            if not cursor.fetchone():
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': 'El producto no existe.'
                }), 404

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Producto actualizado correctamente.'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo actualizar el producto.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


@productos_bp.route(
    '/productos/<int:id_producto>/disponibilidad',
    methods=['PATCH']
)
def cambiar_disponibilidad(id_producto):
    datos = request.get_json()

    if not datos or 'disponible' not in datos:
        return jsonify({
            'mensaje': 'Debes indicar el campo disponible.'
        }), 400

    disponible = datos.get('disponible')

    if disponible not in (True, False, 0, 1):
        return jsonify({
            'mensaje': 'El campo disponible debe ser verdadero o falso.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            UPDATE productos
            SET disponible = %s
            WHERE id_producto = %s
        """, (int(disponible), id_producto))

        if cursor.rowcount == 0:
            cursor.execute("""
                SELECT id_producto
                FROM productos
                WHERE id_producto = %s
            """, (id_producto,))

            if not cursor.fetchone():
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': 'El producto no existe.'
                }), 404

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Disponibilidad actualizada correctamente.',
            'disponible': bool(disponible)
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo cambiar la disponibilidad.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()
