import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Phase 3b: compensated (deeper) raft. net(Df) = P/A + w_raft - sigma_v_total(Df)
w_raft = 25 kN/m3 x 0.8 m = 20 kPa (ASSUMED raft thickness 0.8 m); basement void weight neglected (conservative)."""
import numpy as np
from geotech import *
import site_data as sd
import design_isolated as di
import design_raft as dr

PROF = di.PROF
W_RAFT = 25.0 * 0.8
P_over_A = dr.Ptot / (dr.BR * dr.LR)

def net_pressure(Df):
    sv = np.mean([sigma_v_total_eff(PROF[bh], Df)[0] for bh in PROF])
    return P_over_A + W_RAFT - sv

def station(x, y, Df, qn, force_nc=False):
    bh = sd.borehole_for(round(x / sd.GRID) + 1)
    p = PROF[bh]
    dsig = lambda z: dsig_rect_point(qn, dr.RX0, dr.RX1, dr.RY0, dr.RY1, x, y, z - Df)
    cs = consolidation(p, dsig, wt=p.wt_design, force_nc=force_nc)
    ss = schmertmann(p, dr.BR, dr.LR, Df, qn, years=5.0)
    return ss["S_mm"] + cs["S_mm"]

print(f"P/A = {P_over_A:.1f} kPa ; raft self weight {W_RAFT:.0f} kPa")
for Df in (1.5, 2.5, 3.0, 3.5, 4.0):
    qn = net_pressure(Df)
    # weak-layer FoS: clay top, mid-width, worst zone
    fos = []
    for bh, xs in {"BH-2": 2.5, "BH-1": 15.0, "BH-3": 28.0}.items():
        clay = [L for L in PROF[bh].layers if L.kind == "clay"][0]
        ds = dsig_rect_point(qn, dr.RX0, dr.RX1, dr.RY0, dr.RY1, xs, 7.5, clay.top - Df)
        fos.append(5.14 * clay.cu * (1 + 0.2 * dr.BR / dr.LR) / ds)
    res = {}
    for tag, m in (("OC", False), ("NC", True)):
        xs = [(l - 1) * sd.GRID for l in sd.LINES]
        c = np.array([station(x, 7.5, Df, qn, m) for x in xs])
        e = np.array([station(x, 0.0, Df, qn, m) for x in xs])
        mean = (c + e) / 2.0
        slope = np.polyfit(xs, mean, 1)[0]            # mm per m = rigid tilt
        resid = np.abs(mean - np.polyval(np.polyfit(xs, mean, 1), xs)).max()
        res[tag] = (mean.mean(), mean.max(), 1000.0 / slope if slope else 1e9, resid, c.max() - e.min())
    print(f"Df={Df:3.1f} m  net={qn:5.1f} kPa  weak-layer FoS min={min(fos):.2f}  "
          f"| OC: mean {res['OC'][0]:5.1f} max {res['OC'][1]:5.1f} mm, tilt 1/{abs(res['OC'][2]):.0f}, resid {res['OC'][3]:4.1f} mm "
          f"| NC: mean {res['NC'][0]:5.1f} max {res['NC'][1]:5.1f} mm, tilt 1/{abs(res['NC'][2]):.0f}, resid {res['NC'][3]:4.1f} mm")
