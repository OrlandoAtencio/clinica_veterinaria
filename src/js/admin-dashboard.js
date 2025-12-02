// =====================
// CERRAR SESIÓN
// =====================
document.getElementById("logoutBtn").addEventListener("click", () => {
    window.location.href = "../pages/llogin.html"; 
});

// =====================
// CARGA DE ESTADÍSTICAS
// =====================
function loadDashboardStats() {

    // Simulación de datos — luego conectaremos SQLite vía backend Python
    document.getElementById("activePatients").textContent = 12;
    document.getElementById("consultationsMonth").textContent = 34;
    document.getElementById("doctorsCount").textContent = 3;

    // Lista de médicos (temporal)
    const doctors = [
        { name: "Dr. Carlos", consultations: 14 },
        { name: "Dr. Allen", consultations: 9 },
        { name: "Dra. Mariam", consultations: 22 }
    ];

    const list = document.getElementById("doctorList");
    list.innerHTML = "";

    doctors.forEach(doc => {
        const row = document.createElement("div");
        row.className = "doctor-row";

        row.innerHTML = `
            <div class="doctor-info">
                <div class="doctor-icon">👨‍⚕️</div>
                <div>
                    <p class="doctor-name">${doc.name}</p>
                    <p class="doctor-role">Personal médico</p>
                </div>
            </div>
            <div class="doctor-stats">
                <p class="doctor-number">${doc.consultations}</p>
                <p class="doctor-label">consultas</p>
            </div>
        `;

        list.appendChild(row);
    });
}

// Ejecutar al cargar página
document.addEventListener("DOMContentLoaded", loadDashboardStats);
