import os
import json
import math
import re
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

    DEFAULTS = {
        "mass": 1.0,
        "gravity": 9.81,
        "height": 0.0,
        "initial_velocity": 0.0,
        "launch_angle": 0.0,
        "friction": 0.0,
        "tension": 0.0,
        "elasticity": 1.0,
        "air_resistance": 0.0,
        "planet_mass": 5.972e24,
        "planet_radius": 6371000.0
    }

    SYSTEM_INSTRUCTION = """
You are a physics experiment interpretation assistant.

Your job is to understand the user's physics experiment and return structured JSON.

IMPORTANT RULES:

1. Extract values explicitly mentioned by the user.
2. Convert units to SI units.
3. NEVER invent or guess a value that the user did not mention.
4. If a parameter is not mentioned, use the provided default value.
5. Identify the experiment intent:
   - free_fall
   - projectile
   - slanted_motion
   - unknown

Parameter meanings:

mass:
kg

gravity:
m/s^2

height:
m

initial_velocity:
m/s

launch_angle:
degrees

friction:
coefficient of friction

tension:
N

elasticity:
0 to 1

air_resistance:
coefficient

planet_mass:
kg

planet_radius:
m

Examples:

"Throw a ball at 20 m/s from 10 meters at 40 degrees"

means:

initial_velocity = 20
height = 10
launch_angle = 40

"공이 10m 높이에서 40도로 날아가"

means:

height = 10
launch_angle = 40

initial_velocity was NOT specified,
so initial_velocity must remain 0.

"공을 2kg 질량으로 25m/s의 속도로 30도 방향으로 던진다"

means:

mass = 2
initial_velocity = 25
launch_angle = 30

"속도 36km/h"

means:

initial_velocity = 10

because 36 km/h = 10 m/s.

Return ONLY valid JSON.

Schema:

{
    "intent": "free_fall | projectile | slanted_motion | unknown",
    "parameters": {
        "mass": 1.0,
        "gravity": 9.81,
        "height": 0.0,
        "initial_velocity": 0.0,
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

    @staticmethod
    def _number(text):
        match = re.search(
            r"[-+]?\d+(?:\.\d+)?",
            text.replace(",", "")
        )

        if not match:
            return None

        try:
            return float(match.group())
        except ValueError:
            return None

    @classmethod
    def _extract_explicit_parameters(cls, prompt):

        text = prompt.lower()
        text = text.replace(",", "")

        params = {}

        # -------------------------------------------------
        # HEIGHT
        # -------------------------------------------------

        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:m|meter|meters|미터)\s*(?:높이|높은|위)",
            r"(?:height|높이)\s*(?:가|은|는|:)?\s*(\d+(?:\.\d+)?)\s*(?:m|meter|meters|미터)?",
            r"(?:from|at)\s*(\d+(?:\.\d+)?)\s*(?:m|meter|meters|미터)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                params["height"] = float(match.group(1))
                break

        # -------------------------------------------------
        # LAUNCH ANGLE
        # -------------------------------------------------

        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:도|degrees?|degree)",
            r"(?:angle|각도)\s*(?:가|은|는|:)?\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:deg)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                params["launch_angle"] = float(match.group(1))
                break

        # -------------------------------------------------
        # VELOCITY - m/s
        # -------------------------------------------------

        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:m/s|mps|m/sec|미터/초)",
            r"(?:속도|speed|velocity)\s*(?:가|은|는|:)?\s*(\d+(?:\.\d+)?)\s*(?:m/s|mps|m/sec)?"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                params["initial_velocity"] = float(match.group(1))
                break

        # -------------------------------------------------
        # VELOCITY - km/h
        # -------------------------------------------------

        if "initial_velocity" not in params:

            patterns = [
                r"(\d+(?:\.\d+)?)\s*(?:km/h|kmh)",
                r"(?:시속)\s*(\d+(?:\.\d+)?)"
            ]

            for pattern in patterns:
                match = re.search(pattern, text)

                if match:
                    kmh = float(match.group(1))
                    params["initial_velocity"] = kmh / 3.6
                    break

        # -------------------------------------------------
        # MASS
        # -------------------------------------------------

        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:kg|kilograms?|킬로그램)",
            r"(?:mass|질량)\s*(?:가|은|는|:)?\s*(\d+(?:\.\d+)?)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                params["mass"] = float(match.group(1))
                break

        # -------------------------------------------------
        # GRAVITY
        # -------------------------------------------------

        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:m/s\^?2|m/s²|m/s2)\s*(?:중력|gravity)?",
            r"(?:gravity|중력)\s*(?:가|은|는|:)?\s*(\d+(?:\.\d+)?)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                params["gravity"] = float(match.group(1))
                break

        # -------------------------------------------------
        # FRICTION
        # -------------------------------------------------

        patterns = [
            r"(?:friction|마찰계수|마찰)\s*(?:가|은|는|:)?\s*(\d+(?:\.\d+)?)",
            r"(?:mu|μ)\s*=?\s*(\d+(?:\.\d+)?)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                params["friction"] = float(match.group(1))
                break

        # -------------------------------------------------
        # ELASTICITY
        # -------------------------------------------------

        patterns = [
            r"(?:elasticity|탄성계수|반발계수)\s*(?:가|은|는|:)?\s*(\d+(?:\.\d+)?)",
            r"(?:e)\s*=\s*(\d+(?:\.\d+)?)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                params["elasticity"] = float(match.group(1))
                break

        # -------------------------------------------------
        # AIR RESISTANCE
        # -------------------------------------------------

        patterns = [
            r"(?:air resistance|공기저항)\s*(?:가|은|는|:)?\s*(\d+(?:\.\d+)?)",
            r"(?:drag|저항계수)\s*(?:가|은|는|:)?\s*(\d+(?:\.\d+)?)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                params["air_resistance"] = float(match.group(1))
                break

        return params

    @classmethod
    def _detect_intent(cls, prompt):

        text = prompt.lower()

        projectile_words = [
            "projectile",
            "projectile motion",
            "throw",
            "thrown",
            "launch",
            "launched",
            "shoot",
            "shot",
            "fly",
            "flies",
            "날아",
            "던져",
            "던진",
            "발사",
            "쏘",
            "포물선"
        ]

        free_fall_words = [
            "free fall",
            "freefall",
            "drop",
            "dropped",
            "낙하",
            "떨어",
            "떨어뜨"
        ]

        slanted_words = [
            "incline",
            "inclined",
            "slope",
            "sliding",
            "slide",
            "경사",
            "미끄러"
        ]

        if any(word in text for word in projectile_words):
            return "projectile"

        if any(word in text for word in free_fall_words):
            return "free_fall"

        if any(word in text for word in slanted_words):
            return "slanted_motion"

        return "unknown"

    @classmethod
    def parse(cls, prompt):

        explicit_params = cls._extract_explicit_parameters(prompt)
        detected_intent = cls._detect_intent(prompt)

        ai_result = {}

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
                temperature=0.0
            )

            content = response.choices[0].message.content

            if content:
                ai_result = json.loads(content)

        except Exception:
            ai_result = {}

        # -------------------------------------------------
        # START WITH SAFE DEFAULTS
        # -------------------------------------------------

        final_params = cls.DEFAULTS.copy()

        # -------------------------------------------------
        # APPLY AI RESULT
        # -------------------------------------------------

        ai_params = ai_result.get("parameters", {})

        if isinstance(ai_params, dict):

            for key in final_params:

                value = ai_params.get(key)

                if isinstance(value, (int, float)):
                    final_params[key] = float(value)

        # -------------------------------------------------
        # EXPLICIT VALUES ALWAYS OVERRIDE AI
        # -------------------------------------------------

        for key, value in explicit_params.items():
            final_params[key] = value

        # -------------------------------------------------
        # INTENT
        # -------------------------------------------------

        ai_intent = ai_result.get("intent", "unknown")

        if detected_intent != "unknown":
            intent = detected_intent
        elif ai_intent in [
            "free_fall",
            "projectile",
            "slanted_motion"
        ]:
            intent = ai_intent
        else:
            intent = "unknown"

        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        return {
            "intent": intent,
            "parameters": final_params,
            "needs_clarification": False,
            "clarification_message": None
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
