import json
import re
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from app_modules import client


def simulate_spring(
    mass,
    spring_constant,
    initial_displacement,
    gravity=9.81,
    damping=0.02,
    duration=10.0,
    dt=0.02
):
    time = np.arange(0, duration + dt, dt)

    x = np.zeros(len(time))
    v = np.zeros(len(time))
    a = np.zeros(len(time))

    x[0] = initial_displacement
    v[0] = 0.0

    for i in range(len(time) - 1):
        a[i] = (
            -spring_constant * x[i] / mass
            - damping * v[i]
        )

        v[i + 1] = v[i] + a[i] * dt
        x[i + 1] = x[i] + v[i + 1] * dt

    a[-1] = (
        -spring_constant * x[-1] / mass
        - damping * v[-1]
    )

    kinetic_energy = 0.5 * mass * v**2
    elastic_energy = 0.5 * spring_constant * x**2
    total_energy = kinetic_energy + elastic_energy

    return {
        "time": time,
        "x": x,
        "v": v,
        "a": a,
        "kinetic_energy": kinetic_energy,
        "elastic_energy": elastic_energy,
        "total_energy": total_energy
    }


def parse_ai_spring(user_text):
    result = {
        "mass": None,
        "spring_constant": None,
        "initial_displacement": None,
        "gravity": None,
        "damping": None
    }

    if client is not None:
        try:
            system_prompt = """
You are a physics parameter parser.

Convert the user's natural language into JSON.

Return ONLY valid JSON:

{
  "mass": number or null,
  "spring_constant": number or null,
  "initial_displacement": number or null,
  "gravity": number or null,
  "damping": number or null
}

Rules:
- Only use values explicitly stated by the user.
- Never guess missing values.
- Mass unit: kg.
- Spring constant unit: N/m.
- Initial displacement unit: m.
- Gravity unit: m/s^2.
- Damping is a numerical coefficient.
- "compress" and "압축" mean negative displacement.
- "pull", "stretch", "당겨", and "늘려" mean positive displacement.
"""

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_text
                    }
                ]
            )

            content = response.choices[0].message.content.strip()

            content = re.sub(
                r"```(?:json)?|```",
                "",
                content
            ).strip()

            ai_result = json.loads(content)

            for key in result:
                value = ai_result.get(key)

                if value is not None:
                    result[key] = float(value)

        except Exception:
            pass

    mass_match = re.search(
        r"(?:질량|mass)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)",
        user_text,
        re.IGNORECASE
    )

    if mass_match:
        result["mass"] = float(
            mass_match.group(1)
        )

    k_match = re.search(
        r"(?:스프링\s*상수|spring\s*constant|k)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)",
        user_text,
        re.IGNORECASE
    )

    if k_match:
        result["spring_constant"] = float(
            k_match.group(1)
        )

    displacement_match = re.search(
        r"(?:처음|초기|initial)?\s*(?:변위|displacement)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)\s*(?:m|미터)?",
        user_text,
        re.IGNORECASE
    )

    if displacement_match:
        result["initial_displacement"] = float(
            displacement_match.group(1)
        )

    if result["initial_displacement"] is None:
        stretch_match = re.search(
            r"(?:당겨|늘려|늘어|pull|stretch)\s*(?:서)?\s*(-?\d+(?:\.\d+)?)\s*(?:m|미터)",
            user_text,
            re.IGNORECASE
        )

        if stretch_match:
            result["initial_displacement"] = abs(
                float(stretch_match.group(1))
            )

        compress_match = re.search(
            r"(?:압축|compress)\s*(?:해서|하여)?\s*(-?\d+(?:\.\d+)?)\s*(?:m|미터)",
            user_text,
            re.IGNORECASE
        )

        if compress_match:
            result["initial_displacement"] = -abs(
                float(compress_match.group(1))
            )

    gravity_match = re.search(
        r"(?:중력|gravity|g)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)",
        user_text,
        re.IGNORECASE
    )

    if gravity_match:
        result["gravity"] = float(
            gravity_match.group(1)
        )

    damping_match = re.search(
        r"(?:감쇠|damping)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)",
        user_text,
        re.IGNORECASE
    )

    if damping_match:
        result["damping"] = float(
            damping_match.group(1)
        )

    return result


