from flask import Blueprint, render_template, request, redirect,jsonify, flash
from extensions import db

import csv , io
from string import capwords

from sqlalchemy.orm import selectinload
from models.tables_db import Usuarios, Materias, Aulas, Ciclos, Carreras
from models.tables_db import DocenteCarreras,MateriasCarreras

from functions import verificate_session, get_hex_digest, random_number


admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin")
def admin():
    """
    Vista del administrador
    """
    user = verificate_session()
    if user:
        username = user["username"]
        return render_template(
            "admin.html", user=username
        )
    return redirect("/")

@admin_bp.route("/admin/usuarios")
def admin_docentes():
    """
    vista administrador con todos los docentes
    """
    user = verificate_session()
    if user:
        username = user["username"]
        usuarios = Usuarios.query.order_by(Usuarios.apellido_pat).all()        
        return render_template(
            "admin_usuarios.html", user=username, usuarios=usuarios
        )
    return redirect("/")

@admin_bp.route("/admin/modificar/usuario/<int:userId>", methods=['GET'])
def admin_modificar(userId):
    """
    Vista para modificar un usuario por parte del administrador
    """
    user = verificate_session()
    if user:
        username = user["username"]
        usuario = Usuarios.query.filter_by(id=userId).first()
        return render_template(
            "modificar_usuario.html", user=username, usuario=usuario
        )  
    return redirect("/")

@admin_bp.route("/update/user", methods=["POST"])
def update():
    """
    Metodo para actualizar la informacion en la base de datos
    """
    user = verificate_session()
    if user:
        form = request.form
        user_id = form.get("id")
        nombre = form.get("nombre")
        apellido_pat = form.get("paterno")
        apellido_mat = form.get("materno")
        email = form.get("email")
        user_type = form.get("user_type")
        habilitado = form.get("habilitado") == 'true'
        usuario = db.session.get(Usuarios, user_id)
        
        usuario_existente = Usuarios.query.filter_by(email=email).first()
        if usuario_existente and usuario_existente.id != int(user_id):
            flash("El correo electrónico ya está registrado por otro usuario.", "error")
            return redirect(f"/admin/modificar/usuario/{user_id}")
        
        if usuario:
            usuario.nombre = nombre
            usuario.apellido_pat = apellido_pat
            usuario.apellido_mat = apellido_mat
            usuario.email = email
            usuario.user_type = user_type
            usuario.habilitado = habilitado
            db.session.commit()
            flash("Usuario actualizado correctamente.", "success")
        return redirect("/admin/usuarios")
    else:
        return redirect("/")

@admin_bp.route("/delete/user", methods=["POST"])
def delete_user():
    """
    Método para borrar un usuario de la base de datos
    """
    user = verificate_session()
    if user:
        user_id = request.form.get("id")
        usuario = Usuarios.query.get(user_id)
        if usuario:
            db.session.delete(usuario)
            db.session.commit()
        flash("Usuario borrado correctamente.", "success")
        return redirect("/admin/usuarios")
    
    return redirect("/")

