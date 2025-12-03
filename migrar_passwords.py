# migrar_passwords.py
import sqlite3
import hashlib
import secrets
import os
from datetime import datetime

def crear_backup():
    """Crea un backup de la base de datos antes de la migración"""
    if os.path.exists('clinic.db'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_clinic_{timestamp}.db'
        import shutil
        shutil.copy2('clinic.db', backup_name)
        print(f"📦 Backup creado: {backup_name}")
        return True
    return False

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

def verificar_contraseña_hash(contrasena):
    """Verifica si una contraseña ya está en formato hash"""
    # Un hash PBKDF2 con salt típicamente tiene: salt:hash
    # donde salt es hexadecimal (32 chars) + ':' + hash (64 chars)
    if contrasena and ':' in contrasena:
        parts = contrasena.split(':')
        if len(parts) == 2:
            salt, hash_part = parts
            # Verificar longitudes típicas
            if len(salt) == 32 and len(hash_part) == 64:
                return True
    return False

def migrar_contraseñas():
    """Migra contraseñas existentes a formato hash"""
    print("🔍 Iniciando migración de contraseñas...")
    
    # Crear backup primero
    if not crear_backup():
        print("❌ No se encontró la base de datos clinic.db")
        print("💡 Ejecuta primero: python app.py para crear la base de datos")
        return
    
    conn = sqlite3.connect('clinic.db')
    cursor = conn.cursor()
    
    # Contar usuarios
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    total_usuarios = cursor.fetchone()[0]
    print(f"👥 Total de usuarios en sistema: {total_usuarios}")
    
    # Verificar cuántos necesitan migración
    cursor.execute('SELECT id, username, password FROM usuarios')
    usuarios = cursor.fetchall()
    
    usuarios_migrados = 0
    usuarios_ya_hash = 0
    
    for usuario_id, username, contrasena in usuarios:
        if not contrasena:
            print(f"⚠️  Usuario {username} no tiene contraseña")
            continue
            
        if verificar_contraseña_hash(contrasena):
            usuarios_ya_hash += 1
            continue
        
        # Migrar a hash
        try:
            password_hash = hash_password(contrasena)
            cursor.execute(
                'UPDATE usuarios SET password = ? WHERE id = ?',
                (password_hash, usuario_id)
            )
            usuarios_migrados += 1
            print(f"  ✅ {username}: Migrado a hash")
        except Exception as e:
            print(f"  ❌ {username}: Error en migración - {e}")
    
    if usuarios_migrados > 0:
        conn.commit()
        print(f"\n📊 RESUMEN DE MIGRACIÓN:")
        print(f"   • Total usuarios: {total_usuarios}")
        print(f"   • Ya en hash: {usuarios_ya_hash}")
        print(f"   • Migrados ahora: {usuarios_migrados}")
        print(f"   • Sin contraseña: {total_usuarios - usuarios_ya_hash - usuarios_migrados}")
        print("\n🎉 Migración completada exitosamente!")
    else:
        print("\n✅ Todas las contraseñas ya están en formato hash")
        print(f"   ({usuarios_ya_hash} usuarios verificados)")
    
    conn.close()
    
    # Mostrar contraseñas de ejemplo para testing
    print("\n🔐 Contraseñas de prueba (para login):")
    print("   admin / Admin123!")
    print("   dra.lopez / DraLopez456!")
    print("   dr.gomez / DrGomez789!")

if __name__ == '__main__':
    migrar_contraseñas()