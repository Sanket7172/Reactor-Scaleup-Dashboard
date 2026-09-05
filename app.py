# ============================================================
# REACTOR SCALE-UP & MIXING ENGINEERING DASHBOARD
# ============================================================
# File: app.py
#
# Purpose:
#   Professional Streamlit dashboard for:
#   - Reactor geometry
#   - Agitator selection
#   - Mixing calculations
#   - Scale-up studies
#   - P/V
#   - Tip speed
#   - Power
#   - Pumping
#   - Reynolds number
#   - Froude number
#   - Njs screening
#   - KLa screening
#   - Blend-time screening
#   - Heat-transfer area
#   - 3D reactor visualization
#   - Validation checks
#   - Excel export
#   - Browser persistence
#
# Deployment:
#   GitHub + Streamlit Community Cloud
# ============================================================

import json
import hashlib
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

# ------------------------------------------------------------
# LOCAL STORAGE
# ------------------------------------------------------------

try:
    from streamlit_local_storage import LocalStorage

    LOCAL_STORAGE_AVAILABLE = True
    storage = LocalStorage()

except ImportError:
    LOCAL_STORAGE_AVAILABLE = False
    storage = None


# ------------------------------------------------------------
# PROJECT MODULE IMPORTS
# ------------------------------------------------------------

from calculations.engine import calculate_reactor
from calculations.engine import compare_reactors
from calculations.engine import validation_checks

from libraries.agitator_geometry import (
    AGITATOR_LIBRARY,
    get_agitator,
)

from libraries.reactor_geometry import (
    REACTOR_GEOMETRY_LIBRARY,
    calculate_liquid_height,
    calculate_total_volume,
)

from visualization.reactor_3d import create_reactor_3d


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main application */

    .main {
        background-color: #f7f9fc;
    }

    /* Title */

    .dashboard-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .dashboard-subtitle {
        color: #6b7280;
        font-size: 15px;
        margin-bottom: 20px;
    }

    /* Cards */

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.04);
    }

    .metric-title {
        color: #6b7280;
        font-size: 13px;
        margin-bottom: 4px;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 700;
    }

    /* Section */

    .section-title {
        font-size: 21px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 8px;
    }

    /* Status */

    .status-pass {
        background-color: #dcfce7;
        color: #166534;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: 600;
    }

    .status-warning {
        background-color: #fef3c7;
        color: #92400e;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: 600;
    }

    .status-fail {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: 600;
    }

    /* Sidebar */

    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONSTANTS
# ============================================================

STORAGE_KEY = "reactor_scaleup_dashboard_project_v1"

SCALE_OPTIONS = [
    "Lab",
    "Pilot",
    "Commercial",
]

STUDY_MODES = {
    "Single Reactor": ["Lab"],
    "Lab vs Pilot": ["Lab", "Pilot"],
    "Pilot vs Commercial": ["Pilot", "Commercial"],
    "Lab vs Commercial": ["Lab", "Commercial"],
    "Lab vs Pilot vs Commercial": [
        "Lab",
        "Pilot",
        "Commercial",
    ],
}

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
    "Other",
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
    "User Defined",
]


# ============================================================
# DEFAULT REACTOR DATA
# ============================================================

DEFAULT_REACTOR = {
    "working_volume": 1000.0,
    "tank_id": 1000.0,
    "straight_side_height": 1500.0,

    "bottom_type": "2:1 Ellipsoidal",
    "top_type": "2:1 Ellipsoidal",

    "rpm": 100.0,

    "impeller_type": "Pitched Blade Turbine",
    "impeller_diameter": 400.0,
    "number_of_impellers": 1,

    "impeller_clearance": 200.0,

    "density": 1000.0,
    "viscosity": 1.0,
    "surface_tension": 0.072,

    "solid_density": 2500.0,
    "solid_concentration": 0.0,
    "particle_size": 100.0,

    "gas_flow": 0.0,

    "baffles": 4,
    "baffle_width": 100.0,

    "np_override": None,
    "nq_override": None,

    "suspension_s": None,

    "kla_coefficient": 0.20,

    "blend_coefficient": 5.0,

    "notes": "",
}


