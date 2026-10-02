import math
import numpy as np
import streamlit as st
import plotly.graph_objects as go


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

        return (
            px,
            py,
            v,
            mass * (
                v ** 2 / length
                + gravity * math.cos(theta)
            ),
            0.5 * mass * v ** 2,
            mass * gravity * length
            * (1 - math.cos(theta))
        )

    steps = int(duration / dt)

    for i in range(steps + 1):

        t = i * dt
        px, py, v, tension_value, ke, pe = state()

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
            omega + 0.5 * dt * k1_omega
        )
        k2_omega = acceleration(
            theta + 0.5 * dt * k1_theta,
            omega + 0.5 * dt * k1_omega
        )

        k3_theta = (
            omega + 0.5 * dt * k2_omega
        )
        k3_omega = acceleration(
            theta + 0.5 * dt * k2_theta,
            omega + 0.5 * dt * k2_omega
        )

        k4_theta = (
            omega + dt * k3_omega
        )
        k4_omega = acceleration(
            theta + dt * k3_theta,
            omega + dt * k3_omega
        )

        theta += dt / 6 * (
            k1_theta
            + 2 * k2_theta
            + 2 * k3_theta
            + k4_theta
        )

        omega += dt / 6 * (
            k1_omega
            + 2 * k2_omega
            + 2 * k3_omega
            + k4_omega
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


def create_pendulum_figure(result):

    frame_step = 5
    frames = []

    length = math.sqrt(
        result["x"][0] ** 2
        + result["y"][0] ** 2
    )

    ground = max(3.0, length * 1.5)

    for i in range(
        0,
        len(result["time"]),
        frame_step
    ):

        x = result["x"][i]
        y = result["y"][i]

        angle = result["angle"][i]
        omega = result["angular_velocity"][i]

        vx = (
            omega
            * length
            * math.cos(math.radians(angle))
        )

        vy = (
            -omega
            * length
            * math.sin(math.radians(angle))
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
                            result["time"][i],
                            angle,
                            result["velocity"][i]
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
                        z=[0, 0],
                        customdata=[
                            omega,
                            omega
                        ]
                    )
                ],
                traces=[1, 3, 4]
            )
        )

    first_x = result["x"][0]
    first_y = result["y"][0]

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
                showlegend=False,
                hoverinfo="skip"
            ),

            go.Scatter3d(
                x=[0, first_x],
                y=[0, first_y],
                z=[0, 0],
                mode="lines",
                line=dict(
                    width=8,
                    color="#D1D5DB"
                ),
                name="Rod",
                hovertemplate=(
                    "Length: %{customdata:.2f} m"
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
                    size=10,
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
                    size=16,
                    color="#F6D77A",
                    line=dict(
                        width=2,
                        color="white"
                    )
                ),
                name="Bob",
                hovertemplate=(
                    "Time: %{customdata[0]:.2f} s<br>"
                    "Angle: %{customdata[1]:.2f}°<br>"
                    "Velocity: %{customdata[2]:.2f} m/s"
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
        height=620,

        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),

        paper_bgcolor="#0d1117",

        font=dict(
            color="white"
        ),

        scene=dict(
            uirevision="pendulum-camera",

            xaxis=dict(
                title="X",
                backgroundcolor="#0d1117",
                gridcolor="#30363d"
            ),

            yaxis=dict(
                title="Y",
                backgroundcolor="#0d1117",
                gridcolor="#30363d"
            ),

            zaxis=dict(
                title="Z",
                backgroundcolor="#0d1117",
                gridcolor="#30363d"
            ),

            aspectmode="cube"
        ),

        updatemenus=[
            dict(
                type="buttons",
                showactive=False,

                x=0.02,
                y=1.02,

                xanchor="left",
                yanchor="bottom",

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

                                fromcurrent=True,

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

    st.title("Pendulum")

    st.caption(
        "Explore how length, gravity, angle, mass, "
        "and damping affect pendulum motion."
    )

    left, right = st.columns(2)

    with left:

        length = st.slider(
            "Length (m)",
            0.1,
            10.0,
            2.0,
            0.1
        )

        mass = st.slider(
            "Mass (kg)",
            0.1,
            20.0,
            1.0,
            0.1
        )

        gravity = st.number_input(
            "Gravity (m/s²)",
            0.01,
            1000.0,
            9.81,
            0.1
        )

    with right:

        initial_angle = st.slider(
            "Initial Angle (°)",
            -89.0,
            89.0,
            45.0,
            1.0
        )

        damping = st.slider(
            "Damping",
            0.0,
            1.0,
            0.02,
            0.01
        )

    if st.button(
        "Run Pendulum Experiment",
        type="primary",
        use_container_width=True
    ):

        st.session_state["pendulum_result"] = (
            simulate_pendulum(
                length,
                mass,
                gravity,
                initial_angle,
                damping
            )
        )

    if "pendulum_result" not in st.session_state:

        st.info(
            "Set the parameters and run the experiment."
        )

        return

    result = st.session_state[
        "pendulum_result"
    ]

    st.subheader("3D Simulation")

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
        "← Back to Experiments"
    ):

        st.session_state.page = "select"
        st.session_state.experiment = None

        st.session_state.pop(
            "pendulum_result",
            None
        )

        st.query_params.clear()

        st.rerun()
