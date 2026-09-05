import streamlit as st
import math

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Reactor Scale-Up Dashboard",
    page_icon="🏭",
    layout="wide"
)

# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title("🏭 Reactor Scale-Up & Mixing Dashboard")
st.caption("Pilot → Commercial Reactor Engineering Calculator")

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.header("Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "🏠 Dashboard",
        "⚙️ Reactor Definition",
        "🔄 Agitator",
        "📊 Scale-Up",
        "🧮 Calculations",
        "📚 Agitator Library"
    ]
)

# ---------------------------------------------------------
# AGITATOR LIBRARY
# ---------------------------------------------------------

agitators = {
    "Rushton Turbine": {
        "Np": 5.0,
        "Nq": 0.75,
        "application": "Gas-Liquid / Radial Flow"
    },

    "Pitched Blade Turbine": {
        "Np": 1.5,
        "Nq": 0.75,
        "application": "General Mixing / Axial Flow"
    },

    "Hydrofoil": {
        "Np": 0.5,
        "Nq": 0.7,
        "application": "Low Viscosity / Axial Flow"
    },

    "Propeller": {
        "Np": 0.4,
        "Nq": 0.6,
        "application": "Low Viscosity"
    },

    "Anchor": {
        "Np": 1.0,
        "Nq": 0.3,
        "application": "High Viscosity"
    }
}

# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

if page == "🏠 Dashboard":

    st.subheader("Engineering Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Pilot Volume", "500 L")
    col2.metric("Commercial Volume", "5000 L")
    col3.metric("Scale Factor", "10 X")
    col4.metric("Status", "Ready")

    st.divider()

    st.subheader("Scale-Up Parameters")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("P/V", "-")
    col2.metric("Njs", "-")
    col3.metric("Tip Speed", "-")
    col4.metric("Pumping", "-")
    col5.metric("Blend Time", "-")

    st.divider()

    st.info(
        "Enter Pilot and Commercial reactor data using the modules "
        "from the left navigation menu."
    )

# ---------------------------------------------------------
# REACTOR DEFINITION
# ---------------------------------------------------------

elif page == "⚙️ Reactor Definition":

    st.header("⚙️ Reactor Definition")

    tab1, tab2 = st.tabs(
        ["Pilot Reactor", "Commercial Reactor"]
    )

    with tab1:

        st.subheader("Pilot Reactor")

        col1, col2, col3 = st.columns(3)

        with col1:
            pilot_volume = st.number_input(
                "Working Volume (L)",
                value=500.0
            )

            pilot_id = st.number_input(
                "Tank ID (mm)",
                value=800.0
            )

        with col2:
            pilot_height = st.number_input(
                "Liquid Height (mm)",
                value=900.0
            )

            pilot_rpm = st.number_input(
                "Agitator RPM",
                value=250.0
            )

        with col3:
            pilot_density = st.number_input(
                "Density (kg/m³)",
                value=1000.0
            )

            pilot_viscosity = st.number_input(
                "Viscosity (cP)",
                value=1.0
            )

        pilot_bottom = st.selectbox(
            "Bottom Type",
            [
                "10% Torispherical",
                "6% Torispherical",
                "2:1 Ellipsoidal",
                "Flat Bottom",
                "Hemispherical"
            ]
        )

        st.success("Pilot reactor data entered.")

    with tab2:

        st.subheader("Commercial Reactor")

        col1, col2, col3 = st.columns(3)

        with col1:

            commercial_volume = st.number_input(
                "Working Volume (L)",
                value=5000.0
            )

            commercial_id = st.number_input(
                "Tank ID (mm)",
                value=1800.0
            )

        with col2:

            commercial_height = st.number_input(
                "Liquid Height (mm)",
                value=2200.0
            )

            commercial_rpm = st.number_input(
                "Agitator RPM",
                value=110.0
            )

        with col3:

            commercial_density = st.number_input(
                "Density (kg/m³)",
                value=1000.0
            )

            commercial_viscosity = st.number_input(
                "Viscosity (cP)",
                value=1.0
            )

        commercial_bottom = st.selectbox(
            "Bottom Type",
            [
                "10% Torispherical",
                "6% Torispherical",
                "2:1 Ellipsoidal",
                "Flat Bottom",
                "Hemispherical"
            ]
        )

        st.success("Commercial reactor data entered.")

# ---------------------------------------------------------
# AGITATOR
# ---------------------------------------------------------

