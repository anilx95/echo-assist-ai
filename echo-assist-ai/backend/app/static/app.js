const state = {
  accessToken: sessionStorage.getItem('echo_access'),
  refreshToken: sessionStorage.getItem('echo_refresh'),
  user: null,
  page: 'dashboard',
  refreshInFlight: null,
  authInFlight: false,
  introController: null,
  introPrepared: false,
  introCompleted: false,
};

const $ = selector => document.querySelector(selector);
const content = $('#page-content');
const pageNames = {
  dashboard: ['Overview', 'Dashboard'], monitoring: ['Awareness', 'Smart cane monitor'],
  detection: ['Awareness', 'Obstacle detection'], risk: ['Awareness', 'AI risk prediction'],
  navigation: ['Mobility', 'Navigation'], sos: ['Safety', 'Emergency SOS'],
  contacts: ['Safety', 'Emergency contacts'], notifications: ['Safety & data', 'Alerts & history'],
  sensors: ['Safety & data', 'Sensor history'], analytics: ['Safety & data', 'Reports & analytics'],
  devices: ['Account', 'Device & settings'], profile: ['Account', 'User profile'],
  settings: ['Account', 'Accessibility settings'],
};

function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]); }
function dateText(value) { return value ? new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Not available'; }
function timeText(value) { return value ? new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Not available'; }
function decimal(value, digits = 1) { const number = Number(value); return Number.isFinite(number) ? number.toFixed(digits) : '—'; }
function empty(text) { return `<p class="empty">${escapeHtml(text)}</p>`; }
function tokensAreValid(tokens) { return Boolean(tokens?.access_token && tokens?.refresh_token && tokens.token_type === 'bearer'); }
function tag(value) {
  const safe = escapeHtml(value || 'unavailable');
  const css = /danger|active|critical|not_delivered|failed/i.test(value) ? 'danger' : /warning|pending/i.test(value) ? 'warning' : !value ? 'muted' : '';
  return `<span class="tag ${css}">${safe}</span>`;
}
function notify(message) {
  const toast = $('#toast'); toast.textContent = message; toast.hidden = false;
  clearTimeout(notify.timer); notify.timer = setTimeout(() => { toast.hidden = true; }, 5000);
}
function preferenceReducedMotion() { return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches; }

function saveTokens(tokens) {
  if (!tokensAreValid(tokens)) throw new Error('The server returned an invalid authentication response.');
  state.accessToken = tokens.access_token; state.refreshToken = tokens.refresh_token;
  sessionStorage.setItem('echo_access', state.accessToken); sessionStorage.setItem('echo_refresh', state.refreshToken);
}
function clearSession() {
  state.accessToken = null; state.refreshToken = null; state.user = null;
  sessionStorage.removeItem('echo_access'); sessionStorage.removeItem('echo_refresh');
}

async function refreshSession() {
  if (!state.refreshToken) return false;
  if (!state.refreshInFlight) {
    state.refreshInFlight = (async () => {
      const response = await fetch('/auth/refresh', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: state.refreshToken }),
      });
      if (!response.ok) return false;
      const tokens = await response.json().catch(() => null);
      if (!tokensAreValid(tokens)) return false;
      saveTokens(tokens); return true;
    })().finally(() => { state.refreshInFlight = null; });
  }
  return state.refreshInFlight;
}

