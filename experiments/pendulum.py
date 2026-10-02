import math
import json
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import plotly.io as pio


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

    steps = int(duration / dt)

    for i in range(steps + 1):

        t = i * dt

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


def create_pendulum_animation(result):

    length = math.sqrt(
        result["x"][0] ** 2
        + result["y"][0] ** 2
    )

    ground = max(
        3.0,
        length * 1.5
    )

    x = result["x"][0]
    y = result["y"][0]

    omega = result["angular_velocity"][0]

    angle = result["angle"][0]

    vx = (
        omega
        * length
        * math.cos(
            math.radians(angle)
        )
    )

    vy = (
        -omega
        * length
        * math.sin(
            math.radians(angle)
        )
    )

    fig = go.Figure()

    fig.add_trace(
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
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[0, x],
            y=[0, y],
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
            customdata=[length, length]
        )
    )

    fig.add_trace(
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
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[x],
            y=[y],
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
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[x, x + vx * 0.3],
            y=[y, y + vy * 0.3],
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
                omega,
                omega
            ]
        )
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
        )
    )

    return fig


def create_animation_html(result):

    fig = create_pendulum_animation(result)

    plot_html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs="cdn",
        div_id="pendulum_plot"
    )

    data = {
        "time": result["time"].tolist(),
        "x": result["x"].tolist(),
        "y": result["y"].tolist(),
        "angle": result["angle"].tolist(),
        "angular_velocity":
            result["angular_velocity"].tolist(),
        "velocity":
            result["velocity"].tolist(),
        "tension":
            result["tension"].tolist(),
        "total_energy":
            result["total_energy"].tolist()
    }

    data_json = json.dumps(data)

    html = f"""
    <style>

        body {{
            margin: 0;
            background: #0d1117;
            color: white;
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                sans-serif;
        }}

        .simulation {{
            width: 100%;
        }}

        .time {{
            font-size: 16px;
            color: #c9d1d9;
            margin: 4px 0 8px 4px;
        }}

        .metrics {{
            display: grid;
            grid-template-columns:
                repeat(5, 1fr);
            gap: 14px;
            margin-top: 8px;
        }}

        .metric-title {{
            font-size: 14px;
            color: #c9d1d9;
            margin-bottom: 6px;
        }}

        .metric-value {{
            font-size: 25px;
            color: #f0f6fc;
            white-space: nowrap;
        }}

        @media (max-width: 900px) {{
            .metrics {{
                grid-template-columns:
                    repeat(3, 1fr);
            }}
        }}

        @media (max-width: 600px) {{
            .metrics {{
                grid-template-columns:
                    repeat(2, 1fr);
            }}
        }}

    </style>

    <div class="simulation">

        <div
            class="time"
            id="simulation_time"
        >
            Simulation Time: 0.00 s
        </div>

        {plot_html}

        <div class="metrics">

            <div>
                <div class="metric-title">
                    Angle
                </div>
                <div
                    class="metric-value"
                    id="angle"
                >
                    0.00°
                </div>
            </div>

            <div>
                <div class="metric-title">
                    Angular Velocity
                </div>
                <div
                    class="metric-value"
                    id="angular_velocity"
                >
                    0.00 rad/s
                </div>
            </div>

            <div>
                <div class="metric-title">
                    Velocity
                </div>
                <div
                    class="metric-value"
                    id="velocity"
                >
                    0.00 m/s
                </div>
            </div>

            <div>
                <div class="metric-title">
                    Tension
                </div>
                <div
                    class="metric-value"
                    id="tension"
                >
                    0.00 N
                </div>
            </div>

            <div>
                <div class="metric-title">
                    Total Energy
                </div>
                <div
                    class="metric-value"
                    id="energy"
                >
                    0.00 J
                </div>
            </div>

        </div>

    </div>

    <script>

        const data = {data_json};

        const plot =
            document.getElementById(
                "pendulum_plot"
            );

        let startTime = null;
        let lastMetricTime = -0.5;

        function updateMetrics(index) {{

            document.getElementById(
                "simulation_time"
            ).textContent =
                "Simulation Time: "
                + data.time[index].toFixed(2)
                + " s";

            document.getElementById(
                "angle"
            ).textContent =
                data.angle[index].toFixed(2)
                + "°";

            document.getElementById(
                "angular_velocity"
            ).textContent =
                data.angular_velocity[index]
                .toFixed(2)
                + " rad/s";

            document.getElementById(
                "velocity"
            ).textContent =
                data.velocity[index]
                .toFixed(2)
                + " m/s";

            document.getElementById(
                "tension"
            ).textContent =
                data.tension[index]
                .toFixed(2)
                + " N";

            document.getElementById(
                "energy"
            ).textContent =
                data.total_energy[index]
                .toFixed(2)
                + " J";
        }}

        function animate(timestamp) {{

            if (startTime === null) {{
                startTime = timestamp;
            }}

            const elapsed =
                (timestamp - startTime)
                / 1000;

            const simulationTime =
                Math.min(elapsed, 10);

            const index = Math.min(
                Math.round(
                    simulationTime / 0.01
                ),
                data.time.length - 1
            );

            Plotly.restyle(
                plot,
                {{
                    x: [[0, data.x[index]]],
                    y: [[0, data.y[index]]]
                }},
                [1]
            );

            Plotly.restyle(
                plot,
                {{
                    x: [[data.x[index]]],
                    y: [[data.y[index]]],
                    customdata: [[[
                        data.time[index],
                        data.angle[index],
                        data.velocity[index]
                    ]]]
                }},
                [3]
            );

            const angle =
                data.angle[index];

            const omega =
                data.angular_velocity[index];

            const length =
                Math.sqrt(
                    data.x[0] * data.x[0]
                    + data.y[0] * data.y[0]
                );

            const vx =
                omega
                * length
                * Math.cos(
                    angle * Math.PI / 180
                );

            const vy =
                -omega
                * length
                * Math.sin(
                    angle * Math.PI / 180
                );

            Plotly.restyle(
                plot,
                {{
                    x: [[
                        data.x[index],
                        data.x[index]
                        + vx * 0.3
                    ]],

                    y: [[
                        data.y[index],
                        data.y[index]
                        + vy * 0.3
                    ]],

                    customdata: [[
                        omega,
                        omega
                    ]]
                }},
                [4]
            );

            if (
                simulationTime
                - lastMetricTime >= 0.5
                || simulationTime >= 10
            ) {{

                const metricIndex =
                    Math.min(
                        Math.round(
                            simulationTime / 0.5
                        ) * 50,
                        data.time.length - 1
                    );

                updateMetrics(
                    metricIndex
                );

                lastMetricTime =
                    simulationTime;
            }}

            if (simulationTime < 10) {{
                requestAnimationFrame(
                    animate
                );
            }}
        }}

        window.playPendulum = function() {{

            startTime = null;
            lastMetricTime = -0.5;

            updateMetrics(0);

            requestAnimationFrame(
                animate
            );
        }};

        const playButton =
            document.createElement("button");

        playButton.textContent =
            "▶ Play";

        playButton.style.cssText = `
            position: absolute;
            top: 8px;
            left: 8px;
            z-index: 100;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            background: #2563eb;
            color: white;
            font-size: 14px;
            cursor: pointer;
        `;

        plot.parentElement.style.position =
            "relative";

        plot.parentElement.appendChild(
            playButton
        );

        playButton.onclick =
            window.playPendulum;

    </script>
    """

    return html


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

        return

    result = st.session_state[
        "pendulum_result"
    ]

    st.subheader("3D Simulation")

    components.html(
        create_animation_html(result),
        height=760,
        scrolling=False
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
