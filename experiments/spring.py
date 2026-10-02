import json
import re

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from app_modules import client


DEFAULTS = {
    "spring_mass": 1.0,
    "spring_k": 10.0,
    "spring_displacement": 5.0,
    "spring_gravity": 9.87,
    "spring_damping": 0.02
}


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
    n = int(duration / dt) + 1

    time = np.linspace(
        0,
        duration,
        n
    )

    x = np.zeros(n)
    v = np.zeros(n)

    x[0] = initial_displacement

    def acceleration(xi, vi):
        return (
            -k * xi
            - damping * vi
        ) / mass

    for i in range(n - 1):

        xi = x[i]
        vi = v[i]

        k1x = vi
        k1v = acceleration(
            xi,
            vi
        )

        k2x = (
            vi
            + 0.5 * k1v * dt
        )

        k2v = acceleration(
            xi + 0.5 * k1x * dt,
            vi + 0.5 * k1v * dt
        )

        k3x = (
            vi
            + 0.5 * k2v * dt
        )

        k3v = acceleration(
            xi + 0.5 * k2x * dt,
            vi + 0.5 * k2v * dt
        )

        k4x = (
            vi
            + k3v * dt
        )

        k4v = acceleration(
            xi + k3x * dt,
            vi + k3v * dt
        )

        x[i + 1] = (
            xi
            + dt / 6
            * (
                k1x
                + 2 * k2x
                + 2 * k3x
                + k4x
            )
        )

        v[i + 1] = (
            vi
            + dt / 6
            * (
                k1v
                + 2 * k2v
                + 2 * k3v
                + k4v
            )
        )

    a = (
        -k * x
        - damping * v
    ) / mass

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

        data = json.loads(
            response
            .choices[0]
            .message
            .content
        )

    except Exception:
        data = {}

    patterns = {
        "mass": [
            r"(\d+(?:\.\d+)?)\s*(?:kg|킬로그램)"
        ],
        "k": [
            r"(\d+(?:\.\d+)?)\s*(?:N/m|n/m)"
        ],
        "displacement": [
            r"(-?\d+(?:\.\d+)?)\s*(?:m(?!/s)|미터)"
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

    lower = user_text.lower()

    if (
        "compress" in lower
        or "compressed" in lower
        or "압축" in user_text
    ):
        if data.get("displacement") is not None:
            data["displacement"] = -abs(
                data["displacement"]
            )

    elif (
        "pull" in lower
        or "stretch" in lower
        or "당겨" in user_text
        or "늘려" in user_text
    ):
        if data.get("displacement") is not None:
            data["displacement"] = abs(
                data["displacement"]
            )

    return data


def create_box(
    cx,
    cy,
    cz,
    sx,
    sy,
    sz
):

    x0 = cx - sx / 2
    x1 = cx + sx / 2

    y0 = cy - sy / 2
    y1 = cy + sy / 2

    z0 = cz - sz / 2
    z1 = cz + sz / 2

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
        opacity=1
    )


def create_spring_coil(
    start_z,
    end_z,
    radius=0.2,
    turns=12
):

    points = 120

    theta = np.linspace(
        0,
        2 * np.pi * turns,
        points
    )

    z = np.linspace(
        start_z,
        end_z,
        points
    )

    return go.Scatter3d(
        x=radius * np.cos(theta),
        y=radius * np.sin(theta),
        z=z,
        mode="lines",
        line=dict(
            width=7
        ),
        uid="spring"
    )


def create_mass(
    z
):

    return go.Scatter3d(
        x=[0],
        y=[0],
        z=[z],
        mode="markers",
        marker=dict(
            size=25,
            symbol="circle"
        ),
        uid="mass"
    )


def create_reference(
    z
):

    return go.Scatter3d(
        x=[0, 0],
        y=[0, 0],
        z=[1.45, z],
        mode="lines",
        line=dict(
            width=2,
            dash="dot"
        ),
        opacity=0.35,
        uid="reference"
    )


def dynamic_traces(
    displacement
):

    spring_start = 1.45
    natural_length = 1.0
    mass_height = 0.45

    visual_displacement = np.clip(
        displacement * 0.55,
        -0.75,
        1.25
    )

    spring_length = (
        natural_length
        + visual_displacement
    )

    mass_center = (
        spring_start
        - spring_length
        - mass_height / 2
    )

    spring_end = (
        mass_center
        + mass_height / 2
    )

    return [
        create_spring_coil(
            spring_start,
            spring_end
        ),
        create_mass(
            mass_center
        ),
        create_reference(
            mass_center
        )
    ]


def create_figure(
    displacement
):

    fig = go.Figure()

    fig.add_trace(
        create_box(
            0,
            0,
            1.98,
            2.4,
            1.4,
            0.35
        )
    )

    fig.add_trace(
        create_box(
            0,
            0,
            1.53,
            0.5,
            0.5,
            0.16
        )
    )

    for trace in dynamic_traces(
        displacement
    ):
        fig.add_trace(trace)

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
                    y=3,
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

        uirevision="spring"
    )

    return fig


def reset_spring_state():

    keys = [
        "spring_mass",
        "spring_k",
        "spring_displacement",
        "spring_gravity",
        "spring_damping",
        "spring_ai_input",
        "spring_initialized"
    ]

    for key in keys:
        st.session_state.pop(
            key,
            None
        )


def spring_experiment():

    if (
        "spring_initialized"
        not in st.session_state
    ):

        for key, value in DEFAULTS.items():
            st.session_state[key] = value

        st.session_state.spring_initialized = True

    st.subheader(
        "Spring Experiment"
    )

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
            min_value=0.01,
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

        st.markdown(
            "### 3D Spring"
        )

        frame_count = 240

        frame_indices = np.linspace(
            0,
            len(time) - 1,
            frame_count,
            dtype=int
        )

        initial = create_figure(
            x[frame_indices[0]]
        )

        frames = []

        for number, index in enumerate(
            frame_indices
        ):

            traces = dynamic_traces(
                x[index]
            )

            frames.append(
                go.Frame(
                    data=traces,
                    traces=[2, 3, 4],
                    name=str(number)
                )
            )

        initial.frames = frames

        initial.update_layout(

            updatemenus=[

                {
                    "type": "buttons",

                    "showactive": False,

                    "x": 0.05,
                    "y": 0.05,

                    "buttons": [

                        {
                            "label": "▶ Play",

                            "method": "animate",

                            "args": [

                                None,

                                {
                                    "mode": "immediate",

                                    "fromcurrent": True,

                                    "transition": {
                                        "duration": 30,
                                        "easing": "linear"
                                    },

                                    "frame": {
                                        "duration": 42,
                                        "redraw": False
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        )

        st.plotly_chart(
            initial,
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

    st.markdown(
        "<br><br>",
        unsafe_allow_html=True
    )

    back_col, _, _ = st.columns(
        [1, 5, 1]
    )

    with back_col:

        if st.button(
            "Back to Experiments",
            key="spring_back_button"
        ):

            reset_spring_state()

            st.session_state.page = "select"
            st.session_state.experiment = None

            st.query_params.clear()

            st.rerun()
