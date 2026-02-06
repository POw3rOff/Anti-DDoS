
const API_URL = "http://localhost:8000/api";

// Elements
const elConnection = document.getElementById("connection-status");
const elMode = document.getElementById("mode-display");
const elGrs = document.getElementById("grs-display");
const elStatusPanel = document.getElementById("status-panel");
const elCampaigns = document.getElementById("campaign-list");
const btnPanic = document.getElementById("panic-btn");

// Initialization
async function init() {
    console.log("Initializing Dashboard...");
    setInterval(pollStatus, 1000);
    initChart();
}

async function pollStatus() {
    try {
        const response = await fetch(`${API_URL}/status`);
        const data = await response.json();

        if (data.status === "online") {
            elConnection.textContent = "SYSTEM ONLINE";
            elConnection.classList.add("online");
            updateUI(data);
        } else {
            setOffline();
        }
    } catch (e) {
        setOffline();
    }
}

function setOffline() {
    elConnection.textContent = "DISCONNECTED";
    elConnection.classList.remove("online");
}

function updateUI(data) {
    // Mode
    elMode.textContent = data.mode || "UNKNOWN";
    elMode.className = `big-stat mode-${data.mode.toLowerCase()}`;

    // GRS
    elGrs.textContent = data.grs_score || 0;

    // Campaigns
    elCampaigns.innerHTML = "";
    if (data.campaigns && data.campaigns.length > 0) {
        data.campaigns.forEach(camp => {
            const li = document.createElement("li");
            li.textContent = `[${camp.type}] ${camp.name} (Conf: ${camp.confidence})`;
            li.style.color = "orange";
            elCampaigns.appendChild(li);
        });
    } else {
        elCampaigns.innerHTML = "<li>No active threats detected. System secure.</li>";
    }
}

// Chart Logic (Mock data for now, would connect to Prometheus/Metrics later)
let chart;
function initChart() {
    const ctx = document.getElementById('trafficChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(20).fill(''),
            datasets: [{
                label: 'Total Traffic (PPS)',
                data: Array(20).fill(0),
                borderColor: '#00ff41',
                tension: 0.4,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: '#333' } },
                x: { display: false }
            },
            plugins: { legend: { display: false } }
        }
    });

    // Update Mock Chart
    setInterval(() => {
        const data = chart.data.datasets[0].data;
        const labels = chart.data.labels;

        // Push random data (Simulating live PPS)
        data.push(Math.floor(Math.random() * 500) + 100);
        data.shift();

        chart.update();
    }, 1000);
}

// Panic Button
btnPanic.addEventListener("click", async () => {
    if (confirm("ARE YOU SURE? This will lock the system in ESCALATED mode.")) {
        try {
            const res = await fetch(`${API_URL}/panic`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ confirm: true })
            });
            if (res.ok) alert("PANIC MODE ACTIVATED");
        } catch (e) {
            alert("Failed to send panic signal");
        }
    }
});

// Elements
const modalConfig = document.getElementById("config-modal");
const btnSettings = document.getElementById("settings-btn");
const btnCloseModal = document.querySelector(".close-modal");
const btnSaveConfig = document.getElementById("save-config-btn");
const txtConfigEditor = document.getElementById("config-editor");

// Config Modal Logic
btnSettings.addEventListener("click", async () => {
    modalConfig.classList.add("active");
    await loadConfig();
});

btnCloseModal.addEventListener("click", () => {
    modalConfig.classList.remove("active");
});

window.addEventListener("click", (e) => {
    if (e.target == modalConfig) {
        modalConfig.classList.remove("active");
    }
});

async function loadConfig() {
    try {
        txtConfigEditor.value = "Loading...";
        const res = await fetch(`${API_URL}/config/thresholds`);
        const data = await res.json();
        // Convert JSON to YAML string for editing (simple dumping)
        // Using js-yaml if available, else JSON
        if (window.jsyaml) {
            txtConfigEditor.value = jsyaml.dump(data);
        } else {
            txtConfigEditor.value = JSON.stringify(data, null, 2);
        }
    } catch (e) {
        txtConfigEditor.value = "Error loading config: " + e;
    }
}

btnSaveConfig.addEventListener("click", async () => {
    try {
        const raw = txtConfigEditor.value;
        let configObj;

        if (window.jsyaml) {
            configObj = jsyaml.load(raw);
        } else {
            configObj = JSON.parse(raw);
        }

        const res = await fetch(`${API_URL}/config/thresholds`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ config: configObj })
        });

        if (res.ok) {
            alert("Configuration Saved & Reloaded!");
            modalConfig.classList.remove("active");
        } else {
            alert("Error saving config");
        }
    } catch (e) {
        alert("Invalid YAML/JSON Syntax: " + e);
    }
});

init();
