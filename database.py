import sqlite3
from datetime import datetime, timedelta
import hashlib
import secrets

def init_db():
    """Inicializa la base de datos con todas las tablas necesarias"""
    conn = sqlite3.connect('clinic.db')
    cursor = conn.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('admin', 'doctor')),
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activo INTEGER DEFAULT 1
        )
    ''')
    print("✓ Tabla usuarios creada")
    
    # Tabla de pacientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
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
            notas TEXT
        )
    ''')
    print("✓ Tabla pacientes creada")
    
    # Tabla de consultas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultas (
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
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
            FOREIGN KEY (doctor_id) REFERENCES usuarios (id)
        )
    ''')
    print("✓ Tabla consultas creada")
    
    # Tabla de historial médico
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_medico (
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
    print("✓ Tabla historial_medico creada")
    
    # Tabla de mantenimiento
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mantenimiento_sistema (
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
    print("✓ Tabla mantenimiento_sistema creada")
    
    # ==================== DATOS DE PRUEBA ====================
    
    # Insertar usuarios de prueba (CONTRASEÑAS ENCRIPTADAS)
    usuarios_ejemplo = [
        ('admin', hash_password('Admin123!'), 'Dr. Juan Pérez', 'admin@vetclinic.com', 'admin'),
        ('dra.lopez', hash_password('DraLopez456!'), 'Dra. María López', 'mlopez@vetclinic.com', 'doctor'),
        ('dr.gomez', hash_password('DrGomez789!'), 'Dr. Carlos Gómez', 'cgomez@vetclinic.com', 'doctor'),
        ('dr.rodriguez', hash_password('DrRodriguez123!'), 'Dr. Luis Rodríguez', 'lrodriguez@vetclinic.com', 'doctor')
    ]
    
    for usuario in usuarios_ejemplo:
        try:
            cursor.execute(
                '''INSERT OR IGNORE INTO usuarios 
                (username, password, nombre, email, rol) 
                VALUES (?, ?, ?, ?, ?)''',
                usuario
            )
        except Exception as e:
            print(f"Error insertando usuario {usuario[0]}: {e}")
    print("✓ Usuarios de prueba insertados")
    
    # Insertar pacientes de prueba
    pacientes_ejemplo = [
        ('Max', 'Perro', 'Labrador Retriever', 5, 28.5, 'Dorado', 'M', 
         'Ana García', '555-1234', 'ana.garcia@email.com', 'Calle Primavera 123, Ciudad', 
         'Muy juguetón, alergia a algunos alimentos'),
        
        ('Luna', 'Gato', 'Siamés', 3, 4.2, 'Blanco con gris', 'F',
         'Carlos Martínez', '555-5678', 'carlos.m@email.com', 'Av. Central 456, Ciudad',
         'Tímida pero cariñosa, requiere comida especial'),
        
        ('Rocky', 'Perro', 'Bulldog Francés', 2, 12.8, 'Atigrado', 'M',
         'Laura Sánchez', '555-9012', 'laura.s@email.com', 'Calle Luna 789, Ciudad',
         'Problemas respiratorios leves'),
        
        ('Mimi', 'Gato', 'Persa', 7, 5.5, 'Blanco', 'F',
         'Roberto Díaz', '555-3456', 'roberto.d@email.com', 'Calle Sol 321, Ciudad',
         'Edad avanzada, control de articulaciones'),
        
        ('Toby', 'Perro', 'Golden Retriever', 4, 32.0, 'Dorado', 'M',
         'Sofía Ramírez', '555-7890', 'sofia.r@email.com', 'Av. Norte 654, Ciudad',
         'Activo, necesita ejercicio diario')
    ]
    
    for paciente in pacientes_ejemplo:
        try:
            cursor.execute(
                '''INSERT OR IGNORE INTO pacientes 
                (nombre, especie, raza, edad, peso, color, sexo, nombre_dueno, 
                 telefono_dueno, email_dueno, direccion_dueno, notas) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                paciente
            )
        except Exception as e:
            print(f"Error insertando paciente {paciente[0]}: {e}")
    print("✓ Pacientes de prueba insertados")
    
    # Insertar consultas de prueba
    consultas_ejemplo = [
        (1, 2, '2024-01-15 10:00:00', 'Vacunación anual', 
         'Saludable, peso ideal', 'Vacuna múltiple y desparasitación', 
         'Vacuna: DHPP, Antiparasitario: Prazitel', '2024-01-22 11:00:00', 
         'completada', 850.50),
        
        (2, 2, '2024-01-16 14:30:00', 'Pérdida de apetito', 
         'Problema dental, gingivitis leve', 'Limpieza dental y antibióticos', 
         'Clindamicina 50mg cada 12h por 7 días', '2024-01-23 15:00:00', 
         'completada', 1200.00),
        
        (3, 3, '2024-01-17 09:00:00', 'Control respiratorio', 
         'Estable, mantener monitoreo', 'Continuar con ejercicio moderado', 
         'Ninguno por ahora', '2024-02-17 09:00:00', 'pendiente', 650.00),
        
        (1, 3, '2024-01-18 11:00:00', 'Revisión post-vacuna', 
         'Reacción normal a vacuna', 'Observar por 48 horas', 
         'Antihistamínico si hay inflamación', None, 'completada', 300.00),
        
        (4, 4, '2024-01-19 16:00:00', 'Dolor articular', 
         'Artritis leve por edad', 'Fisioterapia y suplementos', 
         'Condroitín sulfato 500mg diarios', '2024-02-19 16:00:00', 
         'pendiente', 950.00)
    ]
    
    for consulta in consultas_ejemplo:
        try:
            cursor.execute(
                '''INSERT OR IGNORE INTO consultas 
                (paciente_id, doctor_id, fecha_consulta, motivo, diagnostico, 
                 tratamiento, medicamentos, proxima_cita, estado, costo) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                consulta
            )
        except Exception as e:
            print(f"Error insertando consulta: {e}")
    print("✓ Consultas de prueba insertadas")
    
    # Insertar historial médico de prueba
    historial_ejemplo = [
        (1, 1, '2024-01-15 10:00:00', 'vacuna', 
         'Vacunación anual completa', 2, None),
        
        (2, 2, '2024-01-16 14:30:00', 'consulta', 
         'Diagnóstico y tratamiento para gingivitis', 2, 'radiografia_dental.pdf'),
        
        (3, 3, '2024-01-17 09:00:00', 'consulta', 
         'Control rutinario de problemas respiratorios', 3, None),
        
        (1, 4, '2024-01-18 11:00:00', 'consulta', 
         'Revisión post-vacunación sin complicaciones', 3, None),
        
        (4, 5, '2024-01-19 16:00:00', 'consulta', 
         'Evaluación de dolor articular, diagnóstico de artritis', 4, 'rayos_x_articulaciones.pdf'),
        
        (5, None, '2023-12-10 10:00:00', 'vacuna', 
         'Primera vacunación cachorro', 2, 'cartilla_vacunacion.pdf'),
        
        (2, None, '2023-11-15 09:00:00', 'analisis', 
         'Análisis de sangre rutinario - resultados normales', 2, 'analisis_sangre.pdf')
    ]
    
    for historial in historial_ejemplo:
        try:
            cursor.execute(
                '''INSERT OR IGNORE INTO historial_medico 
                (paciente_id, consulta_id, fecha, tipo, descripcion, doctor_id, archivo_adjunto) 
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                historial
            )
        except Exception as e:
            print(f"Error insertando historial médico: {e}")
    print("✓ Historial médico de prueba insertado")
    
    # Insertar registros de mantenimiento de prueba
    mantenimiento_ejemplo = [
        ('Actualización de seguridad', 'Parche de seguridad para vulnerabilidades identificadas', 
         'actualizacion', '2024-01-10 09:00:00', 1, 'completado'),
        
        ('Backup de fin de mes', 'Backup completo de base de datos y archivos', 
         'backup', '2024-01-20 20:00:00', 1, 'pendiente'),
        
        ('Error en reportes', 'Los reportes de consultas no generan PDF correctamente', 
         'error', '2024-01-18 11:30:00', 2, 'en_proceso'),
        
        ('Mantenimiento servidor', 'Reinicio programado del servidor de aplicaciones', 
         'mantenimiento', '2024-01-25 03:00:00', 1, 'pendiente'),
        
        ('Actualización de software', 'Actualización a versión 2.1 del sistema', 
         'actualizacion', '2024-01-05 14:00:00', 1, 'completado')
    ]
    
    for mantenimiento in mantenimiento_ejemplo:
        try:
            cursor.execute(
                '''INSERT OR IGNORE INTO mantenimiento_sistema 
                (titulo, descripcion, tipo, fecha, realizado_por, estado) 
                VALUES (?, ?, ?, ?, ?, ?)''',
                mantenimiento
            )
        except Exception as e:
            print(f"Error insertando registro de mantenimiento: {e}")
    print("✓ Registros de mantenimiento insertados")
    
    conn.commit()
    conn.close()
    print("\n✅ Base de datos inicializada exitosamente con datos de prueba!")

