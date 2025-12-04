from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from database import get_db_connection, verify_password, init_db, obtener_usuario_por_username 
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_veterinaria_2024'  # Clave secreta para sesiones

# Inicializar base de datos si no existe
if not os.path.exists('clinic.db'):
    print("Inicializando base de datos...")
    init_db()

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/')
def index():
    """Redirige al login"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET'])
def login():
    """Muestra la página de login"""
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    """Procesa el login"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email y contraseña son requeridos'}), 400
        
        # Buscar usuario por email
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = ? AND activo = 1', (email,))
        usuario = cursor.fetchone()
        conn.close()
        
        if not usuario:
            return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401
        
        # Verificar contraseña
        if not verify_password(password, usuario['password']):
            return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401
        
        # Guardar sesión
        session['user_id'] = usuario['id']
        session['username'] = usuario['username']
        session['nombre'] = usuario['nombre']
        session['rol'] = usuario['rol']
        
        # Redirigir según rol
        if usuario['rol'] == 'admin':
            redirect_url = url_for('admin_dashboard')
        else:
            redirect_url = url_for('doctor_dashboard')
        
        return jsonify({
            'success': True, 
            'message': 'Login exitoso',
            'redirect': redirect_url,
            'rol': usuario['rol']
        }), 200
        
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({'success': False, 'message': 'Error del servidor'}), 500

@app.route('/logout')
def logout():
    """Cierra sesión"""
    session.clear()
    return redirect(url_for('login'))

# ==================== RUTAS DEL ADMIN ====================

@app.route('/admin/dashboard')
def admin_dashboard():
    """Dashboard del administrador"""
    if 'user_id' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener estadísticas
        cursor.execute('SELECT COUNT(*) as total FROM pacientes')
        total_pacientes = cursor.fetchone()['total']
        
        cursor.execute('''
            SELECT COUNT(*) as total FROM consultas 
            WHERE strftime('%Y-%m', fecha_consulta) = strftime('%Y-%m', 'now')
        ''')
        consultas_mes = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol = 'doctor' AND activo = 1")
        doctores = cursor.fetchone()['total']
        
        # Rendimiento de médicos
        cursor.execute('''
            SELECT u.nombre, COUNT(c.id) as total_consultas
            FROM usuarios u
            LEFT JOIN consultas c ON u.id = c.doctor_id
            WHERE u.rol = 'doctor' AND u.activo = 1
            GROUP BY u.id, u.nombre
            ORDER BY total_consultas DESC
        ''')
        medicos_data = cursor.fetchall()
        
        conn.close()
        
        # Convertir a lista de diccionarios
        medicos = []
        for m in medicos_data:
            medicos.append({
                'nombre': m['nombre'],
                'consultas': m['total_consultas'] or 0
            })

        return render_template('admin-dashboard.html',
                             adminName=session['nombre'],
                             total_pacientes=total_pacientes,
                             consultas_mes=consultas_mes,
                             doctores=doctores,
                             medicos=medicos)
    
    except Exception as e:
        print(f"Error en admin_dashboard: {e}")
        flash('Error al cargar el dashboard', 'error')
        return redirect(url_for('login'))

@app.route('/admin/stats')
def admin_stats():
    """Obtiene estadísticas para el dashboard admin"""
    if 'user_id' not in session or session.get('rol') != 'admin':
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total pacientes
        cursor.execute('SELECT COUNT(*) as total FROM pacientes')
        total_pacientes = cursor.fetchone()['total']
        
        # Consultas este mes
        cursor.execute('''
            SELECT COUNT(*) as total FROM consultas 
            WHERE strftime('%Y-%m', fecha_consulta) = strftime('%Y-%m', 'now')
        ''')
        consultas_mes = cursor.fetchone()['total']
        
        # Doctores activos
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE rol = 'doctor' AND activo = 1")
        doctores = cursor.fetchone()['total']
        
        # Rendimiento de médicos
        cursor.execute('''
            SELECT u.nombre, COUNT(c.id) as total_consultas
            FROM usuarios u
            LEFT JOIN consultas c ON u.id = c.doctor_id
            WHERE u.rol = 'doctor' AND u.activo = 1
            GROUP BY u.id, u.nombre
            ORDER BY total_consultas DESC
        ''')
        medicos = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'pacientes': total_pacientes,
            'consultas_mes': consultas_mes,
            'doctores': doctores,
            'medicos': [{'nombre': m['nombre'], 'consultas': m['total_consultas']} for m in medicos]
        })
        
    except Exception as e:
        print(f"Error obteniendo stats: {e}")
        return jsonify({'error': 'Error del servidor'}), 500

