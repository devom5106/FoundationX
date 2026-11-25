"""
geotech.py - Calculation engine for CE 402 Geotechnical Engineering Design Platform.
Complies with IS 6403:1981, IS 2131:1981, IS 1904:1986, Schmertmann et al. (1978), and Terzaghi 1-D consolidation.
Every equation includes a SOURCE: comment referencing relevant standards and geotechnical literature.
Incorporates verified corrections from AI Audit (Findings 1-4 and Group 4 Audit).
"""

import math
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Dict, Any, Optional

GAMMA_W = 9.81  # Unit weight of water in kN/m3 (IS 6403:1981)


@dataclass
class Layer:
    """Soil layer in profile."""
    name: str
    top: float  # m bgl
    bot: float  # m bgl
    gamma_m: float  # moist/bulk unit weight, kN/m3
    gamma_sat: float  # saturated unit weight, kN/m3
    kind: str  # 'fill', 'sand', 'clay', 'gravel'
    c: float = 0.0  # cohesion, kPa
    phi: float = 0.0  # friction angle, deg
    Es: float = 0.0  # Young's modulus, kPa (if 0, derived from SPT/qc)
    e0: float = 0.8  # initial void ratio
    Cc: float = 0.0  # compression index
    Cr: float = 0.0  # recompression index
    sigma_p: float = 0.0  # preconsolidation stress, kPa (if 0, NC assumed)
    cv: float = 0.0  # m2/s
    spt_data: List[Dict[str, Any]] = field(default_factory=list)  # [{'depth': float, 'N': int}]

    @property
    def thickness(self) -> float:
        return max(0.0, self.bot - self.top)


@dataclass
class SoilProfile:
    """Multilayer soil profile with measured and design water table."""
    name: str
    layers: List[Layer]
    wt_measured: float  # Measured GWT at time of investigation (m bgl) - used for IS 2131 SPT
    wt_design: float    # Design GWT (seasonal high, m bgl) - used for Bearing capacity & Settlement

    @property
    def z_bot(self) -> float:
        if not self.layers:
            return 0.0
        return max(L.bot for L in self.layers)

    def layer_at(self, z: float) -> Optional[Layer]:
        """Returns the layer at depth z. If beyond borehole depth, returns bottom layer."""
        if not self.layers:
            return None
        for L in self.layers:
            if L.top <= z <= L.bot:
                return L
        if z > self.z_bot:
            return self.layers[-1]
        return self.layers[0]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "wt_measured": self.wt_measured,
            "wt_design": self.wt_design,
            "layers": [asdict(L) for L in self.layers]
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SoilProfile":
        layers = [Layer(**ld) for ld in d["layers"]]
        return cls(name=d.get("name", "Soil Profile"), layers=layers,
                   wt_measured=float(d.get("wt_measured", 2.0)),
                   wt_design=float(d.get("wt_design", 1.0)))


# ---------------------------------------------------------------------------
# Module P1: Soil Profile Stresses
# ---------------------------------------------------------------------------

def sigma_v_total_eff(profile: SoilProfile, z: float, wt: float) -> Tuple[float, float, bool]:
    """
    Computes total vertical stress sigma_v and effective vertical stress sigma'_v at depth z.
    SOURCE: Terzaghi effective stress principle; IS 6403:1981 Cl. 5.1.
    AI AUDIT CORRECTION (Finding 4):
    If z > z_bot, extrapolate total stress using the deepest layer's unit weight rather than
    stopping integration at z_bot (which caused an unphysical drop in effective stress).
    Returns (sigma_v, sigma'_v, is_extrapolated).
    """
    if not profile.layers:
        u = max(0.0, z - wt) * GAMMA_W
        return 0.0, -u, False

    sig_v = 0.0
    extrapolated = False

    for L in profile.layers:
        if z <= L.top:
            break
        z_start = L.top
        z_end = min(z, L.bot)
        if z_end > z_start:
            # Check water table intersection within this sub-interval
            if wt >= z_end:
                # Entirely above WT
                sig_v += L.gamma_m * (z_end - z_start)
            elif wt <= z_start:
                # Entirely below WT
                sig_v += L.gamma_sat * (z_end - z_start)
            else:
                # WT crosses layer
                sig_v += L.gamma_m * (wt - z_start) + L.gamma_sat * (z_end - wt)

    # If z is deeper than the borehole termination depth
    z_bot = profile.z_bot
    if z > z_bot:
        extrapolated = True
        bottom_layer = profile.layers[-1]
        delta_z = z - z_bot
        # If WT is below z_bot, check split, but typically WT is shallow
        if wt >= z:
            sig_v += bottom_layer.gamma_m * delta_z
        elif wt <= z_bot:
            sig_v += bottom_layer.gamma_sat * delta_z
        else:
            sig_v += bottom_layer.gamma_m * (wt - z_bot) + bottom_layer.gamma_sat * (z - wt)

    u = max(0.0, z - wt) * GAMMA_W
    sig_v_eff = max(0.0, sig_v - u)
    return sig_v, sig_v_eff, extrapolated


