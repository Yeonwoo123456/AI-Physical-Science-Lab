import math
import time
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

    # -------------------------
    # Parameters
    # -------------------------

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

    # -------------------------
    # Run Experiment
    # -------------------------

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

    # -------------------------
    # Back button
    # -------------------------

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

    # -------------------------
    # Convert angle
    # -------------------------

    theta = math.radians(angle)

    # Initial velocity components

    vx = velocity * math.cos(theta)
    vy = velocity * math.sin(theta)

    # -------------------------
    # Flight time
    # -------------------------

    total_time = (
        vy + math.sqrt(
            vy ** 2 + 2 * gravity * height
        )
    ) / gravity

    # -------------------------
    # Maximum height
    # -------------------------

    max_height = (
        height +
        (vy ** 2) / (2 * gravity)
    )

    # -------------------------
    # Horizontal range
    # -------------------------

    horizontal_range = vx * total_time

    # -------------------------
    # Maximum height time
    # -------------------------

    time_to_peak = vy / gravity

    # -------------------------
    # Create trajectory
    # -------------------------

    point_count = 200

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

        if y >= 0:
            x_values.append(x)
            y_values.append(y)

    # -------------------------
    # Animation
    # -------------------------

    st.markdown("### Simulation")

    chart_placeholder = st.empty()

    # Calculate axis ranges

    x_max = max(
        horizontal_range * 1.1,
        10
    )

    y_max = max(
        max_height * 1.15,
        10
    )

    # Number of animation frames

    animation_frames = 80

    for i in range(animation_frames):

        progress = i / (animation_frames - 1)

        current_time = total_time * progress

        # Current position

        current_x = vx * current_time

        current_y = (
            height
            + vy * current_time
            - 0.5 * gravity * current_time ** 2
        )

        current_y = max(current_y, 0)

        # Draw trajectory up to current point

        visible_points = max(
            2,
            int(len(x_values) * progress)
        )

        fig = go.Figure()

        # Ground

        fig.add_trace(
            go.Scatter(
                x=[0, x_max],
                y=[0, 0],
                mode="lines",
                line=dict(
                    width=3
                ),
                name="Ground"
            )
        )

        # Trajectory

        fig.add_trace(
            go.Scatter(
                x=x_values[:visible_points],
                y=y_values[:visible_points],
                mode="lines",
                line=dict(
                    width=4
                ),
                name="Trajectory"
            )
        )

        # Moving object

        fig.add_trace(
            go.Scatter(
                x=[current_x],
                y=[current_y],
                mode="markers",
                marker=dict(
                    size=18
                ),
                name="Projectile"
            )
        )

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
            height=550,
            showlegend=True
        )

        chart_placeholder.plotly_chart(
            fig,
            use_container_width=True,
            key=f"projectile_frame_{i}"
        )

        time.sleep(0.03)

    # -------------------------
    # Final Results
    # -------------------------

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