# ==================== RUTAS DEL DOCTOR ====================

@app.route('/doctor/dashboard')
def doctor_dashboard():
    """Dashboard del doctor"""
    if 'user_id' not in session or session['rol'] != 'doctor':
        flash('Acceso denegado', 'error')
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener información del doctor actual
        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],))
        doctor = cursor.fetchone()
        
        # Mis consultas totales
        cursor.execute('SELECT COUNT(*) as count FROM consultas WHERE doctor_id = ?', 
                       (session['user_id'],))
        mis_consultas_result = cursor.fetchone()
        mis_consultas = mis_consultas_result['count'] if mis_consultas_result else 0
        
        # Mis pacientes
        cursor.execute('''
            SELECT COUNT(DISTINCT paciente_id) as count 
            FROM consultas 
            WHERE doctor_id = ?
        ''', (session['user_id'],))
        mis_pacientes_result = cursor.fetchone()
        mis_pacientes = mis_pacientes_result['count'] if mis_pacientes_result else 0
        
        # Consultas este mes
        cursor.execute('''
            SELECT COUNT(*) as count FROM consultas 
            WHERE doctor_id = ? 
            AND strftime('%Y-%m', fecha_consulta) = strftime('%Y-%m', 'now')
        ''', (session['user_id'],))
        consultas_mes_result = cursor.fetchone()
        consultas_mes = consultas_mes_result['count'] if consultas_mes_result else 0
        
        # Consultas recientes
        cursor.execute('''
            SELECT c.*, p.nombre as paciente_nombre
            FROM consultas c
            JOIN pacientes p ON c.paciente_id = p.id
            WHERE c.doctor_id = ?
            ORDER BY c.fecha_consulta DESC
            LIMIT 5
        ''', (session['user_id'],))
        consultas_recientes_data = cursor.fetchall()
        
        conn.close()
        
        # Convertir a lista de diccionarios
        consultas_recientes = []
        for c in consultas_recientes_data:
            consultas_recientes.append(dict(c))
        
        return render_template('ddoctor-dashboard.html',
                             doctor=doctor,
                             mis_consultas=mis_consultas,
                             mis_pacientes=mis_pacientes,
                             consultas_mes=consultas_mes,
                             consultas_recientes=consultas_recientes)
        
    except Exception as e:
        print(f"Error en doctor_dashboard: {e}")
        flash('Error al cargar el dashboard', 'error')
        return redirect(url_for('login'))

@app.route('/doctor/stats')
def doctor_stats():
    """Obtiene estadísticas del doctor"""
    if 'user_id' not in session or session.get('rol') != 'doctor':
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        doctor_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total consultas del doctor
        cursor.execute('SELECT COUNT(*) as total FROM consultas WHERE doctor_id = ?', (doctor_id,))
        total_consultas = cursor.fetchone()['total']
        
        # Pacientes únicos del doctor
        cursor.execute('''
            SELECT COUNT(DISTINCT paciente_id) as total 
            FROM consultas 
            WHERE doctor_id = ?
        ''', (doctor_id,))
        pacientes_unicos = cursor.fetchone()['total']
        
        # Consultas este mes
        cursor.execute('''
            SELECT COUNT(*) as total FROM consultas 
            WHERE doctor_id = ? 
            AND strftime('%Y-%m', fecha_consulta) = strftime('%Y-%m', 'now')
        ''', (doctor_id,))
        consultas_mes = cursor.fetchone()['total']
        
        # Consultas recientes
        cursor.execute('''
            SELECT c.*, p.nombre as paciente_nombre, p.especie
            FROM consultas c
            JOIN pacientes p ON c.paciente_id = p.id
            WHERE c.doctor_id = ?
            ORDER BY c.fecha_consulta DESC
            LIMIT 5
        ''', (doctor_id,))
        consultas_recientes = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'total_consultas': total_consultas,
            'pacientes': pacientes_unicos,
            'consultas_mes': consultas_mes,
            'consultas_recientes': [dict(c) for c in consultas_recientes]
        })
        
    except Exception as e:
        print(f"Error obteniendo stats doctor: {e}")
        return jsonify({'error': 'Error del servidor'}), 500

