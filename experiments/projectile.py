import math
import streamlit as st
import plotly.graph_objects as go


def projectile_experiment():

    st.markdown(
        """
        <div class="selection-header">
            <div class="section-title">Projectile Motion</div>
            <div class="selection-description">
                Explore how speed, angle, height, and gravity affect projectile motion.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    left, right = st.columns(2)

    with left:
        velocity = st.number_input(
            "Initial Speed (m/s)",
            min_value=0.0,
            value=20.0,
            step=1.0
        )

        angle = st.number_input(
            "Launch Angle (degrees)",
            min_value=0.0,
            max_value=90.0,
            value=45.0,
            step=1.0
        )

        height = st.number_input(
            "Initial Height (m)",
            min_value=0.0,
            value=0.0,
            step=1.0
        )

    with right:
        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.01,
            value=9.81,
            step=0.1
        )

        mass = st.number_input(
            "Mass (kg)",
            min_value=0.01,
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
    angle_rad = math.radians(angle)

    vx0 = velocity * math.cos(angle_rad)
    vy0 = velocity * math.sin(angle_rad)

    # Time until the projectile reaches the ground.
    total_time = (
        vy0 + math.sqrt(
            vy0 ** 2 + 2 * gravity * height
        )
    ) / gravity

    # Time required to reach maximum height.
    time_to_peak = vy0 / gravity

    # Maximum height.
    max_height = (
        height +
        (vy0 ** 2) / (2 * gravity)
    )

    # Horizontal range.
    horizontal_range = vx0 * total_time

    # Generate trajectory points.
    point_count = 200

    times = [
        total_time * i / (point_count - 1)
        for i in range(point_count)
    ]

    x_values = []
    y_values = []

    for t in times:
        x = vx0 * t
        y = height + vy0 * t - 0.5 * gravity * t ** 2

        if y >= 0:
            x_values.append(x)
            y_values.append(y)

    # Create trajectory graph.
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            name="Trajectory"
        )
    )

    # Mark launch point.
    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[height],
            mode="markers",
            name="Launch"
        )
    )

    # Mark maximum height.
    peak_x = vx0 * time_to_peak

    fig.add_trace(
        go.Scatter(
            x=[peak_x],
            y=[max_height],
            mode="markers",
            name="Maximum Height"
        )
    )

    fig.update_layout(
        title="Projectile Trajectory",
        xaxis_title="Horizontal Distance (m)",
        yaxis_title="Height (m)",
        template="plotly_dark",
        height=500,
        margin=dict(
            l=40,
            r=40,
            t=60,
            b=40
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
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

    st.markdown("### Initial Conditions")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Horizontal Velocity",
            f"{vx0:.2f} m/s"
        )

    with col2:
        st.metric(
            "Vertical Velocity",
            f"{vy0:.2f} m/s"
        )

    with col3:
        st.metric(
            "Mass",
            f"{mass:.2f} kg"
        )
