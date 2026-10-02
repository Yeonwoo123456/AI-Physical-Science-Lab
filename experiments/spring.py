import json
import re

import numpy as np
import streamlit as st
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
    time = np.arange(
        0,
        duration + dt,
        dt
    )

    x = np.zeros(len(time))
    v = np.zeros(len(time))

    equilibrium_displacement = (
        mass * gravity / k
    )

    x[0] = (
        equilibrium_displacement
        + initial_displacement
    )

    v[0] = 0.0

    def derivatives(state):
        position = state[0]
        velocity = state[1]

        acceleration = (
            gravity
            - (k / mass) * position
            - (damping / mass) * velocity
        )

        return np.array([
            velocity,
            acceleration
        ])

    for i in range(len(time) - 1):

        state = np.array([
            x[i],
            v[i]
        ])

        k1 = derivatives(state)

        k2 = derivatives(
            state + 0.5 * dt * k1
        )

        k3 = derivatives(
            state + 0.5 * dt * k2
        )

        k4 = derivatives(
            state + dt * k3
        )

        x[i + 1] = (
            state
            + (dt / 6.0)
            * (
                k1
                + 2 * k2
                + 2 * k3
                + k4
            )
        )[0]

        v[i + 1] = (
            state
            + (dt / 6.0)
            * (
                k1
                + 2 * k2
                + 2 * k3
                + k4
            )
        )[1]

    acceleration = (
        gravity
        - (k / mass) * x
        - (damping / mass) * v
    )

    relative_displacement = (
        x
        - equilibrium_displacement
    )

    kinetic_energy = (
        0.5
        * mass
        * v ** 2
    )

    spring_energy = (
        0.5
        * k
        * relative_displacement ** 2
    )

    total_energy = (
        kinetic_energy
        + spring_energy
    )

    return {
        "time": time,
        "x": x,
        "v": v,
        "a": acceleration,
        "kinetic_energy": kinetic_energy,
        "elastic_energy": spring_energy,
        "total_energy": total_energy,
        "equilibrium_displacement":
            equilibrium_displacement
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

Extract ONLY explicitly stated numerical values.

Return ONLY valid JSON:

{
    "mass": null,
    "k": null,
    "displacement": null,
    "gravity": null,
    "damping": null
}

Rules:

- mass unit: kg
- k unit: N/m
- displacement unit: m
- gravity unit: m/s^2
- damping unit: N*s/m
- Initial displacement is measured from the gravitational equilibrium position.
- Do not guess missing values.
- If the user says compress or 압축, displacement is negative.
- If the user says pull, stretch, 당겨, or 늘려, displacement is positive.
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

        content = (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

        content = re.sub(
            r"```json|```",
            "",
            content
        ).strip()

        ai_data = json.loads(content)

        for key in result:
            if ai_data.get(key) is not None:
                result[key] = float(
                    ai_data[key]
                )

    except Exception:
        pass

    patterns = {
        "mass": [
            r"(-?\d+(?:\.\d+)?)\s*(?:kg|킬로그램)"
        ],

        "k": [
            r"(-?\d+(?:\.\d+)?)\s*(?:N/m|n/m)"
        ],

        "displacement": [
            r"(-?\d+(?:\.\d+)?)\s*(?:m|미터)"
        ],

        "gravity": [
            r"(-?\d+(?:\.\d+)?)\s*(?:m/s\^?2|m/s²)"
        ],

        "damping": [
            r"(?:damping|감쇠)"
            r"\s*(?:=|은|는)?\s*"
            r"(-?\d+(?:\.\d+)?)"
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
                    result[key] = float(
                        match.group(1)
                    )
                except ValueError:
                    pass

                break

    if result["displacement"] is not None:

        lower_text = user_text.lower()

        if (
            "압축" in user_text
            or "compress" in lower_text
        ):
            result["displacement"] = -abs(
                result["displacement"]
            )

        elif (
            "당겨" in user_text
            or "늘려" in user_text
            or "stretch" in lower_text
            or "pull" in lower_text
        ):
            result["displacement"] = abs(
                result["displacement"]
            )

    return result


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
        flatshading=True,
        showlegend=False
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

    for t in theta:
        x.append(
            center_x
            + radius * np.cos(t)
        )
        y.append(
            center_y
            + radius * np.sin(t)
        )
        z.append(
            center_z - height / 2
        )

    for t in theta:
        x.append(
            center_x
            + radius * np.cos(t)
        )
        y.append(
            center_y
            + radius * np.sin(t)
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

        nxt = (
            n + 1
        ) % segments

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
        flatshading=True,
        showlegend=False
    )


def create_spring_coil(
    start_z,
    end_z,
    radius=0.20,
    turns=12
):

    n_points = max(
        int(turns * 12),
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

    return go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode="lines",
        line=dict(
            width=7
        ),
        showlegend=False
    )


def create_spring_figure(
    displacement_from_equilibrium,
    equilibrium_displacement,
    natural_length=1.2
):

    ceiling_z = 1.8
    spring_start = 1.45

    actual_displacement = (
        equilibrium_displacement
        + displacement_from_equilibrium
    )

    current_length = (
        natural_length
        + actual_displacement
    )

    current_length = max(
        current_length,
        0.25
    )

    mass_height = 0.45
    mass_radius = 0.32

    mass_center = (
        spring_start
        - current_length
        - mass_height / 2
    )

    equilibrium_length = (
        natural_length
        + equilibrium_displacement
    )

    equilibrium_mass_center = (
        spring_start
        - equilibrium_length
        - mass_height / 2
    )

    spring_end = (
        mass_center
        + mass_height / 2
    )

    fig = go.Figure()

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

    fig.add_trace(
        create_spring_coil(
            spring_start,
            spring_end
        )
    )

    fig.add_trace(
        create_cylinder_z(
            0,
            0,
            mass_center,
            mass_radius,
            mass_height
        )
    )

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
            opacity=0.35,
            showlegend=False
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[-0.75, 0.75],
            y=[0, 0],
            z=[
                equilibrium_mass_center,
                equilibrium_mass_center
            ],
            mode="lines",
            line=dict(
                width=2,
                dash="dash"
            ),
            opacity=0.45,
            showlegend=False
        )
    )

    fig.update_layout(

        height=500,

        margin=dict(
            l=12,
            r=12,
            t=12,
            b=12
        ),

        paper_bgcolor="#0E1117",

        scene=dict(

            bgcolor="#0E1117",

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

        showlegend=False,

        shapes=[
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0,
                y0=0,
                x1=1,
                y1=1,
                line=dict(
                    color="rgba(255,255,255,0.85)",
                    width=1
                ),
                fillcolor="rgba(0,0,0,0)"
            )
        ]
    )

    return fig


def spring_experiment():

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

    defaults = {
        "spring_mass": 1.0,
        "spring_k": 50.0,
        "spring_displacement": 0.30,
        "spring_gravity": 9.81,
        "spring_damping": 0.02,
        "spring_result": None
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value

    st.markdown(
        "### Describe Your Experiment"
    )

    ai_text = st.text_area(
        "AI Assistant",
        placeholder=(
            "Example: 질량 2kg, 스프링 상수 50N/m, "
            "평형 위치에서 0.3m 당겨서 시작해"
        ),
        key="spring_ai_input",
        height=100
    )

    if st.button(
        "Run AI Analysis",
        key="spring_ai_button"
    ):

        if ai_text.strip():

            parsed = parse_ai_spring(
                ai_text
            )

            if parsed["mass"] is not None:
                st.session_state.spring_mass = (
                    parsed["mass"]
                )

            if parsed["k"] is not None:
                st.session_state.spring_k = (
                    parsed["k"]
                )

            if parsed["displacement"] is not None:
                st.session_state.spring_displacement = (
                    parsed["displacement"]
                )

            if parsed["gravity"] is not None:
                st.session_state.spring_gravity = (
                    parsed["gravity"]
                )

            if parsed["damping"] is not None:
                st.session_state.spring_damping = (
                    parsed["damping"]
                )

            st.success(
                "Experiment parameters updated."
            )

    st.markdown(
        "### Parameters"
    )

    col1, col2 = st.columns(2)

    with col1:

        mass = st.number_input(
            "Mass (kg)",
            min_value=0.01,
            max_value=100.0,
            value=float(
                st.session_state.spring_mass
            ),
            step=0.1,
            key="spring_mass_input"
        )

        k = st.number_input(
            "Spring Constant k (N/m)",
            min_value=0.01,
            max_value=1000.0,
            value=float(
                st.session_state.spring_k
            ),
            step=1.0,
            key="spring_k_input"
        )

        displacement = st.number_input(
            "Initial Displacement from Equilibrium (m)",
            min_value=-5.0,
            max_value=5.0,
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
            max_value=30.0,
            value=float(
                st.session_state.spring_gravity
            ),
            step=0.1,
            key="spring_gravity_input"
        )

        damping = st.number_input(
            "Damping (N·s/m)",
            min_value=0.0,
            max_value=5.0,
            value=float(
                st.session_state.spring_damping
            ),
            step=0.01,
            key="spring_damping_input"
        )

    equilibrium_displacement = (
        mass * gravity / k
    )

    st.info(
        f"Equilibrium displacement: "
        f"{equilibrium_displacement:.3f} m"
    )

    if st.button(
        "Run Experiment",
        type="primary",
        key="spring_run_button"
    ):

        st.session_state.spring_result = (
            simulate_spring(
                mass=mass,
                k=k,
                initial_displacement=displacement,
                gravity=gravity,
                damping=damping
            )
        )

    result = st.session_state.spring_result

    if result is None:
        return

    time = result["time"]
    x = result["x"]
    velocity = result["v"]

    kinetic_energy = (
        result["kinetic_energy"]
    )

    elastic_energy = (
        result["elastic_energy"]
    )

    total_energy = (
        result["total_energy"]
    )

    equilibrium_displacement = (
        result["equilibrium_displacement"]
    )

    relative_displacement = (
        x
        - equilibrium_displacement
    )

    amplitude = np.max(
        np.abs(relative_displacement)
    )

    initial_energy = (
        0.5
        * k
        * displacement ** 2
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Maximum Oscillation",
            f"{amplitude:.3f} m"
        )

    with col2:
        st.metric(
            "Maximum Velocity",
            f"{np.max(np.abs(velocity)):.3f} m/s"
        )

    with col3:
        st.metric(
            "Initial Energy",
            f"{initial_energy:.3f} J"
        )

    st.markdown(
        "### 3D Spring"
    )

    frame_indices = np.linspace(
        0,
        len(time) - 1,
        100,
        dtype=int
    )

    initial_fig = create_spring_figure(
        relative_displacement[
            frame_indices[0]
        ],
        equilibrium_displacement
    )

    frames = []

    for i in frame_indices:

        frame_fig = create_spring_figure(
            relative_displacement[i],
            equilibrium_displacement
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
                                    "duration": 100,
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

    st.markdown(
        "### Displacement vs Time"
    )

    displacement_fig = go.Figure()

    displacement_fig.add_trace(
        go.Scatter(
            x=time,
            y=relative_displacement,
            mode="lines",
            name="Displacement"
        )
    )

    displacement_fig.add_hline(
        y=0,
        line_dash="dash",
        opacity=0.5
    )

    displacement_fig.update_layout(
        xaxis_title="Time (s)",
        yaxis_title=(
            "Displacement from Equilibrium (m)"
        ),
        height=350
    )

    st.plotly_chart(
        displacement_fig,
        use_container_width=True,
        key="spring_displacement_graph"
    )

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
            name="Spring Energy"
        )
    )

    energy_fig.add_trace(
        go.Scatter(
            x=time,
            y=total_energy,
            mode="lines",
            name="Total Mechanical Energy"
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