async function api(path, options = {}, retried = false) {
  const formData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  const headers = { ...(options.headers || {}) };
  if (!formData && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  if (state.accessToken) headers.Authorization = `Bearer ${state.accessToken}`;
  const response = await fetch(path, { ...options, headers });
  const authPath = path.startsWith('/auth/');
  if (response.status === 401 && !authPath && !retried && await refreshSession()) return api(path, options, true);
  if (response.status === 401 && !authPath) {
    clearSession(); showAuth();
    throw new Error('Your session expired. Please sign in again.');
  }
  const body = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 429) throw new Error('Too many requests. Please wait a minute before trying again.');
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}).`);
  }
  return body;
}
async function optional(path) { try { return await api(path); } catch (error) { return { _error: error.message }; } }

function hideIntro() { $('#intro-shell').hidden = true; }
function hideVideoIntro() {
  const shell = $('#video-intro-shell');
  if (shell) {
    shell.classList.remove('is-leaving');
    shell.hidden = true;
  }
}
function finishVideoIntro() {
  const shell = $('#video-intro-shell');
  const video = $('#intro-cane-video');
  if (video) {
    try { video.pause(); } catch (_) {}
  }
  const proceed = () => {
    if (state.accessToken) {
      showApp();
    } else {
      showAuth('login');
    }
  };
  if (!shell || shell.hidden) {
    proceed();
    return;
  }
  // Smooth cinematic cross-fade: start intro fade-out and login card fade-in concurrently
  shell.classList.add('is-leaving');
  if (!state.accessToken) {
    const authShell = $('#auth-shell');
    if (authShell) {
      authShell.hidden = false;
      authShell.classList.add('is-entering');
      setAuthTab('login');
      void authShell.offsetHeight; // Force reflow
      requestAnimationFrame(() => {
        authShell.classList.remove('is-entering');
      });
    }
  }
  setTimeout(() => {
    shell.hidden = true;
    shell.classList.remove('is-leaving');
    proceed();
  }, 600);
}
function playVideoIntro() {
  hideIntro();
  const authShell = $('#auth-shell'); if (authShell) authShell.hidden = true;
  const appShell = $('#app-shell'); if (appShell) appShell.hidden = true;
  const landing = $('#saas-landing'); if (landing) landing.hidden = true;
  const nav = $('#saas-nav'); if (nav) nav.hidden = true;

  const shell = $('#video-intro-shell');
  if (!shell) {
    showAuth('register');
    return;
  }
  shell.hidden = false;
  shell.classList.remove('is-leaving');

  const video = $('#intro-cane-video');
  if (video) {
    try { video.currentTime = 0; } catch (_) {}

    video.onended = () => {
      finishVideoIntro();
    };

    const playPromise = video.play();
    if (playPromise !== undefined) {
      playPromise.catch(err => {
        console.warn('Autoplay waiting for user interaction:', err);
      });
    }
  }
}
function setAuthTab(mode) {
  const login = mode === 'login';
  $('#login-tab').classList.toggle('active', login); $('#register-tab').classList.toggle('active', !login);
  $('#login-tab').setAttribute('aria-selected', String(login)); $('#register-tab').setAttribute('aria-selected', String(!login));
  $('#login-form').hidden = !login; $('#register-form').hidden = login;
  $('#reset-form').hidden = true; $('#verify-form').hidden = true;
}
function showLanding() {
  hideIntro();
  hideVideoIntro();
  const authShell = $('#auth-shell'); if (authShell) authShell.hidden = true;
  const appShell = $('#app-shell'); if (appShell) appShell.hidden = true;
  const landing = $('#saas-landing'); if (landing) landing.hidden = false;
  const nav = $('#saas-nav'); if (nav) nav.hidden = false;
  const navCta = $('#nav-cta-btn');
  if (navCta) navCta.textContent = state.accessToken ? 'Go to Workspace' : 'Launch App';
  requestAnimationFrame(() => {
    document.querySelectorAll('.reveal').forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight + 250 || el.closest('.hero')) {
        el.classList.add('visible');
      }
    });
  });
}
function showAuth(mode = 'login') {
  hideIntro();
  hideVideoIntro();
  const landing = $('#saas-landing'); if (landing) landing.hidden = true;
  const nav = $('#saas-nav'); if (nav) nav.hidden = true;
  $('#app-shell').classList.remove('is-preloading');
  $('#app-shell').hidden = true;
  $('#auth-shell').hidden = false;
  $('#auth-shell').classList.remove('is-entering');
  setAuthTab(mode);
}
function displayDate() { $('#today-date').textContent = new Date().toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' }); }
function updateAccountChrome() {
  const name = state.user?.full_name || 'ECHO-ASSIST user'; const email = state.user?.email || '';
  const initial = name.trim().charAt(0).toUpperCase() || 'E';
  $('#account-name').textContent = name; $('#account-email').textContent = email; $('#account-initial').textContent = initial;
  $('#sidebar-name').textContent = name; $('#sidebar-initial').textContent = initial; displayDate();
}
function setDeviceStatus(devices) {
  const chip = $('#device-status');
  const connected = Array.isArray(devices) && devices.some(device => device.connection_status === 'connected');
  chip.classList.toggle('connected', connected); chip.classList.toggle('disconnected', Array.isArray(devices) && !connected);
  chip.querySelector('span').textContent = connected ? 'Device connected' : 'Device disconnected';
}
function showApp() {
  hideIntro();
  hideVideoIntro();
  const landing = $('#saas-landing'); if (landing) landing.hidden = true;
  const nav = $('#saas-nav'); if (nav) nav.hidden = true;
  $('#auth-shell').hidden = true;
  $('#app-shell').hidden = false;
  $('#app-shell').classList.remove('is-preloading');
  updateAccountChrome();
  renderPage();
}
async function finishAuthentication(tokens) {
  saveTokens(tokens); state.user = await api('/user/profile'); state.page = 'dashboard';
  location.hash = 'dashboard'; showApp();
}
async function bootstrap() {
  if (!state.accessToken) return showLanding();
  try {
    state.user = await api('/user/profile');
    if (location.hash && location.hash.length > 1 && location.hash !== '#landing-top') {
      showApp();
    } else {
      showLanding();
    }
  } catch (_) {
    showLanding();
  }
}
function prepareNextScreen() {
  if (state.introPrepared) return;
  state.introPrepared = true;
  if (state.accessToken) { $('#app-shell').hidden = false; $('#app-shell').classList.add('is-preloading'); return; }
  $('#auth-shell').hidden = false; $('#auth-shell').classList.add('is-entering');
}
function completeIntro() {
  if (state.introCompleted) return;
  state.introCompleted = true;
  sessionStorage.setItem('echo_intro_seen', '1'); hideIntro(); state.introController = null; bootstrap();
}
function leaveIntro() {
  if (state.introController) { state.introController.skip(); return; }
  prepareNextScreen(); completeIntro();
}
function beginExperience() {
  const query = new URLSearchParams(location.search); const token = query.get('token');
  if ((query.get('action') === 'reset-password' || query.get('action') === 'verify-email') && token) {
    showAuth();
    $('#login-form').hidden = true; $('#register-form').hidden = true;
    if (query.get('action') === 'reset-password') { $('#reset-form').hidden = false; $('#reset-form').dataset.token = token; }
    else { $('#verify-form').hidden = false; $('#verify-form').dataset.token = token; }
    return;
  }
  const requested = location.hash.slice(1); if (pageNames[requested]) state.page = requested;
  playVideoIntro();
}

function setPage(page) {
  if (!pageNames[page]) return;
  state.page = page; if (location.hash !== `#${page}`) location.hash = page;
  $('#app-shell').classList.remove('nav-open'); $('#menu-button').setAttribute('aria-expanded', 'false'); $('#nav-backdrop').hidden = true;
  renderPage();
}
async function renderPage() {
  const [kicker, title] = pageNames[state.page] || pageNames.dashboard;
  $('#page-kicker').textContent = kicker; $('#page-title').textContent = title;
  document.querySelectorAll('#sidebar-nav button').forEach(button => button.classList.toggle('active', button.dataset.page === state.page));
  content.classList.remove('is-entering');
  content.innerHTML = '<div class="loading">Loading your account information…</div>';
  try {
    await ({ dashboard: renderDashboard, monitoring: renderMonitoring, detection: renderDetection, risk: renderRisk,
      navigation: renderNavigation, sos: renderSos, contacts: renderContacts, devices: renderDevices,
      sensors: renderSensors, notifications: renderNotifications, analytics: renderAnalytics,
      profile: renderProfile, settings: renderSettings }[state.page] || renderDashboard)();
    if (!preferenceReducedMotion()) {
      void content.offsetWidth;
      content.classList.add('is-entering');
      const clearPageTransition = event => { if (event.currentTarget === content) content.classList.remove('is-entering'); };
      content.addEventListener('animationend', clearPageTransition, { once: true });
    }
  } catch (error) {
    content.innerHTML = `<section class="panel"><h3>Could not load this page</h3><p class="empty">${escapeHtml(error.message)}</p><button id="retry-page" class="secondary-button" type="button">Try again</button></section>`;
    $('#retry-page').onclick = renderPage;
  }
}

