const state = {
  accessToken: sessionStorage.getItem('echo_access'),
  refreshToken: sessionStorage.getItem('echo_refresh'),
  user: null,
  page: 'dashboard',
  refreshInFlight: null,
  authInFlight: false,
};

const $ = selector => document.querySelector(selector);
const content = $('#page-content');
const pageNames = {
  dashboard: ['Workspace', 'Dashboard'], monitoring: ['Awareness', 'Live monitoring'],
  detection: ['Awareness', 'AI obstacle detection'], risk: ['Awareness', 'Risk prediction'],
  navigation: ['Mobility', 'Navigation'], sos: ['Safety', 'Emergency SOS'],
  contacts: ['Safety', 'Emergency contacts'], devices: ['Hardware', 'Device management'],
  sensors: ['Hardware', 'Sensor history'], notifications: ['Activity', 'Notifications'],
  profile: ['Account', 'User profile'], settings: ['Account', 'Settings'],
};

function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[char]); }
function dateText(value) { return value ? new Date(value).toLocaleString() : 'Not available'; }
function empty(text) { return `<p class="empty">${escapeHtml(text)}</p>`; }
function tag(value) { const safe = escapeHtml(value || 'unavailable'); const css = /danger|active|critical|not_delivered/i.test(value) ? 'danger' : /warning|pending/i.test(value) ? 'warning' : !value ? 'muted' : ''; return `<span class="tag ${css}">${safe}</span>`; }
function notify(message) { const toast = $('#toast'); toast.textContent = message; toast.hidden = false; clearTimeout(notify.timer); notify.timer = setTimeout(() => { toast.hidden = true; }, 5000); }
function tokensAreValid(tokens) { return Boolean(tokens?.access_token && tokens?.refresh_token && tokens.token_type === 'bearer'); }

function saveTokens(tokens) {
  if (!tokensAreValid(tokens)) throw new Error('The server returned an invalid authentication response.');
  state.accessToken = tokens.access_token; state.refreshToken = tokens.refresh_token;
  sessionStorage.setItem('echo_access', state.accessToken); sessionStorage.setItem('echo_refresh', state.refreshToken);
}
function clearSession() { state.accessToken = null; state.refreshToken = null; state.user = null; sessionStorage.removeItem('echo_access'); sessionStorage.removeItem('echo_refresh'); }

