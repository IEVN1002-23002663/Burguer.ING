from flask import Flask, jsonify
from flask_cors import CORS

from blueprints.usuarios import usuarios_bp
from blueprints.proveedores import proveedores_bp
from blueprints.categorias_insumos import categorias_insumos_bp
from blueprints.materias_primas import materias_primas_bp
from blueprints.compras import compras_bp
from blueprints.inventario import inventario_bp
from blueprints.productos import productos_bp
from blueprints.produccion import produccion_bp
from blueprints.pedidos import pedidos_bp
from blueprints.ventas import ventas_bp
from blueprints.entregas import entregas_bp
from blueprints.finanzas import finanzas_bp
from config import config
from database import mysql


def create_app():

    app = Flask(__name__)

    

    app.config.from_object(config['development'])

    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:4200",
                "http://127.0.0.1:4200"
            ]
        }
    })

    mysql.init_app(app)

    app.register_blueprint(usuarios_bp)
    app.register_blueprint(proveedores_bp)
    app.register_blueprint(categorias_insumos_bp)
    app.register_blueprint(materias_primas_bp)
    app.register_blueprint(compras_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(produccion_bp)
    
    app.register_blueprint(pedidos_bp)

    app.register_blueprint(ventas_bp)
    app.register_blueprint(entregas_bp)
    app.register_blueprint(finanzas_bp)
    
    

    

    @app.route('/', methods=['GET'])
    def inicio():

        return jsonify({
            'mensaje': 'Bienvenido a Burguer.ING',
            'estado': 'API funcionando correctamente'
        }), 200

    

    @app.route('/api/db-test', methods=['GET'])
    def probar_conexion():

        cursor = None

        try:

            cursor = mysql.connection.cursor()

            
            cursor.execute('SELECT DATABASE()')

            resultado = cursor.fetchone()

           
            cursor.close()
            cursor = None

            return jsonify({
                'estado': 'Correcto',
                'mensaje': 'Conexión exitosa con MySQL',
                'base_datos': resultado[0]
            }), 200

        except Exception as error:

            return jsonify({
                'estado': 'Error',
                'mensaje': str(error)
            }), 500

        finally:

            if cursor is not None:
                cursor.close()

    return app




app = create_app()


if __name__ == '__main__':

    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
