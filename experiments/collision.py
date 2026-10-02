import json
import streamlit as st
import streamlit.components.v1 as components


def collision_experiment():
    defaults = {
        "collision_shape1": "Sphere",
        "collision_shape2": "Cube",
        "collision_mass1": 2.0,
        "collision_mass2": 2.0,
        "collision_velocity1": 5.0,
        "collision_velocity2": 3.0,
        "collision_elasticity": 1.0
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    st.markdown(
        """
        <div class="selection-header">
            <div class="section-title">3D Collision</div>
            <div class="selection-description">
                Simulate a collision between two objects in 3D space.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)

    with c1:
        shape1 = st.selectbox(
            "Shape",
            ["Sphere", "Cube", "Cylinder"],
            key="collision_shape1"
        )
        mass1 = st.number_input(
            "Mass (kg)", 0.1, 1000.0, step=0.1,
            key="collision_mass1"
        )
        velocity1 = st.number_input(
            "Velocity (m/s)", 0.0, 100.0, step=0.5,
            key="collision_velocity1"
        )

    with c2:
        shape2 = st.selectbox(
            "Shape",
            ["Sphere", "Cube", "Cylinder"],
            key="collision_shape2"
        )
        mass2 = st.number_input(
            "Mass (kg)", 0.1, 1000.0, step=0.1,
            key="collision_mass2"
        )
        velocity2 = st.number_input(
            "Velocity (m/s)", 0.0, 100.0, step=0.5,
            key="collision_velocity2"
        )

    elasticity = st.slider(
        "Coefficient of Restitution",
        0.0, 1.0,
        key="collision_elasticity"
    )

    if st.button("Run Experiment", type="primary",
                 use_container_width=True):
        run_collision(
            shape1, shape2,
            mass1, mass2,
            velocity1, velocity2,
            elasticity
        )

    if st.button("Back to Experiments"):
        for k in defaults:
            st.session_state.pop(k, None)
        st.session_state.page = "select"
        st.query_params.clear()
        st.rerun()


def run_collision(
    shape1, shape2,
    mass1, mass2,
    velocity1, velocity2,
    elasticity
):
    distance = 12.0
    contact = 3.5
    closing = velocity1 + velocity2

    if closing <= 0:
        st.warning("The objects must move toward each other.")
        return

    collision_time = max(
        (distance - contact) / closing,
        0.1
    )

    total_time = collision_time + 3.5
    points = 240

    times = [
        total_time * i / (points - 1)
        for i in range(points)
    ]

    u1 = velocity1
    u2 = -velocity2

    v1 = (
        mass1 * u1 + mass2 * u2
        - mass2 * elasticity * (u1 - u2)
    ) / (mass1 + mass2)

    v2 = (
        mass1 * u1 + mass2 * u2
        + mass1 * elasticity * (u1 - u2)
    ) / (mass1 + mass2)

    x1 = []
    x2 = []

    for t in times:
        if t < collision_time:
            x1.append(-distance / 2 + velocity1 * t)
            x2.append(distance / 2 - velocity2 * t)
        else:
            dt = t - collision_time
            x1.append(-contact / 2 + v1 * dt)
            x2.append(contact / 2 + v2 * dt)

    xmin = min(x1 + x2) - 3
    xmax = max(x1 + x2) + 3

    p1 = json.dumps(x1)
    p2 = json.dumps(x2)

    html = f"""
    <style>
    #wrap {{
        height:720px;
    }}
    #plot {{
        width:100%;
        height:620px;
    }}
    #play {{
        display:block;
        margin:14px auto;
        padding:14px 42px;
        min-width:150px;
        border-radius:8px;
        border:1px solid #888;
        background:white;
        color:#111;
        font-size:20px;
        font-weight:600;
        cursor:pointer;
    }}
    </style>

    <div id="wrap">
        <div id="plot"></div>
        <button id="play">PLAY</button>
    </div>

    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <script>
    const p1={p1}, p2={p2};
    const s1="{shape1}", s2="{shape2}";
    const plot=document.getElementById("plot");
    const play=document.getElementById("play");

    function sphere(x,c,n) {{
        return {{
            type:"scatter3d",
            x:[x], y:[0], z:[0],
            mode:"markers",
            marker:{{size:22,color:c}},
            name:n
        }};
    }}

    function cube(x,c,n) {{
        const s=1.25;
        const X=[
            x-s,x+s,x+s,x-s,
            x-s,x+s,x+s,x-s
        ];
        const Y=[-s,-s,s,s,-s,-s,s,s];
        const Z=[-s,-s,-s,-s,s,s,s,s];

        return {{
            type:"mesh3d",
            x:X,y:Y,z:Z,
            i:[0,0,4,4,0,1,2,3,0,1,2,3],
            j:[1,2,5,6,1,2,3,0,4,5,6,7],
            k:[2,3,6,7,5,6,7,4,5,6,7,4],
            color:c,
            lighting:{{
                ambient:.3,
                diffuse:.8,
                specular:.5,
                roughness:.3
            }},
            name:n
        }};
    }}

    function cylinder(x,c,n) {{
        const r=1.15, h=2.5, nseg=24;
        const X=[x,x], Y=[0,0], Z=[-h/2,h/2];
        const I=[],J=[],K=[];

        for(let i=0;i<nseg;i++) {{
            let a=2*Math.PI*i/nseg;
            X.push(x+r*Math.cos(a));
            Y.push(r*Math.sin(a));
            Z.push(-h/2);
        }}

        for(let i=0;i<nseg;i++) {{
            let a=2*Math.PI*i/nseg;
            X.push(x+r*Math.cos(a));
            Y.push(r*Math.sin(a));
            Z.push(h/2);
        }}

        for(let i=0;i<nseg;i++) {{
            let n=(i+1)%nseg;
            let b=2+i, bn=2+n;
            let t=2+nseg+i, tn=2+nseg+n;

            I.push(0); J.push(bn); K.push(b);
            I.push(1); J.push(t); K.push(tn);
            I.push(b); J.push(bn); K.push(tn);
            I.push(b); J.push(tn); K.push(t);
        }}

        return {{
            type:"mesh3d",
            x:X,y:Y,z:Z,
            i:I,j:J,k:K,
            color:c,
            lighting:{{
                ambient:.3,
                diffuse:.8,
                specular:.5,
                roughness:.3
            }},
            name:n
        }};
    }}

    function object(x,c,s,n) {{
        if(s==="Sphere") return sphere(x,c,n);
        if(s==="Cube") return cube(x,c,n);
        return cylinder(x,c,n);
    }}

    const initial=[
        object(p1[0],"blue",s1,"Object 1"),
        object(p2[0],"red",s2,"Object 2")
    ];

    const layout={{
        title:"3D Collision Simulation",
        scene:{{
            dragmode:"orbit",
            xaxis:{{title:"X Position (m)",range:[{xmin},{xmax}]}},
            yaxis:{{title:"Y Position (m)",range:[-5,5]}},
            zaxis:{{title:"Z Position (m)",range:[-5,5]}},
            aspectmode:"cube"
        }},
        height:620,
        margin:{{l:0,r:0,t:60,b:10}},
        paper_bgcolor:"rgba(0,0,0,0)"
    }};

    Plotly.newPlot(
        plot, initial, layout,
        {{
            responsive:true,
            scrollZoom:true,
            displaylogo:false
        }}
    );

    play.onclick=async()=> {{
        play.disabled=true;

        const camera=plot.layout.scene.camera
            ? JSON.parse(JSON.stringify(plot.layout.scene.camera))
            : null;

        const frames=[];

        for(let i=0;i<p1.length;i++) {{
            const f={{
                name:"f"+i,
                data:[
                    object(p1[i],"blue",s1,"Object 1"),
                    object(p2[i],"red",s2,"Object 2")
                ]
            }};

            if(camera)
                f.layout={{scene:{{camera:camera}}}};

            frames.push(f);
        }}

        await Plotly.deleteFrames(plot);
        await Plotly.addFrames(plot,frames);

        await Plotly.animate(
            plot,
            frames.map(f=>f.name),
            {{
                transition:{{duration:0}},
                frame:{{duration:20,redraw:true}},
                mode:"immediate"
            }}
        );

        if(camera)
            await Plotly.relayout(
                plot,
                {{"scene.camera":camera}}
            );

        play.disabled=false;
    }};
    </script>
    """

    components.html(
        html,
        height=750,
        scrolling=False
    )

    st.markdown("### Results")

    c1, c2 = st.columns(2)

    with c1:
        st.metric("Object 1 Final Velocity", f"{v1:.2f} m/s")
        st.metric(
            "Initial Kinetic Energy",
            f"{0.5*mass1*velocity1**2 + 0.5*mass2*velocity2**2:.2f} J"
        )

    with c2:
        st.metric("Object 2 Final Velocity", f"{v2:.2f} m/s")
        st.metric(
            "Final Kinetic Energy",
            f"{0.5*mass1*v1**2 + 0.5*mass2*v2**2:.2f} J"
        )