@admin_bp.route("/crear_usuario", methods=["POST"])
def crear_usuario():
    """
    Metodo para agregar usuario a la base de datos
    """
    user = verificate_session()
    if user:
        # Obtener los datos del formulario
        nombre = request.form.get("nombre")
        apellido_pat = request.form.get("apellido_pat")
        apellido_mat = request.form.get("apellido_mat")
        email = request.form.get("email")
        password = get_hex_digest(str(random_number()))
        user_type = request.form.get("user_type")
        first_login = True  
        habilitado = True
        
        usuario_existente = Usuarios.query.filter_by(email=email).first()
        if usuario_existente:
            flash("El correo electrónico ya está registrado.", "error")
            return redirect("/admin/usuarios")
        
        nuevo_usuario = Usuarios(
            nombre=nombre,
            apellido_pat=apellido_pat,
            apellido_mat=apellido_mat,
            email=email,
            password=password,
            user_type=user_type,
            first_login=first_login,
            habilitado=habilitado
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("Usuario creado exitosamente.", "success")
        return redirect("/admin/usuarios")
    else:
        return redirect("/")


@admin_bp.route("/admin/materias")
def admin_materias():
    """
    vista administrador con todas las materias
    """
    user = verificate_session()
    if user:
        username = user["username"]
        materia = Materias.query.order_by(Materias.semestre).all()
        return render_template(
            "admin_materias.html", user=username, materias=materia
        )
    return redirect("/")

@admin_bp.route("/admin/modificar/materia/<int:materiaId>", methods=['GET'])
def admin_modificar_materia(materiaId):
    """
    Vista para modificar una materia por parte del administrador
    """
    user = verificate_session()
    if user:
        username = user["username"]
        materia = Materias.query.filter_by(id=materiaId).first()
        return render_template(
            "modificar_materia.html", user=username, materia=materia
        )  
    return redirect("/")


@admin_bp.route("/update/materia", methods=["POST"])
def update_materia():
    """
    Metodo para actualizar la informacion en la base de datos
    """
    user = verificate_session()
    if user:
        form = request.form
        materia_id = form.get("id")
        nombre = form.get("nombre")
        clave = form.get("clave")
        semestre = form.get("semestre")
        hpracticas = form.get("Hpracticas")
        hteoria = form.get("Hteoria")

        try:
            hpracticas = int(hpracticas)
            hteoria = int(hteoria)
        except ValueError:
            flash("Las horas de práctica y teoría deben ser números enteros.", "error")
            return redirect(f"/admin/modificar/materia/{materia_id}")

        materia_existente = Materias.query.filter_by(clave=clave).first()
        if materia_existente and materia_existente.id != int(materia_id):
            flash("La clave de la materia ya está en uso por otra materia.", "error")
            return redirect(f"/admin/modificar/materia/{materia_id}")

        materia = db.session.get(Materias, materia_id)
        if materia:
            materia.clave = clave
            materia.nombre = nombre
            materia.semestre = semestre
            materia.horas_practica = hpracticas
            materia.horas_teoria = hteoria
            materia.creditos = hpracticas + hteoria
            db.session.commit()
            flash("Materia actualizada correctamente.", "success")

        return redirect("/admin/materias")
    else:
        return redirect("/")

@admin_bp.route("/delete/materia", methods=["POST"])
def delete_materia():
    """
    Método para borrar una materia de la base de datos
    """
    user = verificate_session()
    if user:
        materiaid = request.form.get("id")
        materia = Materias.query.get(materiaid)
        if materia:
            db.session.delete(materia)
            db.session.commit()
        return redirect("/admin/materias")
    return redirect("/")

@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():
    """
    Metodo para agregar usuario a la base de datos
    """
    user = verificate_session()
    if user:
        form = request.form
        nombre = form.get("nombre")
        clave = form.get("clave")
        semestre = form.get("semestre")
        hpracticas = form.get("Hpracticas")
        hteoria = form.get("Hteoria")
        
        try:
            hpracticas = int(hpracticas)
            hteoria = int(hteoria)
        except ValueError:
            flash("Las horas de práctica y teoría deben ser números enteros.", "error")
            return redirect("/admin/materias")

        materia_existente = Materias.query.filter_by(clave=clave).first()
        if materia_existente:
            flash("La clave de la materia ya está en uso.", "error")
            return redirect("/admin/materias")  

        nueva_materia = Materias(
            clave=clave,
            nombre=nombre,
            semestre=semestre,
            horas_practica=hpracticas,
            horas_teoria=hteoria,
            creditos=hpracticas + hteoria,
        )
        db.session.add(nueva_materia)
        db.session.commit()
        flash("Materia creada correctamente.", "success")
        return redirect("/admin/materias")
    else:
        return redirect("/")

@admin_bp.route("/admin/aulas")
def admin_aulas():
    """
    vista administrador con todas las materias
    """
    user = verificate_session()
    if user:
        username = user["username"]
        aula = Aulas.query.all()
        
        return render_template(
            "admin_aulas.html", user=username,aulas=aula
        )
    return redirect("/")

@admin_bp.route("/admin/modificar/aula/<int:aulaId>", methods=['GET'])
def admin_modificar_aula(aulaId):
    """
    Vista para modificar una aula por parte del administrador
    """
    user = verificate_session()
    if user:
        username = user["username"]
        aula = Aulas.query.filter_by(id=aulaId).first()
        return render_template(
            "modificar_aula.html", user=username, aula=aula
        )  
    return redirect("/")


@admin_bp.route("/update/aula", methods=["POST"])
def update_aula():
    """
    Metodo para actualizar la informacion en la base de datos
    """
    user = verificate_session()
    if user:
        form = request.form
        aula_id = form.get("id")
        nombre = form.get("nombre")
        edificio = form.get("edificio")

        aula_existente = Aulas.query.filter_by(nombre=nombre).first()
        if aula_existente and aula_existente.id != int(aula_id):
            flash("El nombre del aula ya está en uso por otra aula.", "error")
            return redirect(f"/admin/modificar/aula/{aula_id}")

        aula = db.session.get(Aulas, aula_id)
        if aula:
            aula.nombre = nombre
            aula.edificio = edificio
            db.session.commit()
            flash("Aula actualizada correctamente.", "success")

        return redirect("/admin/aulas")
    else:
        return redirect("/")

@admin_bp.route("/delete/aula", methods=["POST"])
def delete_aula():
    """
    Método para borrar una materia de la base de datos
    """
    user = verificate_session()
    if user:
        aulaid = request.form.get("id")
        aula = Aulas.query.get(aulaid)
        if aula:
            db.session.delete(aula)
            db.session.commit()
        return redirect("/admin/aulas")
    return redirect("/")

@admin_bp.route("/crear_aula", methods=["POST"])
def crear_aula():
    """
    Metodo para agregar usuario a la base de datos
    """
    user = verificate_session()
    if user:
        form = request.form
        nombre = form.get("nombre")
        edificio = form.get("edificio")
        
        # Verificar que el nombre no esté en uso por otra aula
        aula_existente = Aulas.query.filter_by(nombre=nombre).first()
        if aula_existente:
            flash("El nombre del aula ya está en uso.", "error")
            return redirect("/admin/aulas")

        nueva_aula = Aulas(
            nombre=nombre,
            edificio=edificio
        )
        db.session.add(nueva_aula)
        db.session.commit()
        flash("Aula creada correctamente.", "success")
        return redirect("/admin/aulas")
    else:
        return redirect("/")


@admin_bp.route("/admin/carreras")
def admin_carreras():
    """
    vista administrador con todas las carreras
    """
    user = verificate_session()
    if user:
        username = user["username"]
        carreras = Carreras.query.all()
        
        return render_template(
            "admin_carreras.html", user=username, carreras=carreras
        )
    return redirect("/")

@admin_bp.route("/admin/carrera/<int:carreraId>", methods=['GET'])
def admin_carrera_asociados(carreraId):
    """
    Vista de materias y docentes asociados a la carrera
    """
    user = verificate_session()
    if user:
        username = user["username"]
        docentes= DocenteCarreras.query.filter_by(carrera_id=carreraId)
        materias= MateriasCarreras.query.filter_by(carrera_id=carreraId)
        
        return render_template(
            "carrera_asociados.html", user=username, docentes=docentes,materias=materias, carreraID=carreraId
        )  
    return redirect("/")

def docente_asociado(carrera_id, docente_id):
    # Verificar si el docente está asociado a la carrera en la base de datos
    return bool(DocenteCarreras.query.filter_by(carrera_id=carrera_id, usuario_id=docente_id).first())

@admin_bp.route("/carrera/<int:carreraId>/asociar/docentes", methods=['GET'])
def asociar_docentes(carreraId):
    """
    Vista para asociar docentes a una carrera específica
    """
    user = verificate_session()
    if user:
        username = user["username"]
        docentes = Usuarios.query.filter(Usuarios.user_type != 1).order_by(Usuarios.apellido_pat).all()
        return render_template("asociar_docentes.html", user=username,
                carreraId=carreraId, docentes=docentes, docente_asociado=docente_asociado)
    
    return redirect("/")

def materia_asociado(carrera_id, materia_id):
    # Verificar si el docente está asociado a la carrera en la base de datos
    return bool(MateriasCarreras.query.filter_by(carrera_id=carrera_id, materia_id=materia_id).first())

@admin_bp.route("/carrera/<int:carreraId>/asociar/materias", methods=['GET'])
def asociar_materia(carreraId):
    """
    Vista para asociar docentes a una carrera específica
    """
    user = verificate_session()
    if user:
        username = user["username"]
        materias = Materias.query.order_by(Materias.semestre).all()
        return render_template("asociar_materias.html", user=username,
                carreraId=carreraId, materias=materias, materia_asociado=materia_asociado)
    
    return redirect("/")

@admin_bp.route("/guardar_docentecarrera", methods=['POST'])
def guardar_docentecarrera():
    user = verificate_session()
    if user:
        data = request.json
        carrera_id = data["carreraId"]
        docentes_seleccionados = data["docentesSeleccionados"]
        docentes_deseleccionados = data["docentesDeseleccionados"]

        if docentes_deseleccionados:
            DocenteCarreras.query.filter(
                DocenteCarreras.carrera_id == carrera_id,
                DocenteCarreras.usuario_id.in_(docentes_deseleccionados)
            ).delete(synchronize_session=False)

        if docentes_seleccionados:
            for docente_id in docentes_seleccionados:
                if not DocenteCarreras.query.filter_by(carrera_id=carrera_id, usuario_id=docente_id).first():
                    nueva_relacion = DocenteCarreras(carrera_id=carrera_id, usuario_id=docente_id)
                    db.session.add(nueva_relacion)
        db.session.commit()

        return jsonify({"success": True})
    return redirect("/")

@admin_bp.route("/guardar_materiacarrera", methods=['POST'])
def guardar_materiacarrera():
    user = verificate_session()
    if user:
        data = request.json
        carrera_id = data["carreraId"]
        materias_seleccionados = data["materiasSeleccionados"]
        materias_deseleccionados = data["materiasDeseleccionados"]

        if materias_deseleccionados:
            MateriasCarreras.query.filter(
                MateriasCarreras.carrera_id == carrera_id,
                MateriasCarreras.materia_id.in_(materias_deseleccionados)
            ).delete(synchronize_session=False)

        if materias_seleccionados:
            for materia_id in materias_seleccionados:
                if not MateriasCarreras.query.filter_by(carrera_id=carrera_id, materia_id=materia_id).first():
                    nueva_relacion = MateriasCarreras(carrera_id=carrera_id, materia_id=materia_id)
                    db.session.add(nueva_relacion)
        db.session.commit()

        return jsonify({"success": True})
    return redirect("/")    
    

@admin_bp.route("/admin/modificar/carrera/<int:carreraId>", methods=['GET'])
def admin_modificar_carrera(carreraId):
    """
    Vista para modificar una carrera por parte del administrador
    """
    user = verificate_session()
    if user:
        username = user["username"]
        carrera = Carreras.query.filter_by(id=carreraId).first()
        return render_template(
            "modificar_carrera.html", user=username, carrera=carrera
        )  
    return redirect("/")


@admin_bp.route("/update/carrera", methods=["POST"])
def update_carrera():
    """
    Metodo para actualizar la informacion en la base de datos
    """
    user = verificate_session()
    if user:
        form = request.form
        carrera_id = form.get("id")
        nombre = form.get("nombre")
        plan = form.get("plan")

        carrera_existente = Carreras.query.filter_by(plan_de_estudio=plan).first()
        if carrera_existente and carrera_existente.id != int(carrera_id):
            flash("El plan de estudio ya está en uso por otra carrera.", "error")
            return redirect(f"/admin/modificar/carrera/{carrera_id}")

        carrera = db.session.get(Carreras, carrera_id)
        if carrera:
            carrera.nombre = nombre
            carrera.plan_de_estudio = plan
            db.session.commit()
            flash("Carrera actualizada correctamente.", "success")

        return redirect("/admin/carreras")
    else:
        return redirect("/")

@admin_bp.route("/delete/carrera", methods=["POST"])
def delete_carrera():
    """
    Método para borrar una carrera de la base de datos
    """
    user = verificate_session()
    if user:
        carreraid = request.form.get("id")
        carrera = Carreras.query.get(carreraid)
        if carrera:
            db.session.delete(carrera)
            db.session.commit()
        return redirect("/admin/carreras")
    return redirect("/")

@admin_bp.route("/crear_carrera", methods=["POST"])
def crear_carrera():
    """
    Metodo para agregar una carrera a la base de datos
    """
    user = verificate_session()
    if user:
        form = request.form
        nombre = form.get("nombre")
        plan = form.get("plan")
        
        carrera_existente = Carreras.query.filter_by(plan_de_estudio=plan).first()
        if carrera_existente:
            flash("El plan de estudio ya está en uso.", "error")
            return redirect("/admin/carreras")

        nueva_carrera = Carreras(
            nombre=nombre,
            plan_de_estudio=plan
        )
        db.session.add(nueva_carrera)
        db.session.commit()
        flash("Carrera creada correctamente.", "success")
        return redirect("/admin/carreras")
    else:
        return redirect("/")    

@admin_bp.route("/admin/ciclos")
def admin_ciclos():
    """
    vista administrador con todas las ciclos
    """
    user = verificate_session()
    if user:
        username = user["username"]
        ciclos = Ciclos.query.all()
        
        return render_template(
            "admin_ciclos.html", user=username, ciclos=ciclos
        )
    return redirect("/")

@admin_bp.route("/admin/modificar/ciclo/<int:cicloId>", methods=['GET'])
def admin_modificar_ciclo(cicloId):
    """
    Vista para modificar una carrera por parte del administrador
    """
    user = verificate_session()
    if user:
        username = user["username"]
        ciclo = Ciclos.query.filter_by(id=cicloId).first()
        return render_template(
            "modificar_ciclo.html", user=username, ciclo=ciclo
        )  
    return redirect("/")


@admin_bp.route("/update/ciclo", methods=["POST"])
def update_ciclo():
    """
    Metodo para actualizar la informacion en la base de datos
    """
    user = verificate_session()
    if user:
        form = request.form
        ciclo_id = form.get("id")
        anio = form.get("anio")
        estacion = form.get("estacion")
        actua = form.get("actual") == 'true'
        
        ciclo_existente = Ciclos.query.filter_by(anio=anio, estacion=estacion).first()
        if ciclo_existente and ciclo_existente.id != int(ciclo_id):
            flash("Ya existe un ciclo con el mismo año y estación.", "error")
            return redirect(f"/admin/modificar/ciclo/{ciclo_id}")

        if actua:
            change = Ciclos.query.filter_by(actual=True).first()
            if change:
                change.actual = False
                db.session.commit()
                       
        ciclo = db.session.get(Ciclos, ciclo_id)
        if ciclo:
            ciclo.anio = anio
            ciclo.estacion = estacion
            ciclo.actual = actua
            
            db.session.commit()
            flash("Ciclo actualizado correctamente.", "success")

        return redirect("/admin/ciclos")
    else:
        return redirect("/")

@admin_bp.route("/delete/ciclo", methods=["POST"])
def delete_ciclo():
    """
    Método para borrar una carrera de la base de datos
    """
    user = verificate_session()
    if user:
        cicloid = request.form.get("id")
        ciclo = Ciclos.query.options(selectinload(Ciclos.disponibilidades), selectinload(Ciclos.asignaciones)).get(cicloid)
        if ciclo:
            db.session.delete(ciclo)
            db.session.commit()
        return redirect("/admin/ciclos")
    return redirect("/")

@admin_bp.route("/crear_ciclo", methods=["POST"])
def crear_ciclo():
    """
    Metodo para agregar una carrera a la base de datos
    """
    user = verificate_session()
    if user:
        form = request.form
        anio = form.get("anio")
        estacion = form.get("estacion")
        actua = form.get("actual") == 'true'
        
        ciclo_existente = Ciclos.query.filter_by(anio=anio, estacion=estacion).first()
        if ciclo_existente:
            flash("Ya existe un ciclo con el mismo año y estación.", "error")
            return redirect("/admin/ciclos")

        if actua:
            change = Ciclos.query.filter_by(actual=True).first()
            if change:
                change.actual = False
                db.session.commit()
            
        nuevo_ciclo = Ciclos(
            anio=anio,
            estacion=estacion,
            actual=actua
        )
        db.session.add(nuevo_ciclo)
        db.session.commit()
        flash("Ciclo creado correctamente.", "success")
        return redirect("/admin/ciclos")
    else:
        return redirect("/")
    
@admin_bp.route('/upload_csv_usuario', methods=['POST'])   
def upload_csv_usuario():
    user = verificate_session()  
    if user:
        file = request.files['file']
        
        if file.filename == '':
            flash('No se seleccionó un archivo')
            return redirect("/admin/usuarios")  
        
        if file and file.filename.endswith('.csv'):
            try:
                stream = io.StringIO(file.stream.read().decode('latin-1'), newline=None)
                csv_input = csv.reader(stream)
                
                headers = next(csv_input)
                expected_headers = ['nombre', 'apellido paterno', 'apellido materno', 'email', 'tipo de usuario']
                if headers != expected_headers:
                    flash('El encabezado del CSV no coincide, vea la guía')
                    return redirect("/admin/usuarios")  
                
                for row in csv_input:
                    if len(row) != 5:
                        flash('El CSV cuenta con más columnas de las que debería')
                        return redirect("/admin/usuarios")  

                    nombre, apellido_pat, apellido_mat, email, user_type = row

                    nombre = capwords(nombre)
                    apellido_pat = capwords(apellido_pat)
                    apellido_mat = capwords(apellido_mat)
                    email = email.lower()

                    existing_user = Usuarios.query.filter_by(email=email).first()
                    if existing_user:
                        continue  

                    password = get_hex_digest(str(random_number()))
                    first_login = True  
                    habilitado = True

                    nuevo_usuario = Usuarios(
                        nombre=nombre,
                        apellido_pat=apellido_pat,
                        apellido_mat=apellido_mat,
                        email=email,
                        password=password,
                        user_type=user_type,
                        first_login=first_login,
                        habilitado=habilitado
                    )
                    db.session.add(nuevo_usuario)

                db.session.commit()
                flash('Guardado correctamente')
                return redirect("/admin/usuarios")  
            except Exception as e:
                flash(f'Error al procesar el CSV: {e}')
                return redirect('/admin/usuarios')  
        else:
            flash('Formato inválido, seleccione un archivo CSV por favor.')
            return redirect("/admin/usuarios")  
    else:
        return redirect("/admin/usuarios")
    
    
@admin_bp.route('/upload_csv_materia', methods=['POST'])   
def upload_csv_materia():
    user = verificate_session()  # Verifica la sesión del usuario
    if user:
        file = request.files['file']
        
        if file.filename == '':
            flash('No se seleccionó un archivo')
            return redirect("/admin/materias")  
        
        if file and file.filename.endswith('.csv'):
            try:
                stream = io.StringIO(file.stream.read().decode('latin-1'), newline=None)
                csv_input = csv.reader(stream)
                
                headers = next(csv_input)
                expected_headers = ['nombre', 'clave', 'semestre', 'horas practica', 'horas teoria']
                if headers != expected_headers:
                    flash('El encabezado del csv no coincide, vea la guía')
                    return redirect("/admin/materias")  

                # Lista para almacenar las claves de materias existentes
                materias_existentes = []

                for row in csv_input:
                    if len(row) != 5:
                        flash('El CSV cuenta con más columnas de las que debería')
                        return redirect("/admin/materias")  
                    
                    nombre, clave, semestre, horas_practica, horas_teoria = row

                    nombre = capwords(nombre)
                    
                    existing_materia = Materias.query.filter_by(clave=clave).first()
                    if existing_materia:
                        continue 

                    horas_practica = int(horas_practica)
                    horas_teoria = int(horas_teoria)
                    creditos = horas_practica + horas_teoria
                    nueva_materia = Materias(
                        nombre=nombre,
                        clave=clave,
                        semestre=semestre,
                        horas_practica=horas_practica,
                        horas_teoria=horas_teoria,
                        creditos=creditos
                    )
                    db.session.add(nueva_materia)
                    materias_existentes.append(clave)  
                
                db.session.commit()
                flash('Guardado correctamente')
                return redirect("/admin/materias")  
            except Exception as e:
                flash(f'Error al procesar el CSV: {e}')
                return redirect("/admin/materias")  
        else:
            flash('Formato inválido, seleccione un archivo CSV por favor.')
            return redirect("/admin/materias")  
    else:
        return redirect("/admin/materias")