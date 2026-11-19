
from flask import Blueprint, request, jsonify
from database import mysql
from decimal import Decimal, InvalidOperation


materias_primas_bp = Blueprint(
    'materias_primas',
    __name__,
    url_prefix='/api/materias-primas'
)


# ==========================================
# CONSULTAR TODAS LAS MATERIAS PRIMAS
# ==========================================

@materias_primas_bp.route('/', methods=['GET'])
def obtener_materias_primas():

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                m.id_materia_prima,
                m.id_categoria_insumo,
                c.nombre,
                m.nombre,
                m.unidad_medida,
                m.stock_actual,
                m.stock_minimo,
                m.costo_unitario,
                m.estado
            FROM materias_primas m
            INNER JOIN categorias_insumos c
                ON m.id_categoria_insumo = c.id_categoria_insumo
            ORDER BY m.id_materia_prima ASC
        """

        cursor.execute(sql)
        resultados = cursor.fetchall()

        materias = []

        for fila in resultados:
            materias.append({
                'id_materia_prima': fila[0],
                'id_categoria_insumo': fila[1],
                'categoria': fila[2],
                'nombre': fila[3],
                'unidad_medida': fila[4],
                'stock_actual': float(fila[5]),
                'stock_minimo': float(fila[6]),
                'costo_unitario': float(fila[7]),
                'estado': fila[8]
            })

        return jsonify(materias), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar las materias primas',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# CONSULTAR MATERIA PRIMA POR ID
# ==========================================

@materias_primas_bp.route('/<int:id_materia_prima>', methods=['GET'])
def obtener_materia_prima(id_materia_prima):

    cursor = None

    try:
        cursor = mysql.connection.cursor()

        sql = """
            SELECT
                m.id_materia_prima,
                m.id_categoria_insumo,
                c.nombre,
                m.nombre,
                m.unidad_medida,
                m.stock_actual,
                m.stock_minimo,
                m.costo_unitario,
                m.estado
            FROM materias_primas m
            INNER JOIN categorias_insumos c
                ON m.id_categoria_insumo = c.id_categoria_insumo
            WHERE m.id_materia_prima = %s
        """

        cursor.execute(sql, (id_materia_prima,))
        fila = cursor.fetchone()

        if fila is None:
            return jsonify({
                'mensaje': 'Materia prima no encontrada'
            }), 404

        materia = {
            'id_materia_prima': fila[0],
            'id_categoria_insumo': fila[1],
            'categoria': fila[2],
            'nombre': fila[3],
            'unidad_medida': fila[4],
            'stock_actual': float(fila[5]),
            'stock_minimo': float(fila[6]),
            'costo_unitario': float(fila[7]),
            'estado': fila[8]
        }

        return jsonify(materia), 200

    except Exception as error:
        return jsonify({
            'mensaje': 'Error al consultar la materia prima',
            'error': str(error)
        }), 500

    finally:
        if cursor:
            cursor.close()


# ==========================================
# REGISTRAR MATERIA PRIMA
# ==========================================

@materias_primas_bp.route('/', methods=['POST'])
def registrar_materia_prima():

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos en formato JSON'
            }), 400

        id_categoria = datos.get('id_categoria_insumo')
        nombre = datos.get('nombre')
        unidad = datos.get('unidad_medida')
        stock_minimo = datos.get('stock_minimo', 0)
        costo_unitario = datos.get('costo_unitario', 0)

        if not id_categoria or not nombre or not unidad:
            return jsonify({
                'mensaje': 'La categoría, el nombre y la unidad de medida son obligatorios'
            }), 400

        nombre = nombre.strip()
        unidad = unidad.strip()

        if not nombre or not unidad:
            return jsonify({
                'mensaje': 'El nombre y la unidad de medida no pueden estar vacíos'
            }), 400

        if len(nombre) > 120 or len(unidad) > 20:
            return jsonify({
                'mensaje': 'El nombre o la unidad supera la longitud permitida'
            }), 400

        try:
            stock_minimo = Decimal(str(stock_minimo))
            costo_unitario = Decimal(str(costo_unitario))
        except (InvalidOperation, ValueError):
            return jsonify({
                'mensaje': 'El stock mínimo y el costo deben ser valores numéricos'
            }), 400

        if not stock_minimo.is_finite() or not costo_unitario.is_finite():
            return jsonify({
                'mensaje': 'Los valores numéricos no son válidos'
            }), 400

        if stock_minimo < 0 or costo_unitario < 0:
            return jsonify({
                'mensaje': 'El stock mínimo y el costo no pueden ser negativos'
            }), 400

        cursor = mysql.connection.cursor()

        sql = """
            INSERT INTO materias_primas
            (
                id_categoria_insumo,
                nombre,
                unidad_medida,
                stock_actual,
                stock_minimo,
                costo_unitario,
                estado
            )
            VALUES (%s, %s, %s, 0, %s, %s, 1)
        """

        cursor.execute(sql, (
            id_categoria,
            nombre,
            unidad,
            stock_minimo,
            costo_unitario
        ))

        mysql.connection.commit()

        id_nuevo = cursor.lastrowid

        return jsonify({
            'mensaje': 'Materia prima registrada correctamente',
            'id_materia_prima': id_nuevo
        }), 201

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al registrar la materia prima. Verifica que la categoría exista.',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# ACTUALIZAR MATERIA PRIMA
# ==========================================

@materias_primas_bp.route('/<int:id_materia_prima>', methods=['PUT'])
def actualizar_materia_prima(id_materia_prima):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos:
            return jsonify({
                'mensaje': 'Debes enviar los datos en formato JSON'
            }), 400

        id_categoria = datos.get('id_categoria_insumo')
        nombre = datos.get('nombre')
        unidad = datos.get('unidad_medida')
        stock_minimo = datos.get('stock_minimo')
        costo_unitario = datos.get('costo_unitario')

        if (
            id_categoria is None
            or not nombre
            or not unidad
            or stock_minimo is None
            or costo_unitario is None
        ):
            return jsonify({
                'mensaje': 'Todos los campos son obligatorios'
            }), 400

        nombre = nombre.strip()
        unidad = unidad.strip()

        if not nombre or not unidad:
            return jsonify({
                'mensaje': 'El nombre y la unidad no pueden estar vacíos'
            }), 400

        if len(nombre) > 120 or len(unidad) > 20:
            return jsonify({
                'mensaje': 'El nombre o la unidad supera la longitud permitida'
            }), 400

        try:
            stock_minimo = Decimal(str(stock_minimo))
            costo_unitario = Decimal(str(costo_unitario))
        except (InvalidOperation, ValueError):
            return jsonify({
                'mensaje': 'El stock mínimo y el costo deben ser valores numéricos'
            }), 400

        if not stock_minimo.is_finite() or not costo_unitario.is_finite():
            return jsonify({
                'mensaje': 'Los valores numéricos no son válidos'
            }), 400

        if stock_minimo < 0 or costo_unitario < 0:
            return jsonify({
                'mensaje': 'El stock mínimo y el costo no pueden ser negativos'
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            SELECT id_materia_prima
            FROM materias_primas
            WHERE id_materia_prima = %s
            """,
            (id_materia_prima,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                'mensaje': 'Materia prima no encontrada'
            }), 404

        sql = """
            UPDATE materias_primas
            SET id_categoria_insumo = %s,
                nombre = %s,
                unidad_medida = %s,
                stock_minimo = %s,
                costo_unitario = %s
            WHERE id_materia_prima = %s
        """

        cursor.execute(sql, (
            id_categoria,
            nombre,
            unidad,
            stock_minimo,
            costo_unitario,
            id_materia_prima
        ))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Materia prima actualizada correctamente'
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al actualizar la materia prima. Verifica que la categoría exista.',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()


