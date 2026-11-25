"""
geotech.py - calculation engine for CE 402 foundation design platform.

Every equation carries a SOURCE comment. Units: kN, kPa, m, mm (SI) unless stated.
NO site values are hard-coded here: all soil data come in through Layer/Profile objects.

Sources (abbreviated):
  [IS6403]  IS 6403:1981 Code of practice for determination of bearing capacity of shallow foundations
  [IS1904]  IS 1904:1986 Code of practice for design and construction of foundations in soils
  [IS2131]  IS 2131:1981 Method for standard penetration test for soils
  [Das]     Das, B.M., Principles of Foundation Engineering
  [Terz]    Terzaghi, Peck & Mesri (1996), Soil Mechanics in Engineering Practice
  [Schm78]  Schmertmann, Hartman & Brown (1978), J. Geotech. Eng. Div. ASCE 104(GT8)
  [Newm]    Newmark (1935) corner formula for uniformly loaded rectangle (see Das, Boussinesq section)
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional, List, Callable

GAMMA_W = 9.81  # kN/m3, unit weight of water


# ----------------------------------------------------------------------------
# 1. Soil profile  (P1)
# ----------------------------------------------------------------------------
@dataclass
class Layer:
    top: float                 # m bgl
    bot: float                 # m bgl
    name: str = ""
    kind: str = "sand"         # 'fill' | 'sand' | 'gravel' | 'clay'
    gamma: float = 18.0        # kN/m3 moist (above WT)
    gamma_sat: float = 20.0    # kN/m3 saturated (below WT)
    c: float = 0.0             # kPa effective cohesion (granular design: usually 0)
    phi: float = 30.0          # deg effective friction angle
    cu: float = 0.0            # kPa undrained shear strength (clay)
    N: Optional[float] = None  # measured SPT N (representative)
    Cc: float = 0.0
    Cr: float = 0.0
    e0_top: float = 0.0
    e0_bot: float = 0.0
    cv: float = 0.0            # m2/year
    ocr: float = 1.0           # overconsolidation ratio at each sublayer: sigma'p = ocr*sigma'v0 + sp_add
    sp_add: float = 0.0        # kPa added to sigma'p (use when preconsolidation is a fixed margin above sigma'v0)
    E: Optional[float] = None  # kPa, user-supplied drained modulus (overrides correlation)
    qc_factor: float = 400.0   # kPa per blow: qc = qc_factor*N. ~400 for sand (Schmertmann 1970; Das Ch.3), 300-400 silty sand, 800-1000 gravelly sand


@dataclass
class Profile:
    layers: List[Layer]
    wt_measured: float         # m bgl, as measured in boring
    wt_design: float           # m bgl, design (conservative) water table
    name: str = ""

    def layer_at(self, z: float) -> Layer:
        for L in self.layers:
            if L.top <= z < L.bot:
                return L
        return self.layers[-1]


def sigma_v_total_eff(profile: Profile, z: float, wt: Optional[float] = None):
    """Total and effective vertical stress at depth z (kPa).
    SOURCE: sigma_v = sum(gamma_i h_i); u = gamma_w (z - wt); sigma' = sigma - u  [Terz, Ch.1]"""
    if wt is None:
        wt = profile.wt_design
    sig = 0.0
    for L in profile.layers:
        if z <= L.top:
            break
        z2 = min(z, L.bot)
        t = L.top
        if wt > t and wt < z2:                 # WT crosses layer
            sig += L.gamma * (wt - t) + L.gamma_sat * (z2 - wt)
        elif wt <= t:
            sig += L.gamma_sat * (z2 - t)
        else:
            sig += L.gamma * (z2 - t)
    u = max(0.0, z - wt) * GAMMA_W
    return sig, sig - u


