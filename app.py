from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import io

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL no está configurada en Render")

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ============================
# MODELO ORIGINAL (NO TOCADO)
# ============================

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
    estado = db.Column(db.String(50), default="Pendiente")
    observaciones = db.Column(db.String(200))
    metodo_pago = db.Column(db.String(50))
    fecha = db.Column(db.Date, default=datetime.today)

# ============================
# NUEVOS MODELOS DINÁMICOS
# ============================

class CampoConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    opciones = db.relationship("OpcionCampo", backref="campo", cascade="all, delete")

class OpcionCampo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    campo_id = db.Column(db.Integer, db.ForeignKey("campo_config.id"))

with app.app_context():
    db.create_all()

# ============================
# INDEX (MODIFICADO SOLO PARA MOSTRAR CAMPOS)
# ============================

@app.route("/")
def index():
    hoy = datetime.today().date()

    campos = CampoConfig.query.filter_by(activo=True).all()

    pedidos_activos = Pedido.query.filter(
        Pedido.estado != "Entregado",
        Pedido.fecha == hoy
    ).all()

    pedidos_entregados = Pedido.query.filter(
        Pedido.estado == "Entregado",
        Pedido.fecha == hoy
    ).all()

    total_dia = sum(p.total for p in pedidos_activos)
    total_entregado = sum(p.total for p in pedidos_entregados)
    total_general = total_dia + total_entregado

    return render_template(
        "index.html",
        pedidos_activos=pedidos_activos,
        pedidos_entregados=pedidos_entregados,
        total_dia=total_dia,
        total_entregado=total_entregado,
        total_general=total_general,
        fecha_hoy=hoy,
        campos=campos
    )

# ============================
# AGREGAR PEDIDO (MODIFICADO SOLO PARA LEER CAMPOS DINÁMICOS)
# ============================

@app.route("/agregar", methods=["POST"])
def agregar():
    cliente = request.form["cliente"]
    departamento = request.form["departamento"]
    telefono = request.form["telefono"]
    cantidad = int(request.form["cantidad"])
    precio = int(request.form["precio"])
    hora = request.form["hora"]
    observaciones = request.form.get("observaciones")

    # 🔥 Capturar campos dinámicos
    campos = CampoConfig.query.filter_by(activo=True).all()
    seleccion = []

    for campo in campos:
        valor = request.form.get(f"campo_{campo.id}")
        if valor:
            seleccion.append(valor)

    sabor_final = " - ".join(seleccion)

    total = cantidad * precio

    nuevo = Pedido(
        cliente=cliente,
        departamento=departamento,
        telefono=telefono,
        sabor=sabor_final,
        cantidad=cantidad,
        precio=precio,
        total=total,
        hora_entrega=hora,
        observaciones=observaciones
    )

    db.session.add(nuevo)
    db.session.commit()

    return redirect("/")

# ============================
# PANEL ADMIN CAMPOS
# ============================

@app.route("/admin_campos")
def admin_campos():
    campos = CampoConfig.query.all()
    return render_template("admin_campos.html", campos=campos)

@app.route("/crear_campo", methods=["POST"])
def crear_campo():
    nombre = request.form["nombre"]
    nuevo = CampoConfig(nombre=nombre)
    db.session.add(nuevo)
    db.session.commit()
    return redirect("/admin_campos")

@app.route("/crear_opcion/<int:campo_id>", methods=["POST"])
def crear_opcion(campo_id):
    nombre = request.form["nombre"]
    nueva = OpcionCampo(nombre=nombre, campo_id=campo_id)
    db.session.add(nueva)
    db.session.commit()
    return redirect("/admin_campos")

# ============================
# TODO LO DEMÁS NO SE TOCA
# ============================

# (Aquí pegas exactamente todas tus rutas originales:
# cambiar_estado, entregar, eliminar, historial, exportar_excel)