def get_db_connection():
    """Crea y retorna una conexión a la base de datos"""
    conn = sqlite3.connect('clinic.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Convierte la contraseña en hash seguro"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{password_hash.hex()}"

def verify_password(password, stored_hash):
    """Verifica si la contraseña coincide con el hash almacenado"""
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

# ==================== FUNCIONES AUXILIARES ====================

def log_evento_seguridad(tipo_evento, usuario=None, ip=None, detalles=None):
    """Registra un evento de seguridad en la base de datos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO logs_seguridad (tipo_evento, usuario, ip, detalles) 
        VALUES (?, ?, ?, ?)''',
        (tipo_evento, usuario, ip, detalles)
    )
    conn.commit()
    conn.close()

def obtener_usuario_por_username(username):
    """Obtiene un usuario por su nombre de usuario"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def registrar_nueva_consulta(paciente_id, doctor_id, fecha_consulta, motivo, 
                            diagnostico=None, tratamiento=None, medicamentos=None, 
                            proxima_cita=None, costo=0.0):
    """Registra una nueva consulta en el sistema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO consultas 
        (paciente_id, doctor_id, fecha_consulta, motivo, diagnostico, 
         tratamiento, medicamentos, proxima_cita, costo) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (paciente_id, doctor_id, fecha_consulta, motivo, diagnostico, 
         tratamiento, medicamentos, proxima_cita, costo)
    )
    consulta_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return consulta_id

def obtener_pacientes():
    """Obtiene todos los pacientes registrados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM pacientes ORDER BY nombre')
    pacientes = cursor.fetchall()
    conn.close()
    return pacientes

def obtener_consultas_pendientes():
    """Obtiene todas las consultas pendientes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT c.*, p.nombre as paciente_nombre, u.nombre as doctor_nombre
                    FROM consultas c
                    JOIN pacientes p ON c.paciente_id = p.id
                    JOIN usuarios u ON c.doctor_id = u.id
                    WHERE c.estado = 'pendiente'
                    ORDER BY c.fecha_consulta''')
    consultas = cursor.fetchall()
    conn.close()
    return consultas

# ==================== EJECUCIÓN INICIAL ====================

if __name__ == "__main__":
    # Inicializar la base de datos al ejecutar el script
    print("Inicializando base de datos de veterinaria...")
    init_db()
    
    # Verificar que todo se creó correctamente
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Contar registros en cada tabla
    tablas = ['usuarios', 'pacientes', 'consultas', 'historial_medico', 'mantenimiento_sistema']
    for tabla in tablas:
        cursor.execute(f'SELECT COUNT(*) as total FROM {tabla}')
        total = cursor.fetchone()['total']
        print(f"📊 {tabla}: {total} registros")
    
    conn.close()
    print("\n🎉 Sistema listo para usar!")