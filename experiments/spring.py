import json
import re

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from app_modules import client


# =========================================================
# 1. Spring Simulation
# =========================================================

@st.cache_data
def simulate_spring(
    mass,
    k,
    initial_displacement,
    gravity,
    damping,
    duration=10.0,
    dt=0.02
):
    """
    Damped spring-mass simulation.

    Physics:
        F = -kx
        a = -kx/m - damping*v
    """

    n = int(duration / dt) + 1

    time = np.linspace(
        0,
        duration,
        n
    )

    x = np.zeros(n)
    v = np.zeros(n)
    a = np.zeros(n)

    x[0] = initial_displacement
    v[0] = 0.0

    for i in range(n - 1):

        a[i] = (
            -k * x[i] / mass
            - damping * v[i]
        )

        v[i + 1] = (
            v[i]
            + a[i] * dt
        )

        x[i + 1] = (
            x[i]
            + v[i] * dt
        )

    a[-1] = (
        -k * x[-1] / mass
        - damping * v[-1]
    )

    # Energy
    kinetic_energy = (
        0.5
        * mass
        * v ** 2
    )

    elastic_energy = (
        0.5
        * k
        * x ** 2
    )

    total_energy = (
        kinetic_energy
        + elastic_energy
    )

    return (
        time,
        x,
        v,
        a,
        kinetic_energy,
        elastic_energy,
        total_energy
    )


# =========================================================
# 2. AI Parser
# =========================================================

