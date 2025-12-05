// static/js/ddoctor-dashboard.js
document.addEventListener('DOMContentLoaded', async function() {
    
    // Cargar información de sesión
    try {
        const sessionResponse = await fetch('/api/session');
        const sessionData = await sessionResponse.json();
        
        if (sessionData.authenticated) {
            document.getElementById('doctorName').textContent = sessionData.nombre;
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error cargando sesión:', error);
    }
    
    // Cargar estadísticas del doctor
    try {
        const statsResponse = await fetch('/doctor/stats');
        const stats = await statsResponse.json();
        
        // Actualizar valores
        document.getElementById('myConsultations').textContent = stats.total_consultas;
        document.getElementById('myPatients').textContent = stats.pacientes;
        document.getElementById('myConsultationsMonth').textContent = stats.consultas_mes;
        
        // Actualizar consultas recientes
        const recentList = document.getElementById('recentConsultations');
        recentList.innerHTML = '';
        
        if (stats.consultas_recientes && stats.consultas_recientes.length > 0) {
            stats.consultas_recientes.forEach(consulta => {
                const item = document.createElement('div');
                item.className = 'recent-item';
                
                const fecha = new Date(consulta.fecha_consulta);
                const fechaStr = fecha.toLocaleDateString('es-ES');
                
                item.innerHTML = `
                    <div>
                        <p style="font-weight: 600; color: #1e293b;">${consulta.paciente_nombre}</p>
                        <p style="font-size: 0.875rem; color: #64748b;">${consulta.especie} - ${consulta.motivo}</p>
                        <p style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">${fechaStr}</p>
                    </div>
                    <span style="padding: 4px 12px; background: ${
                        consulta.estado === 'completada' ? '#dcfce7' : 
                        consulta.estado === 'pendiente' ? '#fef3c7' : '#fee2e2'
                    }; color: ${
                        consulta.estado === 'completada' ? '#166534' : 
                        consulta.estado === 'pendiente' ? '#854d0e' : '#991b1b'
                    }; border-radius: 9999px; font-size: 0.75rem; font-weight: 500;">
                        ${consulta.estado}
                    </span>
                `;
                
                recentList.appendChild(item);
            });
        } else {
            recentList.innerHTML = '<p class="empty">No hay consultas registradas aún</p>';
        }
        
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
    
    // Botones de acción
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const view = this.getAttribute('data-view');
            
            switch(view) {
                case 'register-consultation':
                    window.location.href = '/register-consultation';
                    break;
                case 'register-patient':
                    window.location.href = '/register-patient';
                    break;
                case 'patient-history':
                    window.location.href = '/historial-pacientes';
                    break;
            }
        });
    });
});