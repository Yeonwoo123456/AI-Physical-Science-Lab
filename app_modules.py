import os
import json
import math
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])


class PhysicalEnvironment(BaseModel):
    mass: float = Field(default=1.0)
    gravity: float = Field(default=9.81)
    height: float = Field(default=0.0)
    initial_velocity: float = Field(default=0.0)
    launch_angle: float = Field(default=0.0)
    friction: float = Field(default=0.0)
    tension: float = Field(default=0.0)
    elasticity: float = Field(default=1.0)
    air_resistance: float = Field(default=0.0)
    planet_mass: Optional[float] = Field(default=5.972e24)
    planet_radius: Optional[float] = Field(default=6371000.0)


class ExperimentConfig(BaseModel):
    intent: str
    parameters: PhysicalEnvironment
    needs_clarification: bool = False
    clarification_message: Optional[str] = None


class NaturalLanguageParser:

    SYSTEM_INSTRUCTION = """
You are a physics parameter extraction system.

Read the user's sentence carefully and extract ONLY values explicitly stated by the user.

Rules:

1. Convert all values to SI units.
   - g -> kg
   - kg -> kg
   - km/h -> m/s
   - km -> m
   - cm -> m
   - degrees -> degrees

2. NEVER invent or guess a value that the user did not mention.

3. If a value is not mentioned, use these defaults:

mass = 1.0
gravity = 9.81
height = 0.0
initial_velocity = 20.0
launch_angle = 0.0
friction = 0.0
tension = 0.0
elasticity = 1.0
air_resistance = 0.0
planet_mass = 5.972e24
planet_radius = 6371000.0

4. Examples:

"공이 10m 높이에서 40도로 날아가"

height = 10
launch_angle = 40
initial_velocity = 0

Do NOT guess the speed.

"2kg 공을 20m/s로 30도 던져"

mass = 2
initial_velocity = 20
launch_angle = 30

"36km/h로 공을 던져"

initial_velocity = 10

5. Identify the experiment:

projectile:
throwing, launching, flying, projectile, 던지다, 던져, 발사, 날아가다, 포물선

free_fall:
drop, falling, free fall, 낙하, 떨어지다, 떨어뜨리다

slanted_motion:
incline, slope, sliding, 경사, 미끄러지다

6. Do not modify parameters that are not explicitly mentioned.
Use the default value instead.

7. Return ONLY valid JSON.

{
  "intent": "free_fall | projectile | slanted_motion | unknown",
  "parameters": {
    "mass": 1.0,
    "gravity": 9.81,
    "height": 0.0,
    "initial_velocity": 20.0,
    "launch_angle": 0.0,
    "friction": 0.0,
    "tension": 0.0,
    "elasticity": 1.0,
    "air_resistance": 0.0,
    "planet_mass": 5.972e24,
    "planet_radius": 6371000.0
  },
  "needs_clarification": false,
  "clarification_message": null
}
"""

    @classmethod
    def parse(cls, prompt: str) -> Dict[str, Any]:

        try:

            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {
                        "role": "system",
                        "content": cls.SYSTEM_INSTRUCTION
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0
            )

            result = json.loads(
                response.choices[0].message.content
            )

            return result

        except Exception as e:

            return {
                "intent": "unknown",
                "parameters": {},
                "needs_clarification": True,
                "clarification_message": (
                    "The AI could not understand the experiment. "
                    "Please describe the experiment with more specific values."
                )
            }

class CollisionNaturalLanguageParser:
    SYSTEM_INSTRUCTION = """
You are a physics collision parameter extraction system.

Read the user's sentence carefully and extract ONLY values explicitly stated by the user.
Never guess, infer, estimate, or calculate missing values.

Parameters:
- mass1: Object A mass
- mass2: Object B mass
- velocity1: Object A speed
- velocity2: Object B speed
- elasticity: coefficient of restitution

Units:
- g -> kg
- kg -> kg
- mg -> kg
- km/h -> m/s
- m/s -> m/s

Object identification:
- Object A, object 1, first object -> parameter 1
- Object B, object 2, second object -> parameter 2
- When two objects are described in order without labels, the first is Object A and the second is Object B.
- Velocity must be returned as a positive speed magnitude.
- Elasticity must be between 0 and 1.

If a parameter is not explicitly mentioned, return null.

Examples:
"Object A is 4 kg and moving at 8 m/s" -> mass1=4, velocity1=8
"Object B has a mass of 1 kg and speed of 3 m/s" -> mass2=1, velocity2=3
"두 물체가 충돌한다. A는 6kg이고 10m/s로 움직인다." -> mass1=6, velocity1=10
"첫 번째 공은 500g이고 36km/h로 움직인다." -> mass1=0.5, velocity1=10
"탄성계수는 0.8이다." -> elasticity=0.8

Return ONLY valid JSON in this form:
{
  "parameters": {
    "mass1": null,
    "mass2": null,
    "velocity1": null,
    "velocity2": null,
    "elasticity": null
  },
  "needs_clarification": false,
  "clarification_message": null
}
"""

    @classmethod
    def parse(cls, prompt: str) -> Dict[str, Any]:
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": cls.SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {
                "parameters": {},
                "needs_clarification": True,
                "clarification_message": "AI could not understand the collision experiment."
            }


