import base64
import math
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

from app_modules import NaturalLanguageParser, PhysicsValidator


def projectile_experiment():

    if "projectile_velocity" not in st.session_state:
        st.session_state.projectile_velocity = 20.0

    if "projectile_angle" not in st.session_state:
        st.session_state.projectile_angle = 0.0

    if "projectile_height" not in st.session_state:
        st.session_state.projectile_height = 0.0

    if "projectile_gravity" not in st.session_state:
        st.session_state.projectile_gravity = 9.81

    if "projectile_mass" not in st.session_state:
        st.session_state.projectile_mass = 1.0

    st.markdown(
        """
        <div class="selection-header">
            <div class="section-title">Projectile Motion</div>
            <div class="selection-description">
                Describe your experiment using natural language or adjust the values manually.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### AI Experiment Assistant")

    user_input = st.text_area(
        "Describe your experiment",
        placeholder=(
            "Example: Throw a 2 kg ball at 25 m/s "
            "from a height of 5 meters at an angle of 40 degrees."
        ),
        height=100,
        key="projectile_ai_input"
    )

    if st.button(
        "Analyze with AI",
        use_container_width=True
    ):

        if not user_input.strip():

            st.warning(
                "Please describe your experiment first."
            )

        else:

            with st.spinner("Analyzing your experiment..."):

                result = NaturalLanguageParser.parse(
                    user_input
                )

            if result.get(
                "needs_clarification",
                False
            ):

                st.warning(
                    result.get(
                        "clarification_message",
                        "More information is needed."
                    )
                )

            else:

                validation = PhysicsValidator.validate(
                    result
                )

                if not validation.is_valid:

                    for error in validation.errors:
                        st.error(error)

                else:

                    params = validation.validated_params

                    st.session_state.projectile_velocity = float(
                        params.get(
                            "initial_velocity",
                            20.0
                        )
                    )

                    st.session_state.projectile_angle = float(
                        params.get(
                            "launch_angle",
                            0.0
                        )
                    )

                    st.session_state.projectile_height = float(
                        params.get(
                            "height",
                            0.0
                        )
                    )

                    st.session_state.projectile_gravity = float(
                        params.get(
                            "gravity",
                            9.81
                        )
                    )

                    st.session_state.projectile_mass = float(
                        params.get(
                            "mass",
                            1.0
                        )
                    )

                    st.success(
                        "The AI converted your description into physical parameters."
                    )

    st.markdown("### Parameters")

    col1, col2, col3 = st.columns(3)

    with col1:

        velocity = st.number_input(
            "Initial Speed (m/s)",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key="projectile_velocity"
        )

    with col2:

        angle = st.number_input(
            "Launch Angle (°)",
            min_value=0.0,
            max_value=180.0,
            step=1.0,
            key="projectile_angle"
        )

    with col3:

        height = st.number_input(
            "Initial Height (m)",
            min_value=0.0,
            max_value=500.0,
            step=1.0,
            key="projectile_height"
        )

    col1, col2 = st.columns(2)

    with col1:

        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.01,
            max_value=30.0,
            step=0.1,
            key="projectile_gravity"
        )

    with col2:

        mass = st.number_input(
            "Mass (kg)",
            min_value=0.01,
            max_value=1000.0,
            step=0.1,
            key="projectile_mass"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "Run Experiment",
        type="primary",
        use_container_width=True
    ):

        if angle > 90:

            st.warning(
                "Launch angle cannot be greater than 90°."
            )

        else:

            run_projectile_simulation(
                velocity,
                angle,
                height,
                gravity,
                mass
            )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Back to Experiments"):

        for key in [
            "projectile_velocity",
            "projectile_angle",
            "projectile_height",
            "projectile_gravity",
            "projectile_mass",
            "projectile_ai_input"
        ]:
            if key in st.session_state:
                del st.session_state[key]

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

    max_height = (
        height +
        vy ** 2 /
        (2 * gravity)
    )

    time_to_max = vy / gravity

    max_height_x = vx * time_to_max

    horizontal_range = vx * total_time

    point_count = 100

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
            0.5 * gravity * t ** 2
        )

        x_values.append(x)

        y_values.append(
            max(0.0, y)
        )

    x_max = max(
        horizontal_range * 1.1,
        10
    )

    y_max = max(
        max_height * 1.15,
        10
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[],
            y=[],
            mode="lines",
            line=dict(
                width=4
            ),
            name="Trajectory",
            hovertemplate=(
                "Height: %{y:.2f} m"
                "<br>"
                "Horizontal Distance: %{x:.2f} m"
                "<extra></extra>"
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[],
            y=[],
            mode="markers",
            marker=dict(
                size=15,
                symbol="circle"
            ),
            name="Maximum Height",
            hovertemplate=(
                "Maximum Height: %{y:.2f} m"
                "<br>"
                "Horizontal Distance: %{x:.2f} m"
                "<extra></extra>"
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[x_values[0]],
            y=[y_values[0]],
            mode="markers",
            marker=dict(
                size=20
            ),
            name="Projectile",
            hovertemplate=(
                "Height: %{y:.2f} m"
                "<br>"
                "Horizontal Distance: %{x:.2f} m"
                "<extra></extra>"
            )
        )
    )

    frames = []
    apex_index = max(range(point_count), key=lambda i: y_values[i])

    for i in range(point_count):

        frames.append(
            go.Frame(
                data=[
                    go.Scatter(
                        x=x_values[:i + 1],
                        y=y_values[:i + 1],
                        mode="lines",
                        line=dict(
                            width=4
                        ),
                        hovertemplate=(
                            "Height: %{y:.2f} m"
                            "<br>"
                            "Horizontal Distance: %{x:.2f} m"
                            "<extra></extra>"
                        )
                    ),

                    go.Scatter(
                        x=([max_height_x] if i >= apex_index else []),
                        y=([max_height] if i >= apex_index else []),
                        mode="markers",
                        marker=dict(
                            size=15,
                            symbol="circle"
                        ),
                        hovertemplate=(
                            "Maximum Height: %{y:.2f} m"
                            "<br>"
                            "Horizontal Distance: %{x:.2f} m"
                            "<extra></extra>"
                        )
                    ),

                    go.Scatter(
                        x=[x_values[i]],
                        y=[y_values[i]],
                        mode="markers",
                        marker=dict(
                            size=20
                        ),
                        hovertemplate=(
                            "Height: %{y:.2f} m"
                            "<br>"
                            "Horizontal Distance: %{x:.2f} m"
                            "<extra></extra>"
                        )
                    )
                ],
                name=str(i)
            )
        )

    fig.frames = frames

    fig.update_layout(

        title="Projectile Motion",

        xaxis=dict(
            title="Horizontal Distance (m)",
            range=[
                0,
                x_max
            ]
        ),

        yaxis=dict(
            title="Height (m)",
            range=[
                0,
                y_max
            ]
        ),

        template="plotly_dark",

        height=600,

        showlegend=True,

        margin=dict(
            l=70,
            r=40,
            t=80,
            b=40
        )
    )

    st.markdown("### Simulation")

    def load_audio_data(names):
        base = Path(__file__).parent / "assets"

        for name in names:
            path = base / name
            if path.exists():
                return base64.b64encode(
                    path.read_bytes()
                ).decode()

        return ""

    whoosh_data = load_audio_data([
        "projectile_whoosh.mp3",
        "dragon-studio-simple-whoosh-382724(1).mp3",
        "dragon-studio-simple-whoosh-382724.mp3",
    ])

    bounce_data = load_audio_data([
        "projectile_bounce.mp3",
        "freesound_community-plastic-ball-bounce-14790.mp3",
    ])

    # Plotly의 기본 PLAY 버튼 대신 일반 HTML 버튼을 사용합니다.
    # 일반 버튼의 click 이벤트에서 audio.play()를 직접 호출하면
    # 브라우저의 autoplay 정책에 막힐 가능성이 훨씬 낮습니다.
    chart_html = fig.to_html(
        include_plotlyjs=True,
        full_html=False,
        auto_play=False,
        config={
            "displayModeBar": False
        }
    )

    audio_html = f"""
    <style>
        #projectile-simulation-wrapper {{
            width: 100%;
            box-sizing: border-box;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 8px 8px 14px 8px;
        }}

        #projectile-play-button {{
            display: block;
            width: 130px;
            height: 42px;
            margin: 8px auto 0 auto;
            border: 1px solid #777;
            border-radius: 8px;
            background: white;
            color: #111;
            font-size: 17px;
            font-weight: 600;
            cursor: pointer;
        }}

        #projectile-play-button:hover {{
            background: #eeeeee;
        }}

        #projectile-play-button:active {{
            transform: translateY(1px);
        }}
    </style>

    <div id="projectile-simulation-wrapper">
        {chart_html}
        <button id="projectile-play-button" type="button">▶ PLAY</button>
    </div>

    <audio
        id="projectile-whoosh"
        preload="auto"
        src="data:audio/mpeg;base64,{whoosh_data}">
    </audio>

    <audio
        id="projectile-bounce"
        preload="auto"
        src="data:audio/mpeg;base64,{bounce_data}">
    </audio>

    <script>
    (function() {{
        const playButton = document.getElementById(
            'projectile-play-button'
        );
        const whoosh = document.getElementById(
            'projectile-whoosh'
        );
        const bounce = document.getElementById(
            'projectile-bounce'
        );
        const plot = document.querySelector(
            '#projectile-simulation-wrapper .plotly-graph-div'
        );

        const FRAME_DURATION = 30;
        const FRAME_COUNT = {point_count};
        const ANIMATION_DURATION =
            Math.max(0, FRAME_COUNT - 1) * FRAME_DURATION;

        let bounceTimer = null;

        function stopSound(audio) {{
            if (!audio) return;

            audio.pause();

            try {{
                audio.currentTime = 0;
            }} catch (e) {{}}
        }}

        function playWhooshForOneSecond() {{
            if (!whoosh || !whoosh.getAttribute('src')) return;

            stopSound(whoosh);
            whoosh.loop = true;

            const promise = whoosh.play();

            if (promise && promise.catch) {{
                promise.catch(function(error) {{
                    console.log('Whoosh playback failed:', error);
                }});
            }}

            setTimeout(function() {{
                whoosh.loop = false;
                stopSound(whoosh);
            }}, 1000);
        }}

        function playBounce() {{
            if (!bounce || !bounce.getAttribute('src')) return;

            stopSound(bounce);

            const promise = bounce.play();

            if (promise && promise.catch) {{
                promise.catch(function(error) {{
                    console.log('Bounce playback failed:', error);
                }});
            }}
        }}

        if (playButton) {{
            playButton.addEventListener('click', function() {{

                if (!plot || !window.Plotly) {{
                    return;
                }}

                if (bounceTimer) {{
                    clearTimeout(bounceTimer);
                    bounceTimer = null;
                }}

                stopSound(bounce);
                playWhooshForOneSecond();

                Plotly.animate(
                    plot,
                    null,
                    {{
                        frame: {{
                            duration: FRAME_DURATION,
                            redraw: true
                        }},
                        transition: {{
                            duration: 0
                        }},
                        fromcurrent: false,
                        mode: 'immediate'
                    }}
                );

                bounceTimer = setTimeout(function() {{
                    playBounce();
                }}, ANIMATION_DURATION);
            }});
        }}
    }})();
    </script>
    """

    components.html(
        audio_html,
        height=670,
        scrolling=False
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
