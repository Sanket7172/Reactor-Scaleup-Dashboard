import streamlit as st
import math
import io
import json
from copy import deepcopy

import pandas as pd
import numpy as np
import plotly.graph_objects as go

from streamlit_local_storage import LocalStorage


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Reactor Scale-Up & Mixing Engineering Dashboard",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROFESSIONAL CSS
# ============================================================

st.markdown(
    """
<style>

.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 1700px;
}

h1 {
    font-size: 2.2rem !important;
    font-weight: 750 !important;
}

h2 {
    font-weight: 700 !important;
}

h3 {
    font-weight: 650 !important;
}

[data-testid="stMetric"] {
    background: white;
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

.info-card {
    background: #F5F7FA;
    border-radius: 12px;
    padding: 15px;
    border: 1px solid #E0E5EB;
    margin-bottom: 10px;
}

.pass-card {
    background: #E8F5E9;
    border-left: 5px solid #2E7D32;
    padding: 10px;
    border-radius: 6px;
}

.warning-card {
    background: #FFF8E1;
    border-left: 5px solid #F9A825;
    padding: 10px;
    border-radius: 6px;
}

.fail-card {
    background: #FFEBEE;
    border-left: 5px solid #C62828;
    padding: 10px;
    border-radius: 6px;
}

.auto-card {
    background: #E3F2FD;
    border-left: 5px solid #1565C0;
    padding: 10px;
    border-radius: 6px;
}

.library-card {
    background: #F3E5F5;
    border-left: 5px solid #7B1FA2;
    padding: 10px;
    border-radius: 6px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# LOCAL STORAGE
# ============================================================

local_storage = LocalStorage()


STORAGE_KEY = "reactor_scaleup_engineering_project"


# ============================================================
# CONSTANTS
# ============================================================

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


STUDY_MODES = [
    "Single Reactor",
    "Lab vs Pilot",
    "Pilot vs Commercial",
    "Lab vs Commercial",
    "Lab vs Pilot vs Commercial",
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


BOTTOM_TYPES = [
    "Flat Bottom",
    "2:1 Ellipsoidal",
    "10% Torispherical",
    "6% Torispherical",
    "Hemispherical",
    "Conical",
]


TOP_TYPES = [
    "Flat Top",
    "2:1 Ellipsoidal",
    "10% Torispherical",
    "6% Torispherical",
    "Hemispherical",
]


# ============================================================
# REACTOR GEOMETRY LIBRARY
# ============================================================

REACTOR_GEOMETRY = {

    "Flat Bottom": {
        "type": "Flat",
        "dish_ratio": 0.0,
        "notes": "Flat vessel bottom",
    },

    "2:1 Ellipsoidal": {
        "type": "Ellipsoidal",
        "dish_ratio": 0.25,
        "notes": "Approximate 2:1 ellipsoidal head",
    },

    "10% Torispherical": {
        "type": "Torispherical",
        "dish_ratio": 0.10,
        "notes": "Approximate 10% dish-depth process geometry",
    },

    "6% Torispherical": {
        "type": "Torispherical",
        "dish_ratio": 0.06,
        "notes": "Approximate 6% dish-depth process geometry",
    },

    "Hemispherical": {
        "type": "Hemispherical",
        "dish_ratio": 0.50,
        "notes": "Hemispherical head",
    },

    "Conical": {
        "type": "Conical",
        "dish_ratio": 0.25,
        "notes": "Approximate conical bottom",
    },

    "Flat Top": {
        "type": "Flat",
        "dish_ratio": 0.0,
        "notes": "Flat top",
    },
}


# ============================================================
# AGITATOR LIBRARY
# ============================================================

AGITATORS = {

    "Rushton Turbine": {
        "category": "Radial",
        "flow": "Radial",
        "Np": 5.0,
        "Nq": 0.75,
        "blades": 6,
        "blade_angle": 90,
        "geometry": "rushton",
        "application": "Gas dispersion / high shear",
        "recommended": "Gas-liquid, dispersion",
        "notes": "Disc turbine with flat radial blades",
    },

    "Flat Blade Turbine": {
        "category": "Radial",
        "flow": "Radial",
        "Np": 5.0,
        "Nq": 0.75,
        "blades": 6,
        "blade_angle": 90,
        "geometry": "flat_turbine",
        "application": "Radial mixing",
        "recommended": "Gas dispersion / liquid mixing",
        "notes": "Flat blade turbine",
    },

    "Pitched Blade Turbine 45° Down": {
        "category": "Axial",
        "flow": "Axial Down",
        "Np": 1.5,
        "Nq": 0.75,
        "blades": 4,
        "blade_angle": 45,
        "geometry": "pbt",
        "application": "General mixing / suspension",
        "recommended": "Solid-liquid and general mixing",
        "notes": "45 degree pitched blade turbine",
    },

    "Pitched Blade Turbine 45° Up": {
        "category": "Axial",
        "flow": "Axial Up",
        "Np": 1.5,
        "Nq": 0.75,
        "blades": 4,
        "blade_angle": 45,
        "geometry": "pbt",
        "application": "Top-to-bottom circulation",
        "recommended": "General blending",
        "notes": "Up-pumping pitched blade",
    },

    "Hydrofoil": {
        "category": "Axial",
        "flow": "Axial",
        "Np": 0.50,
        "Nq": 0.70,
        "blades": 3,
        "blade_angle": 30,
        "geometry": "hydrofoil",
        "application": "High circulation / low power",
        "recommended": "Bulk liquid mixing",
        "notes": "Hydrofoil representation",
    },

    "HE-3": {
        "category": "Axial",
        "flow": "Axial",
        "Np": 0.30,
        "Nq": 0.75,
        "blades": 3,
        "blade_angle": 25,
        "geometry": "hydrofoil",
        "application": "Efficient axial mixing",
        "recommended": "Low-to-medium viscosity",
        "notes": "Use validated vendor coefficient for final design",
    },

    "A310": {
        "category": "Axial",
        "flow": "Axial",
        "Np": 0.35,
        "Nq": 0.70,
        "blades": 3,
        "blade_angle": 25,
        "geometry": "hydrofoil",
        "application": "Efficient axial mixing",
        "recommended": "General process mixing",
        "notes": "Use validated vendor coefficient for final design",
    },

    "A320": {
        "category": "Axial",
        "flow": "Axial",
        "Np": 0.40,
        "Nq": 0.68,
        "blades": 3,
        "blade_angle": 25,
        "geometry": "hydrofoil",
        "application": "Axial circulation",
        "recommended": "General process mixing",
        "notes": "Use validated vendor coefficient for final design",
    },

    "Marine Propeller": {
        "category": "Axial",
        "flow": "Axial",
        "Np": 0.40,
        "Nq": 0.60,
        "blades": 3,
        "blade_angle": 30,
        "geometry": "marine",
        "application": "Low viscosity blending",
        "recommended": "Low viscosity systems",
        "notes": "Marine propeller representation",
    },

    "Paddle": {
        "category": "Radial",
        "flow": "Radial",
        "Np": 1.2,
        "Nq": 0.50,
        "blades": 2,
        "blade_angle": 90,
        "geometry": "paddle",
        "application": "Simple liquid mixing",
        "recommended": "Low-to-medium viscosity",
        "notes": "Paddle representation",
    },

    "Anchor": {
        "category": "High Viscosity",
        "flow": "Tangential",
        "Np": 1.0,
        "Nq": 0.30,
        "blades": 2,
        "blade_angle": 90,
        "geometry": "anchor",
        "application": "High viscosity",
        "recommended": "Viscous fluids",
        "notes": "Anchor-type impeller",
    },

    "Gate": {
        "category": "High Viscosity",
        "flow": "Tangential",
        "Np": 1.0,
        "Nq": 0.25,
        "blades": 2,
        "blade_angle": 90,
        "geometry": "gate",
        "application": "High viscosity",
        "recommended": "Viscous fluids",
        "notes": "Gate-type agitator",
    },

    "Retreat Curve Impeller (RCI)": {
        "category": "High Viscosity / Mixed",
        "flow": "Mixed",
        "Np": None,
        "Nq": None,
        "blades": 2,
        "blade_angle": None,
        "geometry": "rci",
        "application": "High viscosity / process mixing",
        "recommended": "Viscous and shear-sensitive systems",
        "notes": (
            "RCI power and pumping coefficients should be "
            "entered from vendor/pilot data for final design."
        ),
    },

    "Helical Ribbon": {
        "category": "Very High Viscosity",
        "flow": "Helical",
        "Np": None,
        "Nq": None,
        "blades": 1,
        "blade_angle": None,
        "geometry": "helical",
        "application": "Very high viscosity",
        "recommended": "Highly viscous products",
        "notes": "Requires validated vendor correlation",
    },
}


# ============================================================
# DEFAULT PROJECT
# ============================================================

DEFAULT_PROJECT = {

    "project_name": "New Reactor Scale-Up Study",

    "product": "",

    "engineer": "",

    "revision": "Rev-00",

    "reaction": "Liquid-Liquid",

    "study_mode": "Single Reactor",

    "scale_up_criterion": "Constant P/V",

    "active_reactor": "Commercial",

    "reactors": {

        "Lab": {},

        "Pilot": {},

        "Commercial": {},
    },

    "global_agitator": {

        "type": "Pitched Blade Turbine 45° Down",

        "n_impellers": 1,

        "Np_override": None,

        "Nq_override": None,
    },

    "saved": True,
}


# ============================================================
# DEFAULT REACTOR
# ============================================================

def default_reactor(scale):

    if scale == "Lab":

        return {

            "working_volume_l": 2.0,

            "tank_id_m": 0.12,

            "straight_side_m": 0.18,

            "total_height_m": 0.25,

            "max_volume_l": 3.0,

            "min_volume_l": 0.5,

            "bottom": "Flat Bottom",

            "top": "Flat Top",

            "rpm": 500.0,

            "rho": 1000.0,

            "viscosity_cp": 1.0,

            "surface_tension_mn_m": 72.0,

            "impeller_d_m": 0.06,

            "n_impellers": 1,

            "clearance_m": 0.03,

            "baffles": 4,

            "baffle_width_m": 0.012,

            "baffle_clearance_m": 0.005,

            "impeller_elevations_m": [0.06],

            "gas_flow_nm3h": 0.0,

            "solid_density": 2500.0,

            "particle_size_um": 100.0,

            "solids_wt_percent": 0.0,

            "suspension_factor": 1.30,

            "bubble_diameter_mm": 2.4,

            "motor_efficiency": 0.90,

            "service_factor": 1.15,

            "tip_speed_limit": 10.0,

        }

    if scale == "Pilot":

        return {

            "working_volume_l": 500.0,

            "tank_id_m": 0.80,

            "straight_side_m": 0.90,

            "total_height_m": 1.30,

            "max_volume_l": 650.0,

            "min_volume_l": 100.0,

            "bottom": "2:1 Ellipsoidal",

            "top": "2:1 Ellipsoidal",

            "rpm": 250.0,

            "rho": 1000.0,

            "viscosity_cp": 1.0,

            "surface_tension_mn_m": 72.0,

            "impeller_d_m": 0.30,

            "n_impellers": 2,

            "clearance_m": 0.15,

            "baffles": 4,

            "baffle_width_m": 0.08,

            "baffle_clearance_m": 0.025,

            "impeller_elevations_m": [0.30, 0.65],

            "gas_flow_nm3h": 0.0,

            "solid_density": 2500.0,

            "particle_size_um": 100.0,

            "solids_wt_percent": 0.0,

            "suspension_factor": 1.30,

            "bubble_diameter_mm": 2.4,

            "motor_efficiency": 0.90,

            "service_factor": 1.15,

            "tip_speed_limit": 10.0,

        }

    return {

        "working_volume_l": 5000.0,

        "tank_id_m": 1.80,

        "straight_side_m": 2.20,

        "total_height_m": 3.10,

        "max_volume_l": 6500.0,

        "min_volume_l": 1000.0,

        "bottom": "10% Torispherical",

        "top": "10% Torispherical",

        "rpm": 110.0,

        "rho": 1000.0,

        "viscosity_cp": 1.0,

        "surface_tension_mn_m": 72.0,

        "impeller_d_m": 0.85,

        "n_impellers": 3,

        "clearance_m": 0.25,

        "baffles": 4,

        "baffle_width_m": 0.18,

        "baffle_clearance_m": 0.05,

        "impeller_elevations_m": [0.40, 1.05, 1.70],

        "gas_flow_nm3h": 0.0,

        "solid_density": 2500.0,

        "particle_size_um": 100.0,

        "solids_wt_percent": 0.0,

        "suspension_factor": 1.30,

        "bubble_diameter_mm": 2.4,

        "motor_efficiency": 0.90,

        "service_factor": 1.15,

        "tip_speed_limit": 10.0,

    }


# ============================================================
# LOAD PROJECT FROM BROWSER
# ============================================================

def load_project():

    try:

        saved = local_storage.getItem(STORAGE_KEY)

        if saved:

            if isinstance(saved, str):

                saved = json.loads(saved)

            project = deepcopy(DEFAULT_PROJECT)

            project.update(saved)

            for scale in ["Lab", "Pilot", "Commercial"]:

                if not project["reactors"].get(scale):

                    project["reactors"][scale] = default_reactor(scale)

            return project

    except Exception:

        pass

    project = deepcopy(DEFAULT_PROJECT)

    for scale in ["Lab", "Pilot", "Commercial"]:

        project["reactors"][scale] = default_reactor(scale)

    return project


# ============================================================
# SESSION INITIALIZATION
# ============================================================

if "project" not in st.session_state:

    st.session_state.project = load_project()


# ============================================================
# AUTOMATIC SAVE
# ============================================================

def save_project():

    try:

        data = deepcopy(st.session_state.project)

        local_storage.setItem(
            STORAGE_KEY,
            json.dumps(data)
        )

        st.session_state.project["saved"] = True

    except Exception:

        st.session_state.project["saved"] = False


# ============================================================
# UTILITY
# ============================================================

def safe_float(value, default=0.0):

    try:

        return float(value)

    except Exception:

        return default


def clamp(value, minimum, maximum):

    return max(minimum, min(value, maximum))


# ============================================================
# HEAD GEOMETRY
# ============================================================

def head_depth(diameter, geometry):

    if geometry not in REACTOR_GEOMETRY:

        return 0.0

    ratio = REACTOR_GEOMETRY[geometry]["dish_ratio"]

    return diameter * ratio


def approximate_head_volume(diameter, geometry):

    """

    Engineering visualization/process-volume approximation.

    Exact fabricated head volume must be obtained from
    vessel fabrication geometry/drawing.
    """

    D = diameter

    R = D / 2.0

    if geometry == "Flat Bottom" or geometry == "Flat Top":

        return 0.0

    if geometry == "Hemispherical":

        return (2.0 / 3.0) * math.pi * R**3

    if geometry == "2:1 Ellipsoidal":

        return (2.0 / 3.0) * math.pi * R**2 * (D / 4.0)

    if geometry == "10% Torispherical":

        depth = 0.10 * D

        return math.pi * R**2 * depth * 0.80

    if geometry == "6% Torispherical":

        depth = 0.06 * D

        return math.pi * R**2 * depth * 0.80

    if geometry == "Conical":

        height = 0.25 * D

        return math.pi * R**2 * height / 3.0

    return 0.0


# ============================================================
# LIQUID HEIGHT FROM VOLUME
# ============================================================

def cylindrical_area(diameter):

    return math.pi * diameter**2 / 4.0


def volume_at_height(
    diameter,
    height,
    bottom,
    top=None
):

    """

    Approximate vessel volume below a liquid elevation.

    Bottom geometry is included.

    Top geometry is only relevant when liquid reaches the top head.
    """

    D = diameter

    straight_area = cylindrical_area(D)

    bottom_depth = head_depth(D, bottom)

    bottom_volume = approximate_head_volume(
        D,
        bottom
    )

    if height <= 0:

        return 0.0

    if height <= bottom_depth and bottom_depth > 0:

        fraction = height / bottom_depth

        return bottom_volume * fraction**2

    cylindrical_height = height - bottom_depth

    volume = (
        bottom_volume
        + straight_area * cylindrical_height
    )

    return max(volume, 0.0)


def liquid_height_from_volume(
    volume_m3,
    diameter,
    bottom,
    top,
    straight_side_height,
    total_height
):

    """

    Calculates approximate liquid height from working volume.

    Internal engineering geometry model.

    For final vessel design, verify against fabricator's
    exact head geometry.
    """

    if volume_m3 <= 0 or diameter <= 0:

        return 0.0

    bottom_depth = head_depth(
        diameter,
        bottom
    )

    bottom_volume = approximate_head_volume(
        diameter,
        bottom
    )

    area = cylindrical_area(
        diameter
    )

    if volume_m3 <= bottom_volume and bottom_depth > 0:

        fraction = (
            volume_m3
            / bottom_volume
        )

        return bottom_depth * math.sqrt(
            clamp(fraction, 0.0, 1.0)
        )

    remaining = volume_m3 - bottom_volume

    cylindrical_height = (
        remaining / area
    )

    height = (
        bottom_depth
        + cylindrical_height
    )

    return clamp(
        height,
        0.0,
        max(total_height, height)
    )


# ============================================================
# AGITATOR COEFFICIENTS
# ============================================================

def get_agitator_coefficients(
    agitator_name,
    np_override=None,
    nq_override=None
):

    data = AGITATORS[agitator_name]

    np_value = (
        np_override
        if np_override is not None
        else data["Np"]
    )

    nq_value = (
        nq_override
        if nq_override is not None
        else data["Nq"]
    )

    return np_value, nq_value


# ============================================================
# AGITATION CALCULATION
# ============================================================

def calculate_impeller(
    volume_m3,
    rho,
    viscosity_cp,
    rpm,
    impeller_d,
    np_value,
    nq_value,
):

    if (
        volume_m3 <= 0
        or rho <= 0
        or viscosity_cp <= 0
        or rpm <= 0
        or impeller_d <= 0
    ):

        return {}

    N = rpm / 60.0

    viscosity_pa_s = viscosity_cp / 1000.0

    if np_value is None:

        return {
            "valid": False,
            "reason": (
                "Power coefficient Np is not defined. "
                "Enter validated vendor/pilot Np."
            )
        }

    if nq_value is None:

        return {
            "valid": False,
            "reason": (
                "Pumping coefficient Nq is not defined. "
                "Enter validated vendor/pilot Nq."
            )
        }

    power_w = (
        np_value
        * rho
        * N**3
        * impeller_d**5
    )

    pumping_m3_s = (
        nq_value
        * N
        * impeller_d**3
    )

    reynolds = (
        rho
        * N
        * impeller_d**2
        / viscosity_pa_s
    )

    tip_speed = (
        math.pi
        * impeller_d
        * N
    )

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

        "valid": True,

        "Power W":
            power_w,

        "Power kW":
            power_w / 1000.0,

        "Pumping m3/h":
            pumping_m3_s * 3600.0,

        "Tip Speed m/s":
            tip_speed,

        "Re":
            reynolds,

        "Fr":
            froude,

        "Torque Nm":
            torque,
    }


# ============================================================
# FULL REACTOR CALCULATION
# ============================================================

def calculate_reactor(
    reactor,
    agitator_name,
    np_override=None,
    nq_override=None,
):

    r = deepcopy(reactor)

    volume_m3 = (
        safe_float(
            r.get("working_volume_l")
        )
        / 1000.0
    )

    rho = safe_float(
        r.get("rho")
    )

    viscosity = safe_float(
        r.get("viscosity_cp")
    )

    rpm = safe_float(
        r.get("rpm")
    )

    tank_d = safe_float(
        r.get("tank_id_m")
    )

    impeller_d = safe_float(
        r.get("impeller_d_m")
    )

    n_impellers = int(
        r.get("n_impellers", 1)
    )

    bottom = r.get(
        "bottom",
        "Flat Bottom"
    )

    top = r.get(
        "top",
        "Flat Top"
    )

    liquid_height = liquid_height_from_volume(
        volume_m3,
        tank_d,
        bottom,
        top,
        safe_float(
            r.get("straight_side_m")
        ),
        safe_float(
            r.get("total_height_m")
        ),
    )

    np_value, nq_value = get_agitator_coefficients(
        agitator_name,
        np_override,
        nq_override
    )

    elevations = r.get(
        "impeller_elevations_m",
        []
    )

    if len(elevations) < n_impellers:

        elevations = list(elevations)

        while len(elevations) < n_impellers:

            if n_impellers == 1:

                elevation = (
                    liquid_height * 0.35
                )

            else:

                elevation = (
                    liquid_height
                    * (
                        0.20
                        + 0.60
                        * len(elevations)
                        / max(
                            n_impellers - 1,
                            1
                        )
                    )
                )

            elevations.append(
                elevation
            )

    elevations = elevations[
        :n_impellers
    ]

    total_power = 0.0

    total_pumping = 0.0

    impeller_results = []

    for i in range(n_impellers):

        result = calculate_impeller(

            volume_m3,

            rho,

            viscosity,

            rpm,

            impeller_d,

            np_value,

            nq_value,
        )

        elevation = elevations[i]

        if result.get("valid"):

            total_power += result[
                "Power W"
            ]

            total_pumping += result[
                "Pumping m3/h"
            ]

        result["Impeller"] = i + 1

        result["Elevation m"] = elevation

        impeller_results.append(
            result
        )

    power_kw = (
        total_power / 1000.0
    )

    pv_kw_m3 = (
        power_kw / volume_m3
        if volume_m3 > 0
        else 0.0
    )

    q_v_h = (
        total_pumping / volume_m3
        if volume_m3 > 0
        else 0.0
    )

    turnover_h = (
        volume_m3 / total_pumping
        if total_pumping > 0
        else 0.0
    )

    turnover_min = (
        turnover_h * 60.0
    )

    reynolds = (
        rho
        * rpm / 60.0
        * impeller_d**2
        / (viscosity / 1000.0)
        if viscosity > 0
        else 0.0
    )

    tip_speed = (
        math.pi
        * impeller_d
        * rpm / 60.0
    )

    froude = (
        (rpm / 60.0)**2
        * impeller_d
        / 9.81
    )

    # --------------------------------------------------------
    # NJS SCREENING
    # --------------------------------------------------------

    njs = None

    if (
        safe_float(
            r.get("solids_wt_percent")
        ) > 0
        and safe_float(
            r.get("solid_density")
        ) > 0
    ):

        rho_s = safe_float(
            r.get("solid_density")
        )

        particle_d = (
            safe_float(
                r.get("particle_size_um")
            )
            / 1e6
        )

        solids_fraction = (
            safe_float(
                r.get("solids_wt_percent")
            )
            / 100.0
        )

        S = safe_float(
            r.get(
                "suspension_factor",
                1.30
            )
        )

        density_term = max(
            (rho_s - rho)
            / rho,
            0.001
        )

        particle_term = (
            particle_d
            / max(impeller_d, 1e-9)
        )

        njs_hz = (
            S
            * density_term**0.45
            * max(
                particle_term,
                1e-9
            )**0.13
            * max(
                solids_fraction,
                0.001
            )**0.08
        )

        njs = njs_hz * 60.0

    n_over_njs = None

    if njs and njs > 0:

        n_over_njs = (
            rpm / njs
        )

    # --------------------------------------------------------
    # MOTOR
    # --------------------------------------------------------

    efficiency = safe_float(
        r.get(
            "motor_efficiency",
            0.90
        )
    )

    service_factor = safe_float(
        r.get(
            "service_factor",
            1.15
        )
    )

    shaft_kw = power_kw

    design_kw = (
        shaft_kw
        / max(efficiency, 0.01)
        * service_factor
    )

    standard_motor = standard_motor_size(
        design_kw
    )

    return {

        "volume_m3":
            volume_m3,

        "liquid_height_m":
            liquid_height,

        "power_kw":
            power_kw,

        "pv_kw_m3":
            pv_kw_m3,

        "pv_w_m3":
            pv_kw_m3 * 1000.0,

        "pumping_m3_h":
            total_pumping,

        "q_v_h":
            q_v_h,

        "turnover_min":
            turnover_min,

        "tip_speed_m_s":
            tip_speed,

        "re":
            reynolds,

        "fr":
            froude,

        "njs_rpm":
            njs,

        "n_over_njs":
            n_over_njs,

        "shaft_power_kw":
            shaft_kw,

        "design_motor_kw":
            design_kw,

        "recommended_motor_kw":
            standard_motor,

        "torque_nm":
            (
                total_power
                / (
                    2
                    * math.pi
                    * max(
                        rpm / 60.0,
                        1e-9
                    )
                )
            ),

        "impeller_results":
            impeller_results,

        "np":
            np_value,

        "nq":
            nq_value,

        "tank_d_m":
            tank_d,

        "impeller_d_m":
            impeller_d,

        "rpm":
            rpm,

        "n_impellers":
            n_impellers,

        "bottom":
            bottom,

        "top":
            top,

        "baffles":
            r.get("baffles", 0),

        "baffle_width_m":
            r.get(
                "baffle_width_m",
                0
            ),
    }


# ============================================================
# MOTOR STANDARD SIZE
# ============================================================

def standard_motor_size(design_kw):

    sizes = [
        0.37,
        0.55,
        0.75,
        1.1,
        1.5,
        2.2,
        3.0,
        4.0,
        5.5,
        7.5,
        11,
        15,
        18.5,
        22,
        30,
        37,
        45,
        55,
        75,
        90,
        110,
        132,
        160,
        200,
        250,
    ]

    for size in sizes:

        if design_kw <= size:

            return size

    return sizes[-1]


# ============================================================
# SCALE-UP CALCULATION
# ============================================================

def scale_up_rpm(
    criterion,
    source,
    target,
):

    N1 = (
        safe_float(
            source.get("rpm")
        )
        / 60.0
    )

    D1 = safe_float(
        source.get("impeller_d_m")
    )

    D2 = safe_float(
        target.get("impeller_d_m")
    )

    if N1 <= 0 or D1 <= 0 or D2 <= 0:

        return 0.0

    if criterion == "Constant Tip Speed":

        N2 = (
            N1
            * D1
            / D2
        )

    elif criterion == "Constant P/V":

        N2 = (
            N1
            * (
                D1 / D2
            ) ** (5.0 / 3.0)
        )

    elif criterion == "Constant RPM":

        N2 = N1

    elif criterion == "Constant Froude Number":

        N2 = (
            N1
            * math.sqrt(
                D1 / D2
            )
        )

    elif criterion == "Constant Reynolds Number":

        N2 = (
            N1
            * (
                D1 / D2
            ) ** 2
        )

    elif criterion == "Constant Pumping / Volume":

        V1 = safe_float(
            source.get(
                "working_volume_l"
            )
        )

        V2 = safe_float(
            target.get(
                "working_volume_l"
            )
        )

        if V1 <= 0 or V2 <= 0:

            return 0.0

        N2 = (
            N1
            * (
                V1 / V2
            )
            * (
                D2 / D1
            ) ** 3
        )

    else:

        N2 = N1

    return N2 * 60.0


# ============================================================
# 3D GEOMETRY HELPERS
# ============================================================

def add_cylinder(
    fig,
    radius,
    z_bottom,
    z_top,
    name,
    opacity=0.18,
):

    theta = np.linspace(
        0,
        2 * np.pi,
        80
    )

    z = np.linspace(
        z_bottom,
        z_top,
        30
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z
    )

    x = radius * np.cos(
        theta_grid
    )

    y = radius * np.sin(
        theta_grid
    )

    fig.add_surface(
        x=x,
        y=y,
        z=z_grid,
        opacity=opacity,
        showscale=False,
        name=name,
    )


def add_head(
    fig,
    diameter,
    base_z,
    geometry,
    direction,
    opacity=0.18,
):

    R = diameter / 2.0

    depth = head_depth(
        diameter,
        geometry
    )

    if depth <= 0:

        return

    theta = np.linspace(
        0,
        2 * np.pi,
        80
    )

    if geometry == "Hemispherical":

        phi = np.linspace(
            0,
            np.pi / 2,
            30
        )

        rr = R * np.sin(phi)

        if direction == "bottom":

            z = base_z + R * (
                1 - np.cos(phi)
            )

        else:

            z = base_z + R * np.cos(phi)

        rr_grid, theta_grid = np.meshgrid(
            rr,
            theta
        )

        z_grid = np.tile(
            z,
            (len(theta), 1)
        )

        x = (
            rr_grid
            * np.cos(theta_grid)
        )

        y = (
            rr_grid
            * np.sin(theta_grid)
        )

        fig.add_surface(
            x=x,
            y=y,
            z=z_grid,
            opacity=opacity,
            showscale=False,
            name=geometry,
        )

        return

    # Generic dome / cone representation

    z_fraction = np.linspace(
        0,
        1,
        30
    )

    radius_fraction = np.sqrt(
        np.maximum(
            1 - z_fraction**2,
            0
        )
    )

    rr = R * radius_fraction

    if direction == "bottom":

        z = (
            base_z
            + depth * z_fraction
        )

    else:

        z = (
            base_z
            - depth * z_fraction
        )

    rr_grid, theta_grid = np.meshgrid(
        rr,
        theta
    )

    z_grid = np.tile(
        z,
        (len(theta), 1)
    )

    x = (
        rr_grid
        * np.cos(theta_grid)
    )

    y = (
        rr_grid
        * np.sin(theta_grid)
    )

    fig.add_surface(
        x=x,
        y=y,
        z=z_grid,
        opacity=opacity,
        showscale=False,
        name=geometry,
    )


# ============================================================
# ADD SHAFT
# ============================================================

def add_shaft(
    fig,
    shaft_radius,
    z_bottom,
    z_top,
):

    theta = np.linspace(
        0,
        2 * np.pi,
        30
    )

    z = np.linspace(
        z_bottom,
        z_top,
        20
    )

    theta_grid, z_grid = np.meshgrid(
        theta,
        z
    )

    x = (
        shaft_radius
        * np.cos(theta_grid)
    )

    y = (
        shaft_radius
        * np.sin(theta_grid)
    )

    fig.add_surface(
        x=x,
        y=y,
        z=z_grid,
        opacity=0.9,
        showscale=False,
        name="Shaft",
    )


# ============================================================
# IMPeller 3D GEOMETRY
# ============================================================

def add_impeller_geometry(
    fig,
    impeller_type,
    diameter,
    elevation,
):

    data = AGITATORS[
        impeller_type
    ]

    geometry = data[
        "geometry"
    ]

    R = diameter / 2.0

    # --------------------------------------------------------
    # RUSHTON
    # --------------------------------------------------------

    if geometry == "rushton":

        theta = np.linspace(
            0,
            2 * np.pi,
            100
        )

        x = (
            R
            * np.cos(theta)
        )

        y = (
            R
            * np.sin(theta)
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=np.ones_like(x)
                * elevation,
                mode="lines",
                line=dict(
                    width=7
                ),
                name=impeller_type,
            )
        )

        for angle in np.linspace(
            0,
            2 * np.pi,
            data["blades"],
            endpoint=False,
        ):

            x1 = (
                0.15
                * R
                * math.cos(angle)
            )

            y1 = (
                0.15
                * R
                * math.sin(angle)
            )

            x2 = (
                R
                * math.cos(angle)
            )

            y2 = (
                R
                * math.sin(angle)
            )

            fig.add_trace(
                go.Scatter3d(
                    x=[x1, x2],
                    y=[y1, y2],
                    z=[
                        elevation,
                        elevation,
                    ],
                    mode="lines",
                    line=dict(
                        width=10
                    ),
                    showlegend=False,
                )
            )

        return

    # --------------------------------------------------------
    # PBT
    # --------------------------------------------------------

    if geometry == "pbt":

        hub = 0.10 * diameter

        theta = np.linspace(
            0,
            2 * np.pi,
            60
        )

        fig.add_trace(
            go.Scatter3d(
                x=(
                    0.5
                    * hub
                    * np.cos(theta)
                ),
                y=(
                    0.5
                    * hub
                    * np.sin(theta)
                ),
                z=np.ones_like(theta)
                * elevation,
                mode="lines",
                line=dict(
                    width=10
                ),
                name=impeller_type,
            )
        )

        for angle in np.linspace(
            0,
            2 * np.pi,
            data["blades"],
            endpoint=False,
        ):

            x1 = (
                0.12
                * diameter
                * math.cos(angle)
            )

            y1 = (
                0.12
                * diameter
                * math.sin(angle)
            )

            x2 = (
                0.47
                * diameter
                * math.cos(
                    angle + 0.12
                )
            )

            y2 = (
                0.47
                * diameter
                * math.sin(
                    angle + 0.12
                )
            )

            fig.add_trace(
                go.Scatter3d(
                    x=[x1, x2],
                    y=[y1, y2],
                    z=[
                        elevation,
                        elevation,
                    ],
                    mode="lines",
                    line=dict(
                        width=10
                    ),
                    showlegend=False,
                )
            )

        return

    # --------------------------------------------------------
    # HYDROFOIL
    # --------------------------------------------------------

    if geometry == "hydrofoil":

        theta = np.linspace(
            0,
            2 * np.pi,
            100
        )

        fig.add_trace(
            go.Scatter3d(
                x=(
                    R
                    * np.cos(theta)
                ),
                y=(
                    R
                    * np.sin(theta)
                ),
                z=np.ones_like(theta)
                * elevation,
                mode="lines",
                line=dict(
                    width=7
                ),
                name=impeller_type,
            )
        )

        for angle in np.linspace(
            0,
            2 * np.pi,
            data["blades"],
            endpoint=False,
        ):

            p1 = (
                0.10
                * diameter
            )

            p2 = (
                0.48
                * diameter
            )

            x = [
                p1 * math.cos(angle),
                p2 * math.cos(
                    angle + 0.10
                ),
            ]

            y = [
                p1 * math.sin(angle),
                p2 * math.sin(
                    angle + 0.10
                ),
            ]

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=[
                        elevation,
                        elevation,
                    ],
                    mode="lines",
                    line=dict(
                        width=12
                    ),
                    showlegend=False,
                )
            )

        return

    # --------------------------------------------------------
    # MARINE PROPELLER
    # --------------------------------------------------------

    if geometry == "marine":

        for angle in np.linspace(
            0,
            2 * np.pi,
            data["blades"],
            endpoint=False,
        ):

            t = np.linspace(
                0,
                1,
                30
            )

            r = (
                0.10
                * diameter
                + 0.40
                * diameter
                * t
            )

            sweep = (
                angle
                + 0.6
                * t
            )

            x = (
                r
                * np.cos(sweep)
            )

            y = (
                r
                * np.sin(sweep)
            )

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=np.ones_like(x)
                    * elevation,
                    mode="lines",
                    line=dict(
                        width=10
                    ),
                    name=(
                        impeller_type
                        if angle == 0
                        else None
                    ),
                    showlegend=(
                        angle == 0
                    ),
                )
            )

        return

    # --------------------------------------------------------
    # PADDLE
    # --------------------------------------------------------

    if geometry == "paddle":

        theta = np.linspace(
            0,
            2 * np.pi,
            100
        )

        for angle in [
            0,
            np.pi,
        ]:

            x1 = (
                0.10
                * diameter
                * math.cos(angle)
            )

            y1 = (
                0.10
                * diameter
                * math.sin(angle)
            )

            x2 = (
                R
                * math.cos(angle)
            )

            y2 = (
                R
                * math.sin(angle)
            )

            fig.add_trace(
                go.Scatter3d(
                    x=[x1, x2],
                    y=[y1, y2],
                    z=[
                        elevation,
                        elevation,
                    ],
                    mode="lines",
                    line=dict(
                        width=14
                    ),
                    name=impeller_type,
                    showlegend=(
                        angle == 0
                    ),
                )
            )

        return

    # --------------------------------------------------------
    # ANCHOR / GATE
    # --------------------------------------------------------

    if geometry in [
        "anchor",
        "gate",
    ]:

        z1 = elevation - 0.25 * diameter

        z2 = elevation + 0.25 * diameter

        theta = np.linspace(
            0,
            np.pi,
            60
        )

        x = R * np.cos(theta)

        y = R * np.sin(theta)

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=np.ones_like(x)
                * z1,
                mode="lines",
                line=dict(
                    width=10
                ),
                name=impeller_type,
            )
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=np.ones_like(x)
                * z2,
                mode="lines",
                line=dict(
                    width=10
                ),
                showlegend=False,
            )
        )

        fig.add_trace(
            go.Scatter3d(
                x=[
                    R,
                    R,
                ],
                y=[
                    0,
                    0,
                ],
                z=[
                    z1,
                    z2,
                ],
                mode="lines",
                line=dict(
                    width=10
                ),
                showlegend=False,
            )
        )

        return

    # --------------------------------------------------------
    # RCI
    # --------------------------------------------------------

    if geometry == "rci":

        """

        Parametric representation of a retreating-curve
        impeller.

        This is a conceptual geometry representation.
        Vendor CAD geometry should be used for final design.
        """

        for blade_angle in np.linspace(
            0,
            2 * np.pi,
            data["blades"],
            endpoint=False,
        ):

            t = np.linspace(
                0,
                1,
                80
            )

            r = (
                0.10
                * diameter
                + 0.40
                * diameter
                * t
            )

            curve = (
                blade_angle
                + 0.75
                * t
                - 0.20
                * np.sin(
                    np.pi * t
                )
            )

            x = (
                r
                * np.cos(curve)
            )

            y = (
                r
                * np.sin(curve)
            )

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=np.ones_like(x)
                    * elevation,
                    mode="lines",
                    line=dict(
                        width=12
                    ),
                    name=(
                        impeller_type
                        if blade_angle == 0
                        else None
                    ),
                    showlegend=(
                        blade_angle == 0
                    ),
                )
            )

        return

    # --------------------------------------------------------
    # HELICAL RIBBON
    # --------------------------------------------------------

    if geometry == "helical":

        t = np.linspace(
            0,
            2 * np.pi * 2,
            200
        )

        z = (
            elevation
            + 0.35
            * diameter
            * (
                t
                / (2 * np.pi * 2)
                - 0.5
            )
        )

        r = 0.45 * diameter

        x = (
            r
            * np.cos(t)
        )

        y = (
            r
            * np.sin(t)
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=12
                ),
                name=impeller_type,
            )
        )


# ============================================================
# 3D REACTOR
# ============================================================

def create_reactor_3d(
    reactor,
    agitator_name,
):

    tank_d = safe_float(
        reactor["tank_id_m"]
    )

    total_height = safe_float(
        reactor["total_height_m"]
    )

    liquid_height = liquid_height_from_volume(

        safe_float(
            reactor[
                "working_volume_l"
            ]
        ) / 1000.0,

        tank_d,

        reactor["bottom"],

        reactor["top"],

        safe_float(
            reactor[
                "straight_side_m"
            ]
        ),

        total_height,
    )

    fig = go.Figure()

    radius = tank_d / 2.0

    bottom_depth = head_depth(
        tank_d,
        reactor["bottom"]
    )

    top_depth = head_depth(
        tank_d,
        reactor["top"]
    )

    straight_bottom = bottom_depth

    straight_top = (
        total_height
        - top_depth
    )

    if straight_top < straight_bottom:

        straight_top = (
            straight_bottom
            + safe_float(
                reactor[
                    "straight_side_m"
                ]
            )
        )

    # --------------------------------------------------------
    # SHELL
    # --------------------------------------------------------

    add_cylinder(
        fig,
        radius,
        straight_bottom,
        straight_top,
        "Reactor Shell",
        opacity=0.12,
    )

    # --------------------------------------------------------
    # BOTTOM
    # --------------------------------------------------------

    add_head(
        fig,
        tank_d,
        straight_bottom,
        reactor["bottom"],
        "bottom",
        opacity=0.12,
    )

    # --------------------------------------------------------
    # TOP
    # --------------------------------------------------------

    add_head(
        fig,
        tank_d,
        straight_top,
        reactor["top"],
        "top",
        opacity=0.12,
    )

    # --------------------------------------------------------
    # LIQUID
    # --------------------------------------------------------

    liquid_radius = (
        radius * 0.98
    )

    theta = np.linspace(
        0,
        2 * np.pi,
        80
    )

    x = (
        liquid_radius
        * np.cos(theta)
    )

    y = (
        liquid_radius
        * np.sin(theta)
    )

    fig.add_trace(
        go.Scatter3d(
            x=x,
            y=y,
            z=np.ones_like(theta)
            * liquid_height,
            mode="lines",
            line=dict(
                width=8
            ),
            name="Liquid Level",
        )
    )

    # --------------------------------------------------------
    # SHAFT
    # --------------------------------------------------------

    add_shaft(
        fig,
        tank_d * 0.025,
        0,
        total_height,
    )

    # --------------------------------------------------------
    # IMPELLERS
    # --------------------------------------------------------

    n_impellers = int(
        reactor["n_impellers"]
    )

    elevations = reactor.get(
        "impeller_elevations_m",
        []
    )

    if len(elevations) < n_impellers:

        elevations = []

        for i in range(
            n_impellers
        ):

            elevations.append(
                liquid_height
                * (
                    0.20
                    + 0.60
                    * i
                    / max(
                        n_impellers - 1,
                        1
                    )
                )
            )

    for i in range(
        n_impellers
    ):

        elevation = clamp(
            safe_float(
                elevations[i]
            ),
            0.01,
            max(
                liquid_height
                - 0.01,
                0.01
            ),
        )

        add_impeller_geometry(
            fig,
            agitator_name,
            safe_float(
                reactor[
                    "impeller_d_m"
                ]
            ),
            elevation,
        )

    # --------------------------------------------------------
    # BAFFLES
    # --------------------------------------------------------

    n_baffles = int(
        reactor.get(
            "baffles",
            0
        )
    )

    baffle_width = safe_float(
        reactor.get(
            "baffle_width_m",
            tank_d * 0.10
        )
    )

    for i in range(
        n_baffles
    ):

        angle = (
            2
            * np.pi
            * i
            / max(
                n_baffles,
                1
            )
        )

        rb = (
            radius
            - baffle_width
        )

        x1 = (
            rb
            * math.cos(angle)
        )

        y1 = (
            rb
            * math.sin(angle)
        )

        x2 = (
            radius
            * math.cos(angle)
        )

        y2 = (
            radius
            * math.sin(angle)
        )

        fig.add_trace(
            go.Scatter3d(
                x=[
                    x1,
                    x2,
                ],
                y=[
                    y1,
                    y2,
                ],
                z=[
                    bottom_depth,
                    liquid_height,
                ],
                mode="lines",
                line=dict(
                    width=10
                ),
                name="Baffle",
                showlegend=(
                    i == 0
                ),
            )
        )

    # --------------------------------------------------------
    # GAS SPARGER
    # --------------------------------------------------------

    gas_flow = safe_float(
        reactor.get(
            "gas_flow_nm3h",
            0
        )
    )

    if gas_flow > 0:

        sparger_r = (
            radius * 0.50
        )

        x = (
            sparger_r
            * np.cos(theta)
        )

        y = (
            sparger_r
            * np.sin(theta)
        )

        z = np.ones_like(theta) * (
            bottom_depth
            + 0.10 * tank_d
        )

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(
                    width=6
                ),
                name="Gas Sparger",
            )
        )

    # --------------------------------------------------------
    # MIXING PATTERN
    # --------------------------------------------------------

    flow = AGITATORS[
        agitator_name
    ]["flow"]

    if flow.startswith("Axial"):

        direction = 1

    else:

        direction = 0

    if direction == 1:

        for rr in np.linspace(
            0.2,
            0.8,
            4
        ):

            z = np.linspace(
                bottom_depth
                + 0.10 * total_height,

                liquid_height
                - 0.10 * total_height,

                40
            )

            x = (
                rr
                * radius
                * np.cos(
                    z * 4
                )
            )

            y = (
                rr
                * radius
                * np.sin(
                    z * 4
                )
            )

            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(
                        width=2
                    ),
                    name="Conceptual Mixing Pattern",
                    showlegend=(
                        rr == 0.2
                    ),
                )
            )

    fig.update_layout(

        height=720,

        margin=dict(
            l=0,
            r=0,
            t=20,
            b=0,
        ),

        scene=dict(

            xaxis_title="X (m)",

            yaxis_title="Y (m)",

            zaxis_title="Height (m)",

            aspectmode="data",

        ),

        legend=dict(
            orientation="h"
        ),
    )

    return fig


# ============================================================
# ACTIVE REACTORS
# ============================================================

def get_active_reactors():

    mode = st.session_state.project[
        "study_mode"
    ]

    if mode == "Single Reactor":

        return [
            st.session_state.project[
                "active_reactor"
            ]
        ]

    if mode == "Lab vs Pilot":

        return [
            "Lab",
            "Pilot"
        ]

    if mode == "Pilot vs Commercial":

        return [
            "Pilot",
            "Commercial"
        ]

    if mode == "Lab vs Commercial":

        return [
            "Lab",
            "Commercial"
        ]

    return [
        "Lab",
        "Pilot",
        "Commercial"
    ]


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "⚗️ Reactor Engineering"
)

st.sidebar.caption(
    "Process Engineering Scale-Up Platform"
)

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

        "📐 Geometry Library",

        "📥 Excel Export",
    ],
)


# ============================================================
# AUTO-SAVE INDICATOR
# ============================================================

st.sidebar.divider()

if st.session_state.project.get(
    "saved",
    False
):

    st.sidebar.success(
        "✓ Inputs automatically saved"
    )

else:

    st.sidebar.warning(
        "Saving unavailable"
    )


# ============================================================
# PROJECT PAGE
# ============================================================

if page == "📋 Project & Design Basis":

    st.header(
        "📋 Project & Design Basis"
    )

    p = st.session_state.project

    c1, c2 = st.columns(2)

    with c1:

        p["project_name"] = st.text_input(
            "Project Name",
            value=p[
                "project_name"
            ],
        )

        p["product"] = st.text_input(
            "Product / Process",
            value=p[
                "product"
            ],
        )

        p["engineer"] = st.text_input(
            "Process Engineer",
            value=p[
                "engineer"
            ],
        )

        p["revision"] = st.text_input(
            "Revision",
            value=p[
                "revision"
            ],
        )

    with c2:

        p["reaction"] = st.selectbox(
            "Reaction / Process Type",
            REACTION_TYPES,
            index=REACTION_TYPES.index(
                p["reaction"]
            ),
        )

        p["study_mode"] = st.selectbox(
            "Study / Comparison Mode",
            STUDY_MODES,
            index=STUDY_MODES.index(
                p["study_mode"]
            ),
        )

        p["scale_up_criterion"] = st.selectbox(
            "Primary Scale-Up Criterion",
            SCALE_UP_CRITERIA,
            index=SCALE_UP_CRITERIA.index(
                p["scale_up_criterion"]
            ),
        )

    if p["study_mode"] == "Single Reactor":

        p["active_reactor"] = st.selectbox(
            "Reactor to Design",
            [
                "Lab",
                "Pilot",
                "Commercial",
            ],
            index=[
                "Lab",
                "Pilot",
                "Commercial",
            ].index(
                p.get(
                    "active_reactor",
                    "Commercial"
                )
            ),
        )

    st.info(
        "The selected Study Mode controls which reactors "
        "are required and which reactors appear in comparisons."
    )

    save_project()


# ============================================================
# REACTOR CONFIGURATION
# ============================================================

elif page == "⚙️ Reactor Configuration":

    st.header(
        "⚙️ Reactor Configuration"
    )

    active = get_active_reactors()

    tabs = st.tabs(
        active
    )

    for tab, scale in zip(
        tabs,
        active
    ):

        with tab:

            r = st.session_state.project[
                "reactors"
            ][scale]

            st.subheader(
                f"{scale} Reactor"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                r[
                    "working_volume_l"
                ] = st.number_input(
                    "Working Volume (L)",
                    min_value=0.01,
                    value=float(
                        r[
                            "working_volume_l"
                        ]
                    ),
                    key=f"{scale}_volume",
                )

                r[
                    "tank_id_m"
                ] = st.number_input(
                    "Tank ID (m)",
                    min_value=0.01,
                    value=float(
                        r[
                            "tank_id_m"
                        ]
                    ),
                    key=f"{scale}_tank",
                )

                r[
                    "straight_side_m"
                ] = st.number_input(
                    "Straight Side Height (m)",
                    min_value=0.01,
                    value=float(
                        r[
                            "straight_side_m"
                        ]
                    ),
                    key=f"{scale}_ss",
                )

                r[
                    "total_height_m"
                ] = st.number_input(
                    "Total Vessel Height (m)",
                    min_value=0.01,
                    value=float(
                        r[
                            "total_height_m"
                        ]
                    ),
                    key=f"{scale}_total",
                )

            with c2:

                r[
                    "rpm"
                ] = st.number_input(
                    "Agitator RPM",
                    min_value=0.1,
                    value=float(
                        r[
                            "rpm"
                        ]
                    ),
                    key=f"{scale}_rpm",
                )

                r[
                    "impeller_d_m"
                ] = st.number_input(
                    "Impeller Diameter (m)",
                    min_value=0.001,
                    value=float(
                        r[
                            "impeller_d_m"
                        ]
                    ),
                    key=f"{scale}_impd",
                )

                r[
                    "n_impellers"
                ] = st.number_input(
                    "Number of Impellers",
                    min_value=1,
                    max_value=10,
                    value=int(
                        r[
                            "n_impellers"
                        ]
                    ),
                    key=f"{scale}_nimp",
                )

                r[
                    "clearance_m"
                ] = st.number_input(
                    "Bottom Clearance (m)",
                    min_value=0.0,
                    value=float(
                        r[
                            "clearance_m"
                        ]
                    ),
                    key=f"{scale}_clearance",
                )

            with c3:

                r[
                    "rho"
                ] = st.number_input(
                    "Liquid Density (kg/m³)",
                    min_value=0.1,
                    value=float(
                        r[
                            "rho"
                        ]
                    ),
                    key=f"{scale}_rho",
                )

                r[
                    "viscosity_cp"
                ] = st.number_input(
                    "Viscosity (cP)",
                    min_value=0.001,
                    value=float(
                        r[
                            "viscosity_cp"
                        ]
                    ),
                    key=f"{scale}_viscosity",
                )

                r[
                    "surface_tension_mn_m"
                ] = st.number_input(
                    "Surface Tension (mN/m)",
                    min_value=0.001,
                    value=float(
                        r[
                            "surface_tension_mn_m"
                        ]
                    ),
                    key=f"{scale}_sigma",
                )

            st.divider()

            c1, c2 = st.columns(2)

            with c1:

                r[
                    "bottom"
                ] = st.selectbox(
                    "Bottom Geometry",
                    BOTTOM_TYPES,
                    index=BOTTOM_TYPES.index(
                        r[
                            "bottom"
                        ]
                    ),
                    key=f"{scale}_bottom",
                )

            with c2:

                r[
                    "top"
                ] = st.selectbox(
                    "Top Geometry",
                    TOP_TYPES,
                    index=TOP_TYPES.index(
                        r[
                            "top"
                        ]
                    ),
                    key=f"{scale}_top",
                )

            # ------------------------------------------------
            # AUTOMATIC LIQUID HEIGHT
            # ------------------------------------------------

            liquid_height = liquid_height_from_volume(

                r[
                    "working_volume_l"
                ] / 1000.0,

                r[
                    "tank_id_m"
                ],

                r[
                    "bottom"
                ],

                r[
                    "top"
                ],

                r[
                    "straight_side_m"
                ],

                r[
                    "total_height_m"
                ],
            )

            st.markdown(
                f"""
                <div class="auto-card">
                <b>🔄 Automatically Calculated Liquid Height</b><br>
                Working Volume = {r["working_volume_l"]:.2f} L<br>
                Tank ID = {r["tank_id_m"]:.3f} m<br>
                Bottom = {r["bottom"]}<br>
                Top = {r["top"]}<br>
                <b>Calculated Liquid Height = {liquid_height:.3f} m</b>
                </div>
                """,
                unsafe_allow_html=True,
            )

            r[
                "calculated_liquid_height_m"
            ] = liquid_height

            # ------------------------------------------------
            # BAFFLES
            # ------------------------------------------------

            st.subheader(
                "Baffle Configuration"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                r[
                    "baffles"
                ] = st.number_input(
                    "Number of Baffles",
                    min_value=0,
                    max_value=16,
                    value=int(
                        r[
                            "baffles"
                        ]
                    ),
                    key=f"{scale}_baffles",
                )

            with c2:

                r[
                    "baffle_width_m"
                ] = st.number_input(
                    "Baffle Width (m)",
                    min_value=0.0,
                    value=float(
                        r[
                            "baffle_width_m"
                        ]
                    ),
                    key=f"{scale}_bw",
                )

            with c3:

                r[
                    "baffle_clearance_m"
                ] = st.number_input(
                    "Baffle Clearance (m)",
                    min_value=0.0,
                    value=float(
                        r[
                            "baffle_clearance_m"
                        ]
                    ),
                    key=f"{scale}_bc",
                )

            # ------------------------------------------------
            # IMPELLER ELEVATIONS
            # ------------------------------------------------

            st.subheader(
                "Impeller Elevations"
            )

            elevations = []

            for i in range(
                int(
                    r[
                        "n_impellers"
                    ]
                )
            ):

                default_elevation = (

                    r.get(
                        "impeller_elevations_m",
                        []
                    )[i]

                    if i < len(
                        r.get(
                            "impeller_elevations_m",
                            []
                        )
                    )

                    else liquid_height
                    * (
                        0.20
                        + 0.60
                        * i
                        / max(
                            int(
                                r[
                                    "n_impellers"
                                ]
                            ) - 1,
                            1,
                        )
                    )
                )

                elevation = st.number_input(
                    f"Impeller {i+1} Elevation (m)",
                    min_value=0.0,
                    value=float(
                        default_elevation
                    ),
                    key=f"{scale}_elev_{i}",
                )

                elevations.append(
                    elevation
                )

            r[
                "impeller_elevations_m"
            ] = elevations

            # ------------------------------------------------
            # MATERIAL / SOLID
            # ------------------------------------------------

            st.subheader(
                "Material / Solid Properties"
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                r[
                    "solid_density"
                ] = st.number_input(
                    "Solid Density (kg/m³)",
                    min_value=0.0,
                    value=float(
                        r[
                            "solid_density"
                        ]
                    ),
                    key=f"{scale}_solidrho",
                )

            with c2:

                r[
                    "particle_size_um"
                ] = st.number_input(
                    "Particle Diameter (µm)",
                    min_value=0.0,
                    value=float(
                        r[
                            "particle_size_um"
                        ]
                    ),
                    key=f"{scale}_particle",
                )

            with c3:

                r[
                    "solids_wt_percent"
                ] = st.number_input(
                    "Solids Concentration (wt%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(
                        r[
                            "solids_wt_percent"
                        ]
                    ),
                    key=f"{scale}_solidwt",
                )

            save_project()


# ============================================================
# AGITATION SYSTEM
# ============================================================

elif page == "🔄 Agitation System":

    st.header(
        "🔄 Agitation System"
    )

    p = st.session_state.project

    agitator_name = st.selectbox(
        "Agitator / Impeller Type",
        list(
            AGITATORS.keys()
        ),
        index=list(
            AGITATORS.keys()
        ).index(
            p[
                "global_agitator"
            ][
                "type"
            ]
        ),
    )

    p[
        "global_agitator"
    ][
        "type"
    ] = agitator_name

    data = AGITATORS[
        agitator_name
    ]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Category",
        data["category"]
    )

    c2.metric(
        "Flow",
        data["flow"]
    )

    c3.metric(
        "Blades",
        data["blades"]
    )

    c4.metric(
        "Geometry",
        data["geometry"]
    )

    st.info(
        data["notes"]
    )

    st.divider()

    st.subheader(
        "Number of Impellers"
    )

    p[
        "global_agitator"
    ][
        "n_impellers"
    ] = st.number_input(
        "Default Number of Impellers",
        min_value=1,
        max_value=10,
        value=int(
            p[
                "global_agitator"
            ][
                "n_impellers"
            ]
        ),
    )

    # --------------------------------------------------------
    # COEFFICIENTS
    # --------------------------------------------------------

    st.subheader(
        "Agitator Coefficients"
    )

    c1, c2 = st.columns(2)

    with c1:

        np_default = (
            data["Np"]
        )

        if np_default is None:

            np_default = 0.0

        np_override = st.number_input(
            "Power Number Np Override",
            min_value=0.0,
            value=float(
                np_default
            ),
        )

    with c2:

        nq_default = (
            data["Nq"]
        )

        if nq_default is None:

            nq_default = 0.0

        nq_override = st.number_input(
            "Pumping Number Nq Override",
            min_value=0.0,
            value=float(
                nq_default
            ),
        )

    if data["Np"] is None:

        st.warning(
            "This agitator does not have a universal "
            "coefficient in this library. Enter validated "
            "vendor/pilot data before using the calculated "
            "power for final engineering."
        )

    p[
        "global_agitator"
    ][
        "Np_override"
    ] = np_override

    p[
        "global_agitator"
    ][
        "Nq_override"
    ] = nq_override

    save_project()

    # --------------------------------------------------------
    # SELECTED REACTOR RESULTS
    # --------------------------------------------------------

    active = get_active_reactors()

    for scale in active:

        result = calculate_reactor(

            p[
                "reactors"
            ][scale],

            agitator_name,

            np_override,

            nq_override,
        )

        st.subheader(
            f"{scale} Agitation"
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Power",
            f"{result.get('power_kw', 0):.2f} kW"
        )

        c2.metric(
            "P/V",
            f"{result.get('pv_kw_m3', 0):.3f} kW/m³"
        )

        c3.metric(
            "Tip Speed",
            f"{result.get('tip_speed_m_s', 0):.2f} m/s"
        )

        c4.metric(
            "Pumping",
            f"{result.get('pumping_m3_h', 0):.1f} m³/h"
        )

        c5.metric(
            "Re",
            f"{result.get('re', 0):.2e}"
        )


# ============================================================
# EXECUTIVE DASHBOARD
# ============================================================

elif page == "🏠 Executive Dashboard":

    st.header(
        "🏭 Reactor Scale-Up & Mixing Engineering Dashboard"
    )

    p = st.session_state.project

    active = get_active_reactors()

    st.markdown(
        f"""
        <div class="info-card">
        <b>Project:</b> {p["project_name"]}<br>
        <b>Reaction:</b> {p["reaction"]}<br>
        <b>Study Mode:</b> {p["study_mode"]}<br>
        <b>Scale-Up Basis:</b> {p["scale_up_criterion"]}<br>
        <b>Active Reactors:</b> {", ".join(active)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    agitator = p[
        "global_agitator"
    ][
        "type"
    ]

    np_override = p[
        "global_agitator"
    ][
        "Np_override"
    ]

    nq_override = p[
        "global_agitator"
    ][
        "Nq_override"
    ]

    rows = []

    results = {}

    for scale in active:

        r = p[
            "reactors"
        ][scale]

        result = calculate_reactor(

            r,

            agitator,

            np_override,

            nq_override,
        )

        results[
            scale
        ] = result

        rows.append({

            "Reactor":
                scale,

            "Working Volume (L)":
                r[
                    "working_volume_l"
                ],

            "Liquid Height (m)":
                result[
                    "liquid_height_m"
                ],

            "RPM":
                result[
                    "rpm"
                ],

            "Impeller D (m)":
                result[
                    "impeller_d_m"
                ],

            "Impellers":
                result[
                    "n_impellers"
                ],

            "Power (kW)":
                result[
                    "power_kw"
                ],

            "P/V (kW/m³)":
                result[
                    "pv_kw_m3"
                ],

            "Tip Speed (m/s)":
                result[
                    "tip_speed_m_s"
                ],

            "Pumping (m³/h)":
                result[
                    "pumping_m3_h"
                ],

            "Q/V (1/h)":
                result[
                    "q_v_h"
                ],

            "Turnover (min)":
                result[
                    "turnover_min"
                ],

            "Re":
                result[
                    "re"
                ],

            "Njs (RPM)":
                result[
                    "njs_rpm"
                ],

            "N/Njs":
                result[
                    "n_over_njs"
                ],

            "Motor (kW)":
                result[
                    "recommended_motor_kw"
                ],
        })

    if rows:

        df = pd.DataFrame(
            rows
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    for scale in active:

        result = results[
            scale
        ]

        st.subheader(
            f"{scale} Key Engineering Parameters"
        )

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        c1.metric(
            "Volume",
            f"{result['volume_m3']*1000:.1f} L"
        )

        c2.metric(
            "Liquid Height",
            f"{result['liquid_height_m']:.3f} m"
        )

        c3.metric(
            "P/V",
            f"{result['pv_kw_m3']:.3f} kW/m³"
        )

        c4.metric(
            "Tip Speed",
            f"{result['tip_speed_m_s']:.2f} m/s"
        )

        c5.metric(
            "Power",
            f"{result['power_kw']:.2f} kW"
        )

        c6.metric(
            "Pumping",
            f"{result['pumping_m3_h']:.1f} m³/h"
        )

    # --------------------------------------------------------
    # CHART
    # --------------------------------------------------------

    if len(active) > 1:

        chart_df = pd.DataFrame(
            {
                "Reactor":
                    active,

                "P/V":
                    [
                        results[x][
                            "pv_kw_m3"
                        ]
                        for x in active
                    ],

                "Tip Speed":
                    [
                        results[x][
                            "tip_speed_m_s"
                        ]
                        for x in active
                    ],

                "Power":
                    [
                        results[x][
                            "power_kw"
                        ]
                        for x in active
                    ],
            }
        )

        st.subheader(
            "Scale-Up Comparison"
        )

        st.bar_chart(
            chart_df.set_index(
                "Reactor"
            )
        )


# ============================================================
# SCALE-UP ENGINE
# ============================================================

elif page == "📊 Scale-Up Engine":

    st.header(
        "📊 Scale-Up Engine"
    )

    p = st.session_state.project

    criterion = st.selectbox(
        "Scale-Up Criterion",
        SCALE_UP_CRITERIA,
        index=SCALE_UP_CRITERIA.index(
            p[
                "scale_up_criterion"
            ]
        ),
    )

    p[
        "scale_up_criterion"
    ] = criterion

    st.info(
        f"Selected basis: **{criterion}**"
    )

    mode = p[
        "study_mode"
    ]

    if mode == "Single Reactor":

        st.warning(
            "Scale-up comparison requires at least two reactors. "
            "You can still use the reactor calculation and "
            "engineering validation modules."
        )

    else:

        active = get_active_reactors()

        source_scale = active[0]

        target_scale = active[-1]

        source = p[
            "reactors"
        ][source_scale]

        target = p[
            "reactors"
        ][target_scale]

        calculated_rpm = scale_up_rpm(

            criterion,

            source,

            target,
        )

        st.subheader(
            f"{source_scale} → {target_scale}"
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            f"{source_scale} RPM",
            f"{source['rpm']:.1f}"
        )

        c2.metric(
            "Calculated Target RPM",
            f"{calculated_rpm:.1f}"
        )

        c3.metric(
            f"Actual {target_scale} RPM",
            f"{target['rpm']:.1f}"
        )

        deviation = (

            (
                target["rpm"]
                / calculated_rpm
            )
            - 1
        ) * 100 if calculated_rpm > 0 else 0

        c4.metric(
            "Deviation",
            f"{deviation:.1f}%"
        )

        # ----------------------------------------------------
        # ALL METHODS
        # ----------------------------------------------------

        st.subheader(
            "All Scale-Up Methods"
        )

        method_rows = []

        for method in SCALE_UP_CRITERIA:

            if method in [
                "User Defined",
                "Constant KLa",
            ]:

                continue

            rpm_value = scale_up_rpm(

                method,

                source,

                target,
            )

            method_rows.append({

                "Method":
                    method,

                "Calculated Target RPM":
                    rpm_value,

                "Actual Target RPM":
                    target["rpm"],

                "Deviation %":
                    (
                        (
                            target["rpm"]
                            / rpm_value
                            - 1
                        ) * 100
                        if rpm_value > 0
                        else None
                    ),
            })

        st.dataframe(
            pd.DataFrame(
                method_rows
            ),
            use_container_width=True,
            hide_index=True,
        )

        save_project()


# ============================================================
# SOLID LIQUID
# ============================================================

elif page == "🧱 Solid-Liquid":

    st.header(
        "🧱 Solid-Liquid Suspension"
    )

    active = get_active_reactors()

    if not active:

        st.warning(
            "Configure a reactor first."
        )

    else:

        scale = st.selectbox(
            "Reactor",
            active
        )

        r = st.session_state.project[
            "reactors"
        ][scale]

        p = st.session_state.project

        agitator = p[
            "global_agitator"
        ][
            "type"
        ]

        result = calculate_reactor(

            r,

            agitator,

            p[
                "global_agitator"
            ][
                "Np_override"
            ],

            p[
                "global_agitator"
            ][
                "Nq_override"
            ],
        )

        njs = result[
            "njs_rpm"
        ]

        if njs is None:

            st.warning(
                "Enter solids concentration > 0 and "
                "solid properties in Reactor Configuration."
            )

        else:

            ratio = result[
                "n_over_njs"
            ]

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Estimated Njs",
                f"{njs:.1f} RPM"
            )

            c2.metric(
                "Actual N",
                f"{r['rpm']:.1f} RPM"
            )

            c3.metric(
                "N / Njs",
                f"{ratio:.2f}"
            )

            if ratio >= 1.20:

                st.success(
                    "PASS — RPM is above the selected "
                    "screening N/Njs margin."
                )

            elif ratio >= 1.00:

                st.warning(
                    "WARNING — Suspension is marginal."
                )

            else:

                st.error(
                    "FAIL — Agitation is below estimated Njs."
                )

            st.info(
                "Njs shown here is an engineering screening "
                "calculation. Validate the correlation coefficient "
                "against pilot/vendor/CFD data before final design."
            )


# ============================================================
# GAS LIQUID
# ============================================================

elif page == "💨 Gas-Liquid":

    st.header(
        "💨 Gas-Liquid Mixing"
    )

    active = get_active_reactors()

    scale = st.selectbox(
        "Reactor",
        active
    )

    r = st.session_state.project[
        "reactors"
    ][scale]

    p = st.session_state.project

    result = calculate_reactor(

        r,

        p[
            "global_agitator"
        ][
            "type"
        ],

        p[
            "global_agitator"
        ][
            "Np_override"
        ],

        p[
            "global_agitator"
        ][
            "Nq_override"
        ],
    )

    gas_flow = st.number_input(
        "Gas Flow (Nm³/h)",
        min_value=0.0,
        value=float(
            r[
                "gas_flow_nm3h"
            ]
        ),
        key=f"gas_{scale}",
    )

    r[
        "gas_flow_nm3h"
    ] = gas_flow

    bubble_d = st.number_input(
        "Bubble Diameter (mm)",
        min_value=0.1,
        value=float(
            r[
                "bubble_diameter_mm"
            ]
        ),
        key=f"bubble_{scale}",
    )

    r[
        "bubble_diameter_mm"
    ] = bubble_d

    volume_m3 = result[
        "volume_m3"
    ]

    if gas_flow > 0 and volume_m3 > 0:

        tank_area = (
            math.pi
            * r[
                "tank_id_m"
            ]**2
            / 4
        )

        vvm = (
            gas_flow
            / 60.0
            / volume_m3
        )

        superficial_velocity = (
            gas_flow
            / 3600.0
            / tank_area
        )

        gas_holdup = min(
            0.35,
            0.02
            * max(
                superficial_velocity
                * 100,
                0.001
            )**0.6
            * max(
                result[
                    "pv_kw_m3"
                ],
                0.001
            )**0.15,
        )

        kla = (
            0.20
            * max(
                result[
                    "pv_kw_m3"
                ],
                0.001
            )**0.5
            * max(
                superficial_velocity,
                1e-5,
            )**0.35
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "VVM",
            f"{vvm:.3f}"
        )

        c2.metric(
            "Superficial Velocity",
            f"{superficial_velocity:.4f} m/s"
        )

        c3.metric(
            "Gas Hold-up",
            f"{gas_holdup*100:.2f}%"
        )

        c4.metric(
            "Screening KLa",
            f"{kla:.4f} 1/s"
        )

        st.warning(
            "KLa and gas hold-up are screening correlations. "
            "Use validated system-specific correlations or pilot "
            "data for final equipment design."
        )

    save_project()


# ============================================================
# HEAT TRANSFER
# ============================================================

elif page == "🔥 Heat Transfer":

    st.header(
        "🔥 Reactor Heat Transfer"
    )

    c1, c2, c3 = st.columns(3)

    U = c1.number_input(
        "U (W/m²-K)",
        value=150.0,
        min_value=0.0,
    )

    area = c2.number_input(
        "Heat Transfer Area (m²)",
        value=20.0,
        min_value=0.0,
    )

    lmtd = c3.number_input(
        "LMTD (K)",
        value=43.1,
        min_value=0.0,
    )

    duty_kw = (
        U
        * area
        * lmtd
        / 1000.0
    )

    st.metric(
        "Heat Duty",
        f"{duty_kw:.2f} kW"
    )


# ============================================================
# 3D REACTOR
# ============================================================

elif page == "🧊 3D Reactor":

    st.header(
        "🧊 Interactive 3D Reactor Geometry"
    )

    p = st.session_state.project

    active = get_active_reactors()

    scale = st.selectbox(
        "Select Reactor",
        active
    )

    r = p[
        "reactors"
    ][scale]

    agitator = p[
        "global_agitator"
    ][
        "type"
    ]

    result = calculate_reactor(

        r,

        agitator,

        p[
            "global_agitator"
        ][
            "Np_override"
        ],

        p[
            "global_agitator"
        ][
            "Nq_override"
        ],
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Tank ID",
        f"{r['tank_id_m']:.3f} m"
    )

    c2.metric(
        "Liquid Height",
        f"{result['liquid_height_m']:.3f} m"
    )

    c3.metric(
        "Impeller",
        agitator
    )

    c4.metric(
        "Impellers",
        r["n_impellers"]
    )

    fig = create_reactor_3d(
        r,
        agitator
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.caption(
        "3D geometry is a conceptual engineering visualization. "
        "It is not a CFD model and should not replace vendor "
        "fabrication drawings or mechanical design calculations."
    )


# ============================================================
# VALIDATION
# ============================================================

elif page == "✓ Engineering Validation":

    st.header(
        "✓ Engineering Validation"
    )

    p = st.session_state.project

    active = get_active_reactors()

    agitator = p[
        "global_agitator"
    ][
        "type"
    ]

    for scale in active:

        st.subheader(
            f"{scale} Validation"
        )

        r = p[
            "reactors"
        ][scale]

        result = calculate_reactor(

            r,

            agitator,

            p[
                "global_agitator"
            ][
                "Np_override"
            ],

            p[
                "global_agitator"
            ][
                "Nq_override"
            ],
        )

        checks = []

        d_t = (
            result[
                "impeller_d_m"
            ]
            /
            result[
                "tank_d_m"
            ]
        )

        checks.append(
            (
                "PASS"
                if 0.20 <= d_t <= 0.70
                else "WARNING",
                "Impeller D/T",
                d_t,
                "Typical screening range 0.20–0.70"
            )
        )

        h_t = (
            result[
                "liquid_height_m"
            ]
            /
            result[
                "tank_d_m"
            ]
        )

        checks.append(
            (
                "PASS"
                if h_t <= 3.0
                else "WARNING",
                "Liquid H/T",
                h_t,
                "Check vessel aspect ratio"
            )
        )

        b_t = (
            safe_float(
                r[
                    "baffle_width_m"
                ]
            )
            /
            result[
                "tank_d_m"
            ]
        )

        checks.append(
            (
                "PASS"
                if r[
                    "baffles"
                ] == 0
                or 0.05 <= b_t <= 0.15
                else "WARNING",
                "Baffle W/T",
                b_t,
                "Screening range 0.05–0.15"
            )
        )

        checks.append(
            (
                "PASS"
                if result[
                    "rpm"
                ] > 0
                else "FAIL",
                "RPM",
                result[
                    "rpm"
                ],
                "RPM must be positive"
            )
        )

        tip_limit = safe_float(
            r.get(
                "tip_speed_limit",
                10.0
            )
        )

        checks.append(
            (
                "PASS"
                if result[
                    "tip_speed_m_s"
                ] <= tip_limit
                else "WARNING",
                "Tip Speed",
                result[
                    "tip_speed_m_s"
                ],
                f"Limit = {tip_limit:.2f} m/s"
            )
        )

        if result[
            "n_over_njs"
        ] is not None:

            checks.append(
                (
                    "PASS"
                    if result[
                        "n_over_njs"
                    ] >= 1.20
                    else (
                        "WARNING"
                        if result[
                            "n_over_njs"
                        ] >= 1.0
                        else "FAIL"
                    ),
                    "N/Njs",
                    result[
                        "n_over_njs"
                    ],
                    "Screening target >= 1.20"
                )
            )

        # ----------------------------------------------------
        # DISPLAY
        # ----------------------------------------------------

        for status, parameter, value, explanation in checks:

            if status == "PASS":

                st.success(
                    f"✓ {parameter}: {value:.3f} — {explanation}"
                )

            elif status == "WARNING":

                st.warning(
                    f"⚠ {parameter}: {value:.3f} — {explanation}"
                )

            else:

                st.error(
                    f"✕ {parameter}: {value:.3f} — {explanation}"
                )

        st.divider()

    st.info(
        "Engineering validation is a screening layer. "
        "Final design should include vendor agitator curves, "
        "mechanical shaft design, gearbox/motor limits, vessel "
        "mechanical design, validated mixing correlations, "
        "pilot data, CFD where required, and applicable design standards."
    )


# ============================================================
# AGITATOR LIBRARY
# ============================================================

elif page == "📚 Agitator Library":

    st.header(
        "📚 Agitator Geometry & Engineering Library"
    )

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

            "Geometry":
                data["geometry"],

            "Application":
                data["application"],

            "Recommended":
                data["recommended"],

            "Notes":
                data["notes"],
        })

    st.dataframe(
        pd.DataFrame(
            rows
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "Np/Nq values are screening library values. "
        "For final design use validated vendor curves or "
        "project-specific experimental correlations."
    )


# ============================================================
# GEOMETRY LIBRARY
# ============================================================

elif page == "📐 Geometry Library":

    st.header(
        "📐 Reactor Geometry Library"
    )

    rows = []

    for name, data in REACTOR_GEOMETRY.items():

        rows.append({

            "Geometry":
                name,

            "Type":
                data["type"],

            "Dish Depth Ratio":
                data["dish_ratio"],

            "Notes":
                data["notes"],
        })

    st.dataframe(
        pd.DataFrame(
            rows
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "Head volumes are process/visualization approximations. "
        "Exact vessel head geometry should be taken from the "
        "fabricator's drawing for final volume calculations."
    )


# ============================================================
# EXCEL EXPORT
# ============================================================

elif page == "📥 Excel Export":

    st.header(
        "📥 Engineering Excel Export"
    )

    p = st.session_state.project

    active = get_active_reactors()

    agitator = p[
        "global_agitator"
    ][
        "type"
    ]

    np_override = p[
        "global_agitator"
    ][
        "Np_override"
    ]

    nq_override = p[
        "global_agitator"
    ][
        "Nq_override"
    ]

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        # ----------------------------------------------------
        # PROJECT
        # ----------------------------------------------------

        pd.DataFrame(
            [
                {

                    "Project":
                        p[
                            "project_name"
                        ],

                    "Product":
                        p[
                            "product"
                        ],

                    "Engineer":
                        p[
                            "engineer"
                        ],

                    "Revision":
                        p[
                            "revision"
                        ],

                    "Reaction":
                        p[
                            "reaction"
                        ],

                    "Study Mode":
                        p[
                            "study_mode"
                        ],

                    "Scale-Up Criterion":
                        p[
                            "scale_up_criterion"
                        ],

                    "Selected Agitator":
                        agitator,
                }
            ]
        ).to_excel(
            writer,
            sheet_name="Project",
            index=False,
        )

        # ----------------------------------------------------
        # REACTORS
        # ----------------------------------------------------

        comparison_rows = []

        for scale in active:

            r = p[
                "reactors"
            ][scale]

            result = calculate_reactor(

                r,

                agitator,

                np_override,

                nq_override,
            )

            reactor_export = deepcopy(
                r
            )

            reactor_export[
                "Calculated Liquid Height (m)"
            ] = result[
                "liquid_height_m"
            ]

            reactor_export[
                "Power (kW)"
            ] = result[
                "power_kw"
            ]

            reactor_export[
                "P/V (kW/m3)"
            ] = result[
                "pv_kw_m3"
            ]

            reactor_export[
                "P/V (W/m3)"
            ] = result[
                "pv_w_m3"
            ]

            reactor_export[
                "Pumping (m3/h)"
            ] = result[
                "pumping_m3_h"
            ]

            reactor_export[
                "Q/V (1/h)"
            ] = result[
                "q_v_h"
            ]

            reactor_export[
                "Turnover (min)"
            ] = result[
                "turnover_min"
            ]

            reactor_export[
                "Tip Speed (m/s)"
            ] = result[
                "tip_speed_m_s"
            ]

            reactor_export[
                "Re"
            ] = result[
                "re"
            ]

            reactor_export[
                "Fr"
            ] = result[
                "fr"
            ]

            reactor_export[
                "Njs (RPM)"
            ] = result[
                "njs_rpm"
            ]

            reactor_export[
                "N/Njs"
            ] = result[
                "n_over_njs"
            ]

            reactor_export[
                "Shaft Power (kW)"
            ] = result[
                "shaft_power_kw"
            ]

            reactor_export[
                "Design Motor Power (kW)"
            ] = result[
                "design_motor_kw"
            ]

            reactor_export[
                "Recommended Motor (kW)"
            ] = result[
                "recommended_motor_kw"
            ]

            pd.DataFrame(
                [reactor_export]
            ).to_excel(
                writer,
                sheet_name=scale,
                index=False,
            )

            comparison_rows.append({

                "Reactor":
                    scale,

                "Working Volume L":
                    r[
                        "working_volume_l"
                    ],

                "Liquid Height m":
                    result[
                        "liquid_height_m"
                    ],

                "Tank ID m":
                    r[
                        "tank_id_m"
                    ],

                "RPM":
                    r[
                        "rpm"
                    ],

                "Impeller Diameter m":
                    r[
                        "impeller_d_m"
                    ],

                "Number Impellers":
                    r[
                        "n_impellers"
                    ],

                "Power kW":
                    result[
                        "power_kw"
                    ],

                "P/V kW/m3":
                    result[
                        "pv_kw_m3"
                    ],

                "Tip Speed m/s":
                    result[
                        "tip_speed_m_s"
                    ],

                "Pumping m3/h":
                    result[
                        "pumping_m3_h"
                    ],

                "Q/V 1/h":
                    result[
                        "q_v_h"
                    ],

                "Turnover min":
                    result[
                        "turnover_min"
                    ],

                "Re":
                    result[
                        "re"
                    ],

                "Fr":
                    result[
                        "fr"
                    ],

                "Njs RPM":
                    result[
                        "njs_rpm"
                    ],

                "N/Njs":
                    result[
                        "n_over_njs"
                    ],

                "Motor kW":
                    result[
                        "recommended_motor_kw"
                    ],
            })

            # ------------------------------------------------
            # IMPELLER RESULTS
            # ------------------------------------------------

            impeller_rows = []

            for imp in result[
                "impeller_results"
            ]:

                row = deepcopy(
                    imp
                )

                row[
                    "Reactor"
                ] = scale

                impeller_rows.append(
                    row
                )

            if impeller_rows:

                pd.DataFrame(
                    impeller_rows
                ).to_excel(
                    writer,
                    sheet_name=f"{scale} Impellers"[
                        :31
                    ],
                    index=False,
                )

        # ----------------------------------------------------
        # COMPARISON
        # ----------------------------------------------------

        pd.DataFrame(
            comparison_rows
        ).to_excel(
            writer,
            sheet_name="Comparison",
            index=False,
        )

        # ----------------------------------------------------
        # AGITATOR LIBRARY
        # ----------------------------------------------------

        agitator_rows = []

        for name, data in AGITATORS.items():

            agitator_rows.append({

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

                "Geometry":
                    data["geometry"],

                "Application":
                    data["application"],

                "Recommended":
                    data["recommended"],

                "Notes":
                    data["notes"],
            })

        pd.DataFrame(
            agitator_rows
        ).to_excel(
            writer,
            sheet_name="Agitator Library",
            index=False,
        )

        # ----------------------------------------------------
        # GEOMETRY LIBRARY
        # ----------------------------------------------------

        geometry_rows = []

        for name, data in REACTOR_GEOMETRY.items():

            geometry_rows.append({

                "Geometry":
                    name,

                "Type":
                    data["type"],

                "Dish Ratio":
                    data["dish_ratio"],

                "Notes":
                    data["notes"],
            })

        pd.DataFrame(
            geometry_rows
        ).to_excel(
            writer,
            sheet_name="Geometry Library",
            index=False,
        )

    output.seek(0)

    st.download_button(

        "⬇️ Download Complete Engineering Excel",

        output.getvalue(),

        file_name=(
            "Reactor_ScaleUp_Engineering.xlsx"
        ),

        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )

    st.success(
        "Complete engineering workbook generated."
    )


# ============================================================
# GLOBAL AUTOMATIC SAVE
# ============================================================

save_project()