# ---------------------------------------------------------------------------
# Module P2: Parameter Tools (IS 2131 SPT Corrections & Direct Shear Fit)
# ---------------------------------------------------------------------------

def spt_corrections(N: int, sigma_v_eff: float, is_submerged_fine_sand: bool,
                    is_clay: bool = False, cn_cap: float = 2.0) -> Dict[str, Any]:
    """
    Applies IS 2131:1981 corrections to field SPT N.
    SOURCE: IS 2131:1981 Cl. 5.2.1; Peck, Hanson & Thornburn (1974); IS 2131:1981 Cl. 5.2.2.
    AI AUDIT CORRECTIONS:
    - Finding 2: If is_clay is True, bypass overburden correction (CN = 1.0) and dilatancy, retaining field N.
    - Group 4 Audit Item 3: Use constant 1920 in Peck closed form CN = 0.77*log10(1920/sigma'_v), capped at cn_cap <= 2.0.
    - Group 4 Audit Item 1: Stress sigma'_v must be calculated using MEASURED groundwater table.
    """
    if is_clay:
        return {
            "N_field": N,
            "sigma_v_eff": sigma_v_eff,
            "CN": 1.0,
            "N_overburden": float(N),
            "applied_dilatancy": False,
            "N_design": float(N),
            "note": "Clay layer: IS 2131 Cl. 5.2.1 overburden & dilatancy corrections bypassed (retained field N)."
        }

    # Overburden correction for granular soils (IS 2131 / Peck et al. 1974)
    # SOURCE: Peck, Hanson & Thornburn (1974); IS 2131:1981 Cl. 5.2.1
    if sigma_v_eff > 0:
        cn_calc = 0.77 * math.log10(1920.0 / sigma_v_eff)
        cn = max(0.0, min(cn_cap, cn_calc))
    else:
        cn = cn_cap

    N_prime = cn * N

    # Dilatancy correction (IS 2131:1981 Cl. 5.2.2)
    # Applied for fine sand / silty sand below water table when N' > 15
    applied_dilatancy = False
    if is_submerged_fine_sand and N_prime > 15.0:
        N_double_prime = 15.0 + 0.5 * (N_prime - 15.0)
        applied_dilatancy = True
    else:
        N_double_prime = N_prime

    return {
        "N_field": N,
        "sigma_v_eff": sigma_v_eff,
        "CN": cn,
        "N_overburden": round(N_prime, 2),
        "applied_dilatancy": applied_dilatancy,
        "N_design": round(N_double_prime, 2),
        "note": "Granular soil: IS 2131 overburden and dilatancy applied."
    }


