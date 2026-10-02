import math
import json
import re
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from app_modules import client


def simulate_pendulum(
    length,
    mass,
    gravity,
    initial_angle,
    damping,
    duration=10.0,
    dt=0.01
):
    theta = math.radians(initial_angle)
    omega = 0.0

    time = []
    angle = []
    angular_velocity = []
    x = []
    y = []
    velocity = []
    tension = []
    kinetic_energy = []
    potential_energy = []
    total_energy = []

    def acceleration(theta, omega):
        return (
            -(gravity / length) * math.sin(theta)
            - damping * omega
        )

    def state():
        px = length * math.sin(theta)
        py = -length * math.cos(theta)
        v = abs(length * omega)

        tension_value = mass * (
            v ** 2 / length
            + gravity * math.cos(theta)
        )

        ke = 0.5 * mass * v ** 2

        pe = (
            mass
            * gravity
            * length
            * (1 - math.cos(theta))
        )

        return px, py, v, tension_value, ke, pe

    steps = int(duration / dt)

    for i in range(steps + 1):

        t = i * dt

        (
            px,
            py,
            v,
            tension_value,
            ke,
            pe
        ) = state()

        time.append(t)
        angle.append(math.degrees(theta))
        angular_velocity.append(omega)
        x.append(px)
        y.append(py)
        velocity.append(v)
        tension.append(tension_value)
        kinetic_energy.append(ke)
        potential_energy.append(pe)
        total_energy.append(ke + pe)

        k1_theta = omega
        k1_omega = acceleration(theta, omega)

        k2_theta = (
            omega
            + 0.5 * dt * k1_omega
        )

        k2_omega = acceleration(
            theta + 0.5 * dt * k1_theta,
            omega + 0.5 * dt * k1_omega
        )

        k3_theta = (
            omega
            + 0.5 * dt * k2_omega
        )

        k3_omega = acceleration(
            theta + 0.5 * dt * k2_theta,
            omega + 0.5 * dt * k2_omega
        )

        k4_theta = (
            omega
            + dt * k3_omega
        )

        k4_omega = acceleration(
            theta + dt * k3_theta,
            omega + dt * k3_omega
        )

        theta += (
            dt / 6
            * (
                k1_theta
                + 2 * k2_theta
                + 2 * k3_theta
                + k4_theta
            )
        )

        omega += (
            dt / 6
            * (
                k1_omega
                + 2 * k2_omega
                + 2 * k3_omega
                + k4_omega
            )
        )

    return {
        "time": np.array(time),
        "angle": np.array(angle),
        "angular_velocity": np.array(
            angular_velocity
        ),
        "x": np.array(x),
        "y": np.array(y),
        "velocity": np.array(velocity),
        "tension": np.array(tension),
        "kinetic_energy": np.array(
            kinetic_energy
        ),
        "potential_energy": np.array(
            potential_energy
        ),
        "total_energy": np.array(
            total_energy
        )
    }


def parse_ai_pendulum(prompt):

    defaults = {
        "length": 2.0,
        "mass": 1.0,
        "gravity": 9.81,
        "initial_angle": -45.0,
        "damping": 0.02
    }

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": """
You are a pendulum parameter parser.

Convert the user's natural language into JSON.

Return ONLY:
{
  "length": number or null,
  "mass": number or null,
  "gravity": number or null,
  "initial_angle": number or null,
  "damping": number or null
}

