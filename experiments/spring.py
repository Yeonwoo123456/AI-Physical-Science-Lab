import json
import re
import html

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

from app_modules import client


@st.cache_data
def simulate_spring(
    mass,
    k,
    initial_displacement,
    gravity,
    damping,
    duration=10.0,
    dt=0.01
):
    time = np.arange(0.0, duration + dt, dt)
    n = len(time)

    x = np.zeros(n)
    v = np.zeros(n)

    equilibrium_displacement = mass * gravity / k

    x[0] = equilibrium_displacement + initial_displacement
    v[0] = 0.0

    def acceleration(position, velocity):
        return gravity - (k / mass) * position - (damping / mass) * velocity

    for i in range(n - 1):
        x0 = x[i]
        v0 = v[i]

        k1_x = v0
        k1_v = acceleration(x0, v0)

        x2 = x0 + 0.5 * dt * k1_x
        v2 = v0 + 0.5 * dt * k1_v
        k2_x = v2
        k2_v = acceleration(x2, v2)

        x3 = x0 + 0.5 * dt * k2_x
        v3 = v0 + 0.5 * dt * k2_v
        k3_x = v3
        k3_v = acceleration(x3, v3)

        x4 = x0 + dt * k3_x
        v4 = v0 + dt * k3_v
        k4_x = v4
        k4_v = acceleration(x4, v4)

        x[i + 1] = x0 + (dt / 6.0) * (k1_x + 2 * k2_x + 2 * k3_x + k4_x)
        v[i + 1] = v0 + (dt / 6.0) * (k1_v + 2 * k2_v + 2 * k3_v + k4_v)

    a = acceleration(x, v)
    relative_displacement = x - equilibrium_displacement
    kinetic_energy = 0.5 * mass * v ** 2
    spring_energy = 0.5 * k * relative_displacement ** 2
    total_energy = kinetic_energy + spring_energy

    return {
        "time": time,
        "x": x,
        "v": v,
        "a": a,
        "relative_displacement": relative_displacement,
        "kinetic_energy": kinetic_energy,
        "spring_energy": spring_energy,
        "elastic_energy": spring_energy,
        "total_energy": total_energy,
        "total_mechanical_energy": total_energy,
        "equilibrium_displacement": equilibrium_displacement
    }