# ==================== RUTAS COMPARTIDAS ====================

@app.route('/register-patient')
def register_patient():
    """Página de registro de pacientes"""
    if 'user_id' not in session:
        flash('Debe iniciar sesión', 'error')
        return redirect(url_for('login'))
    
    # Determinar a qué dashboard regresar
    if session.get('rol') == 'admin':
        dashboard_url = url_for('admin_dashboard')
    else:
        dashboard_url = url_for('doctor_dashboard')
    
    return render_template('register-patient.html',
                         doctorName=session.get('nombre'),
                         dashboard_url=dashboard_url)

@app.route('/register-consultation')
def register_consultation():
    """Página de registro de consultas"""
    if 'user_id' not in session:
        flash('Debe iniciar sesión', 'error')
        return redirect(url_for('login'))
    
    # Obtener lista de pacientes
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if session.get('rol') == 'admin':
        cursor.execute('SELECT * FROM pacientes ORDER BY nombre')
    else:
        # Doctor solo ve sus pacientes
        cursor.execute('''
            SELECT DISTINCT p.* 
            FROM pacientes p
            JOIN consultas c ON p.id = c.paciente_id
            WHERE c.doctor_id = ?
            ORDER BY p.nombre
        ''', (session['user_id'],))
    
    pacientes = cursor.fetchall()
    conn.close()
    
    # Determinar a qué dashboard regresar
    if session.get('rol') == 'admin':
        dashboard_url = url_for('admin_dashboard')
    else:
        dashboard_url = url_for('doctor_dashboard')
    
    return render_template('register-consultation.html',
                         pacientes=pacientes,
                         doctorName=session.get('nombre'),
                         dashboard_url=dashboard_url)

@app.route('/historial-pacientes')
def historial_pacientes():
    """Página de historial de pacientes"""
    if 'user_id' not in session:
        flash('Debe iniciar sesión', 'error')
        return redirect(url_for('login'))
    
    rol = session.get('rol')
    
    # Determinar a qué dashboard regresar
    if rol == 'admin':
        dashboard_url = url_for('admin_dashboard')
    else:
        dashboard_url = url_for('doctor_dashboard')
    
    # Obtener datos según rol
    pacientes, historial, paciente_seleccionado = obtener_datos_historial(rol, session['user_id'])
    
    return render_template('historial-pacientes.html',
                         pacientes=pacientes,
                         historial=historial,
                         paciente_seleccionado=paciente_seleccionado,
                         rol=rol,
                         dashboard_url=dashboard_url)
   