Rules:
- Extract values explicitly stated by the user.
- Never invent missing values.
- Never change a stated number.
- "왼쪽" or "left" means negative angle.
- "오른쪽" or "right" means positive angle.
- Length is meters.
- Mass is kilograms.
- Gravity is m/s².
- Angle is degrees.
"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={
                "type": "json_object"
            },
            temperature=0
        )

        ai_values = json.loads(
            response.choices[0].message.content
        )

    except Exception:
        ai_values = {}

    values = defaults.copy()

    for key in values:

        value = ai_values.get(key)

        if isinstance(value, (int, float)):
            values[key] = float(value)

    def extract(pattern):

        match = re.search(
            pattern,
            prompt,
            re.IGNORECASE
        )

        if match:
            return float(match.group(1))

        return None

    explicit_length = extract(
        r"(?:길이|length|줄|rope)"
        r".*?"
        r"(-?\d+(?:\.\d+)?)"
        r"\s*(?:m|미터)\b"
    )

    explicit_mass = extract(
        r"(?:질량|mass|무게|weight)"
        r".*?"
        r"(-?\d+(?:\.\d+)?)"
        r"\s*(?:kg|킬로그램)\b"
    )

    explicit_angle = extract(
        r"(?:각도|angle)"
        r".*?"
        r"(-?\d+(?:\.\d+)?)"
        r"\s*(?:도|°|degrees?)"
    )

    explicit_gravity = extract(
        r"(?:중력|gravity)"
        r".*?"
        r"(-?\d+(?:\.\d+)?)"
        r"\s*(?:m/s²|m/s2|m/s\^2)"
    )

    explicit_damping = extract(
        r"(?:감쇠|damping)"
        r".*?"
        r"(-?\d+(?:\.\d+)?)"
    )

    if explicit_length is not None:
        values["length"] = explicit_length

    if explicit_mass is not None:
        values["mass"] = explicit_mass

    if explicit_angle is not None:
        values["initial_angle"] = explicit_angle

    if explicit_gravity is not None:
        values["gravity"] = explicit_gravity

    if explicit_damping is not None:
        values["damping"] = explicit_damping

    if re.search(
        r"왼쪽|left",
        prompt,
        re.IGNORECASE
    ):
        values["initial_angle"] = -abs(
            values["initial_angle"]
        )

    elif re.search(
        r"오른쪽|right",
        prompt,
        re.IGNORECASE
    ):
        values["initial_angle"] = abs(
            values["initial_angle"]
        )

    values["length"] = min(
        max(values["length"], 0.1),
        10.0
    )

    values["mass"] = min(
        max(values["mass"], 0.1),
        20.0
    )

    values["gravity"] = min(
        max(values["gravity"], 0.01),
        1000.0
    )

    values["initial_angle"] = min(
        max(values["initial_angle"], -89.0),
        89.0
    )

    values["damping"] = min(
        max(values["damping"], 0.0),
        1.0
    )

    return values


def create_info_text(result, index):

    return (
        f"<b>Time:</b> "
        f"{result['time'][index]:.1f} s"
        "&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<b>Angle:</b> "
        f"{result['angle'][index]:.2f}°"
        "&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<b>Angular Velocity:</b> "
        f"{result['angular_velocity'][index]:.2f} rad/s"
        "<br>"
        f"<b>Velocity:</b> "
        f"{result['velocity'][index]:.2f} m/s"
        "&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<b>Tension:</b> "
        f"{result['tension'][index]:.2f} N"
        "&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<b>Total Energy:</b> "
        f"{result['total_energy'][index]:.2f} J"
    )