function caneScene() {
  return '<div class="cane-scene" aria-hidden="true"><div class="radar-ring ring-one"></div><div class="radar-ring ring-two"></div><div class="radar-ring ring-three"></div><div class="cane-visual"><span class="cane-handle"></span><span class="cane-shaft"></span><span class="cane-tip"></span><span class="cane-sensor"></span></div><div class="radar-sweep"></div></div>';
}
function riskInfo(level) {
  const normalized = String(level || '').toUpperCase();
  if (normalized === 'DANGER') return { label: 'High risk', value: 90, color: 'var(--danger)', css: 'danger' };
  if (normalized === 'WARNING') return { label: 'Caution', value: 62, color: 'var(--warning)', css: 'warning' };
  if (normalized === 'SAFE') return { label: 'Low risk', value: 30, color: 'var(--safe)', css: 'safe' };
  return { label: 'No result', value: 0, color: 'var(--muted)', css: '' };
}
function meter(value) { const bounded = Math.max(0, Math.min(100, Number(value) || 0)); return `<span class="battery-meter"><i style="width:${bounded}%"></i></span>`; }
function sensorTiles(reading, fusion) {
  if (reading?._error || !reading) {
    return `<div class="sensor-grid"><div class="sensor-tile"><small>Ultrasonic distance</small><strong>Standby</strong><em>Awaiting hardware telemetry</em></div><div class="sensor-tile"><small>ToF distance</small><strong>Standby</strong><em>Awaiting hardware telemetry</em></div><div class="sensor-tile"><small>Accelerometer</small><strong>Standby</strong><em>Awaiting hardware telemetry</em></div><div class="sensor-tile"><small>Fused distance</small><strong>Standby</strong><em>Awaiting hardware telemetry</em></div></div>`;
  }
  const distance = fusion?._error ? '—' : decimal(fusion?.fusion?.distance_m, 2);
  return `<div class="sensor-grid"><div class="sensor-tile"><small>Ultrasonic distance</small><strong>${decimal(reading?.ultrasonic_cm)} cm</strong><em>${reading?.ultrasonic_cm == null ? 'Standby' : 'Sensor packet received'}</em></div><div class="sensor-tile"><small>ToF distance</small><strong>${decimal(reading?.tof_mm, 0)} mm</strong><em>${reading?.tof_mm == null ? 'Standby' : 'Sensor packet received'}</em></div><div class="sensor-tile"><small>Accelerometer</small><strong>${decimal(reading?.accel_z, 2)}</strong><em>X ${decimal(reading?.accel_x, 2)} · Y ${decimal(reading?.accel_y, 2)}</em></div><div class="sensor-tile"><small>Fused distance</small><strong>${distance === '—' ? '—' : `${distance} m`}</strong><em>${fusion?._error ? 'Standby' : 'Derived by sensor service'}</em></div></div>`;
}
function radarMarkup(reading, fusion, extraClass = '') {
  const distanceM = Number(fusion?.fusion?.distance_m);
  const sensorMeters = Number.isFinite(distanceM) ? distanceM : (Number(reading?.ultrasonic_cm) / 100);
  if (!Number.isFinite(sensorMeters) || sensorMeters < 0) return `<div class="radar ${extraClass}"><span class="radar-empty">Awaiting hardware telemetry</span><span class="radar-center"></span></div>`;
  const danger = sensorMeters < 1; const caution = sensorMeters < 2;
  const y = Math.max(12, Math.min(40, 48 - Math.min(sensorMeters, 4) * 8));
  return `<div class="radar ${extraClass}"><span class="radar-target ${danger ? 'danger' : caution ? 'warning' : ''}" style="--target-x:50%;--target-y:${y}%" title="Measured distance ${decimal(sensorMeters, 2)} metres"></span><span class="radar-center"></span></div>`;
}
function activityMarkup(items, emptyMessage) { return items.length ? `<ul class="list activity-list">${items.map(item => `<li><strong>${escapeHtml(item.title)}</strong><br><small>${escapeHtml(item.detail)} · ${timeText(item.at)}</small></li>`).join('')}</ul>` : empty(emptyMessage); }
function riskChartMarkup(rows) {
  const riskValues = { SAFE: 25, WARNING: 62, DANGER: 94 };
  const series = rows.slice(0, 12).reverse().map(row => ({ value: riskValues[row.risk_level] ?? 0, at: row.created_at, level: row.risk_level }));
  if (!series.length) return `<div class="status-empty"><div><span class="feature-icon">G</span>${empty('No recorded risk evaluations are available for this chart.')}</div></div>`;
  const denominator = Math.max(series.length - 1, 1);
  const points = series.map((point, index) => `${Math.round((index / denominator) * 400)},${110 - point.value}`).join(' ');
  const latest = series[series.length - 1];
  return `<div class="session-chart"><svg viewBox="0 0 400 120" preserveAspectRatio="none" aria-label="Recorded risk classifications"><defs><linearGradient id="chartGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#a78bfa"/><stop offset="100%" stop-color="#06b6d4"/></linearGradient></defs><polyline points="${points}" fill="none" stroke="url(#chartGrad)" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/></svg></div><div class="chart-note"><span>${dateText(series[0].at)}</span><span>${escapeHtml(latest.level)} · ${dateText(latest.at)}</span></div>`;
}
function bindGoLinks() { document.querySelectorAll('[data-go]').forEach(button => button.onclick = () => setPage(button.dataset.go)); }