# ----------------------------------------------------------------------------
# 2. SPT corrections (P2)  IS 2131
# ----------------------------------------------------------------------------
def spt_corrections(N: float, sigma_v_eff: float, saturated_fine_sand: bool, cn_cap: float = 2.0):
    """Returns dict with every step.
    Step 1 overburden: N' = CN * N, CN = 0.77 log10(1920/sigma'v), sigma'v in kPa, CN<=cn_cap
        SOURCE: [IS2131] cl.5.2.1 / Fig.2 gives CN as a CHART; the closed form used here is the
                Peck, Hanson & Thornburn (1974) fit quoted in [Das] Ch.3 (sigma'v in kN/m2).
                It is an APPROXIMATION of the chart - read the chart in your copy of IS 2131 to confirm.
    Step 2 dilatancy: N'' = 15 + 0.5 (N' - 15) if N' > 15 AND saturated fine/silty sand.
        SOURCE: [IS2131] dilatancy correction; Terzaghi & Peck (1948)
    """
    s = max(sigma_v_eff, 25.0)   # avoid blow-up at very low stress
    CN = min(0.77 * math.log10(1920.0 / s), cn_cap)
    N1 = CN * N
    dil_applied = bool(saturated_fine_sand and N1 > 15.0)
    N2 = 15.0 + 0.5 * (N1 - 15.0) if dil_applied else N1
    return dict(N=N, sigma_v_eff=sigma_v_eff, CN=CN, N_overburden=N1,
                dilatancy_applied=dil_applied, N_design=N2)


def phi_from_N(N1: float) -> float:
    """Cross-check only. phi = 27.1 + 0.3 N1 - 0.00054 N1^2  SOURCE: Wolff (1989), in Das Ch.3"""
    return 27.1 + 0.3 * N1 - 0.00054 * N1 ** 2


def fit_cphi(sigma_n: List[float], tau: List[float]):
    """Least-squares tau = c + sigma_n tan(phi).  SOURCE: ordinary least squares, [Das] Ch.1 (Mohr-Coulomb)."""
    n = len(sigma_n)
    sx = sum(sigma_n); sy = sum(tau)
    sxx = sum(x * x for x in sigma_n); sxy = sum(x * y for x, y in zip(sigma_n, tau))
    m = (n * sxy - sx * sy) / (n * sxx - sx ** 2)
    c = (sy - m * sx) / n
    ybar = sy / n
    ss_tot = sum((y - ybar) ** 2 for y in tau)
    ss_res = sum((y - (c + m * x)) ** 2 for x, y in zip(sigma_n, tau))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return c, math.degrees(math.atan(m)), r2


# ----------------------------------------------------------------------------
# 3. Bearing capacity (P3)  IS 6403:1981
# ----------------------------------------------------------------------------
def bc_factors(phi_deg: float):
    """Nc, Nq, Ngamma.  SOURCE: [IS6403] Table 1 / cl.5.1.2:
       Nq = exp(pi tan phi) tan^2(45+phi/2);  Nc = (Nq-1) cot phi (5.14 at phi=0);
       Ngamma = 2 (Nq+1) tan phi   (reproduces IS table: 22.4 at 30 deg, 48.03 at 35 deg)"""
    if phi_deg <= 0:
        return 5.14, 1.0, 0.0
    p = math.radians(phi_deg)
    Nq = math.exp(math.pi * math.tan(p)) * math.tan(math.radians(45 + phi_deg / 2)) ** 2
    Nc = (Nq - 1) / math.tan(p)
    Ng = 2 * (Nq + 1) * math.tan(p)
    return Nc, Nq, Ng


def shape_factors(shape: str, B: float, L: float):
    """SOURCE: [IS6403] Table 2 (as recalled: square/circle sc=1.3,sq=1.2,sg=0.8/0.6; rect per B/L).
       rect: sc = 1+0.2 B/L ; sq = 1+0.2 B/L ; sg = 1-0.4 B/L"""
    if shape == "strip":
        return 1.0, 1.0, 1.0
    if shape == "square":
        return 1.3, 1.2, 0.8
    if shape == "circle":
        return 1.3, 1.2, 0.6
    r = B / L
    return 1 + 0.2 * r, 1 + 0.2 * r, 1 - 0.4 * r


