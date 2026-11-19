
from flask import Blueprint, request, jsonify
from database import mysql
from decimal import Decimal, InvalidOperation

inventario_bp = Blueprint(
    'inventario',
    __name__,
    url_prefix='/api/inventario'
)


def convertir_decimal(valor):
    try:
        numero = Decimal(str(valor))

        if not numero.is_finite():
            return None

        return numero

    except (InvalidOperation, TypeError, ValueError):
        return None


def validar_usuario(cursor, id_usuario):
    if id_usuario is None:
        return True

    cursor.execute(
        """
        SELECT id_usuario
        FROM usuarios
        WHERE id_usuario = %s AND estado = 1
        """,
        (id_usuario,)
    )

    return cursor.fetchone() is not None


def registrar_movimiento(
    id_materia_prima,
    tipo_movimiento,
    cantidad,
    motivo,
    id_usuario=None
):
    """
    Actualiza las existencias y registra el movimiento
    dentro de una misma transacción.
    """

    cursor = mysql.connection.cursor()

    try:
        # Validar materia prima y bloquear su registro.
        cursor.execute(
            """
            SELECT stock_actual, estado
            FROM materias_primas
            WHERE id_materia_prima = %s
            FOR UPDATE
            """,
            (id_materia_prima,)
        )

        materia = cursor.fetchone()

        if not materia:
            mysql.connection.rollback()
            return None, ('La materia prima no existe.', 404)

        stock_actual = Decimal(str(materia[0]))
        estado = materia[1]

        if estado != 1:
            mysql.connection.rollback()
            return None, ('La materia prima está inactiva.', 400)

        if not validar_usuario(cursor, id_usuario):
            mysql.connection.rollback()
            return None, ('El usuario indicado no existe o está inactivo.', 400)

        # Calcular el nuevo stock según el movimiento.
        if tipo_movimiento in ('AjusteEntrada',):
            nuevo_stock = stock_actual + cantidad

        elif tipo_movimiento in ('AjusteSalida', 'Merma'):
            if stock_actual < cantidad:
                mysql.connection.rollback()
                return None, (
                    'No hay existencias suficientes para realizar la salida.',
                    400
                )

            nuevo_stock = stock_actual - cantidad

        else:
            mysql.connection.rollback()
            return None, ('Tipo de movimiento no válido.', 400)

        # Actualizar existencias.
        cursor.execute(
            """
            UPDATE materias_primas
            SET stock_actual = %s
            WHERE id_materia_prima = %s
            """,
            (nuevo_stock, id_materia_prima)
        )

        # Registrar el movimiento.
        cursor.execute(
            """
            INSERT INTO movimientos_inventario (
                id_materia_prima,
                id_usuario,
                tipo_movimiento,
                cantidad,
                motivo
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                id_materia_prima,
                id_usuario,
                tipo_movimiento,
                cantidad,
                motivo
            )
        )

        mysql.connection.commit()

        return {
            'id_materia_prima': id_materia_prima,
            'tipo_movimiento': tipo_movimiento,
            'cantidad': float(cantidad),
            'stock_anterior': float(stock_actual),
            'stock_nuevo': float(nuevo_stock)
        }, None

    except Exception as e:
        mysql.connection.rollback()
        return None, (f'Error al registrar el movimiento: {str(e)}', 500)

    finally:
        cursor.close()


# ==========================================
# GET: Consultar inventario completo
# ==========================================

@inventario_bp.route('/', methods=['GET'])
def obtener_inventario():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                mp.id_materia_prima,
                mp.nombre,
                mp.unidad_medida,
                mp.stock_actual,
                mp.stock_minimo,
                mp.costo_unitario,
                mp.estado,
                ci.nombre AS categoria,
                CASE
                    WHEN mp.stock_actual <= mp.stock_minimo THEN 1
                    ELSE 0
                END AS stock_bajo
            FROM materias_primas mp
            INNER JOIN categorias_insumos ci
                ON mp.id_categoria_insumo = ci.id_categoria_insumo
            ORDER BY mp.nombre
            """
        )

        columnas = [columna[0] for columna in cursor.description]
        resultados = cursor.fetchall()

        inventario = []

        for fila in resultados:
            registro = dict(zip(columnas, fila))

            registro['stock_actual'] = float(registro['stock_actual'])
            registro['stock_minimo'] = float(registro['stock_minimo'])
            registro['costo_unitario'] = float(registro['costo_unitario'])
            registro['stock_bajo'] = bool(registro['stock_bajo'])

            inventario.append(registro)

        return jsonify(inventario), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar el inventario.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Consultar alertas de stock bajo
# ==========================================

