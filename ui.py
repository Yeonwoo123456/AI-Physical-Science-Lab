import base64
from pathlib import Path

import streamlit as st


def load_css():
    path = Path(__file__).parent / "style.css"

    if path.exists():
        st.markdown(
            f"<style>{path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True
        )


def get_click_sound_data():
    sound_path = Path(__file__).parent / "assets" / "click.mp3"

    if not sound_path.exists():
        return ""

    return base64.b64encode(
        sound_path.read_bytes()
    ).decode()


def add_button_sound():
    sound_data = get_click_sound_data()

    if not sound_data:
        return

    st.html(
        f"""
        <audio
            id="physics-lab-button-sound"
            src="data:audio/mpeg;base64,{sound_data}"
            preload="auto">
        </audio>

        <script>
        (function() {{
            if (window.__physicsLabSoundInstalled) {{
                return;
            }}

            window.__physicsLabSoundInstalled = true;

            window.physicsLabPlayClick = function() {{
                const audio = document.getElementById(
                    "physics-lab-button-sound"
                );

                if (!audio) {{
                    return;
                }}

                audio.currentTime = 0;
                audio.play().catch(function() {{}});
            }};

            document.addEventListener("click", function(event) {{
                const button = event.target.closest("button");

                if (!button) {{
                    return;
                }}

                const text = button.innerText.trim();

                const excludedButtons = [
                    "Run Experiment",
                    "Analyze with AI"
                ];

                if (excludedButtons.includes(text)) {{
                    return;
                }}

                window.physicsLabPlayClick();
            }});
        }})();
        </script>
        """,
        unsafe_allow_javascript=True
    )


@st.cache_data
def get_image(path):
    p = Path(__file__).parent / path

    if not p.exists():
        return ""

    return base64.b64encode(
        p.read_bytes()
    ).decode()


def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "home"

    if "experiment" not in st.session_state:
        st.session_state.experiment = None

    if "natural_language_prompt" not in st.session_state:
        st.session_state.natural_language_prompt = ""


