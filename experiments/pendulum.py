import math
import numpy as np
import streamlit as st
import plotly.graph_objects as go


class PendulumPhysics:

    def __init__(
        self,
        length=2.0,
        mass=1.0,
        gravity=9.81,
        initial_angle=45.0,
        damping=0.02
    ):
        self.length = float(length)
        self.mass = float(mass)
        self.gravity = float(gravity)
        self.theta = math.radians(float(initial_angle))
        self.omega = 0.0
        self.damping = float(damping)

    def angular_acceleration(self, theta, omega):
        return (
            -(self.gravity / self.length) * math.sin(theta)
            - self.damping * omega
        )

    def rk4_step(self, dt):
        theta = self.theta
        omega = self.omega

        k1_theta = omega
        k1_omega = self.angular_acceleration(theta, omega)

        theta2 = theta + 0.5 * dt * k1_theta
        omega2 = omega + 0.5 * dt * k1_omega

        k2_theta = omega2
        k2_omega = self.angular_acceleration(theta2, omega2)

        theta3 = theta + 0.5 * dt * k2_theta
        omega3 = omega + 0.5 * dt * k2_omega

        k3_theta = omega3
        k3_omega = self.angular_acceleration(theta3, omega3)

        theta4 = theta + dt * k3_theta
        omega4 = omega + dt * k3_omega

        k4_theta = omega4
        k4_omega = self.angular_acceleration(theta4, omega4)

        self.theta += (
            dt / 6.0
            * (
                k1_theta
                + 2 * k2_theta
                + 2 * k3_theta
                + k4_theta
            )
        )

        self.omega += (
            dt / 6.0
            * (
                k1_omega
                + 2 * k2_omega
                + 2 * k3_omega
                + k4_omega
            )
        )

    def position(self):
        x = self.length * math.sin(self.theta)
        y = -self.length * math.cos(self.theta)
        return x, y

    def velocity(self):
        return abs(self.length * self.omega)

    def current_angular_acceleration(self):
        return self.angular_acceleration(
            self.theta,
            self.omega
        )

    def tension(self):
        v = self.velocity()

        return self.mass * (
            (v ** 2) / self.length
            + self.gravity * math.cos(self.theta)
        )

    def kinetic_energy(self):
        v = self.velocity()
        return 0.5 * self.mass * v ** 2

    def potential_energy(self):
        return (
            self.mass
            * self.gravity
            * self.length
            * (1 - math.cos(self.theta))
        )

    def total_energy(self):
        return (
            self.kinetic_energy()
            + self.potential_energy()
        )

    def theoretical_period(self):
        return (
            2
            * math.pi
            * math.sqrt(
                self.length / self.gravity
            )
        )

    def state(self):
        x, y = self.position()

        return {
            "theta": self.theta,
            "angle_degrees": math.degrees(self.theta),
            "omega": self.omega,
            "angular_acceleration":
                self.current_angular_acceleration(),
            "x": x,
            "y": y,
            "velocity": self.velocity(),
            "tension": self.tension(),
            "kinetic_energy": self.kinetic_energy(),
            "potential_energy": self.potential_energy(),
            "total_energy": self.total_energy()
        }


def simulate_pendulum(
    length,
    mass,
    gravity,
    initial_angle,
    damping,
    duration=10.0,
    dt=0.01
):
    pendulum = PendulumPhysics(
        length=length,
        mass=mass,
        gravity=gravity,
        initial_angle=initial_angle,
        damping=damping
    )

    time = []
    angle = []
    angular_velocity = []
    angular_acceleration = []
    x = []
    y = []
    velocity = []
    tension = []
    kinetic_energy = []
    potential_energy = []
    total_energy = []

    steps = int(duration / dt)

    for i in range(steps + 1):
        current_time = i * dt
        state = pendulum.state()

        time.append(current_time)
        angle.append(state["angle_degrees"])
        angular_velocity.append(state["omega"])
        angular_acceleration.append(
            state["angular_acceleration"]
        )
        x.append(state["x"])
        y.append(state["y"])
        velocity.append(state["velocity"])
        tension.append(state["tension"])
        kinetic_energy.append(state["kinetic_energy"])
        potential_energy.append(state["potential_energy"])
        total_energy.append(state["total_energy"])

        pendulum.rk4_step(dt)

    return {
        "time": np.array(time),
        "angle": np.array(angle),
        "angular_velocity": np.array(angular_velocity),
        "angular_acceleration": np.array(
            angular_acceleration
        ),
        "x": np.array(x),
        "y": np.array(y),
        "velocity": np.array(velocity),
        "tension": np.array(tension),
        "kinetic_energy": np.array(kinetic_energy),
        "potential_energy": np.array(potential_energy),
        "total_energy": np.array(total_energy),
        "period": pendulum.theoretical_period()
    }