async function renderDashboard() {
  const [overview, latest, fusion, notifications, detections, riskHistory] = await Promise.all([api('/dashboard/overview'), optional('/sensors/latest'), optional('/sensors/fusion/latest'), optional('/notifications'), optional('/ai/history'), optional('/ai/risk/history')]);
  setDeviceStatus(overview.devices); const reading = latest?._error ? null : latest; const risk = overview.latest_risk; const riskView = riskInfo(risk?.risk_level);
  const primaryDevice = overview.devices?.[0]; const activity = [
    ...(Array.isArray(notifications) ? notifications.slice(0, 3).map(item => ({ title: item.title, detail: item.message || item.status, at: item.created_at })) : []),
    ...(Array.isArray(detections) ? detections.slice(0, 2).map(item => ({ title: `${item.class_name} detected`, detail: `${Math.round((item.confidence || 0) * 100)}% confidence`, at: item.created_at })) : []),
  ].slice(0, 4);
  const hasNoDevices = !overview.devices || overview.devices.length === 0;
  const demoBanner = hasNoDevices ? `
  <section class="demo-seed-banner panel" style="display:flex;align-items:center;justify-content:space-between;padding:18px 24px;margin-bottom:20px;border:1px solid rgba(139,92,246,0.35);background:linear-gradient(135deg,rgba(139,92,246,0.14),rgba(6,182,212,0.08));border-radius:var(--radius);gap:16px;flex-wrap:wrap;">
    <div style="display:flex;align-items:center;gap:14px;">
      <span style="font-size:26px;">🦯</span>
      <div>
        <strong style="color:var(--fg);font-size:15px;display:block;">Hardware Simulator Ready</strong>
        <span style="color:var(--muted);font-size:13px;">No physical cane linked yet. Stream simulated ultrasonic, ToF lidar, and AI obstacle detection telemetry with one click.</span>
      </div>
    </div>
    <button id="activate-demo-cane" class="btn-glow" type="button" style="padding:10px 22px;font-size:13px;cursor:pointer;">⚡ Launch Demo Telemetry</button>
  </section>` : '';
  content.innerHTML = `${demoBanner}<section class="welcome-hero"><div><p class="eyebrow">Your mobility workspace</p><h2>Welcome back${state.user?.full_name ? `, ${escapeHtml(state.user.full_name.split(' ')[0])}` : ''}.</h2><p>Stay safe, stay independent with ECHO-ASSIST AI.</p></div><span class="hero-status"><i></i> Account protected</span></section>
  <section class="dashboard-grid"><article class="panel"><div class="card-title"><span class="feature-icon">M</span><div><h3>Smart Cane Monitoring</h3><p class="panel-subtitle">Connection and hardware status</p></div></div><div class="cane-status-layout"><div class="cane-mini">${caneScene()}</div><div class="status-stack"><div class="status-row"><strong>${primaryDevice?.connection_status === 'connected' ? 'Device connected' : primaryDevice ? 'Device disconnected' : 'Hardware Standby'}</strong>${tag(primaryDevice?.connection_status || 'STANDBY')}</div><div class="status-row"><span>Cane ID</span><strong>${escapeHtml(primaryDevice?.device_id || 'Awaiting registration')}</strong></div><div class="status-row"><span>Battery</span><strong>${primaryDevice?.battery_percent == null ? (primaryDevice ? 'Unavailable' : 'Standby') : `${primaryDevice.battery_percent}%`}</strong></div>${primaryDevice?.battery_percent == null ? '' : meter(primaryDevice.battery_percent)}<div class="status-row"><span>System health</span>${tag(primaryDevice?.sensor_health || 'STANDBY')}</div></div></div></article>
  <article class="panel"><div class="card-title"><span class="feature-icon">R</span><div><h3>AI Risk Prediction</h3><p class="panel-subtitle">Latest result from the risk service</p></div></div><div class="risk-layout"><div class="risk-gauge" style="--gauge-value:${riskView.value};--gauge-color:${riskView.color}"><div><strong>${riskView.label}</strong><span>${escapeHtml(risk?.risk_level || 'Standby')}</span></div></div><div class="risk-details"><div class="risk-detail"><span>Risk level</span>${tag(risk?.risk_level || 'STANDBY')}</div><div class="risk-detail"><span>Latest prediction</span><strong>${risk ? timeText(risk.created_at) : 'Awaiting data'}</strong></div><div class="risk-detail"><span>Prediction status</span><strong>${risk ? 'Recorded' : 'Ready'}</strong></div></div></div><p class="risk-message">${escapeHtml(risk?.message || 'No risk event has been recorded for this account yet.')}</p></article>
  <article class="panel sos-card"><span class="sos-mark">SOS</span><h3>Emergency</h3><p>${overview.active_sos ? `Active alert #${overview.active_sos.id}` : 'Emergency assistance'}</p><button id="dashboard-sos" class="danger-button" type="button">${overview.active_sos ? 'Open SOS status' : 'Activate SOS'}</button></article></section>
  <section class="secondary-dashboard-grid"><article class="panel"><div class="card-title"><span class="feature-icon">S</span><div><h3>Live Sensor Readings</h3><p class="panel-subtitle">Latest stored packet from your smart cane</p></div></div>${sensorTiles(reading, fusion)}</article>
  <article class="panel"><div class="card-title"><span class="feature-icon">O</span><div><h3>Obstacle Detection</h3><p class="panel-subtitle">Distance zone from the sensor service</p></div></div>${radarMarkup(reading, fusion)}<div class="radar-key"><span><i></i>Clear</span><span><i class="warning"></i>Caution</span><span><i class="danger"></i>Danger</span></div></article>
  <article class="panel"><div class="card-title"><span class="feature-icon">A</span><div><h3>Alert History</h3><p class="panel-subtitle">Latest recorded events</p></div></div>${activityMarkup(activity, 'No alerts or detections are recorded yet.')}</article></section>
  <section class="grid-two"><article class="panel"><div class="card-title"><span class="feature-icon">G</span><div><h3>Session Overview</h3><p class="panel-subtitle">Recorded risk classifications</p></div></div>${riskHistory?._error ? empty('Risk history is unavailable.') : riskChartMarkup(riskHistory)}</article><article class="panel"><div class="card-title"><span class="feature-icon">Q</span><div><h3>Quick Actions</h3><p class="panel-subtitle">Open existing workspace tools</p></div></div><div class="quick-actions"><button class="quick-action" data-go="monitoring" type="button"><span class="feature-icon">M</span>Live monitor</button><button class="quick-action" data-go="analytics" type="button"><span class="feature-icon">G</span>Reports</button><button class="quick-action" data-go="detection" type="button"><span class="feature-icon">O</span>Detection</button><button class="quick-action" data-go="settings" type="button"><span class="feature-icon">T</span>Settings</button></div></article></section>`;
  const activateDemoBtn = $('#activate-demo-cane');
  if (activateDemoBtn) {
    activateDemoBtn.onclick = async () => {
      activateDemoBtn.disabled = true;
      activateDemoBtn.textContent = 'Connecting simulator…';
      try {
        try {
          await api('/devices', {
            method: 'POST',
            body: JSON.stringify({ device_id: 'ECHO_CANE_001', device_name: 'Smart Cane Alpha (Demo)', is_simulator: true })
          });
        } catch (_) {}
        await api('/sensors/data', {
          method: 'POST',
          body: JSON.stringify({
            device_id: 'ECHO_CANE_001',
            ultrasonic_cm: 124.5,
            tof_mm: 1240,
            accel_x: 0.05,
            accel_y: -0.12,
            accel_z: 9.81,
            battery_percent: 94
          })
        });
        await api('/ai/risk', {
          method: 'POST',
          body: JSON.stringify({
            object_name: 'Drop-off / Curb',
            fused_distance_m: 1.24,
            direction: 'center',
            is_approaching: false
          })
        });
        notify('Demo Smart Cane activated! Real-time telemetry streaming.');
        await renderDashboard();
      } catch (err) {
        notify(err.message || 'Could not connect demo cane');
        activateDemoBtn.disabled = false;
        activateDemoBtn.textContent = '⚡ Launch Demo Telemetry';
      }
    };
  }
  $('#dashboard-sos').onclick = () => setPage('sos'); bindGoLinks();
}

async function renderMonitoring() {
  const [latest, fusion, devices] = await Promise.all([optional('/sensors/latest'), optional('/sensors/fusion/latest'), api('/devices')]);
  setDeviceStatus(devices); const reading = latest?._error ? null : latest; const primary = devices[0]; const connected = primary?.connection_status === 'connected';
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Hardware awareness</p><h2>Smart cane monitor</h2><p>Displays the newest stored packet. It never presents disconnected hardware as live.</p></div><div class="page-heading-actions"><button id="refresh-monitoring" class="secondary-button" type="button">Refresh readings</button><button data-go="devices" class="secondary-button" type="button">Manage device</button></div></div><section class="monitor-layout"><article class="panel monitor-cane">${caneScene()}</article><article class="panel"><div class="card-title"><span class="feature-icon">H</span><div><h3>Hardware status</h3><p class="panel-subtitle">${escapeHtml(primary?.device_name || 'No smart cane registered')}</p></div></div><div class="connection-banner ${connected ? 'connected' : ''}"><i></i><span>${connected ? 'Device Connected' : 'Device Disconnected'}</span></div><div class="reading-stack"><div class="reading-line"><span>Cane ID</span><strong>${escapeHtml(primary?.device_id || 'Not registered')}</strong></div><div class="reading-line"><span>Battery</span><strong>${primary?.battery_percent == null ? 'Unavailable' : `${primary.battery_percent}%`}</strong></div>${primary?.battery_percent == null ? '' : meter(primary.battery_percent)}<div class="reading-line"><span>Sensor health</span>${tag(primary?.sensor_health)}</div><div class="reading-line"><span>Latest timestamp</span><strong>${dateText(reading?.device_timestamp || reading?.received_at)}</strong></div><div class="reading-line"><span>SOS switch</span><strong>${reading ? (reading.sos_pressed ? 'Pressed' : 'Not pressed') : 'No packet'}</strong></div></div></article></section><section class="grid-two"><article class="panel"><div class="card-title"><span class="feature-icon">S</span><div><h3>Sensor availability</h3><p class="panel-subtitle">Measured values from the stored packet</p></div></div>${sensorTiles(reading, fusion)}</article><article class="panel"><div class="card-title"><span class="feature-icon">O</span><div><h3>Distance radar</h3><p class="panel-subtitle">Uses sensor fusion where available</p></div></div>${radarMarkup(reading, fusion)}<p class="danger-zone-note">Distance zones are visual aids. Follow your environment and training at all times.</p></article></section>`;
  $('#refresh-monitoring').onclick = renderMonitoring; bindGoLinks();
}