def parse_ai_spring(user_text):

    system_prompt = """
You are a physics parameter parser.

Extract ONLY explicitly stated numerical values.

Return JSON only:

{
    "mass": null,
    "k": null,
    "displacement": null,
    "gravity": null,
    "damping": null
}

Rules:

mass:
kg

k:
N/m

displacement:
m

gravity:
m/s^2

damping:
dimensionless

Do NOT guess missing values.

If a value is not explicitly given, return null.
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ],
            temperature=0
        )

        content = response.choices[0].message.content

        data = json.loads(content)

    except Exception:
        data = {}

    # -----------------------------------------------------
    # Explicit numerical overrides
    # -----------------------------------------------------

    patterns = {

        "mass": [
            r"(\d+(?:\.\d+)?)\s*(?:kg|킬로그램)"
        ],

        "k": [
            r"(\d+(?:\.\d+)?)\s*(?:N/m|n/m)"
        ],

        "displacement": [
            r"(\d+(?:\.\d+)?)\s*(?:m|미터)"
        ],

        "gravity": [
            r"(\d+(?:\.\d+)?)\s*(?:m/s\^?2|m/s²)"
        ],

        "damping": [
            r"(?:damping|감쇠)\s*(?:=|은|는)?\s*"
            r"(\d+(?:\.\d+)?)"
        ]
    }

    for key, regex_list in patterns.items():

        for pattern in regex_list:

            match = re.search(
                pattern,
                user_text,
                re.IGNORECASE
            )

            if match:

                try:
                    data[key] = float(
                        match.group(1)
                    )
                except ValueError:
                    pass

                break

    return data


# =========================================================
# 3. 3D Geometry Helpers
# =========================================================

def create_box(
    center_x,
    center_y,
    center_z,
    size_x,
    size_y,
    size_z
):

    x0 = center_x - size_x / 2
    x1 = center_x + size_x / 2

    y0 = center_y - size_y / 2
    y1 = center_y + size_y / 2

    z0 = center_z - size_z / 2
    z1 = center_z + size_z / 2

    vertices = np.array([
        [x0, y0, z0],
        [x1, y0, z0],
        [x1, y1, z0],
        [x0, y1, z0],
        [x0, y0, z1],
        [x1, y0, z1],
        [x1, y1, z1],
        [x0, y1, z1]
    ])

    faces = [
        (0, 1, 2),
        (0, 2, 3),

        (4, 5, 6),
        (4, 6, 7),

        (0, 1, 5),
        (0, 5, 4),

        (1, 2, 6),
        (1, 6, 5),

        (2, 3, 7),
        (2, 7, 6),

        (3, 0, 4),
        (3, 4, 7)
    ]

    i = []
    j = []
    k = []

    for a, b, c in faces:
        i.append(a)
        j.append(b)
        k.append(c)

    return go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=i,
        j=j,
        k=k,
        opacity=1.0,
        flatshading=True
    )


def create_cylinder_z(
    center_x,
    center_y,
    center_z,
    radius,
    height,
    segments=16
):

    theta = np.linspace(
        0,
        2 * np.pi,
        segments,
        endpoint=False
    )

    x = []
    y = []
    z = []

    # Bottom
    for t in theta:
        x.append(
            center_x + radius * np.cos(t)
        )
        y.append(
            center_y + radius * np.sin(t)
        )
        z.append(
            center_z - height / 2
        )

    # Top
    for t in theta:
        x.append(
            center_x + radius * np.cos(t)
        )
        y.append(
            center_y + radius * np.sin(t)
        )
        z.append(
            center_z + height / 2
        )

    vertices = np.column_stack(
        (x, y, z)
    )

    faces_i = []
    faces_j = []
    faces_k = []

    for n in range(segments):

        nxt = (n + 1) % segments

        # Side
        faces_i.append(n)
        faces_j.append(nxt)
        faces_k.append(
            n + segments
        )

        faces_i.append(nxt)
        faces_j.append(
            nxt + segments
        )
        faces_k.append(
            n + segments
        )

    return go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=faces_i,
        j=faces_j,
        k=faces_k,
        flatshading=True
    )


# =========================================================
# 4. Spring Coil
# =========================================================

def create_spring_coil(
    start_z,
    end_z,
    radius=0.20,
    turns=12,
    tube_radius=0.035
):

    length = abs(
        end_z - start_z
    )

    points_per_turn = 12

    n_points = max(
        int(turns * points_per_turn),
        24
    )

    theta = np.linspace(
        0,
        2 * np.pi * turns,
        n_points
    )

    z = np.linspace(
        start_z,
        end_z,
        n_points
    )

    x = radius * np.cos(theta)
    y = radius * np.sin(theta)

    # -----------------------------------------------------
    # Use a simple line instead of expensive tube geometry
    # -----------------------------------------------------

    return go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode="lines",
        line=dict(
            width=7
        )
    )


# =========================================================
# 5. Spring 3D Figure
# =========================================================

def create_spring_figure(
    displacement,
    spring_length=3.0
):

    ceiling_z = 1.8
    spring_start = 1.45

    mass_center = (
        ceiling_z
        - spring_length
        - displacement
    )

    mass_height = 0.45
    mass_radius = 0.32

    fig = go.Figure()

    # -----------------------------------------------------
    # Ceiling
    # -----------------------------------------------------

    fig.add_trace(
        create_box(
            0,
            0,
            ceiling_z + 0.18,
            2.4,
            1.4,
            0.35
        )
    )

    # -----------------------------------------------------
    # Mount
    # -----------------------------------------------------

    fig.add_trace(
        create_box(
            0,
            0,
            spring_start + 0.08,
            0.5,
            0.5,
            0.16
        )
    )

    # -----------------------------------------------------
    # Spring
    # -----------------------------------------------------

    fig.add_trace(
        create_spring_coil(
            spring_start,
            mass_center + mass_height / 2,
            radius=0.20,
            turns=12
        )
    )

    # -----------------------------------------------------
    # Mass
    # -----------------------------------------------------

    fig.add_trace(
        create_cylinder_z(
            0,
            0,
            mass_center,
            mass_radius,
            mass_height,
            segments=16
        )
    )

    # -----------------------------------------------------
    # Reference line
    # -----------------------------------------------------

    fig.add_trace(
        go.Scatter3d(
            x=[0, 0],
            y=[0, 0],
            z=[
                spring_start,
                mass_center
            ],
            mode="lines",
            line=dict(
                width=2,
                dash="dot"
            ),
            opacity=0.35
        )
    )

    fig.update_layout(

        height=450,

        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),

        scene=dict(

            xaxis=dict(
                visible=False,
                range=[-1.5, 1.5]
            ),

            yaxis=dict(
                visible=False,
                range=[-1.5, 1.5]
            ),

            zaxis=dict(
                visible=False,
                range=[-1.7, 2.1]
            ),

            aspectmode="manual",

            aspectratio=dict(
                x=1,
                y=1,
                z=2.6
            ),

            camera=dict(
                eye=dict(
                    x=0,
                    y=3.0,
                    z=0
                ),

                center=dict(
                    x=0,
                    y=0,
                    z=0.1
                ),

                up=dict(
                    x=0,
                    y=0,
                    z=1
                )
            )
        ),

        showlegend=False
    )

    return fig


# =========================================================
# 6. Spring Experiment
# =========================================================

def spring_experiment():

    # -----------------------------------------------------
    # Back button
    # -----------------------------------------------------

    if st.button(
        "Back to Experiments",
        key="spring_back_button"
    ):

        st.session_state.page = "select"
        st.session_state.experiment = None

        st.query_params.clear()

        st.rerun()

    st.subheader(
        "Spring Experiment"
    )

    # -----------------------------------------------------
    # Session defaults
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # AI Input
    # -----------------------------------------------------

    st.markdown(
        "### Describe Your Experiment"
    )

    ai_text = st.text_input(
        "Example: 질량 2kg, 스프링 상수 50N/m, "
        "0.3m 당겨서 시작해",
        key="spring_ai_input"
    )

    if st.button(
        "Run AI Analysis",
        key="spring_ai_button"
    ):

        if ai_text.strip():

            parsed = parse_ai_spring(
                ai_text
            )

            if parsed.get("mass") is not None:
                st.session_state.spring_mass = (
                    parsed["mass"]
                )

            if parsed.get("k") is not None:
                st.session_state.spring_k = (
                    parsed["k"]
                )

            if parsed.get("displacement") is not None:
                st.session_state.spring_displacement = (
                    parsed["displacement"]
                )

            if parsed.get("gravity") is not None:
                st.session_state.spring_gravity = (
                    parsed["gravity"]
                )

            if parsed.get("damping") is not None:
                st.session_state.spring_damping = (
                    parsed["damping"]
                )

            st.success(
                "Experiment parameters updated."
            )

    # -----------------------------------------------------
    # Manual Controls
    # -----------------------------------------------------

    st.markdown(
        "### Parameters"
    )

    col1, col2 = st.columns(2)

    with col1:

        mass = st.number_input(
            "Mass (kg)",
            min_value=0.01,
            value=float(
                st.session_state.spring_mass
            ),
            step=0.1,
            key="spring_mass_input"
        )

        k = st.number_input(
            "Spring Constant k (N/m)",
            min_value=0.01,
            value=float(
                st.session_state.spring_k
            ),
            step=1.0,
            key="spring_k_input"
        )

        displacement = st.number_input(
            "Initial Displacement (m)",
            value=float(
                st.session_state.spring_displacement
            ),
            step=0.05,
            key="spring_displacement_input"
        )

    with col2:

        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.0,
            value=float(
                st.session_state.spring_gravity
            ),
            step=0.1,
            key="spring_gravity_input"
        )

        damping = st.number_input(
            "Damping",
            min_value=0.0,
            value=float(
                st.session_state.spring_damping
            ),
            step=0.01,
            key="spring_damping_input"
        )

    # -----------------------------------------------------
    # Simulate
    # -----------------------------------------------------

    if st.button(
        "Run Experiment",
        type="primary",
        key="spring_run_button"
    ):

        (
            time,
            x,
            velocity,
            acceleration,
            kinetic_energy,
            elastic_energy,
            total_energy
        ) = simulate_spring(
            mass,
            k,
            displacement,
            gravity,
            damping
        )

        # =================================================
        # Metrics
        # =================================================

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Maximum Displacement",
                f"{np.max(np.abs(x)):.3f} m"
            )

        with col2:
            st.metric(
                "Maximum Velocity",
                f"{np.max(np.abs(velocity)):.3f} m/s"
            )

        with col3:
            st.metric(
                "Maximum Energy",
                f"{np.max(total_energy):.3f} J"
            )

        # =================================================
        # 3D Animation
        # =================================================

        st.markdown(
            "### 3D Spring"
        )

        # Only 40 frames instead of ~100
        frame_indices = np.linspace(
            0,
            len(time) - 1,
            40,
            dtype=int
        )

        initial_fig = create_spring_figure(
            x[frame_indices[0]]
        )

        frames = []

        for i in frame_indices:

            frame_fig = create_spring_figure(
                x[i]
            )

            frames.append(
                go.Frame(
                    data=frame_fig.data,
                    name=f"{time[i]:.2f}"
                )
            )

        initial_fig.frames = frames

        initial_fig.update_layout(

            updatemenus=[
                {
                    "type": "buttons",

                    "showactive": False,

                    "buttons": [
                        {
                            "label": "▶ Play",

                            "method": "animate",

                            "args": [
                                None,
                                {
                                    "frame": {
                                        "duration": 250,
                                        "redraw": True
                                    },

                                    "transition": {
                                        "duration": 0
                                    },

                                    "fromcurrent": True,

                                    "mode": "immediate"
                                }
                            ]
                        }
                    ]
                }
            ]
        )

        st.plotly_chart(
            initial_fig,
            use_container_width=True,
            key="spring_3d"
        )

        # =================================================
        # Displacement Graph
        # =================================================

        st.markdown(
            "### Displacement vs Time"
        )

        displacement_fig = go.Figure()

        displacement_fig.add_trace(
            go.Scatter(
                x=time,
                y=x,
                mode="lines",
                name="Displacement"
            )
        )

        displacement_fig.update_layout(
            xaxis_title="Time (s)",
            yaxis_title="Displacement (m)",
            height=350
        )

        st.plotly_chart(
            displacement_fig,
            use_container_width=True,
            key="spring_displacement_graph"
        )

        # =================================================
        # Energy Graph
        # =================================================

        st.markdown(
            "### Energy"

        )

        energy_fig = go.Figure()

        energy_fig.add_trace(
            go.Scatter(
                x=time,
                y=kinetic_energy,
                mode="lines",
                name="Kinetic Energy"
            )
        )

        energy_fig.add_trace(
            go.Scatter(
                x=time,
                y=elastic_energy,
                mode="lines",
                name="Elastic Energy"
            )
        )

        energy_fig.add_trace(
            go.Scatter(
                x=time,
                y=total_energy,
                mode="lines",
                name="Total Energy"
            )
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
