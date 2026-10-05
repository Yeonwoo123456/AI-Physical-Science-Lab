import os
import threading
from collections import deque

import av
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

def get_rtc_configuration():
    try:
        turn_key_id = st.secrets.get("CLOUDFLARE_TURN_KEY_ID")
        turn_api_token = st.secrets.get("CLOUDFLARE_TURN_KEY_API_TOKEN")
    except Exception:
        turn_key_id = None
        turn_api_token = None

    if turn_key_id and turn_api_token:
        os.environ["CLOUDFLARE_TURN_KEY_ID"] = str(turn_key_id)
        os.environ["CLOUDFLARE_TURN_KEY_API_TOKEN"] = str(turn_api_token)
        return None

    return {
        "iceServers": [
            {
                "urls": [
                    "stun:stun.l.google.com:19302",
                    "stun:stun1.l.google.com:19302",
                    "stun:stun.cloudflare.com:3478"
                ]
            }
        ]
    }

class MotionTracker:
    def __init__(self, mode):
        self.mode = mode
        self.lock = threading.Lock()
        self.projectile_positions = deque(maxlen=3000)
        self.collision_records = deque(maxlen=3000)
        self.start_time = None

    def reset(self):
        with self.lock:
            self.projectile_positions.clear()
            self.collision_records.clear()
            self.start_time = None

    def projectile_data(self):
        with self.lock:
            return list(self.projectile_positions)

    def collision_data(self):
        with self.lock:
            return list(self.collision_records)

def find_center(mask, minimum_area=150):
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < minimum_area:
        return None

    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return None

    return (
        moments["m10"] / moments["m00"],
        moments["m01"] / moments["m00"]
    )

def make_projectile_callback(tracker):
    def callback(frame):
        try:
            image = frame.to_ndarray(format="bgr24")
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(
                hsv,
                np.array([0, 100, 80]),
                np.array([25, 255, 255])
            )

            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            if contours:
                contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(contour) >= 150:
                    x, y, w, h = cv2.boundingRect(contour)
                    cx = x + w / 2
                    cy = y + h / 2
                    now = pd.Timestamp.now().timestamp()

                    with tracker.lock:
                        if tracker.start_time is None:
                            tracker.start_time = now
                        tracker.projectile_positions.append(
                            (now - tracker.start_time, cx, cy)
                        )

                    cv2.rectangle(
                        image,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )
                    cv2.circle(
                        image,
                        (int(cx), int(cy)),
                        5,
                        (0, 255, 0),
                        -1
                    )

            return av.VideoFrame.from_ndarray(image, format="bgr24")
        except Exception:
            return frame

    return callback

def make_collision_callback(tracker):
    def callback(frame):
        try:
            image = frame.to_ndarray(format="bgr24")
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            red_mask = cv2.inRange(
                hsv,
                np.array([0, 100, 80]),
                np.array([10, 255, 255])
            ) | cv2.inRange(
                hsv,
                np.array([170, 100, 80]),
                np.array([179, 255, 255])
            )

            blue_mask = cv2.inRange(
                hsv,
                np.array([90, 100, 80]),
                np.array([135, 255, 255])
            )

            red_center = find_center(red_mask)
            blue_center = find_center(blue_mask)

            if red_center is not None and blue_center is not None:
                now = pd.Timestamp.now().timestamp()

                with tracker.lock:
                    if tracker.start_time is None:
                        tracker.start_time = now
                    t = now - tracker.start_time
                    tracker.collision_records.append(
                        (
                            t,
                            red_center[0],
                            blue_center[0],
                            abs(red_center[0] - blue_center[0])
                        )
                    )

                cv2.circle(
                    image,
                    (int(red_center[0]), int(red_center[1])),
                    7,
                    (0, 255, 0),
                    -1
                )
                cv2.circle(
                    image,
                    (int(blue_center[0]), int(blue_center[1])),
                    7,
                    (0, 255, 0),
                    -1
                )

            return av.VideoFrame.from_ndarray(image, format="bgr24")
        except Exception:
            return frame

    return callback