def depth_factors(phi_deg: float, Df: float, B: float):
    """SOURCE: [IS6403] cl.5.1.2.2:  dc = 1 + 0.2 (Df/B) sqrt(Nphi);
       dq = dg = 1 + 0.1 (Df/B) sqrt(Nphi) for phi > 10 deg, =1 for phi <= 10 deg;  Nphi = tan^2(45+phi/2)"""
    Nphi = math.tan(math.radians(45 + phi_deg / 2)) ** 2
    dc = 1 + 0.2 * (Df / B) * math.sqrt(Nphi)
    if phi_deg > 10:
        dq = dg = 1 + 0.1 * (Df / B) * math.sqrt(Nphi)
    else:
        dq = dg = 1.0
    return dc, dq, dg


def inclination_factors(alpha_deg: float, phi_deg: float):
    """SOURCE: [IS6403] cl.5.1.2.3: ic = iq = (1 - a/90)^2 ; ig = (1 - a/phi)^2"""
    ic = iq = (1 - alpha_deg / 90.0) ** 2
    ig = (1 - alpha_deg / phi_deg) ** 2 if phi_deg > 0 else 0.0
    return ic, iq, max(ig, 0.0)


def water_table_factor(zw: float, Df: float, B: float):
    """W'.  SOURCE: [IS6403] cl.5.1.2.2 : W' = 0.5 if WT at/above base (zw<=Df);
       W' = 1 if zw >= Df + B ; linear in between: W' = 0.5 (1 + (zw-Df)/B).
       NOTE: with W'=0.5 the gamma in the 3rd term is the BULK/SATURATED unit weight
       (do NOT also use buoyant weight - that would double count the water table).
       The surcharge q in the 2nd term is always the EFFECTIVE overburden at base."""
    if zw <= Df:
        return 0.5
    if zw >= Df + B:
        return 1.0
    return 0.5 * (1 + (zw - Df) / B)


def gamma_avg_below_base(profile: Profile, Df: float, B: float):
    """Weighted bulk unit weight within depth B below base (moist above WT, saturated below).
       SOURCE: [IS6403] cl.5.1.2.2 (gamma = weighted average of soil within failure zone)."""
    wt = profile.wt_design
    n = 40
    tot = 0.0
    for i in range(n):
        z = Df + (i + 0.5) * B / n
        L = profile.layer_at(z)
        tot += L.gamma_sat if z >= wt else L.gamma
    return tot / n


def bearing_capacity(profile: Profile, B: float, L: float, shape: str, Df: float,
                     c: float, phi: float, alpha: float = 0.0, local_shear: bool = False,
                     FoS: float = 3.0, ex: float = 0.0, ey: float = 0.0):
    """Net ultimate and net safe bearing capacity, every factor returned.
       SOURCE: [IS6403] cl.5.1.2:
       q_nu = c Nc sc dc ic + q (Nq-1) sq dq iq + 0.5 B gamma Ngamma sg dg ig W'
       q_ns = q_nu / FoS ;  q_s(gross) = q_ns + q
       Local shear: c* = 2/3 c ; tan(phi*) = 2/3 tan(phi)   [IS6403 cl.5.1.2.1; Terzaghi]
       Eccentric load: B' = B - 2 ex, L' = L - 2 ey (effective area)  [IS6403 cl.5.1.2.3 / Meyerhof]"""
    Be, Le = B - 2 * ex, L - 2 * ey
    if Be > Le:
        Be, Le = Le, Be
    cc, ph = c, phi
    if local_shear:
        cc = 2.0 / 3.0 * c
        ph = math.degrees(math.atan(2.0 / 3.0 * math.tan(math.radians(phi))))
    Nc, Nq, Ng = bc_factors(ph)
    sc, sq, sg = shape_factors(shape, Be, Le)
    dc, dq, dg = depth_factors(ph, Df, Be)
    ic, iq, ig = inclination_factors(alpha, ph)
    _, q = sigma_v_total_eff(profile, Df)          # effective overburden at base
    Wp = water_table_factor(profile.wt_design, Df, Be)
    gam = gamma_avg_below_base(profile, Df, Be)
    t1 = cc * Nc * sc * dc * ic
    t2 = q * (Nq - 1) * sq * dq * iq
    t3 = 0.5 * Be * gam * Ng * sg * dg * ig * Wp
    qnu = t1 + t2 + t3
    return dict(B_eff=Be, L_eff=Le, c_used=cc, phi_used=ph, Nc=Nc, Nq=Nq, Ng=Ng,
                sc=sc, sq=sq, sg=sg, dc=dc, dq=dq, dg=dg, ic=ic, iq=iq, ig=ig,
                W=Wp, q_overburden=q, gamma_used=gam, term_c=t1, term_q=t2, term_g=t3,
                qnu=qnu, qns=qnu / FoS, qs_gross=qnu / FoS + q, FoS=FoS)


