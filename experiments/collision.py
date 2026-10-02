import json
import math
import streamlit as st
import streamlit.components.v1 as components

from app_modules import CollisionNaturalLanguageParser


def collision_experiment():
    defaults = {
        "collision_shape1": "Sphere",
        "collision_shape2": "Cube",
        "collision_mass1": 2.0,
        "collision_mass2": 2.0,
        "collision_velocity1": 5.0,
        "collision_velocity2": 3.0,
        "collision_elasticity": 1.0,
        "collision_speed": 1.0,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.markdown("### AI Experiment Assistant")

    ai_input = st.text_input(
        "Describe your collision experiment",
        placeholder="Example: Object A is 4 kg and moves at 8 m/s. Object B is 1 kg and moves at 3 m/s.",
        key="collision_ai_input",
    )

    if st.button("Run AI Analysis", key="collision_ai_button", type="primary"):
        if not ai_input.strip():
            st.warning("Describe a collision experiment first.")
        else:
            with st.spinner("AI is analyzing your experiment..."):
                result = CollisionNaturalLanguageParser.parse(ai_input)

            if result.get("needs_clarification") and not result.get("parameters"):
                st.warning(
                    result.get(
                        "clarification_message",
                        "Please describe the values more specifically.",
                    )
                )
            else:
                parameters = result.get("parameters", {})
                mapping = {
                    "mass1": "collision_mass1",
                    "mass2": "collision_mass2",
                    "velocity1": "collision_velocity1",
                    "velocity2": "collision_velocity2",
                    "elasticity": "collision_elasticity",
                }
                limits = {
                    "mass1": (0.01, 1000.0),
                    "mass2": (0.01, 1000.0),
                    "velocity1": (0.0, 100.0),
                    "velocity2": (0.0, 100.0),
                    "elasticity": (0.0, 1.0),
                }
                applied = []
                ignored = []

                for parameter, session_key in mapping.items():
                    value = parameters.get(parameter)
                    if value is None:
                        continue
                    try:
                        value = float(value)
                    except (TypeError, ValueError):
                        ignored.append(parameter)
                        continue

                    minimum, maximum = limits[parameter]
                    if minimum <= value <= maximum:
                        st.session_state[session_key] = value
                        applied.append(parameter)
                    else:
                        ignored.append(parameter)

                if applied:
                    st.success("AI analysis completed. Mentioned values were applied.")
                elif ignored:
                    st.warning("The detected values were outside the allowed ranges.")
                else:
                    st.info("No collision values were explicitly mentioned, so the current values were kept.")

    st.markdown("### Collision Setup")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Object A**")
        st.selectbox(
            "Shape",
            ["Sphere", "Cube"],
            key="collision_shape1",
        )
        st.number_input(
            "Mass (kg)",
            min_value=0.01,
            max_value=1000.0,
            step=0.01,
            format="%.2f",
            key="collision_mass1",
        )
        st.number_input(
            "Velocity (m/s)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.2f",
            key="collision_velocity1",
        )

    with col2:
        st.markdown("**Object B**")
        st.selectbox(
            "Shape",
            ["Sphere", "Cube"],
            key="collision_shape2",
        )
        st.number_input(
            "Mass (kg)",
            min_value=0.01,
            max_value=1000.0,
            step=0.01,
            format="%.2f",
            key="collision_mass2",
        )
        st.number_input(
            "Velocity (m/s)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.2f",
            key="collision_velocity2",
        )

    st.number_input(
        "Coefficient of Restitution",
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        format="%.2f",
        key="collision_elasticity",
    )

    st.select_slider(
        "Animation Speed",
        options=[0.25, 0.5, 1.0, 1.5, 2.0],
        format_func=lambda x: f"{x:.2f}x",
        key="collision_speed",
    )

    mass1 = float(st.session_state.collision_mass1)
    mass2 = float(st.session_state.collision_mass2)
    velocity1 = float(st.session_state.collision_velocity1)
    velocity2 = float(st.session_state.collision_velocity2)
    elasticity = float(st.session_state.collision_elasticity)
    shape1 = st.session_state.collision_shape1
    shape2 = st.session_state.collision_shape2
    animation_speed = float(st.session_state.collision_speed)

    run = st.button("PLAY", key="collision_run", type="primary", use_container_width=True)

    if run:
        positions1, positions2, collision_index, final_v1, final_v2 = simulate_collision(
            mass1,
            mass2,
            velocity1,
            velocity2,
            elasticity,
        )
        render_collision(
            positions1,
            positions2,
            collision_index,
            shape1,
            shape2,
            animation_speed,
        )

        initial_momentum1 = mass1 * velocity1
        initial_momentum2 = -mass2 * velocity2
        final_momentum1 = mass1 * final_v1
        final_momentum2 = mass2 * final_v2
        initial_energy1 = 0.5 * mass1 * velocity1 ** 2
        initial_energy2 = 0.5 * mass2 * velocity2 ** 2
        final_energy1 = 0.5 * mass1 * final_v1 ** 2
        final_energy2 = 0.5 * mass2 * final_v2 ** 2

        st.markdown("### Results")
        st.html(
            f"""
            <style>
                .collision-results {{
                    width: 100%;
                    border-collapse: collapse;
                    table-layout: fixed;
                    font-size: 18px;
                    font-weight: 600;
                }}
                .collision-results th,
                .collision-results td {{
                    text-align: center !important;
                    vertical-align: middle !important;
                    padding: 14px 10px;
                    border: 1px solid #3a3f46;
                }}
                .collision-results th {{
                    font-size: 18px;
                    font-weight: 700;
                }}
                .collision-results td {{
                    font-size: 18px;
                    font-weight: 600;
                }}
                .collision-results th:first-child,
                .collision-results td:first-child {{
                    width: 12%;
                    font-weight: 700;
                }}
            </style>
            <table class="collision-results">
                <thead>
                    <tr>
                        <th>Object</th>
                        <th>Velocity<br>BEFORE</th>
                        <th>Velocity<br>AFTER</th>
                        <th>Momentum<br>BEFORE</th>
                        <th>Momentum<br>AFTER</th>
                        <th>Energy<br>BEFORE</th>
                        <th>Energy<br>AFTER</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Object A</td>
                        <td>{velocity1:.2f} m/s</td>
                        <td>{final_v1:.2f} m/s</td>
                        <td>{initial_momentum1:.2f} kg·m/s</td>
                        <td>{final_momentum1:.2f} kg·m/s</td>
                        <td>{initial_energy1:.2f} J</td>
                        <td>{final_energy1:.2f} J</td>
                    </tr>
                    <tr>
                        <td>Object B</td>
                        <td>{velocity2:.2f} m/s</td>
                        <td>{final_v2:.2f} m/s</td>
                        <td>{initial_momentum2:.2f} kg·m/s</td>
                        <td>{final_momentum2:.2f} kg·m/s</td>
                        <td>{initial_energy2:.2f} J</td>
                        <td>{final_energy2:.2f} J</td>
                    </tr>
                </tbody>
            </table>
            """
        )

    if st.button("Back to Experiments", key="collision_back"):
        keys = [
            "collision_shape1",
            "collision_shape2",
            "collision_mass1",
            "collision_mass2",
            "collision_velocity1",
            "collision_velocity2",
            "collision_elasticity",
            "collision_speed",
            "collision_ai_input",
        ]
        for key in keys:
            st.session_state.pop(key, None)
        st.session_state.page = "experiments"
        st.rerun()


def simulate_collision(mass1, mass2, velocity1, velocity2, elasticity):
    dt = 1 / 240
    total_time = 6.0
    radius = 1.25
    wall_left = -9.0
    wall_right = 9.0
    start1 = -6.0
    start2 = 6.0
    contact_distance = 3.5

    x1 = start1
    x2 = start2
    v1 = velocity1
    v2 = -velocity2
    collision_index = None
    final_v1 = v1
    final_v2 = v2
    cooldown = 0.0

    positions1 = []
    positions2 = []
    steps = int(total_time / dt)

    for i in range(steps):
        positions1.append(x1)
        positions2.append(x2)

        next_x1 = x1 + v1 * dt
        next_x2 = x2 + v2 * dt

        if next_x1 >= wall_right - radius:
            x1 = wall_right - radius
            v1 = 0.0
        elif next_x1 <= wall_left + radius:
            x1 = wall_left + radius
            v1 = 0.0
        else:
            x1 = next_x1

        if next_x2 >= wall_right - radius:
            x2 = wall_right - radius
            v2 = 0.0
        elif next_x2 <= wall_left + radius:
            x2 = wall_left + radius
            v2 = 0.0
        else:
            x2 = next_x2

        cooldown = max(0.0, cooldown - dt)
        distance = abs(x2 - x1)

        if distance <= contact_distance and cooldown <= 0 and abs(v1 - v2) > 0.001:
            midpoint = (x1 + x2) / 2
            if x1 < x2:
                x1 = midpoint - contact_distance / 2
                x2 = midpoint + contact_distance / 2
            else:
                x1 = midpoint + contact_distance / 2
                x2 = midpoint - contact_distance / 2

            new_v1 = (
                (mass1 - elasticity * mass2) * v1
                + (1 + elasticity) * mass2 * v2
            ) / (mass1 + mass2)

            new_v2 = (
                (1 + elasticity) * mass1 * v1
                + (mass2 - elasticity * mass1) * v2
            ) / (mass1 + mass2)

            v1 = new_v1
            v2 = new_v2
            final_v1 = v1
            final_v2 = v2
            collision_index = i
            cooldown = 0.25

    positions1.append(x1)
    positions2.append(x2)

    if collision_index is None:
        collision_index = len(positions1) // 2
        final_v1 = v1
        final_v2 = v2

    return positions1, positions2, collision_index, final_v1, final_v2


def sphere_vertices(cx, cy, cz, radius=1.25, segments=32, rings=20):
    x = []
    y = []
    z = []

    for i in range(rings + 1):
        phi = math.pi * i / rings
        sin_phi = math.sin(phi)
        cos_phi = math.cos(phi)
        for j in range(segments):
            theta = 2 * math.pi * j / segments
            x.append(cx + radius * sin_phi * math.cos(theta))
            y.append(cy + radius * sin_phi * math.sin(theta))
            z.append(cz + radius * cos_phi)

    ii = []
    jj = []
    kk = []
    for i in range(rings):
        for j in range(segments):
            a = i * segments + j
            b = i * segments + (j + 1) % segments
            c = (i + 1) * segments + (j + 1) % segments
            d = (i + 1) * segments + j
            ii.extend([a, a])
            jj.extend([b, c])
            kk.extend([c, d])

    return x, y, z, ii, jj, kk


def cube_vertices(cx, cy, cz, size=2.5):
    h = size / 2
    x = [cx - h, cx + h, cx + h, cx - h, cx - h, cx + h, cx + h, cx - h]
    y = [cy - h, cy - h, cy + h, cy + h, cy - h, cy - h, cy + h, cy + h]
    z = [cz - h, cz - h, cz - h, cz - h, cz + h, cz + h, cz + h, cz + h]

    ii = [0, 0, 0, 1, 1, 2, 4, 4, 5, 6, 3, 3]
    jj = [1, 2, 4, 2, 5, 3, 5, 6, 6, 7, 7, 0]
    kk = [2, 4, 1, 5, 6, 7, 6, 7, 2, 3, 0, 4]

    return x, y, z, ii, jj, kk


def render_collision(positions1, positions2, collision_index, shape1, shape2, speed):
    initial1 = geometry_for_position(shape1, positions1[0])
    initial2 = geometry_for_position(shape2, positions2[0])

    payload = {
        "positions1": positions1,
        "positions2": positions2,
        "collisionIndex": collision_index,
        "shape1": shape1,
        "shape2": shape2,
        "speed": speed,
        "geometry1": initial1,
        "geometry2": initial2,
    }

    html = f"""
    <div id="collision-root" style="width:75%;height:500px;margin:0 auto;">
      <div id="plot" style="width:100%;height:430px;"></div>
      <button id="play" style="display:block;margin:8px auto 0;width:150px;height:44px;font-size:20px;font-weight:700;cursor:pointer;">PLAY</button>
    </div>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <script>
    const data = {json.dumps(payload)};
    const g1 = data.geometry1;
    const g2 = data.geometry2;

    const traces = [
      {{
        type:'mesh3d',
        x:g1.x, y:g1.y, z:g1.z,
        i:g1.i, j:g1.j, k:g1.k,
        name:'Object A',
        opacity:0.98,
        flatshading:false,
        lighting:{{ambient:0.55,diffuse:1.0,specular:1.0,fresnel:0.45,roughness:0.05}},
        lightposition:{{x:100,y:150,z:300}}
      }},
      {{
        type:'mesh3d',
        x:g2.x, y:g2.y, z:g2.z,
        i:g2.i, j:g2.j, k:g2.k,
        name:'Object B',
        opacity:0.98,
        flatshading:false,
        lighting:{{ambient:0.55,diffuse:1.0,specular:1.0,fresnel:0.45,roughness:0.05}},
        lightposition:{{x:100,y:150,z:300}}
      }},
      {{
        type:'scatter3d',
        x:[-9,9,-9,9], y:[0,0,0,0], z:[0,0,0,0],
        mode:'lines',
        line:{{width:8}},
        name:'Track'
      }}
    ];

    const layout = {{
      height:430,
      margin:{{l:0,r:0,t:10,b:0}},
      showlegend:false,
      scene:{{
        xaxis:{{range:[-11,11],title:'X'}},
        yaxis:{{range:[-5,5],title:'Y'}},
        zaxis:{{range:[-5,5],title:'Z'}},
        aspectmode:'cube',
        camera:{{eye:{{x:1.65,y:1.45,z:1.15}}}}
      }}
    }};

    Plotly.newPlot('plot', traces, layout, {{responsive:true,displayModeBar:false}}).then(() => {{
      const plot = document.getElementById('plot');
      const play = document.getElementById('play');
      let running = false;
      let frame = 0;
      let startTime = 0;
      let camera = null;

      function geometry(shape, cx) {{
        if (shape === 'Sphere') return sphere(cx);
        return cube(cx);
      }}

      function sphere(cx) {{
        const radius=1.25, segments=32, rings=20;
        const x=[], y=[], z=[], i=[], j=[], k=[];
        for(let a=0;a<=rings;a++) {{
          const phi=Math.PI*a/rings;
          const sp=Math.sin(phi), cp=Math.cos(phi);
          for(let b=0;b<segments;b++) {{
            const theta=2*Math.PI*b/segments;
            x.push(cx+radius*sp*Math.cos(theta));
            y.push(radius*sp*Math.sin(theta));
            z.push(radius*cp);
          }}
        }}
        for(let a=0;a<rings;a++) {{
          for(let b=0;b<segments;b++) {{
            const p=a*segments+b;
            const q=a*segments+(b+1)%segments;
            const r=(a+1)*segments+(b+1)%segments;
            const s=(a+1)*segments+b;
            i.push(p,p); j.push(q,r); k.push(r,s);
          }}
        }}
        return {{x,y,z,i,j,k}};
      }}

      function cube(cx) {{
        const h=1.25;
        return {{
          x:[cx-h,cx+h,cx+h,cx-h,cx-h,cx+h,cx+h,cx-h],
          y:[-h,-h,h,h,-h,-h,h,h],
          z:[-h,-h,-h,-h,h,h,h,h],
          i:[0,0,0,1,1,2,4,4,5,6,3,3],
          j:[1,2,4,2,5,3,5,6,6,7,7,0],
          k:[2,4,1,5,6,7,6,7,2,3,0,4]
        }};
      }}

      function update(index) {{
        const a=geometry(data.shape1,data.positions1[index]);
        const b=geometry(data.shape2,data.positions2[index]);
        Plotly.restyle(plot, {{x:[a.x,b.x],y:[a.y,b.y],z:[a.z,b.z]}}, [0,1]);
      }}

      function stop() {{
        running=false;
        frame=data.positions1.length-1;
        update(frame);
        if(camera) Plotly.relayout(plot, {{'scene.camera':camera}});
        play.textContent='PLAY';
      }}

      function animate(timestamp) {{
        if(!running) return;
        const elapsed=(timestamp-startTime)*0.001*data.speed;
        const duration=6.0;
        const index=Math.min(data.positions1.length-1,Math.floor(elapsed/duration*(data.positions1.length-1)));
        update(index);
        if(index>=data.positions1.length-1) {{
          stop();
          return;
        }}
        requestAnimationFrame(animate);
      }}

      play.addEventListener('click', () => {{
        if(running) return;
        Plotly.relayout(plot, {{}}).then(() => {{
          camera=JSON.parse(JSON.stringify(plot.layout.scene.camera));
          frame=0;
          update(0);
          running=true;
          startTime=performance.now();
          play.textContent='PLAYING...';
          requestAnimationFrame(animate);
        }});
      }});
    }});
    </script>
    """

    components.html(html, height=540, scrolling=False)


def geometry_for_position(shape, x):
    if shape == "Sphere":
        x_values, y_values, z_values, i, j, k = sphere_vertices(x, 0, 0)
    else:
        x_values, y_values, z_values, i, j, k = cube_vertices(x, 0, 0)

    return {
        "x": x_values,
        "y": y_values,
        "z": z_values,
        "i": i,
        "j": j,
        "k": k,
    }
