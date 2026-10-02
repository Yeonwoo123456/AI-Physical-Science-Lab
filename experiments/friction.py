import json
import re

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from app_modules import client


@st.cache_data
def simulate_friction(
    mass,
    mu_static,
    mu_kinetic,
    applied_force,
    gravity,
    duration=8.0,
    dt=0.01
):
    time = np.arange(0.0, duration + dt, dt)
    n = len(time)

    normal_force = mass * gravity
    max_static_friction = mu_static * normal_force
    kinetic_friction = mu_kinetic * normal_force

    position = np.zeros(n)
    velocity = np.zeros(n)
    acceleration = np.zeros(n)
    friction = np.zeros(n)
    net_force = np.zeros(n)

    moving = False

    for i in range(n):
        if not moving:
            if abs(applied_force) <= max_static_friction:
                friction[i] = -applied_force
                net_force[i] = 0.0
                acceleration[i] = 0.0
                velocity[i] = 0.0
                if i > 0:
                    position[i] = position[i - 1]
                continue
            moving = True

        direction = (
            np.sign(velocity[i - 1])
            if i > 0 and abs(velocity[i - 1]) > 1e-9
            else np.sign(applied_force)
        )

        friction[i] = -direction * kinetic_friction
        net_force[i] = applied_force + friction[i]
        acceleration[i] = net_force[i] / mass

        if i > 0:
            velocity[i] = velocity[i - 1] + acceleration[i] * dt
            position[i] = (
                position[i - 1]
                + velocity[i - 1] * dt
                + 0.5 * acceleration[i] * dt * dt
            )

            # The object stops immediately when it touches either wall.
            left_wall = -8.0
            right_wall = 8.0
            half_block = 0.55

            if position[i] - half_block <= left_wall:
                position[i] = left_wall + half_block
                velocity[i] = 0.0
                acceleration[i] = 0.0
                net_force[i] = 0.0
            elif position[i] + half_block >= right_wall:
                position[i] = right_wall - half_block
                velocity[i] = 0.0
                acceleration[i] = 0.0
                net_force[i] = 0.0

    state = np.where(
        np.abs(velocity) > 1e-6,
        "KINETIC",
        "STATIC"
    )

    return {
        "time": time,
        "position": position,
        "velocity": velocity,
        "acceleration": acceleration,
        "friction": friction,
        "net_force": net_force,
        "normal_force": np.full(n, normal_force),
        "weight": np.full(n, -normal_force),
        "max_static_friction": max_static_friction,
        "kinetic_friction": kinetic_friction,
        "state": state
    }


def parse_ai_friction(user_text):
    result = {
        "mass": None,
        "mu_static": None,
        "mu_kinetic": None,
        "applied_force": None,
        "gravity": None
    }

    system_prompt = """
You are a physics parameter parser for a friction experiment.

Return ONLY valid JSON:
{
    "mass": null,
    "mu_static": null,
    "mu_kinetic": null,
    "applied_force": null,
    "gravity": null
}

Units:
mass: kg
mu_static: dimensionless
mu_kinetic: dimensionless
applied_force: N
gravity: m/s^2

Only extract explicitly stated numerical values.
Never guess missing values.

If the user says left / 왼쪽, applied_force should be negative.
If the user says right / 오른쪽, applied_force should be positive.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"```json|```", "", content).strip()
        parsed = json.loads(content)

        for key in result:
            value = parsed.get(key)
            if value is not None:
                result[key] = float(value)

    except Exception:
        pass

    patterns = {
        "mass": r"(-?\d+(?:\.\d+)?)\s*(?:kg|킬로그램)",
        "mu_static": r"(?:μs|mu_s|mus|정지\s*마찰계수)\s*(?:=|은|는)?\s*(-?\d+(?:\.\d+)?)",
        "mu_kinetic": r"(?:μk|mu_k|muk|운동\s*마찰계수)\s*(?:=|은|는)?\s*(-?\d+(?:\.\d+)?)",
        "applied_force": r"(-?\d+(?:\.\d+)?)\s*(?:N|뉴턴)",
        "gravity": r"(-?\d+(?:\.\d+)?)\s*(?:m/s\^?2|m/s²)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, user_text, re.IGNORECASE)
        if match:
            try:
                result[key] = float(match.group(1))
            except ValueError:
                pass

    text = user_text.lower()

    if result["applied_force"] is not None:
        if "왼쪽" in user_text or "left" in text:
            result["applied_force"] = -abs(result["applied_force"])
        elif "오른쪽" in user_text or "right" in text:
            result["applied_force"] = abs(result["applied_force"])

    return result


def friction_animation_html(
    time,
    position,
    applied_force,
    friction,
    normal_force,
    weight,
    net_force,
    max_static_friction
):
    payload = json.dumps({
        "time": np.asarray(time, dtype=float).tolist(),
        "position": np.asarray(position, dtype=float).tolist(),
        "applied": np.full(len(time), applied_force, dtype=float).tolist(),
        "friction": np.asarray(friction, dtype=float).tolist(),
        "normal": np.asarray(normal_force, dtype=float).tolist(),
        "weight": np.asarray(weight, dtype=float).tolist(),
        "net": np.asarray(net_force, dtype=float).tolist(),
        "max_static": float(max_static_friction)
    }, separators=(",", ":"))

    html = """