def home_page():
    st.markdown(
        '<div class="home-title">What happens if…?</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="home-subtitle">'
        'Turn your imagination into a physics experiment.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="home-description">'
        'Imagine a situation, describe it, and explore '
        'what happens through physics simulation.'
        '</div>',
        unsafe_allow_html=True
    )

    # Natural-language experiment input
    st.markdown(
        """
        <div style="
            max-width:850px;
            margin:35px auto 10px auto;
            color:#AAB4C3;
            font-size:15px;
            font-weight:600;
        ">
            ✨ DESCRIBE YOUR EXPERIMENT
        </div>
        """,
        unsafe_allow_html=True
    )

    prompt = st.text_area(
        "Describe your experiment",
        value=st.session_state.natural_language_prompt,
        placeholder=(
            'Example: "What happens if I launch a ball at '
            '20 m/s at a 45° angle?"'
        ),
        height=100,
        label_visibility="collapsed"
    )

    _, col, _ = st.columns([1.5, 1, 1.5])

    with col:
        if st.button(
            "✨ Try It →",
            type="primary",
            use_container_width=True
        ):
            if prompt.strip():
                st.session_state.natural_language_prompt = prompt.strip()
                st.session_state.page = "select"
                st.query_params.clear()
                st.rerun()
            else:
                st.warning("Describe an experiment first.")

    # Main CTA
    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:22px;
            color:#7F8A9A;
            font-size:14px;
        ">
            or choose an experiment manually
        </div>
        """,
        unsafe_allow_html=True
    )

    _, col, _ = st.columns([1, 2, 1])

    with col:
        if st.button(
            "Start Exploring",
            type="secondary",
            use_container_width=True
        ):
            st.session_state.page = "select"
            st.rerun()

    # How it works
    st.markdown(
        """
        <div style="
            max-width:950px;
            margin:75px auto 20px auto;
            text-align:center;
        ">
            <div style="
                color:white;
                font-size:25px;
                font-weight:700;
            ">
                How It Works
            </div>

            <div style="
                color:#7F8A9A;
                font-size:14px;
                margin-top:8px;
            ">
                From an idea to an interactive physics simulation.
            </div>

            <div style="
                display:grid;
                grid-template-columns:repeat(3, 1fr);
                gap:22px;
                margin-top:28px;
            ">
                <div style="
                    padding:24px 18px;
                    border:1px solid #252C36;
                    border-radius:16px;
                    background:#11151C;
                ">
                    <div style="font-size:30px;">💭</div>
                    <div style="
                        color:white;
                        font-size:18px;
                        font-weight:700;
                        margin-top:10px;
                    ">
                        1. Imagine
                    </div>
                    <div style="
                        color:#8E99A8;
                        font-size:14px;
                        margin-top:8px;
                        line-height:1.5;
                    ">
                        Think of a physical situation or experiment.
                    </div>
                </div>

                <div style="
                    padding:24px 18px;
                    border:1px solid #252C36;
                    border-radius:16px;
                    background:#11151C;
                ">
                    <div style="font-size:30px;">✨</div>
                    <div style="
                        color:white;
                        font-size:18px;
                        font-weight:700;
                        margin-top:10px;
                    ">
                        2. Describe
                    </div>
                    <div style="
                        color:#8E99A8;
                        font-size:14px;
                        margin-top:8px;
                        line-height:1.5;
                    ">
                        Describe what you want to test in natural language.
                    </div>
                </div>

                <div style="
                    padding:24px 18px;
                    border:1px solid #252C36;
                    border-radius:16px;
                    background:#11151C;
                ">
                    <div style="font-size:30px;">🔬</div>
                    <div style="
                        color:white;
                        font-size:18px;
                        font-weight:700;
                        margin-top:10px;
                    ">
                        3. Simulate
                    </div>
                    <div style="
                        color:#8E99A8;
                        font-size:14px;
                        margin-top:8px;
                        line-height:1.5;
                    ">
                        Turn the idea into a physics simulation and explore the result.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def selection_page():
    saved_prompt = st.session_state.get("natural_language_prompt", "")

    if saved_prompt:
        st.info(f"Your experiment idea: {saved_prompt}")

    st.html(
        """
        <div style="text-align:center; margin:10px 0 45px 0;">
            <div style="font-size:42px; font-weight:700; color:white;">
                Choose Your Experiment
            </div>
            <div style="
                font-size:20px;
                color:#AAB4C3;
                margin-top:18px;
            ">
                Explore different physical phenomena through simulation.
            </div>
        </div>
        """
    )

    experiments = [
        (
            "projectile",
            "Projectile Motion",
            "Kinematics",
            "Speed · Angle · Gravity",
            "#9FC5F8"
        ),
        (
            "collision",
            "Collision",
            "Momentum & Energy",
            "Mass · Speed · Elasticity",
            "#F4A6A6"
        ),
        (
            "pendulum",
            "Pendulum",
            "Periodic Motion",
            "Length · Gravity · Angle",
            "#F6D77A"
        ),
        (
            "spring",
            "Spring",
            "Hooke's Law",
            "Mass · k · Displacement",
            "#9ED6A8"
        ),
        (
            "friction",
            "Friction",
            "Friction Force",
            "μ · Mass · Gravity",
            "#8FD3D3"
        ),
        (
            "orbit",
            "Gravity & Orbit",
            "Gravity",
            "Mass · Distance · Velocity",
            "#B7A4E8"
        )
    ]

    cards = ""

    for key, title, concept, params, color in experiments:
        image = get_image(f"assets/{key}.png")

        cards += f"""
        <a href="?experiment={key}"
           class="physics-card"
           style="
               background-color:{color};
               background-image:url(
                   'data:image/png;base64,{image}'
               );
           ">

            <div class="card-text">
                <div class="card-title">{title}</div>
                <div class="card-concept">{concept}</div>
                <div class="card-parameters">{params}</div>
            </div>

        </a>
        """

    st.html(
        f"""
        <div class="physics-grid">
            {cards}
        </div>
        """
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.session_state.experiment = None
        st.query_params.clear()
        st.rerun()


def show_experiment_error(name, error):
    st.error(f"{name} could not be loaded.")

    with st.expander("Show error details"):
        st.code(f"{type(error).__name__}: {error}")

    if st.button(
        "Back to Experiments",
        key=f"{name}_error_back"
    ):
        st.session_state.page = "select"
        st.session_state.experiment = None
        st.query_params.clear()
        st.rerun()


def run_experiment_safely(
    experiment,
    module_name,
    function_name,
    display_name
):
    try:
        module = __import__(
            module_name,
            fromlist=[function_name]
        )

        experiment_function = getattr(
            module,
            function_name
        )

        if not callable(experiment_function):
            raise TypeError(
                f"{function_name} is not callable."
            )

        experiment_function()

    except ImportError as error:
        show_experiment_error(display_name, error)

    except AttributeError as error:
        show_experiment_error(display_name, error)

    except Exception as error:
        show_experiment_error(display_name, error)


def experiment_page():
    experiment = st.session_state.get("experiment")

    experiment_map = {
        "projectile": (
            "experiments.projectile",
            "projectile_experiment",
            "Projectile Motion"
        ),
        "collision": (
            "experiments.collision",
            "collision_experiment",
            "Collision"
        ),
        "pendulum": (
            "experiments.pendulum",
            "pendulum_experiment",
            "Pendulum"
        ),
        "spring": (
            "experiments.spring",
            "spring_experiment",
            "Spring"
        ),
        "friction": (
            "experiments.friction",
            "friction_experiment",
            "Friction"
        ),
        "orbit": (
            "experiments.orbit",
            "orbit_experiment",
            "Gravity & Orbit"
        )
    }

    config = experiment_map.get(experiment)

    if config is None:
        st.warning("This experiment is not available.")

        if st.button(
            "Back to Experiments",
            key="unknown_experiment_back"
        ):
            st.session_state.page = "select"
            st.session_state.experiment = None
            st.query_params.clear()
            st.rerun()

        return

    module_name, function_name, display_name = config

    run_experiment_safely(
        experiment,
        module_name,
        function_name,
        display_name
    )


def render_app():
    load_css()
    init_state()
    add_button_sound()

    experiment = st.query_params.get("experiment")

    valid_experiments = {
        "projectile",
        "collision",
        "pendulum",
        "spring",
        "friction",
        "orbit"
    }

    if experiment in valid_experiments:
        st.session_state.experiment = experiment
        st.session_state.page = "experiment"

    elif experiment is not None:
        st.session_state.experiment = None
        st.session_state.page = "select"
        st.query_params.clear()

    if st.session_state.page == "home":
        home_page()

    elif st.session_state.page == "select":
        selection_page()

    else:
        experiment_page()
