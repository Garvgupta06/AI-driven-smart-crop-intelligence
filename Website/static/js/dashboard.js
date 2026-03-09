const ctx = document.getElementById("soilChart").getContext("2d");
const soilChart = new Chart(ctx, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "Soil Moisture %",
        data: [],
        borderColor: "#2f7d32",
        backgroundColor: "rgba(47,125,50,0.15)",
        fill: true,
        tension: 0.32,
        pointRadius: 2,
      },
    ],
  },
  options: {
    responsive: true,
    plugins: { legend: { display: true } },
    scales: { y: { min: 0, max: 100 } },
  },
});

async function refreshDashboard() {
  const [dataResp, predResp] = await Promise.all([
    fetch("/api/data?limit=30"),
    fetch("/api/prediction"),
  ]);

  const dataJson = await dataResp.json();
  const predJson = await predResp.json();

  const points = dataJson.data || [];
  const latest = points[points.length - 1];

  soilChart.data.labels = points.map((p) => p.captured_at.split("T")[1]?.slice(0, 8) || p.captured_at);
  soilChart.data.datasets[0].data = points.map((p) => p.moisture_percent);
  soilChart.update();

  document.getElementById("mVal").textContent = latest ? `${latest.moisture_percent}%` : "--";
  document.getElementById("tVal").textContent =
    latest && latest.temperature !== null ? `${latest.temperature} C` : "--";
  document.getElementById("hVal").textContent =
    latest && latest.humidity !== null ? `${latest.humidity}%` : "--";
  document.getElementById("stageVal").textContent = predJson.current_stage || "--";
}

document.getElementById("plantForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const plantingDate = document.getElementById("planting_date").value;
  const resp = await fetch("/api/planting-date", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ planting_date: plantingDate }),
  });

  const json = await resp.json();
  document.getElementById("plantMsg").textContent = json.message || json.error;
  refreshDashboard();
});

refreshDashboard();
setInterval(refreshDashboard, 7000);