class ValidationResult(BaseModel):
    is_valid: bool
    mode: str
    errors: List[str]
    warnings: List[str]
    validated_params: Dict[str, Any]


class PhysicsValidator:
    EARTH_MASS = 5.972e24
    EARTH_RADIUS = 6371000.0
    G = 6.67430e-11

    @classmethod
    def validate(cls, config: Dict[str, Any]) -> ValidationResult:
        defaults = {
            "mass": 1.0,
            "gravity": 9.81,
            "height": 0.0,
            "initial_velocity": 0.0,
            "launch_angle": 0.0,
            "friction": 0.0,
            "tension": 0.0,
            "elasticity": 1.0,
            "air_resistance": 0.0,
            "planet_mass": cls.EARTH_MASS,
            "planet_radius": cls.EARTH_RADIUS
        }

        params = {**defaults, **config.get("parameters", {})}
        errors = []
        warnings = []
        mode = "Realistic Mode"

        checks = [
            (params["mass"] <= 0, "Mass must be greater than 0 kg."),
            (params["gravity"] < 0, "Gravity cannot be negative."),
            (params["height"] < 0, "Height cannot be negative."),
            (params["initial_velocity"] < 0, "Velocity cannot be negative."),
            (params["friction"] < 0, "Friction cannot be negative."),
            (params["tension"] < 0, "Tension cannot be negative."),
            (params["air_resistance"] < 0, "Air resistance cannot be negative."),
            (params["planet_mass"] <= 0, "Planet mass must be greater than 0 kg."),
            (params["planet_radius"] <= 0, "Planet radius must be greater than 0 m."),
            (
                not 0 <= params["elasticity"] <= 1,
                "Elasticity must be between 0 and 1."
            )
        ]

        errors.extend(message for invalid, message in checks if invalid)

        if errors:
            return ValidationResult(
                is_valid=False,
                mode="Invalid",
                errors=errors,
                warnings=warnings,
                validated_params=params
            )

        if (
            params["planet_mass"] != cls.EARTH_MASS
            or params["planet_radius"] != cls.EARTH_RADIUS
        ):
            mode = "Hypothetical Mode"
            params["gravity"] = (
                cls.G * params["planet_mass"] / params["planet_radius"] ** 2
            )
            warnings.append(
                f"Surface gravity recalculated: {params['gravity']:.4f} m/s²."
            )

        if abs(params["gravity"] - 9.81) > 0.1:
            mode = "Hypothetical Mode"
            warnings.append(
                f"Non-standard gravity detected: {params['gravity']} m/s²."
            )

        if params["friction"] > 1:
            mode = "Hypothetical Mode"
            warnings.append("Friction coefficient is greater than 1.")

        if params["initial_velocity"] > 3e8:
            mode = "Hypothetical Mode"
            warnings.append(
                "Velocity exceeds the speed of light. Relativistic effects are ignored."
            )

        if params["planet_radius"] < 100:
            mode = "Hypothetical Mode"
            warnings.append(
                "Extremely small planetary radius detected."
            )

        return ValidationResult(
            is_valid=True,
            mode=mode,
            errors=[],
            warnings=warnings,
            validated_params=params
        )


class PhysicalObject(BaseModel):
    mass: float = 1.0
    position: List[float] = [0.0, 0.0]
    velocity: List[float] = [0.0, 0.0]
    acceleration: List[float] = [0.0, 0.0]


