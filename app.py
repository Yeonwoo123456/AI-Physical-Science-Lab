import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app_modules import NaturalLanguageParser, PhysicsValidator, PhysicsEngine

st.set_page_config(
    page_title="AI Physical Science Lab",
    layout="wide",
    page_icon="🔬"
)

if "result" not in st.session_state:
    st.session_state.result = None

if "validation_result" not in st.session_state:
    st.session_state.validation_result = None

if "user_prompt" not in st.session_state:
    st.session_state.user_prompt = ""

st.sidebar.header("⚙️ Advanced Controls")

manual_mass = st.sidebar.slider(
    "Mass (kg)",
    0.1,
    50.0,
    1.0
)

manual_gravity = st.sidebar.slider(
    "Gravity (m/s²)",
    0.0,
    30.0,
    9.81
)

manual_height = st.sidebar.slider(
    "Initial Height (m)",
    0.0,
    100.0,
    10.0
)

manual_v0 = st.sidebar.slider(
    "Initial Velocity (m/s)",
    0.0,
    50.0,
    0.0
)

manual_angle = st.sidebar.slider(
    "Launch Angle (deg)",
    0,
    90,
    0
)

manual_elasticity = st.sidebar.slider(
    "Elasticity",
    0.0,
    1.0,
    0.8
)

st.markdown(
    """
    <div style="
        text-align:center;
        padding:55px 0 20px 0;
    ">
        <h1 style="
            font-size:64px;
            margin-bottom:12px;
            font-weight:700;
        ">
            What happens if…?
        </h1>

        <p style="
            font-size:20px;
            color:#777;
            margin-bottom:10px;
        ">
            Turn your imagination into a physics experiment.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="
        text-align:center;
        color:#888;
        font-size:15px;
        margin-bottom:25px;
    ">
        Describe anything you can imagine and let AI turn it into physics.
    </div>
    """,
    unsafe_allow_html=True
)

user_prompt = st.text_input(
    "What would you like to simulate?",
    value=st.session_state.user_prompt,
    placeholder="Example: Drop a ball from 20 meters on the Moon.",
    label_visibility="visible"
)

st.session_state.user_prompt = user_prompt

st.markdown(
    """
    <div style="
        text-align:center;
        color:#888;
        font-size:14px;
        margin-top:8px;
        margin-bottom:20px;
    ">
        Try: drop an object • throw a ball • change gravity • launch an object
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    run_ai = st.button(
        "🚀 Run Experiment",
        use_container_width=True
    )

st.markdown("---")

manual_col1, manual_col2, manual_col3 = st.columns([1, 2, 1])

with manual_col2:
    run_manual = st.button(
        "🎛️ Run with Advanced Controls",
        use_container_width=True
    )

if run_ai:
    if not user_prompt.strip():
        st.warning("Describe a physics situation first.")
    else:
        with st.spinner("AI is turning your idea into a physics experiment..."):
            parsed = NaturalLanguageParser.parse(user_prompt)

        if parsed.get("needs_clarification"):
            st.warning(
                parsed.get(
                    "clarification_message",
                    "More information is required."
                )
            )
        else:
            validation_result = PhysicsValidator.validate(parsed)

            if validation_result.is_valid:
                st.session_state.validation_result = validation_result

                with st.spinner("Running physics simulation..."):
                    engine = PhysicsEngine(
                        dt=0.02,
                        solver="rk4"
                    )

                    result = engine.simulate(
                        validation_result,
                        total_time=8.0
                    )

                st.session_state.result = result

                st.success(
                    f"Experiment ready! [{validation_result.mode}]"
                )

            else:
                st.session_state.result = None
                st.session_state.validation_result = None
                st.error(
                    "\n".join(validation_result.errors)
                )

if run_manual:
    params = {
        "mass": manual_mass,
        "gravity": manual_gravity,
        "height": manual_height,
        "initial_velocity": manual_v0,
        "launch_angle": manual_angle,
        "friction": 0.0,
        "tension": 0.0,
        "elasticity": manual_elasticity,
        "air_resistance": 0.0,
        "planet_mass": 5.972e24,
        "planet_radius": 6371000.0
    }

    validation_result = PhysicsValidator.validate(
        {"parameters": params}
    )

    if validation_result.is_valid:
        st.session_state.validation_result = validation_result

        with st.spinner("Running physics simulation..."):
            engine = PhysicsEngine(
                dt=0.02,
                solver="rk4"
            )

            result = engine.simulate(
                validation_result,
                total_time=8.0
            )

        st.session_state.result = result

        st.success("Manual experiment ready.")

    else:
        st.session_state.result = None
        st.session_state.validation_result = None
        st.error(
            "\n".join(validation_result.errors)
        )

result = st.session_state.result
validation_result = st.session_state.validation_result

if result is not None and validation_result is not None:

    if result["status"] == "success":

        trajectory = result["trajectory"]

        st.markdown("---")

        st.subheader("🔬 Experiment Results")

        left, right = st.columns([3, 2])

        with left:

            tab1, tab2 = st.tabs(
                [
                    "🎥 2D Motion & Vectors",
                    "📊 Energy & Velocity"
                ]
            )

            with tab1:

                xs = [p["x"] for p in trajectory]
                ys = [p["y"] for p in trajectory]

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

                for i in range(
                    0,
                    len(trajectory),
                    step
                ):
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

                times = [
                    p["time"]
                    for p in trajectory
                ]

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

        with right:

            st.subheader("🤖 AI Physics Tutor")

            st.markdown(
                "Ask a question about your experiment."
            )

            q = st.text_input(
                "Question",
                placeholder="Why does potential energy decrease?",
                key="physics_question"
            )

            if q:
                st.write(f"**Q:** {q}")

                st.info(
                    "As the object falls, gravity does work "
                    "on it, converting gravitational potential "
                    "energy into kinetic energy."
                )

            st.markdown("---")

            st.subheader("📌 Experiment Summary")

            st.write(
                f"**Mode:** {validation_result.mode}"
            )

            st.write(
                f"**Simulation:** RK4"
            )

            st.write(
                f"**Time:** {result['trajectory'][-1]['time']:.2f} s"
            )

        if result["warnings"]:
            st.warning(
                "\n".join(result["warnings"])
            )

        st.subheader("📍 Final State")

        st.json(
            result["final_state"]
        )
