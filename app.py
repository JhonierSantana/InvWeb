from flask import Flask, render_template, request, redirect
from datetime import datetime
from flask_mysqldb import MySQL

#

app = Flask(__name__)
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "almacen_bd"

mysql = MySQL(app)


@app.route("/", methods=["GET", "POST"])
def guardar_producto():
    if request.method == "POST":
        cve_producto = request.form["Cve_Producto"]
        grupo = request.form["Grupo"]
        nombre = request.form["NombreP"]
        precio = request.form["Precio"]
        cantidad_stock = request.form["Cantidad_Stok"]
        fecha_entrada = request.form["FechaEntrada"]

        # Guardar los datos en la tabla productos
        cursor = mysql.connection.cursor()
        # Verificar si el producto ya existe en la tabla productos
        cursor.execute(
            "SELECT Cve_Producto FROM productos WHERE Cve_Producto = %s",
            (cve_producto,),
        )
        existing_product = cursor.fetchone()

        if existing_product:
            # El producto ya existe, actualizar la cantidad de stock y la fecha de entrada
            cursor.execute(
                "UPDATE productos SET Cantidad_Stok = Cantidad_Stok + %s, FechaEntrada = %s WHERE Cve_Producto = %s",
                (cantidad_stock, fecha_entrada, cve_producto),
            )
        else:
            # El producto no existe, insertarlo en la tabla productos
            cursor.execute(
                "INSERT INTO productos (Cve_Producto, Grupo, NombreP, Precio, Cantidad_Stok, FechaEntrada) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    cve_producto,
                    grupo,
                    nombre,
                    precio,
                    cantidad_stock,
                    fecha_entrada,
                ),
            )

        mysql.connection.commit()
        cursor.close()

    return render_template("index.html")


@app.route("/grupo/<grupo>", methods=["GET"])
def mostrar_productos_grupo(grupo):
    busqueda = request.args.get("busqueda", default="", type=str)

    cursor = mysql.connection.cursor()
    if busqueda:
        cursor.execute(
            "SELECT * FROM productos WHERE Grupo = %s AND NombreP LIKE %s",
            (grupo, f"%{busqueda}%"),
        )
        productos = cursor.fetchall()
    else:
        cursor.execute("SELECT * FROM productos WHERE Grupo = %s", (grupo,))
        productos = cursor.fetchall()

    cursor.close()

    return render_template("grupos.html", grupo=grupo, productos=productos)


@app.route("/ventas/<grupo>", methods=["POST"])
def ventas(grupo):
    nombre_producto = request.form["Nombre_Producto"]
    cantidad_venta = int(request.form["Cantidad_Venta"])
    fecha_venta_str = request.form["Fecha_Venta"]

    # Convertir la cadena de fecha en un objeto datetime si no está vacía
    fecha_venta = (
        datetime.strptime(fecha_venta_str, "%Y-%m-%d").date()
        if fecha_venta_str
        else None
    )

    cursor = mysql.connection.cursor()

    # Verificar si el producto existe y tiene suficiente cantidad en stock
    cursor.execute(
        "SELECT Cve_Producto, Precio, Cantidad_Stok FROM productos WHERE Grupo = %s AND NombreP = %s",
        (grupo, nombre_producto),
    )
    stock = cursor.fetchone()

    if stock:
        if stock[2] >= cantidad_venta:  # Verificar la cantidad en stock
            cve_producto = stock[0]

            # Realizar la venta y restar la cantidad del stock
            cursor.execute(
                "UPDATE productos SET Cantidad_Stok = Cantidad_Stok - %s WHERE Cve_Producto = %s",
                (cantidad_venta, cve_producto),
            )

            # Guardar la venta en el historial de ventas
            cursor.execute(
                "INSERT INTO ventas (CveProducto, Grupo, NombreP, Precio, FechaVta, CantidadVta) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    cve_producto,
                    grupo,
                    nombre_producto,
                    stock[1],  # Precio
                    fecha_venta,
                    cantidad_venta,
                ),
            )

            mysql.connection.commit()
            cursor.close()

            return redirect(f"/grupo/{grupo}")
        else:
            cursor.close()
            return "No hay suficiente cantidad en stock"
    else:
        cursor.close()
        return "El producto no existe"


@app.route("/historial_ventas", methods=["GET"])
def historial_ventas():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM ventas")
    historial = cursor.fetchall()
    cursor.close()

    return render_template("historial_ventas.html", historial=historial)


if __name__ == "__main__":
    app.run(debug=True)