class PhysicsEngine:
    G = 6.67430e-11

    def __init__(self, dt=0.01, solver="rk4"):
        self.dt = dt
        self.solver = solver.lower()

    def _forces(self, obj, p, spring_k=0, rest_len=0):
        m = obj.mass
        g = p.get("gravity", 9.81)
        mu = p.get("friction", 0)
        drag = p.get("air_resistance", 0)
        tension = p.get("tension", 0)

        vx, vy = obj.velocity
        speed = math.hypot(vx, vy)

        fx = -tension if vx > 0 else tension if vx < 0 else 0
        fy = -m * g

        if speed and drag:
            f = 0.5 * drag * speed ** 2
            fx -= f * vx / speed
            fy -= f * vy / speed

        if obj.position[1] <= 0 and abs(vx) > 0 and mu > 0:
            friction = min(mu * m * g, abs(vx) * m / self.dt)
            fx -= friction * (1 if vx > 0 else -1)

        if spring_k:
            fx -= spring_k * (obj.position[0] - rest_len)

        return fx, fy

    def _acceleration(self, position, velocity, mass, p, spring_k, rest_len):
        temp = PhysicalObject(
            mass=mass,
            position=list(position),
            velocity=list(velocity)
        )
        fx, fy = self._forces(temp, p, spring_k, rest_len)
        return [fx / mass, fy / mass]

    def _step_euler(self, obj, p, k, rest):
        ax, ay = self._acceleration(
            obj.position, obj.velocity, obj.mass, p, k, rest
        )

        obj.position[0] += obj.velocity[0] * self.dt
        obj.position[1] += obj.velocity[1] * self.dt
        obj.velocity[0] += ax * self.dt
        obj.velocity[1] += ay * self.dt
        obj.acceleration = [ax, ay]

    def _step_verlet(self, obj, p, k, rest):
        ax, ay = self._acceleration(
            obj.position, obj.velocity, obj.mass, p, k, rest
        )

        obj.position[0] += (
            obj.velocity[0] * self.dt
            + 0.5 * ax * self.dt ** 2
        )

        obj.position[1] += (
            obj.velocity[1] * self.dt
            + 0.5 * ay * self.dt ** 2
        )

        new_ax, new_ay = self._acceleration(
            obj.position, obj.velocity, obj.mass, p, k, rest
        )

        obj.velocity[0] += 0.5 * (ax + new_ax) * self.dt
        obj.velocity[1] += 0.5 * (ay + new_ay) * self.dt
        obj.acceleration = [new_ax, new_ay]

    def _step_rk4(self, obj, p, k, rest):
        m = obj.mass
        dt = self.dt
        p0 = list(obj.position)
        v0 = list(obj.velocity)

        def f(pos, vel):
            acc = self._acceleration(pos, vel, m, p, k, rest)
            return vel, acc

        dp1, dv1 = f(p0, v0)

        p1 = [p0[i] + dt * dp1[i] / 2 for i in range(2)]
        v1 = [v0[i] + dt * dv1[i] / 2 for i in range(2)]
        dp2, dv2 = f(p1, v1)

        p2 = [p0[i] + dt * dp2[i] / 2 for i in range(2)]
        v2 = [v0[i] + dt * dv2[i] / 2 for i in range(2)]
        dp3, dv3 = f(p2, v2)

        p3 = [p0[i] + dt * dp3[i] for i in range(2)]
        v3 = [v0[i] + dt * dv3[i] for i in range(2)]
        dp4, dv4 = f(p3, v3)

        obj.position = [
            p0[i] + dt / 6 * (
                dp1[i] + 2 * dp2[i] + 2 * dp3[i] + dp4[i]
            )
            for i in range(2)
        ]

        obj.velocity = [
            v0[i] + dt / 6 * (
                dv1[i] + 2 * dv2[i] + 2 * dv3[i] + dv4[i]
            )
            for i in range(2)
        ]

        obj.acceleration = dv4

    def _collision(self, obj, elasticity):
        if obj.position[1] <= 0:
            obj.position[1] = 0

            if obj.velocity[1] < 0:
                obj.velocity[1] *= -elasticity

    def simulate(
        self,
        validation_result,
        total_time=5.0,
        spring_k=0.0,
        spring_rest_len=0.0
    ):
        if not validation_result.is_valid:
            return {
                "status": "error",
                "errors": validation_result.errors,
                "trajectory": []
            }

        p = validation_result.validated_params
        angle = math.radians(p["launch_angle"])
        v = p["initial_velocity"]

        obj = PhysicalObject(
            mass=p["mass"],
            position=[0, p["height"]],
            velocity=[
                v * math.cos(angle),
                v * math.sin(angle)
            ]
        )

        trajectory = []

        for i in range(int(total_time / self.dt)):
            t = i * self.dt
            vx, vy = obj.velocity
            speed = math.hypot(vx, vy)

            ke = 0.5 * obj.mass * speed ** 2
            pe = obj.mass * p["gravity"] * max(obj.position[1], 0)
            fx, fy = self._forces(
                obj, p, spring_k, spring_rest_len
            )

            trajectory.append({
                "time": round(t, 4),
                "x": round(obj.position[0], 4),
                "y": round(obj.position[1], 4),
                "vx": round(vx, 4),
                "vy": round(vy, 4),
                "fx": round(fx, 4),
                "fy": round(fy, 4),
                "ke": round(ke, 4),
                "pe": round(pe, 4),
                "total_e": round(ke + pe, 4),
                "momentum": [
                    round(obj.mass * vx, 4),
                    round(obj.mass * vy, 4)
                ]
            })

            if self.solver == "euler":
                self._step_euler(
                    obj, p, spring_k, spring_rest_len
                )
            elif self.solver == "verlet":
                self._step_verlet(
                    obj, p, spring_k, spring_rest_len
                )
            else:
                self._step_rk4(
                    obj, p, spring_k, spring_rest_len
                )

            self._collision(
                obj,
                p["elasticity"]
            )

        return {
            "status": "success",
            "solver_used": self.solver,
            "mode": validation_result.mode,
            "warnings": validation_result.warnings,
            "total_frames": len(trajectory),
            "trajectory": trajectory,
            "final_state": trajectory[-1]
        }