async function refreshSession() {
  if (!state.refreshToken) return false;
  if (!state.refreshInFlight) {
    state.refreshInFlight = (async () => {
      const response = await fetch('/auth/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: state.refreshToken }) });
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
  if (response.status === 401 && !authPath) { clearSession(); showAuth(); throw new Error('Your session expired. Please sign in again.'); }
  const body = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 429) throw new Error('Too many requests. Please wait a minute before trying again.');
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}).`);
  }
  return body;
}

async function optional(path) { try { return await api(path); } catch (error) { return { _error: error.message }; } }
function setAuthTab(mode) {
  const login = mode === 'login';
  $('#login-tab').classList.toggle('active', login); $('#register-tab').classList.toggle('active', !login);
  $('#login-tab').setAttribute('aria-selected', String(login)); $('#register-tab').setAttribute('aria-selected', String(!login));
  $('#login-form').hidden = !login; $('#register-form').hidden = login; $('#reset-form').hidden = true; $('#verify-form').hidden = true;
}
function showAuth() { $('#app-shell').hidden = true; $('#auth-shell').hidden = false; setAuthTab('login'); }
function showApp() {
  $('#auth-shell').hidden = true; $('#app-shell').hidden = false;
  $('#account-name').textContent = state.user.full_name || 'ECHO-ASSIST user'; $('#account-email').textContent = state.user.email || '';
  $('#account-initial').textContent = (state.user.full_name || 'E').trim().charAt(0).toUpperCase(); renderPage();
}
async function finishAuthentication(tokens) {
  saveTokens(tokens);
  state.user = await api('/user/profile');
  state.page = 'dashboard';
  location.hash = 'dashboard';
  showApp();
}
async function bootstrap() { if (!state.accessToken) return showAuth(); try { state.user = await api('/user/profile'); showApp(); } catch (_) { showAuth(); } }

function setPage(page) { state.page = page; location.hash = page; $('#app-shell').classList.remove('nav-open'); renderPage(); }
async function renderPage() {
  const [kicker, title] = pageNames[state.page] || pageNames.dashboard; $('#page-kicker').textContent = kicker; $('#page-title').textContent = title;
  document.querySelectorAll('#sidebar-nav button').forEach(button => button.classList.toggle('active', button.dataset.page === state.page));
  content.innerHTML = '<div class="loading">Loading your information…</div>';
  try { await ({ dashboard: renderDashboard, monitoring: renderMonitoring, detection: renderDetection, risk: renderRisk, navigation: renderNavigation, sos: renderSos, contacts: renderContacts, devices: renderDevices, sensors: renderSensors, notifications: renderNotifications, profile: renderProfile, settings: renderSettings }[state.page] || renderDashboard)(); }
  catch (error) { content.innerHTML = `<section class="panel"><h3>Could not load this page</h3><p class="empty">${escapeHtml(error.message)}</p><button id="retry-page" class="secondary-button" type="button">Try again</button></section>`; $('#retry-page').onclick = renderPage; }
}

async function renderDashboard() {
  const [overview, notifications, detections] = await Promise.all([api('/dashboard/overview'), optional('/notifications'), optional('/ai/history')]);
  const reading = overview.latest_sensor_reading, risk = overview.latest_risk, sos = overview.active_sos;
  const activity = [
    ...(Array.isArray(notifications) ? notifications.slice(0, 3).map(item => ({ title: item.title, detail: item.status, at: item.created_at })) : []),
    ...(Array.isArray(detections) ? detections.slice(0, 2).map(item => ({ title: `${item.class_name} detected`, detail: `${Math.round((item.confidence || 0) * 100)}% confidence`, at: item.created_at })) : []),
  ].sort((a, b) => new Date(b.at) - new Date(a.at)).slice(0, 5);
  content.innerHTML = `<div class="page-heading"><div><h2>Welcome${state.user?.full_name ? `, ${escapeHtml(state.user.full_name.split(' ')[0])}` : ''}</h2><p>Here is the latest information from your ECHO-ASSIST account.</p></div><button class="secondary-button" id="refresh-dashboard" type="button">Refresh data</button></div><section class="metric-grid"><article class="metric"><small>Smart canes connected</small><strong>${overview.connected_devices}/${overview.device_count}</strong></article><article class="metric"><small>Latest battery</small><strong>${reading?.battery_percent == null ? '—' : `${reading.battery_percent}%`}</strong></article><article class="metric ${risk?.risk_level === 'DANGER' ? 'danger' : 'safe'}"><small>Current AI risk</small><strong>${escapeHtml(risk?.risk_level || 'No risk')}</strong></article><article class="metric ${sos ? 'danger' : 'safe'}"><small>Emergency SOS</small><strong>${sos ? escapeHtml(sos.status) : 'Inactive'}</strong></article></section><section class="grid-two"><article class="panel"><h3>Smart cane status</h3>${overview.devices.length ? `<ul class="list">${overview.devices.map(device => `<li><div class="list-row"><strong>${escapeHtml(device.device_name)}</strong>${tag(device.connection_status)}</div><small>${escapeHtml(device.device_id)} · ${device.is_simulator ? 'Simulator — not physical hardware' : 'Registered hardware'} · Battery ${device.battery_percent ?? 'unavailable'}%</small></li>`).join('')}</ul>` : empty('No smart cane is registered yet.')}</article><article class="panel"><h3>Latest assistance status</h3>${risk ? `<p>${tag(risk.risk_level)}</p><p>${escapeHtml(risk.message || 'No voice message recorded.')}</p><small>${dateText(risk.created_at)}</small>` : empty('No obstacle risk has been recorded.')}</article><article class="panel"><h3>Emergency status</h3>${sos ? `<p>${tag(sos.status)}</p><p>Alert #${sos.id} started ${dateText(sos.created_at)}</p><button class="secondary-button" data-go="sos" type="button">Open SOS</button>` : `<p class="muted">No active emergency alert.</p><button class="danger-button" data-go="sos" type="button">Open SOS controls</button>`}</article><article class="panel"><h3>Recent activity</h3>${activity.length ? `<ul class="list">${activity.map(item => `<li><strong>${escapeHtml(item.title)}</strong><br><small>${escapeHtml(item.detail)} · ${dateText(item.at)}</small></li>`).join('')}</ul>` : empty('No recent account activity.')}</article></section>`;
  $('#refresh-dashboard').onclick = renderDashboard; bindGoLinks();
}

async function renderMonitoring() {
  const [latest, fusion, devices] = await Promise.all([optional('/sensors/latest'), optional('/sensors/fusion/latest'), api('/devices')]);
  const unavailable = value => value?._error ? 'Unavailable' : value;
  content.innerHTML = `<div class="page-heading"><div><h2>Live monitoring</h2><p>Displays the latest stored sensor packet. It does not claim live hardware when none is connected.</p></div><button class="secondary-button" id="refresh-monitoring" type="button">Refresh</button></div><section class="metric-grid"><article class="metric"><small>Ultrasonic distance</small><strong>${latest?._error ? '—' : `${latest.ultrasonic_cm ?? '—'} cm`}</strong></article><article class="metric"><small>ToF distance</small><strong>${latest?._error ? '—' : `${latest.tof_mm ?? '—'} mm`}</strong></article><article class="metric"><small>Battery</small><strong>${latest?._error ? '—' : `${latest.battery_percent ?? '—'}%`}</strong></article><article class="metric"><small>Fused distance</small><strong>${fusion?._error ? '—' : escapeHtml(String(fusion.fusion?.distance_m ?? '—'))}</strong></article></section><section class="grid-two"><article class="panel"><h3>Latest sensor packet</h3>${latest?._error ? empty('No sensor data is available yet.') : `<table class="data-table"><tbody><tr><th>Received</th><td>${dateText(latest.device_timestamp)}</td></tr><tr><th>SOS button</th><td>${latest.sos_pressed ? 'Pressed' : 'Not pressed'}</td></tr><tr><th>Accelerometer</th><td>${latest.accel_x ?? '—'}, ${latest.accel_y ?? '—'}, ${latest.accel_z ?? '—'}</td></tr><tr><th>Gyroscope</th><td>${latest.gyro_x ?? '—'}, ${latest.gyro_y ?? '—'}, ${latest.gyro_z ?? '—'}</td></tr></tbody></table>`}</article><article class="panel"><h3>Connection overview</h3>${devices.length ? `<ul class="list">${devices.map(device => `<li><strong>${escapeHtml(device.device_name)}</strong><br><small>${tag(device.connection_status)} Sensor health: ${escapeHtml(device.sensor_health)}</small></li>`).join('')}</ul>` : empty('No device has been registered.')}</article></section>`;
  $('#refresh-monitoring').onclick = renderMonitoring;
}

async function renderDetection() {
  const history = await optional('/ai/history');
  content.innerHTML = `<div class="page-heading"><div><h2>AI obstacle detection</h2><p>Runs the configured detection service. Results are labelled when the service is in mock or unavailable mode.</p></div></div><section class="grid-two"><article class="panel"><h3>Run object detection</h3><p class="muted">This action uses the existing backend detection service; it does not invent detections in the UI.</p><button id="run-detection" class="primary-button" type="button">Run configured detection</button><div id="detection-result"></div></article><article class="panel"><h3>Detection history</h3>${history?._error ? empty('No detection history is available.') : history.length ? `<ul class="list">${history.map(row => `<li><strong>${escapeHtml(row.class_name)}</strong> · ${Math.round((row.confidence || 0) * 100)}%<br><small>${escapeHtml(row.position || 'unknown position')} · ${dateText(row.created_at)}</small></li>`).join('')}</ul>` : empty('No detections are stored yet.')}</article></section>`;
  $('#run-detection').onclick = async event => { const button = event.currentTarget; button.disabled = true; button.textContent = 'Running…'; try { const result = await api('/ai/detect', { method: 'POST', body: JSON.stringify({ use_mock: false }) }); $('#detection-result').innerHTML = `<p>${tag(result.mock_mode ? 'SIMULATED SERVICE' : 'MODEL RESULT')}</p>${result.detections.length ? `<ul class="list">${result.detections.map(item => `<li><strong>${escapeHtml(item.class_name)}</strong> · ${Math.round(item.confidence * 100)}% · ${escapeHtml(item.position)}</li>`).join('')}</ul>` : empty('No objects were returned by the configured service.')}`; } catch (error) { $('#detection-result').innerHTML = empty(error.message); } finally { button.disabled = false; button.textContent = 'Run configured detection'; } };
}

async function renderRisk() {
  content.innerHTML = `<div class="page-heading"><div><h2>Risk prediction</h2><p>Evaluate a measured or fused obstacle distance through the existing risk API.</p></div></div><section class="grid-two"><article class="panel"><h3>Evaluate obstacle risk</h3><form id="risk-form"><label>Object type<input name="object_name" required placeholder="pole"></label><div class="form-grid"><label>Fused distance (metres)<input name="fused_distance_m" type="number" min="0" step="0.1" required></label><label>Direction<select name="direction"><option value="center">Center</option><option value="left">Left</option><option value="right">Right</option></select></label></div><label><input name="is_approaching" type="checkbox"> Object is approaching</label><button class="primary-button" type="submit">Evaluate risk</button></form></article><article class="panel"><h3>Risk result</h3><div id="risk-result">${empty('Submit a real measurement to evaluate risk.')}</div></article></section>`;
  $('#risk-form').onsubmit = async event => { event.preventDefault(); const raw = Object.fromEntries(new FormData(event.target)); const result = await api('/ai/risk', { method: 'POST', body: JSON.stringify({ object_name: raw.object_name, fused_distance_m: Number(raw.fused_distance_m), direction: raw.direction, is_approaching: raw.is_approaching === 'on' }) }); $('#risk-result').innerHTML = `<p>${tag(result.risk_level)}</p><p><strong>${escapeHtml(result.object_name)}</strong> at ${result.fused_distance_m} metres</p><p>${escapeHtml(result.message || 'No alert message required.')}</p><small>Vibration pattern: ${escapeHtml(result.vibration_pattern)}</small>`; };
}

async function renderNavigation() {
  const history = await api('/navigation/history');
  content.innerHTML = `<div class="page-heading"><div><h2>Navigation</h2><p>Only a configured routing provider can return walking directions.</p></div></div><section class="grid-two"><article class="panel"><h3>Request a provider route</h3><form id="navigation-form"><label>Destination name<input name="destination" required placeholder="Hospital"></label><div class="form-grid"><label>Current latitude<input name="origin_latitude" type="number" step="any" min="-90" max="90"></label><label>Current longitude<input name="origin_longitude" type="number" step="any" min="-180" max="180"></label><label>Destination latitude<input name="destination_latitude" type="number" step="any" min="-90" max="90"></label><label>Destination longitude<input name="destination_longitude" type="number" step="any" min="-180" max="180"></label></div><button class="primary-button" type="submit">Get provider route</button></form></article><article class="panel"><h3>Route result</h3><div id="route-result">${empty('No route requested.')}</div></article></section><section class="panel"><h3>Saved provider routes</h3>${history.length ? `<ul class="list">${history.map(route => `<li><strong>${escapeHtml(route.destination)}</strong><br><small>${route.total_distance_m} m · ${escapeHtml(route.navigation_status)} · ${dateText(route.created_at)}</small></li>`).join('')}</ul>` : empty('No provider-backed routes have been saved.')}</section>`;
  $('#navigation-form').onsubmit = async event => { event.preventDefault(); const raw = Object.fromEntries(new FormData(event.target)); const body = { destination: raw.destination }; ['origin_latitude', 'origin_longitude', 'destination_latitude', 'destination_longitude'].forEach(key => { if (raw[key] !== '') body[key] = Number(raw[key]); }); try { const route = await api('/navigation/route', { method: 'POST', body: JSON.stringify(body) }); $('#route-result').innerHTML = `<p>${tag('PROVIDER ROUTE')}</p><p><strong>${escapeHtml(route.destination)}</strong> · ${route.total_distance_m} m · ${route.estimated_time_minutes} min</p><ol>${route.steps.map(step => `<li>${escapeHtml(step.instruction)} (${step.distance_m} m)</li>`).join('')}</ol>`; } catch (error) { $('#route-result').innerHTML = empty(error.message); } };
}

async function renderSos() {
  const [overview, history] = await Promise.all([api('/dashboard/overview'), api('/emergency/history')]); const active = overview.active_sos;
  content.innerHTML = `<div class="page-heading"><div><h2>Emergency SOS</h2><p>Use only when help is needed. Delivery status is recorded separately in Notifications.</p></div></div><section class="panel sos-panel"><h3>${active ? 'Active emergency alert' : 'Activate emergency SOS'}</h3>${active ? `<p>${tag(active.status)} Alert #${active.id} started ${dateText(active.created_at)}</p><button id="cancel-sos" class="secondary-button" type="button">Cancel active alert</button>` : `<p>Location is only included when the browser has provided a valid location. This form does not invent coordinates.</p><button id="activate-sos" class="danger-button" type="button">Activate SOS</button>`}</section><section class="panel"><h3>Emergency history</h3>${history.length ? `<table class="data-table"><thead><tr><th>Type</th><th>Status</th><th>Started</th><th>Location</th></tr></thead><tbody>${history.map(event => `<tr><td>${escapeHtml(event.event_type)}</td><td>${tag(event.status)}</td><td>${dateText(event.created_at)}</td><td>${event.latitude == null ? 'Unavailable' : `${event.latitude}, ${event.longitude}`}</td></tr>`).join('')}</tbody></table>` : empty('No emergency events recorded.')}</section>`;
  if (active) $('#cancel-sos').onclick = async () => { await api('/emergency/cancel', { method: 'POST', body: JSON.stringify({ emergency_id: active.id }) }); notify('Emergency alert cancelled.'); renderSos(); };
  else $('#activate-sos').onclick = activateSos;
}
async function activateSos() { if (!confirm('Activate an SOS emergency alert?')) return; let latitude = null, longitude = null; if (navigator.geolocation) { try { const position = await new Promise((resolve, reject) => navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 8000, enableHighAccuracy: true })); latitude = position.coords.latitude; longitude = position.coords.longitude; } catch (_) { notify('Location was unavailable. The SOS alert will record no location.'); } } await api('/emergency/trigger', { method: 'POST', body: JSON.stringify({ event_type: 'MANUAL_SOS', latitude, longitude }) }); notify('SOS alert created.'); renderSos(); }

async function renderContacts() {
  const contacts = await api('/contacts');
  content.innerHTML = `<div class="page-heading"><div><h2>Emergency contacts</h2><p>Only contacts in your account can receive an emergency notification attempt.</p></div></div><section class="grid-two"><article class="panel"><h3>Your contacts</h3>${contacts.length ? `<ul class="list">${contacts.map(contact => `<li><div class="list-row"><strong>${escapeHtml(contact.name)}</strong><button class="link-button" data-delete-contact="${contact.id}" type="button">Remove</button></div><small>${escapeHtml(contact.relationship_type)} · ${escapeHtml(contact.phone_number)}${contact.email ? ` · ${escapeHtml(contact.email)}` : ''}</small></li>`).join('')}</ul>` : empty('No emergency contacts added.')}</article><article class="panel"><h3>Add emergency contact</h3><form id="contact-form"><label>Name<input name="name" required></label><label>Relationship<input name="relationship_type" required placeholder="Family or caregiver"></label><label>Phone number<input name="phone_number" required></label><label>Email (optional)<input name="email" type="email"></label><button class="primary-button" type="submit">Add contact</button></form></article></section>`;
  $('#contact-form').onsubmit = async event => { event.preventDefault(); const value = Object.fromEntries(new FormData(event.target)); await api('/contacts', { method: 'POST', body: JSON.stringify(value) }); notify('Emergency contact added.'); renderContacts(); }; document.querySelectorAll('[data-delete-contact]').forEach(button => button.onclick = async () => { if (confirm('Remove this emergency contact?')) { await api(`/contacts/${button.dataset.deleteContact}`, { method: 'DELETE' }); renderContacts(); } });
}

async function renderDevices() {
  const devices = await api('/devices');
  content.innerHTML = `<div class="page-heading"><div><h2>Device management</h2><p>Register and manage only smart canes associated with your account.</p></div></div><section class="grid-two"><article class="panel"><h3>Registered smart canes</h3>${devices.length ? `<ul class="list">${devices.map(device => `<li><div class="list-row"><strong>${escapeHtml(device.device_name)}</strong><button class="link-button" data-delete-device="${device.id}" type="button">Remove</button></div><small>${escapeHtml(device.device_id)} · ${tag(device.connection_status)} · Battery: ${device.battery_percent ?? 'unavailable'}%<br>${device.is_simulator ? 'Simulator — not physical hardware' : 'Hardware device'} · Sensor health: ${escapeHtml(device.sensor_health)}</small></li>`).join('')}</ul>` : empty('No device registered.')}</article><article class="panel"><h3>Register smart cane</h3><form id="device-form"><label>Device ID<input name="device_id" required minlength="3" maxlength="64" placeholder="ECHO_CANE_001"></label><label>Display name<input name="device_name" value="ECHO-CANE" required></label><label>Firmware version (optional)<input name="firmware_version" maxlength="20"></label><label><input name="is_simulator" type="checkbox"> This is a development simulator, not physical hardware</label><button class="primary-button" type="submit">Register device</button></form></article></section>`;
  $('#device-form').onsubmit = async event => { event.preventDefault(); const raw = new FormData(event.target); await api('/devices', { method: 'POST', body: JSON.stringify({ device_id: raw.get('device_id'), device_name: raw.get('device_name'), firmware_version: raw.get('firmware_version') || null, is_simulator: raw.get('is_simulator') === 'on' }) }); notify('Device registered.'); renderDevices(); }; document.querySelectorAll('[data-delete-device]').forEach(button => button.onclick = async () => { if (confirm('Remove this device and its sensor history?')) { await api(`/devices/${button.dataset.deleteDevice}`, { method: 'DELETE' }); renderDevices(); } });
}

async function renderSensors() {
  const readings = await api('/sensors/history');
  content.innerHTML = `<div class="page-heading"><div><h2>Sensor history</h2><p>Recent sensor packets stored for your registered devices.</p></div><button id="refresh-sensors" class="secondary-button" type="button">Refresh</button></div><section class="panel">${readings.length ? `<table class="data-table"><thead><tr><th>Reading</th><th>Ultrasonic</th><th>ToF</th><th>Battery</th><th>SOS</th><th>Accelerometer</th></tr></thead><tbody>${readings.map(reading => `<tr><td>#${reading.id}</td><td>${reading.ultrasonic_cm ?? '—'} cm</td><td>${reading.tof_mm ?? '—'} mm</td><td>${reading.battery_percent ?? '—'}%</td><td>${reading.sos_pressed ? 'Pressed' : '—'}</td><td>${reading.accel_x ?? '—'}, ${reading.accel_y ?? '—'}, ${reading.accel_z ?? '—'}</td></tr>`).join('')}</tbody></table>` : empty('No sensor history is available for this account.')}</section>`; $('#refresh-sensors').onclick = renderSensors;
}

async function renderNotifications() {
  const notifications = await api('/notifications');
  content.innerHTML = `<div class="page-heading"><div><h2>Notifications</h2><p>Provider outcomes are shown as recorded; attempted delivery is not treated as confirmation.</p></div></div><section class="panel">${notifications.length ? `<table class="data-table"><thead><tr><th>Notification</th><th>Channel</th><th>Status</th><th>Created</th></tr></thead><tbody>${notifications.map(item => `<tr><td><strong>${escapeHtml(item.title)}</strong><br><small>${escapeHtml(item.message)}</small></td><td>${escapeHtml(item.channel)}${item.recipient ? `<br><small>${escapeHtml(item.recipient)}</small>` : ''}</td><td>${tag(item.status)}</td><td>${dateText(item.created_at)}</td></tr>`).join('')}</tbody></table>` : empty('No notification attempts are recorded.')}</section>`;
}

async function renderProfile() {
  const profile = await api('/user/profile');
  content.innerHTML = `<div class="page-heading"><div><h2>User profile</h2><p>Update the information associated with your account.</p></div></div><section class="panel"><p>${tag(profile.is_verified ? 'EMAIL VERIFIED' : 'EMAIL NOT VERIFIED')}</p>${profile.is_verified ? '' : '<button id="request-verification" class="secondary-button" type="button">Send verification email</button>'}<form id="profile-form"><div class="form-grid"><label>Full name<input name="full_name" required value="${escapeHtml(profile.full_name)}"></label><label>Phone number<input name="phone_number" value="${escapeHtml(profile.phone_number || '')}"></label><label>Date of birth<input name="date_of_birth" type="date" value="${escapeHtml(profile.date_of_birth || '')}"></label><label>Profile photo URL<input name="profile_photo_url" type="url" value="${escapeHtml(profile.profile_photo_url || '')}"></label><label class="full">Address<input name="address" value="${escapeHtml(profile.address || '')}"></label><label class="full">Medical/accessibility preferences<input name="medical_accessibility_preferences" value="${escapeHtml(profile.medical_accessibility_preferences || '')}"></label></div><button class="primary-button" type="submit">Save profile</button></form></section>`;
  $('#profile-form').onsubmit = async event => { event.preventDefault(); await api('/user/profile', { method: 'PUT', body: JSON.stringify(Object.fromEntries(new FormData(event.target))) }); state.user = await api('/user/profile'); notify('Profile saved.'); showApp(); }; const verify = $('#request-verification'); if (verify) verify.onclick = async () => { const result = await api('/auth/request-email-verification', { method: 'POST', body: '{}' }); notify(result.detail); };
}

async function renderSettings() {
  const settings = await api('/devices/preferences/me');
  content.innerHTML = `<div class="page-heading"><div><h2>Settings</h2><p>Accessibility preferences are stored in your account.</p></div></div><section class="panel"><form id="settings-form"><label>Language<select name="language"><option value="en">English</option><option value="hi">Hindi</option><option value="te">Telugu</option></select></label>${[['voice_alerts_enabled','Enable voice alerts'],['vibration_alerts_enabled','Enable vibration alerts'],['high_contrast_mode','Use high contrast'],['large_text_mode','Use large text'],['fall_detection_enabled','Enable fall detection']].map(([name,label]) => `<label class="switch-row">${label}<input name="${name}" type="checkbox" ${settings[name] ? 'checked' : ''}></label>`).join('')}<label>Fall-alert cancellation time (seconds)<input name="fall_detection_countdown_seconds" type="number" min="5" max="120" value="${settings.fall_detection_countdown_seconds}"></label><button class="primary-button" type="submit">Save settings</button></form></section>`;
  $('#settings-form').language.value = settings.language; $('#settings-form').onsubmit = async event => { event.preventDefault(); const form = new FormData(event.target); const body = { language: form.get('language'), fall_detection_countdown_seconds: Number(form.get('fall_detection_countdown_seconds')) }; ['voice_alerts_enabled','vibration_alerts_enabled','high_contrast_mode','large_text_mode','fall_detection_enabled'].forEach(name => body[name] = form.get(name) === 'on'); await api('/devices/preferences/me', { method: 'PUT', body: JSON.stringify(body) }); notify('Settings saved.'); };
}

function bindGoLinks() { document.querySelectorAll('[data-go]').forEach(button => button.onclick = () => setPage(button.dataset.go)); }
function setButtonBusy(button, busy, text) { button.disabled = busy; if (text) button.textContent = text; }
async function submitAuthentication(event, endpoint) {
  event.preventDefault(); if (state.authInFlight) return; const form = event.currentTarget;
  if (!form.reportValidity()) return; const data = Object.fromEntries(new FormData(form));
  if (endpoint === '/auth/register' && data.password !== data.confirm_password) return notify('Password confirmation does not match.'); delete data.confirm_password;
  state.authInFlight = true; const button = form.querySelector('button[type="submit"]'); const text = button.textContent; setButtonBusy(button, true, 'Please wait…');
  try { await finishAuthentication(await api(endpoint, { method: 'POST', body: JSON.stringify(data) })); }
  catch (error) { notify(error.message); }
  finally { state.authInFlight = false; setButtonBusy(button, false, text); }
}

$('#login-tab').onclick = () => setAuthTab('login'); $('#register-tab').onclick = () => setAuthTab('register');
$('#login-form').onsubmit = event => submitAuthentication(event, '/auth/login'); $('#register-form').onsubmit = event => submitAuthentication(event, '/auth/register');
document.querySelectorAll('[data-toggle-password]').forEach(button => button.onclick = () => { const input = button.previousElementSibling; input.type = input.type === 'password' ? 'text' : 'password'; button.setAttribute('aria-label', input.type === 'password' ? 'Show password' : 'Hide password'); });
$('#forgot-password').onclick = async () => { const email = prompt('Enter your account email address.'); if (!email) return; try { const result = await api('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }); notify(result.detail); } catch (error) { notify(error.message); } };
$('#reset-form').onsubmit = async event => { event.preventDefault(); try { await api('/auth/reset-password', { method: 'POST', body: JSON.stringify({ token: event.currentTarget.dataset.token, new_password: new FormData(event.currentTarget).get('new_password') }) }); history.replaceState({}, '', location.pathname); notify('Password reset. Sign in with your new password.'); showAuth(); } catch (error) { notify(error.message); } };
$('#verify-form').onsubmit = async event => { event.preventDefault(); try { const result = await api('/auth/verify-email', { method: 'POST', body: JSON.stringify({ token: event.currentTarget.dataset.token }) }); history.replaceState({}, '', location.pathname); notify(result.detail); showAuth(); } catch (error) { notify(error.message); } };
document.querySelectorAll('#sidebar-nav button').forEach(button => button.onclick = () => setPage(button.dataset.page)); $('#menu-button').onclick = () => $('#app-shell').classList.toggle('nav-open');
$('#logout-button').onclick = async () => { try { if (state.refreshToken) await api('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: state.refreshToken }) }); } finally { clearSession(); showAuth(); notify('You have been signed out.'); } };
const query = new URLSearchParams(location.search); const token = query.get('token'); if (query.get('action') === 'reset-password' && token) { $('#auth-shell').hidden = false; $('#login-form').hidden = true; $('#register-form').hidden = true; $('#reset-form').hidden = false; $('#reset-form').dataset.token = token; } else if (query.get('action') === 'verify-email' && token) { $('#auth-shell').hidden = false; $('#login-form').hidden = true; $('#register-form').hidden = true; $('#verify-form').hidden = false; $('#verify-form').dataset.token = token; } else { const requested = location.hash.slice(1); if (pageNames[requested]) state.page = requested; bootstrap(); }
