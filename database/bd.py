import sqlite3

# Conectar o crear la base de datos SQLite
conn = sqlite3.connect('clinica_vet.sqlite')
cursor = conn.cursor()

# Desactivar temporalmente las llaves foráneas
cursor.execute("PRAGMA foreign_keys = OFF;")

# Crear tablas
cursor.executescript("""
BEGIN TRANSACTION;

-- Tabla consultas
CREATE TABLE IF NOT EXISTS consultas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  paciente_id INTEGER NOT NULL,
  fecha DATE NOT NULL,
  motivo TEXT NOT NULL,
  diagnostico TEXT,
  tratamiento TEXT,
  creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO consultas (id, paciente_id, fecha, motivo, diagnostico, tratamiento, creado_en) VALUES
(1, 23, '2025-12-11', 'enfermo', 'falta de apetito', 'comer proteinas', '2025-12-01 22:06:47');

-- Tabla consultations
CREATE TABLE IF NOT EXISTS consultations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id INTEGER NOT NULL,
  date DATE NOT NULL,
  diagnosis TEXT NOT NULL,
  details TEXT NOT NULL,
  doctor_id INTEGER NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(patient_id) REFERENCES patients(id),
  FOREIGN KEY(doctor_id) REFERENCES users(id)
);

-- Tabla pacientes
CREATE TABLE IF NOT EXISTS pacientes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  especie TEXT NOT NULL,
  raza TEXT,
  edad INTEGER,
  dueño TEXT NOT NULL,
  telefono TEXT,
  creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
  archivado INTEGER DEFAULT 0
);

INSERT INTO pacientes (id, nombre, especie, raza, edad, dueño, telefono, creado_en, archivado) VALUES
(1, 'Flash', 'Perro', 'Pitbull', 2, 'Mizael', '6505-2960', '2025-12-01 22:10:02', 0);

-- Tabla patients
CREATE TABLE IF NOT EXISTS patients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_name TEXT NOT NULL,
  patient_name TEXT NOT NULL,
  species TEXT NOT NULL,
  breed TEXT NOT NULL,
  age INTEGER NOT NULL,
  created_by INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(created_by) REFERENCES users(id)
);

-- Tabla users
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  correo TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  password_hash TEXT,
  rol TEXT DEFAULT 'veterinario',
  creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (id, nombre, correo, password, rol, creado_en) VALUES
(1, 'Administrador', 'admin@vetcare.com', '123456', 'admin', '2025-12-01 21:21:59');

COMMIT;
""")

# Activar llaves foráneas
cursor.execute("PRAGMA foreign_keys = ON;")

# Cerrar conexión
conn.commit()
conn.close()

print("Base de datos SQLite 'clinica_vet.sqlite' creada con éxito.")
