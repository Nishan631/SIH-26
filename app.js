const months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep"];
const seizures = [6, 4, 5, 3, 3, 2];

function renderTrend() {
  const svg = document.getElementById("trendChart");
  const w = 590, h = 184, pad = { x: 13, top: 11, bottom: 25 };
  const x = i => pad.x + i * ((w - pad.x * 2) / (months.length - 1));
  const y = value => pad.top + (8 - value) * ((h - pad.top - pad.bottom) / 8);
  const line = seizures.map((v, i) => `${i ? "L" : "M"}${x(i)},${y(v)}`).join(" ");
  const area = `${line} L${x(5)},${h - pad.bottom} L${x(0)},${h - pad.bottom} Z`;
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
  svg.innerHTML = `<defs><linearGradient id="areaFill" x1="0" x2="0" y1="0" y2="1"><stop stop-color="#ed7668" stop-opacity=".22"/><stop offset="1" stop-color="#ed7668" stop-opacity="0"/></linearGradient></defs>` +
    [0,2,4,6,8].map(v => `<line class="gridline" x1="0" x2="${w}" y1="${y(v)}" y2="${y(v)}"/>`).join("") +
    `<path class="area" d="${area}"/><path class="line" d="${line}"/>` +
    seizures.map((v,i) => `<circle class="point" cx="${x(i)}" cy="${y(v)}" r="4"/><text class="month" x="${x(i)}" y="${h - 5}" text-anchor="middle">${months[i]}</text>`).join("");
}

const fallbackWindows = [
  { start_time: "3025", end_time: "3030", seizure_probability: .02, status: "Normal" },
  { start_time: "3030", end_time: "3035", seizure_probability: 1, status: "Seizure" },
  { start_time: "3035", end_time: "3040", seizure_probability: 1, status: "Seizure" }
];

function showWindows(data) {
  const rows = data.slice(-3).map(row => {
    const seizure = row.status.toLowerCase() === "seizure";
    const probability = Math.round(Number(row.seizure_probability) * 100);
    return `<article class="detection"><header><span>${row.start_time}–${row.end_time}s</span><span>${probability}% confidence</span></header><strong class="${seizure ? "seizure" : "normal"}">${seizure ? "Potential seizure event" : "Normal activity"}</strong><div class="probability ${seizure ? "alert" : ""}"><i style="width:${Math.max(probability, 3)}%"></i></div></article>`;
  }).join("");
  document.getElementById("detectionRows").innerHTML = rows;
}

async function loadPredictions() {
  try {
    const response = await fetch("data/demo/seizure_predictions.csv");
    if (!response.ok) throw new Error("CSV unavailable");
    const [headers, ...lines] = (await response.text()).trim().split(/\r?\n/);
    const keys = headers.split(",");
    const data = lines.map(line => Object.fromEntries(line.split(",").map((value, index) => [keys[index], value])));
    showWindows(data);
  } catch { showWindows(fallbackWindows); }
}

document.getElementById("exportBtn").addEventListener("click", () => {
  const toast = document.getElementById("toast"); toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2600);
});
document.getElementById("rangeBtn").addEventListener("click", function() {
  this.textContent = this.textContent.includes("6") ? "This year  ⌄" : "Last 6 months  ⌄";
});
renderTrend(); loadPredictions();

// Demo is intentionally activated by a user click: browsers block alarm audio otherwise.
const canvas = document.getElementById("eegCanvas");
const ctx = canvas.getContext("2d");
let demoFrame, demoStartedAt, alarmContext, alarmOscillator, alarmGain, alarmTimer;

function drawEEG(seconds = 0) {
  const { width: w, height: h } = canvas;
  ctx.clearRect(0, 0, w, h);
  const activeEvent = seconds >= 30 && seconds <= 48;
  for (let i = 0; i < 8; i++) {
    const base = (i + .5) * h / 8;
    ctx.strokeStyle = "#e8edf2"; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(0, base); ctx.lineTo(w, base); ctx.stroke();
    ctx.strokeStyle = activeEvent ? (i < 5 ? "#eb7568" : "#d58b7d") : "#54b69c";
    ctx.lineWidth = 1.25; ctx.beginPath();
    for (let px = 0; px < w; px += 2) {
      const t = px / 33 + seconds * 6 + i * 1.7;
      const normal = Math.sin(t * 2.7) * 3 + Math.sin(t * .8) * 2 + Math.sin(t * 7) * 1.3;
      const burst = activeEvent ? Math.sin(t * 7.4) * (i < 5 ? 10 : 6) + Math.sin(t * 2) * 5 : 0;
      const y = base + normal + burst;
      px ? ctx.lineTo(px, y) : ctx.moveTo(px, y);
    }
    ctx.stroke();
  }
  if (activeEvent) { ctx.fillStyle = "#fff1ef"; ctx.globalAlpha = .7; ctx.fillRect(0, 0, w, h); ctx.globalAlpha = 1; }
}

function startAlarm() {
  if (alarmOscillator) return;
  alarmContext = new (window.AudioContext || window.webkitAudioContext)();
  alarmOscillator = alarmContext.createOscillator(); alarmGain = alarmContext.createGain();
  alarmOscillator.type = "square"; alarmOscillator.frequency.value = 720; alarmGain.gain.value = .08;
  alarmOscillator.connect(alarmGain).connect(alarmContext.destination); alarmOscillator.start();
  alarmTimer = setInterval(() => { if (alarmOscillator) alarmOscillator.frequency.value = alarmOscillator.frequency.value === 720 ? 960 : 720; }, 420);
}
function stopAlarm() { if (alarmTimer) clearInterval(alarmTimer); alarmTimer = null; if (alarmOscillator) { alarmOscillator.stop(); alarmContext.close(); alarmOscillator = null; } }
function setDemoState(alert) {
  const state = document.getElementById("detectionState");
  const signal = document.getElementById("signalState");
  state.classList.toggle("alert", alert);
  state.querySelector("strong").textContent = alert ? "Seizure detected" : "Normal activity";
  state.querySelector("p").textContent = alert ? "Alarm active while event continues." : "EEG signal is within normal range.";
  signal.textContent = alert ? "SEIZURE EVENT" : "PROCESSING SIGNAL";
  document.getElementById("emergencyNote").classList.toggle("show", alert);
}
function endDemo() {
  cancelAnimationFrame(demoFrame); demoFrame = null; stopAlarm(); setDemoState(false);
  document.getElementById("demoBtn").innerHTML = "<span>▶</span> Start demo";
  document.getElementById("demoBtn").classList.remove("running");
  document.getElementById("signalState").textContent = "Demo complete";
}
function runDemo(now) {
  const seconds = Math.min((now - demoStartedAt) / 1000, 60);
  const progress = seconds / 60 * 100;
  drawEEG(seconds);
  document.getElementById("timelineFill").style.width = `${progress}%`;
  document.getElementById("playhead").style.left = `${progress}%`;
  const event = seconds >= 30 && seconds < 48;
  if (event && !alarmOscillator) startAlarm();
  if (!event && alarmOscillator) stopAlarm();
  setDemoState(event);
  if (seconds < 60) demoFrame = requestAnimationFrame(runDemo); else endDemo();
}
document.getElementById("demoBtn").addEventListener("click", () => {
  if (demoFrame) return endDemo();
  demoStartedAt = performance.now();
  document.getElementById("demoBtn").innerHTML = "■ Stop demo";
  document.getElementById("demoBtn").classList.add("running");
  demoFrame = requestAnimationFrame(runDemo);
});
drawEEG();
