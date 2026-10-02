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


def orbit_animation_html(data, planet_radius, playback_ratio=45.0):
    payload = json.dumps(
        {
            "time": data["time"],
            "x": data["x"],
            "y": data["y"],
            "speed": data["speed"],
            "distance": data["distance"],
            "acceleration": data["acceleration"],
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
        <button id="reset">↻ Reset</button>
        <span id="status"
              style="margin-left:auto;font-weight:bold;">
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
const data = {payload};
const planetRadius = {planet_radius};
const playbackRatio = {playback_ratio};

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const playButton = document.getElementById("play");
const resetButton = document.getElementById("reset");

const timeEl = document.getElementById("time");
const speedEl = document.getElementById("speed");
const distanceEl = document.getElementById("distance");
const gravityEl = document.getElementById("gravity");

let index = 0;
let playing = false;
let lastTimestamp = 0;
let simulationTime = 0;

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

function draw() {{
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;

    ctx.clearRect(0, 0, w, h);

    const i = Math.min(index, data.x.length - 1);

    const x = data.x[i];
    const y = data.y[i];

    const margin = 70;
    const availableW = w - margin * 2;
    const availableH = h - margin * 2;

    const maxX = Math.max(
        planetRadius * 2,
        ...data.x.map(Math.abs)
    );
    const maxY = Math.max(
        planetRadius * 2,
        ...data.y.map(Math.abs)
    );

    const scale = Math.min(
        availableW / (maxX * 2),
        availableH / (maxY * 2)
    );

    const cx = w / 2;
    const cy = h / 2;

    const planetR = Math.max(
        22,
        planetRadius * scale
    );

    // Orbit trail
    ctx.strokeStyle = "#596273";
    ctx.lineWidth = 1.8;
    ctx.beginPath();

    for (let j = 0; j <= i; j++) {{
        const tx = cx + data.x[j] * scale;
        const ty = cy - data.y[j] * scale;

        if (j === 0) ctx.moveTo(tx, ty);
        else ctx.lineTo(tx, ty);
    }}

    ctx.stroke();

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
    const sx = cx + x * scale;
    const sy = cy - y * scale;

    ctx.fillStyle = "#F4D35E";
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.arc(sx, sy, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Gravity vector: points toward planet.
    const dx = cx - sx;
    const dy = cy - sy;
    const distancePx = Math.hypot(dx, dy);

    if (distancePx > planetR + 15) {{
        const arrowLength = Math.min(
            65,
            Math.max(18, data.acceleration[i] * 10)
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

    ctx.fillText(
        "PLANET",
        cx,
        cy + 5
    );

    ctx.textAlign = "left";
    ctx.fillText(
        "🛰 Satellite",
        sx + 12,
        sy - 12
    );

    ctx.fillStyle = "#FF8A8A";
    ctx.fillText(
        "Gravity",
        sx + 12,
        sy + 25
    );

    timeEl.textContent =
        data.time[i].toFixed(1) + " s";

    speedEl.textContent =
        data.speed[i].toFixed(1) + " m/s";

    distanceEl.textContent =
        formatDistance(data.distance[i]);

    gravityEl.textContent =
        data.acceleration[i].toFixed(3) + " m/s²";
}}

function animate(timestamp) {{
    if (!playing) return;

    if (!lastTimestamp) {{
        lastTimestamp = timestamp;
    }}

    const deltaSeconds = Math.min(0.05, (timestamp - lastTimestamp) / 1000);
    lastTimestamp = timestamp;

    // playbackRatio means simulated seconds per real second.
    simulationTime += deltaSeconds * playbackRatio;

    const dt = data.time.length > 1
        ? data.time[1] - data.time[0]
        : 1;

    index = Math.floor(simulationTime / dt);

    if (index >= data.time.length - 1) {{
        index = data.time.length - 1;
        simulationTime = data.time[index];
        playing = false;
        playButton.textContent = "▶ Play";
    }}

    draw();

    if (playing) {{
        requestAnimationFrame(animate);
    }}
}}

playButton.addEventListener("click", () => {{
    if (index >= data.time.length - 1) {{
        index = 0;
    }}

    playing = !playing;

    if (playing) {{
        playButton.textContent = "⏸ Pause";
        lastTimestamp = 0;
        requestAnimationFrame(animate);
    }} else {{
        playButton.textContent = "▶ Play";
    }}
}});

resetButton.addEventListener("click", () => {{
    playing = false;
    index = 0;
    lastTimestamp = 0;
    simulationTime = 0;
    playButton.textContent = "▶ Play";
    draw();
}});

window.addEventListener("resize", resize);
resize();
</script>
</body>
</html>
"""


def orbit_experiment():
    st.subheader("Gravity & Orbit")

    st.write(
        "Explore how gravity and initial velocity determine a satellite's trajectory."
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

    if st.button("Run AI Analysis"):
        if not ai_prompt.strip():
            st.warning("Please describe an experiment first.")
        else:
            result = parse_ai_orbit(ai_prompt)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["orbit_ai"] = result
                st.success("AI analysis completed.")

    ai_values = st.session_state.get("orbit_ai", {})

    # AI parser returns SI units, so convert them back to the UI units.
    planet_mass_default = (
        float(ai_values["planet_mass"]) / 1000.0
        if ai_values.get("planet_mass") is not None
        else defaults["planet_mass"]
    )

    planet_radius_default = (
        float(ai_values["planet_radius"]) / 1000.0
        if ai_values.get("planet_radius") is not None
        else defaults["planet_radius"]
    )

    satellite_mass_default = (
        float(ai_values["satellite_mass"]) / 1000.0
        if ai_values.get("satellite_mass") is not None
        else defaults["satellite_mass"]
    )

    altitude_default = (
        float(ai_values["initial_altitude"]) / 1000.0
        if ai_values.get("initial_altitude") is not None
        else defaults["initial_altitude"]
    )

    velocity_default = (
        float(ai_values["initial_velocity"]) / 1000.0
        if ai_values.get("initial_velocity") is not None
        else defaults["initial_velocity"]
    )

    angle_default = (
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
            value=planet_mass_default,
            format="%.4e",
        )

        planet_radius_km = st.number_input(
            "Planet Radius (km)",
            min_value=1.0,
            value=planet_radius_default,
        )

    with c2:
        satellite_mass_t = st.number_input(
            "Satellite Mass (t)",
            min_value=0.001,
            value=satellite_mass_default,
        )

        initial_altitude_km = st.number_input(
            "Initial Altitude (km)",
            min_value=0.0,
            value=altitude_default,
        )

    with c3:
        initial_velocity_kms = st.number_input(
            "Initial Velocity (km/s)",
            min_value=0.0,
            value=velocity_default,
        )

        angle_deg = st.slider(
            "Velocity Direction (degrees)",
            min_value=0.0,
            max_value=360.0,
            value=angle_default,
            step=1.0,
        )

    # Convert fixed UI units to SI units for the physics engine.
    planet_mass_si = planet_mass_t * 1000.0
    planet_radius_si = planet_radius_km * 1000.0
    satellite_mass_si = satellite_mass_t * 1000.0
    initial_altitude_si = initial_altitude_km * 1000.0
    initial_velocity_si = initial_velocity_kms * 1000.0

    # Fixed physics settings.
    # The physics engine always uses a 0.75-second time step and
    # a 20,000-second simulation. Only the playback speed is adjustable.
    duration = 20000.0
    dt = 0.75

    playback_ratio = st.slider(
        "Simulation Playback Speed (×)",
        min_value=45,
        max_value=200,
        value=45,
        step=1,
        help="Controls how many simulation seconds pass during 1 real second. 45× means 1 real second = 45 simulated seconds.",
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

        except Exception as exc:
            st.error(f"Simulation error: {exc}")

    result = st.session_state.get("orbit_result")

    if result is not None:
        st.markdown("### 2D Orbit Simulation")

        html = orbit_animation_html(
            result,
            planet_radius_si,
            playback_ratio=float(playback_ratio),
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

