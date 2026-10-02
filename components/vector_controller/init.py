import os

import streamlit.components.v1 as components


_RELEASE = True

if _RELEASE:
    COMPONENT_DIR = os.path.join(
        os.path.dirname(__file__),
        "frontend"
    )

    _vector_controller = components.declare_component(
        "vector_controller",
        path=COMPONENT_DIR
    )
else:
    _vector_controller = components.declare_component(
        "vector_controller",
        url="http://localhost:3001"
    )


def vector_controller(
    velocity=20.0,
    angle=45.0,
    height=500,
    width=900,
    key=None
):
    return _vector_controller(
        velocity=float(velocity),
        angle=float(angle),
        height=height,
        width=width,
        key=key,
        default={
            "velocity": float(velocity),
            "angle": float(angle)
        }
    )