async function renderDetection() {
  const [history, latest, fusion] = await Promise.all([optional('/ai/history'), optional('/sensors/latest'), optional('/sensors/fusion/latest')]);
  const reading = latest?._error ? null : latest;
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Vision assistance</p><h2>Obstacle detection</h2><p>Radar uses real sensor distance only. Object results come from the configured backend detection service.</p></div></div><section class="visual-page-grid"><article class="panel detection-radar"><div class="card-title"><span class="feature-icon">O</span><div><h3>Proximity radar</h3><p class="panel-subtitle">Clear, caution, and danger zones</p></div></div>${radarMarkup(reading, fusion, 'large-radar')}<div class="radar-key"><span><i></i>Clear zone</span><span><i class="warning"></i>Caution (&lt; 2 m)</span><span><i class="danger"></i>Danger (&lt; 1 m)</span></div><p class="danger-zone-note">${reading ? 'Distance reflects the latest stored sensor packet.' : 'Connect a device and send a sensor packet to activate the radar.'}</p></article><article class="panel"><div class="card-title"><span class="feature-icon">AI</span><div><h3>Run configured detection</h3><p class="panel-subtitle">No UI-generated detections</p></div></div><p class="muted">This invokes the existing detection service. Its response identifies whether mock mode is configured.</p><button id="run-detection" class="primary-button" type="button">Run configured detection</button><div id="detection-result" class="result-area"></div></article></section><section class="panel"><div class="card-title"><span class="feature-icon">A</span><div><h3>Detection history</h3><p class="panel-subtitle">Recorded detections for this account</p></div></div>${history?._error ? empty('No detection history is available.') : history.length ? `<ul class="list">${history.map(row => `<li><strong>${escapeHtml(row.class_name)}</strong> · ${Math.round((row.confidence || 0) * 100)}%<br><small>${escapeHtml(row.position || 'unknown position')} · ${dateText(row.created_at)}</small></li>`).join('')}</ul>` : empty('No detections are stored yet.')}</section>`;
  $('#run-detection').onclick = async event => {
    const button = event.currentTarget; button.disabled = true; button.textContent = 'Running detection…';
    try {
      const result = await api('/ai/detect', { method: 'POST', body: JSON.stringify({ use_mock: false }) });
      $('#detection-result').innerHTML = `<p>${tag(result.mock_mode ? 'SIMULATED SERVICE' : 'MODEL RESULT')}</p>${result.detections.length ? `<ul class="list">${result.detections.map(item => `<li><strong>${escapeHtml(item.class_name)}</strong> · ${Math.round(item.confidence * 100)}% · ${escapeHtml(item.position)}</li>`).join('')}</ul>` : empty('No objects were returned by the configured service.')}`;
    } catch (error) { $('#detection-result').innerHTML = empty(error.message); }
    finally { button.disabled = false; button.textContent = 'Run configured detection'; }
  };
}

function riskGauge(level) { const view = riskInfo(level); return `<div class="risk-gauge" style="--gauge-value:${view.value};--gauge-color:${view.color}"><div><strong>${view.label}</strong><span>${escapeHtml(level || 'No result')}</span></div></div>`; }
async function renderRisk() {
  const [overview, history] = await Promise.all([api('/dashboard/overview'), optional('/ai/risk/history')]);
  const latest = overview.latest_risk;
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Risk analysis</p><h2>AI risk prediction</h2><p>Evaluates a real measurement using the existing risk API and records the result for your account.</p></div></div><section class="visual-page-grid"><article class="panel"><div class="card-title"><span class="feature-icon">R</span><div><h3>Evaluate obstacle risk</h3><p class="panel-subtitle">Enter a measured or fused distance</p></div></div><form id="risk-form"><label>Object type<input name="object_name" required maxlength="50" placeholder="e.g. pole"></label><div class="form-grid"><label>Fused distance (metres)<input name="fused_distance_m" type="number" min="0" step="0.1" required></label><label>Direction<select name="direction"><option value="center">Center</option><option value="left">Left</option><option value="right">Right</option></select></label></div><label class="switch-row">Object is approaching<input name="is_approaching" type="checkbox"></label><button class="primary-button" type="submit">Evaluate risk</button></form></article><article class="panel"><div class="card-title"><span class="feature-icon">R</span><div><h3>Latest prediction</h3><p class="panel-subtitle">The API does not invent confidence values</p></div></div><div id="risk-result">${latest ? `<div class="risk-layout">${riskGauge(latest.risk_level)}<div><p>${tag(latest.risk_level)}</p><p><strong>${escapeHtml(latest.message || 'No voice message recorded.')}</strong></p><small>${dateText(latest.created_at)}</small></div></div>` : `<div class="status-empty"><div><span class="feature-icon">R</span>${empty('No risk result has been recorded yet.')}</div></div>`}</div></article></section><section class="grid-two"><article class="panel"><h3>Risk history</h3>${history?._error ? empty('Risk history is unavailable.') : history.length ? `<ul class="list">${history.map(item => `<li><div class="list-row"><strong>${escapeHtml(item.object_name)}</strong>${tag(item.risk_level)}</div><small>${decimal(item.fused_distance_m, 1)} m · ${escapeHtml(item.direction)} · ${dateText(item.created_at)}</small></li>`).join('')}</ul>` : empty('No previous risk evaluations are recorded.')}</article><article class="panel"><h3>Risk levels</h3><p><span class="tag">SAFE</span> Clear or distant measurement.</p><p><span class="tag warning">WARNING</span> An obstacle needs attention.</p><p><span class="tag danger">DANGER</span> Move away and use caution.</p></article></section>`;
  $('#risk-form').onsubmit = async event => {
    event.preventDefault(); const form = event.currentTarget; const button = form.querySelector('button[type="submit"]'); const raw = Object.fromEntries(new FormData(form));
    button.disabled = true; button.textContent = 'Evaluating…';
    try {
      const result = await api('/ai/risk', { method: 'POST', body: JSON.stringify({ object_name: raw.object_name, fused_distance_m: Number(raw.fused_distance_m), direction: raw.direction, is_approaching: raw.is_approaching === 'on' }) });
      $('#risk-result').innerHTML = `<div class="risk-layout">${riskGauge(result.risk_level)}<div><p>${tag(result.risk_level)}</p><p><strong>${escapeHtml(result.object_name)}</strong> at ${decimal(result.fused_distance_m, 1)} metres</p><p>${escapeHtml(result.message || 'No alert message required.')}</p><small>Vibration pattern: ${escapeHtml(result.vibration_pattern)}</small></div></div>`;
      notify('Risk result recorded.');
    } catch (error) { $('#risk-result').innerHTML = empty(error.message); }
    finally { button.disabled = false; button.textContent = 'Evaluate risk'; }
  };
}

