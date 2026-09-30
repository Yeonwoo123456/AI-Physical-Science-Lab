import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app_modules import NaturalLanguageParser, PhysicsValidator, PhysicsEngine


st.set_page_config(
    page_title="AI Physical Science Lab",
    layout="wide",
    page_icon="🔬"
)


with open("style.css", "r", encoding="utf-8") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )


def init_state():
    defaults = {
        "page": "home",
        "experiment": None,
        "result": None,
        "validation": None,
        "prompt": ""
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def card(title, description):
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{title}</div>
            <div class="card-description">
                {description}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def run_simulation(validation):
    engine = PhysicsEngine(
        dt=0.02,
        solver="rk4"
    )

    return engine.simulate(
        validation,
        total_time=8.0
    )


def show_home():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">
                What happens if…?
            </div>

            <div class="hero-subtitle">
                Turn your imagination into a physics experiment.
            </div>

            <div class="hero-description">
                Imagine a physical situation and explore
                what happens through physics simulation.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "🚀 Start Exploring",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.page = "select"
            st.rerun()


def show_selection():
    st.markdown(
        '<div class="section-title">Choose an Experiment</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="muted">Choose how you want to explore physics.</p>',
        unsafe_allow_html=True
    )

    st.write("")

    col1, col2 = st.columns(2)

    with col1:
        card(
            "🤖 AI Experiment",
            "Describe a situation in natural language "
            "and let AI turn it into a physics simulation."
        )

        if st.button(
            "Start AI Experiment",
            use_container_width=True
        ):
            st.session_state.experiment = "ai"
            st.session_state.page = "experiment"
            st.rerun()

    with col2:
        card(
            "🎛️ Custom Experiment",
            "Adjust physical variables yourself "
            "and build your own experiment."
        )

        if st.button(
            "Start Custom Experiment",
            use_container_width=True
        ):
            st.session_state.experiment = "custom"
            st.session_state.page = "experiment"
            st.rerun()

    st.write("")
    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        card(
            "🪂 Free Fall",
            "Explore how objects move under gravity."
        )

    with col2:
        card(
            "🏀 Projectile Motion",
            "Explore how launch speed and angle affect motion."
        )

    with col3:
        card(
            "🌎 Different Worlds",
            "Explore how different gravity changes motion."
        )

    st.write("")

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()


def show_ai_experiment():

    st.sidebar.header("⚙️ Experiment")

    st.sidebar.caption(
        "AI determines the physical parameters "
        "from your description."
    )

    st.markdown(
        '<div class="section-title">🤖 AI Physics Experiment</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="muted">'
        'Describe the situation you want to simulate.'
        '</p>',
        unsafe_allow_html=True
    )

    prompt = st.text_input(
        "What happens if...",
        value=st.session_state.prompt,
        placeholder="Example: Drop a ball from 20 meters on the Moon."
    )

    st.session_state.prompt = prompt

    if st.button(
        "🚀 Run Experiment",
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
            result = run_simulation(validation)

        st.session_state.validation = validation
        st.session_state.result = result

        st.success("Experiment ready!")


def show_custom_experiment():

    st.sidebar.header("⚙️ Physics Controls")

    mass = st.sidebar.slider(
        "Mass (kg)",
        0.1,
        50.0,
        1.0
    )

    gravity = st.sidebar.slider(
        "Gravity (m/s²)",
        0.0,
        30.0,
        9.81
    )

    height = st.sidebar.slider(
        "Initial Height (m)",
        0.0,
        100.0,
        10.0
    )

    velocity = st.sidebar.slider(
        "Initial Velocity (m/s)",
        0.0,
        50.0,
        0.0
    )

    angle = st.sidebar.slider(
        "Launch Angle (deg)",
        0,
        90,
        0
    )

    elasticity = st.sidebar.slider(
        "Elasticity",
        0.0,
        1.0,
        0.8
    )

    st.markdown(
        '<div class="section-title">'
        '🎛️ Custom Physics Experiment'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="muted">'
        'Adjust the physical variables and run your experiment.'
        '</p>',
        unsafe_allow_html=True
    )

    if st.button(
        "🚀 Run Experiment",
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
            result = run_simulation(validation)

        st.session_state.validation = validation
        st.session_state.result = result

        st.success("Experiment ready!")


def show_results():

    result = st.session_state.result
    validation = st.session_state.validation

    if result is None or validation is None:
        return

    if result["status"] != "success":
        return

    trajectory = result["trajectory"]

    st.markdown("---")

    st.markdown(
        '<div class="section-title">🔬 Experiment Results</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns([3, 2])

    with left:
        show_motion_graph(trajectory)

    with right:
        show_tutor(validation, trajectory)

    if result["warnings"]:
        st.warning("\n".join(result["warnings"]))

    st.subheader("📍 Final State")
    st.json(result["final_state"])


def show_motion_graph(trajectory):

    tab1, tab2 = st.tabs(
        [
            "🎥 2D Motion & Vectors",
            "📊 Energy & Velocity"
        ]
    )

    xs = [p["x"] for p in trajectory]
    ys = [p["y"] for p in trajectory]
    times = [p["time"] for p in trajectory]

    with tab1:

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                name="Trajectory",
                line=dict(dash="dot")
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[xs[0]],
                y=[ys[0]],
                mode="markers",
                marker=dict(size=18),
                name="Object"
            )
        )

        frames = []

        step = max(
            1,
            len(trajectory) // 100
        )

        for i in range(0, len(trajectory), step):

            p = trajectory[i]

            frames.append(
                go.Frame(
                    data=[
                        go.Scatter(
                            x=xs,
                            y=ys,
                            mode="lines"
                        ),
                        go.Scatter(
                            x=[p["x"]],
                            y=[p["y"]],
                            mode="markers",
                            marker=dict(size=18)
                        ),
                        go.Scatter(
                            x=[
                                p["x"],
                                p["x"] + p["fx"] * 0.05
                            ],
                            y=[
                                p["y"],
                                p["y"] + p["fy"] * 0.05
                            ],
                            mode="lines+markers"
                        )
                    ]
                )
            )

        fig.frames = frames

        fig.update_layout(
            xaxis_title="X Position (m)",
            yaxis_title="Y Position (m)",
            height=450,
            margin=dict(
                l=20,
                r=20,
                t=30,
                b=20
            ),
            updatemenus=[
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "label": "▶ Play",
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
                "Energy Changes (J)",
                "Velocity Components (m/s)"
            ]
        )

        fig.add_trace(
            go.Scatter(
                x=times,
                y=[p["ke"] for p in trajectory],
                name="Kinetic Energy"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=times,
                y=[p["pe"] for p in trajectory],
                name="Potential Energy"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=times,
                y=[p["total_e"] for p in trajectory],
                name="Total Energy"
            ),
            row=1,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=times,
                y=[p["vx"] for p in trajectory],
                name="Vx"
            ),
            row=2,
            col=1
        )

        fig.add_trace(
            go.Scatter(
                x=times,
                y=[p["vy"] for p in trajectory],
                name="Vy"
            ),
            row=2,
            col=1
        )

        fig.update_layout(
            height=450,
            margin=dict(
                l=20,
                r=20,
                t=50,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


def show_tutor(validation, trajectory):

    st.subheader("🤖 AI Physics Tutor")

    st.markdown(
        "Ask a question about your experiment."
    )

    question = st.text_input(
        "Question",
        placeholder="Why does potential energy decrease?",
        key="physics_question"
    )

    if question:
        st.write(f"**Q:** {question}")

        st.info(
            "As the object falls, gravity does work on it, "
            "converting gravitational potential energy into "
            "kinetic energy."
        )

    st.markdown("---")

    st.subheader("📌 Experiment Summary")

    st.write(
        f"**Mode:** {validation.mode}"
    )

    st.write(
        "**Simulation:** RK4"
    )

    st.write(
        f"**Time:** {trajectory[-1]['time']:.2f} s"
    )


def show_experiment():

    if st.sidebar.button("← Back to Experiments"):
        st.session_state.page = "select"
        st.session_state.result = None
        st.session_state.validation = None
        st.rerun()

    if st.session_state.experiment == "ai":
        show_ai_experiment()

    elif st.session_state.experiment == "custom":
        show_custom_experiment()

    show_results()


init_state()

if st.session_state.page == "home":
    show_home()

elif st.session_state.page == "select":
    show_selection()

elif st.session_state.page == "experiment":
    show_experiment()