@inventario_bp.route('/alertas', methods=['GET'])
def obtener_alertas():
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                mp.id_materia_prima,
                mp.nombre,
                mp.unidad_medida,
                mp.stock_actual,
                mp.stock_minimo,
                ci.nombre AS categoria
            FROM materias_primas mp
            INNER JOIN categorias_insumos ci
                ON mp.id_categoria_insumo = ci.id_categoria_insumo
            WHERE mp.estado = 1
              AND mp.stock_actual <= mp.stock_minimo
            ORDER BY mp.stock_actual ASC
            """
        )

        columnas = [columna[0] for columna in cursor.description]
        resultados = cursor.fetchall()

        alertas = []

        for fila in resultados:
            registro = dict(zip(columnas, fila))
            registro['stock_actual'] = float(registro['stock_actual'])
            registro['stock_minimo'] = float(registro['stock_minimo'])
            alertas.append(registro)

        return jsonify({
            'total_alertas': len(alertas),
            'alertas': alertas
        }), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar las alertas.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Historial de movimientos de una materia
# ==========================================

@inventario_bp.route('/<int:id_materia_prima>/movimientos', methods=['GET'])
def obtener_movimientos(id_materia_prima):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id_materia_prima, nombre, unidad_medida
            FROM materias_primas
            WHERE id_materia_prima = %s
            """,
            (id_materia_prima,)
        )

        materia = cursor.fetchone()

        if not materia:
            return jsonify({
                'mensaje': 'La materia prima no existe.'
            }), 404

        cursor.execute(
            """
            SELECT
                mi.id_movimiento,
                mi.tipo_movimiento,
                mi.cantidad,
                mi.motivo,
                mi.fecha_movimiento,
                mi.id_usuario,
                u.nombre AS usuario
            FROM movimientos_inventario mi
            LEFT JOIN usuarios u
                ON mi.id_usuario = u.id_usuario
            WHERE mi.id_materia_prima = %s
            ORDER BY mi.fecha_movimiento DESC, mi.id_movimiento DESC
            """,
            (id_materia_prima,)
        )

        columnas = [columna[0] for columna in cursor.description]
        resultados = cursor.fetchall()

        movimientos = []

        for fila in resultados:
            registro = dict(zip(columnas, fila))
            registro['cantidad'] = float(registro['cantidad'])

            if registro['fecha_movimiento']:
                registro['fecha_movimiento'] = str(
                    registro['fecha_movimiento']
                )

            movimientos.append(registro)

        return jsonify({
            'materia_prima': {
                'id_materia_prima': materia[0],
                'nombre': materia[1],
                'unidad_medida': materia[2]
            },
            'movimientos': movimientos
        }), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar los movimientos.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# POST: Registrar ajuste de inventario
# ==========================================

@inventario_bp.route('/ajuste', methods=['POST'])
def registrar_ajuste():
    datos = request.get_json()

    if not datos:
        return jsonify({
            'mensaje': 'Debes enviar los datos del ajuste.'
        }), 400

    id_materia_prima = datos.get('id_materia_prima')
    tipo_movimiento = datos.get('tipo_movimiento')
    cantidad = convertir_decimal(datos.get('cantidad'))
    motivo = datos.get('motivo')
    id_usuario = datos.get('id_usuario')

    if not id_materia_prima or not tipo_movimiento or cantidad is None or not motivo:
        return jsonify({
            'mensaje': 'Faltan datos obligatorios.'
        }), 400

    if tipo_movimiento not in ('AjusteEntrada', 'AjusteSalida'):
        return jsonify({
            'mensaje': 'El tipo debe ser AjusteEntrada o AjusteSalida.'
        }), 400

    if cantidad <= 0:
        return jsonify({
            'mensaje': 'La cantidad debe ser mayor que cero.'
        }), 400

    if not isinstance(motivo, str) or not motivo.strip():
        return jsonify({
            'mensaje': 'El motivo debe ser un texto válido.'
        }), 400

    resultado, error = registrar_movimiento(
        id_materia_prima,
        tipo_movimiento,
        cantidad,
        motivo.strip(),
        id_usuario
    )

    if error:
        return jsonify({'mensaje': error[0]}), error[1]

    return jsonify({
        'mensaje': 'Ajuste de inventario registrado correctamente.',
        'resultado': resultado
    }), 201


# ==========================================
# POST: Registrar merma
# ==========================================

@inventario_bp.route('/merma', methods=['POST'])
def registrar_merma():
    datos = request.get_json()

    if not datos:
        return jsonify({
            'mensaje': 'Debes enviar los datos de la merma.'
        }), 400

    id_materia_prima = datos.get('id_materia_prima')
    cantidad = convertir_decimal(datos.get('cantidad'))
    motivo = datos.get('motivo')
    id_usuario = datos.get('id_usuario')

    if not id_materia_prima or cantidad is None or not motivo:
        return jsonify({
            'mensaje': 'Faltan datos obligatorios.'
        }), 400

    if cantidad <= 0:
        return jsonify({
            'mensaje': 'La cantidad debe ser mayor que cero.'
        }), 400

    if not isinstance(motivo, str) or not motivo.strip():
        return jsonify({
            'mensaje': 'El motivo debe ser un texto válido.'
        }), 400

    resultado, error = registrar_movimiento(
        id_materia_prima,
        'Merma',
        cantidad,
        motivo.strip(),
        id_usuario
    )

    if error:
        return jsonify({'mensaje': error[0]}), error[1]

    return jsonify({
        'mensaje': 'Merma registrada correctamente.',
        'resultado': resultado
    }), 201
