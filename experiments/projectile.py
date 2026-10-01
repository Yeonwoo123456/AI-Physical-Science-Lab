import math

import streamlit as st
import plotly.graph_objects as go

from streamlit_drawable_canvas import st_canvas


CANVAS_WIDTH = 900
CANVAS_HEIGHT = 500

ORIGIN_X = 90
ORIGIN_Y = 410

PIXELS_PER_MS = 5.0


def make_arrow(angle, velocity):
    length = velocity * PIXELS_PER_MS

    theta = math.radians(angle)

    end_x = ORIGIN_X + length * math.cos(theta)
    end_y = ORIGIN_Y - length * math.sin(theta)

    line = {
        "type": "line",
        "version": "4.4.0",
        "originX": "center",
        "originY": "center",
        "left": (ORIGIN_X + end_x) / 2,
        "top": (ORIGIN_Y + end_y) / 2,
        "width": length,
        "height": 0,
        "fill": "",
        "stroke": "#2E86DE",
        "strokeWidth": 5,
        "x1": 0,
        "y1": 0,
        "x2": length,
        "y2": 0,
        "angle": -angle,
        "scaleX": 1,
        "scaleY": 1,
        "selectable": False,
        "evented": False
    }

    arrow_head = {
        "type": "triangle",
        "version": "4.4.0",
        "originX": "center",
        "originY": "center",
        "left": end_x,
        "top": end_y,
        "width": 24,
        "height": 30,
        "fill": "#2E86DE",
        "angle": 90 - angle,
        "scaleX": 1,
        "scaleY": 1,
        "selectable": True,
        "evented": True,
        "object_id": "arrow_head"
    }

    origin = {
        "type": "circle",
        "version": "4.4.0",
        "originX": "center",
        "originY": "center",
        "left": ORIGIN_X,
        "top": ORIGIN_Y,
        "radius": 13,
        "fill": "#2E86DE",
        "stroke": "#ffffff",
        "strokeWidth": 2,
        "selectable": False,
        "evented": False
    }

    return {
        "version": "4.4.0",
        "objects": [
            line,
            origin,
            arrow_head
        ]
    }


def get_arrow_values(json_data):
    if not json_data:
        return None

    for obj in json_data.get("objects", []):
        if obj.get("object_id") == "arrow_head":
            x = obj.get("left", ORIGIN_X)
            y = obj.get("top", ORIGIN_Y)

            dx = x - ORIGIN_X
            dy = ORIGIN_Y - y

            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance < 10:
                return None

            angle = math.degrees(
                math.atan2(dy, dx)
            )

            angle = max(0, min(90, angle))

            velocity = distance / PIXELS_PER_MS

            return velocity, angle

    return None


def projectile_experiment():

    st.markdown(
        """
        <div class="selection-header">
            <div class="section-title">Projectile Motion</div>
            <div class="selection-description">
                Drag the arrow to change the launch speed and angle.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if "projectile_velocity" not in st.session_state:
        st.session_state.projectile_velocity = 20.0

    if "projectile_angle" not in st.session_state:
        st.session_state.projectile_angle = 45.0

    velocity_col, angle_col, height_col = st.columns(3)

    with velocity_col:
        velocity = st.number_input(
            "Initial Speed (m/s)",
            min_value=0.1,
            max_value=100.0,
            value=float(st.session_state.projectile_velocity),
            step=1.0,
            key="velocity_input"
        )

    with angle_col:
        angle = st.number_input(
            "Launch Angle (degrees)",
            min_value=0.0,
            max_value=90.0,
            value=float(st.session_state.projectile_angle),
            step=1.0,
            key="angle_input"
        )

    with height_col:
        height = st.number_input(
            "Initial Height (m)",
            min_value=0.0,
            max_value=500.0,
            value=0.0,
            step=1.0,
            key="height_input"
        )

    gravity_col, mass_col = st.columns(2)

    with gravity_col:
        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.01,
            max_value=30.0,
            value=9.81,
            step=0.1
        )

    with mass_col:
        mass = st.number_input(
            "Mass (kg)",
            min_value=0.01,
            max_value=1000.0,
            value=1.0,
            step=0.1
        )

    st.markdown(
        "### Adjust Launch Vector",
        unsafe_allow_html=True
    )

    st.caption(
        "Drag the blue arrow tip to change speed and launch angle."
    )

    canvas = st_canvas(
        fill_color="rgba(0,0,0,0)",
        stroke_width=5,
        stroke_color="#2E86DE",
        background_color="#f7f4ec",
        height=CANVAS_HEIGHT,
        width=CANVAS_WIDTH,
        drawing_mode="transform",
        initial_drawing=make_arrow(angle, velocity),
        display_toolbar=False,
        update_streamlit=True,
        key="projectile_vector_canvas"
    )

    dragged_values = get_arrow_values(
        canvas.json_data
    )

    if dragged_values is not None:
        new_velocity, new_angle = dragged_values

        new_velocity = round(
            max(0.1, min(100.0, new_velocity)),
            1
        )

        new_angle = round(
            max(0.0, min(90.0, new_angle)),
            1
        )

        if (
            abs(new_velocity - st.session_state.projectile_velocity) > 0.1
            or
            abs(new_angle - st.session_state.projectile_angle) > 0.1
        ):
            st.session_state.projectile_velocity = new_velocity
            st.session_state.projectile_angle = new_angle

            st.rerun()

    current_velocity = st.session_state.projectile_velocity
    current_angle = st.session_state.projectile_angle

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:20px;
            font-weight:600;
            margin:10px 0 25px 0;
        ">
            {current_velocity:.1f} m/s
            &nbsp;&nbsp;·&nbsp;&nbsp;
            {current_angle:.1f}°
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "Run Experiment",
        type="primary",
        use_container_width=True
    ):
        run_simulation(
            current_velocity,
            current_angle,
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

    vx = velocity * math.cos(theta)
    vy = velocity * math.sin(theta)

    total_time = (
        vy +
        math.sqrt(
            vy ** 2 +
            2 * gravity * height
        )
    ) / gravity

    time_to_peak = vy / gravity

    max_height = (
        height +
        vy ** 2 / (2 * gravity)
    )

    horizontal_range = vx * total_time

    point_count = 250

    times = [
        total_time * i / (point_count - 1)
        for i in range(point_count)
    ]

    x_values = []
    y_values = []

    for t in times:
        x = vx * t

        y = (
            height +
            vy * t -
            0.5 * gravity * t ** 2
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

    peak_x = vx * time_to_peak

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