def start_camera(key, callback, tracker):
    kwargs = {
        "key": key,
        "mode": WebRtcMode.SENDRECV,
        "media_stream_constraints": {
            "video": True,
            "audio": False
        },
        "video_frame_callback": callback,
        "async_processing": True
    }

    rtc_configuration = get_rtc_configuration()
    if rtc_configuration is not None:
        kwargs["rtc_configuration"] = rtc_configuration

    try:
        return webrtc_streamer(**kwargs)
    except Exception as exc:
        st.error("Camera connection could not be started.")
        with st.expander("Connection details"):
            st.code(f"{type(exc).__name__}: {exc}")
        return None

def get_tracker(key, mode):
    state_key = f"{key}_tracker"
    tracker = st.session_state.get(state_key)
    if tracker is None or tracker.mode != mode:
        tracker = MotionTracker(mode)
        st.session_state[state_key] = tracker
    return tracker

def analyze_projectile(data, pixels_per_meter):
    if len(data) < 5:
        return None

    df = pd.DataFrame(data, columns=["time", "x_px", "y_px"])
    df["x"] = df["x_px"] / pixels_per_meter
    df["y"] = -df["y_px"] / pixels_per_meter

    if len(df) < 3 or np.any(np.diff(df["time"]) <= 0):
        return None

    df["vx"] = np.gradient(df["x"], df["time"])
    df["vy"] = np.gradient(df["y"], df["time"])
    df["speed"] = np.sqrt(df["vx"] ** 2 + df["vy"] ** 2)
    df["ax"] = np.gradient(df["vx"], df["time"])
    df["ay"] = np.gradient(df["vy"], df["time"])
    return df

def analyze_collision(data, pixels_per_meter, mass_red, mass_blue):
    if len(data) < 8:
        return None

    df = pd.DataFrame(
        data,
        columns=["time", "red_px", "blue_px", "distance_px"]
    )

    if len(df) < 3 or np.any(np.diff(df["time"]) <= 0):
        return None

    df["red_x"] = df["red_px"] / pixels_per_meter
    df["blue_x"] = df["blue_px"] / pixels_per_meter
    df["distance"] = df["distance_px"] / pixels_per_meter
    df["red_v"] = np.gradient(df["red_x"], df["time"])
    df["blue_v"] = np.gradient(df["blue_x"], df["time"])
    df["momentum"] = (
        mass_red * df["red_v"] +
        mass_blue * df["blue_v"]
    )
    df["kinetic_energy"] = (
        0.5 * mass_red * df["red_v"] ** 2 +
        0.5 * mass_blue * df["blue_v"] ** 2
    )
    return df

def projectile_mode():
    st.markdown('<h2 style="text-align:center;">Real-World Projectile Motion</h2>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;">Use your laptop camera to track a colored object and estimate its motion.</p>', unsafe_allow_html=True)

    pixels_per_meter = st.number_input(
        "Pixels per meter",
        min_value=10.0,
        value=300.0,
        step=10.0,
        key="rw_projectile_scale"
    )

    st.caption(
        "Place a known-length reference in the camera view to estimate the scale. "
        "The current prototype uses manual calibration."
    )

    tracker = get_tracker("real_world_projectile", "projectile")
    callback = make_projectile_callback(tracker)

    try:
        rtc_configuration = get_rtc_configuration()
        kwargs = {
            "key": "real-world-projectile-v3",
            "mode": WebRtcMode.SENDRECV,
            "media_stream_constraints": {"video": True, "audio": False},
            "video_frame_callback": callback,
            "async_processing": True,
            "media_toggle_controls": False,
        }
        if rtc_configuration is not None:
            kwargs["rtc_configuration"] = rtc_configuration
        ctx = webrtc_streamer(**kwargs)
    except Exception as exc:
        st.error("Camera connection could not be started.")
        st.exception(exc)
        ctx = None

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Analyze Projectile Motion", key="rw_projectile_analyze", use_container_width=True):
            data = tracker.projectile_data()
            df = analyze_projectile(data, pixels_per_meter)
            if df is None:
                st.warning("Not enough motion data yet. Start the camera and move the object first.")
            else:
                st.session_state.real_projectile_data = df

    with col2:
        if st.button("Clear Data", key="rw_projectile_clear", use_container_width=True):
            tracker.reset()
            st.session_state.pop("real_projectile_data", None)
            st.rerun()

    df = st.session_state.get("real_projectile_data")
    if df is not None:
        st.markdown("### Motion Data")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Flight Time", f"{df['time'].iloc[-1]:.2f} s")
        m2.metric("Max Height", f"{df['y'].max():.2f} m")
        m3.metric("Max Speed", f"{df['speed'].max():.2f} m/s")
        m4.metric("Samples", len(df))
        st.markdown("#### Position")
        st.line_chart(df.set_index("time")[["x", "y"]])
        st.markdown("#### Velocity")
        st.line_chart(df.set_index("time")[["vx", "vy", "speed"]])
        st.markdown("#### Acceleration")
        st.line_chart(df.set_index("time")[["ax", "ay"]])
        st.dataframe(
            df[["time", "x", "y", "vx", "vy", "speed", "ax", "ay"]],
            use_container_width=True
        )

