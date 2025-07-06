from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from datetime import datetime

app = Flask(__name__)

conn = mysql.connector.connect(
    host="database-1.cbmc846qcmg5.sa-east-1.rds.amazonaws.com",
    user="admin",
    password="Vamosperu10_",
    database="restaurante_marisol"
)
cursor = conn.cursor(dictionary=True)

@app.route('/')
def index():
    cursor.execute("SELECT * FROM mesas")
    mesas = cursor.fetchall()
    return render_template("mesas.html", mesas=mesas)

@app.route('/reservar/<int:id_mesa>', methods=["GET", "POST"])
def reservar(id_mesa):
    if request.method == "POST":
        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        dni = request.form['dni']
        telefono = request.form['telefono']
        fecha = request.form['fecha']
        hora = request.form['hora']

        cursor.execute("INSERT INTO clientes (nombres, apellidos, dni, telefono) VALUES (%s, %s, %s, %s)", 
                       (nombres, apellidos, dni, telefono))
        conn.commit()
        id_cliente = cursor.lastrowid

        cursor.execute("INSERT INTO reservas (id_cliente, id_mesa, fecha_reserva, hora_reserva) VALUES (%s, %s, %s, %s)", 
                       (id_cliente, id_mesa, fecha, hora))
        cursor.execute("UPDATE mesas SET estado='reservada' WHERE id_mesa=%s", (id_mesa,))
        conn.commit()
        return redirect(url_for('index'))

    return render_template("reservar.html", id_mesa=id_mesa)

@app.route('/cancelar/<int:id_mesa>')
def cancelar(id_mesa):
    cursor.execute("UPDATE mesas SET estado='libre' WHERE id_mesa=%s", (id_mesa,))
    cursor.execute("UPDATE reservas SET estado='cancelada' WHERE id_mesa=%s AND estado='reservada'", (id_mesa,))
    conn.commit()
    return redirect(url_for('index'))

@app.route('/ocupar/<int:id_mesa>')
def ocupar(id_mesa):
    cursor.execute("UPDATE mesas SET estado='ocupada' WHERE id_mesa=%s", (id_mesa,))
    cursor.execute("UPDATE reservas SET estado='ocupada' WHERE id_mesa=%s AND estado='reservada'", (id_mesa,))
    conn.commit()
    return redirect(url_for('index'))

@app.route('/liberar/<int:id_mesa>')
def liberar(id_mesa):
    cursor.execute("UPDATE mesas SET estado='libre' WHERE id_mesa=%s", (id_mesa,))
    conn.commit()
    return redirect(url_for('index'))

@app.route('/historial')
def historial():
    cursor.execute("""
        SELECT r.id_reserva, c.nombres, c.apellidos, r.fecha_reserva, r.hora_reserva, r.estado
        FROM reservas r
        JOIN clientes c ON r.id_cliente = c.id_cliente
        ORDER BY r.id_reserva DESC
    """)
    reservas = cursor.fetchall()
    return render_template("historial.html", reservas=reservas)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