# ============================================================
# DEFAULT PROJECT
# ============================================================

DEFAULT_PROJECT = {
    "project_name": "New Reactor Scale-Up Study",

    "project_number": "",
    "prepared_by": "",
    "company": "",

    "reaction_type": "Liquid-Liquid",

    "study_mode": "Lab vs Pilot vs Commercial",

    "scale_up_criterion": "Constant P/V",

    "selected_scales": [
        "Lab",
        "Pilot",
        "Commercial",
    ],

    "reactors": {
        "Lab": DEFAULT_REACTOR.copy(),
        "Pilot": DEFAULT_REACTOR.copy(),
        "Commercial": DEFAULT_REACTOR.copy(),
    },
}


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

def initialize_session_state():

    if "project" not in st.session_state:

        st.session_state.project = json.loads(
            json.dumps(DEFAULT_PROJECT)
        )

    if "last_saved_signature" not in st.session_state:
        st.session_state.last_saved_signature = None

    if "storage_loaded" not in st.session_state:
        st.session_state.storage_loaded = False

    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"


# ============================================================
# LOCAL STORAGE FUNCTIONS
# ============================================================

def project_signature(project):

    payload = json.dumps(
        project,
        sort_keys=True,
        default=str,
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def save_project():

    project = st.session_state.project

    signature = project_signature(project)

    if signature == st.session_state.last_saved_signature:
        return

    if LOCAL_STORAGE_AVAILABLE:

        try:

            storage.setItem(
                STORAGE_KEY,
                json.dumps(project),
            )

            st.session_state.last_saved_signature = signature

        except Exception:
            pass


def load_project():

    if st.session_state.storage_loaded:
        return

    st.session_state.storage_loaded = True

    if not LOCAL_STORAGE_AVAILABLE:
        return

    try:

        saved = storage.getItem(STORAGE_KEY)

        if saved:

            project = json.loads(saved)

            if isinstance(project, dict):

                st.session_state.project = project

                st.session_state.last_saved_signature = (
                    project_signature(project)
                )

    except Exception:
        pass


def reset_project():

    st.session_state.project = json.loads(
        json.dumps(DEFAULT_PROJECT)
    )

    st.session_state.last_saved_signature = None

    save_project()


# ============================================================
# INITIALIZE
# ============================================================

initialize_session_state()
load_project()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🏭 Reactor Scale-Up"
    )

    st.caption(
        "Process Engineering Dashboard"
    )

    st.divider()

    page_options = [
        "Dashboard",
        "Project Setup",
        "Reactor Configuration",
        "Agitation System",
        "Scale-Up Engine",
        "Solid-Liquid",
        "Gas-Liquid",
        "Heat Transfer",
        "3D Reactor",
        "Validation",
        "Libraries",
        "Excel Export",
    ]

    selected_page = st.radio(
        "Navigation",
        page_options,
        index=page_options.index(
            st.session_state.page
        ),
    )

    st.session_state.page = selected_page

    st.divider()

    st.markdown(
        "### 💾 Project Storage"
    )

    if LOCAL_STORAGE_AVAILABLE:

        st.success(
            "Browser auto-save enabled"
        )

    else:

        st.warning(
            "Browser storage package unavailable"
        )

    if st.button(
        "💾 Save Project Now",
        use_container_width=True,
    ):

        save_project()

        st.success(
            "Project saved."
        )

    if st.button(
        "♻️ Reset Project",
        use_container_width=True,
    ):

        reset_project()

        st.rerun()


# ============================================================
# PROJECT SHORTCUT
# ============================================================

project = st.session_state.project


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">'
    '🏭 Reactor Scale-Up & Mixing Dashboard'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'Professional process engineering tool for reactor geometry, '
    'mixing, agitation and scale-up studies'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_selected_scales():

    mode = project.get(
        "study_mode",
        "Lab vs Pilot vs Commercial",
    )

    return STUDY_MODES.get(
        mode,
        ["Lab", "Pilot", "Commercial"],
    )


def reactor_data(scale):

    return project["reactors"][scale]


