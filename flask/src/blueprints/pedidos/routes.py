
from flask import Blueprint, request, jsonify
from database import mysql
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


pedidos_bp = Blueprint(
    'pedidos',
    __name__,
    url_prefix='/api'
)

# Por ahora la entrega tiene costo cero.
# Cuando definamos una tarifa, se modifica aquí.
COSTO_ENTREGA = Decimal('0.00')


def convertir_decimal(valor):
    try:
        numero = Decimal(str(valor))

        if not numero.is_finite():
            return None

        return numero

    except (InvalidOperation, TypeError, ValueError):
        return None


def dinero(valor):
    return valor.quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )


def obtener_carrito_activo(cursor, id_cliente, bloquear=False):
    consulta = """
        SELECT id_carrito
        FROM carritos
        WHERE id_cliente = %s
          AND estado = 'Activo'
        ORDER BY id_carrito DESC
        LIMIT 1
    """

    if bloquear:
        consulta += " FOR UPDATE"

    cursor.execute(consulta, (id_cliente,))
    carrito = cursor.fetchone()

    return carrito[0] if carrito else None


# ==========================================
# GET: Consultar carrito de un cliente
# ==========================================

@pedidos_bp.route(
    '/carrito/<int:id_cliente>',
    methods=['GET']
)
def obtener_carrito(id_cliente):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_cliente
            FROM clientes
            WHERE id_cliente = %s
        """, (id_cliente,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'El cliente no existe.'
            }), 404

        id_carrito = obtener_carrito_activo(cursor, id_cliente)

        if not id_carrito:
            return jsonify({
                'id_carrito': None,
                'id_cliente': id_cliente,
                'productos': [],
                'subtotal': 0
            }), 200

        cursor.execute("""
            SELECT
                dc.id_detalle_carrito,
                dc.id_producto,
                p.nombre,
                p.descripcion,
                p.imagen,
                p.precio,
                dc.cantidad,
                (p.precio * dc.cantidad) AS subtotal
            FROM detalle_carrito dc
            INNER JOIN productos p
                ON dc.id_producto = p.id_producto
            WHERE dc.id_carrito = %s
            ORDER BY p.nombre
        """, (id_carrito,))

        productos = []
        subtotal = Decimal('0.00')

        for fila in cursor.fetchall():
            precio = Decimal(str(fila[5]))
            cantidad = int(fila[6])
            subtotal_producto = dinero(precio * cantidad)

            productos.append({
                'id_detalle_carrito': fila[0],
                'id_producto': fila[1],
                'nombre': fila[2],
                'descripcion': fila[3],
                'imagen': fila[4],
                'precio': float(precio),
                'cantidad': cantidad,
                'subtotal': float(subtotal_producto)
            })

            subtotal += subtotal_producto

        return jsonify({
            'id_carrito': id_carrito,
            'id_cliente': id_cliente,
            'productos': productos,
            'subtotal': float(dinero(subtotal))
        }), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar el carrito.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# POST: Agregar producto al carrito
# ==========================================

@pedidos_bp.route(
    '/carrito/<int:id_cliente>/productos',
    methods=['POST']
)
def agregar_producto_carrito(id_cliente):
    datos = request.get_json()

    if not datos:
        return jsonify({
            'mensaje': 'Debes enviar los datos.'
        }), 400

    id_producto = datos.get('id_producto')
    cantidad = datos.get('cantidad')

    if (
        not isinstance(id_producto, int)
        or isinstance(id_producto, bool)
        or id_producto <= 0
    ):
        return jsonify({
            'mensaje': 'El producto indicado no es válido.'
        }), 400

    if (
        not isinstance(cantidad, int)
        or isinstance(cantidad, bool)
        or cantidad <= 0
    ):
        return jsonify({
            'mensaje': 'La cantidad debe ser un entero mayor que cero.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_cliente
            FROM clientes
            WHERE id_cliente = %s
        """, (id_cliente,))

        if not cursor.fetchone():
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El cliente no existe.'
            }), 404

        cursor.execute("""
            SELECT id_producto, nombre, precio
            FROM productos
            WHERE id_producto = %s
              AND disponible = 1
        """, (id_producto,))

        producto = cursor.fetchone()

        if not producto:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El producto no existe o no está disponible.'
            }), 404

        # Buscar o crear el carrito activo.
        id_carrito = obtener_carrito_activo(
            cursor,
            id_cliente,
            bloquear=True
        )

        if not id_carrito:
            cursor.execute("""
                INSERT INTO carritos (
                    id_cliente,
                    fecha_creacion,
                    estado
                )
                VALUES (%s, NOW(), 'Activo')
            """, (id_cliente,))

            id_carrito = cursor.lastrowid

        # Revisar si el producto ya está en el carrito.
        cursor.execute("""
            SELECT id_detalle_carrito, cantidad
            FROM detalle_carrito
            WHERE id_carrito = %s
              AND id_producto = %s
            FOR UPDATE
        """, (id_carrito, id_producto))

        detalle = cursor.fetchone()

        if detalle:
            nueva_cantidad = detalle[1] + cantidad

            cursor.execute("""
                UPDATE detalle_carrito
                SET cantidad = %s
                WHERE id_detalle_carrito = %s
            """, (nueva_cantidad, detalle[0]))

        else:
            cursor.execute("""
                INSERT INTO detalle_carrito (
                    id_carrito,
                    id_producto,
                    cantidad
                )
                VALUES (%s, %s, %s)
            """, (id_carrito, id_producto, cantidad))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Producto agregado al carrito.',
            'id_carrito': id_carrito,
            'id_producto': id_producto
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo agregar el producto.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# PUT: Modificar cantidad de un producto
# ==========================================

@pedidos_bp.route(
    '/carrito/<int:id_cliente>/productos/<int:id_producto>',
    methods=['PUT']
)
def actualizar_cantidad_carrito(id_cliente, id_producto):
    datos = request.get_json()

    if not datos or 'cantidad' not in datos:
        return jsonify({
            'mensaje': 'Debes indicar la cantidad.'
        }), 400

    cantidad = datos.get('cantidad')

    if (
        not isinstance(cantidad, int)
        or isinstance(cantidad, bool)
        or cantidad <= 0
    ):
        return jsonify({
            'mensaje': 'La cantidad debe ser un entero mayor que cero.'
        }), 400

    cursor = mysql.connection.cursor()

    try:
        id_carrito = obtener_carrito_activo(
            cursor,
            id_cliente,
            bloquear=True
        )

        if not id_carrito:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El cliente no tiene un carrito activo.'
            }), 404

        cursor.execute("""
            UPDATE detalle_carrito
            SET cantidad = %s
            WHERE id_carrito = %s
              AND id_producto = %s
        """, (cantidad, id_carrito, id_producto))

        if cursor.rowcount == 0:
            cursor.execute("""
                SELECT id_detalle_carrito
                FROM detalle_carrito
                WHERE id_carrito = %s
                  AND id_producto = %s
            """, (id_carrito, id_producto))

            if not cursor.fetchone():
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': 'El producto no está en el carrito.'
                }), 404

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Cantidad actualizada correctamente.'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo actualizar la cantidad.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# DELETE: Eliminar producto del carrito
# ==========================================

@pedidos_bp.route(
    '/carrito/<int:id_cliente>/productos/<int:id_producto>',
    methods=['DELETE']
)
def eliminar_producto_carrito(id_cliente, id_producto):
    cursor = mysql.connection.cursor()

    try:
        id_carrito = obtener_carrito_activo(
            cursor,
            id_cliente,
            bloquear=True
        )

        if not id_carrito:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El cliente no tiene un carrito activo.'
            }), 404

        cursor.execute("""
            DELETE FROM detalle_carrito
            WHERE id_carrito = %s
              AND id_producto = %s
        """, (id_carrito, id_producto))

        if cursor.rowcount == 0:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El producto no está en el carrito.'
            }), 404

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Producto eliminado del carrito.'
        }), 200

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo eliminar el producto.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# POST: Confirmar carrito y crear pedido
# ==========================================

