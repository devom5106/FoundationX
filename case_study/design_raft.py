import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Phase 3: raft alternative. 31 m x 16 m (0.5 m projection each side of the 30 x 15 footprint)."""
import math
from geotech import *
import site_data as sd
import design_isolated as di

PROF = di.PROF
RX0, RX1, RY0, RY1 = -0.5, 30.5, -0.5, 15.5
BR, LR = RY1 - RY0, RX1 - RX0

# total service load incl. C4 and lambda; net pressure = P/A (same basis as isolated: raft+backfill weight ~ soil removed)
Ptot = 0.0
for row in sd.ROWS:
    for line in sd.LINES:
        ct = sd.column_type(row, line)
        Ptot += (sd.C4_ASSUMED["P"] if ct == "C4" else sd.LOAD_TYPES[ct][0]) * sd.LAMBDA
q_net = Ptot / (BR * LR)
print(f"Total service load = {Ptot:.0f} kN ; raft {LR} x {BR} m ; net pressure = {q_net:.1f} kPa")

# 1) bearing capacity of raft on founding sand (IS 6403), BH-wise, B = 16 m (rectangle)
print("\nRAFT BEARING (IS 6403, FoS 3):")
for bh in PROF:
    q, info = di.qns_design(bh, BR, LR, "rect", sd.DF)
    print(f"  {bh}: qns = {q:.0f} kPa  (w_local {info['w_local']:.2f}) vs applied net {q_net:.1f}  -> FoS_actual = {3*q/q_net:.2f}")

# 2) weak clay layer under the sand: FoS on clay at its top  (net: q_ult,net = Nc cu sc ; applied = Boussinesq dsigma)
print("\nWEAK-LAYER (clay top) CHECK, applied = Boussinesq under raft centre / mid-edge of the zone:")
for bh, xs in {"BH-2": 2.5, "BH-1": 15.0, "BH-3": 28.0}.items():
    p = PROF[bh]
    clay = [L for L in p.layers if L.kind == "clay"][0]
    zb = clay.top - sd.DF
    for yy, tag in ((7.5, "mid-width"), (0.0, "edge")):
        ds = dsig_rect_point(q_net, RX0, RX1, RY0, RY1, xs, yy, zb)
        qult = 5.14 * clay.cu * (1 + 0.2 * (BR / LR))
        print(f"  {bh} x={xs:4.1f} {tag:9s}: dsig(clay top, {zb:.1f} m below base) = {ds:5.1f} kPa ; "
              f"Nc*cu*sc = {qult:5.1f} ; FoS = {qult/ds:.2f}")

# 3) settlement of flexible raft at grid points (centreline y=7.5, edge y=0) with each zone's stratigraphy
def S_point(x, y, years=5.0, force_nc=False):
    bh = sd.borehole_for(round(x / sd.GRID) + 1)
    p = PROF[bh]
    dsig = lambda z: dsig_rect_point(q_net, RX0, RX1, RY0, RY1, x, y, z - sd.DF)
    cs = consolidation(p, dsig, wt=p.wt_design, force_nc=force_nc)
    # sand: Schmertmann is for a footing of width B; for a raft use compressible founding sand only (depth to clay top)
    ss = schmertmann(p, BR, LR, sd.DF, q_net, years=years)
    return ss["S_mm"], cs["S_mm"], bh

print("\nRAFT SETTLEMENT (flexible, mm): sand + clay (OC margin 20 kPa)  /  clay if NC")
for yy, tag in ((7.5, "centreline"), (0.0, "edge A/D")):
    row = []
    for line in sd.LINES:
        x = (line - 1) * sd.GRID
        s, c, bh = S_point(x, yy)
        _, cnc, _ = S_point(x, yy, force_nc=True)
        row.append((s, c, cnc))
    print(f" {tag}: " + "  ".join(f"{a+b:5.1f}/{a+cn:5.1f}" for a, b, cn in row))
    if tag == "centreline":
        tot = [a + b for a, b, cn in row]; totnc = [a + cn for a, b, cn in row]
    else:
        tot_e = [a + b for a, b, cn in row]
for name, arr in (("OC", tot), ("NC", totnc)):
    diffs = [abs(arr[i + 1] - arr[i]) for i in range(6)]
    print(f"  centreline {name}: max S = {max(arr):.1f} mm ; max adjacent diff = {max(diffs):.1f} mm -> angular dist 1/{5000/max(diffs):.0f}")
# rigid raft estimate: area-weighted mean of centreline/edge values
import statistics
print("  (a stiff raft evens these out toward roughly the mean: "
      f"OC mean {statistics.mean(tot):.1f} mm, NC mean {statistics.mean(totnc):.1f} mm)")
