import json
import math
import re

import streamlit as st
import streamlit.components.v1 as components

try:
    from groq import Groq
except Exception:
    Groq = None


G = 6.67430e-11


def simulate_orbit(
    planet_mass,
    planet_radius,
    satellite_mass,
    initial_altitude,
    initial_velocity,
    angle_deg,
    duration=7200.0,
    dt=2.0,
):
    """
    2D two-body approximation:
    the planet is fixed at the origin and the satellite moves under
    the planet's gravity.

    Initial position is on +x axis.
    angle_deg is measured from +x direction for the initial velocity.
    """

    r0 = planet_radius + initial_altitude

    if r0 <= 0:
        raise ValueError("Initial distance must be greater than zero.")

    if planet_mass <= 0:
        raise ValueError("Planet mass must be greater than zero.")

    if satellite_mass <= 0:
        raise ValueError("Satellite mass must be greater than zero.")

    theta = math.radians(angle_deg)

    x = r0
    y = 0.0
    vx = initial_velocity * math.cos(theta)
    vy = initial_velocity * math.sin(theta)

    n = int(duration / dt) + 1

    time = [0.0] * n
    xs = [0.0] * n
    ys = [0.0] * n
    vxs = [0.0] * n
    vys = [0.0] * n
    speeds = [0.0] * n
    distances = [0.0] * n
    accelerations = [0.0] * n
    kinetic = [0.0] * n
    potential = [0.0] * n
    total_energy = [0.0] * n

    mu = G * planet_mass

    def acceleration(px, py):
        r2 = px * px + py * py
        r = math.sqrt(max(r2, 1e-30))
        factor = -mu / (r ** 3)
        return factor * px, factor * py

    def deriv(state):
        px, py, pvx, pvy = state
        ax, ay = acceleration(px, py)
        return pvx, pvy, ax, ay

    def rk4_step(state, h):
        k1 = deriv(state)

        s2 = [
            state[j] + 0.5 * h * k1[j]
            for j in range(4)
        ]
        k2 = deriv(s2)

        s3 = [
            state[j] + 0.5 * h * k2[j]
            for j in range(4)
        ]
        k3 = deriv(s3)

        s4 = [
            state[j] + h * k3[j]
            for j in range(4)
        ]
        k4 = deriv(s4)

        return [
            state[j]
            + h * (
                k1[j]
                + 2 * k2[j]
                + 2 * k3[j]
                + k4[j]
            ) / 6.0
            for j in range(4)
        ]

    state = [x, y, vx, vy]

    impact_index = None

    for i in range(n):
        px, py, pvx, pvy = state

        r = math.hypot(px, py)
        speed = math.hypot(pvx, pvy)
        ax, ay = acceleration(px, py)
        acc = math.hypot(ax, ay)

        ke = 0.5 * satellite_mass * speed * speed
        pe = -G * planet_mass * satellite_mass / r
        te = ke + pe

        time[i] = i * dt
        xs[i] = px
        ys[i] = py
        vxs[i] = pvx
        vys[i] = pvy
        speeds[i] = speed
        distances[i] = r
        accelerations[i] = acc
        kinetic[i] = ke
        potential[i] = pe
        total_energy[i] = te

        if r <= planet_radius:
            impact_index = i

            # Keep the final frame exactly on the planet surface.
            scale = planet_radius / max(r, 1e-30)
            xs[i] = px * scale
            ys[i] = py * scale

            # Stop after impact.
            for j in range(i + 1, n):
                time[j] = time[i]
                xs[j] = xs[i]
                ys[j] = ys[i]
                vxs[j] = 0.0
                vys[j] = 0.0
                speeds[j] = 0.0
                distances[j] = planet_radius
                accelerations[j] = 0.0
                kinetic[j] = 0.0
                potential[j] = -G * planet_mass * satellite_mass / planet_radius
                total_energy[j] = potential[j]

            break

        if i < n - 1:
            state = rk4_step(state, dt)

    if impact_index is not None:
        last = impact_index
        # Trim after impact to keep animation clean.
        end = last + 1
        arrays = [
            time[:end],
            xs[:end],
            ys[:end],
            vxs[:end],
            vys[:end],
            speeds[:end],
            distances[:end],
            accelerations[:end],
            kinetic[:end],
            potential[:end],
            total_energy[:end],
        ]
        (
            time,
            xs,
            ys,
            vxs,
            vys,
            speeds,
            distances,
            accelerations,
            kinetic,
            potential,
            total_energy,
        ) = arrays

    escape_velocity = math.sqrt(
        2 * G * planet_mass / r0
    )

    initial_specific_energy = (
        initial_velocity ** 2 / 2
        - G * planet_mass / r0
    )

    if impact_index is not None:
        orbit_type = "Collision"
    elif initial_specific_energy >= 0:
        orbit_type = "Escape Trajectory"
    else:
        # Bound trajectory: classify circular vs elliptical using
        # initial speed relative to local circular speed.
        circular_velocity = math.sqrt(
            G * planet_mass / r0
        )

        if (
            abs(initial_velocity - circular_velocity)
            <= max(1.0, circular_velocity * 0.01)
            and abs(angle_deg - 90.0) <= 5.0
        ):
            orbit_type = "Circular Orbit"
        else:
            orbit_type = "Elliptical Orbit"

    return {
        "time": time,
        "x": xs,
        "y": ys,
        "vx": vxs,
        "vy": vys,
        "speed": speeds,
        "distance": distances,
        "acceleration": accelerations,
        "kinetic": kinetic,
        "potential": potential,
        "total_energy": total_energy,
        "escape_velocity": escape_velocity,
        "orbit_type": orbit_type,
        "initial_distance": r0,
        "circular_velocity": math.sqrt(
            G * planet_mass / r0
        ),
    }


