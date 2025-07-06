from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

# 🔐 Conexión a MySQL RDS
db = mysql.connector.connect(
    host="database-1.cbmc846qcmg5.sa-east-1.rds.amazonaws.com",
    user="admin",
    password="Vamosperu10_",
    database="restaurante_marisol"
)

# 🔄 Reconexión automática
def get_cursor():
    global db
    if not db.is_connected():
        db.reconnect()
    return db.cursor(dictionary=True)

# 🔄 Actualizar estado de mesas según hora
def actualizar_estados():
    now = datetime.now()
    cursor = get_cursor()
    cursor.execute("""
        SELECT r.id_reserva, r.id_mesa, r.fecha_reserva, r.hora_reserva
        FROM reservas r
        WHERE r.estado = 'activa'
    """)
    reservas = cursor.fetchall()
    for reserva in reservas:
        hora_raw = reserva['hora_reserva']
        hora = (datetime.min + hora_raw).time() if isinstance(hora_raw, timedelta) else hora_raw
        fecha_hora = datetime.combine(reserva['fecha_reserva'], hora)
        minutos_faltantes = (fecha_hora - now).total_seconds() / 60

        if minutos_faltantes <= 30:
            get_cursor().execute(
                "UPDATE mesas SET estado = 'reservada' WHERE id_mesa = %s AND estado != 'ocupada'",
                (reserva['id_mesa'],)
            )
        else:
            get_cursor().execute(
                "UPDATE mesas SET estado = 'libre' WHERE id_mesa = %s AND estado != 'ocupada'",
                (reserva['id_mesa'],)
            )
    db.commit()
    cursor.close()

# 🏠 Página principal
@app.route('/')
def index():
    actualizar_estados()
    cursor = get_cursor()
    cursor.execute("SELECT * FROM mesas ORDER BY numero")
    mesas = cursor.fetchall()
    cursor.close()
    return render_template('mesas.html', mesas=mesas)

# 📋 Formulario de reserva
@app.route('/reservar/<int:id_mesa>', methods=['GET', 'POST'])
def reservar(id_mesa):
    if request.method == 'POST':
        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        dni = request.form['dni']
        telefono = request.form['telefono']
        fecha = request.form['fecha']
        hora = request.form['hora']

        cursor = get_cursor()
        cursor.execute("INSERT INTO clientes (nombres, apellidos, dni, telefono) VALUES (%s, %s, %s, %s)",
                       (nombres, apellidos, dni, telefono))
        id_cliente = cursor.lastrowid
        cursor.execute("INSERT INTO reservas (id_mesa, id_cliente, fecha_reserva, hora_reserva) VALUES (%s, %s, %s, %s)",
                       (id_mesa, id_cliente, fecha, hora))
        db.commit()
        cursor.close()
        return redirect(url_for('index'))

    return render_template('reservar.html', id_mesa=id_mesa)

# ❌ Cancelar reserva
@app.route('/cancelar/<int:id_mesa>')
def cancelar(id_mesa):
    cursor = get_cursor()
    cursor.execute("UPDATE reservas SET estado = 'cancelada' WHERE id_mesa = %s AND estado = 'activa'", (id_mesa,))
    cursor.execute("UPDATE mesas SET estado = 'libre' WHERE id_mesa = %s", (id_mesa,))
    db.commit()
    cursor.close()
    return redirect(url_for('index'))

# ✅ Ocupar mesa
@app.route('/ocupar/<int:id_mesa>')
def ocupar(id_mesa):
    cursor = get_cursor()
    cursor.execute("UPDATE reservas SET estado = 'ocupada' WHERE id_mesa = %s AND estado = 'activa'", (id_mesa,))
    cursor.execute("UPDATE mesas SET estado = 'ocupada' WHERE id_mesa = %s", (id_mesa,))
    db.commit()
    cursor.close()
    return redirect(url_for('index'))

# ✅ Liberar mesa ocupada
@app.route('/liberar/<int:id_mesa>')
def liberar(id_mesa):
    cursor = get_cursor()
    cursor.execute("UPDATE mesas SET estado = 'libre' WHERE id_mesa = %s", (id_mesa,))
    db.commit()
    cursor.close()
    return redirect(url_for('index'))

# 📋 Historial de reservas (corregido)
@app.route('/historial')
def historial():
    cursor = get_cursor()
    cursor.execute("""
        SELECT r.id_reserva, r.fecha_reserva, r.hora_reserva, r.estado,
               m.numero AS numero_mesa,
               c.nombres, c.apellidos
        FROM reservas r
        JOIN mesas m ON r.id_mesa = m.id_mesa
        JOIN clientes c ON r.id_cliente = c.id_cliente
        ORDER BY r.fecha_reserva DESC, r.hora_reserva DESC
    """)
    reservas = cursor.fetchall()
    cursor.close()

    # ✅ Convertir hora_reserva si es timedelta
    for r in reservas:
        if isinstance(r['hora_reserva'], timedelta):
            r['hora_reserva'] = (datetime.min + r['hora_reserva']).time()

    return render_template('historial.html', reservas=reservas)

# 🔥 Ejecutar la app
if __name__ == '__main__':
    app.run(debug=True)
