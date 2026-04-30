async function loadData() {
    const status = document.getElementById("status");
    const soilValue = document.getElementById("soil");
    const tempValue = document.getElementById("temp");
    const humValue = document.getElementById("hum");
    const soilInput = document.getElementById("soil_moisture");
    const tempInput = document.getElementById("temperature");
    const humInput = document.getElementById("humidity");

    try {
        const res = await fetch("/data");

        if (!res.ok) {
            window.location.href = "/";
            return;
        }

        const data = await res.json();
        const soil = data.V0 ?? "--";
        const temp = data.V1 ?? "--";
        const hum = data.V2 ?? "--";

        if (soilValue) {
            soilValue.innerText = soil;
        }

        if (tempValue) {
            tempValue.innerText = temp;
        }

        if (humValue) {
            humValue.innerText = hum;
        }

        if (soilInput && soil !== "--") {
            soilInput.value = soil;
        }

        if (tempInput && temp !== "--") {
            tempInput.value = temp;
        }

        if (humInput && hum !== "--") {
            humInput.value = hum;
        }

        if (status) {
            status.innerText = "Live data updated";
        }
    } catch (error) {
        if (status) {
            status.innerText = "Error fetching data from Blynk";
        }
    }
}

loadData();
setInterval(loadData, 3000);

function titleCase(value) {
    return value
        .replaceAll("_", " ")
        .replace(/\w\S*/g, (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());
}

function renderPrediction(result) {
    const status = document.getElementById("auto-prediction-status");
    const probability = document.getElementById("auto-prediction-probability");
    const note = document.getElementById("auto-prediction-note");
    const riskGrid = document.getElementById("auto-risk-grid");

    if (!status || !probability) {
        return;
    }

    status.innerText = result.prediction;
    status.classList.add("prediction-status");
    status.classList.toggle("status-needed", result.prediction === "IRRIGATION NEEDED");
    status.classList.toggle("status-not-needed", result.prediction !== "IRRIGATION NEEDED");
    probability.innerHTML = `Irrigation probability: <strong>${result.irrigation_probability}%</strong>`;

    if (note) {
        note.innerText = "Auto prediction updates every 10 minutes.";
    }

    if (riskGrid && result.risk_analysis) {
        riskGrid.innerHTML = Object.entries(result.risk_analysis)
            .map(([key, value]) => `<div><span>${titleCase(key)}</span><strong>${value}</strong></div>`)
            .join("");
    }
}

function renderPredictionError(message) {
    const status = document.getElementById("auto-prediction-status");
    const note = document.getElementById("auto-prediction-note");

    if (status) {
        status.innerText = "Prediction unavailable";
        status.classList.remove("status-needed", "status-not-needed");
    }

    if (note) {
        note.innerText = message;
    }
}

function getPredictionFormData() {
    const form = document.querySelector(".prediction-form");

    if (!form) {
        return null;
    }

    return Object.fromEntries(new FormData(form).entries());
}

async function runAutoPrediction() {
    const formData = getPredictionFormData();
    const endpoint = formData ? "/predict-json" : "/auto-predict";
    const options = formData
        ? {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        }
        : {};

    try {
        const res = await fetch(endpoint, options);

        if (!res.ok) {
            const errorData = await res.json();
            renderPredictionError(errorData.error || "Auto prediction failed");
            return;
        }

        const result = await res.json();
        renderPrediction(result);
    } catch (error) {
        renderPredictionError("Auto prediction failed");
    }
}

if (document.getElementById("auto-prediction-status")) {
    setTimeout(runAutoPrediction, 3000);
    setInterval(runAutoPrediction, 600000);
}

function checkIrrigationConditionGuide() {
    const soil = Number(document.getElementById("guide_soil")?.value);
    const temp = Number(document.getElementById("guide_temp")?.value);
    const humidity = Number(document.getElementById("guide_humidity")?.value);
    const status = document.getElementById("condition-guide-status");
    const list = document.getElementById("condition-guide-list");

    if (!status || !list) {
        return;
    }

    const reasons = [];
    let irrigationNeeded = false;

    if (soil < 40) {
        irrigationNeeded = true;
        reasons.push("Soil moisture is below 40%, so the soil is dry.");
    } else {
        reasons.push("Soil moisture is 40% or above, so soil water level is acceptable.");
    }

    if (temp > 32 && humidity < 50) {
        irrigationNeeded = true;
        reasons.push("Temperature is high and humidity is low, so plants can lose water faster.");
    }

    if (temp > 38) {
        irrigationNeeded = true;
        reasons.push("Temperature is very high, which increases irrigation demand.");
    }

    if (soil >= 40 && soil <= 70 && temp >= 20 && temp <= 30 && humidity >= 50 && humidity <= 70) {
        irrigationNeeded = false;
        reasons.push("Moisture, temperature, and humidity are in a comfortable range.");
    }

    status.innerText = irrigationNeeded ? "IRRIGATION MAY BE NEEDED" : "IRRIGATION MAY NOT BE NEEDED";
    status.classList.add("prediction-status");
    status.classList.toggle("status-needed", irrigationNeeded);
    status.classList.toggle("status-not-needed", !irrigationNeeded);
    list.innerHTML = reasons.map((reason) => `<li>${reason}</li>`).join("");
}

const conditionCheckButton = document.getElementById("condition-check-btn");

if (conditionCheckButton) {
    conditionCheckButton.addEventListener("click", checkIrrigationConditionGuide);
    checkIrrigationConditionGuide();
}