def parse_ai_orbit(prompt):
    if Groq is None:
        return {
            "error": "Groq is not installed. Please install the groq package."
        }

    api_key = st.secrets.get("GROQ_API_KEY")

    if not api_key:
        return {
            "error": "GROQ_API_KEY is not configured."
        }

    system_prompt = """
You convert natural-language orbit experiment descriptions into JSON.

Return ONLY valid JSON.

Schema:
{
  "planet_mass": number or null,
  "planet_radius": number or null,
  "satellite_mass": number or null,
  "initial_altitude": number or null,
  "initial_velocity": number or null,
  "angle_deg": number or null
}

Units:
planet_mass: kg
planet_radius: m
satellite_mass: kg
initial_altitude: m
initial_velocity: m/s
angle_deg: degrees

The user may describe values using:
tonnes (t), kilograms (kg), kilometers (km), meters (m),
kilometers per second (km/s), or meters per second (m/s).

Convert all values to SI units before returning JSON.

Only use values explicitly stated by the user.
Do not invent missing values.

Conversions:
1 t = 1000 kg
1 km = 1000 m
1 km/s = 1000 m/s
"""

    try:
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content.strip()

        raw = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            raw,
            flags=re.IGNORECASE,
        )

        result = json.loads(raw)

        allowed = {
            "planet_mass",
            "planet_radius",
            "satellite_mass",
            "initial_altitude",
            "initial_velocity",
            "angle_deg",
        }

        return {
            key: result.get(key)
            for key in allowed
        }

    except Exception as exc:
        return {
            "error": str(exc)
        }


