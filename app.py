from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Base de datos (funciona en local y en Render)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL") or \
    'sqlite:///' + os.path.join(basedir, 'pizzas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# MODELO
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(100), nullable=False)
    pizza = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), default="En preparación")
    observaciones = db.Column(db.String(300))
    metodo_pago = db.Column(db.String(50))


with app.app_context():
    db.create_all()


# HOME
@app.route("/")
def index():
    pedidos = Pedido.query.filter(Pedido.estado != "Entregado").all()
    entregados = Pedido.query.filter_by(estado="Entregado").all()
    return render_template("index.html", pedidos=pedidos, entregados=entregados)


# AGREGAR PEDIDO
@app.route("/agregar", methods=["POST"])
def agregar():
    cliente = request.form["cliente"]
    pizza = request.form["pizza"]
    cantidad = int(request.form["cantidad"])
    precio = float(request.form["precio"])
    observaciones = request.form["observaciones"]

    total = cantidad * precio

    nuevo_pedido = Pedido(
        cliente=cliente,
        pizza=pizza,
        cantidad=cantidad,
        precio=precio,
        total=total,
        observaciones=observaciones
    )

    db.session.add(nuevo_pedido)
    db.session.commit()

    return redirect("/")


# ELIMINAR PEDIDO
@app.route("/eliminar/<int:id>")
def eliminar(id):
    pedido = Pedido.query.get_or_404(id)
    db.session.delete(pedido)
    db.session.commit()
    return redirect("/")


# ENTREGAR PEDIDO
@app.route("/entregar/<int:id>", methods=["GET", "POST"])
def entregar(id):
    pedido = Pedido.query.get_or_404(id)

    if request.method == "POST":
        metodo_pago = request.form["metodo_pago"]
        pedido.metodo_pago = metodo_pago
        pedido.estado = "Entregado"
        db.session.commit()
        return redirect("/")

    return render_template("entregar.html", pedido=pedido)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