@pedidos_bp.route(
    '/pedidos/confirmar/<int:id_cliente>',
    methods=['POST']
)
def confirmar_pedido(id_cliente):
    datos = request.get_json() or {}

    tipo_entrega = datos.get('tipo_entrega')
    id_direccion = datos.get('id_direccion')
    observaciones = datos.get('observaciones')

    tipos_validos = ('Domicilio', 'Recoger')

    if tipo_entrega not in tipos_validos:
        return jsonify({
            'mensaje': 'El tipo de entrega debe ser Domicilio o Recoger.'
        }), 400

    if tipo_entrega == 'Domicilio' and not id_direccion:
        return jsonify({
            'mensaje': 'Debes seleccionar una dirección para la entrega.'
        }), 400

    if tipo_entrega == 'Recoger':
        id_direccion = None

    cursor = mysql.connection.cursor()

    try:
        # Bloquear el carrito para evitar confirmaciones simultáneas.
        id_carrito = obtener_carrito_activo(
            cursor,
            id_cliente,
            bloquear=True
        )

        if not id_carrito:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'No tienes un carrito activo.'
            }), 404

        # Verificar que el cliente exista y consultar su descuento.
        cursor.execute("""
            SELECT
                c.id_cliente,
                c.id_descuento,
                c.estado_acreditacion,
                d.porcentaje,
                d.estado
            FROM clientes c
            LEFT JOIN descuentos d
                ON c.id_descuento = d.id_descuento
            WHERE c.id_cliente = %s
            FOR UPDATE
        """, (id_cliente,))

        cliente = cursor.fetchone()

        if not cliente:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El cliente no existe.'
            }), 404

        # Validar dirección y pertenencia al cliente.
        if tipo_entrega == 'Domicilio':
            cursor.execute("""
                SELECT id_direccion
                FROM direcciones
                WHERE id_direccion = %s
                  AND id_cliente = %s
            """, (id_direccion, id_cliente))

            if not cursor.fetchone():
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': 'La dirección no existe o no pertenece al cliente.'
                }), 400

        # Consultar los productos del carrito con sus precios actuales.
        cursor.execute("""
            SELECT
                dc.id_producto,
                dc.cantidad,
                p.nombre,
                p.precio,
                p.disponible
            FROM detalle_carrito dc
            INNER JOIN productos p
                ON dc.id_producto = p.id_producto
            WHERE dc.id_carrito = %s
            FOR UPDATE
        """, (id_carrito,))

        productos = cursor.fetchall()

        if not productos:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El carrito está vacío.'
            }), 400

        subtotal = Decimal('0.00')

        detalles = []

        for producto in productos:
            id_producto = producto[0]
            cantidad = int(producto[1])
            nombre = producto[2]
            precio = Decimal(str(producto[3]))
            disponible = producto[4]

            if disponible != 1:
                mysql.connection.rollback()
                return jsonify({
                    'mensaje': f'El producto {nombre} ya no está disponible.'
                }), 400

            subtotal_producto = dinero(precio * cantidad)
            subtotal += subtotal_producto

            detalles.append({
                'id_producto': id_producto,
                'nombre': nombre,
                'cantidad': cantidad,
                'precio': precio,
                'subtotal': subtotal_producto
            })

        subtotal = dinero(subtotal)

        # Aplicar descuento solamente si la acreditación está validada
        # y el descuento continúa activo.
        porcentaje_descuento = Decimal('0.00')

        id_descuento = cliente[1]
        estado_acreditacion = cliente[2]
        porcentaje_bd = cliente[3]
        estado_descuento = cliente[4]

        if (
            id_descuento is not None
            and estado_acreditacion == 'Validada'
            and porcentaje_bd is not None
            and estado_descuento == 1
        ):
            porcentaje_descuento = Decimal(str(porcentaje_bd))

        if porcentaje_descuento < 0 or porcentaje_descuento > 100:
            mysql.connection.rollback()
            return jsonify({
                'mensaje': 'El porcentaje de descuento configurado no es válido.'
            }), 400

        monto_descuento = dinero(
            subtotal * porcentaje_descuento / Decimal('100')
        )

        costo_entrega = (
            COSTO_ENTREGA
            if tipo_entrega == 'Domicilio'
            else Decimal('0.00')
        )

        total = dinero(
            subtotal - monto_descuento + costo_entrega
        )

        # Crear pedido.
        cursor.execute("""
            INSERT INTO pedidos (
                id_cliente,
                id_usuario,
                id_direccion,
                fecha_pedido,
                tipo_entrega,
                subtotal,
                porcentaje_descuento,
                monto_descuento,
                costo_entrega,
                total,
                estado,
                observaciones
            )
            VALUES (
                %s, NULL, %s, NOW(), %s, %s, %s, %s, %s, %s,
                'Pendiente', %s
            )
        """, (
            id_cliente,
            id_direccion,
            tipo_entrega,
            subtotal,
            porcentaje_descuento,
            monto_descuento,
            costo_entrega,
            total,
            observaciones
        ))

        id_pedido = cursor.lastrowid

        # Guardar los productos y precios históricos del pedido.
        for detalle in detalles:
            cursor.execute("""
                INSERT INTO detalle_pedidos (
                    id_pedido,
                    id_producto,
                    nombre_producto,
                    cantidad,
                    precio_unitario,
                    subtotal
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                id_pedido,
                detalle['id_producto'],
                detalle['nombre'],
                detalle['cantidad'],
                detalle['precio'],
                detalle['subtotal']
            ))

        # Registrar el primer estado en el historial.
        cursor.execute("""
            INSERT INTO historial_pedidos (
                id_pedido,
                id_usuario,
                estado,
                comentario,
                fecha_cambio
            )
            VALUES (%s, NULL, 'Pendiente', 'Pedido creado por el cliente', NOW())
        """, (id_pedido,))

        # Marcar el carrito como convertido.
        cursor.execute("""
            UPDATE carritos
            SET estado = 'Convertido'
            WHERE id_carrito = %s
        """, (id_carrito,))

        mysql.connection.commit()

        return jsonify({
            'mensaje': 'Pedido confirmado correctamente.',
            'id_pedido': id_pedido,
            'subtotal': float(subtotal),
            'porcentaje_descuento': float(porcentaje_descuento),
            'monto_descuento': float(monto_descuento),
            'costo_entrega': float(costo_entrega),
            'total': float(total),
            'estado': 'Pendiente'
        }), 201

    except Exception as e:
        mysql.connection.rollback()
        return jsonify({
            'mensaje': 'No se pudo confirmar el pedido.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Historial de pedidos de un cliente
# ==========================================

@pedidos_bp.route(
    '/pedidos/cliente/<int:id_cliente>',
    methods=['GET']
)
def obtener_pedidos_cliente(id_cliente):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT id_cliente
            FROM clientes
            WHERE id_cliente = %s
        """, (id_cliente,))

        if not cursor.fetchone():
            return jsonify({
                'mensaje': 'El cliente no existe.'
            }), 404

        cursor.execute("""
            SELECT
                id_pedido,
                fecha_pedido,
                tipo_entrega,
                subtotal,
                porcentaje_descuento,
                monto_descuento,
                costo_entrega,
                total,
                estado,
                observaciones
            FROM pedidos
            WHERE id_cliente = %s
            ORDER BY fecha_pedido DESC
        """, (id_cliente,))

        columnas = [col[0] for col in cursor.description]
        pedidos = []

        for fila in cursor.fetchall():
            pedido = dict(zip(columnas, fila))

            for campo in (
                'subtotal',
                'porcentaje_descuento',
                'monto_descuento',
                'costo_entrega',
                'total'
            ):
                pedido[campo] = float(pedido[campo])

            if pedido['fecha_pedido']:
                pedido['fecha_pedido'] = str(
                    pedido['fecha_pedido']
                )

            pedidos.append(pedido)

        return jsonify(pedidos), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar los pedidos.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()


