from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from datetime import datetime
import locale
import os

locale.setlocale(locale.LC_ALL, '')

app = Flask(__name__)

if os.environ.get("DATABASE_URL"):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pizzas.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

    observaciones = db.Column(db.String(300))
    metodo_pago = db.Column(db.String(50))

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

    total_dia = sum(p.total for p in pedidos_activos)
    total_entregado = sum(p.total for p in pedidos_entregados)
    total_general = total_dia + total_entregado

    return render_template("index.html",
                           pedidos_activos=pedidos_activos,
                           pedidos_entregados=pedidos_entregados,
                           total_dia=formato_clp(total_dia),
                           total_entregado=formato_clp(total_entregado),
                           total_general=formato_clp(total_general),
                           fecha_hoy=fecha_hoy)

@app.route("/agregar", methods=["POST"])
def agregar():

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    nuevo_pedido = Pedido(
        cliente=request.form["cliente"],
        departamento=request.form["departamento"],
        telefono=request.form["telefono"],
        sabor=request.form["sabor"],
        cantidad=int(request.form["cantidad"]),
        precio=int(request.form["precio"]),
        total=int(request.form["cantidad"]) * int(request.form["precio"]),
        hora_entrega=request.form["hora"],
        estado="Pendiente",
        fecha=fecha_hoy,
        observaciones=request.form.get("observaciones"),
        metodo_pago=""
    )

    db.session.add(nuevo_pedido)
    db.session.commit()

    return redirect("/")

@app.route("/entregar/<int:id>")
def entregar(id):
    pedido = Pedido.query.get(id)

    metodo = request.args.get("metodo")
    pedido.metodo_pago = metodo
    pedido.estado = "Entregado"

    db.session.commit()
    return redirect("/")

@app.route("/eliminar/<int:id>")
def eliminar(id):
    pedido = Pedido.query.get(id)
    db.session.delete(pedido)
    db.session.commit()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
