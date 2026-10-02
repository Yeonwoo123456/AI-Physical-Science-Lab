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
        "collision_elasticity": 1.0,
        "collision_speed": 1.0
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
        shape1 = st.selectbox(
            "Shape",
            ["Sphere", "Cube"],
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
        shape2 = st.selectbox(
            "Shape",
            ["Sphere", "Cube"],
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

    speed = st.select_slider(
        "Animation Speed",
        options=[0.25, 0.5, 1.0, 1.5, 2.0],
        value=1.0,
        format_func=lambda x: f"{x}x",
        key="collision_speed"
    )

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
            elasticity,
            speed
        )

    if st.button("Back to Experiments"):
        for key in defaults:
            st.session_state.pop(key, None)

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
    elasticity,
    speed
):

    radius = 1.25
    start_distance = 12.0
    collision_distance = radius * 2
    start1 = -start_distance / 2
    start2 = start_distance / 2
    collision1 = -collision_distance / 2
    collision2 = collision_distance / 2
    points = 240

    closing_speed = velocity1 + velocity2

    if closing_speed <= 0:
        st.warning("The objects must move toward each other.")
        return

    collision_time = max(
        (start_distance - collision_distance) / closing_speed,
        0.01
    )

    u1 = velocity1
    u2 = -velocity2

    v1 = (
        mass1 * u1
        + mass2 * u2
        - mass2 * elasticity * (u1 - u2)
    ) / (mass1 + mass2)

    v2 = (
        mass1 * u1
        + mass2 * u2
        + mass1 * elasticity * (u1 - u2)
    ) / (mass1 + mass2)

    return_distance = (
        start_distance - collision_distance
    ) / 2

    return_speed = max(
        velocity1,
        velocity2,
        1.0
    )

    return_time = max(
        return_distance / return_speed,
        0.8
    )

    total_time = collision_time + return_time

    times = [
        total_time * i / (points - 1)
        for i in range(points)
    ]

    times.append(collision_time)
    times = sorted(set(times))

    positions1 = []
    positions2 = []

    for t in times:

        if t < collision_time:

            pos1 = start1 + velocity1 * t
            pos2 = start2 - velocity2 * t

        else:

            progress = min(
                (t - collision_time) / return_time,
                1.0
            )

            smooth = (
                progress
                * progress
                * (3 - 2 * progress)
            )

            pos1 = collision1 + (
                start1 - collision1
            ) * smooth

            pos2 = collision2 + (
                start2 - collision2
            ) * smooth

        positions1.append(
            max(start1, min(pos1, collision1))
        )

        positions2.append(
            min(start2, max(pos2, collision2))
        )

    xmin = start1 - 3
    xmax = start2 + 3

    p1 = json.dumps(positions1)
    p2 = json.dumps(positions2)

    html = f"""
    <style>

        html,
        body {{
            width: 100%;
            height: 540px;
            margin: 0;
            padding: 0;
            background: transparent;
            overflow: hidden;
        }}

        #display {{
            width: 75%;
            height: 500px;
            margin: 0 auto;
            padding: 8px;
            box-sizing: border-box;
            border: 1px solid #6b7280;
            border-radius: 10px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        #plot {{
            width: 100%;
            height: 430px;
            flex: 0 0 430px;
        }}

        #play {{
            display: block;
            width: 120px;
            height: 44px;
            margin: 10px auto 0;
            border: 1px solid #888;
            border-radius: 8px;
            background: white;
            color: #111;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            flex-shrink: 0;
        }}

        #play:hover {{
            background: #f2f2f2;
        }}

        #play:disabled {{
            opacity: 0.5;
            cursor: default;
        }}

    </style>

    <div id="display">
        <div id="plot"></div>
        <button id="play">PLAY</button>
    </div>

    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>

    <script>

        const p1 = {p1};
        const p2 = {p2};
        const s1 = "{shape1}";
        const s2 = "{shape2}";
        const SPEED = {speed};

        const plot = document.getElementById("plot");
        const play = document.getElementById("play");


        function sphere(x, color, name) {{

            const radius = 1.25;
            const segments = 16;
            const rings = 10;

            const X = [];
            const Y = [];
            const Z = [];
            const I = [];
            const J = [];
            const K = [];

            for (let r = 0; r <= rings; r++) {{

                const phi = Math.PI * r / rings;

                for (let s = 0; s < segments; s++) {{

                    const theta =
                        2 * Math.PI * s / segments;

                    X.push(
                        x +
                        radius *
                        Math.sin(phi) *
                        Math.cos(theta)
                    );

                    Y.push(
                        radius *
                        Math.sin(phi) *
                        Math.sin(theta)
                    );

                    Z.push(
                        radius * Math.cos(phi)
                    );
                }}
            }}

            for (let r = 0; r < rings; r++) {{

                for (let s = 0; s < segments; s++) {{

                    const next =
                        (s + 1) % segments;

                    const a =
                        r * segments + s;

                    const b =
                        r * segments + next;

                    const c =
                        (r + 1) * segments + next;

                    const d =
                        (r + 1) * segments + s;

                    I.push(a);
                    J.push(b);
                    K.push(c);

                    I.push(a);
                    J.push(c);
                    K.push(d);
                }}
            }}

            return {{
                type: "mesh3d",
                x: X,
                y: Y,
                z: Z,
                i: I,
                j: J,
                k: K,
                color: color,
                opacity: 1,
                flatshading: false,
                lighting: {{
                    ambient: 0.35,
                    diffuse: 0.8,
                    specular: 0.4,
                    roughness: 0.4
                }},
                name: name
            }};
        }}


        function cube(x, color, name) {{

            const s = 1.25;

            return {{
                type: "mesh3d",

                x: [
                    x-s, x+s, x+s, x-s,
                    x-s, x+s, x+s, x-s
                ],

                y: [
                    -s, -s, s, s,
                    -s, -s, s, s
                ],

                z: [
                    -s, -s, -s, -s,
                    s, s, s, s
                ],

                i: [
                    0, 0,
                    4, 4,
                    0, 0,
                    1, 1,
                    2, 2,
                    3, 3
                ],

                j: [
                    1, 2,
                    5, 6,
                    1, 5,
                    2, 6,
                    3, 7,
                    0, 4
                ],

                k: [
                    2, 3,
                    6, 7,
                    5, 4,
                    6, 5,
                    7, 6,
                    4, 7
                ],

                color: color,
                opacity: 1,
                flatshading: true,

                lighting: {{
                    ambient: 0.3,
                    diffuse: 0.8,
                    specular: 0.5,
                    roughness: 0.3
                }},

                name: name
            }};
        }}


        function createObject(
            x,
            color,
            shape,
            name
        ) {{

            if (shape === "Sphere") {{
                return sphere(x, color, name);
            }}

            return cube(x, color, name);
        }}


        function updateSphere(
            objectIndex,
            x
        ) {{

            const radius = 1.25;
            const segments = 16;
            const rings = 10;
            const X = [];

            for (let r = 0; r <= rings; r++) {{

                const phi = Math.PI * r / rings;

                for (let s = 0; s < segments; s++) {{

                    const theta =
                        2 * Math.PI * s / segments;

                    X.push(
                        x +
                        radius *
                        Math.sin(phi) *
                        Math.cos(theta)
                    );
                }}
            }}

            Plotly.restyle(
                plot,
                {{x: [X]}},
                [objectIndex]
            );
        }}


        function updateCube(
            objectIndex,
            x
        ) {{

            const s = 1.25;

            const X = [
                x-s, x+s, x+s, x-s,
                x-s, x+s, x+s, x-s
            ];

            Plotly.restyle(
                plot,
                {{x: [X]}},
                [objectIndex]
            );
        }}


        function updateObject(
            objectIndex,
            x,
            shape
        ) {{

            if (shape === "Sphere") {{
                updateSphere(objectIndex, x);
            }} else {{
                updateCube(objectIndex, x);
            }}
        }}


        const data = [
            createObject(
                p1[0],
                "blue",
                s1,
                "Object 1"
            ),
            createObject(
                p2[0],
                "red",
                s2,
                "Object 2"
            )
        ];


        const layout = {{

            title: "3D Collision Simulation",

            autosize: true,

            scene: {{

                dragmode: "orbit",

                camera: {{
                    projection: {{
                        type: "orthographic"
                    }}
                }},

                xaxis: {{
                    title: "X Position (m)",
                    range: [{xmin}, {xmax}]
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

            height: 420,

            margin: {{
                l: 0,
                r: 0,
                t: 50,
                b: 0
            }},

            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)"
        }};


        Plotly.newPlot(
            plot,
            data,
            layout,
            {{
                responsive: false,
                scrollZoom: true,
                displaylogo: false
            }}
        );


        play.onclick = function() {{

            if (play.disabled) {{
                return;
            }}

            play.disabled = true;

            const camera = JSON.parse(
                JSON.stringify(
                    plot.layout.scene.camera
                )
            );

            let i = 0;


            function nextFrame() {{

                if (i >= p1.length) {{

                    updateObject(
                        0,
                        p1[p1.length - 1],
                        s1
                    );

                    updateObject(
                        1,
                        p2[p2.length - 1],
                        s2
                    );

                    if (camera) {{

                        Plotly.relayout(
                            plot,
                            {{
                                "scene.camera": camera
                            }}
                        );
                    }}

                    play.disabled = false;
                    return;
                }}


                updateObject(
                    0,
                    p1[i],
                    s1
                );

                updateObject(
                    1,
                    p2[i],
                    s2
                );


                i++;

                setTimeout(
                    nextFrame,
                    20 / SPEED
                );
            }}


            nextFrame();
        }};

    </script>
    """

    components.html(
        html,
        height=540,
        scrolling=False
    )


    initial_energy = (
        0.5 * mass1 * velocity1 ** 2
        + 0.5 * mass2 * velocity2 ** 2
    )

    final_energy = (
        0.5 * mass1 * v1 ** 2
        + 0.5 * mass2 * v2 ** 2
    )

    st.markdown("### Results")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Object 1 Final Velocity",
            f"{v1:.2f} m/s"
        )

        st.metric(
            "Initial Kinetic Energy",
            f"{initial_energy:.2f} J"
        )

    with col2:
        st.metric(
            "Object 2 Final Velocity",
            f"{v2:.2f} m/s"
        )

        st.metric(
            "Final Kinetic Energy",
            f"{final_energy:.2f} J"
        )
