import math
import streamlit as st
import plotly.graph_objects as go


def collision_experiment():

    defaults = {
        "collision_shape1": "Sphere",
        "collision_shape2": "Cube",
        "collision_mass1": 2.0,
        "collision_mass2": 2.0,
        "collision_velocity1": 5.0,
        "collision_velocity2": -3.0,
        "collision_elasticity": 1.0
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.markdown(
        """
        <div class="selection-header">
            <div class="section-title">3D Collision</div>
            <div class="selection-description">
                Simulate a collision between two objects in 3D space.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Object 1")

        shape1 = st.selectbox(
            "Shape",
            ["Sphere", "Cube", "Cylinder"],
            key="collision_shape1"
        )

        mass1 = st.number_input(
            "Mass (kg)",
            min_value=0.1,
            max_value=1000.0,
            step=0.1,
            key="collision_mass1"
        )

        velocity1 = st.number_input(
            "Velocity (m/s)",
            min_value=0.0,
            max_value=100.0,
            step=0.5,
            key="collision_velocity1"
        )

    with col2:
        st.markdown("### Object 2")

        shape2 = st.selectbox(
            "Shape",
            ["Sphere", "Cube", "Cylinder"],
            key="collision_shape2"
        )

        mass2 = st.number_input(
            "Mass (kg)",
            min_value=0.1,
            max_value=1000.0,
            step=0.1,
            key="collision_mass2"
        )

        velocity2 = st.number_input(
            "Velocity (m/s)",
            min_value=0.0,
            max_value=100.0,
            step=0.5,
            key="collision_velocity2"
        )

    elasticity = st.slider(
        "Coefficient of Restitution",
        0.0,
        1.0,
        key="collision_elasticity"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "Run Experiment",
        type="primary",
        use_container_width=True
    ):

        run_collision(
            shape1,
            shape2,
            mass1,
            mass2,
            velocity1,
            velocity2,
            elasticity
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Back to Experiments"):

        for key in defaults:
            if key in st.session_state:
                del st.session_state[key]

        st.session_state.page = "select"
        st.query_params.clear()
        st.rerun()


def make_object(
    shape,
    x,
    color,
    name
):

    if shape == "Sphere":

        return go.Scatter3d(
            x=[x],
            y=[0],
            z=[0],
            mode="markers",
            marker=dict(
                size=25,
                color=color,
                symbol="circle"
            ),
            name=name
        )

    if shape == "Cube":

        return go.Scatter3d(
            x=[x],
            y=[0],
            z=[0],
            mode="markers",
            marker=dict(
                size=25,
                color=color,
                symbol="square"
            ),
            name=name
        )

    return go.Scatter3d(
        x=[x],
        y=[0],
        z=[0],
        mode="markers",
        marker=dict(
            size=25,
            color=color,
            symbol="diamond"
        ),
        name=name
    )


def run_collision(
    shape1,
    shape2,
    mass1,
    mass2,
    velocity1,
    velocity2,
    elasticity
):

    collision_distance = 4.0

    collision_time = (
        collision_distance /
        (velocity1 + velocity2)
        if velocity1 + velocity2 > 0
        else 1.0
    )

    total_time = collision_time + 2.5

    final_velocity1 = (
        (
            mass1 * velocity1
            + mass2 * velocity2
            - mass2 * elasticity *
            (velocity1 - velocity2)
        )
        /
        (mass1 + mass2)
    )

    final_velocity2 = (
        (
            mass1 * velocity1
            + mass2 * velocity2
            + mass1 * elasticity *
            (velocity1 - velocity2)
        )
        /
        (mass1 + mass2)
    )

    points = 100

    times = [
        total_time * i / (points - 1)
        for i in range(points)
    ]

    positions1 = []
    positions2 = []

    for t in times:

        if t <= collision_time:

            x1 = -collision_distance + velocity1 * t
            x2 = collision_distance - velocity2 * t

        else:

            dt = t - collision_time

            x1 = final_velocity1 * dt
            x2 = final_velocity2 * dt

        positions1.append(x1)
        positions2.append(x2)

    fig = go.Figure()

    fig.add_trace(
        make_object(
            shape1,
            positions1[0],
            "blue",
            "Object 1"
        )
    )

    fig.add_trace(
        make_object(
            shape2,
            positions2[0],
            "red",
            "Object 2"
        )
    )

    frames = []

    for i in range(points):

        frames.append(
            go.Frame(
                data=[
                    make_object(
                        shape1,
                        positions1[i],
                        "blue",
                        "Object 1"
                    ),
                    make_object(
                        shape2,
                        positions2[i],
                        "red",
                        "Object 2"
                    )
                ],
                name=str(i)
            )
        )

    fig.frames = frames

    fig.update_layout(

        title="3D Collision Simulation",

        scene=dict(

            xaxis=dict(
    title="X Position (m)",
    range=[
        min(positions1 + positions2) - 3,
        max(positions1 + positions2) + 3
    ]
),

            yaxis=dict(
                title="Y Position (m)",
                range=[
                    -5,
                    5
                ]
            ),

            zaxis=dict(
                title="Z Position (m)",
                range=[
                    -5,
                    5
                ]
            ),

            aspectmode="cube"
        ),

        template="plotly_dark",

        height=600,

        margin=dict(
            l=0,
            r=0,
            t=60,
            b=100
        ),

        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "x": 0.5,
                "xanchor": "center",
                "y": -0.12,
                "yanchor": "top",
                "buttons": [
                    {
                        "label": "PLAY",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {
                                    "duration": 35,
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
            "displayModeBar": True
        }
    )

    initial_energy = (
        0.5 * mass1 * velocity1 ** 2
        +
        0.5 * mass2 * velocity2 ** 2
    )

    final_energy = (
        0.5 * mass1 * final_velocity1 ** 2
        +
        0.5 * mass2 * final_velocity2 ** 2
    )

    initial_momentum = (
        mass1 * velocity1
        -
        mass2 * velocity2
    )

    final_momentum = (
        mass1 * final_velocity1
        +
        mass2 * final_velocity2
    )

    st.markdown("### Results")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Object 1 Final Velocity",
            f"{final_velocity1:.2f} m/s"
        )

    with col2:
        st.metric(
            "Object 2 Final Velocity",
            f"{final_velocity2:.2f} m/s"
        )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Initial Kinetic Energy",
            f"{initial_energy:.2f} J"
        )

    with col2:
        st.metric(
            "Final Kinetic Energy",
            f"{final_energy:.2f} J"
        )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Initial Momentum",
            f"{initial_momentum:.2f} kg·m/s"
        )

    with col2:
        st.metric(
            "Final Momentum",
            f"{final_momentum:.2f} kg·m/s"
        )
