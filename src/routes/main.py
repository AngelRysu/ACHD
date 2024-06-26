from flask import Blueprint, render_template, redirect, request, session, jsonify
from functions import verificate_session, get_hex_digest, admin, docente,jefe_de_carrera
from models.tables_db import Usuarios, Ciclos, Asignaciones, Materias, Aulas,Disponibilidades
from models.tables_db import Disponibilidades
from extensions import db
import json

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    user = verificate_session()
    if user:
        usernivel = user["nivel"]
        if usernivel:
            if usernivel == admin:
                return redirect("/admin")
            if usernivel == docente:
                return redirect("/homeDocente")
            if usernivel == jefe_de_carrera:
                return redirect("/jefeCarrera")
    return render_template("index.html")

@main_bp.route("/dashboard")
def dashboard():
    user = verificate_session()
    if user:
        username = user["username"]
        return render_template("dashboard.html", user=username)
    return redirect("/")

@main_bp.route("/firstlogin")
def firstlogin():
    user = verificate_session()
    if user:
        username = user["username"]
        return render_template("firstlogin.html", user=username)
    return redirect("/")

@main_bp.route("/change", methods=["POST", "GET"])
def change():
    user = verificate_session()
    if not user:
        return redirect("/")

    user_id = user["userid"]
    mensaje = None
    
    if request.method == "POST":
        current_password = request.form["password"]
        new_password = request.form["newpass"]
        confirm_password = request.form["conf_newpass"]

        if not current_password or not new_password or not confirm_password:
            mensaje = "Favor de llenar todos los campos"
            return jsonify({"success": False, "message": mensaje})

        usactual = Usuarios.query.filter_by(id=user_id).first()
        current_password = get_hex_digest(current_password)
        new_password = get_hex_digest(new_password)
        confirm_password = get_hex_digest(confirm_password)

        if current_password != usactual.password:
            mensaje = "La contraseña actual no coincide"
            return jsonify({"success": False, "message": mensaje})

        if new_password != confirm_password:
            mensaje = "La nueva contraseña no coincide"
            return jsonify({"success": False, "message": mensaje})

        if current_password == new_password:
            mensaje = "La nueva contraseña es la misma que la actual"
            return jsonify({"success": False, "message": mensaje})

        mensaje = "La contraseña se cambió exitosamente. En 3 segundos serás redirigido"
        usactual.password = new_password
        db.session.commit()

    return jsonify({"success": True, "message": mensaje})

@main_bp.route("/change_first", methods=["POST", "GET"])
def change_first():
    user = verificate_session()
    if not user:
        return redirect("/")
    user_id = user["userid"]
    mensaje = None
    user_first = Usuarios.query.filter_by(id=user_id, first_login = True).first()
    
    if request.method == "POST":
        new_password = request.form["newpass"]
        confirm_password = request.form["conf_newpass"]    
        new_password = get_hex_digest(new_password)
        confirm_password = get_hex_digest(confirm_password)
        if new_password != confirm_password:
            mensaje = "La nueva contraseña no coincide"
            return jsonify({"success": False, "message": mensaje})
            
        mensaje = "La contraseña se cambió exitosamente. En 3 segundos serás redirigido"
        user_first.password = new_password
        user_first.first_login = False
        db.session.commit()   
    return jsonify({"success": True, "message": mensaje})
    


@main_bp.route("/getDisponibilidad/<int:idDocente>", methods=["GET"])
def get_dispo(idDocente):
    user = verificate_session()
    if user:
        ciclo = Ciclos.query.filter_by(actual=True).first()
        dispo = Disponibilidades.query.filter_by(usuario_id=idDocente, ciclo_id=ciclo.id).first()
        if dispo:
            disponibilidad = json.loads(dispo.horas)
            return jsonify({"success": True, "disponibilidad": disponibilidad})
        else:
            return jsonify({"success": False, "message": "Docente no encontrado"})
    else:
        return jsonify({"success": False, "message": "Usuario no autenticado"})


@main_bp.route("/get_horario", methods=['GET'])
def get_horario():
    user = verificate_session()
    if user:
        carrera = user["carrera"]
        turno = request.args.get('turno')
        ciclo = Ciclos.query.filter_by(actual=True).first()
        asignacion = Asignaciones.query.filter_by(carrera_id=carrera, grupo_id=turno, ciclo_id=ciclo.id).first()
        if asignacion:
            horarios = json.loads(asignacion.horario)
            return jsonify({"success": True, "horario": horarios})
        return jsonify({'error': 'Horario no encontrado'})
    return redirect("/")

@main_bp.route("/setDisponibilidad", methods=["POST"])
def set_disp():
    user = verificate_session()
    if user:
        user_id = user["userid"]
        propuesta = request.json
        selected_ids = propuesta["selectedIDs"]
        selected_indices = [int(idx) for idx in selected_ids]
        availability_matrix = [0] * 90
        for idx in selected_indices:
            availability_matrix[idx] = 1
            
        result_dict = {"disponibilidad": availability_matrix}
        result_json = json.dumps(result_dict)
        
        ciclo = Ciclos.query.filter_by(actual=True).first()

        d = Disponibilidades.query.filter_by(usuario_id=user_id, ciclo_id=ciclo.id).first()
        if not d:
            d = Disponibilidades(usuario_id=user_id, ciclo_id=ciclo.id, horas={'disponibilidad': [0]*90})
            db.session.add(d)
        d.horas = result_json
        db.session.commit()

        return jsonify({"status": "success", "message": "Disponibilidad guardada correctamente"})
    return redirect("/")


@main_bp.route("/get_materia", methods=['GET'])
def get_materias():
    user = verificate_session()
    if user:
        carrera = user["carrera"]
        user_id = str(user["userid"])  # Convertimos el user_id a string para la comparación
        try:
            user_id = str(request.args["userid"])
        except:
            pass
        ciclo = Ciclos.query.filter_by(actual=True).first()
        asignaciones = Asignaciones.query.filter_by(carrera_id=carrera, ciclo_id=ciclo.id).all()
        
        if asignaciones:
            filtered_horarios = {
                "docente": [],
                "materia": [],
                "aula": [],
                "cell_ids": []
            }

            for asignacion in asignaciones:
                horarios = json.loads(asignacion.horario)
                
                for i, docente_id in enumerate(horarios["docente"]):
                    if docente_id == user_id:
                        filtered_horarios["docente"].append(horarios["docente"][i])
                        
                        materia_id = horarios["materia"][i]
                        materia = Materias.query.get(materia_id)
                        materia_nombre = materia.nombre if materia else 'Desconocida'
                        filtered_horarios["materia"].append(materia_nombre)
                        
                        aula_id = horarios["aula"][i]
                        aula = Aulas.query.get(aula_id)
                        aula_nombre = aula.nombre if aula else 'Desconocida'
                        filtered_horarios["aula"].append(aula_nombre)
                        
                        filtered_horarios["cell_ids"].append(horarios["cell_ids"][i])

            if filtered_horarios["docente"]:
                return jsonify({"success": True, "horario": filtered_horarios})
            return jsonify({'error': 'Horario no encontrado'})
        
        return jsonify({'error': 'Horario no encontrado'})
    return redirect("/")

@main_bp.route("/myAccount", methods=['GET'])
def myAccount():
    user = verificate_session()
    if user:
        usuario = Usuarios.query.filter_by(id=user["userid"]).first()
        return render_template("myAccount.html",user=usuario.nombre,usuario=usuario)
    return redirect("/")




