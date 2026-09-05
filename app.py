import streamlit as st
import math
import io
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up & Mixing Engine",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# PROFESSIONAL UI
# =========================================================

st.markdown("""
<style>

.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1600px;
}

h1 {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
}

h2 {
    font-weight: 650 !important;
}

h3 {
    font-weight: 600 !important;
}

[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #D9E1EA;
    border-radius: 12px;
    padding: 14px;
}

[data-testid="stMetricValue"] {
    font-size: 1.45rem;
}

.stButton > button {
    border-radius: 8px;
    font-weight: 600;
}

div[data-testid="stExpander"] {
    border-radius: 12px;
    border: 1px solid #D9E1EA;
}

.status-pass {
    background: #E8F5E9;
    border-left: 5px solid #2E7D32;
    padding: 10px;
    border-radius: 6px;
}

.status-warning {
    background: #FFF8E1;
    border-left: 5px solid #F9A825;
    padding: 10px;
    border-radius: 6px;
}

.status-fail {
    background: #FFEBEE;
    border-left: 5px solid #C62828;
    padding: 10px;
    border-radius: 6px;
}

.info-card {
    background: #F5F7FA;
    border-radius: 12px;
    padding: 15px;
    border: 1px solid #E0E5EB;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# CONSTANTS
# =========================================================

REACTION_TYPES = [
    "Liquid-Liquid",
    "Solid-Liquid",
    "Gas-Liquid",
    "Gas-Liquid-Solid",
    "Crystallization",
    "Precipitation",
    "Dissolution",
    "Extraction",
    "Neutralization",
    "Other"
]

BOTTOM_TYPES = [
    "Flat Bottom",
    "2:1 Ellipsoidal",
    "10% Torispherical",
    "6% Torispherical",
    "Hemispherical",
    "Conical"
]

SCALE_UP_CRITERIA = [
    "Constant P/V",
    "Constant Tip Speed",
    "Constant RPM",
    "Constant Froude Number",
    "Constant Reynolds Number",
    "Constant N/Njs",
    "Constant Pumping / Volume",
    "Constant KLa",
    "User Defined"
]


# =========================================================
# AGITATOR LIBRARY
# =========================================================

AGITATORS = {

    "Rushton Turbine": {
        "Np": 5.0,
        "Nq": 0.75,
        "blades": 6,
        "flow": "Radial",
        "application": "Gas-Liquid / High Dispersion / High Shear",
        "recommended": "Gas dispersion, mass transfer"
    },

    "Pitched Blade Turbine": {
        "Np": 1.5,
        "Nq": 0.75,
        "blades": 4,
        "flow": "Mixed",
        "application": "General Mixing / Suspension",
        "recommended": "Solid-liquid and general blending"
    },

    "Hydrofoil": {
        "Np": 0.5,
        "Nq": 0.70,
        "blades": 3,
        "flow": "Axial",
        "application": "Low Power / High Circulation",
        "recommended": "Bulk liquid mixing"
    },

    "Marine Propeller": {
        "Np": 0.40,
        "Nq": 0.60,
        "blades": 3,
        "flow": "Axial",
        "application": "Low Viscosity",
        "recommended": "Low viscosity blending"
    },

    "Anchor": {
        "Np": 1.0,
        "Nq": 0.30,
        "blades": 2,
        "flow": "Tangential",
        "application": "High Viscosity",
        "recommended": "Viscous fluids"
    },

    "Helical Ribbon": {
        "Np": 1.2,
        "Nq": 0.20,
        "blades": 1,
        "flow": "Axial / Helical",
        "application": "Very High Viscosity",
        "recommended": "Highly viscous products"
    }
}


# =========================================================
# SESSION STATE
# =========================================================

if "reactor_data" not in st.session_state:

    st.session_state.reactor_data = {
        "Lab": {},
        "Pilot": {},
        "Commercial": {}
    }


# =========================================================
# CALCULATION FUNCTIONS
# =========================================================

def calculate_agitation(
    volume_m3,
    rho,
    viscosity_cp,
    rpm,
    impeller_d,
    n_impellers,
    np_value,
    nq_value
):

    viscosity = viscosity_cp / 1000.0

    N = rpm / 60.0

    if N <= 0:
        return {}

    power_w = (
        np_value
        * rho
        * N**3
        * impeller_d**5
        * n_impellers
    )

    power_kw = power_w / 1000

    pv = power_kw / volume_m3 if volume_m3 > 0 else 0

    tip_speed = math.pi * impeller_d * N

    pumping_m3s = (
        nq_value
        * N
        * impeller_d**3
        * n_impellers
    )

    pumping_m3h = pumping_m3s * 3600

    reynolds = (
        rho
        * N
        * impeller_d**2
        / viscosity
    ) if viscosity > 0 else 0

    froude = (
        N**2
        * impeller_d
        / 9.81
    )

    torque = (
        power_w
        / (2 * math.pi * N)
    )

    return {
        "N": N,
        "Power kW": power_kw,
        "P/V kW/m³": pv,
        "Tip Speed m/s": tip_speed,
        "Pumping m³/h": pumping_m3h,
        "Re": reynolds,
        "Fr": froude,
        "Torque N·m": torque
    }


# =========================================================
# REACTOR VOLUME
# =========================================================

def cylindrical_volume(diameter, height):

    return (
        math.pi
        * diameter**2
        / 4
        * height
    )


def calculate_geometry_ratios(
    tank_d,
    liquid_height,
    impeller_d,
    clearance,
    baffle_width
):

    return {
        "D/T": impeller_d / tank_d if tank_d else 0,
        "H/T": liquid_height / tank_d if tank_d else 0,
        "C/T": clearance / tank_d if tank_d else 0,
        "B/T": baffle_width / tank_d if tank_d else 0
    }


# =========================================================
# NJS ESTIMATION
# =========================================================

def calculate_njs(
    rho_liquid,
    rho_solid,
    particle_diameter,
    solids_fraction,
    impeller_d,
    suspension_factor
):

    density_ratio = max(
        (rho_solid - rho_liquid)
        / rho_liquid,
        0.01
    )

    particle_ratio = (
        particle_diameter
        / impeller_d
    )

    njs_hz = (
        suspension_factor
        * density_ratio**0.45
        * particle_ratio**0.13
        * max(solids_fraction, 0.001)**0.08
    )

    return njs_hz * 60


# =========================================================
# GAS-LIQUID
# =========================================================

def calculate_gas_liquid(
    gas_flow_nm3h,
    volume_m3,
    liquid_height,
    tank_diameter,
    bubble_diameter,
    pv
):

    if volume_m3 <= 0:
        return {}

    gas_flow_m3s = (
        gas_flow_nm3h
        / 3600
    )

    vvm = (
        gas_flow_nm3h
        / 60
        / volume_m3
    )

    tank_area = (
        math.pi
        * tank_diameter**2
        / 4
    )

    superficial_velocity = (
        gas_flow_m3s
        / tank_area
    )

    g = 9.81

    bubble_velocity = math.sqrt(
        max(
            4
            * g
            * bubble_diameter
            / 3,
            1e-9
        )
    )

    residence_time = (
        liquid_height
        / bubble_velocity
    )

    gas_holdup = min(
        0.35,
        max(
            0.0,
            0.02
            * (superficial_velocity * 100)**0.6
            * max(pv, 0.001)**0.15
        )
    )

    kla = (
        0.20
        * max(pv, 0.001)**0.5
        * max(superficial_velocity, 1e-5)**0.35
    )

    return {
        "VVM": vvm,
        "Superficial Velocity m/s": superficial_velocity,
        "Bubble Velocity m/s": bubble_velocity,
        "Bubble Residence Time s": residence_time,
        "Gas Hold-up": gas_holdup,
        "KLa 1/s": kla
    }


# =========================================================
# SCALE-UP
# =========================================================

def scale_up_rpm(
    criterion,
    pilot,
    commercial
):

    pilot_N = pilot["rpm"] / 60
    pilot_D = pilot["impeller_d"]
    commercial_D = commercial["impeller_d"]

    if criterion == "Constant Tip Speed":

        pilot_tip = (
            math.pi
            * pilot_D
            * pilot_N
        )

        commercial_N = (
            pilot_tip
            / (
                math.pi
                * commercial_D
            )
        )

    elif criterion == "Constant P/V":

        commercial_N = (
            pilot_N
            * (
                pilot_D
                / commercial_D
            )**(5/3)
        )

    elif criterion == "Constant RPM":

        commercial_N = pilot_N

    elif criterion == "Constant Froude Number":

        commercial_N = (
            pilot_N
            * math.sqrt(
                pilot_D
                / commercial_D
            )
        )

    elif criterion == "Constant Reynolds Number":

        commercial_N = (
            pilot_N
            * (
                pilot_D
                / commercial_D
            )**2
        )

    elif criterion == "Constant Pumping / Volume":

        commercial_N = (
            pilot_N
            * (
                pilot["volume_m3"]
                / commercial["volume_m3"]
            )
            * (
                commercial_D
                / pilot_D
            )**3
        )

    else:

        commercial_N = pilot_N

    return commercial_N * 60


# =========================================================
# 3D REACTOR
# =========================================================

def create_reactor_3d(
    tank_d,
    liquid_height,
    impeller_d,
    n_impellers,
    baffles,
    ticklers
):

    fig = go.Figure()

    radius = tank_d / 2

    theta = np.linspace(
        0,
        2 * np.pi,
        60
    )

    z = np.linspace(
        0,
        liquid_height,
        30
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z
    )

    x = (
        radius
        * np.cos(theta_grid)
    )

    y = (
        radius
        * np.sin(theta_grid)
    )

    # Reactor shell

    fig.add_surface(
        x=x,
        y=y,
        z=z_grid,
        opacity=0.15,
        showscale=False,
        name="Reactor"
    )

    # Liquid surface

    fig.add_surface(
        x=x,
        y=y,
        z=np.ones_like(x)
        * liquid_height,
        opacity=0.08,
        showscale=False,
        name="Liquid"
    )

    # Shaft

    fig.add_trace(
        go.Scatter3d(
            x=[0, 0],
            y=[0, 0],
            z=[0, liquid_height],
            mode="lines",
            line=dict(width=8),
            name="Shaft"
        )
    )

    # Impellers

    if n_impellers == 1:

        elevations = [
            liquid_height * 0.35
        ]

    else:

        elevations = np.linspace(
            liquid_height * 0.20,
            liquid_height * 0.80,
            n_impellers
        )

    for i, elevation in enumerate(
        elevations
    ):

        imp_x = (
            impeller_d / 2
            * np.cos(theta)
        )

        imp_y = (
            impeller_d / 2
            * np.sin(theta)
        )

        fig.add_trace(
            go.Scatter3d(
                x=imp_x,
                y=imp_y,
                z=np.ones_like(theta)
                * elevation,
                mode="lines",
                line=dict(width=8),
                name=f"Impeller {i+1}"
            )
        )

    # Baffles

    for i in range(
        int(baffles)
    ):

        angle = (
            2
            * np.pi
            * i
            / max(baffles, 1)
        )

        rb = radius * 0.92

        fig.add_trace(
            go.Scatter3d(
                x=[
                    rb * math.cos(angle),
                    rb * math.cos(angle)
                ],
                y=[
                    rb * math.sin(angle),
                    rb * math.sin(angle)
                ],
                z=[
                    0,
                    liquid_height
                ],
                mode="lines",
                line=dict(width=6),
                name="Baffle",
                showlegend=i == 0
            )
        )

    # Ticklers

    for i in range(
        int(ticklers)
    ):

        angle = (
            2
            * np.pi
            * i
            / max(ticklers, 1)
        )

        rt = radius * 0.80

        fig.add_trace(
            go.Scatter3d(
                x=[
                    rt * math.cos(angle),
                    rt * math.cos(angle)
                ],
                y=[
                    rt * math.sin(angle),
                    rt * math.sin(angle)
                ],
                z=[
                    liquid_height * 0.15,
                    liquid_height * 0.85
                ],
                mode="lines",
                line=dict(width=4),
                name="Tickler",
                showlegend=i == 0
            )
        )

    fig.update_layout(

        height=650,

        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Height (m)",
            aspectmode="data"
        ),

        margin=dict(
            l=0,
            r=0,
            t=20,
            b=0
        )
    )

    return fig


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚗️ Reactor Engineering")

page = st.sidebar.radio(
    "Engineering Module",
    [
        "🏠 Executive Dashboard",
        "📋 Project & Design Basis",
        "⚙️ Reactor Configuration",
        "🔄 Agitation System",
        "📊 Scale-Up Engine",
        "🧱 Solid-Liquid",
        "💨 Gas-Liquid",
        "🔥 Heat Transfer",
        "🧊 3D Reactor",
        "✓ Engineering Validation",
        "📚 Agitator Library",
        "📥 Excel Export"
    ]
)


# =========================================================
# PROJECT
# =========================================================

if "project" not in st.session_state:

    st.session_state.project = {
        "name": "New Reactor Scale-Up Study",
        "product": "",
        "engineer": "",
        "reaction": "Liquid-Liquid",
        "criterion": "Constant P/V"
    }


# =========================================================
# PROJECT PAGE
# =========================================================

if page == "📋 Project & Design Basis":

    st.header("📋 Project & Design Basis")

    c1, c2 = st.columns(2)

    with c1:

        st.session_state.project["name"] = st.text_input(
            "Project Name",
            st.session_state.project["name"]
        )

        st.session_state.project["product"] = st.text_input(
            "Product / Process",
            st.session_state.project["product"]
        )

        st.session_state.project["engineer"] = st.text_input(
            "Process Engineer",
            st.session_state.project["engineer"]
        )

    with c2:

        st.session_state.project["reaction"] = st.selectbox(
            "Reaction / Process Type",
            REACTION_TYPES,
            index=REACTION_TYPES.index(
                st.session_state.project["reaction"]
            )
        )

        st.session_state.project["criterion"] = st.selectbox(
            "Primary Scale-Up Criterion",
            SCALE_UP_CRITERIA,
            index=SCALE_UP_CRITERIA.index(
                st.session_state.project["criterion"]
            )
        )

        st.text_input(
            "Revision",
            "Rev-00"
        )


# =========================================================
# REACTOR CONFIGURATION
# =========================================================

elif page == "⚙️ Reactor Configuration":

    st.header("⚙️ Reactor Configuration")

    tabs = st.tabs(
        [
            "LAB",
            "PILOT",
            "COMMERCIAL"
        ]
    )

    defaults = {

        "Lab": {
            "volume": 2,
            "id": 0.12,
            "height": 0.18,
            "rpm": 500,
            "di": 0.06
        },

        "Pilot": {
            "volume": 500,
            "id": 0.80,
            "height": 0.90,
            "rpm": 250,
            "di": 0.30
        },

        "Commercial": {
            "volume": 5000,
            "id": 1.80,
            "height": 2.20,
            "rpm": 110,
            "di": 0.85
        }
    }

    for tab, scale in zip(
        tabs,
        ["Lab", "Pilot", "Commercial"]
    ):

        with tab:

            st.subheader(
                f"{scale} Reactor"
            )

            d = defaults[scale]

            c1, c2, c3 = st.columns(3)

            with c1:

                volume_l = st.number_input(
                    "Working Volume (L)",
                    value=float(d["volume"]),
                    min_value=0.1,
                    key=f"{scale}_volume"
                )

                tank_d = st.number_input(
                    "Tank ID (m)",
                    value=float(d["id"]),
                    min_value=0.01,
                    key=f"{scale}_tank"
                )

                liquid_height = st.number_input(
                    "Liquid Height (m)",
                    value=float(d["height"]),
                    min_value=0.01,
                    key=f"{scale}_height"
                )

            with c2:

                rpm = st.number_input(
                    "Agitator RPM",
                    value=float(d["rpm"]),
                    min_value=0.1,
                    key=f"{scale}_rpm"
                )

                impeller_d = st.number_input(
                    "Impeller Diameter (m)",
                    value=float(d["di"]),
                    min_value=0.01,
                    key=f"{scale}_di"
                )

                n_impellers = st.number_input(
                    "Number of Impellers",
                    min_value=1,
                    max_value=10,
                    value=1 if scale == "Lab" else 2,
                    key=f"{scale}_nimp"
                )

            with c3:

                rho = st.number_input(
                    "Density (kg/m³)",
                    value=1000.0,
                    key=f"{scale}_rho"
                )

                viscosity = st.number_input(
                    "Viscosity (cP)",
                    value=1.0,
                    min_value=0.01,
                    key=f"{scale}_mu"
                )

                sigma = st.number_input(
                    "Surface Tension (mN/m)",
                    value=72.0,
                    key=f"{scale}_sigma"
                )

            bottom = st.selectbox(
                "Reactor Bottom",
                BOTTOM_TYPES,
                key=f"{scale}_bottom"
            )

            st.session_state.reactor_data[
                scale
            ] = {

                "volume_m3":
                    volume_l / 1000,

                "tank_d":
                    tank_d,

                "liquid_height":
                    liquid_height,

                "rpm":
                    rpm,

                "impeller_d":
                    impeller_d,

                "n_impellers":
                    n_impellers,

                "rho":
                    rho,

                "viscosity":
                    viscosity,

                "sigma":
                    sigma,

                "bottom":
                    bottom
            }

            st.success(
                f"{scale} reactor configuration saved."
            )


# =========================================================
# AGITATION
# =========================================================

elif page == "🔄 Agitation System":

    st.header("🔄 Agitation System")

    agitator_type = st.selectbox(
        "Agitator Type",
        list(AGITATORS.keys())
    )

    data = AGITATORS[
        agitator_type
    ]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Power Number",
        data["Np"]
    )

    c2.metric(
        "Pumping Number",
        data["Nq"]
    )

    c3.metric(
        "Flow",
        data["flow"]
    )

    c4.metric(
        "Application",
        data["application"]
    )

    st.divider()

    st.subheader(
        "Impeller Configuration"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        tank_d = st.number_input(
            "Tank Diameter (m)",
            value=1.80
        )

        impeller_d = st.number_input(
            "Impeller Diameter (m)",
            value=0.85
        )

    with c2:

        rpm = st.number_input(
            "RPM",
            value=110.0
        )

        n_impellers = st.number_input(
            "Number of Impellers",
            1,
            10,
            3
        )

    with c3:

        clearance = st.number_input(
            "Bottom Clearance (m)",
            value=0.25
        )

        baffle_width = st.number_input(
            "Baffle Width (m)",
            value=0.18
        )

    ratios = calculate_geometry_ratios(
        tank_d,
        2.2,
        impeller_d,
        clearance,
        baffle_width
    )

    st.subheader(
        "Geometry Ratios"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "D/T",
        f"{ratios['D/T']:.3f}"
    )

    c2.metric(
        "H/T",
        f"{ratios['H/T']:.3f}"
    )

    c3.metric(
        "C/T",
        f"{ratios['C/T']:.3f}"
    )

    c4.metric(
        "B/T",
        f"{ratios['B/T']:.3f}"
    )


# =========================================================
# SCALE-UP ENGINE
# =========================================================

elif page == "📊 Scale-Up Engine":

    st.header(
        "📊 Lab → Pilot → Commercial Scale-Up"
    )

    criterion = st.selectbox(
        "Scale-Up Criterion",
        SCALE_UP_CRITERIA
    )

    st.info(
        f"Selected basis: **{criterion}**"
    )

    pilot = st.session_state.reactor_data.get(
        "Pilot"
    )

    commercial = st.session_state.reactor_data.get(
        "Commercial"
    )

    if pilot and commercial:

        commercial_rpm = scale_up_rpm(
            criterion,
            pilot,
            commercial
        )

        st.subheader(
            "Scale-Up Result"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Pilot RPM",
            f"{pilot['rpm']:.1f}"
        )

        c2.metric(
            "Calculated Commercial RPM",
            f"{commercial_rpm:.1f}"
        )

        c3.metric(
            "Actual Commercial RPM",
            f"{commercial['rpm']:.1f}"
        )

        deviation = (
            commercial["rpm"]
            / commercial_rpm
            - 1
        ) * 100

        st.metric(
            "RPM Deviation",
            f"{deviation:.1f}%"
        )

    else:

        st.warning(
            "Please enter Pilot and Commercial reactor data first."
        )


# =========================================================
# CALCULATIONS / DASHBOARD
# =========================================================

elif page == "🏠 Executive Dashboard":

    st.header(
        "🏭 Reactor Scale-Up & Mixing Engine"
    )

    st.caption(
        "Process Engineering Decision Support Dashboard"
    )

    reaction = st.session_state.project[
        "reaction"
    ]

    criterion = st.session_state.project[
        "criterion"
    ]

    st.markdown(
        f"""
        <div class="info-card">
        <b>Project:</b> {st.session_state.project['name']}<br>
        <b>Reaction Type:</b> {reaction}<br>
        <b>Scale-Up Basis:</b> {criterion}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    scales = [
        "Lab",
        "Pilot",
        "Commercial"
    ]

    for scale in scales:

        r = st.session_state.reactor_data.get(
            scale
        )

        if not r:
            continue

        agitator = AGITATORS[
            "Pitched Blade Turbine"
        ]

        results = calculate_agitation(
            r["volume_m3"],
            r["rho"],
            r["viscosity"],
            r["rpm"],
            r["impeller_d"],
            r["n_impellers"],
            agitator["Np"],
            agitator["Nq"]
        )

        r.update(results)

    st.subheader(
        "Reactor Comparison"
    )

    rows = []

    for scale in scales:

        r = st.session_state.reactor_data.get(
            scale
        )

        if r and "Power kW" in r:

            rows.append({

                "Scale":
                    scale,

                "Volume (L)":
                    r["volume_m3"] * 1000,

                "RPM":
                    r["rpm"],

                "Power (kW)":
                    r["Power kW"],

                "P/V":
                    r["P/V kW/m³"],

                "Tip Speed":
                    r["Tip Speed m/s"],

                "Pumping":
                    r["Pumping m³/h"],

                "Re":
                    r["Re"],

                "Fr":
                    r["Fr"],

                "Torque":
                    r["Torque N·m"]
            })

    if rows:

        df = pd.DataFrame(
            rows
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    st.subheader(
        "Key Commercial Parameters"
    )

    commercial = st.session_state.reactor_data.get(
        "Commercial"
    )

    if commercial and "Power kW" in commercial:

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "P/V",
            f"{commercial['P/V kW/m³']:.2f} kW/m³"
        )

        c2.metric(
            "Tip Speed",
            f"{commercial['Tip Speed m/s']:.2f} m/s"
        )

        c3.metric(
            "Pumping",
            f"{commercial['Pumping m³/h']:.1f} m³/h"
        )

        c4.metric(
            "Re",
            f"{commercial['Re']:.2e}"
        )

        c5.metric(
            "Power",
            f"{commercial['Power kW']:.2f} kW"
        )


# =========================================================
# SOLID-LIQUID
# =========================================================

elif page == "🧱 Solid-Liquid":

    st.header(
        "🧱 Solid-Liquid Suspension"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        rho_liquid = st.number_input(
            "Liquid Density (kg/m³)",
            value=1000.0
        )

        rho_solid = st.number_input(
            "Solid Density (kg/m³)",
            value=2500.0
        )

    with c2:

        particle_size = st.number_input(
            "Particle Diameter (µm)",
            value=100.0
        )

        solids_wt = st.number_input(
            "Solids Concentration (wt%)",
            value=10.0
        )

    with c3:

        impeller_d = st.number_input(
            "Impeller Diameter (m)",
            value=0.85
        )

        suspension_factor = st.number_input(
            "Suspension Correlation Factor",
            value=1.30
        )

    njs = calculate_njs(
        rho_liquid,
        rho_solid,
        particle_size / 1e6,
        solids_wt / 100,
        impeller_d,
        suspension_factor
    )

    st.divider()

    commercial = st.session_state.reactor_data.get(
        "Commercial"
    )

    if commercial:

        actual_rpm = commercial[
            "rpm"
        ]

        ratio = (
            actual_rpm
            / njs
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Estimated Njs",
            f"{njs:.1f} RPM"
        )

        c2.metric(
            "Actual N",
            f"{actual_rpm:.1f} RPM"
        )

        c3.metric(
            "N / Njs",
            f"{ratio:.2f}"
        )

        if ratio >= 1.2:

            st.success(
                "PASS — Agitation exceeds the selected N/Njs screening margin."
            )

        elif ratio >= 1.0:

            st.warning(
                "REVIEW — Suspension may be marginal."
            )

        else:

            st.error(
                "FAIL — Agitation is below estimated Njs."
            )


# =========================================================
# GAS-LIQUID
# =========================================================

elif page == "💨 Gas-Liquid":

    st.header(
        "💨 Gas-Liquid Mixing & Mass Transfer"
    )

    commercial = st.session_state.reactor_data.get(
        "Commercial"
    )

    if commercial:

        c1, c2, c3 = st.columns(3)

        with c1:

            gas_flow = st.number_input(
                "Gas Flow (Nm³/h)",
                value=25.0
            )

            bubble_d = st.number_input(
                "Bubble Diameter (mm)",
                value=2.4
            )

        with c2:

            liquid_height = st.number_input(
                "Liquid Height (m)",
                value=commercial[
                    "liquid_height"
                ]
            )

            tank_d = st.number_input(
                "Tank Diameter (m)",
                value=commercial[
                    "tank_d"
                ]
            )

        with c3:

            pv = commercial.get(
                "P/V kW/m³",
                1.0
            )

        gas = calculate_gas_liquid(
            gas_flow,
            commercial["volume_m3"],
            liquid_height,
            tank_d,
            bubble_d / 1000,
            pv
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "VVM",
            f"{gas['VVM']:.3f}"
        )

        c2.metric(
            "Gas Hold-up",
            f"{gas['Gas Hold-up']*100:.2f}%"
        )

        c3.metric(
            "Bubble Residence",
            f"{gas['Bubble Residence Time s']:.2f} s"
        )

        c4.metric(
            "KLa",
            f"{gas['KLa 1/s']:.4f} 1/s"
        )

        st.subheader(
            "Gas-Liquid Results"
        )

        st.dataframe(
            pd.DataFrame(
                [gas]
            ).T.rename(
                columns={0: "Value"}
            ),
            use_container_width=True
        )


# =========================================================
# HEAT TRANSFER
# =========================================================

elif page == "🔥 Heat Transfer":

    st.header(
        "🔥 Reactor Heat Transfer"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        U = st.number_input(
            "Overall Heat Transfer Coefficient (W/m²K)",
            value=150.0
        )

    with c2:

        area = st.number_input(
            "Heat Transfer Area (m²)",
            value=20.0
        )

    with c3:

        lmtd = st.number_input(
            "LMTD (K)",
            value=43.1
        )

    duty_kw = (
        U
        * area
        * lmtd
        / 1000
    )

    st.metric(
        "Heat Duty",
        f"{duty_kw:.2f} kW"
    )


# =========================================================
# 3D
# =========================================================

elif page == "🧊 3D Reactor":

    st.header(
        "🧊 Interactive 3D Reactor"
    )

    commercial = st.session_state.reactor_data.get(
        "Commercial"
    )

    if commercial:

        c1, c2, c3 = st.columns(3)

        with c1:

            baffles = st.number_input(
                "Baffles",
                0,
                12,
                4
            )

        with c2:

            ticklers = st.number_input(
                "Ticklers",
                0,
                20,
                0
            )

        with c3:

            impeller_d = st.number_input(
                "Impeller Diameter",
                value=commercial[
                    "impeller_d"
                ]
            )

        fig = create_reactor_3d(
            commercial["tank_d"],
            commercial["liquid_height"],
            impeller_d,
            commercial["n_impellers"],
            baffles,
            ticklers
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.caption(
            "Geometry visualization is intended for engineering visualization and configuration checking; it is not a CFD solution."
        )


# =========================================================
# VALIDATION
# =========================================================

elif page == "✓ Engineering Validation":

    st.header(
        "✓ Engineering Validation"
    )

    commercial = st.session_state.reactor_data.get(
        "Commercial"
    )

    if commercial:

        checks = []

        ratio = (
            commercial["impeller_d"]
            / commercial["tank_d"]
        )

        checks.append(
            (
                "PASS" if 0.2 <= ratio <= 0.7
                else "REVIEW",
                f"Impeller / tank diameter ratio D/T = {ratio:.3f}"
            )
        )

        checks.append(
            (
                "PASS" if commercial["n_impellers"] >= 1
                else "FAIL",
                "At least one impeller is defined."
            )
        )

        checks.append(
            (
                "PASS" if commercial["volume_m3"] > 0
                else "FAIL",
                "Working volume is positive."
            )
        )

        checks.append(
            (
                "PASS" if commercial["rpm"] > 0
                else "FAIL",
                "Agitator RPM is positive."
            )
        )

        for status, message in checks:

            if status == "PASS":

                st.success(
                    f"✓ {message}"
                )

            elif status == "REVIEW":

                st.warning(
                    f"⚠ {message}"
                )

            else:

                st.error(
                    f"✕ {message}"
                )

        st.divider()

        st.info(
            "Final engineering validation should include vendor agitator curves, mechanical design limits, validated mixing correlations, experimental data and applicable company/design standards."
        )


# =========================================================
# AGITATOR LIBRARY
# =========================================================

elif page == "📚 Agitator Library":

    st.header(
        "📚 Agitator Engineering Library"
    )

    rows = []

    for name, data in AGITATORS.items():

        rows.append({

            "Agitator":
                name,

            "Np":
                data["Np"],

            "Nq":
                data["Nq"],

            "Blades":
                data["blades"],

            "Flow":
                data["flow"],

            "Application":
                data["application"],

            "Recommended":
                data["recommended"]
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# EXCEL EXPORT
# =========================================================

elif page == "📥 Excel Export":

    st.header(
        "📥 Engineering Excel Export"
    )

    st.write(
        "Export the current reactor configuration and calculated results."
    )

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        # Project

        pd.DataFrame(
            [{
                "Project":
                    st.session_state.project["name"],

                "Product":
                    st.session_state.project["product"],

                "Engineer":
                    st.session_state.project["engineer"],

                "Reaction":
                    st.session_state.project["reaction"],

                "Scale-Up Criterion":
                    st.session_state.project["criterion"]
            }]
        ).to_excel(
            writer,
            sheet_name="Project",
            index=False
        )

        # Reactor sheets

        for scale in [
            "Lab",
            "Pilot",
            "Commercial"
        ]:

            data = st.session_state.reactor_data.get(
                scale
            )

            if data:

                pd.DataFrame(
                    [data]
                ).to_excel(
                    writer,
                    sheet_name=scale,
                    index=False
                )

        # Comparison

        comparison = []

        for scale in [
            "Lab",
            "Pilot",
            "Commercial"
        ]:

            r = st.session_state.reactor_data.get(
                scale
            )

            if r:

                comparison.append({

                    "Scale":
                        scale,

                    "Volume L":
                        r["volume_m3"] * 1000,

                    "RPM":
                        r["rpm"],

                    "Impeller D m":
                        r["impeller_d"],

                    "Number Impellers":
                        r["n_impellers"],

                    "Power kW":
                        r.get(
                            "Power kW",
                            None
                        ),

                    "P/V kW/m³":
                        r.get(
                            "P/V kW/m³",
                            None
                        ),

                    "Tip Speed m/s":
                        r.get(
                            "Tip Speed m/s",
                            None
                        ),

                    "Pumping m³/h":
                        r.get(
                            "Pumping m³/h",
                            None
                        ),

                    "Re":
                        r.get(
                            "Re",
                            None
                        ),

                    "Fr":
                        r.get(
                            "Fr",
                            None
                        ),

                    "Torque N·m":
                        r.get(
                            "Torque N·m",
                            None
                        )
                })

        pd.DataFrame(
            comparison
        ).to_excel(
            writer,
            sheet_name="Scale Comparison",
            index=False
        )

    st.download_button(
        "⬇️ Download Reactor Scale-Up Excel",
        output.getvalue(),
        file_name="Reactor_ScaleUp_Engineering.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success(
        "Excel workbook generated successfully."
    )