def create_pendulum_figure(
    result,
    frame_index=0,
    show_vector=True
):
    x = result["x"][frame_index]
    y = result["y"][frame_index]

    length = math.sqrt(x ** 2 + y ** 2)
    angle = result["angle"][frame_index]
    velocity = result["velocity"][frame_index]

    fig = go.Figure()

    ground_size = max(3.0, length * 1.5)

    fig.add_trace(
        go.Scatter3d(
            x=[-ground_size, ground_size],
            y=[-length, -length],
            z=[0, 0],
            mode="lines",
            line=dict(
                width=2,
                color="rgba(150,150,150,0.35)"
            ),
            showlegend=False
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[0, x],
            y=[0, y],
            z=[0, 0],
            mode="lines",
            line=dict(
                width=8,
                color="#D1D5DB"
            ),
            name="Rod",
            hovertemplate=(
                "Rod<br>"
                "Length: %{customdata:.2f} m"
                "<extra></extra>"
            ),
            customdata=[length, length]
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[0],
            y=[0],
            z=[0],
            mode="markers",
            marker=dict(
                size=10,
                color="#FFFFFF"
            ),
            name="Pivot"
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[x],
            y=[y],
            z=[0],
            mode="markers",
            marker=dict(
                size=16,
                color="#F6D77A",
                line=dict(
                    width=2,
                    color="#FFFFFF"
                )
            ),
            name="Bob",
            hovertemplate=(
                "Time: %{customdata[0]:.2f} s<br>"
                "Angle: %{customdata[1]:.2f}°<br>"
                "Velocity: %{customdata[2]:.2f} m/s"
                "<extra></extra>"
            ),
            customdata=[
                [
                    result["time"][frame_index],
                    angle,
                    velocity
                ]
            ]
        )
    )

    if show_vector:
        angular_velocity = (
            result["angular_velocity"][frame_index]
        )

        vx = (
            angular_velocity
            * length
            * math.cos(angle * math.pi / 180)
        )

        vy = (
            -angular_velocity
            * length
            * math.sin(angle * math.pi / 180)
        )

        vector_scale = 0.3

        fig.add_trace(
            go.Scatter3d(
                x=[
                    x,
                    x + vx * vector_scale
                ],
                y=[
                    y,
                    y + vy * vector_scale
                ],
                z=[0, 0],
                mode="lines+markers",
                line=dict(
                    width=6,
                    color="#60A5FA"
                ),
                marker=dict(size=4),
                name="Velocity",
                hovertemplate=(
                    "Angular Velocity: "
                    "%{customdata:.2f} rad/s"
                    "<extra></extra>"
                ),
                customdata=[
                    angular_velocity,
                    angular_velocity
                ]
            )
        )

    fig.update_layout(
        height=620,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),
        scene=dict(
            xaxis=dict(
                title="X",
                backgroundcolor="#0d1117",
                gridcolor="#30363d",
                zerolinecolor="#505862"
            ),
            yaxis=dict(
                title="Y",
                backgroundcolor="#0d1117",
                gridcolor="#30363d",
                zerolinecolor="#505862"
            ),
            zaxis=dict(
                title="Z",
                backgroundcolor="#0d1117",
                gridcolor="#30363d",
                zerolinecolor="#505862"
            ),
            aspectmode="cube",
            camera=dict(
                eye=dict(
                    x=1.4,
                    y=1.4,
                    z=0.9
                )
            )
        ),
        paper_bgcolor="#0d1117",
        font=dict(color="#FFFFFF"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)"
        )
    )

    return fig


def create_angle_graph(result):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=result["time"],
            y=result["angle"],
            mode="lines",
            name="Angle",
            hovertemplate=(
                "Time: %{x:.2f} s<br>"
                "Angle: %{y:.2f}°"
                "<extra></extra>"
            )
        )
    )

    fig.update_layout(
        title="Angular Position",
        xaxis_title="Time (s)",
        yaxis_title="Angle (°)",
        height=350,
        hovermode="closest"
    )

    return fig