def create_box(
    x0,
    x1,
    y0,
    y1,
    z0,
    z1
):
    vertices = [
        [x0, y0, z0],
        [x1, y0, z0],
        [x1, y1, z0],
        [x0, y1, z0],
        [x0, y0, z1],
        [x1, y0, z1],
        [x1, y1, z1],
        [x0, y1, z1]
    ]

    faces = [
        [0, 1, 2],
        [0, 2, 3],
        [4, 6, 5],
        [4, 7, 6],
        [0, 4, 5],
        [0, 5, 1],
        [1, 5, 6],
        [1, 6, 2],
        [2, 6, 7],
        [2, 7, 3],
        [4, 0, 3],
        [4, 3, 7]
    ]

    return go.Mesh3d(
        x=[v[0] for v in vertices],
        y=[v[1] for v in vertices],
        z=[v[2] for v in vertices],
        i=[f[0] for f in faces],
        j=[f[1] for f in faces],
        k=[f[2] for f in faces],
        flatshading=True,
        opacity=1.0,
        showscale=False
    )


def create_cylinder_z(
    z0,
    z1,
    radius,
    center_x=0,
    center_y=0,
    segments=32
):
    theta = np.linspace(
        0,
        2 * np.pi,
        segments,
        endpoint=False
    )

    x_ring = center_x + radius * np.cos(theta)
    y_ring = center_y + radius * np.sin(theta)

    x = np.concatenate([
        x_ring,
        x_ring
    ])

    y = np.concatenate([
        y_ring,
        y_ring
    ])

    z = np.concatenate([
        np.full(segments, z0),
        np.full(segments, z1)
    ])

    faces_i = []
    faces_j = []
    faces_k = []

    for n in range(segments):
        nxt = (n + 1) % segments

        faces_i.extend([
            n,
            nxt
        ])

        faces_j.extend([
            nxt,
            segments + nxt
        ])

        faces_k.extend([
            segments + n,
            segments + n
        ])

    bottom_center = len(x)

    x = np.append(
        x,
        center_x
    )

    y = np.append(
        y,
        center_y
    )

    z = np.append(
        z,
        z0
    )

    for n in range(segments):
        nxt = (n + 1) % segments

        faces_i.append(
            bottom_center
        )

        faces_j.append(
            nxt
        )

        faces_k.append(
            n
        )

    top_center = len(x)

    x = np.append(
        x,
        center_x
    )

    y = np.append(
        y,
        center_y
    )

    z = np.append(
        z,
        z1
    )

    for n in range(segments):
        nxt = (n + 1) % segments

        faces_i.append(
            top_center
        )

        faces_j.append(
            segments + n
        )

        faces_k.append(
            segments + nxt
        )

    return go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=faces_i,
        j=faces_j,
        k=faces_k,
        flatshading=True,
        opacity=1.0,
        showscale=False
    )


