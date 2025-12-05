document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("consultationForm");
    const patientSelect = document.getElementById("patientId");

    const speciesInfo = document.getElementById("infoSpecies");
    const breedInfo = document.getElementById("infoBreed");
    const ageInfo = document.getElementById("infoAge");
    const patientBox = document.getElementById("patientInfo");

    const successBox = document.getElementById("successBox");

    // Mostrar info del paciente al seleccionarlo
    patientSelect.addEventListener("change", () => {
        const option = patientSelect.selectedOptions[0];

        if (option.value === "") {
            patientBox.style.display = "none";
            return;
        }

        speciesInfo.textContent = option.dataset.species;
        breedInfo.textContent = option.dataset.breed;
        ageInfo.textContent = option.dataset.age;

        patientBox.style.display = "block";
    });


    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const data = {
            patientId: patientSelect.value,
            date: document.getElementById("date").value,
            diagnosis: document.getElementById("diagnosis").value,
            details: document.getElementById("details").value
        };

        if (!data.patientId || !data.date || !data.diagnosis || !data.details) {
            alert("Completa todos los campos");
            return;
        }

        let resp = await fetch("/register-consultation", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        let result = await resp.json();

        if (result.success) {
            successBox.style.display = "block";
            form.reset();
            patientBox.style.display = "none";

            setTimeout(() => {
                successBox.style.display = "none";
            }, 3000);
        } else {
            alert("Error guardando consulta");
        }
    });

});
