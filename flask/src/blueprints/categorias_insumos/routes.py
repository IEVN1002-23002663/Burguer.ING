
from flask import Blueprint, request, jsonify
from database import mysql


categorias_insumos_bp = Blueprint(
    'categorias_insumos',
    __name__,
    url_prefix='/api/categorias-insumos'
)


# ==========================================
# CONSULTAR TODAS LAS CATEGORIAS
# ==========================================

@categorias_insumos_bp.route('/', methods=['GET'])
def obtener_categorias():

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                id_categoria_insumo,
                nombre,
                descripcion
            FROM categorias_insumos
            ORDER BY id_categoria_insumo ASC
        """

        cursor.execute(sql)
        resultados = cursor.fetchall()

        categorias = []

        for fila in resultados:
            categorias.append({
                'id_categoria_insumo': fila[0],
                'nombre': fila[1],
                'descripcion': fila[2]
            })

        return jsonify(categorias), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar las categorias',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# CONSULTAR CATEGORIA POR ID
# ==========================================

@categorias_insumos_bp.route('/<int:id_categoria>', methods=['GET'])
def obtener_categoria(id_categoria):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                id_categoria_insumo,
                nombre,
                descripcion
            FROM categorias_insumos
            WHERE id_categoria_insumo = %s
        """

        cursor.execute(sql, (id_categoria,))
        fila = cursor.fetchone()

        if fila is None:
            return jsonify({
                'mensaje': 'Categoria no encontrada'
            }), 404

        categoria = {
            'id_categoria_insumo': fila[0],
            'nombre': fila[1],
            'descripcion': fila[2]
        }

        return jsonify(categoria), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar la categoria',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# REGISTRAR CATEGORIA
# ==========================================

@categorias_insumos_bp.route('/', methods=['POST'])
def registrar_categoria():

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos en formato JSON'
            }), 400

        nombre = datos.get('nombre')
        descripcion = datos.get('descripcion')

        if not nombre or not nombre.strip():
            return jsonify({
                'mensaje': 'El nombre de la categoria es obligatorio'
            }), 400

        nombre = nombre.strip()

        if len(nombre) > 100:
            return jsonify({
                'mensaje': 'El nombre no puede superar los 100 caracteres'
            }), 400

        cursor = mysql.connection.cursor()

        sql = """
            INSERT INTO categorias_insumos
            (nombre, descripcion)
            VALUES (%s, %s)
        """

        cursor.execute(sql, (nombre, descripcion))

        mysql.connection.commit()

        id_nuevo = cursor.lastrowid

        return jsonify({
            'mensaje': 'Categoria registrada correctamente',
            'id_categoria_insumo': id_nuevo
        }), 201

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al registrar la categoria. Verifica que el nombre no exista.',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# ACTUALIZAR CATEGORIA
# ==========================================

@categorias_insumos_bp.route('/<int:id_categoria>', methods=['PUT'])
def actualizar_categoria(id_categoria):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos en formato JSON'
            }), 400

        nombre = datos.get('nombre')
        descripcion = datos.get('descripcion')

        if not nombre or not nombre.strip():
            return jsonify({
                'mensaje': 'El nombre de la categoria es obligatorio'
            }), 400

        nombre = nombre.strip()

        if len(nombre) > 100:
            return jsonify({
                'mensaje': 'El nombre no puede superar los 100 caracteres'
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            SELECT id_categoria_insumo
            FROM categorias_insumos
            WHERE id_categoria_insumo = %s
            """,
            (id_categoria,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                'mensaje': 'Categoria no encontrada'
            }), 404

        sql = """
            UPDATE categorias_insumos
            SET nombre = %s,
                descripcion = %s
            WHERE id_categoria_insumo = %s
        """

        cursor.execute(sql, (
            nombre,
            descripcion,
            id_categoria
        ))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Categoria actualizada correctamente'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al actualizar la categoria. Verifica que el nombre no exista.',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# ELIMINAR CATEGORIA
# ==========================================

@categorias_insumos_bp.route('/<int:id_categoria>', methods=['DELETE'])
def eliminar_categoria(id_categoria):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            SELECT id_categoria_insumo
            FROM categorias_insumos
            WHERE id_categoria_insumo = %s
            """,
            (id_categoria,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                'mensaje': 'Categoria no encontrada'
            }), 404

        # Verificar si tiene materias primas relacionadas
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM materias_primas
            WHERE id_categoria_insumo = %s
            """,
            (id_categoria,)
        )

        cantidad = cursor.fetchone()[0]

        if cantidad > 0:
            return jsonify({
                'mensaje': 'No se puede eliminar la categoria porque tiene materias primas relacionadas'
            }), 409

        cursor.execute(
            """
            DELETE FROM categorias_insumos
            WHERE id_categoria_insumo = %s
            """,
            (id_categoria,)
        )

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Categoria eliminada correctamente'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al eliminar la categoria',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()
