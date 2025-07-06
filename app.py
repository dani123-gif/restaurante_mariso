from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'secreto123'

# Conexión a la base de datos
config = {
    'host': 'database-1.cbmc846qcmg5.sa-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Vamosperu10_',
    'database': 'restaurante_marisol'
}

db = mysql.connector.connect(**config)

@app.route('/')
def index():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mesas")
    mesas = cursor.fetchall()
    return render_template('mesas.html', mesas=mesas)

@app.route('/reservar', methods=['POST'])
def reservar():
    id_mesa = request.form['id_mesa']
    nombres = request.form['nombres']
    apellidos = request.form['apellidos']
    dni = request.form['dni']
    telefono = request.form['telefono']
    fecha = request.form['fecha']
    hora = request.form['hora']

    cursor = db.cursor()

    # Verificar conflicto de horario (1 hora antes o después)
    cursor.execute("""
        SELECT * FROM reservas 
        WHERE id_mesa = %s AND fecha_reserva = %s
        AND ABS(TIMESTAMPDIFF(MINUTE, hora_reserva, %s)) < 60
    """, (id_mesa, fecha, hora))

    conflicto = cursor.fetchone()
    if conflicto:
        flash(f"❌ La mesa {id_mesa} ya está reservada para una hora cercana. Espere mínimo 1 hora entre reservas.")
        return redirect(url_for('index'))

    cursor.execute("INSERT INTO clientes (nombres, apellidos, dni, telefono) VALUES (%s, %s, %s, %s)",
                   (nombres, apellidos, dni, telefono))
    id_cliente = cursor.lastrowid

    cursor.execute("""
        INSERT INTO reservas (id_mesa, id_cliente, fecha_reserva, hora_reserva, estado)
        VALUES (%s, %s, %s, %s, 'reservada')
    """, (id_mesa, id_cliente, fecha, hora))

    cursor.execute("UPDATE mesas SET estado = 'reservada' WHERE id_mesa = %s", (id_mesa,))
    db.commit()

    flash("✅ Reserva registrada exitosamente.")
    return redirect(url_for('index'))

@app.route('/reservas_mesa/<int:id_mesa>')
def reservas_mesa(id_mesa):
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.fecha_reserva as fecha, r.hora_reserva as hora, c.nombres as nombre
        FROM reservas r
        JOIN clientes c ON r.id_cliente = c.id_cliente
        WHERE r.id_mesa = %s
        ORDER BY r.fecha_reserva, r.hora_reserva
    """, (id_mesa,))
    reservas = cursor.fetchall()
    return jsonify(reservas)

@app.route('/historial')
def historial():
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.*, c.nombres, c.apellidos, c.dni, c.telefono
        FROM reservas r
        JOIN clientes c ON r.id_cliente = c.id_cliente
        ORDER BY r.fecha_reserva DESC, r.hora_reserva DESC
    """)
    reservas = cursor.fetchall()

    for r in reservas:
        if isinstance(r['hora_reserva'], timedelta):
            r['hora_reserva'] = (datetime.min + r['hora_reserva']).time()

    return render_template('historial.html', reservas=reservas)

# Render compatible
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