def orbit_animation_html(data, planet_radius, playback_ratio=100.0, planet_mass=0.0, initial_altitude=0.0, initial_velocity=0.0, angle_deg=90.0):
    """
    Browser-side continuous orbit animation.

    The Python RK4 simulation is still used for analysis/graphs, but the
    animation itself integrates the orbit continuously in JavaScript. This
    removes the old 20,000-second playback limit and prevents the animation
    from jumping back to the initial position when the precomputed data ends.
    """
    payload = json.dumps(
        {
            "x": data["x"],
            "y": data["y"],
            "distance": data["distance"],
            "acceleration": data["acceleration"],
            "speed": data["speed"],
            "orbit_type": data["orbit_type"],
        }
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
html, body {{
    margin: 0;
    padding: 0;
    background: #0e1117;
    overflow: hidden;
}}

#wrap {{
    box-sizing: border-box;
    width: 100%;
    height: 680px;
    border: 2px solid white;
    border-radius: 8px;
    background: #0e1117;
    padding: 12px;
    color: white;
    font-family: Arial, sans-serif;
}}

canvas {{
    display: block;
    width: 100%;
    height: 530px;
    background: #0e1117;
}}

.controls {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
}}

button {{
    background: #151922;
    color: white;
    border: 1px solid #777;
    border-radius: 7px;
    padding: 8px 18px;
    font-size: 14px;
    cursor: pointer;
}}

button:hover {{
    background: #252b38;
}}

.info {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-top: 12px;
}}

.card {{
    border: 1px solid #444;
    border-radius: 6px;
    padding: 7px 9px;
    background: #131720;
}}

.label {{
    color: #aaa;
    font-size: 12px;
}}

.value {{
    margin-top: 3px;
    font-size: 14px;
    font-weight: bold;
}}
</style>
</head>

<body>
<div id="wrap">
    <canvas id="canvas"></canvas>

    <div class="controls">
        <button id="play">▶ Play</button>
        <span id="status" style="margin-left:auto;font-weight:bold;">
            {data["orbit_type"]}
        </span>
    </div>

    <div class="info">
        <div class="card">
            <div class="label">Time</div>
            <div class="value" id="time">0.00 s</div>
        </div>
        <div class="card">
            <div class="label">Speed</div>
            <div class="value" id="speed">0 m/s</div>
        </div>
        <div class="card">
            <div class="label">Distance</div>
            <div class="value" id="distance">0 m</div>
        </div>
        <div class="card">
            <div class="label">Gravity</div>
            <div class="value" id="gravity">0 m/s²</div>
        </div>
    </div>
</div>

<script>
const referenceData = {payload};
const G = 6.67430e-11;
const planetMass = {planet_mass};
const planetRadius = {planet_radius};
const initialAltitude = {initial_altitude};
const initialVelocity = {initial_velocity};
const angleDeg = {angle_deg};
const playbackRatio = {playback_ratio};
const physicsDt = 0.75;

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const playButton = document.getElementById("play");
const statusEl = document.getElementById("status");
const timeEl = document.getElementById("time");
const speedEl = document.getElementById("speed");
const distanceEl = document.getElementById("distance");
const gravityEl = document.getElementById("gravity");

const mu = G * planetMass;
const r0 = planetRadius + initialAltitude;
const theta = angleDeg * Math.PI / 180;

let state = [
    r0,
    0,
    initialVelocity * Math.cos(theta),
    initialVelocity * Math.sin(theta)
];

let simulationTime = 0;
let playing = false;
let lastTimestamp = 0;
let accumulator = 0;
let collision = false;

// Keep a browser-side trail so the orbit can continue indefinitely.
const trail = [];
const MAX_TRAIL_POINTS = 9000;

// Use the precomputed trajectory only to choose a useful initial display scale.
let displayMaxRadius = Math.max(
    planetRadius * 2.5,
    ...referenceData.distance
) * 1.12;

function resize() {{
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
}}

function formatDistance(m) {{
    if (m >= 1e9) return (m / 1e9).toFixed(2) + " Gm";
    if (m >= 1e6) return (m / 1e6).toFixed(2) + " Mm";
    if (m >= 1e3) return (m / 1e3).toFixed(2) + " km";
    return m.toFixed(1) + " m";
}}

