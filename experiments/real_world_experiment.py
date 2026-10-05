import threading
from collections import deque

import av
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_webrtc import VideoProcessorBase, WebRtcMode, webrtc_streamer



class ProjectileProcessor(VideoProcessorBase):
    def __init__(self):
        self.positions = deque(maxlen=3000)
        self.start_time = None
        self.lock = threading.Lock()
        self.pixels_per_meter = 300.0

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        lower = np.array([0, 100, 80])
        upper = np.array([25, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:
            contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(contour)

            if area > 150:
                x, y, w, h = cv2.boundingRect(contour)
                cx = x + w / 2
                cy = y + h / 2

                if self.start_time is None:
                    self.start_time = pd.Timestamp.now().timestamp()

                t = pd.Timestamp.now().timestamp() - self.start_time

                with self.lock:
                    self.positions.append((t, cx, cy))

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

    def get_data(self):
        with self.lock:
            return list(self.positions)

    def clear(self):
        with self.lock:
            self.positions.clear()
        self.start_time = None


class CollisionProcessor(VideoProcessorBase):
    def __init__(self):
        self.records = deque(maxlen=3000)
        self.start_time = None
        self.lock = threading.Lock()

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        red1 = cv2.inRange(
            hsv,
            np.array([0, 100, 80]),
            np.array([10, 255, 255])
        )
        red2 = cv2.inRange(
            hsv,
            np.array([170, 100, 80]),
            np.array([179, 255, 255])
        )
        red_mask = red1 | red2

        blue_mask = cv2.inRange(
            hsv,
            np.array([90, 100, 80]),
            np.array([135, 255, 255])
        )

        red_center = self._find_center(red_mask)
        blue_center = self._find_center(blue_mask)

        if red_center is not None and blue_center is not None:
            if self.start_time is None:
                self.start_time = pd.Timestamp.now().timestamp()

            t = pd.Timestamp.now().timestamp() - self.start_time
            red_x = red_center[0]
            blue_x = blue_center[0]
            distance = abs(red_x - blue_x)

            with self.lock:
                self.records.append(
                    (t, red_x, blue_x, distance)
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

    @staticmethod
    def _find_center(mask):
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        contour = max(contours, key=cv2.contourArea)

        if cv2.contourArea(contour) < 150:
            return None

        m = cv2.moments(contour)
        if m["m00"] == 0:
            return None

        return (
            m["m10"] / m["m00"],
            m["m01"] / m["m00"]
        )

    def get_data(self):
        with self.lock:
            return list(self.records)

    def clear(self):
        with self.lock:
            self.records.clear()
        self.start_time = None



def analyze_projectile(data, pixels_per_meter):
    if len(data) < 5:
        return None

    df = pd.DataFrame(
        data,
        columns=["time", "x_px", "y_px"]
    )

    df["x"] = df["x_px"] / pixels_per_meter
    df["y"] = -df["y_px"] / pixels_per_meter

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

    ctx = webrtc_streamer(
        key="real-world-projectile",
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={
            "video": True,
            "audio": False
        },
        video_processor_factory=ProjectileProcessor,
        async_processing=True
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Analyze Projectile Motion", key="rw_projectile_analyze"):
            if ctx.video_processor:
                data = ctx.video_processor.get_data()
                df = analyze_projectile(
                    data,
                    pixels_per_meter
                )

                if df is None:
                    st.warning("Not enough motion data yet.")
                else:
                    st.session_state.real_projectile_data = df

    with col2:
        if st.button("Clear Data", key="rw_projectile_clear"):
            if ctx.video_processor:
                ctx.video_processor.clear()
            st.session_state.pop("real_projectile_data", None)
            st.rerun()

    df = st.session_state.get("real_projectile_data")

    if df is not None:
        st.markdown('<h3 style="text-align:center;">Motion Data</h3>', unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Flight Time", f"{df['time'].iloc[-1]:.2f} s")
        m2.metric("Max Height", f"{df['y'].max():.2f} m")
        m3.metric("Max Speed", f"{df['speed'].max():.2f} m/s")
        m4.metric("Samples", len(df))

        st.markdown("#### Position")
        st.line_chart(
            df.set_index("time")[["x", "y"]]
        )

        st.markdown("#### Velocity")
        st.line_chart(
            df.set_index("time")[["vx", "vy", "speed"]]
        )

        st.markdown("#### Acceleration")
        st.line_chart(
            df.set_index("time")[["ax", "ay"]]
        )

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

    ctx = webrtc_streamer(
        key="real-world-collision",
        mode=WebRtcMode.SENDRECV,
        media_stream_constraints={
            "video": True,
            "audio": False
        },
        video_processor_factory=CollisionProcessor,
        async_processing=True
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Analyze Collision", key="rw_collision_analyze"):
            if ctx.video_processor:
                data = ctx.video_processor.get_data()
                df = analyze_collision(
                    data,
                    pixels_per_meter,
                    mass_red,
                    mass_blue
                )

                if df is None:
                    st.warning("Not enough collision data yet.")
                else:
                    st.session_state.real_collision_data = df

    with col2:
        if st.button("Clear Data", key="rw_collision_clear"):
            if ctx.video_processor:
                ctx.video_processor.clear()
            st.session_state.pop("real_collision_data", None)
            st.rerun()

    df = st.session_state.get("real_collision_data")

    if df is not None:
        st.markdown('<h3 style="text-align:center;">Collision Data</h3>', unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Initial Distance", f"{df['distance'].iloc[0]:.2f} m")
        m2.metric("Minimum Distance", f"{df['distance'].min():.2f} m")
        m3.metric("Samples", len(df))

        st.markdown("#### Object Velocity")
        st.line_chart(
            df.set_index("time")[["red_v", "blue_v"]]
        )

        st.markdown("#### Total Momentum")
        st.line_chart(
            df.set_index("time")[["momentum"]]
        )

        st.markdown("#### Kinetic Energy")
        st.line_chart(
            df.set_index("time")[["kinetic_energy"]]
        )

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

    st.markdown('<p style="text-align:center;">Choose what you want to measure</p>', unsafe_allow_html=True)

    mode = st.radio(
        "",
        [
            "Projectile Motion",
            "Collision"
        ],
        horizontal=True,
        key="real_world_mode"
    )

    st.divider()

    if mode == "Projectile Motion":
        projectile_mode()
    else:
        collision_mode()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Back to Experiments", key="real_world_back"):
        st.session_state.page = "select"
        st.session_state.experiment = None
        st.query_params.clear()
        st.rerun()