def create_spring_coil(
    start_z,
    end_z,
    radius=0.20,
    turns=14,
    tube_radius=0.035
):
    points_per_turn = 20
    total_points = turns * points_per_turn

    t = np.linspace(
        0,
        turns * 2 * np.pi,
        total_points
    )

    z = np.linspace(
        start_z,
        end_z,
        total_points
    )

    x = radius * np.cos(t)
    y = radius * np.sin(t)

    points = np.column_stack([
        x,
        y,
        z
    ])

    rings = 8
    vertices = []

    for p in range(total_points):
        if p == 0:
            tangent = (
                points[1]
                - points[0]
            )
        elif p == total_points - 1:
            tangent = (
                points[-1]
                - points[-2]
            )
        else:
            tangent = (
                points[p + 1]
                - points[p - 1]
            )

        tangent /= np.linalg.norm(
            tangent
        )

        reference = np.array([
            1.0,
            0.0,
            0.0
        ])

        if abs(
            np.dot(
                tangent,
                reference
            )
        ) > 0.9:
            reference = np.array([
                0.0,
                1.0,
                0.0
            ])

        normal = np.cross(
            tangent,
            reference
        )

        normal /= np.linalg.norm(
            normal
        )

        binormal = np.cross(
            tangent,
            normal
        )

        binormal /= np.linalg.norm(
            binormal
        )

        for r in range(rings):
            angle = (
                2
                * np.pi
                * r
                / rings
            )

            offset = (
                tube_radius
                * np.cos(angle)
                * normal
                + tube_radius
                * np.sin(angle)
                * binormal
            )

            vertices.append(
                points[p] + offset
            )

    vertices = np.array(
        vertices
    )

    faces_i = []
    faces_j = []
    faces_k = []

    for p in range(
        total_points - 1
    ):
        for r in range(rings):
            current = (
                p * rings + r
            )

            next_ring = (
                p * rings
                + (r + 1) % rings
            )

            next_point = (
                (p + 1) * rings
                + r
            )

            next_point_ring = (
                (p + 1) * rings
                + (r + 1) % rings
            )

            faces_i.extend([
                current,
                next_ring
            ])

            faces_j.extend([
                next_ring,
                next_point_ring
            ])

            faces_k.extend([
                next_point,
                next_point
            ])

    return go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=faces_i,
        j=faces_j,
        k=faces_k,
        flatshading=False,
        opacity=1.0,
        showscale=False
    )