function drawArrow(x1, y1, x2, y2, color) {{
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy);
    if (len < 1) return;

    const ux = dx / len;
    const uy = dy / len;
    const head = 9;

    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 3;

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(
        x2 - ux * head - uy * head * 0.5,
        y2 - uy * head + ux * head * 0.5
    );
    ctx.lineTo(
        x2 - ux * head + uy * head * 0.5,
        y2 - uy * head - ux * head * 0.5
    );
    ctx.closePath();
    ctx.fill();
}}

function acceleration(px, py) {{
    const r2 = px * px + py * py;
    const r = Math.sqrt(Math.max(r2, 1e-30));
    const factor = -mu / (r * r * r);
    return [factor * px, factor * py];
}}

function deriv(s) {{
    const a = acceleration(s[0], s[1]);
    return [s[2], s[3], a[0], a[1]];
}}

function rk4Step(s, h) {{
    const k1 = deriv(s);
    const s2 = s.map((v, j) => v + 0.5 * h * k1[j]);
    const k2 = deriv(s2);
    const s3 = s.map((v, j) => v + 0.5 * h * k2[j]);
    const k3 = deriv(s3);
    const s4 = s.map((v, j) => v + h * k3[j]);
    const k4 = deriv(s4);

    return s.map((v, j) =>
        v + h * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j]) / 6
    );
}}

function physicsStep() {{
    if (collision) return;

    state = rk4Step(state, physicsDt);
    simulationTime += physicsDt;

    const r = Math.hypot(state[0], state[1]);

    if (r <= planetRadius) {{
        const scale = planetRadius / Math.max(r, 1e-30);
        state[0] *= scale;
        state[1] *= scale;
        state[2] = 0;
        state[3] = 0;
        collision = true;
        playing = false;
        playButton.textContent = "▶ Play";
        statusEl.textContent = "Collision";
    }}

    trail.push([state[0], state[1]]);
    if (trail.length > MAX_TRAIL_POINTS) trail.shift();
}}