<!DOCTYPE html>
<html>
<head>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    background: #0E1117;
    color: #FFFFFF;
    font-family: Arial, sans-serif;
}
#wrap {
    border: 2px solid #FFFFFF;
    border-radius: 10px;
    overflow: hidden;
    background: #0E1117;
}
#canvas {
    width: 100%;
    height: 560px;
    display: block;
    background: #0E1117;
}
#controls {
    padding: 12px 16px 15px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-top: 1px solid #444;
}
button {
    border: 1px solid #888;
    background: #20242D;
    color: white;
    border-radius: 6px;
    padding: 8px 16px;
    cursor: pointer;
}
button:hover { background: #303641; }
#status {
    margin-left: auto;
    font-weight: bold;
}
#values {
    padding: 0 16px 14px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
}
.value {
    background: #171B23;
    border-radius: 6px;
    padding: 9px;
    text-align: center;
    font-size: 13px;
}
.value b {
    display: block;
    margin-top: 4px;
    font-size: 15px;
}
</style>
</head>
<body>
<div id="wrap">
<canvas id="canvas"></canvas>

<div id="controls">
    <button id="play">▶ Play</button>
    <button id="reset">↺ Reset</button>
    <span id="status">STATIC</span>
</div>

<div id="values">
    <div class="value">Applied Force<b id="applied">0 N</b></div>
    <div class="value">Friction<b id="friction">0 N</b></div>
    <div class="value">Net Force<b id="net">0 N</b></div>
    <div class="value">Time<b id="time">0.00 s</b></div>
</div>
</div>

<script>
const data = __PAYLOAD__;
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const playButton = document.getElementById("play");
const resetButton = document.getElementById("reset");
const statusEl = document.getElementById("status");

let index = 0;
let playing = false;
let raf = null;
let lastTimestamp = 0;
let elapsedAccumulator = 0;

function resize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, rect.width * dpr);
    canvas.height = Math.max(1, rect.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
}

function arrow(x1, y1, x2, y2, color, label) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const length = Math.hypot(dx, dy);

    if (length < 1) return;

    const ux = dx / length;
    const uy = dy / length;
    const head = 11;

    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(
        x2 - ux * head - uy * head * 0.55,
        y2 - uy * head + ux * head * 0.55
    );
    ctx.lineTo(
        x2 - ux * head + uy * head * 0.55,
        y2 - uy * head - ux * head * 0.55
    );
    ctx.closePath();
    ctx.fill();

    ctx.font = "bold 14px Arial";
    ctx.textAlign = "center";
    ctx.fillText(label, (x1 + x2) / 2, (y1 + y2) / 2 - 9);
}

function springLine(x1, x2, y) {
    const turns = 12;
    const amplitude = 12;
    const points = 100;

    ctx.strokeStyle = "#DDDDDD";
    ctx.lineWidth = 2.5;
    ctx.beginPath();

    for (let i = 0; i <= points; i++) {
        const p = i / points;
        const x = x1 + (x2 - x1) * p;
        const yy = y + Math.sin(p * Math.PI * 2 * turns) * amplitude;

        if (i === 0) ctx.moveTo(x, yy);
        else ctx.lineTo(x, yy);
    }

    ctx.stroke();
}