async function renderNavigation() {
  const history = await api('/navigation/history');
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Mobility</p><h2>Navigation</h2><p>Only a configured routing provider can return walking directions.</p></div></div><section class="grid-two"><article class="panel"><h3>Request a provider route</h3><form id="navigation-form"><label>Destination name<input name="destination" required placeholder="Hospital"></label><div class="form-grid"><label>Current latitude<input name="origin_latitude" type="number" step="any" min="-90" max="90"></label><label>Current longitude<input name="origin_longitude" type="number" step="any" min="-180" max="180"></label><label>Destination latitude<input name="destination_latitude" type="number" step="any" min="-90" max="90"></label><label>Destination longitude<input name="destination_longitude" type="number" step="any" min="-180" max="180"></label></div><button class="primary-button" type="submit">Get provider route</button></form></article><article class="panel"><h3>Route result</h3><div id="route-result">${empty('No route requested.')}</div></article></section><section class="panel"><h3>Saved provider routes</h3>${history.length ? `<ul class="list">${history.map(route => `<li><strong>${escapeHtml(route.destination)}</strong><br><small>${route.total_distance_m} m · ${escapeHtml(route.navigation_status)} · ${dateText(route.created_at)}</small></li>`).join('')}</ul>` : empty('No provider-backed routes have been saved.')}</section>`;
  $('#navigation-form').onsubmit = async event => {
    event.preventDefault(); const raw = Object.fromEntries(new FormData(event.target)); const body = { destination: raw.destination };
    ['origin_latitude', 'origin_longitude', 'destination_latitude', 'destination_longitude'].forEach(key => { if (raw[key] !== '') body[key] = Number(raw[key]); });
    try { const route = await api('/navigation/route', { method: 'POST', body: JSON.stringify(body) }); $('#route-result').innerHTML = `<p>${tag('PROVIDER ROUTE')}</p><p><strong>${escapeHtml(route.destination)}</strong> · ${route.total_distance_m} m · ${route.estimated_time_minutes} min</p><ol>${route.steps.map(step => `<li>${escapeHtml(step.instruction)} (${step.distance_m} m)</li>`).join('')}</ol>`; }
    catch (error) { $('#route-result').innerHTML = empty(error.message); }
  };
}

async function renderSos() {
  const [overview, history] = await Promise.all([api('/dashboard/overview'), api('/emergency/history')]); const active = overview.active_sos;
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Emergency assistance</p><h2>Emergency SOS</h2><p>Use only when help is needed. The application records configured delivery attempts separately.</p></div></div><section class="panel sos-panel"><h3>${active ? 'Active emergency alert' : 'Activate emergency SOS'}</h3>${active ? `<p>${tag(active.status)} Alert #${active.id} started ${dateText(active.created_at)}</p><button id="cancel-sos" class="secondary-button" type="button">Cancel active alert</button>` : `<p>Location is included only when the browser provides it. This application never invents coordinates.</p><button id="activate-sos" class="danger-button" type="button">Activate SOS</button>`}</section><section class="panel"><h3>Emergency history</h3>${history.length ? `<table class="data-table"><thead><tr><th>Type</th><th>Status</th><th>Started</th><th>Location</th></tr></thead><tbody>${history.map(event => `<tr><td>${escapeHtml(event.event_type)}</td><td>${tag(event.status)}</td><td>${dateText(event.created_at)}</td><td>${event.latitude == null ? 'Unavailable' : `${event.latitude}, ${event.longitude}`}</td></tr>`).join('')}</tbody></table>` : empty('No emergency events recorded.')}</section>`;
  if (active) $('#cancel-sos').onclick = async () => { await api('/emergency/cancel', { method: 'POST', body: JSON.stringify({ emergency_id: active.id }) }); notify('Emergency alert cancelled.'); renderSos(); };
  else $('#activate-sos').onclick = openSosConfirmation;
}
function openSosConfirmation() { const dialog = $('#sos-dialog'); if (typeof dialog.showModal === 'function') dialog.showModal(); else if (confirm('Activate an SOS emergency alert?')) activateSos(); }
async function activateSos() {
  let latitude = null, longitude = null;
  if (navigator.geolocation) {
    try { const position = await new Promise((resolve, reject) => navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 8000, enableHighAccuracy: true })); latitude = position.coords.latitude; longitude = position.coords.longitude; }
    catch (_) { notify('Location was unavailable. The SOS alert will record no location.'); }
  }
  try { await api('/emergency/trigger', { method: 'POST', body: JSON.stringify({ event_type: 'MANUAL_SOS', latitude, longitude }) }); notify('SOS alert created.'); renderSos(); }
  catch (error) { notify(error.message); }
}

async function renderContacts() {
  const contacts = await api('/contacts');
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Safety network</p><h2>Emergency contacts</h2><p>Only contacts in your account can receive an emergency notification attempt.</p></div></div><section class="grid-two"><article class="panel"><h3>Your contacts</h3>${contacts.length ? `<ul class="list">${contacts.map(contact => `<li><div class="list-row"><strong>${escapeHtml(contact.name)}</strong><button class="link-button" data-delete-contact="${contact.id}" type="button">Remove</button></div><small>${escapeHtml(contact.relationship_type)} · ${escapeHtml(contact.phone_number)}${contact.email ? ` · ${escapeHtml(contact.email)}` : ''}</small></li>`).join('')}</ul>` : empty('No emergency contacts added.')}</article><article class="panel"><h3>Add emergency contact</h3><form id="contact-form"><label>Name<input name="name" required></label><label>Relationship<input name="relationship_type" required placeholder="Family or caregiver"></label><label>Phone number<input name="phone_number" required></label><label>Email (optional)<input name="email" type="email"></label><button class="primary-button" type="submit">Add contact</button></form></article></section>`;
  $('#contact-form').onsubmit = async event => { event.preventDefault(); const value = Object.fromEntries(new FormData(event.target)); await api('/contacts', { method: 'POST', body: JSON.stringify(value) }); notify('Emergency contact added.'); renderContacts(); };
  document.querySelectorAll('[data-delete-contact]').forEach(button => button.onclick = async () => { if (confirm('Remove this emergency contact?')) { await api(`/contacts/${button.dataset.deleteContact}`, { method: 'DELETE' }); renderContacts(); } });
}

async function renderDevices() {
  const devices = await api('/devices'); setDeviceStatus(devices);
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Hardware</p><h2>Device & settings</h2><p>Register and manage only smart canes associated with your account.</p></div></div><section class="grid-two"><article class="panel"><h3>Registered smart canes</h3>${devices.length ? `<ul class="list">${devices.map(device => `<li><div class="list-row"><strong>${escapeHtml(device.device_name)}</strong><button class="link-button" data-delete-device="${device.id}" type="button">Remove</button></div><small>${escapeHtml(device.device_id)} · ${tag(device.connection_status)} · Battery: ${device.battery_percent ?? 'unavailable'}%<br>${device.is_simulator ? 'Simulator — not physical hardware' : 'Hardware device'} · Sensor health: ${escapeHtml(device.sensor_health)}</small></li>`).join('')}</ul>` : empty('No device registered.')}</article><article class="panel"><h3>Register smart cane</h3><form id="device-form"><label>Device ID<input name="device_id" required minlength="3" maxlength="64" placeholder="ECHO_CANE_001"></label><label>Display name<input name="device_name" value="ECHO-CANE" required></label><label>Firmware version (optional)<input name="firmware_version" maxlength="20"></label><label class="switch-row">This is a development simulator, not physical hardware<input name="is_simulator" type="checkbox"></label><button class="primary-button" type="submit">Register device</button></form></article></section>`;
  $('#device-form').onsubmit = async event => { event.preventDefault(); const raw = new FormData(event.target); await api('/devices', { method: 'POST', body: JSON.stringify({ device_id: raw.get('device_id'), device_name: raw.get('device_name'), firmware_version: raw.get('firmware_version') || null, is_simulator: raw.get('is_simulator') === 'on' }) }); notify('Device registered.'); renderDevices(); };
  document.querySelectorAll('[data-delete-device]').forEach(button => button.onclick = async () => { if (confirm('Remove this device and its sensor history?')) { await api(`/devices/${button.dataset.deleteDevice}`, { method: 'DELETE' }); renderDevices(); } });
}

async function renderSensors() {
  const readings = await api('/sensors/history');
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Hardware data</p><h2>Sensor history</h2><p>Recent sensor packets stored for your registered devices.</p></div><div class="page-heading-actions"><button id="refresh-sensors" class="secondary-button" type="button">Refresh</button></div></div><section class="panel">${readings.length ? `<table class="data-table"><thead><tr><th>Received</th><th>Ultrasonic</th><th>ToF</th><th>Battery</th><th>SOS</th><th>Accelerometer</th></tr></thead><tbody>${readings.map(reading => `<tr><td>${dateText(reading.device_timestamp || reading.received_at)}</td><td>${reading.ultrasonic_cm ?? '—'} cm</td><td>${reading.tof_mm ?? '—'} mm</td><td>${reading.battery_percent ?? '—'}%</td><td>${reading.sos_pressed ? 'Pressed' : 'Not pressed'}</td><td>${reading.accel_x ?? '—'}, ${reading.accel_y ?? '—'}, ${reading.accel_z ?? '—'}</td></tr>`).join('')}</tbody></table>` : empty('No sensor history is available for this account.')}</section>`;
  $('#refresh-sensors').onclick = renderSensors;
}

async function renderNotifications() {
  const [notifications, emergency, detections] = await Promise.all([api('/notifications'), optional('/emergency/history'), optional('/ai/history')]);
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Alerts & history</p><h2>Alerts & history</h2><p>Provider outcomes are shown as recorded; a notification attempt is not treated as confirmation.</p></div></div><section class="grid-three"><article class="panel"><h3>Notifications</h3>${notifications.length ? `<ul class="list">${notifications.slice(0, 8).map(item => `<li><strong>${escapeHtml(item.title)}</strong><br><small>${escapeHtml(item.channel)} · ${escapeHtml(item.status)} · ${dateText(item.created_at)}</small></li>`).join('')}</ul>` : empty('No notification attempts are recorded.')}</article><article class="panel"><h3>Emergency events</h3>${emergency?._error ? empty('Emergency history is unavailable.') : emergency.length ? `<ul class="list">${emergency.slice(0, 8).map(item => `<li><strong>${escapeHtml(item.event_type)}</strong><br><small>${escapeHtml(item.status)} · ${dateText(item.created_at)}</small></li>`).join('')}</ul>` : empty('No emergency events are recorded.')}</article><article class="panel"><h3>Obstacle events</h3>${detections?._error ? empty('Detection history is unavailable.') : detections.length ? `<ul class="list">${detections.slice(0, 8).map(item => `<li><strong>${escapeHtml(item.class_name)}</strong><br><small>${Math.round(item.confidence * 100)}% · ${dateText(item.created_at)}</small></li>`).join('')}</ul>` : empty('No obstacles have been recorded.')}</article></section>`;
}

