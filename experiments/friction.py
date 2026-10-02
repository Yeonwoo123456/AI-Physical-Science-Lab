import json
import re

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from app_modules import client


@st.cache_data
def simulate_friction(
    mass,
    mu_static,
    mu_kinetic,
    applied_force,
    gravity,
    duration=8.0,
    dt=0.01
):
    time = np.arange(0.0, duration + dt, dt)
    n = len(time)

    normal_force = mass * gravity
    max_static_friction = mu_static * normal_force
    kinetic_friction = mu_kinetic * normal_force

    position = np.zeros(n)
    velocity = np.zeros(n)
    acceleration = np.zeros(n)
    friction = np.zeros(n)
    net_force = np.zeros(n)

    moving = False

    for i in range(n):
        if not moving:
            if abs(applied_force) <= max_static_friction:
                friction[i] = -applied_force
                net_force[i] = 0.0
                acceleration[i] = 0.0
                velocity[i] = 0.0

                if i > 0:
                    position[i] = position[i - 1]
                continue

            moving = True

        direction = np.sign(velocity[i - 1]) if i > 0 and abs(velocity[i - 1]) > 1e-9 else np.sign(applied_force)

        friction[i] = -direction * kinetic_friction
        net_force[i] = applied_force + friction[i]
        acceleration[i] = net_force[i] / mass

        if i > 0:
            velocity[i] = velocity[i - 1] + acceleration[i] * dt
            position[i] = (
                position[i - 1]
                + velocity[i - 1] * dt
                + 0.5 * acceleration[i] * dt * dt
            )

    state = np.where(
        np.abs(velocity) > 1e-6,
        "KINETIC",
        "STATIC"
    )

    return {
        "time": time,
        "position": position,
        "velocity": velocity,
        "acceleration": acceleration,
        "friction": friction,
        "net_force": net_force,
        "normal_force": np.full(n, normal_force),
        "weight": np.full(n, -normal_force),
        "max_static_friction": max_static_friction,
        "kinetic_friction": kinetic_friction,
        "state": state
    }