function getScale(applied, friction, normal, weight, net) {
    const maxForce = Math.max(
        1,
        Math.abs(applied),
        Math.abs(friction),
        Math.abs(normal),
        Math.abs(weight),
        Math.abs(net)
    );

    return Math.min(100, 170 / maxForce);
}

function draw() {
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;

    ctx.clearRect(0, 0, w, h);

    const i = Math.max(0, Math.min(index, data.time.length - 1));

    const applied = data.applied[i];
    const friction = data.friction[i];
    const normal = data.normal[i];
    const weight = data.weight[i];
    const net = data.net[i];

    const position = data.position[i];

    const centerX = w * 0.5;
    const baseY = h * 0.67;
    const blockW = 110;
    const blockH = 75;

    const wallMargin = 45;
    const leftWallX = wallMargin;
    const rightWallX = w - wallMargin;
    const positionScale = (rightWallX - leftWallX) / 16;
    const blockX = centerX + position * positionScale;

    // Surface and two walls.
    ctx.strokeStyle = "#777";
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(leftWallX, baseY + blockH / 2 + 2);
    ctx.lineTo(rightWallX, baseY + blockH / 2 + 2);
    ctx.stroke();

    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(leftWallX, baseY - blockH / 2 - 20);
    ctx.lineTo(leftWallX, baseY + blockH / 2 + 4);
    ctx.moveTo(rightWallX, baseY - blockH / 2 - 20);
    ctx.lineTo(rightWallX, baseY + blockH / 2 + 4);
    ctx.stroke();

    ctx.fillStyle = "#B8B8B8";
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(
        blockX - blockW / 2,
        baseY - blockH / 2,
        blockW,
        blockH,
        5
    );
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = "#111";
    ctx.font = "bold 16px Arial";
    ctx.textAlign = "center";
    ctx.fillText("BLOCK", blockX, baseY + 6);

    const scale = getScale(
        applied,
        friction,
        normal,
        weight,
        net
    );

    const horizontalMax = Math.min(
        w * 0.38,
        230
    );

    const horizontalScale = Math.min(
        scale,
        horizontalMax / Math.max(
            1,
            Math.abs(applied),
            Math.abs(friction)
        )
    );

    const verticalScale = Math.min(
        1.7,
        115 / Math.max(
            1,
            Math.abs(normal),
            Math.abs(weight)
        )
    );

    arrow(
        blockX,
        baseY - 38,
        blockX + applied * horizontalScale,
        baseY - 38,
        "#4DA6FF",
        "Applied " + Math.abs(applied).toFixed(1) + " N"
    );

    arrow(
        blockX,
        baseY + 38,
        blockX + friction * horizontalScale,
        baseY + 38,
        "#FF6B6B",
        "Friction " + Math.abs(friction).toFixed(1) + " N"
    );

    arrow(
        blockX,
        baseY - blockH / 2,
        blockX,
        baseY - blockH / 2 - normal * verticalScale,
        "#69D391",
        "Normal " + Math.abs(normal).toFixed(1) + " N"
    );

    arrow(
        blockX,
        baseY + blockH / 2,
        blockX,
        baseY + blockH / 2 - weight * verticalScale,
        "#C084FC",
        "Weight " + Math.abs(weight).toFixed(1) + " N"
    );

    const state =
        Math.abs(data.friction[i] - (-applied)) < 1e-6 &&
        Math.abs(data.net[i]) < 1e-6
            ? "STATIC"
            : "KINETIC";

    statusEl.textContent = state;
    statusEl.style.color =
        state === "STATIC" ? "#69D391" : "#FFB86B";

    document.getElementById("applied").textContent =
        applied.toFixed(2) + " N";

    document.getElementById("friction").textContent =
        Math.abs(friction).toFixed(2) + " N";

    document.getElementById("net").textContent =
        net.toFixed(2) + " N";

    document.getElementById("time").textContent =
        data.time[i].toFixed(2) + " s";
}

