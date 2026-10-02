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

    equilibrium_displacement = (
        mass * gravity / k
    )

    def acceleration(
        position,
        velocity
    ):

        return (
            gravity
            - (k * position / mass)
            - (damping * velocity / mass)
        )

    for i in range(n - 1):

        x0 = x[i]
        v0 = v[i]

        k1_x = v0

        k1_v = acceleration(
            x0,
            v0
        )

        k2_x = (
            v0
            + 0.5 * dt * k1_v
        )

        k2_v = acceleration(
            x0 + 0.5 * dt * k1_x,
            v0 + 0.5 * dt * k1_v
        )

        k3_x = (
            v0
            + 0.5 * dt * k2_v
        )

        k3_v = acceleration(
            x0 + 0.5 * dt * k2_x,
            v0 + 0.5 * dt * k2_v
        )

        k4_x = (
            v0
            + dt * k3_v
        )

        k4_v = acceleration(
            x0 + dt * k3_x,
            v0 + dt * k3_v
        )

        x[i + 1] = (
            x0
            + (dt / 6.0)
            * (
                k1_x
                + 2 * k2_x
                + 2 * k3_x
                + k4_x
            )
        )

        v[i + 1] = (
            v0
            + (dt / 6.0)
            * (
                k1_v
                + 2 * k2_v
                + 2 * k3_v
                + k4_v
            )
        )

    for i in range(n):

        a[i] = acceleration(
            x[i],
            v[i]
        )

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

    gravitational_energy = (
        -mass
        * gravity
        * x
    )

    total_mechanical_energy = (
        kinetic_energy
        + elastic_energy
        + gravitational_energy
    )

    equilibrium_energy = (
        kinetic_energy
        + 0.5
        * k
        * (
            x
            - equilibrium_displacement
        ) ** 2
    )

    return {
        "time": time,
        "x": x,
        "v": v,
        "a": a,
        "kinetic_energy": kinetic_energy,
        "elastic_energy": elastic_energy,
        "gravitational_energy": gravitational_energy,
        "total_mechanical_energy": total_mechanical_energy,
        "equilibrium_energy": equilibrium_energy,
        "equilibrium_displacement": equilibrium_displacement
    }