def create_pendulum_figure(result):

    length = math.sqrt(
        result["x"][0] ** 2
        + result["y"][0] ** 2
    )

    ground = max(
        3.0,
        length * 1.5
    )

    frames = []
    animation_step = 5

    for i in range(
        0,
        len(result["time"]),
        animation_step
    ):

        x = result["x"][i]
        y = result["y"][i]

        angle = result["angle"][i]
        omega = result["angular_velocity"][i]

        angle_rad = math.radians(angle)

        vx = (
            omega
            * length
            * math.cos(angle_rad)
        )

        vy = (
            -omega
            * length
            * math.sin(angle_rad)
        )

        display_index = int(
            round(
                result["time"][i] / 0.5
            )
            * 0.5
            / 0.01
        )

        display_index = min(
            display_index,
            len(result["time"]) - 1
        )

        info_text = create_info_text(
            result,
            display_index
        )

        frames.append(
            go.Frame(
                name=f"frame{i}",
                data=[
                    go.Scatter3d(
                        x=[0, x],
                        y=[0, y],
                        z=[0, 0]
                    ),
                    go.Scatter3d(
                        x=[x],
                        y=[y],
                        z=[0],
                        customdata=[[
                            result["time"][display_index],
                            result["angle"][display_index],
                            result["velocity"][display_index]
                        ]]
                    ),
                    go.Scatter3d(
                        x=[
                            x,
                            x + vx * 0.3
                        ],
                        y=[
                            y,
                            y + vy * 0.3
                        ],
                        z=[0, 0]
                    )
                ],
                traces=[1, 3, 4],
                layout=go.Layout(
                    annotations=[
                        dict(
                            x=0.5,
                            y=0.055,
                            xref="paper",
                            yref="paper",
                            text=info_text,
                            showarrow=False,
                            align="center",
                            font=dict(
                                size=17,
                                color="white"
                            )
                        )
                    ]
                )
            )
        )

    first_x = result["x"][0]
    first_y = result["y"][0]

    initial_info = create_info_text(
        result,
        0
    )

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=[-ground, ground],
                y=[-length, -length],
                z=[0, 0],
                mode="lines",
                line=dict(
                    width=2,
                    color="rgba(150,150,150,0.35)"
                ),
                hoverinfo="skip"
            ),
            go.Scatter3d(
                x=[0, first_x],
                y=[0, first_y],
                z=[0, 0],
                mode="lines",
                line=dict(
                    width=9,
                    color="#D1D5DB"
                ),
                name="Rod",
                hovertemplate=(
                    "Length: "
                    "%{customdata:.2f} m"
                    "<extra></extra>"
                ),
                customdata=[
                    length,
                    length
                ]
            ),
            go.Scatter3d(
                x=[0],
                y=[0],
                z=[0],
                mode="markers",
                marker=dict(
                    size=11,
                    color="white"
                ),
                name="Pivot",
                hoverinfo="skip"
            ),
            go.Scatter3d(
                x=[first_x],
                y=[first_y],
                z=[0],
                mode="markers",
                marker=dict(
                    size=17,
                    color="#F6D77A",
                    line=dict(
                        width=2,
                        color="white"
                    )
                ),
                name="Bob",
                hovertemplate=(
                    "Time: "
                    "%{customdata[0]:.2f} s<br>"
                    "Angle: "
                    "%{customdata[1]:.2f}°<br>"
                    "Velocity: "
                    "%{customdata[2]:.2f} m/s"
                    "<extra></extra>"
                ),
                customdata=[[
                    result["time"][0],
                    result["angle"][0],
                    result["velocity"][0]
                ]]
            ),
            go.Scatter3d(
                x=[first_x, first_x],
                y=[first_y, first_y],
                z=[0, 0],
                mode="lines+markers",
                line=dict(
                    width=6,
                    color="#60A5FA"
                ),
                marker=dict(size=4),
                name="Velocity",
                hovertemplate=(
                    "Angular Velocity: "
                    "%{customdata:.2f} rad/s"
                    "<extra></extra>"
                ),
                customdata=[
                    result["angular_velocity"][0],
                    result["angular_velocity"][0]
                ]
            )
        ],
        frames=frames
    )

    fig.update_layout(
        height=520,
        margin=dict(
            l=5,
            r=5,
            t=5,
            b=0
        ),
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="white"),
        scene=dict(
            domain=dict(
                x=[0.04, 0.96],
                y=[0.18, 1.0]
            ),
            xaxis=dict(
                title="X",
                backgroundcolor="#0d1117",
                gridcolor="#30363d",
                range=[
                    -ground,
                    ground
                ]
            ),
            yaxis=dict(
                title="Y",
                backgroundcolor="#0d1117",
                gridcolor="#30363d",
                range=[
                    -length * 1.2,
                    length * 0.35
                ]
            ),
            zaxis=dict(
                title="Z",
                backgroundcolor="#0d1117",
                gridcolor="#30363d",
                range=[
                    -0.7,
                    0.7
                ]
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=1.7,
                y=1.7,
                z=0.65
            ),
            camera=dict(
                eye=dict(
                    x=0.15,
                    y=-0.05,
                    z=3.0
                ),
                center=dict(
                    x=0,
                    y=0.25,
                    z=0
                ),
                up=dict(
                    x=0,
                    y=1,
                    z=0
                )
            )
        ),
        annotations=[
            dict(
                x=0.5,
                y=0.055,
                xref="paper",
                yref="paper",
                text=initial_info,
                showarrow=False,
                align="center",
                font=dict(
                    size=17,
                    color="white"
                )
            )
        ],
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.035,
                y=0.96,
                xanchor="left",
                yanchor="top",
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(
                                    duration=50,
                                    redraw=True
                                ),
                                transition=dict(
                                    duration=0
                                ),
                                mode="immediate"
                            )
                        ]
                    )
                ]
            )
        ]
    )

    return fig


def create_angle_graph(result):

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=result["time"],
            y=result["angle"],
            mode="lines",
            name="Angle",
            hovertemplate=(
                "Time: %{x:.2f} s<br>"
                "Angle: %{y:.2f}°"
                "<extra></extra>"
            )
        )
    )

    fig.update_layout(
        title="Angular Position",
        xaxis_title="Time (s)",
        yaxis_title="Angle (°)",
        height=350,
        hovermode="closest"
    )

    return fig