async function renderAnalytics() {
  const [sensors, detections, emergency, riskHistory, devices] = await Promise.all([optional('/sensors/history'), optional('/ai/history'), optional('/emergency/history'), optional('/ai/risk/history'), optional('/devices')]);
  const sensorRows = Array.isArray(sensors) ? sensors : []; const detectionRows = Array.isArray(detections) ? detections : []; const emergencyRows = Array.isArray(emergency) ? emergency : []; const riskRows = Array.isArray(riskHistory) ? riskHistory : [];
  setDeviceStatus(Array.isArray(devices) ? devices : []);
  const bars = sensorRows.slice(0, 12).reverse().map(row => { const raw = Number(row.battery_percent); const height = Number.isFinite(raw) ? Math.max(5, Math.min(100, raw)) : 5; return `<i style="height:${height}%" title="Battery ${Number.isFinite(raw) ? `${raw}%` : 'unavailable'}"></i>`; }).join('');
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Account reports</p><h2>Reports & analytics</h2><p>Account-scoped totals and patterns derived from real stored events. Empty data remains empty.</p></div></div><section class="analytics-summary"><article class="metric"><small>Sensor packets</small><strong>${sensorRows.length}</strong></article><article class="metric"><small>Obstacle events</small><strong>${detectionRows.length}</strong></article><article class="metric ${emergencyRows.some(item => /active/i.test(item.status)) ? 'danger' : 'safe'}"><small>Emergency events</small><strong>${emergencyRows.length}</strong></article><article class="metric ${riskRows.some(item => item.risk_level === 'DANGER') ? 'danger' : riskRows.some(item => item.risk_level === 'WARNING') ? 'warning' : 'safe'}"><small>Risk evaluations</small><strong>${riskRows.length}</strong></article></section><section class="grid-two"><article class="panel"><div class="card-title"><span class="feature-icon">G</span><div><h3>Battery history</h3><p class="panel-subtitle">Latest ${sensorRows.length} stored packets</p></div></div>${sensorRows.length ? `<div class="history-bars" aria-label="Battery levels from recent sensor packets">${bars}</div><div class="chart-note"><span>Oldest displayed</span><span>Latest displayed</span></div>` : `<div class="status-empty"><div><span class="feature-icon">S</span>${empty('No sensor packets are available for a battery chart.')}</div></div>`}</article><article class="panel"><div class="card-title"><span class="feature-icon">R</span><div><h3>Risk distribution</h3><p class="panel-subtitle">Recorded risk evaluations</p></div></div>${riskRows.length ? `<ul class="list"><li><div class="list-row"><span>Safe</span><strong>${riskRows.filter(row => row.risk_level === 'SAFE').length}</strong></div></li><li><div class="list-row"><span>Warning</span><strong>${riskRows.filter(row => row.risk_level === 'WARNING').length}</strong></div></li><li><div class="list-row"><span>Danger</span><strong>${riskRows.filter(row => row.risk_level === 'DANGER').length}</strong></div></li></ul>` : empty('No risk evaluations are available.')}</article></section><section class="panel"><h3>Recent risk evaluations</h3>${riskRows.length ? `<table class="data-table"><thead><tr><th>Object</th><th>Distance</th><th>Direction</th><th>Risk</th><th>Recorded</th></tr></thead><tbody>${riskRows.slice(0, 12).map(row => `<tr><td>${escapeHtml(row.object_name)}</td><td>${decimal(row.fused_distance_m, 1)} m</td><td>${escapeHtml(row.direction)}</td><td>${tag(row.risk_level)}</td><td>${dateText(row.created_at)}</td></tr>`).join('')}</tbody></table>` : empty('No risk evaluations have been recorded.')}</section>`;
}

async function renderProfile() {
  const profile = await api('/user/profile');
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Account</p><h2>User profile</h2><p>Update the information associated with your account.</p></div></div><section class="panel"><p>${tag(profile.is_verified ? 'EMAIL VERIFIED' : 'EMAIL NOT VERIFIED')}</p>${profile.is_verified ? '' : '<button id="request-verification" class="secondary-button" type="button">Send verification email</button>'}<form id="profile-form"><div class="form-grid"><label>Full name<input name="full_name" required value="${escapeHtml(profile.full_name)}"></label><label>Phone number<input name="phone_number" value="${escapeHtml(profile.phone_number || '')}"></label><label>Date of birth<input name="date_of_birth" type="date" value="${escapeHtml(profile.date_of_birth || '')}"></label><label>Profile photo URL<input name="profile_photo_url" type="url" value="${escapeHtml(profile.profile_photo_url || '')}"></label><label class="full">Address<input name="address" value="${escapeHtml(profile.address || '')}"></label><label class="full">Medical/accessibility preferences<input name="medical_accessibility_preferences" value="${escapeHtml(profile.medical_accessibility_preferences || '')}"></label></div><button class="primary-button" type="submit">Save profile</button></form></section>`;
  $('#profile-form').onsubmit = async event => { event.preventDefault(); await api('/user/profile', { method: 'PUT', body: JSON.stringify(Object.fromEntries(new FormData(event.target))) }); state.user = await api('/user/profile'); updateAccountChrome(); notify('Profile saved.'); renderProfile(); };
  const verify = $('#request-verification'); if (verify) verify.onclick = async () => { const result = await api('/auth/request-email-verification', { method: 'POST', body: '{}' }); notify(result.detail); };
}

async function renderSettings() {
  const settings = await api('/devices/preferences/me');
  content.innerHTML = `<div class="page-heading"><div><p class="eyebrow">Accessibility</p><h2>Accessibility settings</h2><p>Preferences are stored in your account.</p></div></div><section class="panel"><form id="settings-form"><label>Language<select name="language"><option value="en">English</option><option value="hi">Hindi</option><option value="te">Telugu</option></select></label>${[['voice_alerts_enabled', 'Enable voice alerts'], ['vibration_alerts_enabled', 'Enable vibration alerts'], ['high_contrast_mode', 'Use high contrast'], ['large_text_mode', 'Use large text'], ['fall_detection_enabled', 'Enable fall detection']].map(([name, label]) => `<label class="switch-row">${label}<input name="${name}" type="checkbox" ${settings[name] ? 'checked' : ''}></label>`).join('')}<label>Fall-alert cancellation time (seconds)<input name="fall_detection_countdown_seconds" type="number" min="5" max="120" value="${settings.fall_detection_countdown_seconds}"></label><button class="primary-button" type="submit">Save settings</button></form></section>`;
  $('#settings-form').language.value = settings.language;
  $('#settings-form').onsubmit = async event => { event.preventDefault(); const form = new FormData(event.target); const body = { language: form.get('language'), fall_detection_countdown_seconds: Number(form.get('fall_detection_countdown_seconds')) }; ['voice_alerts_enabled', 'vibration_alerts_enabled', 'high_contrast_mode', 'large_text_mode', 'fall_detection_enabled'].forEach(name => body[name] = form.get(name) === 'on'); await api('/devices/preferences/me', { method: 'PUT', body: JSON.stringify(body) }); notify('Settings saved.'); };
}