def obtener_datos_historial(rol, user_id):
    """Obtiene datos del historial según el rol"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    paciente_id = request.args.get('paciente_id')
    pacientes = []
    historial = []
    paciente_seleccionado = None
    
    # Obtener pacientes
    if rol == 'admin':
        cursor.execute('SELECT * FROM pacientes ORDER BY nombre')
    else:
        cursor.execute('''
            SELECT DISTINCT p.* 
            FROM pacientes p
            JOIN consultas c ON p.id = c.paciente_id
            WHERE c.doctor_id = ?
            ORDER BY p.nombre
        ''', (user_id,))
    
    pacientes_data = cursor.fetchall()
    pacientes = [dict(p) for p in pacientes_data]
    
    # Obtener historial si hay paciente seleccionado
    if paciente_id:
        if rol == 'admin':
            cursor.execute('''
                SELECT h.*, u.nombre as doctor_nombre
                FROM historial_medico h
                LEFT JOIN usuarios u ON h.doctor_id = u.id
                WHERE h.paciente_id = ?
                ORDER BY h.fecha DESC
            ''', (paciente_id,))
        else:
            cursor.execute('''
                SELECT h.*, u.nombre as doctor_nombre
                FROM historial_medico h
                LEFT JOIN usuarios u ON h.doctor_id = u.id
                WHERE h.paciente_id = ? 
                AND (h.doctor_id = ? OR h.doctor_id IS NULL)
                ORDER BY h.fecha DESC
            ''', (paciente_id, user_id))
        
        historial_data = cursor.fetchall()
        historial = [dict(h) for h in historial_data]
        
        # Obtener paciente seleccionado
        cursor.execute('SELECT * FROM pacientes WHERE id = ?', (paciente_id,))
        paciente = cursor.fetchone()
        paciente_seleccionado = dict(paciente) if paciente else None
    
    conn.close()
    return pacientes, historial, paciente_seleccionado
@app.route('/system-maintenance')
def system_maintenance():
    """Página de mantenimiento del sistema"""
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('Acceso denegado. Solo administradores', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Total de pacientes
        cursor.execute('SELECT COUNT(*) as total FROM pacientes')
        total_pacientes = cursor.fetchone()['total']
        
        # 2. Pacientes inactivos (24+ meses sin consultas)
        cursor.execute('''
            SELECT p.*, MAX(c.fecha_consulta) as ultima_consulta,
                   julianday('now') - julianday(MAX(c.fecha_consulta)) as dias_inactivo
            FROM pacientes p
            LEFT JOIN consultas c ON p.id = c.paciente_id
            GROUP BY p.id
            HAVING ultima_consulta IS NULL 
                   OR (julianday('now') - julianday(ultima_consulta)) > 730
            ORDER BY dias_inactivo DESC
        ''')
        pacientes_inactivos_data = cursor.fetchall()
        
        # 3. Contar inactivos
        pacientes_inactivos = [dict(p) for p in pacientes_inactivos_data]
        inactivos_count = len(pacientes_inactivos)
        
        # 4. Obtener información de médicos para los registros
        cursor.execute("SELECT id, nombre FROM usuarios WHERE rol = 'doctor'")
        doctores = cursor.fetchall()
        doctores_dict = {d['id']: d['nombre'] for d in doctores}
        
        # 5. Para cada paciente inactivo, obtener info del médico que lo registró
        for paciente in pacientes_inactivos:
            # Buscar la última consulta para obtener el médico
            cursor.execute('''
                SELECT c.doctor_id, u.nombre as doctor_nombre
                FROM consultas c
                JOIN usuarios u ON c.doctor_id = u.id
                WHERE c.paciente_id = ?
                ORDER BY c.fecha_consulta DESC
                LIMIT 1
            ''', (paciente['id'],))
            ultima_consulta = cursor.fetchone()
            
            if ultima_consulta:
                paciente['doctor_id'] = ultima_consulta['doctor_id']
                paciente['doctor_nombre'] = ultima_consulta['doctor_nombre']
            else:
                paciente['doctor_id'] = None
                paciente['doctor_nombre'] = 'No registrado'
            
            # Calcular meses desde última consulta
            if paciente.get('ultima_consulta'):
                cursor.execute('''
                    SELECT ROUND((julianday('now') - julianday(?)) / 30.44, 1) as meses
                ''', (paciente['ultima_consulta'],))
                meses_result = cursor.fetchone()
                paciente['meses_inactivo'] = meses_result['meses'] if meses_result else 'N/A'
            else:
                paciente['meses_inactivo'] = 'N/A'
        
        conn.close()
        
        return render_template('system-maintenance.html',
                             total_pacientes=total_pacientes,
                             pacientes_inactivos=pacientes_inactivos,
                             inactivos_count=inactivos_count,
                             adminName=session['nombre'])
        
    except Exception as e:
        print(f"Error en system_maintenance: {e}")
        flash('Error al cargar la página de mantenimiento', 'error')
        return redirect(url_for('admin_dashboard'))

# ==================== API ENDPOINTS ====================

@app.route('/api/pacientes', methods=['GET'])
def get_pacientes():
    """Obtiene lista de pacientes"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pacientes ORDER BY nombre')
        pacientes = cursor.fetchall()
        conn.close()
        
        return jsonify([dict(p) for p in pacientes])
    except Exception as e:
        print(f"Error obteniendo pacientes: {e}")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/session')
