/* ─── app.js — ECHO-ASSIST AI Dashboard ─── */

const API_BASE = 'http://localhost:8000';

/* ─────────────────────────────────────────
   NAVBAR SCROLL
───────────────────────────────────────── */
window.addEventListener('scroll', () => {
  document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 20);
});

/* ─────────────────────────────────────────
   GRID CANVAS BACKGROUND
───────────────────────────────────────── */
function drawGrid() {
  const canvas = document.getElementById('gridCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#3db2ff';
  ctx.lineWidth = 0.5;
  const spacing = 48;
  for (let x = 0; x <= canvas.width; x += spacing) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y <= canvas.height; y += spacing) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
}
drawGrid();
window.addEventListener('resize', drawGrid);

/* ─────────────────────────────────────────
   PHONE MOCKUP ANIMATION
───────────────────────────────────────── */
const alerts = [
  'Obstacle detected: 1.2m ahead',
  'DANGER: Car approaching at 0.8m',
  'Stairs detected: 2.1m ahead',
  'Path clear — safe to proceed',
  'Person nearby: 1.6m right',
];
let alertIdx = 0;
function cycleAlerts() {
  const el = document.getElementById('phoneAlertText');
  const wrap = document.getElementById('phoneAlert');
  if (!el || !wrap) return;
  alertIdx = (alertIdx + 1) % alerts.length;
  const text = alerts[alertIdx];
  el.style.opacity = 0;
  setTimeout(() => {
    el.textContent = text;
    el.style.opacity = 1;
    const isDanger = text.includes('DANGER') || text.includes('Stairs');
    const isSafe = text.includes('clear') || text.includes('safe');
    wrap.style.background = isDanger
      ? 'rgba(255,77,77,0.1)'
      : isSafe
        ? 'rgba(46,204,113,0.1)'
        : 'rgba(255,176,32,0.1)';
    wrap.style.borderColor = isDanger
      ? 'rgba(255,77,77,0.25)'
      : isSafe
        ? 'rgba(46,204,113,0.25)'
        : 'rgba(255,176,32,0.25)';
    wrap.style.color = isDanger ? '#ff4d4d' : isSafe ? '#2ecc71' : '#ffb020';
  }, 200);
}
setInterval(cycleAlerts, 3500);

