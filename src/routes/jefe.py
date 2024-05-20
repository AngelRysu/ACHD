from flask import Blueprint, render_template, redirect, request, jsonify
from functions import verificate_session
from models.tables_db import Usuarios, Materias, Aulas, Asignaciones, Ciclos
from extensions import db
import json
from functions import  docente

jefe_bp = Blueprint('jefe', __name__)

@jefe_bp.route("/jefeCarrera")
def jefe_carrera():
    user = verificate_session()
    if user:
        username = user["username"]
        carrera = user["carrera"]
        d = Usuarios.query.filter_by(user_type=docente, carrera=carrera).all()
        a = Materias.query.filter_by(carrera=carrera).all()
        return render_template("jefeCarrera.html", user=username, asignaturas=a, docentes=d)
    return redirect("/")

@jefe_bp.route("/jefeCarrera/docentes")
def docentes():
    user = verificate_session()
    if user:
        try:
            userid = request.args["userid"]
        except KeyError:
            userid = None
        username = user["username"]
        carrera = user["carrera"]
        d = Usuarios.query.filter_by(user_type=docente, carrera=carrera).order_by(Usuarios.apellido_pat).all()
        return render_template("docentes.html", user=username, docentes=d, userid=userid)
    return redirect("/")

@jefe_bp.route("/jefeCarrera/materias")
def materias():
    user = verificate_session()
    if user:
        username = user["username"]
        carrera = user["carrera"]
        d = Materias.query.filter_by(carrera=carrera).order_by(Materias.semestre).all()
        return render_template("materias.html", user=username, materias=d)
    return redirect("/")

@jefe_bp.route("/jefeCarrera/asignacion")
def asignacion():
    user = verificate_session()
    if user:
        username = user["username"]
        carrera = user["carrera"]
        d = Usuarios.query.filter_by(user_type=docente, carrera=carrera).all()
        a = Materias.query.filter_by(carrera=carrera).all()
        aula = Aulas.query.all()
        return render_template("asignacion.html", user=username, asignaturas=a, docentes=d, aulas=aula)
    return redirect("/")


@jefe_bp.route("/setAsignacion", methods=["POST"])
def set_asignacion():
    user = verificate_session()
    if user:
        user_carrera = user["carrera"]
        asignacion_propuesta = request.json
        semestre = asignacion_propuesta.pop("semestre")
        turno = asignacion_propuesta.pop("turno")
        ciclo = Ciclos.query.filter_by(actual=True).first()
        asignacion = Asignaciones.query.filter_by(carrera=user_carrera, semestre=semestre, turno=turno, ciclo=ciclo.id).first()

        if not asignacion:
            asignacion = Asignaciones(
                carrera=user_carrera,
                semestre=semestre,
                turno=turno,
                ciclo=ciclo.id,
                horario=json.dumps(asignacion_propuesta.get("asignacion", {}))
            )
            horariov = None
            db.session.add(asignacion)
        else:
            horariov = json.loads(asignacion.horario)
            asignacion.horario = json.dumps(asignacion_propuesta.get("asignacion", {}))

        db.session.commit()
        horarion = json.loads(asignacion.horario)
        docentes = horarion.get("docente", [])
        cell_ids = horarion.get("cell_ids", [])

        docentes_actualizados = 0

        if horariov:
            actualizar = detectar_cambios(horarion, horariov)
            docentesold = actualizar.get("docente", [])
            cell_idsold = actualizar.get("cell_ids", [])

            for i, doc_id in enumerate(docentesold):
                if doc_id != '':
                    cell_id = int(cell_idsold[i])
                    if update_disp(doc_id, [cell_id], 1):
                        docentes_actualizados += 1

        for i, doc_id in enumerate(docentes):
            if doc_id != '':
                cell_id = int(cell_ids[i])
                if update_disp(doc_id, [cell_id], 3):
                    docentes_actualizados += 1

        if docentes_actualizados > 0:
            return jsonify({"success": True, "message": f"Disponibilidad actualizada para {docentes_actualizados} docente(s)"})
        else:
            return jsonify({"success": False, "message": "No se encontraron docentes con disponibilidad para actualizar"})

    return redirect("/")

def detectar_cambios(jsnew, jsold):
    cambios = {"docente": [], "cell_ids": []}
    for old_docente, new_docente, cell_id in zip(jsold["docente"], jsnew["docente"], jsnew["cell_ids"]):
        if old_docente != new_docente and old_docente != "":
            cambios["docente"].append(old_docente)
            cambios["cell_ids"].append(cell_id)
    return cambios

def update_disp(user_id, indices_to_update, value):
    usuario = Usuarios.query.filter_by(id=user_id).first()
    if usuario:
        current_availability = json.loads(usuario.disponibilidad)["disponibilidad"]
        for idx in indices_to_update:
            current_availability[idx] = value

        result_dict = {"disponibilidad": current_availability}
        result_json = json.dumps(result_dict)

        usuario.disponibilidad = result_json
        db.session.commit()
        return True
    return False

@jefe_bp.route("/jefeCarrera/grupos")
def grupos():
    user = verificate_session()
    if user:
        username = user["username"]
        carrera = user["carrera"]
        d = Usuarios.query.filter_by(user_type=docente, carrera=carrera).all()
        a = Materias.query.filter_by(carrera=carrera).all()
        aula = Aulas.query.all()
        return render_template("grupos.html", user=username, asignaturas=a, docentes=d, aulas=aula)
    return redirect("/")