def calculate_all_reactors():

    results = {}

    for scale in get_selected_scales():

        reactor = reactor_data(scale)

        try:

            results[scale] = calculate_reactor(
                reactor,
                project["reaction_type"],
            )

        except Exception as exc:

            results[scale] = {
                "error": str(exc)
            }

    return results


def fmt(value, digits=2):

    if value is None:
        return "—"

    try:

        if np.isnan(value):
            return "—"

    except Exception:
        pass

    return f"{value:,.{digits}f}"


# ============================================================
# PAGE: PROJECT SETUP
# ============================================================

if st.session_state.page == "Project Setup":

    st.markdown(
        '<div class="section-title">'
        '📋 Project Setup'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:

        project["project_name"] = st.text_input(
            "Project Name",
            value=project["project_name"],
        )

        project["project_number"] = st.text_input(
            "Project Number",
            value=project["project_number"],
        )

        project["company"] = st.text_input(
            "Company",
            value=project["company"],
        )

    with col2:

        project["prepared_by"] = st.text_input(
            "Prepared By",
            value=project["prepared_by"],
        )

        project["reaction_type"] = st.selectbox(
            "Reaction / Process Type",
            REACTION_TYPES,
            index=REACTION_TYPES.index(
                project["reaction_type"]
            ),
        )

        project["study_mode"] = st.selectbox(
            "Study / Comparison Mode",
            list(STUDY_MODES.keys()),
            index=list(STUDY_MODES.keys()).index(
                project["study_mode"]
            ),
        )

    st.info(
        "Only the reactor scales selected by the Study Mode "
        "will be displayed throughout the dashboard."
    )

    project["scale_up_criterion"] = st.selectbox(
        "Scale-Up Criterion",
        SCALE_UP_CRITERIA,
        index=SCALE_UP_CRITERIA.index(
            project["scale_up_criterion"]
        ),
    )

    project["selected_scales"] = get_selected_scales()

    st.markdown("### Selected Reactor Scales")

    st.dataframe(
        pd.DataFrame(
            {
                "Scale": project["selected_scales"]
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    save_project()


# ============================================================
# PAGE: REACTOR CONFIGURATION
# ============================================================

elif st.session_state.page == "Reactor Configuration":

    st.markdown(
        '<div class="section-title">'
        '📐 Reactor Configuration'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Liquid height is automatically calculated from working "
        "volume and reactor geometry. It is not a manual input."
    )

    for scale in get_selected_scales():

        reactor = reactor_data(scale)

        st.markdown(
            f"## {scale} Reactor"
        )

        with st.expander(
            f"📐 {scale} Geometry",
            expanded=True,
        ):

            col1, col2, col3 = st.columns(3)

            with col1:

                reactor["working_volume"] = st.number_input(
                    f"{scale} Working Volume (L)",
                    min_value=1.0,
                    value=float(
                        reactor["working_volume"]
                    ),
                    key=f"{scale}_working_volume",
                )

                reactor["tank_id"] = st.number_input(
                    f"{scale} Tank ID (mm)",
                    min_value=100.0,
                    value=float(
                        reactor["tank_id"]
                    ),
                    key=f"{scale}_tank_id",
                )

                reactor[
                    "straight_side_height"
                ] = st.number_input(
                    f"{scale} Straight Side Height (mm)",
                    min_value=100.0,
                    value=float(
                        reactor["straight_side_height"]
                    ),
                    key=f"{scale}_ssh",
                )

            with col2:

                reactor["bottom_type"] = st.selectbox(
                    f"{scale} Bottom Geometry",
                    list(
                        REACTOR_GEOMETRY_LIBRARY.keys()
                    ),
                    index=list(
                        REACTOR_GEOMETRY_LIBRARY.keys()
                    ).index(
                        reactor["bottom_type"]
                    ),
                    key=f"{scale}_bottom",
                )

                reactor["top_type"] = st.selectbox(
                    f"{scale} Top Geometry",
                    list(
                        REACTOR_GEOMETRY_LIBRARY.keys()
                    ),
                    index=list(
                        REACTOR_GEOMETRY_LIBRARY.keys()
                    ).index(
                        reactor["top_type"]
                    ),
                    key=f"{scale}_top",
                )

            with col3:

                calculated_height = calculate_liquid_height(
                    working_volume_l=reactor[
                        "working_volume"
                    ],
                    tank_id_mm=reactor[
                        "tank_id"
                    ],
                    straight_side_height_mm=reactor[
                        "straight_side_height"
                    ],
                    bottom_type=reactor[
                        "bottom_type"
                    ],
                    top_type=reactor[
                        "top_type"
                    ],
                )

                total_volume = calculate_total_volume(
                    tank_id_mm=reactor[
                        "tank_id"
                    ],
                    straight_side_height_mm=reactor[
                        "straight_side_height"
                    ],
                    bottom_type=reactor[
                        "bottom_type"
                    ],
                    top_type=reactor[
                        "top_type"
                    ],
                )

                st.metric(
                    "Calculated Liquid Height",
                    f"{fmt(calculated_height, 1)} mm",
                )

                st.metric(
                    "Approx. Vessel Volume",
                    f"{fmt(total_volume, 1)} L",
                )

                reactor[
                    "calculated_liquid_height"
                ] = calculated_height

        with st.expander(
            f"⚙️ Process Properties — {scale}"
        ):

            col1, col2, col3 = st.columns(3)

            with col1:

                reactor["density"] = st.number_input(
                    "Liquid Density (kg/m³)",
                    min_value=1.0,
                    value=float(
                        reactor["density"]
                    ),
                    key=f"{scale}_density",
                )

                reactor["viscosity"] = st.number_input(
                    "Viscosity (cP)",
                    min_value=0.01,
                    value=float(
                        reactor["viscosity"]
                    ),
                    key=f"{scale}_viscosity",
                )

            with col2:

                reactor[
                    "surface_tension"
                ] = st.number_input(
                    "Surface Tension (N/m)",
                    min_value=0.001,
                    value=float(
                        reactor[
                            "surface_tension"
                        ]
                    ),
                    key=f"{scale}_surface_tension",
                )

                reactor[
                    "solid_density"
                ] = st.number_input(
                    "Solid Density (kg/m³)",
                    min_value=1.0,
                    value=float(
                        reactor[
                            "solid_density"
                        ]
                    ),
                    key=f"{scale}_solid_density",
                )

            with col3:

                reactor[
                    "solid_concentration"
                ] = st.number_input(
                    "Solid Concentration (wt%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(
                        reactor[
                            "solid_concentration"
                        ]
                    ),
                    key=f"{scale}_solid_conc",
                )

                reactor[
                    "particle_size"
                ] = st.number_input(
                    "Particle Size (µm)",
                    min_value=0.1,
                    value=float(
                        reactor[
                            "particle_size"
                        ]
                    ),
                    key=f"{scale}_particle_size",
                )

        st.divider()

    save_project()


# ============================================================
# PAGE: AGITATION SYSTEM
# ============================================================

elif st.session_state.page == "Agitation System":

    st.markdown(
        '<div class="section-title">'
        '⚙️ Agitation System'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Select the agitator type for each reactor. "
        "The corresponding conceptual 3D geometry is generated automatically."
    )

    for scale in get_selected_scales():

        reactor = reactor_data(scale)

        st.markdown(
            f"## {scale} Agitator"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            agitator_names = list(
                AGITATOR_LIBRARY.keys()
            )

            reactor[
                "impeller_type"
            ] = st.selectbox(
                "Impeller / Agitator Type",
                agitator_names,
                index=agitator_names.index(
                    reactor["impeller_type"]
                ),
                key=f"{scale}_agitator",
            )

        with col2:

            reactor[
                "impeller_diameter"
            ] = st.number_input(
                "Impeller Diameter (mm)",
                min_value=10.0,
                value=float(
                    reactor[
                        "impeller_diameter"
                    ]
                ),
                key=f"{scale}_impeller_d",
            )

        with col3:

            reactor[
                "number_of_impellers"
            ] = st.number_input(
                "Number of Impellers",
                min_value=1,
                max_value=10,
                value=int(
                    reactor[
                        "number_of_impellers"
                    ]
                ),
                step=1,
                key=f"{scale}_number_impellers",
            )

        col1, col2, col3 = st.columns(3)

        with col1:

            reactor["rpm"] = st.number_input(
                "Agitator Speed (RPM)",
                min_value=0.1,
                value=float(
                    reactor["rpm"]
                ),
                key=f"{scale}_rpm",
            )

        with col2:

            reactor[
                "impeller_clearance"
            ] = st.number_input(
                "Bottom Clearance (mm)",
                min_value=0.0,
                value=float(
                    reactor[
                        "impeller_clearance"
                    ]
                ),
                key=f"{scale}_clearance",
            )

        with col3:

            reactor["baffles"] = st.number_input(
                "Number of Baffles",
                min_value=0,
                max_value=12,
                value=int(
                    reactor["baffles"]
                ),
                step=1,
                key=f"{scale}_baffles",
            )

        agitator = get_agitator(
            reactor["impeller_type"]
        )

        st.markdown(
            f"**Selected:** {reactor['impeller_type']}"
        )

        st.write(
            agitator.get(
                "description",
                "Agitator geometry from engineering library.",
            )
        )

        st.caption(
            "Np/Nq values are correlation/library dependent. "
            "RCI values should be entered from validated vendor/literature data "
            "when required."
        )

        if reactor[
            "impeller_type"
        ] == "Retreating Curve Impeller (RCI)":

            col1, col2 = st.columns(2)

            with col1:

                np_value = st.number_input(
                    "RCI Np Override",
                    min_value=0.0,
                    value=float(
                        reactor["np_override"]
                        or 0.0
                    ),
                    key=f"{scale}_rci_np",
                )

                reactor["np_override"] = (
                    np_value
                    if np_value > 0
                    else None
                )

            with col2:

                nq_value = st.number_input(
                    "RCI Nq Override",
                    min_value=0.0,
                    value=float(
                        reactor["nq_override"]
                        or 0.0
                    ),
                    key=f"{scale}_rci_nq",
                )

                reactor["nq_override"] = (
                    nq_value
                    if nq_value > 0
                    else None
                )

        st.divider()

    save_project()


# ============================================================
# PAGE: SCALE-UP ENGINE
# ============================================================

elif st.session_state.page == "Scale-Up Engine":

    st.markdown(
        '<div class="section-title">'
        '📈 Scale-Up Engine'
        '</div>',
        unsafe_allow_html=True,
    )

    project[
        "scale_up_criterion"
    ] = st.selectbox(
        "Scale-Up Basis",
        SCALE_UP_CRITERIA,
        index=SCALE_UP_CRITERIA.index(
            project[
                "scale_up_criterion"
            ]
        ),
    )

    selected = get_selected_scales()

    st.markdown(
        "### Selected Scale-Up Study"
    )

    st.write(
        " → ".join(selected)
    )

    results = calculate_all_reactors()

    rows = []

    for scale in selected:

        result = results.get(scale, {})

        if "error" in result:
            continue

        rows.append(
            {
                "Scale": scale,
                "Volume (L)": result.get(
                    "working_volume"
                ),
                "RPM": result.get(
                    "rpm"
                ),
                "Impeller (mm)": result.get(
                    "impeller_diameter"
                ),
                "Power (kW)": result.get(
                    "power_kw"
                ),
                "P/V (kW/m³)": result.get(
                    "power_per_volume"
                ),
                "Tip Speed (m/s)": result.get(
                    "tip_speed"
                ),
                "Pumping (m³/h)": result.get(
                    "pumping_capacity"
                ),
                "Re": result.get(
                    "reynolds_number"
                ),
                "Fr": result.get(
                    "froude_number"
                ),
            }
        )

    if rows:

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    save_project()


# ============================================================
# PAGE: DASHBOARD
# ============================================================

elif st.session_state.page == "Dashboard":

    results = calculate_all_reactors()

    selected = get_selected_scales()

    st.markdown(
        '<div class="section-title">'
        '📊 Engineering Dashboard'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        f"Study: {project['study_mode']} | "
        f"Reaction Type: {project['reaction_type']} | "
        f"Scale-Up Basis: {project['scale_up_criterion']}"
    )

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    for scale in selected:

        result = results.get(scale, {})

        if "error" in result:
            st.error(
                f"{scale}: {result['error']}"
            )
            continue

        st.markdown(
            f"### {scale}"
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:

            st.metric(
                "Working Volume",
                f"{fmt(result.get('working_volume'), 1)} L",
            )

        with c2:

            st.metric(
                "Liquid Height",
                f"{fmt(result.get('liquid_height'), 0)} mm",
            )

        with c3:

            st.metric(
                "Power",
                f"{fmt(result.get('power_kw'), 2)} kW",
            )

        with c4:

            st.metric(
                "P/V",
                f"{fmt(result.get('power_per_volume'), 2)} kW/m³",
            )

        with c5:

            st.metric(
                "Tip Speed",
                f"{fmt(result.get('tip_speed'), 2)} m/s",
            )

        st.divider()

    # --------------------------------------------------------
    # COMPARISON
    # --------------------------------------------------------

    if len(selected) > 1:

        st.markdown(
            "### 🔄 Scale Comparison"
        )

        try:

            comparison = compare_reactors(
                results,
                selected,
            )

            st.dataframe(
                pd.DataFrame(comparison),
                use_container_width=True,
                hide_index=True,
            )

        except Exception as exc:

            st.warning(
                f"Comparison unavailable: {exc}"
            )

    save_project()


# ============================================================
# PAGE: SOLID-LIQUID
# ============================================================

elif st.session_state.page == "Solid-Liquid":

    st.markdown(
        '<div class="section-title">'
        '🧱 Solid-Liquid Mixing'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Njs calculations are screening-level unless a validated "
        "suspension correlation and coefficient are supplied."
    )

    for scale in get_selected_scales():

        reactor = reactor_data(scale)

        result = calculate_reactor(
            reactor,
            "Solid-Liquid",
        )

        st.markdown(
            f"### {scale}"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Solid Concentration",
                f"{reactor['solid_concentration']:.2f} wt%",
            )

        with c2:

            njs = result.get(
                "njs_rpm"
            )

            st.metric(
                "Njs",
                (
                    f"{fmt(njs, 1)} RPM"
                    if njs is not None
                    else "Not Available"
                ),
            )

        with c3:

            if njs and reactor["rpm"] >= njs:

                st.success(
                    "Suspension Speed: PASS"
                )

            else:

                st.warning(
                    "Suspension Speed: CHECK"
                )


# ============================================================
# PAGE: GAS-LIQUID
# ============================================================

elif st.session_state.page == "Gas-Liquid":

    st.markdown(
        '<div class="section-title">'
        '💨 Gas-Liquid Mixing'
        '</div>',
        unsafe_allow_html=True,
    )

    for scale in get_selected_scales():

        reactor = reactor_data(scale)

        result = calculate_reactor(
            reactor,
            "Gas-Liquid",
        )

        st.markdown(
            f"### {scale}"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            reactor[
                "gas_flow"
            ] = st.number_input(
                "Gas Flow (m³/h)",
                min_value=0.0,
                value=float(
                    reactor[
                        "gas_flow"
                    ]
                ),
                key=f"{scale}_gas_flow",
            )

        with c2:

            st.metric(
                "KLa Screening",
                (
                    f"{fmt(result.get('kla'), 3)} 1/s"
                    if result.get("kla") is not None
                    else "—"
                ),
            )

        with c3:

            st.metric(
                "Gas Flow",
                f"{fmt(reactor['gas_flow'], 2)} m³/h",
            )

    save_project()


# ============================================================
# PAGE: HEAT TRANSFER
# ============================================================

elif st.session_state.page == "Heat Transfer":

    st.markdown(
        '<div class="section-title">'
        '🔥 Heat Transfer'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Heat-transfer calculations shown here are preliminary "
        "engineering estimates. Final exchanger/reactor jacket design "
        "requires validated U values and thermal duty."
    )

    for scale in get_selected_scales():

        reactor = reactor_data(scale)

        result = calculate_reactor(
            reactor,
            project["reaction_type"],
        )

        st.markdown(
            f"### {scale}"

        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Approx. Reactor Diameter",
                f"{fmt(reactor['tank_id'], 0)} mm",
            )

        with c2:

            st.metric(
                "Liquid Height",
                f"{fmt(result.get('liquid_height'), 0)} mm",
            )

        with c3:

            st.metric(
                "Estimated Heat Transfer Area",
                f"{fmt(result.get('heat_transfer_area'), 2)} m²",
            )


# ============================================================
# PAGE: 3D REACTOR
# ============================================================

elif st.session_state.page == "3D Reactor":

    st.markdown(
        '<div class="section-title">'
        '🧊 3D Reactor & Agitator Visualization'
        '</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "The 3D model is a conceptual engineering visualization "
        "generated from the entered reactor geometry and selected "
        "agitator type. It is not manufacturer CAD."
    )

    selected = get_selected_scales()

    scale = st.selectbox(
        "Select Reactor",
        selected,
    )

    reactor = reactor_data(scale)

    result = calculate_reactor(
        reactor,
        project["reaction_type"],
    )

    try:

        fig = create_reactor_3d(
            reactor,
            result,
            project["reaction_type"],
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    except Exception as exc:

        st.error(
            f"3D visualization error: {exc}"
        )


# ============================================================
# PAGE: VALIDATION
# ============================================================

elif st.session_state.page == "Validation":

    st.markdown(
        '<div class="section-title">'
        '✅ Engineering Validation'
        '</div>',
        unsafe_allow_html=True,
    )

    for scale in get_selected_scales():

        reactor = reactor_data(scale)

        result = calculate_reactor(
            reactor,
            project["reaction_type"],
        )

        checks = validation_checks(
            reactor,
            result,
            project["reaction_type"],
        )

        st.markdown(
            f"### {scale}"
        )

        if not checks:

            st.info(
                "No validation checks available."
            )

            continue

        validation_df = pd.DataFrame(
            checks
        )

        st.dataframe(
            validation_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# PAGE: LIBRARIES
# ============================================================

elif st.session_state.page == "Libraries":

    st.markdown(
        '<div class="section-title">'
        '📚 Engineering Libraries'
        '</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(
        [
            "Agitator Library",
            "Reactor Geometry Library",
        ]
    )

    with tab1:

        rows = []

        for name, data in AGITATOR_LIBRARY.items():

            rows.append(
                {
                    "Agitator": name,
                    "Description": data.get(
                        "description",
                        "",
                    ),
                    "Np": data.get(
                        "Np"
                    ),
                    "Nq": data.get(
                        "Nq"
                    ),
                    "Application": data.get(
                        "application",
                        "",
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    with tab2:

        rows = []

        for name, data in (
            REACTOR_GEOMETRY_LIBRARY.items()
        ):

            rows.append(
                {
                    "Geometry": name,
                    "Type": data.get(
                        "type",
                        "",
                    ),
                    "Description": data.get(
                        "description",
                        "",
                    ),
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# PAGE: EXCEL EXPORT
# ============================================================

elif st.session_state.page == "Excel Export":

    st.markdown(
        '<div class="section-title">'
        '📥 Excel Export'
        '</div>',
        unsafe_allow_html=True,
    )

    st.write(
        "Generate a professional workbook containing project "
        "inputs, reactor geometry, agitation data, calculated results, "
        "comparison results and engineering libraries."
    )

    if st.button(
        "📊 Generate Excel Workbook",
        type="primary",
        use_container_width=True,
    ):

        from calculations.engine import create_excel_workbook

        try:

            results = calculate_all_reactors()

            excel_file = create_excel_workbook(
                project,
                results,
            )

            st.download_button(
                label="⬇️ Download Excel File",
                data=excel_file,
                file_name=(
                    f"{project['project_name']}"
                    "_Reactor_ScaleUp.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        except Exception as exc:

            st.error(
                f"Excel generation failed: {exc}"
            )


# ============================================================
# AUTO SAVE
# ============================================================

save_project()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Reactor Scale-Up Dashboard | "
    "Process Engineering Tool | "
    "Screening calculations require engineering validation before "
    "final equipment/design decisions."
)