def parse_ai_spring(user_text):

    system_prompt = """
You are a physics parameter parser.

Extract only numerical values explicitly stated by the user.

Return JSON only:

{
    "mass": null,
    "k": null,
    "displacement": null,
    "gravity": null,
    "damping": null
}

Units:

mass = kg
k = N/m
displacement = m
gravity = m/s^2
damping = N*s/m

Do not guess missing values.

Displacement is measured from the spring's natural length.

If the user says:
compress or 압축 -> negative displacement
pull, stretch, 당겨, 늘려 -> positive displacement
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

        content = re.sub(
            r"```json|```",
            "",
            content
        ).strip()

        data = json.loads(content)

    except Exception:

        data = {}

    patterns = {

        "mass": [
            r"([-+]?\d+(?:\.\d+)?)\s*(?:kg|킬로그램)"
        ],

        "k": [
            r"([-+]?\d+(?:\.\d+)?)\s*(?:N/m|n/m)"
        ],

        "displacement": [
            r"([-+]?\d+(?:\.\d+)?)\s*(?:m|미터)(?!\s*/)"
        ],

        "gravity": [
            r"([-+]?\d+(?:\.\d+)?)\s*(?:m/s\^?2|m/s²)"
        ],

        "damping": [
            r"(?:damping|감쇠)\s*(?:=|은|는|계수)?\s*"
            r"([-+]?\d+(?:\.\d+)?)"
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

                    value = float(
                        match.group(1)
                    )

                    if key == "displacement":

                        if re.search(
                            r"(압축|compress)",
                            user_text,
                            re.IGNORECASE
                        ):
                            value = -abs(value)

                        elif re.search(
                            r"(당겨|늘려|stretch|pull)",
                            user_text,
                            re.IGNORECASE
                        ):
                            value = abs(value)

                    data[key] = value

                except ValueError:
                    pass

                break

    return data


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

        nxt = (n + 1) % segments

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


def create_spring_coil(
    start_z,
    end_z,
    radius=0.20,
    turns=12
):

    n_points = max(
        int(turns * 24),
        48
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

    x = (
        radius
        * np.cos(theta)
    )

    y = (
        radius
        * np.sin(theta)
    )

    return go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode="lines",
        line=dict(
            width=7
        )
    )


def create_spring_figure(
    displacement,
    equilibrium_displacement,
    natural_length=1.2
):

    ceiling_z = 1.8
    spring_start = 1.45

    mass_height = 0.45
    mass_radius = 0.32

    current_length = (
        natural_length
        + displacement
    )

    current_length = max(
        current_length,
        0.25
    )

    mass_center = (
        spring_start
        - current_length
        - mass_height / 2
    )

    spring_end = (
        mass_center
        + mass_height / 2
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
            spring_end,
            radius=0.20,
            turns=12
        )
    )

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

        plot_bgcolor="#0E1117",

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

    if (
        "spring_result" in st.session_state
        and not isinstance(
            st.session_state.spring_result,
            dict
        )
    ):

        st.session_state.spring_result = None

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

    st.subheader(
        "Spring Experiment"
    )

    st.markdown(
        "### AI Assistant"
    )

    ai_text = st.text_area(
        "Describe your experiment",
        placeholder=(
            "Example: A 1 kg mass is attached to a spring "
            "with a spring constant of 50 N/m and pulled "
            "0.3 m from its natural length before being released."
        ),
        height=100,
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

            st.rerun()

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
            "Initial Displacement from Natural Length (m)",
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
            "Damping c (N·s/m)",
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

    if isinstance(result, dict):

        time = result["time"]
        x = result["x"]
        velocity = result["v"]
        kinetic_energy = result["kinetic_energy"]
        elastic_energy = result["elastic_energy"]
        gravitational_energy = result[
            "gravitational_energy"
        ]
        total_mechanical_energy = result[
            "total_mechanical_energy"
        ]
        equilibrium_energy = result[
            "equilibrium_energy"
        ]
        equilibrium_displacement = result[
            "equilibrium_displacement"
        ]

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Equilibrium Displacement",
                f"{equilibrium_displacement:.3f} m"
            )

        with col2:

            st.metric(
                "Maximum Displacement",
                f"{np.max(np.abs(x)):.3f} m"
            )

        with col3:

            st.metric(
                "Maximum Velocity",
                f"{np.max(np.abs(velocity)):.3f} m/s"
            )

        with col4:

            st.metric(
                "Maximum Energy",
                f"{np.max(equilibrium_energy):.3f} J"
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
            x[frame_indices[0]],
            equilibrium_displacement
        )

        frames = []

        for i in frame_indices:

            frame_fig = create_spring_figure(
                x[i],
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
                y=x,
                mode="lines",
                name="Displacement"
            )
        )

        displacement_fig.add_hline(
            y=equilibrium_displacement,
            line_dash="dash",
            annotation_text="Equilibrium"
        )

        displacement_fig.update_layout(
            xaxis_title="Time (s)",
            yaxis_title=(
                "Displacement from Natural Length (m)"
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
                name="Elastic Energy"
            )
        )

        energy_fig.add_trace(
            go.Scatter(
                x=time,
                y=gravitational_energy,
                mode="lines",
                name="Gravitational Energy"
            )
        )

        energy_fig.add_trace(
            go.Scatter(
                x=time,
                y=total_mechanical_energy,
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

    st.divider()

    if st.button(
        "Back to Experiments",
        key="spring_back_button"
    ):

        st.session_state.page = "select"

        st.session_state.experiment = None

        st.session_state.spring_result = None

        st.query_params.clear()

        st.rerun()