function setButtonBusy(button, busy, text) { button.disabled = busy; if (text) button.textContent = text; }
async function submitAuthentication(event, endpoint) {
  event.preventDefault(); if (state.authInFlight) return; const form = event.currentTarget;
  if (!form.reportValidity()) return;
  const data = Object.fromEntries(new FormData(form));
  if (endpoint === '/auth/register' && data.password !== data.confirm_password) return notify('Password confirmation does not match.');
  delete data.confirm_password; state.authInFlight = true;
  const button = form.querySelector('button[type="submit"]'); const text = button.textContent; setButtonBusy(button, true, 'Please wait…');
  try { await finishAuthentication(await api(endpoint, { method: 'POST', body: JSON.stringify(data) })); }
  catch (error) { notify(error.message); }
  finally { state.authInFlight = false; setButtonBusy(button, false, text); }
}

$('#skip-intro').onclick = leaveIntro;
const skipVideoIntroBtn = $('#skip-video-intro');
if (skipVideoIntroBtn) skipVideoIntroBtn.onclick = finishVideoIntro;
const authReplayBtn = $('#auth-replay-video-btn');
if (authReplayBtn) authReplayBtn.onclick = () => playVideoIntro();
const navReplayBtn = $('#nav-replay-btn');
if (navReplayBtn) navReplayBtn.onclick = () => playVideoIntro();
const heroReplayBtn = $('#hero-replay-btn');
if (heroReplayBtn) heroReplayBtn.onclick = () => playVideoIntro();
const sidebarReplayBtn = $('#sidebar-replay-btn');
if (sidebarReplayBtn) sidebarReplayBtn.onclick = () => playVideoIntro();
const videoIntroShell = $('#video-intro-shell');
if (videoIntroShell) {
  videoIntroShell.onclick = finishVideoIntro;
}
$('#login-tab').onclick = () => setAuthTab('login'); $('#register-tab').onclick = () => setAuthTab('register');
$('#login-form').onsubmit = event => submitAuthentication(event, '/auth/login'); $('#register-form').onsubmit = event => submitAuthentication(event, '/auth/register');
document.querySelectorAll('[data-toggle-password]').forEach(button => button.onclick = () => { const input = button.previousElementSibling; input.type = input.type === 'password' ? 'text' : 'password'; const hide = input.type === 'text'; button.textContent = hide ? 'Hide' : 'Show'; button.setAttribute('aria-label', hide ? 'Hide password' : 'Show password'); });
$('#forgot-password').onclick = async () => { const email = prompt('Enter your account email address.'); if (!email) return; try { const result = await api('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }); notify(result.detail); } catch (error) { notify(error.message); } };
$('#reset-form').onsubmit = async event => { event.preventDefault(); try { await api('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token: event.currentTarget.dataset.token, new_password: new FormData(event.currentTarget).get('new_password') }) }); history.replaceState({}, '', location.pathname); notify('Password reset. Sign in with your new password.'); showAuth(); } catch (error) { notify(error.message); } };
$('#verify-form').onsubmit = async event => { event.preventDefault(); try { const result = await api('/auth/verify-email', { method: 'POST', body: JSON.stringify({ token: event.currentTarget.dataset.token }) }); history.replaceState({}, '', location.pathname); notify(result.detail); showAuth(); } catch (error) { notify(error.message); } };
document.querySelectorAll('[data-page]').forEach(button => button.onclick = () => setPage(button.dataset.page));
$('#menu-button').onclick = () => { const app = $('#app-shell'); const open = !app.classList.contains('nav-open'); app.classList.toggle('nav-open', open); $('#menu-button').setAttribute('aria-expanded', String(open)); $('#nav-backdrop').hidden = !open; };
$('#close-menu-button').onclick = () => { $('#app-shell').classList.remove('nav-open'); $('#menu-button').setAttribute('aria-expanded', 'false'); $('#nav-backdrop').hidden = true; };
$('#nav-backdrop').onclick = () => $('#close-menu-button').click();
$('#sos-dialog').addEventListener('close', () => { if ($('#sos-dialog').returnValue === 'confirm') activateSos(); });
$('#logout-button').onclick = async () => { try { if (state.refreshToken) await api('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: state.refreshToken }) }); } finally { clearSession(); showAuth(); notify('You have been signed out.'); } };
const closeAuth = $('#close-auth-btn'); if (closeAuth) closeAuth.onclick = () => { if (state.accessToken) showApp(); else showLanding(); };
document.querySelectorAll('.brand-lockup').forEach(b => {
  b.onclick = e => {
    e.preventDefault();
    if (state.accessToken) showApp(); else showLanding();
  };
});
const sidebarLanding = $('#sidebar-landing-btn'); if (sidebarLanding) sidebarLanding.onclick = () => showLanding();
const handleCta = () => { if (state.accessToken) showApp(); else showAuth('register'); };
const navCta = $('#nav-cta-btn'); if (navCta) navCta.onclick = handleCta;
const heroCta = $('#hero-cta-btn'); if (heroCta) heroCta.onclick = handleCta;

const play3dIntro = () => {
  hideIntro();
  const authShell = $('#auth-shell'); if (authShell) authShell.hidden = true;
  const appShell = $('#app-shell'); if (appShell) appShell.hidden = true;
  const landing = $('#saas-landing'); if (landing) landing.hidden = true;
  const nav = $('#saas-nav'); if (nav) nav.hidden = true;
  $('#intro-shell').hidden = false;
  if (window.EchoCinematicIntro) {
    state.introController = new window.EchoCinematicIntro($('#intro-shell'), {
      onLoginEnter: prepareNextScreen,
      onLoginReady: () => { const a = $('#auth-shell'); if (a) a.classList.remove('is-entering'); },
      onFinish: completeIntro,
    });
    state.introController.start();
  }
};
const nav3d = $('#nav-3d-btn'); if (nav3d) nav3d.onclick = play3dIntro;
const hero3d = $('#hero-3d-btn'); if (hero3d) hero3d.onclick = play3dIntro;

const emailForm = $('#landing-email-form');
if (emailForm) {
  emailForm.onsubmit = event => {
    event.preventDefault();
    const email = $('#landing-email-input')?.value.trim();
    showAuth('register');
    const regEmail = $('#register-form')?.querySelector('input[name="email"]');
    if (regEmail && email) regEmail.value = email;
  };
}

document.querySelectorAll('[data-plan]').forEach(button => {
  button.onclick = () => showAuth('register');
});

const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.05, rootMargin: '0px 0px 50px 0px' });
document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));
window.addEventListener('scroll', () => {
  document.querySelectorAll('.reveal:not(.visible)').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.top < window.innerHeight + 100) el.classList.add('visible');
  });
}, { passive: true });

beginExperience();
