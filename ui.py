import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from pathlib import Path

from app_modules import (
    NaturalLanguageParser,
    PhysicsValidator,
    PhysicsEngine
)


def load_css():
    css_path = Path(__file__).parent / "style.css"

    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


def init_state():
    defaults = {
        "page": "home",
        "experiment": None,
        "result": None,
        "validation": None
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_image_base64(path):
    image_path = Path(__file__).parent / path

    if not image_path.exists():
        return None

    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def card(title, description):
    st.markdown(
        f"""
        <div class="experiment-card">
            <div class="experiment-title">{title}</div>
            <div class="experiment-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def run_engine(validation):
    engine = PhysicsEngine(
        dt=0.02,
        solver="rk4"
    )

    return engine.simulate(
        validation,
        total_time=8.0
    )

def home_page():
    st.markdown(
        '<div class="home-title">What happens if…?</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="home-subtitle">Turn your imagination into a physics experiment.</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="home-description">Imagine a situation, describe it, and explore what happens through physics simulation.</div>',
        unsafe_allow_html=True
    )

    _, col, _ = st.columns([1, 2, 1])

    with col:
        if st.button(
            "Start Exploring",
            type="primary",
            use_container_width=True
        ):
            st.session_state.page = "select"
            st.rerun()

def selection_page():
    st.markdown(
        '<div class="selection-header">'
        '<div class="section-title">Choose Your Experiment</div>'
        '<div class="selection-description">'
        'Explore different physical phenomena through simulation.'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    experiments = [
        (
            "projectile",
            "Projectile Motion",
            "Kinematics",
            "Speed · Angle · Gravity",
            "projectile-card",
            "assets/projectile.png"
        ),
        (
            "collision",
            "Collision",
            "Momentum & Energy",
            "Mass · Speed · Elasticity",
            "collision-card",
            "assets/collision.png"
        ),
        (
            "pendulum",
            "Pendulum",
            "Periodic Motion",
            "Length · Gravity · Angle",
            "pendulum-card",
            "assets/pendulum.png"
        ),
        (
            "spring",
            "Spring",
            "Hooke's Law",
            "Mass · k · Displacement",
            "spring-card",
            "assets/spring.png"
        ),
        (
            "friction",
            "Friction",
            "Friction Force",
            "μ · Mass · Gravity",
            "friction-card",
            "assets/friction.png"
        ),
        (
            "orbit",
            "Gravity & Orbit",
            "Gravity",
            "Mass · Distance · Velocity",
            "orbit-card",
            "assets/orbit.png"
        )
    ]

    for row in range(0, 6, 3):
        cols = st.columns(3)

        for col, experiment in zip(
            cols,
            experiments[row:row + 3]
        ):
            (
                key,
                title,
                concept,
                parameters,
                css_class,
                image
            ) = experiment

            image_data = get_image_base64(image)

            if image_data:
                image_html = (
                    f'<img '
                    f'class="physics-illustration" '
                    f'src="data:image/png;base64,{image_data}" '
                    f'alt="">'
                )
            else:
                image_html = ""

            card_html = (
                f'<a '
                f'href="?experiment={key}" '
                f'class="physics-card {css_class}">'
                f'{image_html}'
                f'<div class="physics-overlay">'
                f'<div class="physics-info-box">'
                f'<div class="physics-title {key}-title">'
                f'{title}'
                f'</div>'
                f'<div class="physics-concept">'
                f'{concept}'
                f'</div>'
                f'<div class="physics-parameters">'
                f'{parameters}'
                f'</div>'
                f'</div>'
                f'</div>'
                f'</a>'
            )

            with col:
                st.markdown(
                    card_html,
                    unsafe_allow_html=True
                )

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.query_params.clear()
        st.rerun()

def ai_experiment():
    st.markdown(
        '<div class="section-title">AI Physics Experiment</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="muted">Describe the situation you want to simulate.</div>',
        unsafe_allow_html=True
    )

    prompt = st.text_area(
        "What happens if...",
        placeholder=(
            "Example: A ball is thrown from a 20-meter "
            "building at 15 m/s."
        ),
        height=120
    )

    if st.button(
        "Run Experiment",
        type="primary",
        use_container_width=True
    ):
        if not prompt.strip():
            st.warning("Describe a physics situation first.")
            return

        with st.spinner("AI is analyzing your experiment..."):
            parsed = NaturalLanguageParser.parse(prompt)

        if parsed.get("needs_clarification"):
            st.warning(
                parsed.get(
                    "clarification_message",
                    "More information is required."
                )
            )
            return

        validation = PhysicsValidator.validate(parsed)

        if not validation.is_valid:
            st.error("\n".join(validation.errors))
            return

        with st.spinner("Running physics simulation..."):
            result = run_engine(validation)

        st.session_state.validation = validation
        st.session_state.result = result

        st.success("Experiment complete!")


def custom_experiment():
    st.markdown(
        '<div class="section-title">Custom Experiment</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="muted">Adjust the physical variables yourself.</div>',
        unsafe_allow_html=True
    )

    with st.sidebar:
        st.header("Physics Controls")

        mass = st.slider(
            "Mass (kg)",
            0.1,
            50.0,
            1.0
        )

        gravity = st.slider(
            "Gravity (m/s²)",
            0.0,
            30.0,
            9.81
        )

        height = st.slider(
            "Initial Height (m)",
            0.0,
            100.0,
            10.0
        )

        velocity = st.slider(
            "Initial Velocity (m/s)",
            0.0,
            50.0,
            0.0
        )

        angle = st.slider(
            "Launch Angle (°)",
            0,
            90,
            0
        )

        elasticity = st.slider(
            "Elasticity",
            0.0,
            1.0,
            0.8
        )

    if st.button(
        "Run Experiment",
        type="primary",
        use_container_width=True
    ):
        params = {
            "mass": mass,
            "gravity": gravity,
            "height": height,
            "initial_velocity": velocity,
            "launch_angle": angle,
            "friction": 0.0,
            "tension": 0.0,
            "elasticity": elasticity,
            "air_resistance": 0.0,
            "planet_mass": 5.972e24,
            "planet_radius": 6371000.0
        }

        validation = PhysicsValidator.validate(
            {"parameters": params}
        )

        if not validation.is_valid:
            st.error("\n".join(validation.errors))
            return

        with st.spinner("Running physics simulation..."):
            result = run_engine(validation)

        st.session_state.validation = validation
        st.session_state.result = result

        st.success("Experiment complete!")


def results_page():
    result = st.session_state.result
    validation = st.session_state.validation

    if result is None or validation is None:
        return

    if result["status"] != "success":
        return

    trajectory = result["trajectory"]

    st.divider()

    st.markdown(
        '<div class="section-title">Experiment Results</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([3, 2])

    with col1:
        motion_graph(trajectory)

    with col2:
        physics_tutor(trajectory)

    if result.get("warnings"):
        st.warning("\n".join(result["warnings"]))

    st.subheader("Final State")
    st.json(result["final_state"])


def motion_graph(trajectory):
    tab1, tab2 = st.tabs(
        [
            "2D Motion & Vectors",
            "Energy & Velocity"
        ]
    )

    x = [p["x"] for p in trajectory]
    y = [p["y"] for p in trajectory]
    time = [p["time"] for p in trajectory]

    with tab1:
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name="Trajectory"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[x[0]],
                y=[y[0]],
                mode="markers",
                marker=dict(size=15),
                name="Object"
            )
        )

        frames = []
        step = max(1, len(trajectory) // 100)

        for i in range(0, len(trajectory), step):
            p = trajectory[i]

            frames.append(
                go.Frame(
                    data=[
                        go.Scatter(
                            x=x,
                            y=y,
                            mode="lines"
                        ),
                        go.Scatter(
                            x=[p["x"]],
                            y=[p["y"]],
                            mode="markers",
                            marker=dict(size=15)
                        )
                    ]
                )
            )

        fig.frames = frames

        fig.update_layout(
            height=450,
            xaxis_title="X Position (m)",
            yaxis_title="Y Position (m)",
            updatemenus=[
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "label": "Play",
                            "method": "animate",
                            "args": [
                                None,
                                {
                                    "frame": {
                                        "duration": 20,
                                        "redraw": True
                                    },
                                    "fromcurrent": True
                                }
                            ]
                        }
                    ]
                }
            ]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with tab2:
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=[
                "Energy Changes",
                "Velocity"
            ]
        )

        fig.add_trace(
            go.Scatter(
                x=time,
                y=[p["ke"] for p in trajectory],
                name="Kinetic Energy"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=time,
                y=[p["pe"] for p in trajectory],
                name="Potential Energy"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=time,
                y=[p["total_e"] for p in trajectory],
                name="Total Energy"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=time,
                y=[p["vx"] for p in trajectory],
                name="Vx"
            ),
            row=2,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=time,
                y=[p["vy"] for p in trajectory],
                name="Vy"
            ),
            row=2,
            col=1
        )

        fig.update_layout(height=450)

        st.plotly_chart(
            fig,
            use_container_width=True
        )


def physics_tutor(trajectory):
    st.subheader("AI Physics Tutor")

    question = st.text_input(
        "Ask about the experiment",
        placeholder="Why does potential energy decrease?"
    )

    if question:
        st.info(
            "As the object falls, gravitational potential "
            "energy is converted into kinetic energy."
        )

    st.subheader("Experiment Summary")

    st.write("**Simulation:** RK4")

    st.write(
        f"**Time:** {trajectory[-1]['time']:.2f} s"
    )


def experiment_page():
    if st.sidebar.button("Back to Experiments"):
        st.session_state.page = "select"
        st.session_state.result = None
        st.session_state.validation = None
        st.query_params.clear()
        st.rerun()

    if st.session_state.experiment == "ai":
        ai_experiment()

    elif st.session_state.experiment == "custom":
        custom_experiment()

    results_page()


def render_app():
    load_css()
    init_state()

    experiment = st.query_params.get("experiment")

    if experiment:
        st.session_state.experiment = experiment
        st.session_state.page = "experiment"

    if st.session_state.page == "home":
        home_page()

    elif st.session_state.page == "select":
        selection_page()

    elif st.session_state.page == "experiment":
        experiment_page()
