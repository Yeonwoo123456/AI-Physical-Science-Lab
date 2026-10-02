import math

import streamlit as st
import plotly.graph_objects as go

from components.vector_controller import vector_controller


def projectile_experiment():

    st.markdown(
        """
        <div class="selection-header">
            <div class="section-title">Projectile Motion</div>
            <div class="selection-description">
                Drag the arrow to adjust the launch speed and angle.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if "projectile_velocity" not in st.session_state:
        st.session_state.projectile_velocity = 20.0

    if "projectile_angle" not in st.session_state:
        st.session_state.projectile_angle = 45.0

    st.markdown(
        "### Launch Vector"
    )

    result = vector_controller(
        velocity=st.session_state.projectile_velocity,
        angle=st.session_state.projectile_angle,
        key="projectile_vector"
    )

    if result is not None:

        new_velocity = result.get(
            "velocity",
            st.session_state.projectile_velocity
        )

        new_angle = result.get(
            "angle",
            st.session_state.projectile_angle
        )

        st.session_state.projectile_velocity = new_velocity
        st.session_state.projectile_angle = new_angle

    st.markdown(
        "### Parameters"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        velocity = st.number_input(
            "Initial Speed (m/s)",
            min_value=0.1,
            max_value=100.0,
            value=float(
                st.session_state.projectile_velocity
            ),
            step=1.0,
            key="projectile_velocity_input"
        )

    with col2:

        angle = st.number_input(
            "Launch Angle (°)",
            min_value=0.0,
            max_value=90.0,
            value=float(
                st.session_state.projectile_angle
            ),
            step=1.0,
            key="projectile_angle_input"
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

    if (
        abs(
            velocity -
            st.session_state.projectile_velocity
        ) > 0.001
        or
        abs(
            angle -
            st.session_state.projectile_angle
        ) > 0.001
    ):

        st.session_state.projectile_velocity = velocity
        st.session_state.projectile_angle = angle

        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "Run Experiment",
        type="primary",
        use_container_width=True
    ):

        run_simulation(
            st.session_state.projectile_velocity,
            st.session_state.projectile_angle,
            height,
            gravity,
            mass
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Back to Experiments"):

        st.session_state.page = "select"

        st.query_params.clear()

        st.rerun()


def run_simulation(
    velocity,
    angle,
    height,
    gravity,
    mass
):

    theta = math.radians(angle)

    vx = (
        velocity *
        math.cos(theta)
    )

    vy = (
        velocity *
        math.sin(theta)
    )

    total_time = (
        vy +
        math.sqrt(
            vy ** 2 +
            2 * gravity * height
        )
    ) / gravity

    time_to_peak = (
        vy / gravity
    )

    max_height = (
        height +
        vy ** 2 /
        (2 * gravity)
    )

    horizontal_range = (
        vx *
        total_time
    )

    point_count = 250

    times = [
        total_time * i /
        (point_count - 1)
        for i in range(point_count)
    ]

    x_values = []
    y_values = []

    for t in times:

        x = vx * t

        y = (
            height +
            vy * t -
            0.5 *
            gravity *
            t ** 2
        )

        if y >= 0:

            x_values.append(x)
            y_values.append(y)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            name="Trajectory",
            line=dict(width=4)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[height],
            mode="markers",
            name="Launch Point",
            marker=dict(size=12)
        )
    )

    peak_x = (
        vx *
        time_to_peak
    )

    fig.add_trace(
        go.Scatter(
            x=[peak_x],
            y=[max_height],
            mode="markers",
            name="Maximum Height",
            marker=dict(size=10)
        )
    )

    fig.update_layout(
        title="Projectile Trajectory",
        xaxis_title="Horizontal Distance (m)",
        yaxis_title="Height (m)",
        template="plotly_dark",
        height=500
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
            f"{vx:.2f} m/s"
        )

    with col2:
        st.metric(
            "Vertical Velocity",
            f"{vy:.2f} m/s"
        )

    with col3:
        st.metric(
            "Mass",
            f"{mass:.2f} kg"
        )