def get_session():
    """Obtiene información de la sesión actual"""
    if 'user_id' not in session:
        return jsonify({'authenticated': False})
    
    return jsonify({
        'authenticated': True,
        'nombre': session.get('nombre'),
        'username': session.get('username'),
        'rol': session.get('rol')
    })

# ==================== API PARA MANTENIMIENTO ====================

@app.route('/api/archive-patients', methods=['POST'])
def archive_patients():
    """Archiva pacientes seleccionados"""
    if 'user_id' not in session or session.get('rol') != 'admin':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        data = request.get_json()
        patient_ids = data.get('patient_ids', [])
        
        if not patient_ids:
            return jsonify({'success': False, 'message': 'No hay pacientes seleccionados'}), 400
        
        # Aquí implementarías la lógica para archivar
        # Por ejemplo, mover a una tabla de pacientes_archivados
        # o marcar como inactivo
        
        return jsonify({
            'success': True, 
            'message': f'{len(patient_ids)} pacientes archivados',
            'archived': patient_ids
        })
        
    except Exception as e:
        print(f"Error archivando pacientes: {e}")
        return jsonify({'success': False, 'message': 'Error del servidor'}), 500

@app.route('/api/delete-patients', methods=['POST'])
def delete_patients():
    """Elimina pacientes seleccionados"""
    if 'user_id' not in session or session.get('rol') != 'admin':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        data = request.get_json()
        patient_ids = data.get('patient_ids', [])
        
        if not patient_ids:
            return jsonify({'success': False, 'message': 'No hay pacientes seleccionados'}), 400
        
        # Confirmación adicional para eliminación
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Primero eliminar historial médico
        cursor.executemany(
            'DELETE FROM historial_medico WHERE paciente_id = ?',
            [(pid,) for pid in patient_ids]
        )
        
        # 2. Eliminar consultas
        cursor.executemany(
            'DELETE FROM consultas WHERE paciente_id = ?',
            [(pid,) for pid in patient_ids]
        )
        
        # 3. Finalmente eliminar pacientes
        cursor.executemany(
            'DELETE FROM pacientes WHERE id = ?',
            [(pid,) for pid in patient_ids]
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'{len(patient_ids)} pacientes eliminados permanentemente',
            'deleted': patient_ids
        })
        
    except Exception as e:
        print(f"Error eliminando pacientes: {e}")
        return jsonify({'success': False, 'message': 'Error del servidor'}), 500

# ==================== API ADICIONALES ÚTILES ====================

@app.route('/api/patient/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Obtiene información de un paciente específico"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pacientes WHERE id = ?', (patient_id,))
        paciente = cursor.fetchone()
        conn.close()
        
        if not paciente:
            return jsonify({'error': 'Paciente no encontrado'}), 404
        
        return jsonify(dict(paciente))
    except Exception as e:
        print(f"Error obteniendo paciente: {e}")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/patient-history/<int:patient_id>', methods=['GET'])
def get_patient_history(patient_id):
    """Obtiene historial médico de un paciente"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT h.*, u.nombre as doctor_nombre
            FROM historial_medico h
            LEFT JOIN usuarios u ON h.doctor_id = u.id
            WHERE h.paciente_id = ?
            ORDER BY h.fecha DESC
        ''', (patient_id,))
        historial = cursor.fetchall()
        
        conn.close()
        
        return jsonify([dict(h) for h in historial])
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return jsonify({'error': 'Error del servidor'}), 500

# ==================== EJECUCIÓN ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)