# ==========================================
# GET: Consultar detalle de un pedido
# ==========================================

@pedidos_bp.route(
    '/pedidos/<int:id_pedido>',
    methods=['GET']
)
def obtener_detalle_pedido(id_pedido):
    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            SELECT
                p.id_pedido,
                p.id_cliente,
                c.id_usuario,
                p.id_direccion,
                p.fecha_pedido,
                p.tipo_entrega,
                p.subtotal,
                p.porcentaje_descuento,
                p.monto_descuento,
                p.costo_entrega,
                p.total,
                p.estado,
                p.observaciones
            FROM pedidos p
            LEFT JOIN clientes c
                ON p.id_cliente = c.id_cliente
            WHERE p.id_pedido = %s
        """, (id_pedido,))

        fila = cursor.fetchone()

        if not fila:
            return jsonify({
                'mensaje': 'El pedido no existe.'
            }), 404

        columnas = [col[0] for col in cursor.description]
        pedido = dict(zip(columnas, fila))

        for campo in (
            'subtotal',
            'porcentaje_descuento',
            'monto_descuento',
            'costo_entrega',
            'total'
        ):
            pedido[campo] = float(pedido[campo])

        if pedido['fecha_pedido']:
            pedido['fecha_pedido'] = str(
                pedido['fecha_pedido']
            )

        cursor.execute("""
            SELECT
                id_detalle_pedido,
                id_producto,
                nombre_producto,
                cantidad,
                precio_unitario,
                subtotal
            FROM detalle_pedidos
            WHERE id_pedido = %s
            ORDER BY id_detalle_pedido
        """, (id_pedido,))

        columnas_detalle = [
            col[0] for col in cursor.description
        ]

        detalles = []

        for fila_detalle in cursor.fetchall():
            detalle = dict(zip(columnas_detalle, fila_detalle))
            detalle['precio_unitario'] = float(
                detalle['precio_unitario']
            )
            detalle['subtotal'] = float(detalle['subtotal'])
            detalles.append(detalle)

        pedido['productos'] = detalles

        cursor.execute("""
            SELECT
                estado,
                comentario,
                fecha_cambio
            FROM historial_pedidos
            WHERE id_pedido = %s
            ORDER BY fecha_cambio ASC, id_historial ASC
        """, (id_pedido,))

        historial = []

        for estado, comentario, fecha in cursor.fetchall():
            historial.append({
                'estado': estado,
                'comentario': comentario,
                'fecha_cambio': str(fecha) if fecha else None
            })

        pedido['historial'] = historial

        return jsonify(pedido), 200

    except Exception as e:
        return jsonify({
            'mensaje': 'Error al consultar el pedido.',
            'error': str(e)
        }), 500

    finally:
        cursor.close()