def create_energy_graph(result):

    fig = go.Figure()

    for key, name in [
        ("kinetic_energy", "Kinetic Energy"),
        ("potential_energy", "Potential Energy"),
        ("total_energy", "Total Energy")
    ]:

        fig.add_trace(
            go.Scatter(
                x=result["time"],
                y=result[key],
                mode="lines",
                name=name,
                hovertemplate=(
                    "Time: %{x:.2f} s<br>"
                    f"{name}: "
                    "%{y:.4f} J"
                    "<extra></extra>"
                )
            )
        )

    fig.update_layout(
        title="Energy",
        xaxis_title="Time (s)",
        yaxis_title="Energy (J)",
        height=350,
        hovermode="closest"
    )

    return fig


def pendulum_experiment():

    st.subheader(
        "Pendulum Experiment"
    )

    st.title("Pendulum")

    st.caption(
        "Explore how length, gravity, angle, "
        "mass, and damping affect pendulum motion."
    )

    ai_prompt = st.text_area(
        "AI Natural Language",
        placeholder=(
            "예: 처음 각도 45도에서 시작하고 "
            "길이는 3m, 질량은 2kg으로 해줘"
        ),
        height=80
    )

    if st.button(
        "Analyze with AI",
        use_container_width=True
    ):

        if ai_prompt.strip():

            try:

                params = parse_ai_pendulum(
                    ai_prompt
                )

                st.session_state[
                    "length_value"
                ] = params["length"]

                st.session_state[
                    "mass_value"
                ] = params["mass"]

                st.session_state[
                    "gravity_value"
                ] = params["gravity"]

                st.session_state[
                    "angle_value"
                ] = params["initial_angle"]

                st.session_state[
                    "damping_value"
                ] = params["damping"]

                st.session_state[
                    "pendulum_result"
                ] = simulate_pendulum(
                    params["length"],
                    params["mass"],
                    params["gravity"],
                    params["initial_angle"],
                    params["damping"]
                )

                st.session_state[
                    "ai_applied"
                ] = True

                st.rerun()

            except Exception as e:

                st.error(
                    f"AI error: {e}"
                )

    left, right = st.columns(2)

    with left:

        length = st.slider(
            "Length (m)",
            0.1,
            10.0,
            st.session_state.get(
                "length_value",
                2.0
            ),
            0.1
        )

        mass = st.slider(
            "Mass (kg)",
            0.1,
            20.0,
            st.session_state.get(
                "mass_value",
                1.0
            ),
            0.1
        )

        gravity = st.number_input(
            "Gravity (m/s²)",
            0.01,
            1000.0,
            st.session_state.get(
                "gravity_value",
                9.81
            ),
            0.1
        )

    with right:

        initial_angle = st.slider(
            "Initial Angle (°)",
            -89.0,
            89.0,
            st.session_state.get(
                "angle_value",
                45.0
            ),
            1.0
        )

        damping = st.slider(
            "Damping",
            0.0,
            1.0,
            st.session_state.get(
                "damping_value",
                0.02
            ),
            0.01
        )

    if st.session_state.pop(
        "ai_applied",
        False
    ):

        st.success(
            "AI parameters applied."
        )

    if st.button(
        "Run Pendulum Experiment",
        type="primary",
        use_container_width=True
    ):

        st.session_state[
            "pendulum_result"
        ] = simulate_pendulum(
            length,
            mass,
            gravity,
            initial_angle,
            damping
        )

    if "pendulum_result" not in st.session_state:

        st.info(
            "Set the parameters and run the experiment."
        )

    else:

        result = st.session_state[
            "pendulum_result"
        ]

        st.subheader("3D Simulation")

        with st.container(border=True):

            st.plotly_chart(
                create_pendulum_figure(result),
                use_container_width=True,
                config={
                    "displaylogo": False
                }
            )

        st.divider()

        st.subheader("Analysis")

        tab1, tab2 = st.tabs(
            ["Angle", "Energy"]
        )

        with tab1:

            st.plotly_chart(
                create_angle_graph(result),
                use_container_width=True
            )

        with tab2:

            st.plotly_chart(
                create_energy_graph(result),
                use_container_width=True
            )

    st.divider()

    if st.button(
        "← Back to Experiments",
        key="pendulum_back_bottom"
    ):

        st.session_state.page = "select"
        st.session_state.experiment = None

        st.session_state.pop(
            "pendulum_result",
            None
        )

        st.session_state.pop(
            "length_value",
            None
        )

        st.session_state.pop(
            "mass_value",
            None
        )

        st.session_state.pop(
            "gravity_value",
            None
        )

        st.session_state.pop(
            "angle_value",
            None
        )

        st.session_state.pop(
            "damping_value",
            None
        )

        st.query_params.clear()

        st.rerun()
