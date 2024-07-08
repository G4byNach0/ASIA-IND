from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from werkzeug.utils import secure_filename
import os
import time

try:
    cnx = mysql.connector.connect(
        database="g4bynach0$miapp",
        user="g4bynach0",
        password="grupo13cac",
        host="g4bynach0.mysql.pythonanywhere-services.com"
    )
    print("Conexión exitosa!")
    cnx.close()
except mysql.connector.Error as err:
    print(f"Error: {err}")
    if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
        print("Algo está mal con tu nombre de usuario o contraseña")
    elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
        print("La base de datos no existe")
    else:
        print(err)

app = Flask(__name__)
CORS(app)

dbconfig = {
    "database": "g4bynach0$miapp",
    "user": "g4bynach0",
    "password": "grupo13cac",
    "host": "g4bynach0.mysql.pythonanywhere-services.com"
}

class Catalogo:
    def __init__(self, host, user, password, database, cnx):
        self.cnx = cnx
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
        )
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute(f"USE {database}")
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.cursor.execute(f"CREATE DATABASE {database}")
                self.conn.database = database
            else:
                raise err

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            codigo INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(40) NOT NULL,
            descripcion VARCHAR(255) NOT NULL,
            cantidad INT NOT NULL,
            precio DECIMAL(10, 2) NOT NULL,
            imagen_url VARCHAR(255))''')
        self.conn.commit()

        self.cursor.close()
        self.cursor = self.conn.cursor(dictionary=True)

    def agregar_producto(self, titulo, descripcion, cantidad, precio, imagen):
        sql = "INSERT INTO productos (titulo, descripcion, cantidad, precio, imagen_url) VALUES (%s, %s, %s, %s, %s)"
        valores = (titulo, descripcion, cantidad, precio, imagen)
        self.cursor.execute(sql, valores)
        self.conn.commit()
        return self.cursor.lastrowid

    def consultar_producto(self, codigo):
        self.cursor.execute(f"SELECT * FROM productos WHERE codigo = {codigo}")
        return self.cursor.fetchone()

    def modificar_producto(self, codigo, nuevo_titulo, nueva_descripcion, nueva_cantidad, nuevo_precio, nueva_imagen):
        sql = "UPDATE productos SET titulo = %s, descripcion = %s, cantidad = %s, precio = %s, imagen_url = %s WHERE codigo = %s"
        valores = (nuevo_titulo, nueva_descripcion, nueva_cantidad, nuevo_precio, nueva_imagen, codigo)
        try:
            self.cursor.execute(sql, valores)
            self.conn.commit()
            return self.cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            print(f"SQL: {sql}")
            print(f"Valores: {valores}")
            return False

    def listar_productos(self):
        try:
            self.cursor.execute("SELECT * FROM productos")
            productos = self.cursor.fetchall()
            return productos
        except Error as err:
            app.logger.error(f'Error executing query: {err}')
            return {"error": "Internal Server Error"}

    def eliminar_producto(self, codigo):
        self.cursor.execute(f"DELETE FROM productos WHERE codigo = {codigo}")
        self.conn.commit()
        return self.cursor.rowcount > 0

    def mostrar_producto(self, codigo):
        producto = self.consultar_producto(codigo)
        if producto:
            print("-" * 40)
            print(f"Código.....: {producto['codigo']}")
            print(f"titulo.....: {producto['titulo']}")
            print(f"Descripción: {producto['descripcion']}")
            print(f"Cantidad...: {producto['cantidad']}")
            print(f"Precio.....: {producto['precio']}")
            print(f"Imagen.....: {producto['imagen_url']}")
            print("-" * 40)
        else:
            print("Producto no encontrado.")

catalogo = Catalogo(
    host='g4bynach0.mysql.pythonanywhere-services.com',
    user='g4bynach0',
    password='grupo13cac',
    database='g4bynach0$miapp',
    cnx='cnx'
)

RUTA_DESTINO = '/home/g4bynach0/mysite/src/imgs'

@app.route('/src/imgs/<path:filename>')
def send_image(filename):
    return send_from_directory('src/imgs', filename)


@app.route("/productos/<int:codigo>", methods=["GET"])
def mostrar_producto(codigo):
    producto = catalogo.consultar_producto(codigo)
    if producto:
        return jsonify(producto), 201
    else:
        return "Producto no encontrado", 404

@app.route("/productos", methods=["POST"])

def agregar_producto():
    if not request.form:
        return jsonify({"error": "Request body must be Form DATA"}), 400

    titulo = request.form['titulo']
    descripcion = request.form['descripcion']
    cantidad = request.form['cantidad']
    precio = request.form['precio']

    if 'imagen' in request.files:
        imagen = request.files['imagen']
        nombre_imagen = secure_filename(imagen)
        nombre_base, extension = os.path.splitext(nombre_imagen)
        nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}"
        imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))
    else:
        return jsonify({"error": "Missing image file"}), 400

    nuevo_codigo = catalogo.agregar_producto(titulo, descripcion, cantidad, precio, nombre_imagen)
    if nuevo_codigo:
        imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))
        return jsonify({"mensaje": "Producto agregado correctamente.", "codigo": nuevo_codigo, "titulo": titulo, "descripcion": descripcion, "precio": precio, "imagen": nombre_imagen}), 201
    else:
        return jsonify({"mensaje": "Error al agregar el producto."}), 500

    

@app.route("/productos/<int:codigo>", methods=["PUT"])
def modificar_producto(codigo):
    if request.method == 'OPTIONS':
        response = app.make_response('')
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Requested-With")
        return response
    elif request.method == 'PUT':
        try:
            nuevo_titulo = request.form.get("titulo")
            nueva_descripcion = request.form.get("descripcion")
            nueva_cantidad = request.form.get("cantidad")
            nuevo_precio = request.form.get("precio")

            if 'imagen' in request.files:
                imagen = request.files['imagen']
                nombre_imagen = secure_filename(imagen.filename)
                nombre_base, extension = os.path.splitext(nombre_imagen)
                nombre_imagen = f"{nombre_base}_{int(time.time())}{extension}"
                imagen.save(os.path.join(RUTA_DESTINO, nombre_imagen))
                producto = catalogo.consultar_producto(codigo)
                if producto:
                    imagen_vieja = producto["imagen_url"]
                    ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)
                    if os.path.exists(ruta_imagen):
                        os.remove(ruta_imagen)
            else:
                producto = catalogo.consultar_producto(codigo)
                if producto:
                    nombre_imagen = producto["imagen_url"]

            if catalogo.modificar_producto(codigo, nuevo_titulo, nueva_descripcion, nueva_cantidad, nuevo_precio, nombre_imagen):
                return jsonify({"mensaje": "Producto modificado"}), 200
            else:
                return jsonify({"mensaje": "Producto no encontrado"}), 403
        except Exception as e:
            print(f"Error en la vista: {str(e)}")
            return jsonify({'message': str(e)}), 500

@app.route("/productos/<int:codigo>", methods=["DELETE"])
def eliminar_producto(codigo):
    producto = catalogo.consultar_producto(codigo)
    if producto:
        imagen_vieja = producto["imagen_url"]
        ruta_imagen = os.path.join(RUTA_DESTINO, imagen_vieja)
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)
        if catalogo.eliminar_producto(codigo):
            return jsonify({"mensaje": "Producto eliminado"}), 200
        else:
            return jsonify({"mensaje": "Error al eliminar el producto"}), 500
    else:
        return jsonify({"mensaje": "Producto no encontrado"}), 404

@app.route("/productos", methods=["GET"])
def listar_productos():
    productos = catalogo.listar_productos()
    if isinstance(productos, list):
        return jsonify(productos), 200
    else:
        return jsonify(productos), 500

if __name__ == '__main__':
    app.run(debug=True)