function step(timestamp) {
    if (!playing) return;

    if (!lastTimestamp) lastTimestamp = timestamp;

    const delta = Math.min(
        50,
        timestamp - lastTimestamp
    );

    lastTimestamp = timestamp;
    elapsedAccumulator += delta;

    const frameInterval = 1000 / 60;

    while (elapsedAccumulator >= frameInterval) {
        index++;

        if (index >= data.time.length) {
            index = data.time.length - 1;
            playing = false;
            playButton.textContent = "▶ Play";
            break;
        }

        elapsedAccumulator -= frameInterval;
    }

    draw();

    if (playing) {
        raf = requestAnimationFrame(step);
    }
}

playButton.addEventListener("click", () => {
    if (index >= data.time.length - 1) {
        index = 0;
    }

    playing = !playing;
    playButton.textContent = playing ? "⏸ Pause" : "▶ Play";

    if (playing) {
        lastTimestamp = 0;
        elapsedAccumulator = 0;
        raf = requestAnimationFrame(step);
    } else if (raf) {
        cancelAnimationFrame(raf);
        raf = null;
    }
});

resetButton.addEventListener("click", () => {
    playing = false;

    if (raf) {
        cancelAnimationFrame(raf);
        raf = null;
    }

    index = 0;
    lastTimestamp = 0;
    elapsedAccumulator = 0;
    playButton.textContent = "▶ Play";
    draw();
});

