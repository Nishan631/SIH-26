const trend = [9, 11, 8, 13, 12, 14];
const free = [21, 19, 22, 18, 19, 16];
const svg = document.getElementById('trendChart');
const width = 700, height = 236, baseline = 218, scale = 6.25;
let chart = '';
[30,20,10,0].forEach(v => { const y = baseline - v * scale; chart += `<line class="grid-line" x1="0" y1="${y}" x2="700" y2="${y}"/>`; });
const positions = trend.map((_, i) => 62 + i * 125);
trend.forEach((value, i) => { const x = positions[i]; const h = value * scale; const fh = free[i] * scale; chart += `<rect class="bar-fatigue" x="${x - 25}" y="${baseline - h}" width="50" height="${h}" rx="5"/><rect class="bar-clear" x="${x - 25}" y="${baseline - h - fh}" width="50" height="${fh}" rx="5"/>`; });
const points = trend.map((v, i) => `${positions[i]},${baseline - v * scale}`).join(' ');
chart += `<polyline class="trend-line" points="${points}"/>`;
trend.forEach((v,i)=>chart += `<circle class="trend-dot" cx="${positions[i]}" cy="${baseline-v*scale}" r="4"/>`);
svg.innerHTML = chart;

const bars = document.getElementById('fatigueBars');
[35,60,40,70,55,80,48,65,92,70,86,100].forEach(v => bars.innerHTML += `<i style="height:${v}%"></i>`);

document.getElementById('detailsButton').addEventListener('click', () => {
  const toast = document.getElementById('toast'); toast.classList.add('show'); setTimeout(() => toast.classList.remove('show'), 3000);
});