def parse_ai_spring(user_text):
    result = {
        "mass": None,
        "k": None,
        "displacement": None,
        "gravity": None,
        "damping": None
    }

    system_prompt = """
You are a physics parameter parser.

Return ONLY valid JSON:
{
    "mass": null,
    "k": null,
    "displacement": null,
    "gravity": null,
    "damping": null
}

Units:
mass: kg
k: N/m
displacement: m
gravity: m/s^2
damping: N*s/m

Initial displacement is measured from the gravitational equilibrium position.
Only extract explicitly stated numerical values.
Never guess missing values.
If the user says compress or 압축: displacement is negative.
If the user says pull, stretch, 당겨, 늘려: displacement is positive.
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
        "mass": [r"(-?\d+(?:\.\d+)?)\s*(?:kg|킬로그램)"],
        "k": [r"(-?\d+(?:\.\d+)?)\s*(?:N/m|n/m)"],
        "displacement": [r"(-?\d+(?:\.\d+)?)\s*(?:m(?!/s)|미터)"],
        "gravity": [r"(-?\d+(?:\.\d+)?)\s*(?:m/s\^?2|m/s²)"],
        "damping": [r"(?:damping|감쇠)\s*(?:=|은|는)?\s*(-?\d+(?:\.\d+)?)"]
    }

    for key, regex_list in patterns.items():
        for pattern in regex_list:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                try:
                    result[key] = float(match.group(1))
                except ValueError:
                    pass
                break

    text = user_text.lower()

    if result["displacement"] is not None:
        if "압축" in user_text or "compress" in text:
            result["displacement"] = -abs(result["displacement"])
        elif "당겨" in user_text or "늘려" in user_text or "stretch" in text or "pull" in text:
            result["displacement"] = abs(result["displacement"])

    return result


def spring_animation_html(relative_displacement, equilibrium_displacement, time=None):
    import json

    displacement = np.asarray(relative_displacement, dtype=float)

    if time is None:
        time = np.arange(len(displacement), dtype=float) * 0.01
    else:
        time = np.asarray(time, dtype=float)

    payload = json.dumps({
        "time": time.tolist(),
        "displacement": displacement.tolist(),
        "equilibrium": float(equilibrium_displacement)
    }, separators=(",", ":"))

    payload_js = json.dumps(payload)

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<style>
html, body {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #0E1117;
    font-family: Arial, sans-serif;
}}
#wrap {{
    position: relative;
    width: 100%;
    height: 500px;
    box-sizing: border-box;
    border: 2px solid #FFFFFF;
    border-radius: 10px;
    overflow: hidden;
    background: #0E1117;
}}
#scene {{
    width: 100%;
    height: 100%;
}}
#controls {{
    position: absolute;
    left: 16px;
    bottom: 16px;
    display: flex;
    gap: 8px;
}}
button {{
    border: 0;
    border-radius: 7px;
    padding: 8px 14px;
    background: #262B35;
    color: white;
    cursor: pointer;
    font-size: 13px;
}}
button:hover {{ background: #343B48; }}
#status {{
    position: absolute;
    right: 16px;
    bottom: 18px;
    color: #AAB2C0;
    font-size: 12px;
}}
</style>
</head>
<body>
<div id="wrap">
    <div id="scene"></div>
    <div id="controls">
        <button id="play">▶ Play</button>
        <button id="reset">↺ Reset</button>
    </div>
    <div id="status">0.00 s</div>
</div>
<script>
const DATA = JSON.parse({payload_js});

const sceneElement = document.getElementById('scene');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0E1117);

const camera = new THREE.PerspectiveCamera(
    42,
    sceneElement.clientWidth / sceneElement.clientHeight,
    0.1,
    100
);

camera.position.set(3.2, 0.65, 6.2);
camera.lookAt(0, 0.45, 0);

const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(sceneElement.clientWidth, sceneElement.clientHeight);
sceneElement.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0xffffff, 1.5));

const ceilingMaterial = new THREE.MeshStandardMaterial({{
    color: 0x9AA0A6,
    roughness: 0.8
}});

const mountMaterial = new THREE.MeshStandardMaterial({{
    color: 0x777D84,
    roughness: 0.7
}});

const massMaterial = new THREE.MeshStandardMaterial({{
    color: 0x4D9DE0,
    roughness: 0.35,
    metalness: 0.15
}});

const ceiling = new THREE.Mesh(
    new THREE.BoxGeometry(3.0, 0.30, 1.25),
    ceilingMaterial
);
ceiling.position.set(0, 2.05, 0);
scene.add(ceiling);

const mount = new THREE.Mesh(
    new THREE.BoxGeometry(0.5, 0.20, 0.5),
    mountMaterial
);
mount.position.set(0, 1.78, 0);
scene.add(mount);

const springGroup = new THREE.Group();
scene.add(springGroup);

const massHeight = 0.45;
const massRadius = 0.32;
const springStart = 1.67;
const naturalLength = 1.0;
const springRadius = 0.18;
const turns = 14;
const pointsPerTurn = 8;
const springPoints = turns * pointsPerTurn + 1;

const springGeometry = new THREE.BufferGeometry();
const springPositions = new Float32Array(springPoints * 3);
springGeometry.setAttribute(
    'position',
    new THREE.BufferAttribute(springPositions, 3)
);

const springMaterial = new THREE.LineBasicMaterial({{
    color: 0xE6E6E6,
    linewidth: 2
}});

const springLine = new THREE.Line(springGeometry, springMaterial);
springGroup.add(springLine);

const mass = new THREE.Mesh(
    new THREE.BoxGeometry(0.64, massHeight, 0.64),
    massMaterial
);
springGroup.add(mass);

const connectorGeometry = new THREE.BufferGeometry();
const connectorPositions = new Float32Array(6);
connectorGeometry.setAttribute(
    'position',
    new THREE.BufferAttribute(connectorPositions, 3)
);
const connector = new THREE.Line(
    connectorGeometry,
    new THREE.LineDashedMaterial({{
        color: 0xAAB2C0,
        transparent: true,
        opacity: 0.35,
        dashSize: 0.05,
        gapSize: 0.04
    }})
);
connector.computeLineDistances();
springGroup.add(connector);

const equilibriumLineMaterial = new THREE.LineDashedMaterial({{
    color: 0xAAB2C0,
    transparent: true,
    opacity: 0.45,
    dashSize: 0.06,
    gapSize: 0.05
}});

const equilibriumGeometry = new THREE.BufferGeometry();
const equilibriumPositions = new Float32Array(6);
equilibriumPositions[0] = -0.65;
equilibriumPositions[1] = 0;
equilibriumPositions[2] = 0;
equilibriumPositions[3] = 0.65;
equilibriumPositions[4] = 0;
equilibriumPositions[5] = 0;
equilibriumGeometry.setAttribute(
    'position',
    new THREE.BufferAttribute(equilibriumPositions, 3)
);
const equilibriumLine = new THREE.Line(
    equilibriumGeometry,
    equilibriumLineMaterial
);
scene.add(equilibriumLine);

const maxAmplitude = Math.max(
    Math.max(...DATA.displacement.map(Math.abs)),
    0.05
);
const visualScale = Math.min(0.55, 0.55 / maxAmplitude);

function interpolate(t) {{
    const times = DATA.time;
    const values = DATA.displacement;

    if (t <= times[0]) return values[0];
    if (t >= times[times.length - 1]) return values[values.length - 1];

    let lo = 0;
    let hi = times.length - 1;

    while (lo <= hi) {{
        const mid = (lo + hi) >> 1;
        if (times[mid] < t) lo = mid + 1;
        else hi = mid - 1;
    }}

    const i = Math.max(0, lo - 1);
    const f = (t - times[i]) / (times[i + 1] - times[i]);
    return values[i] + (values[i + 1] - values[i]) * f;
}}

function updateObject(t) {{
    const relative = interpolate(t);
    const visualRelative = relative * visualScale;
    const equilibriumVisual = DATA.equilibrium * 0.55;
    const currentLength = naturalLength + equilibriumVisual + visualRelative;

    const massCenter = springStart - currentLength - massHeight / 2;
    const springEnd = massCenter + massHeight / 2;

    for (let i = 0; i < springPoints; i++) {{
        const u = i / (springPoints - 1);
        const angle = u * Math.PI * 2 * turns;
        springPositions[i * 3] = springRadius * Math.cos(angle);
        springPositions[i * 3 + 1] = springStart + (springEnd - springStart) * u;
        springPositions[i * 3 + 2] = springRadius * Math.sin(angle);
    }}

    springGeometry.attributes.position.needsUpdate = true;

    mass.position.set(0, massCenter, 0);

    connectorPositions[0] = 0;
    connectorPositions[1] = springStart;
    connectorPositions[2] = 0;
    connectorPositions[3] = 0;
    connectorPositions[4] = massCenter;
    connectorPositions[5] = 0;
    connectorGeometry.attributes.position.needsUpdate = true;
    connector.computeLineDistances();

    const equilibriumLength = naturalLength + equilibriumVisual;
    const equilibriumMassCenter = springStart - equilibriumLength - massHeight / 2;
    equilibriumPositions[1] = equilibriumMassCenter;
    equilibriumPositions[4] = equilibriumMassCenter;
    equilibriumGeometry.attributes.position.needsUpdate = true;

    document.getElementById('status').textContent = t.toFixed(2) + ' s';
}}

let playing = true;
let startWall = performance.now();
let pausedAt = 0;
const duration = DATA.time[DATA.time.length - 1];

function animate(now) {{
    requestAnimationFrame(animate);

    if (playing) {{
        let elapsed = (now - startWall) / 1000;
        if (elapsed >= duration) {{
            elapsed = duration;
            playing = false;
            document.getElementById('play').textContent = '▶ Play';
        }}
        updateObject(elapsed);
    }}

    renderer.render(scene, camera);
}}

function startAnimation() {{
    startWall = performance.now() - pausedAt * 1000;
    playing = true;
    document.getElementById('play').textContent = '⏸ Pause';
}}

document.getElementById('play').addEventListener('click', () => {{
    if (playing) {{
        pausedAt = Math.min(duration, (performance.now() - startWall) / 1000);
        playing = false;
        document.getElementById('play').textContent = '▶ Play';
    }} else {{
        startAnimation();
    }}
}});

document.getElementById('reset').addEventListener('click', () => {{
    pausedAt = 0;
    updateObject(0);
    startAnimation();
}});

window.addEventListener('resize', () => {{
    const w = sceneElement.clientWidth;
    const h = sceneElement.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
}});

updateObject(0);
startAnimation();
requestAnimationFrame(animate);
</script>
</body>
</html>
"""


