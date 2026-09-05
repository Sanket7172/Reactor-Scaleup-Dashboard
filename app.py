import io
import math

import pandas as pd
import streamlit as st

from libraries.agitator_library import (
    AGITATORS
)

from libraries.reactor_geometry_library import (
    BOTTOM_GEOMETRIES,
    TOP_GEOMETRIES
)

from libraries.baffle_library import (
    BAFFLES
)

from calculations.geometry import (
    calculate_total_geometry,
    calculate_liquid_height
)

from calculations.mixing import (
    calculate_mixing
)

from calculations.njs import (
    calculate_njs
)

from calculations.scaleup import (
    calculate_scaleup_rpm
)

from calculations.validation import (
    validation_checks
)

from visualization.reactor_3d import (
    create_reactor_3d
)


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Reactor Scale-Up Engineering Dashboard",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1700px;
        padding-top: 1rem;
    }

    .metric-card {
        border: 1px solid #d9e1ea;
        border-radius: 12px;
        padding: 12px;
        background: #ffffff;
    }

    .title {
        font-size: 2.2rem;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SESSION MEMORY
# =========================================================

if "project" not in st.session_state:

    st.session_state.project = {

        "name":
            "New Reactor Scale-Up Study",

        "product":
            "",

        "engineer":
            "",

        "reaction":
            "Liquid-Liquid",

        "analysis_mode":
            "Single Reactor",

        "criterion":
            "Constant P/V"
    }


if "reactors" not in st.session_state:

    st.session_state.reactors = {}


if "selected_reactor" not in st.session_state:

    st.session_state.selected_reactor = "Pilot"


# =========================================================
# REACTION TYPES
# =========================================================

REACTIONS = [

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


# =========================================================
# ANALYSIS MODES
# =========================================================

ANALYSIS_MODES = [

    "Single Reactor",

    "Lab vs Pilot",

    "Pilot vs Commercial",

    "Lab vs Commercial",

    "Lab vs Pilot vs Commercial"
]


# =========================================================
# SCALEUP
# =========================================================

CRITERIA = [

    "Constant P/V",

    "Constant Tip Speed",

    "Constant RPM",

    "Constant Froude Number",

    "Constant Reynolds Number",

    "Constant Pumping / Volume"
]


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "⚗️ Reactor Engineering"
)

page = st.sidebar.radio(

    "Engineering Module",

    [

        "🏠 Dashboard",

        "📋 Project",

        "⚙️ Reactor",

        "🔄 Agitator",

        "📊 Scale-Up",

        "🧱 Solid-Liquid",

        "💨 Gas-Liquid",

        "🧊 3D Reactor",

        "✓ Validation",

        "📚 Libraries",

        "📥 Excel Export"
    ]
)


# =========================================================
# PROJECT
# =========================================================

if page == "📋 Project":

    st.header(
        "📋 Project & Analysis Configuration"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.session_state.project["name"] = (
            st.text_input(
                "Project Name",
                st.session_state.project["name"]
            )
        )

        st.session_state.project["product"] = (
            st.text_input(
                "Product / Process",
                st.session_state.project["product"]
            )
        )

        st.session_state.project["engineer"] = (
            st.text_input(
                "Process Engineer",
                st.session_state.project["engineer"]
            )
        )

    with c2:

        reaction = st.selectbox(

            "Reaction / Process Type",

            REACTIONS,

            index=REACTIONS.index(
                st.session_state.project[
                    "reaction"
                ]
            )
        )

        st.session_state.project[
            "reaction"
        ] = reaction

        mode = st.selectbox(

            "Analysis Mode",

            ANALYSIS_MODES,

            index=ANALYSIS_MODES.index(
                st.session_state.project[
                    "analysis_mode"
                ]
            )
        )

        st.session_state.project[
            "analysis_mode"
        ] = mode

        criterion = st.selectbox(

            "Primary Scale-Up Criterion",

            CRITERIA,

            index=CRITERIA.index(
                st.session_state.project[
                    "criterion"
                ]
            )
        )

        st.session_state.project[
            "criterion"
        ] = criterion

    st.success(
        "Project configuration is retained automatically during the session."
    )

    st.info(
        """
        You can now perform:

        • One reactor calculation

        • Lab → Pilot

        • Pilot → Commercial

        • Lab → Commercial

        • Lab → Pilot → Commercial
        """
    )


# =========================================================
# REACTOR CONFIGURATION
# =========================================================

elif page == "⚙️ Reactor":

    st.header(
        "⚙️ Reactor Configuration"
    )

    scale = st.selectbox(

        "Select Reactor",

        [
            "Lab",
            "Pilot",
            "Commercial"
        ]
    )

    if scale not in st.session_state.reactors:

        st.session_state.reactors[
            scale
        ] = {

            "working_volume_l":
                500,

            "tank_d":
                1.0,

            "straight_height":
                1.2,

            "bottom":
                "10% Torispherical",

            "top":
                "Flat Top",

            "rho":
                1000.0,

            "viscosity":
                1.0,

            "sigma":
                72.0,

            "rpm":
                150.0,

            "baffle":
                "Standard Vertical",

            "baffle_width":
                0.10,

            "impellers":
                []
        }

    r = st.session_state.reactors[
        scale
    ]

    st.subheader(
        f"{scale} Reactor"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        r["working_volume_l"] = st.number_input(

            "Working Volume (L)",

            min_value=0.1,

            value=float(
                r["working_volume_l"]
            ),

            key=f"{scale}_volume"
        )

        r["tank_d"] = st.number_input(

            "Tank ID (m)",

            min_value=0.01,

            value=float(
                r["tank_d"]
            ),

            key=f"{scale}_tank"
        )

        r["straight_height"] = st.number_input(

            "Straight-Side Height (m)",

            min_value=0.01,

            value=float(
                r["straight_height"]
            ),

            key=f"{scale}_height"
        )

    with c2:

        r["bottom"] = st.selectbox(

            "Bottom Geometry",

            list(
                BOTTOM_GEOMETRIES.keys()
            ),

            index=list(
                BOTTOM_GEOMETRIES.keys()
            ).index(
                r["bottom"]
            ),

            key=f"{scale}_bottom"
        )

        r["top"] = st.selectbox(

            "Top Geometry",

            list(
                TOP_GEOMETRIES.keys()
            ),

            index=list(
                TOP_GEOMETRIES.keys()
            ).index(
                r["top"]
            ),

            key=f"{scale}_top"
        )

        r["rpm"] = st.number_input(

            "Agitator RPM",

            min_value=0.1,

            value=float(
                r["rpm"]
            ),

            key=f"{scale}_rpm"
        )

    with c3:

        r["rho"] = st.number_input(

            "Liquid Density (kg/m³)",

            min_value=0.1,

            value=float(
                r["rho"]
            ),

            key=f"{scale}_rho"
        )

        r["viscosity"] = st.number_input(

            "Viscosity (cP)",

            min_value=0.01,

            value=float(
                r["viscosity"]
            ),

            key=f"{scale}_viscosity"
        )

        r["sigma"] = st.number_input(

            "Surface Tension (mN/m)",

            min_value=0.01,

            value=float(
                r["sigma"]
            ),

            key=f"{scale}_sigma"
        )

    # ============================================
    # AUTOMATIC GEOMETRY
    # ============================================

    geometry = calculate_total_geometry(

        r["tank_d"],

        r["straight_height"],

        r["bottom"],

        r["top"]
    )

    liquid_height = calculate_liquid_height(

        r["working_volume_l"] / 1000,

        r["tank_d"],

        r["straight_height"],

        r["bottom"]
    )

    r["volume_m3"] = (
        r["working_volume_l"] / 1000
    )

    r["liquid_height"] = liquid_height

    r["bottom_depth"] = (
        geometry[
            "bottom_depth_m"
        ]
    )

    r["top_depth"] = (
        geometry[
            "top_depth_m"
        ]
    )

    st.divider()

    st.subheader(
        "📐 Automatic Geometry Calculation"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Working Volume",
        f"{r['working_volume_l']:.1f} L"
    )

    c2.metric(
        "Calculated Liquid Height",
        f"{liquid_height:.3f} m"
    )

    c3.metric(
        "Bottom Depth",
        f"{r['bottom_depth']:.3f} m"
    )

    c4.metric(
        "Total Vessel Geometry Volume",
        f"{geometry['total_volume_m3']:.2f} m³"
    )

    st.info(
        "Liquid height is calculated automatically from working volume, tank diameter and bottom geometry."
    )

    # ============================================
    # BAFFLES
    # ============================================

    st.subheader(
        "🧱 Baffle Configuration"
    )

    r["baffle"] = st.selectbox(

        "Baffle Type",

        list(
            BAFFLES.keys()
        ),

        key=f"{scale}_baffle"
    )

    baffle_data = BAFFLES[
        r["baffle"]
    ]

    c1, c2 = st.columns(2)

    with c1:

        r["baffle_number"] = st.number_input(

            "Number of Baffles",

            min_value=0,

            max_value=12,

            value=int(
                baffle_data[
                    "number"
                ]
            ),

            key=f"{scale}_baffle_number"
        )

    with c2:

        r["baffle_width"] = st.number_input(

            "Baffle Width (m)",

            min_value=0.0,

            value=float(
                r.get(
                    "baffle_width",
                    r["tank_d"]
                    * baffle_data[
                        "width_ratio"
                    ]
                )
            ),

            key=f"{scale}_baffle_width"
        )

    st.session_state.reactors[
        scale
    ] = r

    st.success(
        f"{scale} reactor data automatically retained."
    )


# =========================================================
# AGITATOR
# =========================================================

elif page == "🔄 Agitator":

    st.header(
        "🔄 Agitator Configuration"
    )

    scale = st.selectbox(

        "Reactor",

        [
            "Lab",
            "Pilot",
            "Commercial"
        ]
    )

    if scale not in st.session_state.reactors:

        st.warning(
            "Configure the reactor first."
        )

        st.stop()

    r = st.session_state.reactors[
        scale
    ]

    number = st.number_input(

        "Number of Impellers",

        min_value=1,

        max_value=3,

        value=max(
            1,
            len(
                r.get(
                    "impellers",
                    []
                )
            )
        )
    )

    r["impellers"] = []

    for i in range(
        int(number)
    ):

        st.subheader(
            f"Impeller {i + 1}"
        )

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            impeller_type = st.selectbox(

                "Agitator Type",

                list(
                    AGITATORS.keys()
                ),

                key=f"{scale}_imp_type_{i}"
            )

        data = AGITATORS[
            impeller_type
        ]

        with c2:

            diameter = st.number_input(

                "Impeller Diameter (m)",

                min_value=0.01,

                value=float(
                    r["tank_d"]
                    * data[
                        "recommended_DT"
                    ]
                ),

                key=f"{scale}_imp_d_{i}"
            )

        with c3:

            elevation = st.number_input(

                "Elevation from Bottom (m)",

                min_value=0.0,

                value=float(
                    r["liquid_height"]
                    * (
                        0.25
                        + i * 0.25
                    )
                ),

                key=f"{scale}_imp_elev_{i}"
            )

        with c4:

            active = st.checkbox(

                "Active",

                value=True,

                key=f"{scale}_imp_active_{i}"
            )

        st.caption(
            f"""
            Flow: {data['flow']} |
            Np: {data['Np']} |
            Nq: {data['Nq']} |
            Application: {data['application']}
            """
        )

        r["impellers"].append({

            "type":
                impeller_type,

            "diameter":
                diameter,

            "elevation":
                elevation,

            "Np":
                data["Np"],

            "Nq":
                data["Nq"],

            "blades":
                data["blades"],

            "active":
                active
        })

    # ============================================
    # CALCULATE
    # ============================================

    result = calculate_mixing(

        r["volume_m3"],

        r["rho"],

        r["viscosity"],

        r["rpm"],

        r["impellers"]
    )

    r.update(
        result
    )

    # Representative tip speed
    active_impellers = [
        x for x in r["impellers"]
        if x["active"]
    ]

    if active_impellers:

        largest = max(
            active_impellers,
            key=lambda x: x["diameter"]
        )

        r["impeller_d"] = (
            largest["diameter"]
        )

        r["Tip Speed m/s"] = (
            math.pi
            * largest["diameter"]
            * r["rpm"]
            / 60
        )

    st.session_state.reactors[
        scale
    ] = r

    st.divider()

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Power",
        f"{r['Power kW']:.2f} kW"
    )

    c2.metric(
        "P/V",
        f"{r['P/V kW/m3']:.2f} kW/m³"
    )

    c3.metric(
        "Pumping",
        f"{r['Pumping m3/h']:.1f} m³/h"
    )

    c4.metric(
        "Q/V",
        f"{r['Q/V 1/h']:.1f} 1/h"
    )

    c5.metric(
        "Torque",
        f"{r['Torque Nm']:.1f} Nm"
    )

    st.dataframe(

        pd.DataFrame(
            r["Impellers"]
        ),

        use_container_width=True,

        hide_index=True
    )


# =========================================================
# DASHBOARD
# =========================================================

elif page == "🏠 Dashboard":

    st.header(
        "🏭 Reactor Scale-Up & Mixing Dashboard"
    )

    st.caption(
        "Process Engineering Decision Support System"
    )

    st.info(
        f"""
        **Project:** {st.session_state.project['name']}

        **Reaction:** {st.session_state.project['reaction']}

        **Analysis:** {st.session_state.project['analysis_mode']}

        **Scale-Up Basis:** {st.session_state.project['criterion']}
        """
    )

    rows = []

    for name, r in st.session_state.reactors.items():

        if "Power kW" not in r:

            continue

        rows.append({

            "Reactor":
                name,

            "Working Volume L":
                r["volume_m3"] * 1000,

            "Liquid Height m":
                r["liquid_height"],

            "RPM":
                r["rpm"],

            "Power kW":
                r["Power kW"],

            "P/V kW/m3":
                r["P/V kW/m3"],

            "Tip Speed m/s":
                r.get(
                    "Tip Speed m/s",
                    0
                ),

            "Pumping m3/h":
                r["Pumping m3/h"],

            "Q/V 1/h":
                r["Q/V 1/h"],

            "Turnover min":
                r["Turnover min"]
        })

    if rows:

        st.dataframe(

            pd.DataFrame(rows),

            use_container_width=True,

            hide_index=True
        )

    else:

        st.warning(
            "Configure a reactor and agitator to generate results."
        )


# =========================================================
# SCALE-UP
# =========================================================

elif page == "📊 Scale-Up":

    st.header(
        "📊 Scale-Up Engine"
    )

    mode = st.session_state.project[
        "analysis_mode"
    ]

    criterion = st.selectbox(
        "Scale-Up Criterion",
        CRITERIA,
        index=CRITERIA.index(
            st.session_state.project[
                "criterion"
            ]
        )
    )

    if mode == "Single Reactor":

        st.info(
            "Single Reactor mode selected. No comparison is required."
        )

    else:

        pairs = {

            "Lab vs Pilot":
                ("Lab", "Pilot"),

            "Pilot vs Commercial":
                ("Pilot", "Commercial"),

            "Lab vs Commercial":
                ("Lab", "Commercial")
        }

        if mode in pairs:

            reference_name, target_name = (
                pairs[mode]
            )

            reference = (
                st.session_state.reactors.get(
                    reference_name
                )
            )

            target = (
                st.session_state.reactors.get(
                    target_name
                )
            )

            if not reference or not target:

                st.warning(
                    f"Configure {reference_name} and {target_name} reactors first."
                )

            else:

                calculated_rpm = (
                    calculate_scaleup_rpm(
                        criterion,
                        reference,
                        target
                    )
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    f"{reference_name} RPM",
                    f"{reference['rpm']:.1f}"
                )

                c2.metric(
                    f"Calculated {target_name} RPM",
                    f"{calculated_rpm:.1f}"
                )

                c3.metric(
                    f"Actual {target_name} RPM",
                    f"{target['rpm']:.1f}"
                )

                deviation = (

                    (
                        target["rpm"]
                        - calculated_rpm
                    )
                    / calculated_rpm
                    * 100

                    if calculated_rpm
                    else 0
                )

                st.metric(
                    "RPM Deviation",
                    f"{deviation:.1f}%"
                )

                comparison = pd.DataFrame({

                    "Parameter": [

                        "Working Volume L",

                        "RPM",

                        "Power kW",

                        "P/V kW/m3",

                        "Tip Speed m/s",

                        "Pumping m3/h",

                        "Q/V 1/h",

                        "Turnover min"
                    ],

                    reference_name: [

                        reference[
                            "volume_m3"
                        ] * 1000,

                        reference[
                            "rpm"
                        ],

                        reference.get(
                            "Power kW",
                            0
                        ),

                        reference.get(
                            "P/V kW/m3",
                            0
                        ),

                        reference.get(
                            "Tip Speed m/s",
                            0
                        ),

                        reference.get(
                            "Pumping m3/h",
                            0
                        ),

                        reference.get(
                            "Q/V 1/h",
                            0
                        ),

                        reference.get(
                            "Turnover min",
                            0
                        )
                    ],

                    target_name: [

                        target[
                            "volume_m3"
                        ] * 1000,

                        target[
                            "rpm"
                        ],

                        target.get(
                            "Power kW",
                            0
                        ),

                        target.get(
                            "P/V kW/m3",
                            0
                        ),

                        target.get(
                            "Tip Speed m/s",
                            0
                        ),

                        target.get(
                            "Pumping m3/h",
                            0
                        ),

                        target.get(
                            "Q/V 1/h",
                            0
                        ),

                        target.get(
                            "Turnover min",
                            0
                        )
                    ]
                })

                st.dataframe(
                    comparison,
                    use_container_width=True,
                    hide_index=True
                )

        elif mode == "Lab vs Pilot vs Commercial":

            available = [

                x for x in
                [
                    "Lab",
                    "Pilot",
                    "Commercial"
                ]

                if x in
                st.session_state.reactors
            ]

            rows = []

            for name in available:

                r = (
                    st.session_state.reactors[
                        name
                    ]
                )

                rows.append({

                    "Parameter":
                        name,

                    "Volume L":
                        r.get(
                            "volume_m3",
                            0
                        ) * 1000,

                    "RPM":
                        r.get(
                            "rpm",
                            0
                        ),

                    "Power kW":
                        r.get(
                            "Power kW",
                            0
                        ),

                    "P/V":
                        r.get(
                            "P/V kW/m3",
                            0
                        ),

                    "Tip Speed":
                        r.get(
                            "Tip Speed m/s",
                            0
                        ),

                    "Pumping":
                        r.get(
                            "Pumping m3/h",
                            0
                        ),

                    "Q/V":
                        r.get(
                            "Q/V 1/h",
                            0
                        ),

                    "Turnover":
                        r.get(
                            "Turnover min",
                            0
                        )
                })

            if rows:

                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True
                )


# =========================================================
# SOLID LIQUID
# =========================================================

elif page == "🧱 Solid-Liquid":

    st.header(
        "🧱 Solid-Liquid Suspension"
    )

    reactor_name = st.selectbox(

        "Reactor",

        list(
            st.session_state.reactors.keys()
        )
    )

    if reactor_name:

        r = (
            st.session_state.reactors[
                reactor_name
            ]
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            rho_solid = st.number_input(
                "Solid Density kg/m³",
                value=2500.0
            )

        with c2:

            particle_size = st.number_input(
                "Particle Size µm",
                value=100.0
            )

        with c3:

            solids = st.number_input(
                "Solids wt%",
                value=10.0
            )

        suspension_factor = st.number_input(
            "Suspension Correlation Factor",
            value=1.30
        )

        impeller_d = r.get(
            "impeller_d",
            0.3
        )

        njs = calculate_njs(

            r["rho"],

            rho_solid,

            particle_size,

            solids,

            impeller_d,

            suspension_factor
        )

        ratio = (
            r["rpm"]
            / njs
            if njs > 0
            else 0
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Njs",
            f"{njs:.1f} RPM"
        )

        c2.metric(
            "Actual RPM",
            f"{r['rpm']:.1f}"
        )

        c3.metric(
            "N/Njs",
            f"{ratio:.2f}"
        )

        if ratio >= 1.2:

            st.success(
                "PASS — Agitation is above the screening Njs margin."
            )

        elif ratio >= 1.0:

            st.warning(
                "WARNING — Suspension is close to Njs."
            )

        else:

            st.error(
                "FAIL — Agitation is below estimated Njs."
            )

        st.caption(
            "Engineering screening correlation only. Validate Njs against pilot/vendor/CFD data before final design."
        )


# =========================================================
# GAS LIQUID
# =========================================================

elif page == "💨 Gas-Liquid":

    st.header(
        "💨 Gas-Liquid Mixing"
    )

    reactor_name = st.selectbox(

        "Reactor",

        list(
            st.session_state.reactors.keys()
        )
    )

    if reactor_name:

        r = (
            st.session_state.reactors[
                reactor_name
            ]
        )

        gas_flow = st.number_input(
            "Gas Flow Nm³/h",
            value=25.0
        )

        area = (
            math.pi
            * r["tank_d"]**2
            / 4
        )

        superficial_velocity = (

            gas_flow / 3600
        ) / area

        vvm = (

            gas_flow
            / 60
            / r["volume_m3"]
        )

        st.metric(
            "VVM",
            f"{vvm:.3f}"
        )

        st.metric(
            "Superficial Gas Velocity",
            f"{superficial_velocity:.4f} m/s"
        )

        st.info(
            "Gas holdup and kLa require validated gas-liquid correlations and should not be treated as universal constants."
        )


# =========================================================
# 3D REACTOR
# =========================================================

elif page == "🧊 3D Reactor":

    st.header(
        "🧊 3D Reactor Geometry"
    )

    reactor_name = st.selectbox(

        "Select Reactor",

        list(
            st.session_state.reactors.keys()
        )
    )

    r = (
        st.session_state.reactors[
            reactor_name
        ]
    )

    if not r.get(
        "impellers"
    ):

        st.warning(
            "Configure agitators first."
        )

    else:

        fig = create_reactor_3d(

            r["tank_d"],

            r["liquid_height"],

            r["straight_height"],

            r["bottom_depth"],

            r["top_depth"],

            r["impellers"],

            r.get(
                "baffle_number",
                4
            ),

            r.get(
                "baffle_width",
                0.1
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.caption(
            "Conceptual 3D engineering visualization — not a CFD/CAD model."
        )


# =========================================================
# VALIDATION
# =========================================================

elif page == "✓ Validation":

    st.header(
        "✓ Engineering Validation"
    )

    if not st.session_state.reactors:

        st.warning(
            "No reactor configured."
        )

    else:

        reactor_name = st.selectbox(

            "Reactor",

            list(
                st.session_state.reactors.keys()
            )
        )

        r = (
            st.session_state.reactors[
                reactor_name
            ]
        )

        checks = validation_checks(
            r
        )

        for status, message in checks:

            if status == "PASS":

                st.success(
                    f"✓ {message}"
                )

            elif status == "WARNING":

                st.warning(
                    f"⚠ {message}"
                )

            else:

                st.error(
                    f"✕ {message}"
                )


# =========================================================
# LIBRARIES
# =========================================================

elif page == "📚 Libraries":

    st.header(
        "📚 Engineering Libraries"
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "Agitators",
            "Baffles",
            "Geometry"
        ]
    )

    with tab1:

        rows = []

        for name, data in AGITATORS.items():

            rows.append({

                "Agitator":
                    name,

                "Category":
                    data["category"],

                "Flow":
                    data["flow"],

                "Np":
                    data["Np"],

                "Nq":
                    data["Nq"],

                "Blades":
                    data["blades"],

                "Recommended D/T":
                    data["recommended_DT"],

                "Application":
                    data["application"],

                "Reference":
                    data["reference"]
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

    with tab2:

        st.dataframe(
            pd.DataFrame(
                BAFFLES
            ).T,
            use_container_width=True
        )

    with tab3:

        st.subheader(
            "Bottom Geometry"
        )

        st.dataframe(
            pd.DataFrame(
                BOTTOM_GEOMETRIES
            ).T,
            use_container_width=True
        )

        st.subheader(
            "Top Geometry"
        )

        st.dataframe(
            pd.DataFrame(
                TOP_GEOMETRIES
            ).T,
            use_container_width=True
        )


# =========================================================
# EXCEL EXPORT
# =========================================================

elif page == "📥 Excel Export":

    st.header(
        "📥 Engineering Excel Export"
    )

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        # ============================================
        # PROJECT
        # ============================================

        pd.DataFrame(
            [
                st.session_state.project
            ]
        ).to_excel(
            writer,
            sheet_name="Project",
            index=False
        )

        # ============================================
        # REACTOR INPUTS + RESULTS
        # ============================================

        for name, r in (
            st.session_state.reactors.items()
        ):

            reactor_data = {

                "Reactor":
                    name,

                "Working Volume L":
                    r.get(
                        "working_volume_l"
                    ),

                "Tank ID m":
                    r.get(
                        "tank_d"
                    ),

                "Straight Height m":
                    r.get(
                        "straight_height"
                    ),

                "Bottom":
                    r.get(
                        "bottom"
                    ),

                "Top":
                    r.get(
                        "top"
                    ),

                "Calculated Liquid Height m":
                    r.get(
                        "liquid_height"
                    ),

                "Bottom Depth m":
                    r.get(
                        "bottom_depth"
                    ),

                "Top Depth m":
                    r.get(
                        "top_depth"
                    ),

                "Density kg/m3":
                    r.get(
                        "rho"
                    ),

                "Viscosity cP":
                    r.get(
                        "viscosity"
                    ),

                "RPM":
                    r.get(
                        "rpm"
                    ),

                "Power kW":
                    r.get(
                        "Power kW"
                    ),

                "P/V kW/m3":
                    r.get(
                        "P/V kW/m3"
                    ),

                "Pumping m3/h":
                    r.get(
                        "Pumping m3/h"
                    ),

                "Q/V 1/h":
                    r.get(
                        "Q/V 1/h"
                    ),

                "Turnover min":
                    r.get(
                        "Turnover min"
                    ),

                "Torque Nm":
                    r.get(
                        "Torque Nm"
                    )
            }

            pd.DataFrame(
                [reactor_data]
            ).to_excel(
                writer,
                sheet_name=f"{name} Reactor",
                index=False
            )

            # ========================================
            # IMPELLERS
            # ========================================

            if r.get(
                "Impellers"
            ):

                pd.DataFrame(
                    r["Impellers"]
                ).to_excel(
                    writer,
                    sheet_name=f"{name} Impellers",
                    index=False
                )

        # ============================================
        # COMPARISON
        # ============================================

        comparison_rows = []

        for name, r in (
            st.session_state.reactors.items()
        ):

            comparison_rows.append({

                "Reactor":
                    name,

                "Volume L":
                    r.get(
                        "volume_m3",
                        0
                    ) * 1000,

                "Liquid Height m":
                    r.get(
                        "liquid_height",
                        0
                    ),

                "RPM":
                    r.get(
                        "rpm",
                        0
                    ),

                "Power kW":
                    r.get(
                        "Power kW",
                        0
                    ),

                "P/V kW/m3":
                    r.get(
                        "P/V kW/m3",
                        0
                    ),

                "Tip Speed m/s":
                    r.get(
                        "Tip Speed m/s",
                        0
                    ),

                "Pumping m3/h":
                    r.get(
                        "Pumping m3/h",
                        0
                    ),

                "Q/V 1/h":
                    r.get(
                        "Q/V 1/h",
                        0
                    ),

                "Turnover min":
                    r.get(
                        "Turnover min",
                        0
                    )
            })

        pd.DataFrame(
            comparison_rows
        ).to_excel(
            writer,
            sheet_name="Comparison",
            index=False
        )

        # ============================================
        # AGITATOR LIBRARY
        # ============================================

        agitator_rows = []

        for name, data in AGITATORS.items():

            row = {
                "Agitator":
                    name
            }

            row.update(data)

            agitator_rows.append(
                row
            )

        pd.DataFrame(
            agitator_rows
        ).to_excel(
            writer,
            sheet_name="Agitator Library",
            index=False
        )

    st.download_button(

        "⬇️ Download Complete Engineering Excel",

        output.getvalue(),

        file_name=(
            "Reactor_ScaleUp_Engineering.xlsx"
        ),

        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    st.success(
        "Complete engineering workbook generated."
    )
