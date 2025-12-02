// =======================
// CARGA INICIAL DEL PANEL
// =======================
document.addEventListener("DOMContentLoaded", () => {

    const doctorName = document.getElementById("doctorName");
    const myConsultations = document.getElementById("myConsultations");
    const myPatients = document.getElementById("myPatients");
    const myConsultationsMonth = document.getElementById("myConsultationsMonth");
    const recentList = document.getElementById("recentConsultations");

    // Datos temporales (luego se conectarán a Python + SQLite)
    const mockDoctor = {
        name: "Médico A",
        consultations: 18,
        patients: 7,
        monthConsultations: 6,
        recent: [
            { patient: "Flash", date: "2025-12-01" },
            { patient: "Rocky", date: "2025-11-28" },
            { patient: "Toby", date: "2025-11-22" }
        ]
    };

    // Rellenar texto
    doctorName.textContent = mockDoctor.name;
    myConsultations.textContent = mockDoctor.consultations;
    myPatients.textContent = mockDoctor.patients;
    myConsultationsMonth.textContent = mockDoctor.monthConsultations;

    // Consultas recientes
    recentList.innerHTML = "";

    if (mockDoctor.recent.length === 0) {
        recentList.innerHTML = `<p class="empty">No hay consultas registradas aún</p>`;
    } else {
        mockDoctor.recent.forEach(c => {
            const row = document.createElement("div");
            row.className = "recent-row";

            row.innerHTML = `
                <div>
                    <p class="patient">${c.patient}</p>
                    <p class="date">${c.date}</p>
                </div>
            `;

            recentList.appendChild(row);
        });
    }
});

// =======================
// BOTONES DE ACCIÓN
// =======================
document.addEventListener("click", e => {
    const btn = e.target.closest(".action-btn");
    if (!btn) return;

    const view = btn.getAttribute("data-view");

    // Navegación según acción elegida
    if (view === "register-consultation") {
        window.location.href = "register-consultation.html";
    }
    if (view === "register-patient") {
        window.location.href = "register-patient.html";
    }
    if (view === "patient-history") {
        window.location.href = "historial-pacientes.html";
    }
});

