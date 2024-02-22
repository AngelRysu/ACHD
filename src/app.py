# c-basic-offset: 4; tab-width: 8; indent-tabs-mode: nil
# vi: set shiftwidth=4 tabstop=8 expandtab:
# :indentSize=4:tabSize=8:noTabs=true:
#
# SPDX-License-Identifier: GPL-3.0-or-later

import hashlib
import json
from configparser import ConfigParser

from flask import Flask, render_template, send_from_directory
from flask import session, request, redirect
from flask_orator import Orator


app=Flask(__name__)

config = ConfigParser()
config.read(".env") # EN ESTE APARTADO TOMARA LOS VALORES DE ENTORNO OBTENIDOS EN .env
app.secret_key = config.get("SCT","SECRET_KY") 
#para guardar las cookies es necesario una secret_key que se encuentra en .env
DB_HOST = config.get("DB", "DB_HOST")
DB_PASSWORD = config.get("DB", "DB_PASSWORD")
DB_DB = config.get("DB", "DB_DB")
DB_USER = config.get("DB", "DB_USER")

DATABASES = {
    "default": "mysql",
    "mysql": {
        "driver": "mysql",
        "host": DB_HOST,
        "database": DB_DB,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "prefix": "",
        "log_queries": True,
    },
}
app.config["ORATOR_DATABASES"] = DATABASES
db = Orator(app)

def get_hex_digest(cadena):
    """
    Recibe un String.
    Regresa el hexadecimal de un Hash en SHA256.
    """
    sha256 = hashlib.sha256()
    sha256.update(cadena.encode("utf-8"))
    hexdigest = sha256.hexdigest()
    return hexdigest

def verificate_session():
    """verificate_session
    Returns:
        user: nombre del usuario en la cookie
        False: en caso de no tener encontrar la cookie
    """
    if 'username' in session:
        user = session["username"]
        return user
    return False

@app.route("/img/<filename>", methods=["GET"])
def route_img_files(filename):
    """
    Recibe la ruta de la imagen que pide.
    Regresa la imagen.
    """
    return send_from_directory("templates/img", path=filename)

@app.route("/css/<filename>")
def route_js_files(filename):
    """
    Recibe la ruta del CSS que se pide.
    Regresa el archivo CSS.
    """
    return send_from_directory("templates/css", path=filename)

@app.route("/js/<filename>")
def route_css_files(filename):
    """
    Recibe la ruta del JS que pide.
    Regresa el JS.
    """
    return send_from_directory("templates/js", path=filename)

@app.route("/")
def index():
    """
    Si hay una sesión iniciada, redirecciona al dashboard.
    Si no hay una sesión iniciada, regresa el login.
    """
    return render_template("index.html")

@app.route("/logout")
def logout():
    """
    Borra las cookies del sitio en el navegador del usuario.
    """
    session.pop('username', None)
    return redirect('/')

@app.route("/login", methods=["POST"])
def login():
    """
    Método para iniciar sesión.
    Recibe el usuario y la contraseña de un form.
    Si coincide, inserta una sesión en la tabla de sesiones y regresa la
    cookie con el SessionID.
    """
    form = request.form
    print(str(form))
    user = form["email"]
    pssw = get_hex_digest(form["password"])
    user = (
        db.table("usersPrueba")
        .where("email", user)
        .where("password", pssw)
        .get()
        .first()
    )
    if user is None:
        return render_template(
            "index.html", mensaje="Usuario y/o contraseña incorrectos"
        )
    while True:
        session['username'] = user['user'] #'user' hace referencia a la tabla de la base de datos
        return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    """
    Regresa la vista del dashboard.
    """
    user=verificate_session()
    if user:
        return render_template("dashboard.html", user=user)
    return redirect('/')

@app.route("/homeDocente")
def home_docente():
    """
    Regresa el panel de docente
    """
    user=verificate_session()
    if user:
        return render_template("homeDocente.html", user=user)    
    return redirect('/')

@app.route("/horario")
def horario():
    """
    Regresa el selector de horario
    """
    user=verificate_session()
    if user:
        usuario = db.table("usersPrueba").where("user",user).get().first()
        disponibilidad = usuario.disponibilidad
        return render_template("horario.html", user=user, disponibilidad=disponibilidad)
    return redirect('/')
    
@app.route("/setDisponibilidad", methods=['POST'])
def set_disp():
    """
    Guarda la disponibilidad de un docente
    """
    user=verificate_session()
    if user:
        propuesta = request.json
        selected_ids = propuesta['selectedIDs']
        selected_indices = [int(idx) for idx in selected_ids]
        availability_matrix = [0] * 90
        for idx in selected_indices:
            availability_matrix[idx] = 1
        result_dict = {"disponibilidad": availability_matrix}
        result_json = json.dumps(result_dict)
        resp = db.table('usersPrueba').where('user',user).update(disponibilidad=result_json)
        return str(resp)
    return redirect('/')



@app.route("/jefeCarrera")
def jefe_carrera():
    """
    Vista del jefe de carrera
    """
    user=verificate_session()
    if user:
        d = db.table('docentes').get()
        a = db.table('asignaturas').get()
        return render_template("jefeCarrera.html", user=user,asignaturas=a,docentes=d)
    return redirect('/')

@app.route("/asignacion")
def asignacion():
    """
    Vista de asignacion de materias
 
   """
    user=verificate_session()
    if user:
        return render_template("asignacion.html", user=user)
    return redirect('/')
    
if __name__=='__main__':
    app.run(debug=True, port=5000)
    