def fit_direct_shear(normal_stresses: List[float], shear_stresses: List[float]) -> Tuple[float, float, float]:
    """
    Fits Mohr-Coulomb failure envelope tau = c' + sigma_n * tan(phi') by ordinary least squares.
    SOURCE: IS 2720 (Part 13): 1986.
    Returns (c_prime, phi_prime_deg, r_squared).
    """
    x = np.array(normal_stresses, dtype=float)
    y = np.array(shear_stresses, dtype=float)
    if len(x) < 2:
        return 0.0, 0.0, 0.0

    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    c_prime = max(0.0, float(c))
    phi_prime_deg = math.degrees(math.atan(max(0.0, float(m))))

    # R^2 determination
    y_pred = m * x + c
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum((y - y_pred) ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

    return round(c_prime, 2), round(phi_prime_deg, 2), round(r2, 4)


# ---------------------------------------------------------------------------
# Module P3: Bearing Capacity (IS 6403:1981)
# ---------------------------------------------------------------------------

def is6403_factors(phi_deg: float) -> Tuple[float, float, float]:
    """
    IS 6403:1981 Table 1 bearing capacity factors Nc, Nq, Ngamma.
    SOURCE: IS 6403:1981 Cl. 5.1.1, Table 1.
    Nq = tan^2(45 + phi/2) * exp(pi * tan(phi))
    Nc = (Nq - 1) / tan(phi)  [or 5.14 at phi=0]
    Ngamma = 2 * (Nq + 1) * tan(phi)
    """
    if phi_deg <= 0.0:
        return 5.14, 1.0, 0.0

    phi_rad = math.radians(phi_deg)
    tan_phi = math.tan(phi_rad)
    tan_45_phi2 = math.tan(math.radians(45.0 + phi_deg / 2.0))

    Nq = (tan_45_phi2 ** 2) * math.exp(math.pi * tan_phi)
    Nc = (Nq - 1.0) / tan_phi
    Ngamma = 2.0 * (Nq + 1.0) * tan_phi
    return Nc, Nq, Ngamma


def shape_factors(shape: str, B: float, L: float) -> Tuple[float, float, float]:
    """
    IS 6403:1981 Table 2 Shape Factors sc, sq, sgamma.
    SOURCE: IS 6403:1981 Table 2.
    """
    if shape == "strip":
        return 1.0, 1.0, 1.0
    elif shape == "circle":
        return 1.3, 1.2, 0.6
    elif shape == "square":
        return 1.3, 1.2, 0.8
    else:  # 'rect'
        ratio = min(B, L) / max(B, L) if max(B, L) > 0 else 1.0
        sc = 1.0 + 0.2 * ratio
        sq = 1.0 + 0.2 * ratio
        sg = max(0.0, 1.0 - 0.4 * ratio)
        return sc, sq, sg


def depth_factors(phi_deg: float, Df: float, B_physical: float) -> Tuple[float, float, float]:
    """
    IS 6403:1981 Cl. 5.1.2.2 Depth Factors dc, dq, dgamma.
    SOURCE: IS 6403:1981 Cl. 5.1.2.2.
    NOTE (Finding 1): Uses physical footing width B_physical, NOT effective width B'.
    """
    if B_physical <= 0.0 or Df <= 0.0:
        return 1.0, 1.0, 1.0

    N_phi = math.tan(math.radians(45.0 + phi_deg / 2.0)) ** 2
    sqrt_N_phi = math.sqrt(N_phi)
    ratio = Df / B_physical

    dc = 1.0 + 0.2 * ratio * sqrt_N_phi
    if phi_deg < 10.0:
        dq = 1.0
        dg = 1.0
    else:
        dq = 1.0 + 0.1 * ratio * sqrt_N_phi
        dg = dq
    return dc, dq, dg


def water_table_factor(dw: float, Df: float, B: float) -> float:
    """
    IS 6403:1981 Cl. 5.1.2.4 Water table correction factor W'.
    SOURCE: IS 6403:1981 Cl. 5.1.2.4.
    dw: depth to design water table below existing ground level (m bgl)
    """
    if dw <= Df:
        return 0.5
    elif dw >= Df + B:
        return 1.0
    else:
        return 0.5 + 0.5 * ((dw - Df) / B)


def bearing_capacity_is6403(c: float, phi_deg: float, Df: float, B: float, L: float,
                            shape: str, gamma: float, dw_design: float,
                            ex: float = 0.0, ey: float = 0.0,
                            shear_mode: str = "general",
                            N_spt: Optional[float] = None,
                            FoS: float = 3.0) -> Dict[str, Any]:
    """
    Computes net ultimate (q_nu) and net safe (q_ns) bearing capacity per IS 6403:1981.
    AI AUDIT CORRECTIONS INCORPORATED:
    - Finding 1: For eccentric square footings (B' != L'), route to rectangular shape factors:
      eff_shape = 'rect' if (shape == 'square' and abs(B_eff - L_eff) > 1e-6) else shape
      and pass physical width B to depth_factors!
    """
    # 1. Effective Dimensions for Eccentricity (IS 6403:1981 Cl. 5.1.2)
    B_eff = max(0.1, B - 2.0 * abs(ex))
    L_eff = max(0.1, L - 2.0 * abs(ey))
    A_eff = B_eff * L_eff

    # 2. Shear Mode Determination (General, Local, or Blended)
    # SOURCE: IS 6403:1981 Cl. 5.2.2.1
    if shear_mode == "local":
        phi_calc = math.degrees(math.atan((2.0 / 3.0) * math.tan(math.radians(phi_deg))))
        c_calc = (2.0 / 3.0) * c
        blend_factor = 0.0
    elif shear_mode == "blended" and N_spt is not None:
        # Linear interpolation between local (N<=10) and general (N>=30)
        blend_factor = max(0.0, min(1.0, (N_spt - 10.0) / 20.0))
        phi_local = math.degrees(math.atan((2.0 / 3.0) * math.tan(math.radians(phi_deg))))
        phi_calc = (1.0 - blend_factor) * phi_local + blend_factor * phi_deg
        c_calc = (1.0 - blend_factor) * (2.0 / 3.0) * c + blend_factor * c
    else:  # General shear
        phi_calc = phi_deg
        c_calc = c
        blend_factor = 1.0

    Nc, Nq, Ng = is6403_factors(phi_calc)

    # 3. Shape Factors
    # AI AUDIT FINDING 1: Eccentric square footing must use rectangular shape factors
    eff_shape = "rect" if (shape == "square" and abs(B_eff - L_eff) > 1e-6) else shape
    sc, sq, sg = shape_factors(eff_shape, B_eff, L_eff)

    # 4. Depth Factors
    # AI AUDIT FINDING 1: Use physical width B, NOT effective width B_eff
    dc, dq, dg = depth_factors(phi_calc, Df, B)

    # 5. Inclination Factors (assuming vertical load ic=iq=ig=1.0 per IS 6403 Cl. 5.1.2.3)
    ic, iq, ig = 1.0, 1.0, 1.0

    # 6. Water Table Factor W' and Surcharge q
    # SOURCE: IS 6403:1981 Cl. 5.1.2.4 & Cl. 5.1
    W_prime = water_table_factor(dw_design, Df, B_eff)

    # Overburden stress at founding level Df using design WT
    if dw_design >= Df:
        q_overburden = gamma * Df
    else:
        q_overburden = gamma * dw_design + (gamma - GAMMA_W) * (Df - dw_design)

    # 7. Terms of IS 6403 Equation (Cl. 5.1)
    # qnu = c * Nc * sc * dc * ic + q * (Nq - 1) * sq * dq * iq + 0.5 * B_eff * gamma * Ng * sg * dg * ig * W'
    term_c = c_calc * Nc * sc * dc * ic
    term_q = q_overburden * (Nq - 1.0) * sq * dq * iq
    term_gamma = 0.5 * B_eff * gamma * Ng * sg * dg * ig * W_prime

    q_nu = term_c + term_q + term_gamma
    q_ns = q_nu / FoS
    q_gross_safe = q_ns + q_overburden
    P_safe = q_ns * A_eff

    return {
        "B_physical": B, "L_physical": L,
        "B_eff": round(B_eff, 3), "L_eff": round(L_eff, 3), "A_eff": round(A_eff, 3),
        "effective_shape": eff_shape,
        "shear_mode": shear_mode,
        "phi_calc": round(phi_calc, 2), "c_calc": round(c_calc, 2),
        "Nc": round(Nc, 3), "Nq": round(Nq, 3), "Ngamma": round(Ng, 3),
        "sc": round(sc, 3), "sq": round(sq, 3), "sgamma": round(sg, 3),
        "dc": round(dc, 3), "dq": round(dq, 3), "dgamma": round(dg, 3),
        "W_prime": round(W_prime, 3),
        "q_overburden": round(q_overburden, 2),
        "term_c": round(term_c, 2),
        "term_q": round(term_q, 2),
        "term_gamma": round(term_gamma, 2),
        "q_nu": round(q_nu, 2),
        "q_ns": round(q_ns, 2),
        "q_gross_safe": round(q_gross_safe, 2),
        "P_safe_kN": round(P_safe, 1)
    }


# ---------------------------------------------------------------------------
# Module P4: Stress Increase (Boussinesq & 2:1 Method)
# ---------------------------------------------------------------------------

def boussinesq_corner_influence(m: float, n: float) -> float:
    """
    Boussinesq influence factor I_z under the corner of a uniformly loaded rectangular area.
    SOURCE: Boussinesq (1885); Newmark (1935); Das, Principles of Foundation Engineering.
    m = B / z, n = L / z
    """
    if m <= 0 or n <= 0:
        return 0.0
    term1 = (2.0 * m * n * math.sqrt(m**2 + n**2 + 1.0)) / (m**2 + n**2 + 1.0 + (m**2) * (n**2))
    term2 = (m**2 + n**2 + 2.0) / (m**2 + n**2 + 1.0)
    denom_atan = m**2 + n**2 + 1.0 - (m**2) * (n**2)
    num_atan = 2.0 * m * n * math.sqrt(m**2 + n**2 + 1.0)

    angle = math.atan2(num_atan, denom_atan)
    if angle < 0:
        angle += math.pi

    Iz = (1.0 / (4.0 * math.pi)) * (term1 * term2 + angle)
    return Iz


def boussinesq_center_stress(delta_p: float, B: float, L: float, z: float) -> float:
    """
    Vertical stress increase below the CENTRE of a rectangle by 4-quadrant superposition.
    SOURCE: Newmark (1935); superposition of 4 corners of dimensions (B/2) x (L/2).
    """
    if z <= 0:
        return delta_p
    m = (B / 2.0) / z
    n = (L / 2.0) / z
    return 4.0 * boussinesq_corner_influence(m, n) * delta_p


def two_to_one_stress(delta_p: float, B: float, L: float, z: float) -> float:
    """
    Vertical stress increase by 2:1 dispersion method.
    SOURCE: IS 1904:1986; 2:1 load distribution method.
    """
    if z <= 0:
        return delta_p
    return delta_p * (B * L) / ((B + z) * (L + z))


# ---------------------------------------------------------------------------
# Module P5: Settlement (Schmertmann 1978 & 1-D Consolidation)
# ---------------------------------------------------------------------------

def schmertmann_settlement(profile: SoilProfile, B: float, L: float, Df: float,
                           delta_p: float, years: float = 5.0) -> Dict[str, Any]:
    """
    Computes granular layer settlement by Schmertmann et al. (1978) strain influence method.
    SOURCE: Schmertmann, Hartman & Brown (1978) ASCE GT8.
    AI AUDIT CORRECTION (Finding 3):
    Base immediate settlement S0 = S_gran / C2 is evaluated, and granular settlement at any time t
    is evaluated dynamically via Sgran(t) = S0 * [1 + 0.2*log10(max(t, 0.1)/0.1)].
    """
    ratio = max(B, L) / min(B, L) if min(B, L) > 0 else 1.0
    is_axisymmetric = (ratio < 1.5)  # Square / circle approximation
    z_max = 2.0 * B if is_axisymmetric else 4.0 * B
    z_peak = 0.5 * B if is_axisymmetric else 1.0 * B
    Iz0 = 0.1 if is_axisymmetric else 0.2

    # Initial effective overburden stress at footing base and at peak depth
    _, sig_v0_eff, _ = sigma_v_total_eff(profile, Df, profile.wt_design)
    _, sig_vp_eff, _ = sigma_v_total_eff(profile, Df + z_peak, profile.wt_design)

    # Peak strain influence factor Izp (Schmertmann et al. 1978 Eq. 2)
    Izp = 0.5 + 0.1 * math.sqrt(max(0.0, delta_p / max(1.0, sig_vp_eff)))

    # Embedment correction C1 and creep correction C2
    C1 = max(0.5, 1.0 - 0.5 * (sig_v0_eff / delta_p)) if delta_p > 0 else 1.0
    C2 = 1.0 + 0.2 * math.log10(max(years, 0.1) / 0.1)

    # Discretize influence zone into thin sublayers (dz <= 0.1 m)
    n_steps = 100
    dz = z_max / n_steps
    sum_iz_dz_es = 0.0
    granular_layers_details = []

    for i in range(n_steps):
        z_from_base = (i + 0.5) * dz
        z_depth = Df + z_from_base

        # Calculate Iz at z_from_base
        if z_from_base <= z_peak:
            Iz = Iz0 + (Izp - Iz0) * (z_from_base / z_peak)
        else:
            Iz = Izp * ((z_max - z_from_base) / (z_max - z_peak))

        layer = profile.layer_at(z_depth)
        # Apply Schmertmann only to granular layers (sand, gravel, fill)
        if layer and layer.kind in ["sand", "gravel", "fill"]:
            Es = layer.Es
            if Es <= 0:
                # Approximate Es from SPT if available: Es = 2.5 * qc = 2.5 * (400 * N) = 1000 * N (kPa)
                spt_n = 15
                if layer.spt_data:
                    spt_n = layer.spt_data[0].get("N", 15)
                Es = 2500.0 * spt_n  # kPa
            sum_iz_dz_es += (Iz / Es) * dz

    # S0 is immediate settlement (C2 = 1.0)
    S0_m = C1 * 1.0 * delta_p * sum_iz_dz_es
    S_total_mm = C1 * C2 * delta_p * sum_iz_dz_es * 1000.0
    S0_mm = S0_m * 1000.0

    return {
        "z_max": z_max, "z_peak": z_peak,
        "Izp": round(Izp, 4), "C1": round(C1, 4), "C2": round(C2, 4),
        "S0_mm": round(S0_mm, 2),  # Immediate settlement before creep
        "S_mm": round(S_total_mm, 2),  # Settlement at specified years
        "years": years
    }


def consolidation_settlement_sublayers(profile: SoilProfile, B: float, L: float,
                                       Df: float, delta_p: float,
                                       max_dz: float = 0.5) -> Dict[str, Any]:
    """
    1-D consolidation settlement for clay layers divided into sublayers <= max_dz (0.5 m).
    SOURCE: IS 1904:1986; Terzaghi 1-D consolidation theory.
    Accounts for OCR, NC, and OC response using Cc, Cr, and preconsolidation stress sigma_p.
    """
    total_Sc_mm = 0.0
    sublayer_results = []

    for L_idx, layer in enumerate(profile.layers):
        if layer.kind != "clay" or layer.Cc <= 0:
            continue

        z_top = max(Df, layer.top)
        z_bot = layer.bot
        if z_bot <= z_top:
            continue

        H_layer = z_bot - z_top
        n_subs = max(1, math.ceil(H_layer / max_dz))
        actual_dz = H_layer / n_subs

        for i in range(n_subs):
            z_mid = z_top + (i + 0.5) * actual_dz
            z_from_base = z_mid - Df

            # Initial effective stress
            _, sig_v0_eff, _ = sigma_v_total_eff(profile, z_mid, profile.wt_design)

            # Stress increase at mid of sublayer using Boussinesq under centre
            delta_sig = boussinesq_center_stress(delta_p, B, L, z_from_base)

            sig_f_eff = sig_v0_eff + delta_sig
            sig_p = layer.sigma_p if layer.sigma_p > 0 else sig_v0_eff  # Default NC if sigma_p=0
            Cr = layer.Cr if layer.Cr > 0 else 0.15 * layer.Cc
            Cc = layer.Cc
            e0 = layer.e0

            # 1-D Consolidation formula (IS 1904:1986 / Das)
            if sig_v0_eff >= sig_p:
                # Normally consolidated
                s_sub = (Cc * actual_dz / (1.0 + e0)) * math.log10(sig_f_eff / max(1e-3, sig_v0_eff))
            else:
                # Overconsolidated
                if sig_f_eff <= sig_p:
                    s_sub = (Cr * actual_dz / (1.0 + e0)) * math.log10(sig_f_eff / max(1e-3, sig_v0_eff))
                else:
                    s_sub = (Cr * actual_dz / (1.0 + e0)) * math.log10(sig_p / max(1e-3, sig_v0_eff)) + \
                            (Cc * actual_dz / (1.0 + e0)) * math.log10(sig_f_eff / sig_p)

            s_sub_mm = max(0.0, s_sub * 1000.0)
            total_Sc_mm += s_sub_mm

            sublayer_results.append({
                "layer": layer.name,
                "z_mid": round(z_mid, 2),
                "dz": round(actual_dz, 2),
                "sig_v0_eff": round(sig_v0_eff, 2),
                "delta_sig": round(delta_sig, 2),
                "sig_p": round(sig_p, 2),
                "Sc_sub_mm": round(s_sub_mm, 2)
            })

    return {
        "Sc_total_mm": round(total_Sc_mm, 2),
        "sublayers": sublayer_results
    }


def terzaghi_time_factor_curve(cv: float, H_drainage: float, drainage: str = "double",
                               t_points_years: Optional[List[float]] = None) -> List[Tuple[float, float, float]]:
    """
    Computes time-consolidation curve (t_years, Tv, U_percent) per Terzaghi 1-D consolidation theory.
    SOURCE: Terzaghi (1943); IS 1904:1986.
    """
    if t_points_years is None:
        t_points_years = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0]

    d = (H_drainage / 2.0) if drainage == "double" else H_drainage
    curve = []

    for t_yr in t_points_years:
        t_sec = t_yr * 365.25 * 86400.0
        Tv = (cv * t_sec) / (d ** 2) if d > 0 else 10.0

        # Terzaghi empirical relation between Tv and U
        if Tv < 0.2827:  # U < 60%
            U = 100.0 * math.sqrt(4.0 * Tv / math.pi)
        else:  # U >= 60%
            # Tv = 1.781 - 0.933 * log10(100 - U)
            val = (1.781 - Tv) / 0.933
            U = max(0.0, min(100.0, 100.0 - 10.0 ** val))

        curve.append((t_yr, Tv, U))

    return curve