def create_energy_graph(result):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=result["time"],
            y=result["kinetic_energy"],
            mode="lines",
            name="Kinetic Energy",
            hovertemplate=(
                "Time: %{x:.2f} s<br>"
                "Kinetic Energy: %{y:.4f} J"
                "<extra></extra>"
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=result["time"],
            y=result["potential_energy"],
            mode="lines",
            name="Potential Energy",
            hovertemplate=(
                "Time: %{x:.2f} s<br>"
                "Potential Energy: %{y:.4f} J"
                "<extra></extra>"
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=result["time"],
            y=result["total_energy"],
            mode="lines",
            name="Total Energy",
            hovertemplate=(
                "Time: %{x:.2f} s<br>"
                "Total Energy: %{y:.4f} J"
                "<extra></extra>"
            )
        )
    )

    fig.update_layout(
        title="Energy",
        xaxis_title="Time (s)",
        yaxis_title="Energy (J)",
        height=350,
        hovermode="closest"
    )

    return fig


def pendulum_experiment():

    st.title("Pendulum")

    st.caption(
        "Explore how length, gravity, angle, mass, "
        "and damping affect pendulum motion."
    )

    left, right = st.columns(2)

    with left:
        length = st.slider(
            "Length (m)",
            min_value=0.1,
            max_value=10.0,
            value=2.0,
            step=0.1
        )

        mass = st.slider(
            "Mass (kg)",
            min_value=0.1,
            max_value=20.0,
            value=1.0,
            step=0.1
        )

        gravity = st.number_input(
            "Gravity (m/s²)",
            min_value=0.01,
            max_value=1000.0,
            value=9.81,
            step=0.1
        )

    with right:
        initial_angle = st.slider(
            "Initial Angle (°)",
            min_value=-89.0,
            max_value=89.0,
            value=45.0,
            step=1.0
        )

        damping = st.slider(
            "Damping",
            min_value=0.0,
            max_value=1.0,
            value=0.02,
            step=0.01
        )

    duration = st.slider(
        "Simulation Time (s)",
        min_value=1.0,
        max_value=60.0,
        value=10.0,
        step=1.0
    )

    st.divider()

    if st.button(
        "▶ Run Pendulum Experiment",
        type="primary",
        use_container_width=True
    ):
        result = simulate_pendulum(
            length=length,
            mass=mass,
            gravity=gravity,
            initial_angle=initial_angle,
            damping=damping,
            duration=duration,
            dt=0.01
        )

        st.session_state["pendulum_result"] = result

    if "pendulum_result" not in st.session_state:
        st.info(
            "Set the parameters and run the experiment."
        )
        return

    result = st.session_state["pendulum_result"]

    st.subheader("3D Simulation")

    frame_slider = st.slider(
        "Simulation Time",
        min_value=0,
        max_value=len(result["time"]) - 1,
        value=0,
        format="Frame %d"
    )

    current_time = result["time"][frame_slider]

    st.caption(
        f"t = {current_time:.2f} s"
    )

    fig = create_pendulum_figure(
        result,
        frame_index=frame_slider
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    angle = result["angle"][frame_slider]
    omega = result["angular_velocity"][frame_slider]
    velocity = result["velocity"][frame_slider]
    tension = result["tension"][frame_slider]
    energy = result["total_energy"][frame_slider]

    m1, m2, m3, m4, m5 = st.columns(5)

    m1.metric(
        "Angle",
        f"{angle:.2f}°"
    )

    m2.metric(
        "Angular Velocity",
        f"{omega:.2f} rad/s"
    )

    m3.metric(
        "Velocity",
        f"{velocity:.2f} m/s"
    )

    m4.metric(
        "Tension",
        f"{tension:.2f} N"
    )

    m5.metric(
        "Total Energy",
        f"{energy:.2f} J"
    )

    st.divider()

    st.subheader("Analysis")

    tab1, tab2 = st.tabs(
        ["Angle", "Energy"]
    )

    with tab1:
        st.plotly_chart(
            create_angle_graph(result),
            use_container_width=True
        )

    with tab2:
        st.plotly_chart(
            create_energy_graph(result),
            use_container_width=True
        )

    st.divider()

    if st.button("← Back to Experiments"):
        st.session_state.page = "select"
        st.session_state.experiment = None
        st.session_state.pop(
            "pendulum_result",
            None
        )
        st.query_params.clear()
        st.rerun()