def create_spring_figure(
    displacement,
    spring_length=3.0
):
    ceiling_z = 1.8
    spring_start = ceiling_z - 0.35
    mass_length = 0.55

    mass_center = (
        ceiling_z
        - spring_length
        - displacement
    )

    mass_top = (
        mass_center
        + mass_length / 2
    )

    mass_bottom = (
        mass_center
        - mass_length / 2
    )

    spring_end = (
        mass_top
        + 0.08
    )

    if spring_end >= spring_start - 0.2:
        spring_end = (
            spring_start
            - 0.2
        )

    fig = go.Figure()

    fig.add_trace(
        create_box(
            -0.65,
            0.65,
            -0.65,
            0.65,
            1.8,
            2.0
        )
    )

    fig.add_trace(
        create_cylinder_z(
            1.55,
            1.8,
            0.12
        )
    )

    fig.add_trace(
        create_spring_coil(
            spring_start,
            spring_end,
            radius=0.20,
            turns=14,
            tube_radius=0.035
        )
    )

    fig.add_trace(
        create_cylinder_z(
            spring_end,
            mass_top,
            0.045
        )
    )

    fig.add_trace(
        create_cylinder_z(
            mass_bottom,
            mass_top,
            0.35
        )
    )

    fig.add_trace(
        create_cylinder_z(
            mass_top - 0.05,
            mass_top + 0.02,
            0.17
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[0, 0],
            y=[0, 0],
            z=[-1.8, 1.55],
            mode="lines",
            line=dict(
                width=3,
                dash="dash"
            ),
            showlegend=False
        )
    )

    fig.update_layout(
        height=600,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),
        scene=dict(
            xaxis=dict(
                range=[
                    -1.0,
                    1.0
                ],
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                range=[
                    -1.0,
                    1.0
                ],
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            zaxis=dict(
                range=[
                    -2.0,
                    2.2
                ],
                showticklabels=False,
                showgrid=False,
                zeroline=False
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


def spring_experiment():
    st.subheader(
        "Spring Experiment"
    )

    defaults = {
        "spring_mass": 1.00,
        "spring_k": 50.00,
        "spring_displacement": 0.30,
        "spring_gravity": 9.81,
        "spring_damping": 0.02
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.markdown(
        "### AI Natural Language"
    )

    ai_text = st.text_input(
        "Describe your spring experiment",
        placeholder=(
            "예: 질량 2kg, "
            "스프링 상수 50N/m, "
            "0.3m 당겨서 시작해"
        )
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

            if parsed["spring_constant"] is not None:
                st.session_state.spring_k = (
                    parsed["spring_constant"]
                )

            if parsed["initial_displacement"] is not None:
                st.session_state.spring_displacement = (
                    parsed["initial_displacement"]
                )

            if parsed["gravity"] is not None:
                st.session_state.spring_gravity = (
                    parsed["gravity"]
                )

            if parsed["damping"] is not None:
                st.session_state.spring_damping = (
                    parsed["damping"]
                )

            st.rerun()

    st.markdown(
        "### Manual Parameters"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        mass = st.number_input(
            "Mass (kg)",
            min_value=0.01,
            max_value=100.0,
            step=0.1,
            key="spring_mass"
        )

    with col2:
        spring_constant = st.number_input(
            "Spring Constant k (N/m)",
            min_value=0.1,
            max_value=1000.0,
            step=1.0,
            key="spring_k"
        )

    with col3:
        initial_displacement = st.number_input(
            "Initial Displacement (m)",
            min_value=-5.0,
            max_value=5.0,
            step=0.05,
            key="spring_displacement"
        )

    col4, col5 = st.columns(2)

    with col4:
        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.0,
            max_value=30.0,
            step=0.01,
            key="spring_gravity"
        )

    with col5:
        damping = st.number_input(
            "Damping",
            min_value=0.0,
            max_value=5.0,
            step=0.01,
            key="spring_damping"
        )

    result = simulate_spring(
        mass=mass,
        spring_constant=spring_constant,
        initial_displacement=initial_displacement,
        gravity=gravity,
        damping=damping
    )

    time = result["time"]
    displacement = result["x"]

    st.markdown(
        "### Simulation"
    )

    current_col1, current_col2, current_col3 = st.columns(3)

    with current_col1:
        st.metric(
            "Mass",
            f"{mass:.2f} kg"
        )

    with current_col2:
        st.metric(
            "Spring Constant",
            f"{spring_constant:.2f} N/m"
        )

    with current_col3:
        st.metric(
            "Initial Displacement",
            f"{initial_displacement:.2f} m"
        )

    frames = []

    for i in range(
        0,
        len(time),
        5
    ):
        frame_fig = create_spring_figure(
            displacement[i]
        )

        frames.append(
            go.Frame(
                data=frame_fig.data,
                name=f"{time[i]:.2f}"
            )
        )

    fig = create_spring_figure(
        displacement[0]
    )

    fig.frames = frames

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.05,
                y=1.05,
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(
                                    duration=20,
                                    redraw=True
                                ),
                                transition=dict(
                                    duration=0
                                ),
                                fromcurrent=True
                            )
                        ]
                    )
                ]
            )
        ]
    )

    with st.container(
        border=True
    ):
        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown(
        "### Analysis"
    )

    displacement_fig = go.Figure()

    displacement_fig.add_trace(
        go.Scatter(
            x=time,
            y=displacement,
            mode="lines",
            name="Displacement"
        )
    )

    displacement_fig.update_layout(
        title="Displacement vs Time",
        xaxis_title="Time (s)",
        yaxis_title="Displacement (m)",
        height=400
    )

    st.plotly_chart(
        displacement_fig,
        use_container_width=True
    )

    energy_fig = go.Figure()

    energy_fig.add_trace(
        go.Scatter(
            x=time,
            y=result["kinetic_energy"],
            mode="lines",
            name="Kinetic Energy"
        )
    )

    energy_fig.add_trace(
        go.Scatter(
            x=time,
            y=result["elastic_energy"],
            mode="lines",
            name="Elastic Potential Energy"
        )
    )

    energy_fig.add_trace(
        go.Scatter(
            x=time,
            y=result["total_energy"],
            mode="lines",
            name="Total Energy"
        )
    )

    energy_fig.update_layout(
        title="Energy",
        xaxis_title="Time (s)",
        yaxis_title="Energy (J)",
        height=400
    )

    st.plotly_chart(
        energy_fig,
        use_container_width=True
    )