window.addEventListener("resize", resize);
resize();
</script>
</body>
</html>
"""

    html = html.replace(
        "__PAYLOAD__",
        payload
    )

    return html


def friction_experiment():

    st.subheader("Friction Experiment")

    defaults = {
        "friction_mass": 10.0,
        "friction_mu_static": 0.50,
        "friction_mu_kinetic": 0.30,
        "friction_force": 50.0,
        "friction_gravity": 9.81
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "friction_result" not in st.session_state:
        st.session_state.friction_result = None

    st.markdown("### Describe Your Experiment")

    ai_text = st.text_area(
        "AI Assistant",
        placeholder=(
            "Example: 질량 10kg인 블록을 μs 0.5, μk 0.3인 "
            "바닥에서 오른쪽으로 50N의 힘으로 밀어줘"
        ),
        key="friction_ai_input",
        height=100
    )

    if st.button(
        "Run AI Analysis",
        key="friction_ai_button"
    ):
        if ai_text.strip():
            parsed = parse_ai_friction(ai_text)

            if parsed["mass"] is not None:
                st.session_state.friction_mass = parsed["mass"]

            if parsed["mu_static"] is not None:
                st.session_state.friction_mu_static = parsed["mu_static"]

            if parsed["mu_kinetic"] is not None:
                st.session_state.friction_mu_kinetic = parsed["mu_kinetic"]

            if parsed["applied_force"] is not None:
                st.session_state.friction_force = parsed["applied_force"]

            if parsed["gravity"] is not None:
                st.session_state.friction_gravity = parsed["gravity"]

            st.session_state.friction_result = None
            st.success("Experiment parameters updated.")

    st.markdown("### Parameters")

    col1, col2 = st.columns(2)

    with col1:
        mass = st.number_input(
            "Mass (kg)",
            min_value=0.01,
            max_value=1000.0,
            step=0.1,
            key="friction_mass"
        )

        mu_static = st.number_input(
            "Coefficient of Static Friction μs",
            min_value=0.0,
            max_value=5.0,
            step=0.01,
            key="friction_mu_static"
        )

        mu_kinetic = st.number_input(
            "Coefficient of Kinetic Friction μk",
            min_value=0.0,
            max_value=5.0,
            step=0.01,
            key="friction_mu_kinetic"
        )

    with col2:
        applied_force = st.number_input(
            "Applied Force (N)",
            min_value=-1000.0,
            max_value=1000.0,
            step=1.0,
            key="friction_force"
        )

        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.0,
            max_value=30.0,
            step=0.1,
            key="friction_gravity"
        )

    normal_force = mass * gravity
    max_static = mu_static * normal_force
    kinetic = mu_kinetic * normal_force

    st.info(
        f"Normal Force: {normal_force:.2f} N  |  "
        f"Maximum Static Friction: {max_static:.2f} N  |  "
        f"Kinetic Friction: {kinetic:.2f} N"
    )

    if st.button(
        "Run Experiment",
        type="primary",
        key="friction_run_button"
    ):
        st.session_state.friction_result = simulate_friction(
            mass=mass,
            mu_static=mu_static,
            mu_kinetic=mu_kinetic,
            applied_force=applied_force,
            gravity=gravity
        )

    result = st.session_state.friction_result

    if result is None:
        current_friction = (
            -applied_force
            if abs(applied_force) <= max_static
            else -np.sign(applied_force) * kinetic
        )

        st.markdown("### 2D Friction Model")

        st.components.v1.html(
            friction_animation_html(
                np.array([0.0]),
                np.array([0.0]),
                applied_force,
                np.array([current_friction]),
                np.array([normal_force]),
                np.array([-normal_force]),
                np.array([0.0]),
                max_static
            ),
            height=590,
            scrolling=False
        )

    else:
        time = result["time"]
        position = result["position"]
        velocity = result["velocity"]
        acceleration = result["acceleration"]
        friction = result["friction"]
        net_force = result["net_force"]

        st.markdown("### 2D Friction Model")

        st.components.v1.html(
            friction_animation_html(
                time,
                position,
                applied_force,
                friction,
                result["normal_force"],
                result["weight"],
                net_force,
                result["max_static_friction"]
            ),
            height=590,
            scrolling=False
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "State",
                result["state"][-1]
            )

        with col2:
            st.metric(
                "Velocity",
                f"{velocity[-1]:.2f} m/s"
            )

        with col3:
            st.metric(
                "Acceleration",
                f"{acceleration[-1]:.2f} m/s²"
            )

        with col4:
            st.metric(
                "Net Force",
                f"{net_force[-1]:.2f} N"
            )

        st.markdown("### Position vs Time")

        position_fig = go.Figure()
        position_fig.add_trace(
            go.Scatter(
                x=time,
                y=position,
                mode="lines",
                name="Position"
            )
        )
        position_fig.update_layout(
            height=320,
            xaxis_title="Time (s)",
            yaxis_title="Position (m)"
        )
        st.plotly_chart(
            position_fig,
            use_container_width=True,
            key="friction_position_graph"
        )

        st.markdown("### Velocity vs Time")

        velocity_fig = go.Figure()
        velocity_fig.add_trace(
            go.Scatter(
                x=time,
                y=velocity,
                mode="lines",
                name="Velocity"
            )
        )
        velocity_fig.update_layout(
            height=320,
            xaxis_title="Time (s)",
            yaxis_title="Velocity (m/s)"
        )
        st.plotly_chart(
            velocity_fig,
            use_container_width=True,
            key="friction_velocity_graph"
        )

        st.markdown("### Force vs Time")

        force_fig = go.Figure()

        force_fig.add_trace(
            go.Scatter(
                x=time,
                y=np.full_like(time, applied_force),
                mode="lines",
                name="Applied Force"
            )
        )

        force_fig.add_trace(
            go.Scatter(
                x=time,
                y=friction,
                mode="lines",
                name="Friction"
            )
        )

        force_fig.add_trace(
            go.Scatter(
                x=time,
                y=net_force,
                mode="lines",
                name="Net Force"
            )
        )

        force_fig.add_hline(
            y=max_static,
            line_dash="dash",
            opacity=0.5
        )

        force_fig.add_hline(
            y=-max_static,
            line_dash="dash",
            opacity=0.5
        )

        force_fig.update_layout(
            height=350,
            xaxis_title="Time (s)",
            yaxis_title="Force (N)"
        )

        st.plotly_chart(
            force_fig,
            use_container_width=True,
            key="friction_force_graph"
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    if st.button(
        "Back to Experiments",
        key="friction_back_button"
    ):
        st.session_state.page = "select"
        st.session_state.experiment = None
        st.session_state.pop("friction_result", None)
        st.query_params.clear()
        st.rerun()