def local_general_weight(N_design: float, N_loose: float = 10.0, N_dense: float = 30.0):
    """Weight on LOCAL shear. 1 at N<=10 (loose, Dr<~35%), 0 at N>=30, linear between.
       SOURCE: Terzaghi & Peck (loose -> local shear, dense -> general shear); IS 6403 cl.5.1.2.1 allows
       interpolation. Thresholds are an ENGINEERING JUDGEMENT, adjustable in the app."""
    if N_design <= N_loose:
        return 1.0
    if N_design >= N_dense:
        return 0.0
    return (N_dense - N_design) / (N_dense - N_loose)


# ----------------------------------------------------------------------------
# 4. Stress increase (P4)
# ----------------------------------------------------------------------------
def I_corner(m: float, n: float) -> float:
    """Influence factor at depth z below ONE CORNER of a uniform rectangle, m=B/z, n=L/z.
       SOURCE: [Newm]; [Das] Eq. (Boussinesq/Newmark). Uses atan2 so that the branch is correct when
       m^2 n^2 > m^2 + n^2 + 1 (plain atan gives a negative, wrong value there)."""
    a = m * m + n * n
    r = math.sqrt(a + 1)
    t1 = 2 * m * n * r / (a + 1 + m * m * n * n) * (a + 2) / (a + 1)
    t2 = math.atan2(2 * m * n * r, a + 1 - m * m * n * n)
    return (t1 + t2) / (4 * math.pi)


def dsig_corner(q: float, B: float, L: float, z: float) -> float:
    """Boussinesq dsigma_z below a corner. SOURCE: [Newm]/[Das]."""
    return q * I_corner(B / z, L / z)


def dsig_center(q: float, B: float, L: float, z: float) -> float:
    """Below the centre = 4 x corner of (B/2 x L/2) rectangle (superposition). SOURCE: [Das]."""
    return 4 * q * I_corner(B / 2 / z, L / 2 / z)


def dsig_2to1(q: float, B: float, L: float, z: float) -> float:
    """2:1 approximate method: dsigma = q B L / ((B+z)(L+z)). SOURCE: [Das], approximate stress spread."""
    return q * B * L / ((B + z) * (L + z))


def _cs(a: float, b: float, z: float) -> float:
    sg = (1 if a >= 0 else -1) * (1 if b >= 0 else -1)
    return sg * I_corner(abs(a) / z, abs(b) / z)


def dsig_rect_point(q: float, x1: float, x2: float, y1: float, y2: float,
                    px: float, py: float, z: float) -> float:
    """Stress at depth z under ANY point (px,py) from rectangle [x1,x2]x[y1,y2] by corner
       superposition (signed). SOURCE: [Newm] superposition principle."""
    return q * (_cs(x2 - px, y2 - py, z) - _cs(x1 - px, y2 - py, z)
                - _cs(x2 - px, y1 - py, z) + _cs(x1 - px, y1 - py, z))