def collision_mode():
    st.markdown('<h2 style="text-align:center;">Real-World Collision</h2>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;">Use two colored objects to estimate velocity, momentum, and kinetic energy.</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        pixels_per_meter = st.number_input(
            "Pixels per meter",
            min_value=10.0,
            value=300.0,
            step=10.0,
            key="rw_collision_scale"
        )
    with col2:
        mass_red = st.number_input(
            "Red mass (kg)",
            min_value=0.001,
            value=1.0,
            step=0.1,
            key="rw_collision_mass_red"
        )
    with col3:
        mass_blue = st.number_input(
            "Blue mass (kg)",
            min_value=0.001,
            value=1.0,
            step=0.1,
            key="rw_collision_mass_blue"
        )

    st.caption(
        "Use a red object and a blue object. Keep the motion mostly horizontal for this prototype."
    )

    tracker = get_tracker("real_world_collision", "collision")
    callback = make_collision_callback(tracker)

    try:
        rtc_configuration = get_rtc_configuration()
        kwargs = {
            "key": "real-world-collision-v3",
            "mode": WebRtcMode.SENDRECV,
            "media_stream_constraints": {"video": True, "audio": False},
            "video_frame_callback": callback,
            "async_processing": True,
            "media_toggle_controls": False,
        }
        if rtc_configuration is not None:
            kwargs["rtc_configuration"] = rtc_configuration
        ctx = webrtc_streamer(**kwargs)
    except Exception as exc:
        st.error("Camera connection could not be started.")
        st.exception(exc)
        ctx = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Analyze Collision", key="rw_collision_analyze", use_container_width=True):
            data = tracker.collision_data()
            df = analyze_collision(
                data,
                pixels_per_meter,
                mass_red,
                mass_blue
            )
            if df is None:
                st.warning("Not enough collision data yet. Start the camera and move the objects first.")
            else:
                st.session_state.real_collision_data = df

    with col2:
        if st.button("Clear Data", key="rw_collision_clear", use_container_width=True):
            tracker.reset()
            st.session_state.pop("real_collision_data", None)
            st.rerun()

    df = st.session_state.get("real_collision_data")
    if df is not None:
        st.markdown("### Collision Data")
        m1, m2, m3 = st.columns(3)
        m1.metric("Initial Distance", f"{df['distance'].iloc[0]:.2f} m")
        m2.metric("Minimum Distance", f"{df['distance'].min():.2f} m")
        m3.metric("Samples", len(df))
        st.markdown("#### Object Velocity")
        st.line_chart(df.set_index("time")[["red_v", "blue_v"]])
        st.markdown("#### Total Momentum")
        st.line_chart(df.set_index("time")[["momentum"]])
        st.markdown("#### Kinetic Energy")
        st.line_chart(df.set_index("time")[["kinetic_energy"]])
        st.dataframe(
            df[[
                "time",
                "red_x",
                "blue_x",
                "distance",
                "red_v",
                "blue_v",
                "momentum",
                "kinetic_energy"
            ]],
            use_container_width=True
        )

def real_world_experiment():
    st.markdown('<h1 style="text-align:center;">Real-World Physics Experiment</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;">Use your laptop camera to turn a real physical experiment into measurable data.</p>', unsafe_allow_html=True)

    mode = st.radio(
        "Choose what you want to measure",
        ["Projectile Motion", "Collision"],
        horizontal=True,
        key="real_world_mode"
    )

    st.divider()

    if mode == "Projectile Motion":
        projectile_mode()
    else:
        collision_mode()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Back to Experiments", key="real_world_back", use_container_width=True):
        st.session_state.page = "select"
        st.session_state.experiment = None
        st.query_params.clear()
        st.rerun()
