(() => {
  const searchRoot = document.querySelector(".patient-select-field");
  if (!searchRoot) return;

  const searchInput = searchRoot.querySelector("#patient-search");
  const results = searchRoot.querySelector("#patient-search-results");
  const selected = searchRoot.querySelector("#selected-patient");
  const selectedName = selected.querySelector("span");
  const hiddenPatient = searchRoot.querySelector("#id_paciente");
  const status = searchRoot.querySelector("#patient-search-status");
  const submitButton = document.querySelector(".archive-intake-form button[type='submit']");
  const changeButton = selected.querySelector(".patient-change-button");
  const searchUrl = searchRoot.dataset.patientSearchUrl;
  let debounceTimer;
  let latestRequest = 0;

  const setSelection = (patient) => {
    hiddenPatient.value = patient ? patient.id : "";
    selectedName.textContent = patient
      ? `${patient.nombre} · DNI ${patient.documento || "No registrado"}`
      : "";
    selected.hidden = !patient;
    searchInput.hidden = Boolean(patient);
    results.replaceChildren();
    status.textContent = "";
    submitButton.disabled = !patient;
  };

  const showResults = (patients) => {
    results.replaceChildren();
    if (!patients.length) {
      status.textContent = "No encontramos pacientes pendientes de expediente.";
      return;
    }

    patients.forEach((patient) => {
      const option = document.createElement("button");
      const main = document.createElement("strong");
      const details = document.createElement("small");
      option.type = "button";
      option.className = "patient-search-option";
      option.setAttribute("role", "option");
      main.textContent = patient.nombre;
      details.textContent = [
        patient.documento ? `DNI ${patient.documento}` : "",
        patient.historia_clinica ? `HC ${patient.historia_clinica}` : "",
      ].filter(Boolean).join(" · ");
      option.append(main, details);
      option.addEventListener("click", () => setSelection(patient));
      results.append(option);
    });
  };

  searchInput.addEventListener("input", () => {
    window.clearTimeout(debounceTimer);
    results.replaceChildren();
    const consulta = searchInput.value.trim();
    const requestId = ++latestRequest;
    if (consulta.length < 2) {
      status.textContent = "Escribí al menos 2 caracteres para buscar.";
      return;
    }

    status.textContent = "Buscando pacientes…";
    debounceTimer = window.setTimeout(async () => {
      try {
        const url = new URL(searchUrl, window.location.origin);
        url.searchParams.set("q", consulta);
        const response = await fetch(url, {
          headers: { Accept: "application/json" },
          credentials: "same-origin",
        });
        if (!response.ok) throw new Error("No se pudo completar la búsqueda.");
        const data = await response.json();
        if (requestId !== latestRequest) return;
        showResults(data.resultados);
      } catch {
        if (requestId === latestRequest) {
          status.textContent = "No se pudo buscar. Revisá tu conexión e intentá nuevamente.";
        }
      }
    }, 250);
  });

  changeButton.addEventListener("click", () => {
    setSelection(null);
    searchInput.value = "";
    searchInput.focus();
  });

  setSelection(selected.dataset.selected === "true" ? {
    id: selected.dataset.patientId,
    nombre: selected.dataset.patientName,
    documento: selected.dataset.patientDocument,
  } : null);
})();