def back_to_experiments_button():
    if st.button("Back to Experiments", key="spring_back_button"):
        st.session_state.page = "select"
        st.session_state.experiment = None
        st.session_state.pop("spring_result", None)
        st.query_params.clear()
        st.rerun()


def spring_experiment():

    st.html(
        """
        <div style="text-align:center; margin:10px 0 55px 0;">
            <div style="font-size:42px; font-weight:700; color:white;">
                Spring Motion
            </div>
            <div style="font-size:18px; color:#AAB4C3; margin-top:18px;">
                Explore how mass, spring constant, displacement, gravity, and damping affect spring motion.
            </div>
        </div>
        """
    )

    defaults = {
        "spring_mass": 1.0,
        "spring_k": 50.0,
        "spring_displacement": 0.30,
        "spring_gravity": 9.81,
        "spring_damping": 0.02
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    required_keys = {
        "time", "x", "v", "a", "relative_displacement",
        "kinetic_energy", "spring_energy", "elastic_energy",
        "total_energy", "total_mechanical_energy",
        "equilibrium_displacement"
    }

    result = st.session_state.get("spring_result")
    if not isinstance(result, dict) or not required_keys.issubset(result.keys()):
        st.session_state.pop("spring_result", None)

    st.markdown("### AI Experiment Assistant")

    ai_text = st.text_area(
        "AI Natural Language",
        placeholder=(
            "Example: 질량 5kg, 스프링 상수 100N/m, "
            "평형 위치에서 0.5m 당겨서 시작해"
        ),
        key="spring_ai_input",
        height=100
    )

    if st.button(
        "Analyze with AI",
        key="spring_ai_button",
        use_container_width=True
    ):
        if ai_text.strip():
            parsed = parse_ai_spring(ai_text)

            if parsed["mass"] is not None:
                st.session_state.spring_mass = parsed["mass"]
            if parsed["k"] is not None:
                st.session_state.spring_k = parsed["k"]
            if parsed["displacement"] is not None:
                st.session_state.spring_displacement = parsed["displacement"]
            if parsed["gravity"] is not None:
                st.session_state.spring_gravity = parsed["gravity"]
            if parsed["damping"] is not None:
                st.session_state.spring_damping = parsed["damping"]

            st.session_state.pop("spring_result", None)
            st.success("Experiment parameters updated.")

    st.markdown("### Parameters")

    col1, col2 = st.columns(2)

    with col1:
        mass = st.number_input(
            "Mass (kg)", min_value=0.01, max_value=100.0,
            step=0.1, key="spring_mass"
        )
        k = st.number_input(
            "Spring Constant k (N/m)", min_value=0.01, max_value=1000.0,
            step=1.0, key="spring_k"
        )
        displacement = st.number_input(
            "Initial Displacement from Equilibrium (m)",
            min_value=-20.0, max_value=20.0, step=0.05,
            key="spring_displacement"
        )

    with col2:
        gravity = st.number_input(
            "Gravity (m/s²)", min_value=0.0, max_value=30.0,
            step=0.1, key="spring_gravity"
        )
        damping = st.number_input(
            "Damping (N·s/m)", min_value=0.0, max_value=5.0,
            step=0.01, key="spring_damping"
        )

    equilibrium_displacement = mass * gravity / k

    st.info(f"Equilibrium displacement: {equilibrium_displacement:.3f} m")

    if st.button(
    "Run Experiment",
    key="spring_run_button",
    use_container_width=True
):
        try:
            result = simulate_spring(
                mass=mass,
                k=k,
                initial_displacement=displacement,
                gravity=gravity,
                damping=damping
            )

            if not required_keys.issubset(result.keys()):
                raise ValueError()

            st.session_state.spring_result = result
        except Exception:
            st.session_state.pop("spring_result", None)
            st.error("The simulation could not be completed. Please check the parameters.")
            st.markdown("<div style='min-height: 20px;'></div>", unsafe_allow_html=True)
            back_to_experiments_button()
            return

    result = st.session_state.get("spring_result")
    if not isinstance(result, dict) or not required_keys.issubset(result.keys()):
        st.markdown("<div style='min-height: 20px;'></div>", unsafe_allow_html=True)
        back_to_experiments_button()
        return

    time = result["time"]
    velocity = result["v"]
    relative_displacement = result["relative_displacement"]
    kinetic_energy = result["kinetic_energy"]
    spring_energy = result["spring_energy"]
    total_energy = result["total_energy"]
    equilibrium_displacement = result["equilibrium_displacement"]

    amplitude = np.max(np.abs(relative_displacement))
    initial_energy = 0.5 * k * displacement ** 2
    maximum_energy = np.max(total_energy)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Maximum Oscillation", f"{amplitude:.3f} m")
    with col2:
        st.metric("Maximum Velocity", f"{np.max(np.abs(velocity)):.3f} m/s")
    with col3:
        st.metric("Initial Energy", f"{initial_energy:.3f} J")

    st.caption(f"Maximum calculated energy: {maximum_energy:.3f} J")

    st.markdown("### 3D Spring")
    components.html(
        spring_animation_html(
            relative_displacement,
            equilibrium_displacement,
            time
        ),
        height=510,
        scrolling=False
    )

    st.markdown("### Displacement vs Time")

    displacement_fig = go.Figure()
    displacement_fig.add_trace(
        go.Scatter(
            x=time,
            y=relative_displacement,
            mode="lines",
            name="Displacement"
        )
    )
    displacement_fig.add_hline(y=0, line_dash="dash", opacity=0.5)
    displacement_fig.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Displacement from Equilibrium (m)",
        height=350
    )
    st.plotly_chart(
        displacement_fig,
        use_container_width=True,
        key="spring_displacement_graph"
    )

    st.markdown("### Energy")

    energy_fig = go.Figure()
    energy_fig.add_trace(
        go.Scatter(x=time, y=kinetic_energy, mode="lines", name="Kinetic Energy")
    )
    energy_fig.add_trace(
        go.Scatter(x=time, y=spring_energy, mode="lines", name="Spring Energy")
    )
    energy_fig.add_trace(
        go.Scatter(x=time, y=total_energy, mode="lines", name="Total Energy")
    )
    energy_fig.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Energy (J)",
        height=350
    )
    st.plotly_chart(
        energy_fig,
        use_container_width=True,
        key="spring_energy_graph"
    )

    st.markdown("<div style='min-height: 28px;'></div>", unsafe_allow_html=True)
    back_to_experiments_button()
