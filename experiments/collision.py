import json
import streamlit as st
import streamlit.components.v1 as components


def collision_experiment():

    defaults = {
        "collision_shape1": "Sphere",
        "collision_shape2": "Cube",
        "collision_mass1": 2.0,
        "collision_mass2": 2.0,
        "collision_velocity1": 5.0,
        "collision_velocity2": 3.0,
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

def run_collision(
    shape1,
    shape2,
    mass1,
    mass2,
    velocity1,
    velocity2,
    elasticity
):

    start_distance = 12.0

    # 두 물체의 중심 사이 최소 거리
    contact_distance = 3.5

    closing_speed = velocity1 + velocity2

    if closing_speed <= 0:

        st.warning(
            "The objects must move toward each other."
        )

        return

    collision_time = (
        start_distance - contact_distance
    ) / closing_speed

    collision_time = max(
        collision_time,
        0.1
    )

    after_collision_time = 3.5

    total_time = (
        collision_time +
        after_collision_time
    )

    # 프레임 수 증가
    points = 240

    times = [
        total_time * i / (points - 1)
        for i in range(points)
    ]
    
    u1 = velocity1
    u2 = -velocity2

    final_velocity1 = (
        (
            mass1 * u1
            +
            mass2 * u2
            -
            mass2 * elasticity * (u1 - u2)
        )
        /
        (mass1 + mass2)
    )

    final_velocity2 = (
        (
            mass1 * u1
            +
            mass2 * u2
            +
            mass1 * elasticity * (u1 - u2)
        )
        /
        (mass1 + mass2)
    )

    collision_x1 = -contact_distance / 2
    collision_x2 = contact_distance / 2

    positions1 = []
    positions2 = []

    for t in times:

        # Before collision
        if t < collision_time:

            x1 = (
                -start_distance / 2
                +
                velocity1 * t
            )

            x2 = (
                start_distance / 2
                -
                velocity2 * t
            )

        # After collision
        else:

            dt = t - collision_time

            x1 = (
                collision_x1
                +
                final_velocity1 * dt
            )

            x2 = (
                collision_x2
                +
                final_velocity2 * dt
            )

        positions1.append(x1)
        positions2.append(x2)

    all_positions = positions1 + positions2

    x_min = min(all_positions) - 3
    x_max = max(all_positions) + 3

    positions1_json = json.dumps(positions1)
    positions2_json = json.dumps(positions2)

    html = f"""
    <style>

    #collision-wrapper {{
        width: 100%;
        height: 720px;
        position: relative;
    }}

    #collision-container {{
        width: 100%;
        height: 620px;
    }}

    #play-button {{
        display: block;

        margin: 14px auto 0 auto;

        padding: 14px 42px;

        min-width: 150px;

        border-radius: 8px;

        border: 1px solid #888;

        background: #ffffff;

        color: #111111;

        font-size: 20px;

        font-weight: 600;

        cursor: pointer;

        box-shadow: 0 2px 6px rgba(0,0,0,0.25);

        transition:
            background 0.15s ease,
            transform 0.1s ease;
    }}

    #play-button:hover {{
        background: #eeeeee;
    }}

    #play-button:active {{
        transform: scale(0.97);
    }}

    #play-button:disabled {{
        opacity: 0.55;
        cursor: default;
    }}

    </style>


    <div id="collision-wrapper">

        <div id="collision-container"></div>

        <button id="play-button">
            PLAY
        </button>

    </div>


    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>

    <script>

    const positions1 = {positions1_json};

    const positions2 = {positions2_json};

    const shape1 = "{shape1}";

    const shape2 = "{shape2}";

    const container =
        document.getElementById(
            "collision-container"
        );

    const playButton =
        document.getElementById(
            "play-button"
        );


    function markerSymbol(shape) {{

        if (shape === "Sphere")
            return "circle";

        if (shape === "Cube")
            return "square";

        return "diamond";
    }}


    function createObject(
        position,
        color,
        shape,
        name
    ) {{

        return {{

            x: [position],

            y: [0],

            z: [0],

            mode: "markers",

            type: "scatter3d",

            marker: {{

                size: 20,

                color: color,

                symbol:
                    markerSymbol(shape),

                opacity: 1

            }},

            name: name,

            hovertemplate:

                name +

                "<br>X: %{{x:.2f}} m" +

                "<br>Y: %{{y:.2f}} m" +

                "<br>Z: %{{z:.2f}} m" +

                "<extra></extra>"
        }};
    }}


    const initialData = [

        createObject(
            positions1[0],
            "blue",
            shape1,
            "Object 1"
        ),

        createObject(
            positions2[0],
            "red",
            shape2,
            "Object 2"
        )

    ];


    const layout = {{

        title: "3D Collision Simulation",

        scene: {{

            dragmode: "orbit",

            xaxis: {{

                title: "X Position (m)",

                range: [
                    {x_min},
                    {x_max}
                ]

            }},

            yaxis: {{

                title: "Y Position (m)",

                range: [-5, 5]

            }},

            zaxis: {{

                title: "Z Position (m)",

                range: [-5, 5]

            }},

            aspectmode: "cube"

        }},

        height: 620,

        margin: {{

            l: 0,

            r: 0,

            t: 60,

            b: 10

        }},

        paper_bgcolor:
            "rgba(0,0,0,0)",

        plot_bgcolor:
            "rgba(0,0,0,0)"
    }};


    Plotly.newPlot(

        container,

        initialData,

        layout,

        {{

            responsive: true,

            scrollZoom: true,

            displaylogo: false

        }}

    ).then(() => {{

        setupAnimation();

    }});


    function setupAnimation() {{

        playButton.onclick = async function() {{

            if (playButton.disabled)
                return;


            const currentCamera =
                container.layout.scene.camera
                ?
                JSON.parse(
                    JSON.stringify(
                        container.layout.scene.camera
                    )
                )
                :
                null;


            playButton.disabled = true;


            const frames = [];


            for (
                let i = 0;
                i < positions1.length;
                i++
            ) {{

                const frame = {{

                    name: "frame" + i,

                    data: [

                        createObject(
                            positions1[i],
                            "blue",
                            shape1,
                            "Object 1"
                        ),

                        createObject(
                            positions2[i],
                            "red",
                            shape2,
                            "Object 2"
                        )

                    ]

                }};


                if (currentCamera) {{

                    frame.layout = {{

                        scene: {{

                            camera:
                                currentCamera

                        }}

                    }};

                }}


                frames.push(frame);

            }}


            await Plotly.deleteFrames(
                container
            );


            await Plotly.addFrames(
                container,
                frames
            );


            await Plotly.animate(

                container,

                frames.map(
                    frame => frame.name
                ),

                {{

                    transition: {{

                        duration: 0

                    }},

                    frame: {{

                        duration: 20,

                        redraw: true

                    }},

                    mode: "immediate",

                    fromcurrent: false

                }}

            );


            if (currentCamera) {{

                await Plotly.relayout(

                    container,

                    {{

                        "scene.camera":
                            currentCamera

                    }}

                );

            }}


            playButton.disabled = false;

        }};

    }}

    </script>
    """

    components.html(
        html,
        height=750,
        scrolling=False
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