def parse_ai_friction(user_text):
    result = {
        "mass": None,
        "mu_static": None,
        "mu_kinetic": None,
        "applied_force": None,
        "gravity": None
    }

    system_prompt = """
You are a physics parameter parser for a friction experiment.

Return ONLY valid JSON:

{
    "mass": null,
    "mu_static": null,
    "mu_kinetic": null,
    "applied_force": null,
    "gravity": null
}

Units:
mass: kg
mu_static: dimensionless
mu_kinetic: dimensionless
applied_force: N
gravity: m/s^2

Only extract explicitly stated numerical values.
Never guess missing values.

If the user says left / 왼쪽, applied_force should be negative.
If the user says right / 오른쪽, applied_force should be positive.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"```json|```", "", content).strip()

        parsed = json.loads(content)

        for key in result:
            value = parsed.get(key)
            if value is not None:
                result[key] = float(value)

    except Exception:
        pass

    patterns = {
        "mass": r"(-?\d+(?:\.\d+)?)\s*(?:kg|킬로그램)",
        "mu_static": r"(?:μs|mu_s|mus|정지\s*마찰계수)\s*(?:=|은|는)?\s*(-?\d+(?:\.\d+)?)",
        "mu_kinetic": r"(?:μk|mu_k|muk|운동\s*마찰계수)\s*(?:=|은|는)?\s*(-?\d+(?:\.\d+)?)",
        "applied_force": r"(-?\d+(?:\.\d+)?)\s*(?:N|뉴턴)",
        "gravity": r"(-?\d+(?:\.\d+)?)\s*(?:m/s\^?2|m/s²)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, user_text, re.IGNORECASE)
        if match:
            try:
                result[key] = float(match.group(1))
            except ValueError:
                pass

    text = user_text.lower()

    if result["applied_force"] is not None:
        if "왼쪽" in user_text or "left" in text:
            result["applied_force"] = -abs(result["applied_force"])
        elif "오른쪽" in user_text or "right" in text:
            result["applied_force"] = abs(result["applied_force"])

    return result


def force_arrow(
    fig,
    force,
    y,
    label,
    scale,
    color,
    x0=0.0
):
    if abs(force) < 1e-9:
        return

    length = abs(force) * scale
    x1 = x0 + np.sign(force) * length

    fig.add_annotation(
        x=x1,
        y=y,
        ax=x0,
        ay=y,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.2,
        arrowwidth=4,
        arrowcolor=color,
        text=f"{label}: {abs(force):.1f} N",
        font=dict(size=14, color=color),
        bgcolor="rgba(14,17,23,0.85)",
        bordercolor=color,
        borderwidth=1,
        borderpad=4
    )


def create_force_diagram(
    mass,
    applied_force,
    friction_force,
    gravity,
    max_static_friction,
    state
):
    normal = mass * gravity
    maximum_force = max(
        abs(applied_force),
        abs(friction_force),
        abs(normal),
        1.0
    )

    scale_horizontal = 2.5 / maximum_force
    scale_vertical = 1.6 / maximum_force

    fig = go.Figure()

    fig.add_shape(
        type="rect",
        x0=-0.45,
        x1=0.45,
        y0=-0.3,
        y1=0.3,
        fillcolor="#B8B8B8",
        line=dict(color="white", width=2)
    )

    fig.add_shape(
        type="line",
        x0=-3.2,
        x1=3.2,
        y0=-0.75,
        y1=-0.75,
        line=dict(color="#888888", width=5)
    )

    force_arrow(
        fig,
        applied_force,
        0.0,
        "Applied",
        scale_horizontal,
        "#4DA6FF"
    )

    force_arrow(
        fig,
        friction_force,
        -0.05,
        "Friction",
        scale_horizontal,
        "#FF6B6B"
    )

    force_arrow(
        fig,
        normal,
        0.8,
        "Normal",
        scale_vertical,
        "#69D391"
    )

    force_arrow(
        fig,
        -normal,
        -1.25,
        "Weight",
        scale_vertical,
        "#C084FC"
    )

    fig.add_annotation(
        x=0,
        y=1.55,
        text=f"<b>{state}</b>",
        showarrow=False,
        font=dict(
            size=20,
            color="white"
        )
    )

    fig.add_annotation(
        x=0,
        y=1.25,
        text=f"Maximum static friction: {max_static_friction:.2f} N",
        showarrow=False,
        font=dict(size=13, color="#DDDDDD")
    )

    fig.update_layout(
        height=520,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        xaxis=dict(
            range=[-3.5, 3.5],
            visible=False,
            fixedrange=True
        ),
        yaxis=dict(
            range=[-1.7, 1.8],
            visible=False,
            fixedrange=True
        ),
        showlegend=False
    )

    return fig


def create_motion_figure(position, time):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=time,
            y=position,
            mode="lines",
            name="Position"
        )
    )

    fig.update_layout(
        height=320,
        xaxis_title="Time (s)",
        yaxis_title="Position (m)"
    )

    return fig


def create_velocity_figure(velocity, time):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=time,
            y=velocity,
            mode="lines",
            name="Velocity"
        )
    )

    fig.update_layout(
        height=320,
        xaxis_title="Time (s)",
        yaxis_title="Velocity (m/s)"
    )

    return fig


def friction_experiment():

    st.subheader("Friction Experiment")

    if "friction_mass" not in st.session_state:
        st.session_state.friction_mass = 10.0

    if "friction_mu_static" not in st.session_state:
        st.session_state.friction_mu_static = 0.50

    if "friction_mu_kinetic" not in st.session_state:
        st.session_state.friction_mu_kinetic = 0.30

    if "friction_force" not in st.session_state:
        st.session_state.friction_force = 40.0

    if "friction_gravity" not in st.session_state:
        st.session_state.friction_gravity = 9.81

    if "friction_result" not in st.session_state:
        st.session_state.friction_result = None

    st.markdown("### Describe Your Experiment")

    ai_text = st.text_area(
        "AI Assistant",
        placeholder=(
            "Example: 질량 10kg인 블록을 μs 0.5, μk 0.3인 "
            "바닥에서 오른쪽으로 50N의 힘으로 밀어줘"
        ),
        key="friction_ai_input",
        height=100
    )

    if st.button(
        "Run AI Analysis",
        key="friction_ai_button"
    ):
        if ai_text.strip():
            parsed = parse_ai_friction(ai_text)

            if parsed["mass"] is not None:
                st.session_state.friction_mass = parsed["mass"]

            if parsed["mu_static"] is not None:
                st.session_state.friction_mu_static = parsed["mu_static"]

            if parsed["mu_kinetic"] is not None:
                st.session_state.friction_mu_kinetic = parsed["mu_kinetic"]

            if parsed["applied_force"] is not None:
                st.session_state.friction_force = parsed["applied_force"]

            if parsed["gravity"] is not None:
                st.session_state.friction_gravity = parsed["gravity"]

            st.session_state.friction_result = None
            st.success("Experiment parameters updated.")

    st.markdown("### Parameters")

    col1, col2 = st.columns(2)

    with col1:
        mass = st.number_input(
            "Mass (kg)",
            min_value=0.01,
            max_value=1000.0,
            step=0.1,
            key="friction_mass"
        )

        mu_static = st.number_input(
            "Coefficient of Static Friction μs",
            min_value=0.0,
            max_value=5.0,
            step=0.01,
            key="friction_mu_static"
        )

        mu_kinetic = st.number_input(
            "Coefficient of Kinetic Friction μk",
            min_value=0.0,
            max_value=5.0,
            step=0.01,
            key="friction_mu_kinetic"
        )

    with col2:
        applied_force = st.number_input(
            "Applied Force (N)",
            min_value=-1000.0,
            max_value=1000.0,
            step=1.0,
            key="friction_force"
        )

        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.0,
            max_value=30.0,
            step=0.1,
            key="friction_gravity"
        )

    normal_force = mass * gravity
    max_static = mu_static * normal_force
    kinetic = mu_kinetic * normal_force

    st.info(
        f"Normal Force: {normal_force:.2f} N  |  "
        f"Maximum Static Friction: {max_static:.2f} N  |  "
        f"Kinetic Friction: {kinetic:.2f} N"
    )

    if st.button(
        "Run Experiment",
        type="primary",
        key="friction_run_button"
    ):
        st.session_state.friction_result = simulate_friction(
            mass=mass,
            mu_static=mu_static,
            mu_kinetic=mu_kinetic,
            applied_force=applied_force,
            gravity=gravity
        )

    result = st.session_state.friction_result

    if result is None:
        current_friction = (
            -applied_force
            if abs(applied_force) <= max_static
            else -np.sign(applied_force) * kinetic
        )

        current_state = (
            "STATIC"
            if abs(applied_force) <= max_static
            else "KINETIC"
        )

        st.markdown("### Force Diagram")

        fig = create_force_diagram(
            mass,
            applied_force,
            current_friction,
            gravity,
            max_static,
            current_state
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key="friction_force_diagram_preview"
        )

    else:
        time = result["time"]
        position = result["position"]
        velocity = result["velocity"]
        acceleration = result["acceleration"]
        friction = result["friction"]
        net_force = result["net_force"]

        final_state = result["state"][-1]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "State",
                final_state
            )

        with col2:
            st.metric(
                "Velocity",
                f"{velocity[-1]:.2f} m/s"
            )

        with col3:
            st.metric(
                "Acceleration",
                f"{acceleration[-1]:.2f} m/s²"
            )

        with col4:
            st.metric(
                "Net Force",
                f"{net_force[-1]:.2f} N"
            )

        st.markdown("### Force Diagram")

        diagram_index = len(time) - 1

        diagram_fig = create_force_diagram(
            mass,
            applied_force,
            friction[diagram_index],
            gravity,
            max_static,
            final_state
        )

        st.plotly_chart(
            diagram_fig,
            use_container_width=True,
            key="friction_force_diagram"
        )

        st.markdown("### Motion")

        st.plotly_chart(
            create_motion_figure(position, time),
            use_container_width=True,
            key="friction_position_graph"
        )

        st.plotly_chart(
            create_velocity_figure(velocity, time),
            use_container_width=True,
            key="friction_velocity_graph"
        )

        st.markdown("### Force Analysis")

        force_fig = go.Figure()

        force_fig.add_trace(
            go.Scatter(
                x=time,
                y=np.full_like(
                    time,
                    applied_force
                ),
                mode="lines",
                name="Applied Force"
            )
        )

        force_fig.add_trace(
            go.Scatter(
                x=time,
                y=friction,
                mode="lines",
                name="Friction"
            )
        )

        force_fig.add_trace(
            go.Scatter(
                x=time,
                y=net_force,
                mode="lines",
                name="Net Force"
            )
        )

        force_fig.add_hline(
            y=max_static,
            line_dash="dash",
            opacity=0.5
        )

        force_fig.add_hline(
            y=-max_static,
            line_dash="dash",
            opacity=0.5
        )

        force_fig.update_layout(
            height=350,
            xaxis_title="Time (s)",
            yaxis_title="Force (N)"
        )

        st.plotly_chart(
            force_fig,
            use_container_width=True,
            key="friction_force_graph"
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    if st.button(
        "Back to Experiments",
        key="friction_back_button"
    ):
        st.session_state.page = "select"
        st.session_state.experiment = None
        st.session_state.pop("friction_result", None)
        st.query_params.clear()
        st.rerun()
