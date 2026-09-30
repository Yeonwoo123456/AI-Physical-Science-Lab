import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app_modules import NaturalLanguageParser, PhysicsValidator, PhysicsEngine

st.set_page_config(
    page_title="AI Physical Science Lab",
    layout="wide",
    page_icon="🔬"
)

st.sidebar.header("⚙️ Manual Controls")

manual_mass = st.sidebar.slider("Mass (kg)", 0.1, 50.0, 1.0)
manual_gravity = st.sidebar.slider("Gravity (m/s²)", 0.0, 30.0, 9.81)
manual_height = st.sidebar.slider("Initial Height (m)", 0.0, 100.0, 10.0)
manual_v0 = st.sidebar.slider("Initial Velocity (m/s)", 0.0, 50.0, 0.0)
manual_angle = st.sidebar.slider("Launch Angle (deg)", 0, 90, 0)
manual_elasticity = st.sidebar.slider("Elasticity", 0.0, 1.0, 0.8)

st.title("🔬 AI Physical Science Lab")

st.markdown(
    "Describe a physics experiment in natural language "
    "or adjust the variables manually."
)

user_prompt = st.text_input(
    "💬 AI Natural Language Command",
    placeholder="Example: Drop a 5 kg ball from 20 meters on a planet with 3 times Earth's gravity."
)

col_btn1, col_btn2 = st.columns([1, 4])

with col_btn1:
    run_ai = st.button(
        "🚀 Run AI Analysis",
        use_container_width=True
    )

with col_btn2:
    run_manual = st.button(
        "🎛️ Run Manual Experiment",
        use_container_width=True
    )

params = None
validation_result = None

if run_ai and user_prompt:
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
            params = validation_result.validated_params
            st.success(
                f"AI analysis complete! [{validation_result.mode}]"
            )
        else:
            st.error("\n".join(validation_result.errors))

elif run_manual:
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
        st.info("Manual experiment initialized.")
    else:
        st.error("\n".join(validation_result.errors))
        params = None

if params is not None and validation_result is not None:
    engine = PhysicsEngine(dt=0.02, solver="rk4")

    result = engine.simulate(
        validation_result,
        total_time=8.0
    )

    if result["status"] == "success":
        trajectory = result["trajectory"]

        left, right = st.columns([3, 2])

        with left:
            tab1, tab2 = st.tabs(
                ["🎥 2D Motion & Vectors", "📊 Energy & Velocity"]
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

                for i in range(
                    0,
                    len(trajectory),
                    max(1, len(trajectory) // 100)
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
                    height=420,
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
                                            }
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
                times = [p["time"] for p in trajectory]

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

                fig.update_layout(height=420)

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        with right:
            st.subheader("🤖 AI Physics Tutor")
            st.markdown("Ask questions about the simulation.")

            q = st.text_input(
                "Question",
                placeholder="Why does potential energy decrease?"
            )

            if q:
                st.write(f"**Q:** {q}")
                st.info(
                    "**AI Answer:** As the object falls, gravity does work "
                    "on it, converting gravitational potential energy into "
                    "kinetic energy."
                )

        if result["warnings"]:
            st.warning("\n".join(result["warnings"]))

        st.subheader("Final State")
        st.json(result["final_state"])
