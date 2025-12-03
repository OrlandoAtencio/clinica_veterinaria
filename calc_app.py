# app.py - SISTEMA DE GESTIÓN VETERINARIA
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
import sqlite3
from datetime import datetime, timedelta
import hashlib
import secrets
import time
import os

# Importar funciones de tu database.py existente
from database import (
    init_db, 
    get_db_connection, 
    hash_password, 
    verify_password,
    log_evento_seguridad,
    obtener_usuario_por_username,
    obtener_pacientes,
    obtener_consultas_pendientes
)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configuración
DB_NAME = 'clinic.db'
MAX_INTENTOS_LOGIN = 5
TIEMPO_BLOQUEO_MINUTOS = 30

# Diccionarios para seguridad
intentos_ip = {}

# ==================== FUNCIONES DE BASE DE DATOS ====================

def init_db():
    """Inicializa la base de datos"""
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                rol TEXT NOT NULL CHECK(rol IN ('admin', 'doctor')),
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activo INTEGER DEFAULT 1,
                intentos_login INTEGER DEFAULT 0,
                bloqueado_hasta TIMESTAMP NULL,
                ultimo_intento TIMESTAMP NULL,
                especialidad TEXT
            )
        ''')
        
        # Tabla de pacientes
        cursor.execute('''
            CREATE TABLE pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                especie TEXT NOT NULL,
                raza TEXT,
                edad INTEGER,
                peso REAL,
                color TEXT,
                sexo TEXT CHECK(sexo IN ('M', 'F')),
                nombre_dueno TEXT NOT NULL,
                telefono_dueno TEXT NOT NULL,
                email_dueno TEXT,
                direccion_dueno TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notas TEXT,
                alergias TEXT,
                vacunas TEXT
            )
        ''')
        
        # Tabla de consultas
        cursor.execute('''
            CREATE TABLE consultas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                fecha_consulta TIMESTAMP NOT NULL,
                motivo TEXT NOT NULL,
                diagnostico TEXT,
                tratamiento TEXT,
                medicamentos TEXT,
                proxima_cita TIMESTAMP,
                estado TEXT CHECK(estado IN ('pendiente', 'completada', 'cancelada')) DEFAULT 'pendiente',
                costo REAL,
                notas_internas TEXT,
                FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
                FOREIGN KEY (doctor_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabla de historial médico
        cursor.execute('''
            CREATE TABLE historial_medico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                consulta_id INTEGER,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT NOT NULL CHECK(tipo IN ('consulta', 'vacuna', 'cirugia', 'analisis', 'otro')),
                descripcion TEXT NOT NULL,
                doctor_id INTEGER,
                archivo_adjunto TEXT,
                FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
                FOREIGN KEY (consulta_id) REFERENCES consultas (id),
                FOREIGN KEY (doctor_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabla de mantenimiento
        cursor.execute('''
            CREATE TABLE mantenimiento_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('actualizacion', 'mantenimiento', 'backup', 'error')) NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                realizado_por INTEGER,
                estado TEXT CHECK(estado IN ('pendiente', 'en_proceso', 'completado')) DEFAULT 'pendiente',
                FOREIGN KEY (realizado_por) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabla de logs de seguridad
        cursor.execute('''
            CREATE TABLE logs_seguridad (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_evento TEXT NOT NULL,
                usuario TEXT,
                ip TEXT,
                detalles TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insertar usuarios iniciales con contraseñas hasheadas
        usuarios_iniciales = [
            ('admin', hash_password('Admin123!'), 'Administrador Principal', 'admin@vetclinic.com', 'admin'),
            ('dra.lopez', hash_password('DraLopez456!'), 'Dra. María López', 'mlopez@vetclinic.com', 'doctor'),
            ('dr.gomez', hash_password('DrGomez789!'), 'Dr. Carlos Gómez', 'cgomez@vetclinic.com', 'doctor')
        ]
        
        for usuario in usuarios_iniciales:
            try:
                cursor.execute(
                    'INSERT INTO usuarios (username, password, nombre, email, rol) VALUES (?, ?, ?, ?, ?)',
                    usuario
                )
            except:
                pass
        
        # Insertar pacientes de ejemplo
        pacientes_ejemplo = [
            ('Max', 'Perro', 'Labrador Retriever', 5, 28.5, 'Dorado', 'M',
             'Ana García', '555-1234', 'ana.garcia@email.com', 'Calle Primavera 123',
             'Muy juguetón, alergia a algunos alimentos', 'Alergia al pollo', 'Rabia, Parvovirus'),
            
            ('Luna', 'Gato', 'Siamés', 3, 4.2, 'Blanco con gris', 'F',
             'Carlos Martínez', '555-5678', 'carlos.m@email.com', 'Av. Central 456',
             'Tímida pero cariñosa', 'Ninguna conocida', 'Rabia, Triple felina')
        ]
        
        for paciente in pacientes_ejemplo:
            try:
                cursor.execute('''
                    INSERT INTO pacientes 
                    (nombre, especie, raza, edad, peso, color, sexo, nombre_dueno, 
                     telefono_dueno, email_dueno, direccion_dueno, notas, alergias, vacunas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', paciente)
            except:
                pass
        
        # Insertar consultas de ejemplo
        consultas_ejemplo = [
            (1, 2, '2024-01-20 10:00:00', 'Vacunación anual', 
             'Saludable, peso ideal', 'Vacuna múltiple y desparasitación',
             'Vacuna: DHPP, Antiparasitario: Prazitel', '2024-07-20 10:00:00',
             'completada', 850.50, 'Paciente muy tranquilo durante el procedimiento'),
            
            (2, 3, '2024-01-21 14:30:00', 'Pérdida de apetito',
             'Problema dental, gingivitis leve', 'Limpieza dental y antibióticos',
             'Clindamicina 50mg cada 12h por 7 días', '2024-01-28 15:00:00',
             'pendiente', 1200.00, 'Revisión programada para próxima semana')
        ]
        
        for consulta in consultas_ejemplo:
            try:
                cursor.execute('''
                    INSERT INTO consultas 
                    (paciente_id, doctor_id, fecha_consulta, motivo, diagnostico, 
                     tratamiento, medicamentos, proxima_cita, estado, costo, notas_internas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', consulta)
            except:
                pass
        
        conn.commit()
        conn.close()
        print(f"✅ Base de datos '{DB_NAME}' creada con datos de ejemplo")
    else:
        print(f"✅ Base de datos '{DB_NAME}' ya existe")

def get_db_connection():
    """Crea conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Genera hash de contraseña"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{password_hash.hex()}"

def verify_password(password, stored_hash):
    """Verifica contraseña con hash almacenado"""
    try:
        salt, stored_password_hash = stored_hash.split(':')
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return password_hash.hex() == stored_password_hash
    except:
        return False

# ==================== DECORADORES ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Acceso restringido a administradores', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    """Redirige al login si no hay sesión"""
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('doctor_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Verificar rate limiting por IP
        ip = request.remote_addr
        ahora = time.time()
        
        if ip not in intentos_ip:
            intentos_ip[ip] = []
        
        # Limpiar intentos antiguos (5 minutos)
        intentos_ip[ip] = [t for t in intentos_ip[ip] if ahora - t < 300]
        
        if len(intentos_ip[ip]) >= 10:
            flash('Demasiados intentos desde tu IP. Espera 5 minutos.', 'error')
            return render_template('llogin.html')
        
        # Buscar usuario
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE username = ? AND activo = 1',
            (username,)
        ).fetchone()
        
        if user and verify_password(password, user['password']):
            # Login exitoso
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['nombre']
            session['email'] = user['email']
            session['role'] = user['rol']
            
            # Resetear intentos fallidos
            conn.execute(
                'UPDATE usuarios SET intentos_login = 0, bloqueado_hasta = NULL WHERE id = ?',
                (user['id'],)
            )
            
            # Registrar login exitoso
            conn.execute(
                'INSERT INTO logs_seguridad (tipo_evento, usuario, ip, detalles) VALUES (?, ?, ?, ?)',
                ('LOGIN_EXITOSO', username, ip, 'Inicio de sesión exitoso')
            )
            
            conn.commit()
            conn.close()
            
            # Limpiar intentos de esta IP
            intentos_ip[ip] = []
            
            flash(f'¡Bienvenido/a, {user["nombre"]}!', 'success')
            
            if user['rol'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('doctor_dashboard'))
        else:
            # Login fallido
            if user:
                # Incrementar intentos fallidos
                nuevos_intentos = user['intentos_login'] + 1
                ahora_dt = datetime.now()
                
                if nuevos_intentos >= MAX_INTENTOS_LOGIN:
                    bloqueado_hasta = ahora_dt + timedelta(minutes=TIEMPO_BLOQUEO_MINUTOS)
                    conn.execute(
                        '''UPDATE usuarios 
                        SET intentos_login = ?, bloqueado_hasta = ?, ultimo_intento = ? 
                        WHERE id = ?''',
                        (nuevos_intentos, bloqueado_hasta.isoformat(), ahora_dt.isoformat(), user['id'])
                    )
                    flash('Cuenta bloqueada por demasiados intentos fallidos. Espera 30 minutos.', 'error')
                else:
                    conn.execute(
                        'UPDATE usuarios SET intentos_login = ?, ultimo_intento = ? WHERE id = ?',
                        (nuevos_intentos, ahora_dt.isoformat(), user['id'])
                    )
                
                # Registrar intento fallido
                conn.execute(
                    'INSERT INTO logs_seguridad (tipo_evento, usuario, ip, detalles) VALUES (?, ?, ?, ?)',
                    ('LOGIN_FALLIDO', username, ip, f'Intento fallido #{nuevos_intentos}')
                )
            else:
                # Usuario no existe
                conn.execute(
                    'INSERT INTO logs_seguridad (tipo_evento, usuario, ip, detalles) VALUES (?, ?, ?, ?)',
                    ('LOGIN_FALLIDO', username, ip, 'Usuario no existe')
                )
            
            conn.commit()
            conn.close()
            
            # Agregar intento a rate limiting
            intentos_ip[ip].append(ahora)
            
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    if 'username' in session:
        # Registrar logout
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO logs_seguridad (tipo_evento, usuario, ip, detalles) VALUES (?, ?, ?, ?)',
            ('LOGOUT', session['username'], request.remote_addr, 'Cierre de sesión')
        )
        conn.commit()
        conn.close()
    
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))

# ==================== DASHBOARDS ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal (redirige según rol)"""
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('doctor_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Dashboard de administrador"""
    conn = get_db_connection()
    
    # Estadísticas
    stats = {
        'total_pacientes': conn.execute('SELECT COUNT(*) FROM pacientes').fetchone()[0],
        'total_doctores': conn.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'doctor'").fetchone()[0],
        'consultas_hoy': conn.execute(
            "SELECT COUNT(*) FROM consultas WHERE DATE(fecha_consulta) = DATE('now')"
        ).fetchone()[0],
        'consultas_pendientes': conn.execute(
            "SELECT COUNT(*) FROM consultas WHERE estado = 'pendiente'"
        ).fetchone()[0],
        'ingresos_mes': conn.execute(
            "SELECT SUM(costo) FROM consultas WHERE strftime('%Y-%m', fecha_consulta) = strftime('%Y-%m', 'now')"
        ).fetchone()[0] or 0
    }
    
    # Últimos registros
    ultimos_pacientes = conn.execute(
        'SELECT * FROM pacientes ORDER BY fecha_registro DESC LIMIT 5'
    ).fetchall()
    
    ultimas_consultas = conn.execute('''
        SELECT c.*, p.nombre as paciente_nombre, u.nombre as doctor_nombre
        FROM consultas c
        JOIN pacientes p ON c.paciente_id = p.id
        JOIN usuarios u ON c.doctor_id = u.id
        ORDER BY c.fecha_consulta DESC LIMIT 5
    ''').fetchall()
    
    # Logs recientes
    logs_recientes = conn.execute(
        'SELECT * FROM logs_seguridad ORDER BY fecha DESC LIMIT 10'
    ).fetchall()
    
    conn.close()
    
    return render_template('admin-dashboard.html',
                         stats=stats,
                         pacientes=ultimos_pacientes,
                         consultas=ultimas_consultas,
                         logs=logs_recientes)

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    """Dashboard de doctor"""
    conn = get_db_connection()
    
    # Estadísticas para el doctor
    doctor_id = session['user_id']
    
    stats = {
        'mis_pacientes': conn.execute(
            'SELECT COUNT(DISTINCT paciente_id) FROM consultas WHERE doctor_id = ?',
            (doctor_id,)
        ).fetchone()[0],
        'consultas_hoy': conn.execute(
            "SELECT COUNT(*) FROM consultas WHERE doctor_id = ? AND DATE(fecha_consulta) = DATE('now')",
            (doctor_id,)
        ).fetchone()[0],
        'consultas_pendientes': conn.execute(
            "SELECT COUNT(*) FROM consultas WHERE doctor_id = ? AND estado = 'pendiente'",
            (doctor_id,)
        ).fetchone()[0],
        'ingresos_mes': conn.execute(
            "SELECT SUM(costo) FROM consultas WHERE doctor_id = ? AND strftime('%Y-%m', fecha_consulta) = strftime('%Y-%m', 'now')",
            (doctor_id,)
        ).fetchone()[0] or 0
    }
    
    # Próximas consultas
    proximas_consultas = conn.execute('''
        SELECT c.*, p.nombre as paciente_nombre, p.especie
        FROM consultas c
        JOIN pacientes p ON c.paciente_id = p.id
        WHERE c.doctor_id = ? AND c.estado = 'pendiente'
        ORDER BY c.fecha_consulta ASC
        LIMIT 5
    ''', (doctor_id,)).fetchall()
    
    # Pacientes recientes
    pacientes_recientes = conn.execute('''
        SELECT p.* FROM pacientes p
        JOIN consultas c ON p.id = c.paciente_id
        WHERE c.doctor_id = ?
        GROUP BY p.id
        ORDER BY MAX(c.fecha_consulta) DESC
        LIMIT 5
    ''', (doctor_id,)).fetchall()
    
    conn.close()
    
    return render_template('doctor-dashboard.html',
                         stats=stats,
                         consultas=proximas_consultas,
                         pacientes=pacientes_recientes)

# ==================== PACIENTES ====================

@app.route('/pacientes')
@login_required
def pacientes():
    """Lista de pacientes"""
    busqueda = request.args.get('q', '')
    
    conn = get_db_connection()
    
    if busqueda:
        pacientes = conn.execute('''
            SELECT * FROM pacientes 
            WHERE nombre LIKE ? OR nombre_dueno LIKE ? OR especie LIKE ?
            ORDER BY nombre
        ''', (f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%')).fetchall()
    else:
        pacientes = conn.execute('SELECT * FROM pacientes ORDER BY nombre').fetchall()
    
    conn.close()
    
    return render_template('historial-pacientes.html', pacientes=pacientes, busqueda=busqueda)

@app.route('/pacientes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_paciente():
    """Registrar nuevo paciente"""
    if request.method == 'POST':
        try:
            # Recoger datos del formulario
            datos = {
                'nombre': request.form.get('nombre', '').strip(),
                'especie': request.form.get('especie', '').strip(),
                'raza': request.form.get('raza', '').strip(),
                'edad': request.form.get('edad'),
                'peso': request.form.get('peso'),
                'color': request.form.get('color', '').strip(),
                'sexo': request.form.get('sexo', 'M'),
                'nombre_dueno': request.form.get('dueno', '').strip(),
                'telefono_dueno': request.form.get('telefono', '').strip(),
                'email_dueno': request.form.get('email', '').strip(),
                'direccion_dueno': request.form.get('direccion', '').strip(),
                'notas': request.form.get('notas', '').strip(),
                'alergias': request.form.get('alergias', '').strip(),
                'vacunas': request.form.get('vacunas', '').strip()
            }
            
            # Validaciones básicas
            if not datos['nombre'] or not datos['especie']:
                flash('Nombre y especie son campos requeridos', 'error')
                return render_template('register-patient.html', datos=datos)
            
            # Convertir tipos
            if datos['edad']:
                try:
                    datos['edad'] = int(datos['edad'])
                except:
                    datos['edad'] = None
            
            if datos['peso']:
                try:
                    datos['peso'] = float(datos['peso'])
                except:
                    datos['peso'] = None
            
            # Insertar en base de datos
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO pacientes 
                (nombre, especie, raza, edad, peso, color, sexo, nombre_dueno, 
                 telefono_dueno, email_dueno, direccion_dueno, notas, alergias, vacunas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datos['nombre'], datos['especie'], datos['raza'], datos['edad'],
                datos['peso'], datos['color'], datos['sexo'], datos['nombre_dueno'],
                datos['telefono_dueno'], datos['email_dueno'], datos['direccion_dueno'],
                datos['notas'], datos['alergias'], datos['vacunas']
            ))
            
            paciente_id = cursor.lastrowid
            
            # Registrar en logs
            cursor.execute(
                'INSERT INTO logs_seguridad (tipo_evento, usuario, ip, detalles) VALUES (?, ?, ?, ?)',
                ('PACIENTE_REGISTRADO', session['username'], request.remote_addr,
                 f'Paciente #{paciente_id}: {datos["nombre"]}')
            )
            
            conn.commit()
            conn.close()
            
            flash(f'Paciente {datos["nombre"]} registrado exitosamente', 'success')
            return redirect(url_for('pacientes'))
            
        except Exception as e:
            flash(f'Error al registrar paciente: {str(e)}', 'error')
            return render_template('register-patient.html', datos=datos)
    
    return render_template('register-patient.html')

# ==================== CONSULTAS ====================

@app.route('/consultas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_consulta():
    """Registrar nueva consulta"""
    if request.method == 'POST':
        try:
            datos = {
                'paciente_id': request.form.get('paciente_id'),
                'fecha_consulta': request.form.get('fecha'),
                'motivo': request.form.get('motivo', '').strip(),
                'diagnostico': request.form.get('diagnostico', '').strip(),
                'tratamiento': request.form.get('tratamiento', '').strip(),
                'medicamentos': request.form.get('medicamentos', '').strip(),
                'proxima_cita': request.form.get('proxima_cita'),
                'costo': request.form.get('costo', '0'),
                'notas': request.form.get('notas', '').strip()
            }
            
            # Validaciones
            if not datos['paciente_id'] or not datos['fecha_consulta'] or not datos['motivo']:
                flash('Paciente, fecha y motivo son campos requeridos', 'error')
                return redirect(url_for('nueva_consulta'))
            
            # Convertir costo
            try:
                datos['costo'] = float(datos['costo'])
            except:
                datos['costo'] = 0.0
            
            # Insertar consulta
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO consultas 
                (paciente_id, doctor_id, fecha_consulta, motivo, diagnostico, 
                 tratamiento, medicamentos, proxima_cita, costo, notas_internas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datos['paciente_id'], session['user_id'], datos['fecha_consulta'],
                datos['motivo'], datos['diagnostico'], datos['tratamiento'],
                datos['medicamentos'], datos['proxima_cita'], datos['costo'],
                datos['notas']
            ))
            
            consulta_id = cursor.lastrowid
            
            # Agregar al historial médico
            cursor.execute('''
                INSERT INTO historial_medico 
                (paciente_id, consulta_id, tipo, descripcion, doctor_id)
                VALUES (?, ?, 'consulta', ?, ?)
            ''', (datos['paciente_id'], consulta_id, datos['motivo'], session['user_id']))
            
            # Registrar en logs
            cursor.execute(
                'INSERT INTO logs_seguridad (tipo_evento, usuario, ip, detalles) VALUES (?, ?, ?, ?)',
                ('CONSULTA_REGISTRADA', session['username'], request.remote_addr,
                 f'Consulta #{consulta_id} para paciente #{datos["paciente_id"]}')
            )
            
            conn.commit()
            conn.close()
            
            flash('Consulta registrada exitosamente', 'success')
            return redirect(url_for('doctor_dashboard'))
            
        except Exception as e:
            flash(f'Error al registrar consulta: {str(e)}', 'error')
            return redirect(url_for('nueva_consulta'))
    
    # GET - Obtener lista de pacientes para el formulario
    conn = get_db_connection()
    pacientes = conn.execute('SELECT id, nombre, especie FROM pacientes ORDER BY nombre').fetchall()
    conn.close()
    
    return render_template('register-consultation.html', pacientes=pacientes)

# ==================== MANTENIMIENTO ====================

@app.route('/mantenimiento')
@admin_required
def mantenimiento():
    """Página de mantenimiento del sistema"""
    conn = get_db_connection()
    
    registros = conn.execute('''
        SELECT m.*, u.nombre as responsable
        FROM mantenimiento_sistema m
        LEFT JOIN usuarios u ON m.realizado_por = u.id
        ORDER BY m.fecha DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('system-maintenance.html', registros=registros)

@app.route('/api/estadisticas')
@login_required
def api_estadisticas():
    """API para obtener estadísticas en tiempo real"""
    conn = get_db_connection()
    
    stats = {}
    
    if session.get('role') == 'admin':
        stats = {
            'total_pacientes': conn.execute('SELECT COUNT(*) FROM pacientes').fetchone()[0],
            'total_consultas': conn.execute('SELECT COUNT(*) FROM consultas').fetchone()[0],
            'consultas_pendientes': conn.execute(
                "SELECT COUNT(*) FROM consultas WHERE estado = 'pendiente'"
            ).fetchone()[0],
            'ingresos_hoy': conn.execute(
                "SELECT SUM(costo) FROM consultas WHERE DATE(fecha_consulta) = DATE('now')"
            ).fetchone()[0] or 0
        }
    else:
        doctor_id = session['user_id']
        stats = {
            'mis_pacientes': conn.execute(
                'SELECT COUNT(DISTINCT paciente_id) FROM consultas WHERE doctor_id = ?',
                (doctor_id,)
            ).fetchone()[0],
            'consultas_hoy': conn.execute(
                "SELECT COUNT(*) FROM consultas WHERE doctor_id = ? AND DATE(fecha_consulta) = DATE('now')",
                (doctor_id,)
            ).fetchone()[0],
            'consultas_pendientes': conn.execute(
                "SELECT COUNT(*) FROM consultas WHERE doctor_id = ? AND estado = 'pendiente'",
                (doctor_id,)
            ).fetchone()[0]
        }
    
    conn.close()
    return jsonify(stats)

# ==================== INICIALIZACIÓN ====================

@app.route('/inicializar')
def inicializar_sistema():
    """Ruta para inicializar la base de datos"""
    try:
        init_db()
        return '''
            <h1>Sistema Inicializado</h1>
            <p>Base de datos creada exitosamente.</p>
            <p><a href="/">Ir al login</a></p>
            <p>Credenciales:</p>
            <ul>
                <li>Admin: admin / Admin123!</li>
                <li>Doctor: dra.lopez / DraLopez456!</li>
                <li>Doctor: dr.gomez / DrGomez789!</li>
            </ul>
        '''
    except Exception as e:
        return f'<h1>Error</h1><p>{str(e)}</p>'

# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template('error.html', 
                         mensaje='Página no encontrada',
                         detalles='La página que buscas no existe.'), 404

@app.errorhandler(403)
def acceso_denegado(error):
    return render_template('error.html',
                         mensaje='Acceso denegado',
                         detalles='No tienes permiso para acceder a esta página.'), 403

@app.errorhandler(500)
def error_interno(error):
    return render_template('error.html',
                         mensaje='Error interno del servidor',
                         detalles='Ha ocurrido un error inesperado.'), 500

# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    # Verificar si la base de datos existe
    if not os.path.exists(DB_NAME):
        print("⚠️  Base de datos no encontrada. Ejecuta /inicializar para crearla.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)