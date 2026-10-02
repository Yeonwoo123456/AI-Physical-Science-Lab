import json
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from app_modules import CollisionNaturalLanguageParser


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

    st.markdown("### AI Experiment Assistant")

    st.markdown("Describe the collision experiment in natural language. Only values explicitly mentioned will be changed.")

    ai_input = st.text_area(
        "Collision description",
        placeholder="Example: Object A is 4 kg and moves at 8 m/s. Object B is 1 kg and moves at 3 m/s.",
        height=90,
        key="collision_ai_input"
    )

    if st.button(
        "Run AI Analysis",
        key="collision_ai_button",
        type="primary",
        use_container_width=True
    ):
        if not ai_input.strip():
            st.warning("Describe a collision experiment first.")
        else:
            with st.spinner("AI is analyzing the collision experiment..."):
                result = CollisionNaturalLanguageParser.parse(ai_input)

            parameters = result.get("parameters", {})
            updated = False

            mapping = {
                "mass1": ("collision_mass1", 0.1, 1000.0),
                "mass2": ("collision_mass2", 0.1, 1000.0),
                "velocity1": ("collision_velocity1", 0.0, 100.0),
                "velocity2": ("collision_velocity2", 0.0, 100.0),
                "elasticity": ("collision_elasticity", 0.0, 1.0)
            }

            for parameter, (session_key, minimum, maximum) in mapping.items():
                value = parameters.get(parameter)

                if value is None:
                    continue

                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue

                if minimum <= value <= maximum:
                    st.session_state[session_key] = value
                    updated = True

            if result.get("needs_clarification") and not updated:
                st.warning(
                    result.get(
                        "clarification_message",
                        "The AI could not find valid collision values."
                    )
                )
            elif updated:
                st.success("AI analysis completed. The detected values have been applied.")
            else:
                st.warning("No valid collision values were found. The current values were kept.")

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

        st.session_state.pop("collision_ai_input", None)

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

    wall_left = -9.0
    wall_right = 9.0

    center_left = wall_left + radius
    center_right = wall_right - radius

    start1 = -6.0
    start2 = 6.0

    v1 = velocity1
    v2 = -velocity2

    collision_result_v1 = None
    collision_result_v2 = None

    dt = 1 / 240
    simulation_time = 6.0

    positions1 = []
    positions2 = []
    times = []

    velocity1_history = []
    velocity2_history = []
    energy1_history = []
    energy2_history = []

    x1 = start1
    x2 = start2

    collision_cooldown = 0.0

    steps = int(simulation_time / dt)

    for step in range(steps + 1):

        t = step * dt

        positions1.append(x1)
        positions2.append(x2)
        times.append(t)

        velocity1_history.append(v1)
        velocity2_history.append(v2)

        energy1_history.append(0.5 * mass1 * v1 ** 2)
        energy2_history.append(0.5 * mass2 * v2 ** 2)

        next_x1 = x1 + v1 * dt
        next_x2 = x2 + v2 * dt

        if next_x1 <= center_left:
            next_x1 = center_left
            v1 = 0.0

        elif next_x1 >= center_right:
            next_x1 = center_right
            v1 = 0.0

        if next_x2 <= center_left:
            next_x2 = center_left
            v2 = 0.0

        elif next_x2 >= center_right:
            next_x2 = center_right
            v2 = 0.0

        x1 = next_x1
        x2 = next_x2

        collision_cooldown = max(
            0.0,
            collision_cooldown - dt
        )

        distance = x2 - x1

        if (
            distance <= radius * 2
            and collision_cooldown <= 0
            and abs(v1 - v2) > 0.001
        ):

            center = (x1 + x2) / 2

            x1 = center - radius
            x2 = center + radius

            relative_velocity = v1 - v2

            if relative_velocity > 0:

                new_v1 = (
                    (
                        mass1 - elasticity * mass2
                    ) * v1
                    + (
                        1 + elasticity
                    ) * mass2 * v2
                ) / (mass1 + mass2)

                new_v2 = (
                    (
                        1 + elasticity
                    ) * mass1 * v1
                    + (
                        mass2 - elasticity * mass1
                    ) * v2
                ) / (mass1 + mass2)

                v1 = new_v1
                v2 = new_v2

                if collision_result_v1 is None:
                    collision_result_v1 = v1
                    collision_result_v2 = v2

            collision_cooldown = 0.08

    if collision_result_v1 is None:
        collision_result_v1 = v1
        collision_result_v2 = v2

    p1 = json.dumps(positions1)
    p2 = json.dumps(positions2)
    pt = json.dumps(times)

    html = f"""
    <style>

        html,
        body {{
            width: 100%;
            height: 540px;
            margin: 0;
            padding: 0;
            background: #111827;
            overflow: hidden;
        }}

        #display {{
            width: 75%;
            height: 500px;
            margin: 0 auto;
            padding: 8px;
            box-sizing: border-box;
            border: 1px solid #4b5563;
            border-radius: 10px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            background: #111827;
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
        const pt = {pt};

        const s1 = "{shape1}";
        const s2 = "{shape2}";
        const SPEED = {speed};

        const plot = document.getElementById("plot");
        const play = document.getElementById("play");


        function sphere(x, color, name) {{

            const radius = 1.25;
            const segments = 32;
            const rings = 20;

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
                        radius *
                        Math.cos(phi)
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

                color:
                    color === "blue"
                        ? "#4DA3FF"
                        : "#FF5C5C",

                opacity: 1,
                flatshading: false,

                lighting: {{
                    ambient: 0.4,
                    diffuse: 0.8,
                    specular: 0.5,
                    roughness: 0.3
                }},

                lightposition: {{
                    x: 100,
                    y: 100,
                    z: 200
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


        function createObject(x, color, shape, name) {{

            return shape === "Sphere"
                ? sphere(x, color, name)
                : cube(x, color, name);
        }}


        function updateSphere(objectIndex, x) {{

            const radius = 1.25;
            const segments = 32;
            const rings = 20;

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


        function updateCube(objectIndex, x) {{

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


        function updateObject(objectIndex, x, shape) {{

            if (shape === "Sphere")
                updateSphere(objectIndex, x);
            else
                updateCube(objectIndex, x);
        }}


        function interpolate(values, times, time) {{

            if (time <= times[0])
                return values[0];

            if (time >= times[times.length - 1])
                return values[values.length - 1];

            let low = 0;
            let high = times.length - 1;

            while (low < high) {{

                const mid =
                    Math.floor((low + high) / 2);

                if (times[mid] < time)
                    low = mid + 1;
                else
                    high = mid;
            }}

            const i = Math.max(0, low - 1);

            const ratio =
                (time - times[i]) /
                (times[i + 1] - times[i]);

            return (
                values[i] +
                (values[i + 1] - values[i]) * ratio
            );
        }}


        const data = [
            createObject(
                p1[0],
                "blue",
                s1,
                "Object A"
            ),
            createObject(
                p2[0],
                "red",
                s2,
                "Object B"
            )
        ];


        const layout = {{

            title: "3D Collision Simulation",

            autosize: true,

            scene: {{

                bgcolor: "#111827",
                dragmode: "orbit",

                camera: {{
                    projection: {{
                        type: "orthographic"
                    }}
                }},

                xaxis: {{
                    title: "X Position (m)",
                    range: [-9, 9],
                    autorange: false,
                    color: "#D1D5DB",
                    gridcolor: "#374151",
                    zerolinecolor: "#4B5563"
                }},

                yaxis: {{
                    title: "Y Position (m)",
                    range: [-5, 5],
                    autorange: false,
                    color: "#D1D5DB",
                    gridcolor: "#374151",
                    zerolinecolor: "#4B5563"
                }},

                zaxis: {{
                    title: "Z Position (m)",
                    range: [-5, 5],
                    autorange: false,
                    color: "#D1D5DB",
                    gridcolor: "#374151",
                    zerolinecolor: "#4B5563"
                }},

                aspectmode: "manual",

                aspectratio: {{
                    x: 1.6,
                    y: 1,
                    z: 1
                }}
            }},

            height: 420,

            margin: {{
                l: 0,
                r: 0,
                t: 50,
                b: 0
            }},

            paper_bgcolor: "#111827",
            plot_bgcolor: "#111827",
            font: {{color: "#E5E7EB"}}
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

            if (play.disabled)
                return;

            play.disabled = true;

            const camera = JSON.parse(
                JSON.stringify(
                    plot.layout.scene.camera
                )
            );

            const totalTime =
                pt[pt.length - 1];

            const duration =
                totalTime * 1000 / SPEED;

            const startTime =
                performance.now();


            function animate(now) {{

                const elapsed =
                    now - startTime;

                const simulationTime =
                    Math.min(
                        elapsed / duration *
                        totalTime,
                        totalTime
                    );

                updateObject(
                    0,
                    interpolate(
                        p1,
                        pt,
                        simulationTime
                    ),
                    s1
                );

                updateObject(
                    1,
                    interpolate(
                        p2,
                        pt,
                        simulationTime
                    ),
                    s2
                );

                if (simulationTime < totalTime) {{

                    requestAnimationFrame(
                        animate
                    );

                }} else {{

                    Plotly.relayout(
                        plot,
                        {{
                            "scene.camera": camera
                        }}
                    );

                    play.disabled = false;
                }}
            }}

            requestAnimationFrame(animate);
        }};

    </script>
    """

    components.html(
        html,
        height=540,
        scrolling=False
    )

    initial_velocity1 = velocity1
    initial_velocity2 = -velocity2

    initial_momentum1 = mass1 * initial_velocity1
    initial_momentum2 = mass2 * initial_velocity2

    final_momentum1 = mass1 * collision_result_v1
    final_momentum2 = mass2 * collision_result_v2

    initial_energy1 = (
        0.5 * mass1 * initial_velocity1 ** 2
    )

    initial_energy2 = (
        0.5 * mass2 * initial_velocity2 ** 2
    )

    final_energy1 = (
        0.5 * mass1 * collision_result_v1 ** 2
    )

    final_energy2 = (
        0.5 * mass2 * collision_result_v2 ** 2
    )

    st.markdown("### Velocity")

    velocity_fig = go.Figure()

    velocity_fig.add_trace(
        go.Scatter(
            x=times,
            y=velocity1_history,
            mode="lines",
            name="Object A",
            line=dict(width=3)
        )
    )

    velocity_fig.add_trace(
        go.Scatter(
            x=times,
            y=velocity2_history,
            mode="lines",
            name="Object B",
            line=dict(width=3)
        )
    )

    velocity_fig.update_layout(
        title="Velocity vs Time",
        xaxis_title="Time (s)",
        yaxis_title="Velocity (m/s)",
        template="plotly_dark",
        height=420,
        margin=dict(l=60, r=30, t=60, b=60),
        hovermode="x unified"
    )

    st.plotly_chart(
        velocity_fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )

    st.markdown("### Energy")

    energy_fig = go.Figure()

    energy_fig.add_trace(
        go.Scatter(
            x=times,
            y=energy1_history,
            mode="lines",
            name="Object A",
            line=dict(width=3)
        )
    )

    energy_fig.add_trace(
        go.Scatter(
            x=times,
            y=energy2_history,
            mode="lines",
            name="Object B",
            line=dict(width=3)
        )
    )

    total_energy = [
        a + b
        for a, b in zip(
            energy1_history,
            energy2_history
        )
    ]

    energy_fig.add_trace(
        go.Scatter(
            x=times,
            y=total_energy,
            mode="lines",
            name="Total Energy",
            line=dict(width=3, dash="dash")
        )
    )

    energy_fig.update_layout(
        title="Kinetic Energy vs Time",
        xaxis_title="Time (s)",
        yaxis_title="Energy (J)",
        template="plotly_dark",
        height=420,
        margin=dict(l=60, r=30, t=60, b=60),
        hovermode="x unified"
    )

    st.plotly_chart(
        energy_fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )
