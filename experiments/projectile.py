import math
import streamlit as st
import plotly.graph_objects as go


def projectile_experiment():

    st.markdown(
        """
        <div class="selection-header">
            <div class="section-title">Projectile Motion</div>
            <div class="selection-description">
                Enter the initial conditions and observe the projectile motion.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Initial Conditions")

    col1, col2, col3 = st.columns(3)

    with col1:
        velocity = st.number_input(
            "Initial Speed (m/s)",
            min_value=0.1,
            max_value=100.0,
            value=20.0,
            step=1.0
        )

    with col2:
        angle = st.number_input(
            "Launch Angle (°)",
            min_value=0.0,
            max_value=90.0,
            value=45.0,
            step=1.0
        )

    with col3:
        height = st.number_input(
            "Initial Height (m)",
            min_value=0.0,
            max_value=500.0,
            value=0.0,
            step=1.0
        )

    col1, col2 = st.columns(2)

    with col1:
        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.01,
            max_value=30.0,
            value=9.81,
            step=0.1
        )

    with col2:
        mass = st.number_input(
            "Mass (kg)",
            min_value=0.01,
            max_value=1000.0,
            value=1.0,
            step=0.1
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "Run Experiment",
        type="primary",
        use_container_width=True
    ):
        run_projectile_simulation(
            velocity,
            angle,
            height,
            gravity,
            mass
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Back to Experiments"):
        st.session_state.page = "select"
        st.query_params.clear()
        st.rerun()


def run_projectile_simulation(
    velocity,
    angle,
    height,
    gravity,
    mass
):

    theta = math.radians(angle)

    vx = velocity * math.cos(theta)
    vy = velocity * math.sin(theta)

    total_time = (
        vy + math.sqrt(
            vy ** 2 + 2 * gravity * height
        )
    ) / gravity

    max_height = (
        height +
        vy ** 2 / (2 * gravity)
    )

    horizontal_range = vx * total_time

    point_count = 100

    times = [
        total_time * i / (point_count - 1)
        for i in range(point_count)
    ]

    x_values = []
    y_values = []

    for t in times:

        x = vx * t

        y = (
            height
            + vy * t
            - 0.5 * gravity * t ** 2
        )

        x_values.append(x)
        y_values.append(max(0.0, y))

    x_max = max(horizontal_range * 1.1, 10)
    y_max = max(max_height * 1.15, 10)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            line=dict(
                width=2,
                dash="dot"
            ),
            name="Trajectory"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[x_values[0]],
            y=[y_values[0]],
            mode="markers",
            marker=dict(
                size=20
            ),
            name="Projectile"
        )
    )

    frames = []

    for i in range(point_count):

        frames.append(
            go.Frame(
                data=[
                    go.Scatter(
                        x=x_values[:i + 1],
                        y=y_values[:i + 1],
                        mode="lines",
                        line=dict(
                            width=4
                        )
                    ),
                    go.Scatter(
                        x=[x_values[i]],
                        y=[y_values[i]],
                        mode="markers",
                        marker=dict(
                            size=20
                        )
                    )
                ],
                name=str(i)
            )
        )

    fig.frames = frames

    fig.update_layout(
        title="Projectile Motion",
        xaxis=dict(
            title="Horizontal Distance (m)",
            range=[0, x_max]
        ),
        yaxis=dict(
            title="Height (m)",
            range=[0, y_max]
        ),
        template="plotly_dark",
        height=600,
        showlegend=True,
        margin=dict(
            l=70,
            r=40,
            t=80,
            b=130
        ),
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "showactive": False,
                "x": 0.5,
                "xanchor": "center",
                "y": -0.20,
                "yanchor": "top",
                "buttons": [
                    {
                        "label": "▶  PLAY",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {
                                    "duration": 30,
                                    "redraw": True
                                },
                                "transition": {
                                    "duration": 0
                                },
                                "fromcurrent": False,
                                "mode": "immediate"
                            }
                        ]
                    }
                ]
            }
        ]
    )

    st.markdown("### Simulation")

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

    st.markdown(
        """
        <style>
        .js-plotly-plot .updatemenu-button {
            font-size: 22px !important;
            font-weight: 700 !important;
        }

        .js-plotly-plot .updatemenu-button rect {
            height: 48px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Flight Time",
            f"{total_time:.2f} s"
        )

    with col2:
        st.metric(
            "Maximum Height",
            f"{max_height:.2f} m"
        )

    with col3:
        st.metric(
            "Horizontal Range",
            f"{horizontal_range:.2f} m"
        )

    st.markdown("### Initial Velocity")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Initial Speed",
            f"{velocity:.2f} m/s"
        )

    with col2:
        st.metric(
            "Horizontal Velocity",
            f"{vx:.2f} m/s"
        )

    with col3:
        st.metric(
            "Vertical Velocity",
            f"{vy:.2f} m/s"
        )

    st.markdown("### Experiment Conditions")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Launch Angle",
            f"{angle:.1f}°"
        )

    with col2:
        st.metric(
            "Gravity",
            f"{gravity:.2f} m/s²"
        )

    with col3:
        st.metric(
            "Mass",
            f"{mass:.2f} kg"
        )