elif page == "🔄 Agitator":

    st.header("🔄 Agitator Selection")

    agitator_type = st.selectbox(
        "Select Agitator Type",
        list(agitators.keys())
    )

    data = agitators[agitator_type]

    col1, col2, col3 = st.columns(3)

    col1.metric("Power Number Np", data["Np"])
    col2.metric("Pumping Number Nq", data["Nq"])
    col3.metric("Application", data["application"])

    st.divider()

    st.subheader("Impeller Geometry")

    col1, col2, col3 = st.columns(3)

    with col1:
        tank_diameter = st.number_input(
            "Tank Diameter (m)",
            value=1.8
        )

    with col2:
        impeller_diameter = st.number_input(
            "Impeller Diameter (m)",
            value=0.6
        )

    with col3:
        number_impellers = st.number_input(
            "Number of Impellers",
            min_value=1,
            max_value=3,
            value=1
        )

    d_t = impeller_diameter / tank_diameter

    st.metric("Impeller / Tank Ratio D/T", round(d_t, 3))

# ---------------------------------------------------------
# CALCULATIONS
# ---------------------------------------------------------

elif page == "🧮 Calculations":

    st.header("🧮 Mixing Calculations")

    st.subheader("Input")

    col1, col2, col3 = st.columns(3)

    with col1:

        rho = st.number_input(
            "Density (kg/m³)",
            value=1000.0
        )

        rpm = st.number_input(
            "RPM",
            value=250.0
        )

    with col2:

        impeller_d = st.number_input(
            "Impeller Diameter (m)",
            value=0.6
        )

        np_value = st.number_input(
            "Power Number (Np)",
            value=1.5
        )

    with col3:

        volume = st.number_input(
            "Working Volume (m³)",
            value=5.0
        )

        nq_value = st.number_input(
            "Pumping Number (Nq)",
            value=0.75
        )

    # RPM → rev/s
    N = rpm / 60

    # POWER
    power_w = (
        np_value
        * rho
        * N**3
        * impeller_d**5
    )

    power_kw = power_w / 1000

    # P/V
    pv = power_kw / volume

    # TIP SPEED
    tip_speed = math.pi * impeller_d * N

    # PUMPING
    pumping = nq_value * N * impeller_d**3

    # PUMPING IN m3/h
    pumping_m3h = pumping * 3600

    # RESULTS

    st.divider()

    st.subheader("Results")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Power",
        f"{power_kw:.2f} kW"
    )

    col2.metric(
        "P/V",
        f"{pv:.2f} kW/m³"
    )

    col3.metric(
        "Tip Speed",
        f"{tip_speed:.2f} m/s"
    )

    col4.metric(
        "Pumping",
        f"{pumping_m3h:.1f} m³/h"
    )

    st.divider()

    st.warning(
        "Engineering note: Np and Nq are correlation-dependent. "
        "Use validated vendor/literature data for final design."
    )

# ---------------------------------------------------------
# SCALE-UP
# ---------------------------------------------------------

elif page == "📊 Scale-Up":

    st.header("📊 Pilot → Commercial Scale-Up")

    st.subheader("Scale-Up Basis")

    basis = st.selectbox(
        "Select Scale-Up Criterion",
        [
            "Constant P/V",
            "Constant Tip Speed",
            "Constant N/Njs",
            "Constant Pumping/V",
            "User Defined"
        ]
    )

    st.info(
        f"Selected scale-up basis: {basis}"
    )

    st.subheader("Pilot")

    pilot_volume = st.number_input(
        "Pilot Volume (m³)",
        value=0.5
    )

    pilot_d = st.number_input(
        "Pilot Impeller Diameter (m)",
        value=0.30
    )

    pilot_rpm = st.number_input(
        "Pilot RPM",
        value=250.0
    )

    st.subheader("Commercial")

    commercial_volume = st.number_input(
        "Commercial Volume (m³)",
        value=5.0
    )

    commercial_d = st.number_input(
        "Commercial Impeller Diameter (m)",
        value=0.85
    )

    # SCALE-UP CALCULATIONS

    pilot_N = pilot_rpm / 60

    pilot_tip = math.pi * pilot_d * pilot_N

    if basis == "Constant Tip Speed":

        commercial_N = pilot_tip / (
            math.pi * commercial_d
        )

    elif basis == "Constant P/V":

        commercial_N = pilot_N * (
            pilot_d / commercial_d
        ) ** (5 / 3)

    else:

        commercial_N = pilot_N * (
            pilot_volume / commercial_volume
        ) ** (1 / 3)

    commercial_rpm = commercial_N * 60

    commercial_tip = (
        math.pi
        * commercial_d
        * commercial_N
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Pilot Tip Speed",
            f"{pilot_tip:.2f} m/s"
        )

    with col2:

        st.metric(
            "Commercial RPM",
            f"{commercial_rpm:.1f} RPM"
        )

    st.metric(
        "Commercial Tip Speed",
        f"{commercial_tip:.2f} m/s"
    )

# ---------------------------------------------------------
# LIBRARY
# ---------------------------------------------------------

elif page == "📚 Agitator Library":

    st.header("📚 Agitator Library")

    for name, data in agitators.items():

        st.subheader(name)

        st.write(
            f"**Np:** {data['Np']}"
        )

        st.write(
            f"**Nq:** {data['Nq']}"
        )

        st.write(
            f"**Application:** {data['application']}"
        )

        st.divider()