# ----------------------------------------------------------------------------
# 5. Settlement (P5)
# ----------------------------------------------------------------------------
def modulus_granular(L: Layer, B: float, Lf: float):
    """Es for Schmertmann: 2.5 qc (axisymmetric) ... 3.5 qc (strip), interpolated with L/B up to 10.
       SOURCE: [Schm78] Es = 2.5 qc (square) / 3.5 qc (L/B>=10); qc = qc_factor * N (user parameter)."""
    if L.E is not None:
        return L.E
    ratio = min(max(Lf / B, 1.0), 10.0)
    fac = 2.5 + (3.5 - 2.5) * (ratio - 1) / 9.0
    return fac * L.qc_factor * (L.N if L.N else 10.0)


def schmertmann(profile: Profile, B: float, Lf: float, Df: float, q_net: float,
                years: float = 5.0, dz: float = 0.1):
    """Settlement of granular layers. SOURCE: [Schm78]
       S = C1 C2 dp  sum( Iz/Es dz )   [Schm78 Eq.1]
       C1 = 1 - 0.5 sigma'v0/dp (>=0.5) ; C2 = 1 + 0.2 log10(t/0.1), t in years
       Iz: 0.1 -> 0.5 at B/2 -> 0 at 2B (square);  0.2 -> 0.5 at B -> 0 at 4B (L/B>=10), interpolated.
       Izp = 0.5 + 0.1 sqrt(dp / sigma'vp), sigma'vp at depth of peak.
       Clay sub-layers are skipped here (handled by consolidation)."""
    r = min(max(Lf / B, 1.0), 10.0)
    f = (r - 1) / 9.0
    z_peak = B * (0.5 + 0.5 * f)
    z_max = B * (2.0 + 2.0 * f)
    Iz0 = 0.1 + 0.1 * f
    _, sv0 = sigma_v_total_eff(profile, Df)
    _, svp = sigma_v_total_eff(profile, Df + z_peak)
    dp = q_net
    Izp = 0.5 + 0.1 * math.sqrt(max(dp, 1e-9) / svp)
    C1 = max(1 - 0.5 * sv0 / dp, 0.5)
    C2 = 1 + 0.2 * math.log10(years / 0.1)
    s = 0.0
    rows = []
    n = int(z_max / dz)
    for i in range(n):
        z = (i + 0.5) * dz
        Iz = Iz0 + (Izp - Iz0) * z / z_peak if z <= z_peak else Izp * (z_max - z) / (z_max - z_peak)
        Lyr = profile.layer_at(Df + z)
        if Lyr.kind == "clay":
            continue
        E = modulus_granular(Lyr, B, Lf)
        s += Iz / E * dz
        rows.append(dict(z=z, layer=Lyr.name, Iz=Iz, E=E, strain_term=Iz / E * dz))
    S = C1 * C2 * dp * s
    return dict(S_mm=S * 1000, C1=C1, C2=C2, Izp=Izp, z_peak=z_peak, z_max=z_max, dp=dp,
                Iz0=Iz0, sigma_v0=sv0, sigma_vp=svp, rows=rows)