# ==========================================
# CAMBIAR ESTADO DE MATERIA PRIMA
# ==========================================

@materias_primas_bp.route('/<int:id_materia_prima>/estado', methods=['PATCH'])
def cambiar_estado_materia_prima(id_materia_prima):

    cursor = None

    try:
        datos = request.get_json(silent=True)

        if not datos or 'estado' not in datos:
            return jsonify({
                'mensaje': 'Debes indicar el estado de la materia prima'
            }), 400

        estado = datos['estado']

        if type(estado) is not int or estado not in (0, 1):
            return jsonify({
                'mensaje': 'El estado debe ser 1 (activo) o 0 (inactivo)'
            }), 400

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            UPDATE materias_primas
            SET estado = %s
            WHERE id_materia_prima = %s
            """,
            (estado, id_materia_prima)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                """
                SELECT id_materia_prima
                FROM materias_primas
                WHERE id_materia_prima = %s
                """,
                (id_materia_prima,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    'mensaje': 'Materia prima no encontrada'
                }), 404

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Estado de la materia prima actualizado correctamente',
            'estado': estado
        }), 200

    except Exception as error:
        mysql.connection.rollback()

        return jsonify({
            'mensaje': 'Error al cambiar el estado de la materia prima',
            'error': str(error)
        }), 400

    finally:
        if cursor:
            cursor.close()