function draw() {{
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    ctx.clearRect(0, 0, w, h);

    const margin = 70;
    const availableW = w - margin * 2;
    const availableH = h - margin * 2;

    // If the satellite reaches a new distance, expand the view smoothly.
    const currentRadius = Math.hypot(state[0], state[1]);
    if (currentRadius * 1.15 > displayMaxRadius) {{
        displayMaxRadius = currentRadius * 1.15;
    }}

    const scale = Math.min(
        availableW / (displayMaxRadius * 2),
        availableH / (displayMaxRadius * 2)
    );

    const cx = w / 2;
    const cy = h / 2;
    const planetR = Math.max(22, planetRadius * scale);

    // Trail
    if (trail.length > 1) {{
        ctx.strokeStyle = "#596273";
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        trail.forEach((p, i) => {{
            const tx = cx + p[0] * scale;
            const ty = cy - p[1] * scale;
            if (i === 0) ctx.moveTo(tx, ty);
            else ctx.lineTo(tx, ty);
        }});
        ctx.stroke();
    }}

    // Planet
    const gradient = ctx.createRadialGradient(
        cx - planetR * 0.3,
        cy - planetR * 0.3,
        3,
        cx,
        cy,
        planetR
    );
    gradient.addColorStop(0, "#69A7FF");
    gradient.addColorStop(1, "#2451A6");

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(cx, cy, planetR, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Satellite
    const sx = cx + state[0] * scale;
    const sy = cy - state[1] * scale;

    ctx.fillStyle = "#F4D35E";
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(sx, sy, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Gravity vector. Length is based on the actual current gravity.
    const dx = cx - sx;
    const dy = cy - sy;
    const distancePx = Math.hypot(dx, dy);
    const r = Math.hypot(state[0], state[1]);
    const gravity = mu / Math.max(r * r, 1e-30);

    if (distancePx > planetR + 15) {{
        const arrowLength = Math.min(
            140,
            Math.max(12, 12 + gravity * 12)
        );
        const ux = dx / distancePx;
        const uy = dy / distancePx;

        drawArrow(
            sx,
            sy,
            sx + ux * arrowLength,
            sy + uy * arrowLength,
            "#FF6B6B"
        );
    }}

    // Labels
    ctx.fillStyle = "#FFFFFF";
    ctx.font = "bold 14px Arial";
    ctx.textAlign = "center";
    ctx.fillText("PLANET", cx, cy + 5);

    ctx.textAlign = "left";
    ctx.fillText("🛰 Satellite", sx + 12, sy - 12);

    ctx.fillStyle = "#FF8A8A";
    ctx.fillText("Gravity", sx + 12, sy + 25);

    const speed = Math.hypot(state[2], state[3]);

    timeEl.textContent = simulationTime.toFixed(1) + " s";
    speedEl.textContent = speed.toFixed(1) + " m/s";
    distanceEl.textContent = formatDistance(r);
    gravityEl.textContent = gravity.toFixed(3) + " m/s²";
}}

function animate(timestamp) {{
    if (!playing) return;

    if (!lastTimestamp) lastTimestamp = timestamp;

    const deltaSeconds = Math.min(
        0.05,
        Math.max(0, (timestamp - lastTimestamp) / 1000)
    );
    lastTimestamp = timestamp;

    accumulator += deltaSeconds * playbackRatio;

    // Run the fixed 0.75 s physics steps until the requested playback time
    // has been caught up. There is deliberately no simulation-time endpoint.
    let steps = 0;
    const MAX_STEPS_PER_FRAME = 120;

    while (accumulator >= physicsDt && steps < MAX_STEPS_PER_FRAME) {{
        physicsStep();
        accumulator -= physicsDt;
        steps += 1;
        if (collision) break;
    }}

    draw();

    if (playing) requestAnimationFrame(animate);
}}

playButton.addEventListener("click", () => {{
    if (collision) {{
        // Collision is a physical endpoint. A fresh Run Experiment is needed
        // to create a new initial condition.
        return;
    }}

    playing = !playing;

    if (playing) {{
        playButton.textContent = "⏸ Pause";
        lastTimestamp = 0;
        requestAnimationFrame(animate);
    }} else {{
        playButton.textContent = "▶ Play";
        lastTimestamp = 0;
    }}
}});

window.addEventListener("resize", resize);
resize();
draw();
</script>
</body>
</html>
"""


def orbit_experiment():

    st.html(
        """
        <div style="text-align:center; margin:10px 0 55px 0;">
            <div style="font-size:42px; font-weight:700; color:white;">
                Gravity & Orbit
            </div>
            <div style="font-size:18px; color:#AAB4C3; margin-top:18px;">
                Explore how gravity and initial velocity determine a satellite's trajectory.
            </div>
        </div>
        """
    )

    defaults = {
        "planet_mass": 5.972e21,       # tonnes
        "planet_radius": 6371.0,       # km
        "satellite_mass": 1.0,         # tonnes
        "initial_altitude": 400.0,     # km
        "initial_velocity": 7.67,      # km/s
        "angle_deg": 90.0,
    }

    ai_prompt = st.text_input(
        "Describe your orbit experiment",
        placeholder=(
            "Example: Put a 1 t satellite 400 km above Earth "
            "with an initial velocity of 7.67 km/s."
        ),
    )

    if st.button(
                "Analyze with AI"
                use_container_width=True
                ):
        if not ai_prompt.strip():
            st.warning("Please describe an experiment first.")
        else:
            result = parse_ai_orbit(ai_prompt)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["orbit_ai"] = result

                # Apply AI-parsed values directly to the widget state so the
                # next Run Experiment always uses the newly analyzed values.
                if result.get("planet_mass") is not None:
                    st.session_state.orbit_planet_mass_t = float(result["planet_mass"]) / 1000.0
                if result.get("planet_radius") is not None:
                    st.session_state.orbit_planet_radius_km = float(result["planet_radius"]) / 1000.0
                if result.get("satellite_mass") is not None:
                    st.session_state.orbit_satellite_mass_t = float(result["satellite_mass"]) / 1000.0
                if result.get("initial_altitude") is not None:
                    st.session_state.orbit_initial_altitude_km = float(result["initial_altitude"]) / 1000.0
                if result.get("initial_velocity") is not None:
                    st.session_state.orbit_initial_velocity_kms = float(result["initial_velocity"]) / 1000.0
                if result.get("angle_deg") is not None:
                    st.session_state.orbit_angle_deg = float(result["angle_deg"])

                st.success("AI analysis completed and parameters updated.")

    ai_values = st.session_state.get("orbit_ai", {})

    # Keep each input in Streamlit session state. This prevents stale widget
    # defaults from being reused when the user changes a value and clicks Run.
    if "orbit_planet_mass_t" not in st.session_state:
        st.session_state.orbit_planet_mass_t = (
            float(ai_values["planet_mass"]) / 1000.0
            if ai_values.get("planet_mass") is not None
            else defaults["planet_mass"]
        )
    if "orbit_planet_radius_km" not in st.session_state:
        st.session_state.orbit_planet_radius_km = (
            float(ai_values["planet_radius"]) / 1000.0
            if ai_values.get("planet_radius") is not None
            else defaults["planet_radius"]
        )
    if "orbit_satellite_mass_t" not in st.session_state:
        st.session_state.orbit_satellite_mass_t = (
            float(ai_values["satellite_mass"]) / 1000.0
            if ai_values.get("satellite_mass") is not None
            else defaults["satellite_mass"]
        )
    if "orbit_initial_altitude_km" not in st.session_state:
        st.session_state.orbit_initial_altitude_km = (
            float(ai_values["initial_altitude"]) / 1000.0
            if ai_values.get("initial_altitude") is not None
            else defaults["initial_altitude"]
        )
    if "orbit_initial_velocity_kms" not in st.session_state:
        st.session_state.orbit_initial_velocity_kms = (
            float(ai_values["initial_velocity"]) / 1000.0
            if ai_values.get("initial_velocity") is not None
            else defaults["initial_velocity"]
        )
    if "orbit_angle_deg" not in st.session_state:
        st.session_state.orbit_angle_deg = (
            float(ai_values["angle_deg"])
            if ai_values.get("angle_deg") is not None
            else defaults["angle_deg"]
        )

    st.markdown("### Parameters")

    c1, c2, c3 = st.columns(3)

    with c1:
        planet_mass_t = st.number_input(
            "Planet Mass (t)",
            min_value=1.0,
            key="orbit_planet_mass_t",
            format="%.4e",
        )

        planet_radius_km = st.number_input(
            "Planet Radius (km)",
            min_value=1.0,
            key="orbit_planet_radius_km",
        )

    with c2:
        satellite_mass_t = st.number_input(
            "Satellite Mass (t)",
            min_value=0.001,
            key="orbit_satellite_mass_t",
        )

        initial_altitude_km = st.number_input(
            "Initial Altitude (km)",
            min_value=0.0,
            key="orbit_initial_altitude_km",
        )

    with c3:
        initial_velocity_kms = st.number_input(
            "Initial Velocity (km/s)",
            min_value=0.0,
            key="orbit_initial_velocity_kms",
        )

        angle_deg = st.slider(
            "Velocity Direction (degrees)",
            min_value=0.0,
            max_value=360.0,
            value=st.session_state.orbit_angle_deg,
            key="orbit_angle_deg",
            step=1.0,
        )

    # Convert fixed UI units to SI units for the physics engine.
    # Read the current widget values on every rerun. These are the exact
    # values visible in the controls when Run Experiment is pressed.
    planet_mass_si = float(planet_mass_t) * 1000.0
    planet_radius_si = float(planet_radius_km) * 1000.0
    satellite_mass_si = float(satellite_mass_t) * 1000.0
    initial_altitude_si = float(initial_altitude_km) * 1000.0
    initial_velocity_si = float(initial_velocity_kms) * 1000.0

    # Physics settings. The animation uses the same fixed 0.75-second
    # physics step, but it is integrated continuously in the browser with
    # no playback time limit. 20,000 s is kept only as the analysis/graph
    # window and is not an animation endpoint.
    duration = 20000.0
    dt = 0.75

    playback_ratio = st.slider(
        "Simulation Playback Speed (×)",
        min_value=100,
        max_value=2000,
        value=100,
        step=1,
        key="orbit_playback_ratio",
        help="Controls how many simulation seconds pass during 1 real second. 100× means 1 real second = 100 simulated seconds.",
    )

    if st.button(
        "Run Experiment",
        type="primary",
        use_container_width=True,
    ):
        try:
            result = simulate_orbit(
                planet_mass=planet_mass_si,
                planet_radius=planet_radius_si,
                satellite_mass=satellite_mass_si,
                initial_altitude=initial_altitude_si,
                initial_velocity=initial_velocity_si,
                angle_deg=angle_deg,
                duration=float(duration),
                dt=float(dt),
            )

            st.session_state["orbit_result"] = result
            st.session_state["orbit_result_signature"] = (
                float(planet_mass_si),
                float(planet_radius_si),
                float(satellite_mass_si),
                float(initial_altitude_si),
                float(initial_velocity_si),
                float(angle_deg),
            )

        except Exception as exc:
            st.error(f"Simulation error: {exc}")

    result = st.session_state.get("orbit_result")
    current_signature = (
        float(planet_mass_si),
        float(planet_radius_si),
        float(satellite_mass_si),
        float(initial_altitude_si),
        float(initial_velocity_si),
        float(angle_deg),
    )
    stored_signature = st.session_state.get("orbit_result_signature")

    # Never show a previous simulation as if it represented newly edited
    # parameters. A fresh Run Experiment is required after any change.
    if stored_signature != current_signature:
        result = None

    if result is not None:
        st.markdown("### 2D Orbit Simulation")

        html = orbit_animation_html(
            result,
            planet_radius_si,
            playback_ratio=float(playback_ratio),
            planet_mass=planet_mass_si,
            initial_altitude=initial_altitude_si,
            initial_velocity=initial_velocity_si,
            angle_deg=angle_deg,
        )

        components.html(
            html,
            height=710,
            scrolling=False,
        )

        st.markdown("### Orbit Analysis")

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.metric(
                "Orbit Type",
                result["orbit_type"],
            )

        with m2:
            st.metric(
                "Circular Velocity",
                f'{result["circular_velocity"] / 1000:.2f} km/s',
            )

        with m3:
            st.metric(
                "Escape Velocity",
                f'{result["escape_velocity"] / 1000:.2f} km/s',
            )

        with m4:
            st.metric(
                "Final Speed",
                f'{result["speed"][-1] / 1000:.2f} km/s',
            )

        st.markdown("### Energy")

        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=result["time"],
                    y=result["kinetic"],
                    name="Kinetic Energy",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=result["time"],
                    y=result["potential"],
                    name="Potential Energy",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=result["time"],
                    y=result["total_energy"],
                    name="Total Energy",
                )
            )

            fig.update_layout(
                xaxis_title="Time (s)",
                yaxis_title="Energy (J)",
                height=400,
                margin=dict(
                    l=20,
                    r=20,
                    t=30,
                    b=20,
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        except Exception as exc:
            st.warning(
                f"Energy graph could not be displayed: {exc}"
            )

    if st.button("Back to Experiments"):
        st.session_state.page = "select"
        st.session_state.experiment = None
        st.query_params.clear()
        st.rerun()