/* ─────────────────────────────────────────
   API STATUS CHECK
───────────────────────────────────────── */
async function fetchJSON(url) {
  const res = await fetch(url, { mode: 'cors' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function setChip(id, text, cls) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className = `status-chip ${cls}`;
}
function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? '--';
}

async function checkAllStatus() {
  // Use /health for both the backend server card AND health card
  // (the root / now serves the HTML dashboard, not JSON)
  try {
    const h = await fetchJSON(`${API_BASE}/health`);

    // Backend Server card
    setChip('chipMain', '● Online', 'ok');
    setText('dataAppName', h.app_name ?? 'ECHO-ASSIST AI');
    setText('dataTagline', 'AI for Inclusive Mobility');
    const badge = document.getElementById('heroBadge');
    if (badge) {
      badge.className = 'badge badge-online';
      badge.innerHTML = '<span class="dot"></span> API Online';
    }
    setText('statUptime', 'Online');

    // Health card
    setChip('chipHealth', '● Healthy', 'ok');
    setText('dataStatus', h.status?.toUpperCase() ?? 'OK');
    setText('dataEnv', h.environment ?? 'development');
    setText('dataAiMock', h.ai_mock_mode ? 'Yes (mock)' : 'No (live AI)');
  } catch (e) {
    // Backend offline
    setChip('chipMain', '✕ Offline', 'error');
    setChip('chipHealth', '✕ Unreachable', 'error');
    const badge = document.getElementById('heroBadge');
    if (badge) {
      badge.className = 'badge badge-offline';
      badge.innerHTML = '✕ API Offline — start backend first';
    }
    setText('statUptime', 'Offline');
  }
}

// Run on load
checkAllStatus();
// Refresh every 30 seconds
setInterval(checkAllStatus, 30000);

/* ─────────────────────────────────────────
   API EXPLORER
───────────────────────────────────────── */
const ENDPOINTS = {
  root: {
    method: 'GET',
    url: `${API_BASE}/health`,
    note: 'The / root now serves the web dashboard. Use /health for the JSON status check.',
  },
  health: {
    method: 'GET',
    url: `${API_BASE}/health`,
    note: 'Public endpoint — no auth required.',
  },
  docs: {
    method: 'GET',
    url: `${API_BASE}/docs`,
    note: 'Opens the interactive Swagger UI in a new tab.',
    openTab: true,
  },
  riskSafe: {
    method: 'POST',
    url: `${API_BASE}/ai/risk`,
    note: '⚠️ This endpoint requires authentication (JWT token). It will return 401 without a token. Register/login via /auth endpoints first.',
    body: JSON.stringify({
      object_name: "bench",
      fused_distance_m: 5.2,
      direction: "ahead",
      is_approaching: false,
    }, null, 2),
  },
  riskDanger: {
    method: 'POST',
    url: `${API_BASE}/ai/risk`,
    note: '⚠️ This endpoint requires authentication (JWT token). It will return 401 without a token.',
    body: JSON.stringify({
      object_name: "car",
      fused_distance_m: 0.7,
      direction: "left",
      is_approaching: true,
    }, null, 2),
  },
};

let currentEp = 'root';

function selectEndpoint(key, btn) {
  currentEp = key;
  const ep = ENDPOINTS[key];
  // Update method badge
  const methodEl = document.getElementById('expMethod');
  if (methodEl) {
    methodEl.textContent = ep.method;
    methodEl.className = `ep-method ${ep.method.toLowerCase()}`;
  }
  // Update URL
  const urlEl = document.getElementById('expUrl');
  if (urlEl) urlEl.textContent = ep.url;
  // Body
  const bodyWrap = document.getElementById('explorerBodyWrap');
  const bodyEl = document.getElementById('explorerBody');
  if (bodyWrap && bodyEl) {
    if (ep.body) {
      bodyWrap.style.display = 'block';
      bodyEl.value = ep.body;
    } else {
      bodyWrap.style.display = 'none';
    }
  }
  // Note
  const noteEl = document.getElementById('explorerNote');
  if (noteEl) noteEl.textContent = ep.note || '';
  // Active button
  document.querySelectorAll('.explorer-nav-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // Clear response
  const resp = document.getElementById('responseBody');
  if (resp) resp.textContent = 'Click ▶ Run to execute the request';
  const statusEl = document.getElementById('responseStatus');
  if (statusEl) { statusEl.textContent = ''; statusEl.className = 'response-status'; }
  document.getElementById('responseTime').textContent = '';
}

async function runRequest() {
  const ep = ENDPOINTS[currentEp];
  if (!ep) return;

  if (ep.openTab) {
    window.open(ep.url, '_blank');
    return;
  }

  const btn = document.getElementById('runBtn');
  btn.textContent = '⏳ Running…';
  btn.disabled = true;

  const respBody = document.getElementById('responseBody');
  const statusEl = document.getElementById('responseStatus');
  const timeEl = document.getElementById('responseTime');
  respBody.textContent = 'Sending request…';
  statusEl.textContent = '';
  statusEl.className = 'response-status';
  timeEl.textContent = '';

  const start = performance.now();
  try {
    const opts = {
      method: ep.method,
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
    };
    if (ep.body) {
      const bodyEl = document.getElementById('explorerBody');
      opts.body = bodyEl ? bodyEl.value : ep.body;
    }
    const res = await fetch(ep.url, opts);
    const elapsed = Math.round(performance.now() - start);
    const json = await res.json();
    respBody.textContent = JSON.stringify(json, null, 2);
    statusEl.textContent = `${res.status} ${res.statusText}`;
    statusEl.className = `response-status ${res.ok ? 'ok' : 'error'}`;
    timeEl.textContent = `${elapsed}ms`;
  } catch (e) {
    const elapsed = Math.round(performance.now() - start);
    respBody.textContent = `Error: ${e.message}\n\nMake sure the backend is running at:\n  ${API_BASE}\n\nStart it with:\n  cd backend\n  python -m uvicorn app.main:app --reload`;
    statusEl.textContent = 'Network Error';
    statusEl.className = 'response-status error';
    timeEl.textContent = `${elapsed}ms`;
  } finally {
    btn.textContent = '▶ Run';
    btn.disabled = false;
  }
}

/* ─────────────────────────────────────────
   INTERSECTION OBSERVER (fade-in on scroll)
───────────────────────────────────────── */
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.style.opacity = 1;
      e.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.feature-card, .status-card, .setup-step, .arch-node').forEach(el => {
  el.style.opacity = 0;
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  observer.observe(el);
});
