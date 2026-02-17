from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from datetime import datetime
import locale
import os

# Configurar moneda chilena
locale.setlocale(locale.LC_ALL, '')

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pizzas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
    sabor = db.Column(db.String(100))
    cantidad = db.Column(db.Integer)
    precio = db.Column(db.Integer)
    total = db.Column(db.Integer)
    hora_entrega = db.Column(db.String(10))
    estado = db.Column(db.String(50))
    fecha = db.Column(db.String(20))

with app.app_context():
    db.create_all()

def formato_clp(valor):
    return "${:,.0f}".format(valor).replace(",", ".")

@app.route("/")
def index():

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    pedidos_activos = Pedido.query.filter(
        Pedido.estado != "Entregado",
        Pedido.fecha == fecha_hoy
    ).order_by(Pedido.hora_entrega.asc()).all()

    pedidos_entregados = Pedido.query.filter(
        Pedido.estado == "Entregado",
        Pedido.fecha == fecha_hoy
    ).order_by(Pedido.hora_entrega.asc()).all()

    total_pizzas = sum(p.cantidad for p in pedidos_activos)
    total_dia = sum(p.total for p in pedidos_activos)

    total_entregado = sum(p.total for p in pedidos_entregados)

    total_general = total_dia + total_entregado

    return render_template("index.html",
                           pedidos_activos=pedidos_activos,
                           pedidos_entregados=pedidos_entregados,
                           total_pizzas=total_pizzas,
                           total_dia=formato_clp(total_dia),
                           total_entregado=formato_clp(total_entregado),
                           total_general=formato_clp(total_general),
                           fecha_hoy=fecha_hoy)

@app.route("/agregar", methods=["POST"])
def agregar():

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    cliente = request.form["cliente"]
    departamento = request.form["departamento"]
    telefono = request.form["telefono"]
    sabor = request.form["sabor"]
    cantidad = int(request.form["cantidad"])
    precio = int(request.form["precio"])
    hora = request.form["hora"]

    total = cantidad * precio

    nuevo_pedido = Pedido(
        cliente=cliente,
        departamento=departamento,
        telefono=telefono,
        sabor=sabor,
        cantidad=cantidad,
        precio=precio,
        total=total,
        hora_entrega=hora,
        estado="Pendiente",
        fecha=fecha_hoy
    )

    db.session.add(nuevo_pedido)
    db.session.commit()

    return redirect("/")

@app.route("/cambiar_estado/<int:id>/<estado>")
def cambiar_estado(id, estado):
    pedido = Pedido.query.get(id)
    pedido.estado = estado
    db.session.commit()
    return redirect("/")

@app.route("/eliminar/<int:id>")
def eliminar(id):
    pedido = Pedido.query.get(id)
    db.session.delete(pedido)
    db.session.commit()
    return redirect("/")

@app.route("/historial", methods=["GET"])
def historial():

    fecha = request.args.get("fecha")

    pedidos = []
    total = 0

    if fecha:
        pedidos = Pedido.query.filter_by(fecha=fecha).all()
        total = sum(p.total for p in pedidos)

    return render_template("historial.html",
                           pedidos=pedidos,
                           total=formato_clp(total),
                           fecha=fecha)

@app.route("/exportar")
def exportar():

    pedidos = Pedido.query.all()

    data = []

    for p in pedidos:
        data.append({
            "Fecha": p.fecha,
            "Cliente": p.cliente,
            "Departamento": p.departamento,
            "Teléfono": p.telefono,
            "Sabor": p.sabor,
            "Cantidad": p.cantidad,
            "Precio": p.precio,
            "Total": p.total,
            "Hora Entrega": p.hora_entrega,
            "Estado": p.estado
        })

    df = pd.DataFrame(data)
    archivo = "ventas_pizzas.xlsx"
    df.to_excel(archivo, index=False)

    return send_file(archivo, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
