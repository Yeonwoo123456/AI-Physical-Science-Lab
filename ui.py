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
        '<div class="section-title">Choose Your Experiment</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="selection-description">'
        'Explore different physical phenomena through simulation.'
        '</div>',
        unsafe_allow_html=True
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

        image = get_image(
            f"assets/{key}.png"
        )

        cards += f"""
        <a href="?experiment={key}"
           class="physics-card"
           style="
               background-color:{color};
               background-image:url('data:image/png;base64,{image}');
           ">

            <div class="card-text">

                <div class="card-title">
                    {title}
                </div>

                <div class="card-concept">
                    {concept}
                </div>

                <div class="card-parameters">
                    {params}
                </div>

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

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    if st.button("Back to Home"):

        st.session_state.page = "home"
        st.session_state.experiment = None

        st.query_params.clear()

        st.rerun()


def experiment_page():

    experiment = st.session_state.experiment

    # ----------------------------------------
    # Projectile Motion
    # ----------------------------------------
    if experiment == "projectile":

        from experiments.projectile import projectile_experiment

        projectile_experiment()

        return

    # ----------------------------------------
    # Collision
    # ----------------------------------------
    if experiment == "collision":

        from experiments.collision import collision_experiment

        collision_experiment()

        return

    # ----------------------------------------
    # Pendulum
    # ----------------------------------------
    if experiment == "pendulum":

        from experiments.pendulum import pendulum_experiment

        pendulum_experiment()

        return

    # ----------------------------------------
    # Spring
    # ----------------------------------------
    if experiment == "spring":

        from experiments.spring import spring_experiment

        spring_experiment()

        return

    # ----------------------------------------
    # Friction
    # ----------------------------------------
    if experiment == "friction":

        from experiments.friction import friction_experiment

        friction_experiment()

        return

    # ----------------------------------------
    # Gravity & Orbit
    # ----------------------------------------
    if experiment == "orbit":

        from experiments.orbit import orbit_experiment

        orbit_experiment()

        return

    # ----------------------------------------
    # Unknown experiment
    # ----------------------------------------
    st.title("Physics Experiment")

    st.write(
        "This experiment is currently under development."
    )

    if st.button("Back to Experiments"):

        st.session_state.page = "select"
        st.session_state.experiment = None

        st.query_params.clear()

        st.rerun()


def render_app():

    load_css()

    init_state()

    experiment = st.query_params.get(
        "experiment"
    )

    if experiment:

        st.session_state.experiment = experiment
        st.session_state.page = "experiment"

    if st.session_state.page == "home":

        home_page()

    elif st.session_state.page == "select":

        selection_page()

    else:

        experiment_page()
