import math
import json
import re

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from app_modules import client


# -----------------------------
# Spring Simulation
# -----------------------------
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


# -----------------------------
# AI Parser
# -----------------------------
def parse_ai_spring(user_text):
    result = {
        "mass": None,
        "spring_constant": None,
        "initial_displacement": None,
        "gravity": None,
        "damping": None
    }

    # AI parsing
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
- Mass unit: kg
- Spring constant unit: N/m
- Initial displacement unit: m
- Gravity unit: m/s^2
- Damping is a numerical coefficient.
- If the user says "compress" or "압축", displacement should be negative.
- If the user says "pull", "stretch", "당겨", or "늘려", displacement should normally be positive.
"""

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                temperature=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ]
            )

            content = response.choices[0].message.content.strip()

            content = re.sub(r"```json|```", "", content).strip()

            ai_result = json.loads(content)

            for key in result:
                if ai_result.get(key) is not None:
                    result[key] = float(ai_result[key])

        except Exception:
            pass

    # --------------------------------
    # Explicit numerical value parsing
    # --------------------------------

    # Mass
    match = re.search(
        r"(?:질량|mass)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)\s*(?:kg|킬로그램)?",
        user_text,
        re.IGNORECASE
    )

    if match:
        result["mass"] = float(match.group(1))

    # Spring constant
    match = re.search(
        r"(?:스프링\s*상수|spring\s*constant|k)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)\s*(?:N\s*/?\s*m|N/m)?",
        user_text,
        re.IGNORECASE
    )

    if match:
        result["spring_constant"] = float(match.group(1))

    # Initial displacement
    displacement_match = re.search(
        r"(?:처음|초기|initial)?\s*(?:변위|displacement)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)\s*(?:m|미터)?",
        user_text,
        re.IGNORECASE
    )

    if displacement_match:
        result["initial_displacement"] = float(
            displacement_match.group(1)
        )

    # Pull / stretch / compress expressions
    if result["initial_displacement"] is None:

        match = re.search(
            r"(?:당겨|늘려|늘어|pull|stretch)\s*(?:서|서)?\s*(-?\d+(?:\.\d+)?)\s*(?:m|미터)",
            user_text,
            re.IGNORECASE
        )

        if match:
            result["initial_displacement"] = abs(
                float(match.group(1))
            )

        match = re.search(
            r"(?:압축|compress)\s*(?:해서|하여)?\s*(-?\d+(?:\.\d+)?)\s*(?:m|미터)",
            user_text,
            re.IGNORECASE
        )

        if match:
            result["initial_displacement"] = -abs(
                float(match.group(1))
            )

    # Gravity
    match = re.search(
        r"(?:중력|gravity|g)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)\s*(?:m/s.?2|m/s²)?",
        user_text,
        re.IGNORECASE
    )

    if match:
        result["gravity"] = float(match.group(1))

    # Damping
    match = re.search(
        r"(?:감쇠|damping)\s*(?:은|는|이|가|=|:)?\s*(-?\d+(?:\.\d+)?)",
        user_text,
        re.IGNORECASE
    )

    if match:
        result["damping"] = float(match.group(1))

    return result


# -----------------------------
# 3D Spring
# -----------------------------
def create_spring_figure(
    displacement,
    spring_length=3.0,
    turns=14
):
    base_x = 0.0

    mass_x = spring_length + displacement

    if mass_x < 0.8:
        mass_x = 0.8

    spring_start = 0.2
    spring_end = mass_x - 0.35

    if spring_end <= spring_start:
        spring_end = spring_start + 0.2

    x = np.linspace(
        spring_start,
        spring_end,
        turns * 20
    )

    y = 0.18 * np.sin(
        np.linspace(0, turns * 2 * np.pi, len(x))
    )

    z = np.zeros_like(x)

    fig = go.Figure()

    # Fixed wall
    fig.add_trace(
        go.Scatter3d(
            x=[base_x, base_x],
            y=[-0.45, 0.45],
            z=[0, 0],
            mode="lines",
            line=dict(width=12),
            showlegend=False
        )
    )

    # Spring
    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="lines",
            line=dict(width=6),
            showlegend=False
        )
    )

    # Mass
    fig.add_trace(
        go.Scatter3d(
            x=[mass_x],
            y=[0],
            z=[0],
            mode="markers",
            marker=dict(
                size=28,
                symbol="square"
            ),
            showlegend=False
        )
    )

    # Center line
    fig.add_trace(
        go.Scatter3d(
            x=[0, spring_length + 0.8],
            y=[0, 0],
            z=[0, 0],
            mode="lines",
            line=dict(
                width=2,
                dash="dash"
            ),
            showlegend=False
        )
    )

    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        scene=dict(
            xaxis=dict(
                range=[-0.5, spring_length + 1.0],
                title="",
                showticklabels=False
            ),
            yaxis=dict(
                range=[-1, 1],
                title="",
                showticklabels=False
            ),
            zaxis=dict(
                range=[-1, 1],
                title="",
                showticklabels=False
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=2.5,
                y=1,
                z=1
            ),
            camera=dict(
                eye=dict(
                    x=1.5,
                    y=0,
                    z=0.8
                )
            )
        ),
        showlegend=False
    )

    return fig


# -----------------------------
# Main Experiment
# -----------------------------
def spring_experiment():

    st.subheader("Spring Experiment")

    # -----------------------------
    # Session State
    # -----------------------------
    defaults = {
        "spring_mass": 1.00,
        "spring_k": 50.00,
        "spring_displacement": 0.30,
        "spring_gravity": 9.81,
        "spring_damping": 0.02,
        "spring_ai_text": ""
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # -----------------------------
    # AI Natural Language
    # -----------------------------
    st.markdown("### AI Natural Language")

    ai_text = st.text_input(
        "Describe your spring experiment",
        placeholder="예: 질량 2kg, 스프링 상수 50N/m, 0.3m 당겨서 시작해"
    )

    if st.button("Run AI Analysis", key="spring_ai_button"):

        if ai_text.strip():

            parsed = parse_ai_spring(ai_text)

            if parsed["mass"] is not None:
                st.session_state.spring_mass = parsed["mass"]

            if parsed["spring_constant"] is not None:
                st.session_state.spring_k = parsed["spring_constant"]

            if parsed["initial_displacement"] is not None:
                st.session_state.spring_displacement = parsed[
                    "initial_displacement"
                ]

            if parsed["gravity"] is not None:
                st.session_state.spring_gravity = parsed["gravity"]

            if parsed["damping"] is not None:
                st.session_state.spring_damping = parsed["damping"]

            st.rerun()

    # -----------------------------
    # Manual Parameters
    # -----------------------------
    st.markdown("### Manual Parameters")

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

    # -----------------------------
    # Simulation
    # -----------------------------
    result = simulate_spring(
        mass=mass,
        spring_constant=spring_constant,
        initial_displacement=initial_displacement,
        gravity=gravity,
        damping=damping
    )

    time = result["time"]
    displacement = result["x"]

    # -----------------------------
    # Current Values
    # -----------------------------
    st.markdown("### Simulation")

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

    # -----------------------------
    # 3D Animation
    # -----------------------------
    frames = []

    for i in range(0, len(time), 5):

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

    with st.container(border=True):
        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # -----------------------------
    # Analysis
    # -----------------------------
    st.markdown("### Analysis")

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

    # -----------------------------
    # Energy
    # -----------------------------
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
