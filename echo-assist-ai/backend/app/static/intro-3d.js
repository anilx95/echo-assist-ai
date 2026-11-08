/*
 * ECHO-ASSIST product assembly.  A single, dependency-free WebGL scene owns
 * the intro lifecycle: one RAF loop, reusable buffers, adaptive quality, and
 * deterministic state transitions.  It does not model undocumented hardware.
 */
(() => {
  const STATES = Object.freeze({
    INITIALIZING: 'INITIALIZING', INTRO_START: 'INTRO_START', CANE_REVEAL: 'CANE_REVEAL',
    SENSOR_ACTIVATION: 'SENSOR_ACTIVATION', BRAND_REVEAL: 'BRAND_REVEAL', INTRO_EXIT: 'INTRO_EXIT',
    LOGIN_ENTER: 'LOGIN_ENTER', LOGIN_READY: 'LOGIN_READY', DASHBOARD_ENTER: 'DASHBOARD_ENTER', DASHBOARD_READY: 'DASHBOARD_READY',
  });
  // 0–1.4s exploded parts, 1.4–5.1s assembly, 5.1–6.5s reveal, 6.5–7.5s brand, 7.5–10s login.
  const TIMELINE = [[0, STATES.INTRO_START], [1400, STATES.CANE_REVEAL], [5100, STATES.SENSOR_ACTIVATION], [6500, STATES.BRAND_REVEAL], [7500, STATES.INTRO_EXIT], [8500, STATES.LOGIN_ENTER], [9250, STATES.LOGIN_READY], [9450, STATES.DASHBOARD_READY]];
  const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
  const easeOut = value => 1 - Math.pow(1 - clamp(value), 3);
  const easeInOut = value => { const t = clamp(value); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  const mix = (first, second, progress) => first + (second - first) * progress;
  const mixVector = (first, second, progress) => first.map((value, index) => mix(value, second[index], progress));

  function createShader(gl, type, source) {
    const shader = gl.createShader(type); gl.shaderSource(shader, source); gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader) || 'WebGL shader compilation failed.');
    return shader;
  }
  function createProgram(gl) {
    const vertexSource = `
      attribute vec3 aPosition; attribute vec3 aColor;
      uniform mat4 uProjection; uniform vec3 uTranslation;
      uniform float uYaw; uniform float uPitch; uniform float uPartYaw; uniform float uPartPitch;
      uniform float uScale; uniform float uTime; uniform float uPointMode; uniform float uAlpha; uniform float uEmission;
      varying vec3 vColor; varying float vAlpha;
      void main(){
        vec3 p = aPosition;
        if (uPointMode > .5) {
          p.y += sin(uTime * .0014 + p.x * 2.7 + p.z) * .09; p.x += cos(uTime * .0008 + p.y) * .025;
          gl_PointSize = 1.8 + mod(abs(p.x * 13. + p.y * 7.), 2.8);
        } else {
          float cpy = cos(uPartYaw), spy = sin(uPartYaw), cpp = cos(uPartPitch), spp = sin(uPartPitch);
          p.xz = mat2(cpy, -spy, spy, cpy) * p.xz; p.yz = mat2(cpp, -spp, spp, cpp) * p.yz; p += uTranslation;
          float cy = cos(uYaw), sy = sin(uYaw), cp = cos(uPitch), sp = sin(uPitch);
          p.xz = mat2(cy, -sy, sy, cy) * p.xz; p.yz = mat2(cp, -sp, sp, cp) * p.yz; p *= uScale; gl_PointSize = 1.;
        }
        p.z -= 4.7; gl_Position = uProjection * vec4(p, 1.); vColor = min(vec3(1.), aColor * (1. + uEmission)); vAlpha = uAlpha;
      }`;
    const fragmentSource = `
      precision mediump float; uniform float uPointMode; varying vec3 vColor; varying float vAlpha;
      void main(){ float alpha = vAlpha; if(uPointMode > .5){ alpha *= smoothstep(.5, .12, length(gl_PointCoord - .5)); } gl_FragColor = vec4(vColor, alpha); }`;
    const program = gl.createProgram(); gl.attachShader(program, createShader(gl, gl.VERTEX_SHADER, vertexSource)); gl.attachShader(program, createShader(gl, gl.FRAGMENT_SHADER, fragmentSource)); gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program) || 'WebGL program linking failed.');
    return program;
  }
  function perspective(fov, aspect, near, far) {
    const f = 1 / Math.tan(fov / 2), range = 1 / (near - far);
    return new Float32Array([f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (near + far) * range, -1, 0, 0, near * far * range * 2, 0]);
  }
  function addVertex(vertices, colors, point, color) { vertices.push(point[0], point[1], point[2]); colors.push(color[0], color[1], color[2]); }
  function addTriangle(vertices, colors, first, second, third, color) { addVertex(vertices, colors, first, color); addVertex(vertices, colors, second, color); addVertex(vertices, colors, third, color); }
  function addCylinder(vertices, colors, start, end, radius, color, sides = 10) {
    const direction = [end[0] - start[0], end[1] - start[1], end[2] - start[2]], length = Math.hypot(...direction); if (!length) return;
    direction[0] /= length; direction[1] /= length; direction[2] /= length;
    const reference = Math.abs(direction[1]) > .86 ? [1, 0, 0] : [0, 1, 0];
    let u = [direction[1] * reference[2] - direction[2] * reference[1], direction[2] * reference[0] - direction[0] * reference[2], direction[0] * reference[1] - direction[1] * reference[0]];
    const uLength = Math.hypot(...u); u = u.map(value => value / uLength);
    const v = [direction[1] * u[2] - direction[2] * u[1], direction[2] * u[0] - direction[0] * u[2], direction[0] * u[1] - direction[1] * u[0]];
    for (let index = 0; index < sides; index += 1) {
      const theta = index / sides * Math.PI * 2, nextTheta = (index + 1) / sides * Math.PI * 2;
      const pointAt = (origin, angle) => [origin[0] + radius * (u[0] * Math.cos(angle) + v[0] * Math.sin(angle)), origin[1] + radius * (u[1] * Math.cos(angle) + v[1] * Math.sin(angle)), origin[2] + radius * (u[2] * Math.cos(angle) + v[2] * Math.sin(angle))];
      const a = pointAt(start, theta), b = pointAt(start, nextTheta), c = pointAt(end, nextTheta), d = pointAt(end, theta), shade = .72 + .28 * Math.max(0, Math.cos(theta - .6)), shaded = color.map(value => value * shade);
      addTriangle(vertices, colors, a, b, c, shaded); addTriangle(vertices, colors, a, c, d, shaded);
    }
  }
  function addBox(vertices, colors, center, size, color) {
    const [x, y, z] = center, [width, height, depth] = size;
    const points = [[x-width/2,y-height/2,z-depth/2],[x+width/2,y-height/2,z-depth/2],[x+width/2,y+height/2,z-depth/2],[x-width/2,y+height/2,z-depth/2],[x-width/2,y-height/2,z+depth/2],[x+width/2,y-height/2,z+depth/2],[x+width/2,y+height/2,z+depth/2],[x-width/2,y+height/2,z+depth/2]];
    [[0,1,2,3],[1,5,6,2],[5,4,7,6],[4,0,3,7],[3,2,6,7],[4,5,1,0]].forEach((face, index) => { const shade = .68 + (index % 3) * .13, shaded = color.map(value => value * shade); addTriangle(vertices, colors, points[face[0]], points[face[1]], points[face[2]], shaded); addTriangle(vertices, colors, points[face[0]], points[face[2]], points[face[3]], shaded); });
  }
  function shape(builder) { const vertices = [], colors = []; builder(vertices, colors); return { vertices: new Float32Array(vertices), colors: new Float32Array(colors) }; }
  function partGeometries() {
    const metal = [.62, .81, .96], dark = [.06, .17, .31], blue = [.04, .42, .68], cyan = [.03, .86, 1.];
    return {
      shaft: shape((v, c) => { addCylinder(v, c, [0, -1.05, 0], [0, 1.05, 0], .065, metal, 12); addCylinder(v, c, [0, .25, 0], [0, .34, 0], .082, blue, 12); }),
      handle: shape((v, c) => { addCylinder(v, c, [0, -.27, 0], [-.10, .07, 0], .115, dark, 12); addCylinder(v, c, [-.10, .07, 0], [.12, .30, 0], .135, dark, 12); addCylinder(v, c, [.12, .30, 0], [.42, .22, 0], .14, dark, 12); }),
      control: shape((v, c) => { addBox(v, c, [0, 0, 0], [.23, .48, .21], [.04, .30, .48]); addCylinder(v, c, [0, .12, .12], [0, .12, .16], .054, cyan, 10); addCylinder(v, c, [0, -.12, .12], [0, -.12, .16], .045, blue, 10); }),
      ultrasonic: shape((v, c) => { addBox(v, c, [0, 0, 0], [.18, .11, .10], dark); addCylinder(v, c, [0, 0, .05], [0, 0, .09], .047, cyan, 10); }),
      tof: shape((v, c) => { addBox(v, c, [0, 0, 0], [.15, .10, .09], dark); addCylinder(v, c, [0, 0, .045], [0, 0, .082], .036, blue, 10); }),
      tip: shape((v, c) => { addCylinder(v, c, [0, -.09, 0], [0, .09, 0], .105, dark, 12); addCylinder(v, c, [0, .06, 0], [0, .10, 0], .075, metal, 12); }),
    };
  }
  function particleGeometry(count) {
    const positions = new Float32Array(count * 3), colors = new Float32Array(count * 3);
    for (let index = 0; index < count; index += 1) { const base = index * 3, radius = 1.1 + Math.random() * 3.5, angle = Math.random() * Math.PI * 2; positions[base] = Math.cos(angle) * radius; positions[base + 1] = (Math.random() - .5) * 3.8; positions[base + 2] = Math.sin(angle) * 1.3; const blue = .62 + Math.random() * .38; colors[base] = .08; colors[base + 1] = blue; colors[base + 2] = 1; }
    return { vertices: positions, colors };
  }
  function makeMesh(gl, geometry) { const position = gl.createBuffer(), color = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, position); gl.bufferData(gl.ARRAY_BUFFER, geometry.vertices, gl.STATIC_DRAW); gl.bindBuffer(gl.ARRAY_BUFFER, color); gl.bufferData(gl.ARRAY_BUFFER, geometry.colors, gl.STATIC_DRAW); return { position, color, count: geometry.vertices.length / 3 }; }

  class CinematicIntro {
    constructor(root, callbacks = {}) {
      this.root = root; this.canvas = root.querySelector('#intro-canvas'); this.callbacks = callbacks; this.state = STATES.INITIALIZING;
      this.lowPower = Boolean(window.matchMedia('(max-width: 700px)').matches || (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) || (navigator.deviceMemory && navigator.deviceMemory < 4));
      this.frame = this.frame.bind(this); this.resize = this.resize.bind(this); this.visibilityChange = this.visibilityChange.bind(this); this.skip = this.skip.bind(this); this.frameSamples = []; this.lastFrameAt = 0; this.finished = false;
      // Derived only from documented protocol components; no undocumented battery enclosure is visualized.
      this.parts = [
        { id: 'shaft', label: 'Main cane shaft', target: [0, -.52, 0], start: [-.90, -.22, .78], yaw: -1.45, pitch: .42, begin: 1400, end: 3200 },
        { id: 'handle', label: 'Cane handle', target: [0, .82, 0], start: [.98, .73, .55], yaw: .92, pitch: -.48, begin: 1660, end: 3700 },
        { id: 'control', label: 'ESP32 control module', target: [0, .12, .02], start: [-1.05, .48, -.42], yaw: -1.18, pitch: .58, begin: 2150, end: 4100 },
        { id: 'ultrasonic', label: 'Ultrasonic sensor module', target: [0, .30, .15], start: [.89, -.09, .61], yaw: 1.38, pitch: -.75, begin: 2670, end: 4450 },
        { id: 'tof', label: 'ToF sensor module', target: [0, -.08, .15], start: [-.84, -.64, .55], yaw: -.91, pitch: .66, begin: 2970, end: 4750 },
        { id: 'tip', label: 'Bottom support tip', target: [0, -1.71, 0], start: [.68, -1.22, -.46], yaw: .74, pitch: -.86, begin: 3330, end: 5100 },
      ];
    }
    prepareLetters() {
      const heading = this.root.querySelector('#intro-title'); if (!heading || heading.dataset.animated) return;
      const text = heading.textContent.trim(); heading.setAttribute('aria-label', text); heading.dataset.animated = 'true';
      heading.innerHTML = [...text].map((letter, index) => letter === ' ' ? '<span class="brand-space"> </span>' : `<span class="brand-letter ${index >= text.length - 2 ? 'accent-letter' : ''}" style="--letter-index:${index}">${letter}</span>`).join('');
    }
    start() {
      this.prepareLetters(); this.root.dataset.introState = STATES.INITIALIZING; this.root.hidden = false; this.root.querySelector('#skip-intro').addEventListener('click', this.skip, { once: true });
      try { this.setupRenderer(); } catch (_) { this.root.classList.add('intro-fallback'); }
      window.addEventListener('resize', this.resize, { passive: true }); document.addEventListener('visibilitychange', this.visibilityChange);
      this.startedAt = performance.now(); this.transition(STATES.INTRO_START); this.raf = requestAnimationFrame(this.frame);
    }
    setupRenderer() {
      const gl = this.canvas.getContext('webgl', { alpha: true, antialias: !this.lowPower, powerPreference: 'high-performance', preserveDrawingBuffer: false }); if (!gl) throw new Error('WebGL unavailable');
      this.gl = gl; this.program = createProgram(gl); this.locations = { position: gl.getAttribLocation(this.program, 'aPosition'), color: gl.getAttribLocation(this.program, 'aColor'), projection: gl.getUniformLocation(this.program, 'uProjection'), translation: gl.getUniformLocation(this.program, 'uTranslation'), yaw: gl.getUniformLocation(this.program, 'uYaw'), pitch: gl.getUniformLocation(this.program, 'uPitch'), partYaw: gl.getUniformLocation(this.program, 'uPartYaw'), partPitch: gl.getUniformLocation(this.program, 'uPartPitch'), scale: gl.getUniformLocation(this.program, 'uScale'), time: gl.getUniformLocation(this.program, 'uTime'), pointMode: gl.getUniformLocation(this.program, 'uPointMode'), alpha: gl.getUniformLocation(this.program, 'uAlpha'), emission: gl.getUniformLocation(this.program, 'uEmission') };
      const geometries = partGeometries(); this.meshes = Object.fromEntries(this.parts.map(part => [part.id, makeMesh(gl, geometries[part.id])])); const particles = particleGeometry(this.lowPower ? 56 : 160); this.particles = makeMesh(gl, particles);
      gl.enable(gl.DEPTH_TEST); gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); this.root.classList.add('intro-webgl'); this.resize();
    }
    resize() {
      if (!this.gl) return; const pixelRatio = Math.min(window.devicePixelRatio || 1, this.lowPower ? 1.25 : 1.75), width = Math.max(1, Math.round(this.canvas.clientWidth * pixelRatio)), height = Math.max(1, Math.round(this.canvas.clientHeight * pixelRatio));
      if (this.canvas.width !== width || this.canvas.height !== height) { this.canvas.width = width; this.canvas.height = height; } this.gl.viewport(0, 0, width, height); this.projection = perspective(Math.PI / 3, width / height, .1, 30);
    }
    transition(next) {
      if (this.state === next) return; this.state = next; this.root.dataset.introState = next;
      const status = this.root.querySelector('#intro-assembly-status');
      if (status) {
        const message = {
          [STATES.INTRO_START]: 'Exploded smart cane components displayed',
          [STATES.CANE_REVEAL]: 'Assembling the smart cane',
          [STATES.SENSOR_ACTIVATION]: 'Ultrasonic and ToF sensors activated',
          [STATES.BRAND_REVEAL]: 'ECHO-ASSIST AI product reveal complete',
          [STATES.INTRO_EXIT]: 'Opening secure account access',
        }[next];
        if (message) status.textContent = message;
      }
      if (next === STATES.LOGIN_ENTER) this.callbacks.onLoginEnter?.(); if (next === STATES.LOGIN_READY) this.callbacks.onLoginReady?.(); this.callbacks.onStateChange?.(next);
    }
    frame(now) {
      if (this.finished) return; const elapsed = now - this.startedAt - (this.pausedDuration || 0); this.updateState(elapsed); this.render(elapsed, now);
      if (elapsed >= 9450) { this.complete(); return; } this.raf = requestAnimationFrame(this.frame);
    }
    updateState(elapsed) { let next = STATES.INTRO_START; for (const [start, state] of TIMELINE) if (elapsed >= start) next = state; this.transition(next); }
    partTransform(part, elapsed) {
      const progress = easeInOut((elapsed - part.begin) / (part.end - part.begin));
      const floatFade = elapsed < part.begin ? 1 - easeOut((elapsed - (part.begin - 220)) / 220) : 0;
      const hover = Math.sin(elapsed * .0016 + part.start[0] * 3) * .035 * floatFade;
      const position = mixVector(part.start, part.target, progress); position[1] += hover + Math.sin(progress * Math.PI) * (.09 + Math.abs(part.start[0]) * .05); position[2] += Math.sin(progress * Math.PI) * .20;
      return { position, yaw: mix(part.yaw, 0, progress) + Math.sin(progress * Math.PI) * .26, pitch: mix(part.pitch, 0, progress) + Math.sin(progress * Math.PI) * .16, progress, alpha: easeOut(elapsed / 760) };
    }
    render(elapsed, now) {
      if (!this.gl) return; const gl = this.gl, exit = easeInOut((elapsed - 7500) / 1050), yaw = -.42 + Math.min(1, Math.max(0, (elapsed - 5100) / 1300)) * .55 + Math.sin(elapsed * .001) * .025, pitch = .10 + Math.sin(elapsed * .0009) * .025, scale = 1.02 * (1 - exit * .55), particleAlpha = Math.max(0, .15 + Math.min(1, elapsed / 1200) * .42 - exit * .56);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); gl.useProgram(this.program); gl.uniformMatrix4fv(this.locations.projection, false, this.projection); gl.uniform1f(this.locations.time, now); gl.uniform1f(this.locations.yaw, yaw); gl.uniform1f(this.locations.pitch, pitch); gl.uniform1f(this.locations.scale, scale);
      this.draw(this.particles, gl.POINTS, { position: [0, 0, 0], yaw: 0, pitch: 0, alpha: particleAlpha, emission: 0, pointMode: 1 });
      this.parts.forEach(part => { const transform = this.partTransform(part, elapsed); const sensorProgress = part.id === 'ultrasonic' ? clamp((elapsed - 5100) / 360) : part.id === 'tof' ? clamp((elapsed - 5450) / 360) : part.id === 'control' ? clamp((elapsed - 5800) / 400) : 0; this.draw(this.meshes[part.id], gl.TRIANGLES, { ...transform, alpha: transform.alpha * (1 - exit), emission: sensorProgress * .65, pointMode: 0 }); });
      if (this.lastFrameAt) { const delta = now - this.lastFrameAt; if (delta < 100) this.frameSamples.push(delta); } this.lastFrameAt = now;
      if (this.frameSamples.length === 180) { const average = this.frameSamples.reduce((sum, value) => sum + value, 0) / this.frameSamples.length; console.info(`[ECHO-ASSIST] Assembly intro average frame time: ${average.toFixed(1)} ms`); this.frameSamples.length = 0; }
    }
    draw(mesh, mode, transform) {
      const gl = this.gl, location = this.locations; gl.bindBuffer(gl.ARRAY_BUFFER, mesh.position); gl.enableVertexAttribArray(location.position); gl.vertexAttribPointer(location.position, 3, gl.FLOAT, false, 0, 0); gl.bindBuffer(gl.ARRAY_BUFFER, mesh.color); gl.enableVertexAttribArray(location.color); gl.vertexAttribPointer(location.color, 3, gl.FLOAT, false, 0, 0);
      gl.uniform3fv(location.translation, transform.position); gl.uniform1f(location.partYaw, transform.yaw); gl.uniform1f(location.partPitch, transform.pitch); gl.uniform1f(location.pointMode, transform.pointMode); gl.uniform1f(location.alpha, transform.alpha); gl.uniform1f(location.emission, transform.emission); gl.drawArrays(mode, 0, mesh.count);
    }
    visibilityChange() { if (document.hidden) { this.pauseStartedAt = performance.now(); cancelAnimationFrame(this.raf); } else if (this.pauseStartedAt) { this.pausedDuration = (this.pausedDuration || 0) + performance.now() - this.pauseStartedAt; this.pauseStartedAt = 0; this.raf = requestAnimationFrame(this.frame); } }
    complete() {
      if (this.finished) return;
      this.finished = true;
      cancelAnimationFrame(this.raf);
      this.root.classList.add('is-leaving');
      let completed = false;
      const finishOnce = () => {
        if (completed) return;
        completed = true;
        this.dispose();
        this.callbacks.onFinish?.();
      };

      // Use the actual exit animation's completion, not a wall-clock timeout.
      // If Web Animations cannot run, prefer access to login over a stuck intro.
      if (typeof this.root.animate === 'function') {
        try {
          const exit = this.root.animate(
            [
              { opacity: 1, transform: 'scale(1)', visibility: 'visible' },
              { opacity: 0, transform: 'scale(1.015)', visibility: 'hidden' },
            ],
            { duration: 550, easing: 'ease', fill: 'forwards' },
          );
          if (exit?.finished?.then) { exit.finished.then(finishOnce, finishOnce); return; }
        } catch (_) { /* Continue to the CSS completion fallback. */ }
      }

      queueMicrotask(finishOnce);
    }
    skip() { if (this.finished) return; this.finished = true; cancelAnimationFrame(this.raf); this.callbacks.onLoginEnter?.(); this.callbacks.onLoginReady?.(); this.dispose(); this.callbacks.onFinish?.(); }
    dispose() { window.removeEventListener('resize', this.resize); document.removeEventListener('visibilitychange', this.visibilityChange); if (!this.gl) return; [...Object.values(this.meshes || {}), this.particles].filter(Boolean).forEach(mesh => { this.gl.deleteBuffer(mesh.position); this.gl.deleteBuffer(mesh.color); }); this.gl.deleteProgram(this.program); this.gl = null; this.root.classList.remove('intro-webgl'); }
  }
  window.ECHO_INTRO_STATES = STATES; window.EchoCinematicIntro = CinematicIntro;
})();