def consolidation(profile: Profile, dsig_fn: Callable[[float], float], sub: float = 0.5,
                  wt: Optional[float] = None, force_nc: bool = False):
    """1-D consolidation settlement of every clay layer, sublayers <= sub (0.5 m).
       NC:  S = Cc/(1+e0) H log10((s0+ds)/s0)                      [Das, Terz Ch.]
       OC, s0+ds <= sp: S = Cr/(1+e0) H log10((s0+ds)/s0)
       OC, s0+ds >  sp: S = Cr/(1+e0) H log10(sp/s0) + Cc/(1+e0) H log10((s0+ds)/sp)
       dsig_fn(z) returns stress increase at depth z (m bgl). Returns total (mm) and per-sublayer table."""
    if wt is None:
        wt = profile.wt_design
    rows = []
    tot = 0.0
    sub = min(sub, 0.5)          # brief: sublayers no thicker than 0.5 m
    for Ly in profile.layers:
        if Ly.kind != "clay":
            continue
        H = Ly.bot - Ly.top
        n = max(1, math.ceil(H / sub - 1e-9))
        h = H / n
        for i in range(n):
            z = Ly.top + (i + 0.5) * h
            e0 = Ly.e0_top + (Ly.e0_bot - Ly.e0_top) * (z - Ly.top) / H
            _, s0 = sigma_v_total_eff(profile, z, wt)
            ds = dsig_fn(z)
            sp = s0 if force_nc else max(Ly.ocr * s0 + Ly.sp_add, s0)   # sigma'p, never below sigma'v0
            if sp <= s0 * (1 + 1e-12):
                S = Ly.Cc / (1 + e0) * h * math.log10((s0 + ds) / s0)
            elif s0 + ds <= sp:
                S = Ly.Cr / (1 + e0) * h * math.log10((s0 + ds) / s0)
            else:
                S = (Ly.Cr / (1 + e0) * h * math.log10(sp / s0)
                     + Ly.Cc / (1 + e0) * h * math.log10((s0 + ds) / sp))
            tot += S
            rows.append(dict(layer=Ly.name, z=z, h=h, e0=e0, s0=s0, sp=sp, ds=ds,
                             state="NC" if sp <= s0 * (1 + 1e-12) else "OC", S_mm=S * 1000))
    return dict(S_mm=tot * 1000, rows=rows)


def Tv_from_U(U: float) -> float:
    """Time factor. SOURCE: Terzaghi 1-D consolidation, [Das]: Tv = pi/4 U^2 (U<0.6); Tv = -0.933 log10(1-U) - 0.085."""
    if U < 0.6:
        return math.pi / 4 * U ** 2
    return -0.933 * math.log10(1 - U) - 0.085


def time_settlement(S_total_mm: float, cv_m2yr: float, H_clay: float, double_drained: bool,
                    times_years: List[float]):
    """U(t) from Tv = cv t / Hdr^2, Hdr = H/2 (double) or H (single). SOURCE: Terzaghi; [Das].
       Inverse of Tv_from_U by bisection."""
    Hdr = H_clay / 2 if double_drained else H_clay
    out = []
    for t in times_years:
        Tv = cv_m2yr * t / Hdr ** 2
        lo, hi = 0.0, 0.9999
        for _ in range(60):
            mid = (lo + hi) / 2
            if Tv_from_U(mid) < Tv:
                lo = mid
            else:
                hi = mid
        U = lo if Tv < 2.0 else 1.0
        out.append((t, U, U * S_total_mm))
    return out


# ----------------------------------------------------------------------------
# 6. Serviceability check (IS 1904)
# ----------------------------------------------------------------------------
def check_limits(settlements: dict, spacing: float, max_total: float, diff_ratio: float, ang_dist: float,
                 adjacency: List[tuple]):
    """settlements: {col: mm}. adjacency: list of (colA, colB, distance m).
       differential = |S_a - S_b| <= diff_ratio * L ;  angular distortion = diff / L <= ang_dist
       SOURCE: [IS1904] Table 1 (limits are USER INPUTS; verify against your copy)."""
    worst_tot = max(settlements.values())
    worst = None
    for a, b, d in adjacency:
        diff = abs(settlements[a] - settlements[b])
        ad = diff / 1000.0 / d
        if worst is None or ad > worst["ad"]:
            worst = dict(a=a, b=b, diff_mm=diff, ad=ad, L=d)
    return dict(max_total_mm=worst_tot, ok_total=worst_tot <= max_total, worst=worst,
                ok_diff=worst["diff_mm"] <= diff_ratio * worst["L"] * 1000.0,
                ok_ad=worst["ad"] <= ang_dist)
