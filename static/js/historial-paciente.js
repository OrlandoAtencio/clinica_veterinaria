document.addEventListener("DOMContentLoaded", () => {

    const listaPacientesDiv = document.getElementById("listaPacientes");
    const historialDiv = document.getElementById("historialPaciente");
    const buscador = document.querySelector(".search-box input");

    let pacientesGlobal = []; // almacenamos los pacientes

    // ===== 1) Obtener lista de pacientes desde Flask =====
    fetch("/api/pacientes")
        .then(res => res.json())
        .then(data => {
            pacientesGlobal = data;
            mostrarPacientes(data);
        })
        .catch(err => console.error("Error cargando pacientes", err));

    // ===== Mostrar lista =====
    function mostrarPacientes(lista) {
        listaPacientesDiv.innerHTML = "";

        if (lista.length === 0) {
            listaPacientesDiv.innerHTML = "<p>No hay pacientes encontrados</p>";
            return;
        }

        lista.forEach(p => {
            const div = document.createElement("div");
            div.classList.add("patient-item");
            div.innerHTML = `
                <h4>${p.nombre}</h4>
                <p>${p.especie} – ${p.raza || "Sin raza"}</p>
                <p><strong>Dueño:</strong> ${p.dueno}</p>
            `;
            div.addEventListener("click", () => cargarHistorial(p.id));
            listaPacientesDiv.appendChild(div);
        });
    }

    // ===== 2) Búsqueda =====
    buscador.addEventListener("keyup", () => {
        const text = buscador.value.toLowerCase();
        const filtrados = pacientesGlobal.filter(p =>
            p.nombre.toLowerCase().includes(text) ||
            p.dueno.toLowerCase().includes(text)
        );
        mostrarPacientes(filtrados);
    });

    // ===== 3) Obtener historial del paciente =====
    function cargarHistorial(id) {

        historialDiv.innerHTML = "<p>Cargando...</p>";

        fetch(`/api/patient-history/${id}`)
            .then(res => res.json())
            .then(historial => {
                if (!historial.length) {
                    historialDiv.innerHTML = `
                        <div class="empty">
                            <p>El paciente no tiene historial registrado.</p>
                        </div>
                    `;
                    return;
                }

                historialDiv.innerHTML = "";
                historial.forEach(item => {
                    const div = document.createElement("div");
                    div.classList.add("hist-item");
                    div.innerHTML = `
                        <p><strong>Fecha:</strong> ${item.fecha}</p>
                        <p><strong>Doctor:</strong> ${item.doctor_nombre || "No registrado"}</p>
                        <p><strong>Motivo:</strong> ${item.motivo}</p>
                        <hr>
                    `;
                    historialDiv.appendChild(div);
                });
            })
            .catch(err => {
                historialDiv.innerHTML = "<p>Error cargando historial.</p>";
                console.error(err);
            });

    }

});
