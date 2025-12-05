// static/js/admin-dashboard.js
document.addEventListener('DOMContentLoaded', async function() {
    
    // Cargar información de sesión
    try {
        const sessionResponse = await fetch('/api/session');
        const sessionData = await sessionResponse.json();
        
        if (sessionData.authenticated) {
            document.getElementById('adminName').textContent = sessionData.nombre;
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error cargando sesión:', error);
    }
    
    // Cargar estadísticas
    try {
        const statsResponse = await fetch('/admin/stats');
        const stats = await statsResponse.json();
        
        // Actualizar valores en el dashboard
        document.getElementById('activePatients').textContent = stats.pacientes;
        document.getElementById('consultationsMonth').textContent = stats.consultas_mes;
        document.getElementById('doctorsCount').textContent = stats.doctores;
        
        // Actualizar lista de médicos
        const doctorList = document.getElementById('doctorList');
        doctorList.innerHTML = ''; // Limpiar ejemplo
        
        if (stats.medicos && stats.medicos.length > 0) {
            stats.medicos.forEach(medico => {
                const row = document.createElement('div');
                row.className = 'doctor-row';
                
                row.innerHTML = `
                    <div class="doctor-info">
                        <div class="doctor-icon">👨‍⚕️</div>
                        <div>
                            <p class="doctor-name">${medico.nombre}</p>
                            <p class="doctor-role">Personal médico</p>
                        </div>
                    </div>
                    <div class="doctor-stats">
                        <p class="doctor-number">${medico.consultas}</p>
                        <p class="doctor-label">consultas</p>
                    </div>
                `;
                
                doctorList.appendChild(row);
            });
        }
        
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
    
    // Botón de logout
    document.getElementById('logoutBtn').addEventListener('click', function() {
        if (confirm('¿Está seguro que desea cerrar sesión?')) {
            window.location.href = '/logout';
        }
    });
});