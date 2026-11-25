import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Site data for the Mandi hostel (CE 402). Kept SEPARATE from geotech.py so the engine has no hard-coded site values.
All parameters below are DESIGN values derived in Phase 1 (see report), not raw logs."""
from geotech import Layer, Profile

GROUP = 4
LAMBDA = 1 + GROUP / 100.0          # brief: multiply every load by 1 + g/100
DF = 1.5                            # m, minimum founding depth (brief)

# SPT tests per borehole: (depth m, N). BH-1 9.0 m (N=22, cobble strike) REJECTED.
SPT = {
    "BH-1": [(1.5, 13), (3.0, 16), (4.5, 24), (6.0, 6), (7.5, 5), (10.5, 8)],
    "BH-2": [(1.5, 14), (3.0, 17), (4.5, 26), (6.0, 31), (7.5, 34), (9.0, 9)],
    "BH-3": [(1.5, 6), (3.0, 14), (4.5, 4), (6.0, 4), (7.5, 5), (9.0, 6), (10.5, 8)],
}

def profiles():
    gw = dict(kind="gravel", gamma=21.0, gamma_sat=21.5, phi=40.0, N=100, qc_factor=800.0)
    bh1 = Profile(name="BH-1", wt_measured=2.6, wt_design=1.0, layers=[
        Layer(0.0, 0.6, "Fill", kind="fill", gamma=16.5, gamma_sat=18.0, phi=25, N=None),
        Layer(0.6, 3.4, "SM", kind="sand", gamma=18.0, gamma_sat=20.0, c=0.0, phi=30.0, N=14.5),
        Layer(3.4, 5.8, "SP", kind="sand", gamma=19.0, gamma_sat=20.4, c=0.0, phi=34.0, N=24, qc_factor=500.0),
        Layer(5.8, 10.6, "CI", kind="clay", gamma=18.6, gamma_sat=18.6, cu=24.0, Cc=0.29, Cr=0.038,
              e0_top=0.964, e0_bot=0.809, cv=2.0, sp_add=20.0),
        Layer(10.6, 15.0, "GW", **gw)])
    bh2 = Profile(name="BH-2", wt_measured=3.2, wt_design=1.7, layers=[
        Layer(0.0, 0.5, "Fill", kind="fill", gamma=16.5, gamma_sat=18.0, phi=25),
        Layer(0.5, 3.8, "SM", kind="sand", gamma=18.2, gamma_sat=20.0, c=0.0, phi=30.0, N=15.5),
        Layer(3.8, 7.6, "SP", kind="sand", gamma=19.3, gamma_sat=20.6, c=0.0, phi=34.0, N=30, qc_factor=500.0),
        Layer(7.6, 9.6, "CI", kind="clay", gamma=18.7, gamma_sat=18.7, cu=29.5, Cc=0.288, Cr=0.038,
              e0_top=0.891, e0_bot=0.891, cv=2.0, sp_add=20.0),
        Layer(9.6, 15.0, "GW", **gw)])
    bh3 = Profile(name="BH-3", wt_measured=1.9, wt_design=0.6, layers=[
        Layer(0.0, 0.9, "Fill", kind="fill", gamma=16.0, gamma_sat=18.0, phi=25),
        Layer(0.9, 2.6, "SM-loose", kind="sand", gamma=17.5, gamma_sat=19.5, c=0.0, phi=28.0, N=6),
        Layer(2.6, 4.4, "SP", kind="sand", gamma=18.6, gamma_sat=20.0, c=0.0, phi=32.0, N=14, qc_factor=500.0),
        Layer(4.4, 11.2, "CI", kind="clay", gamma=18.5, gamma_sat=18.5, cu=20.0, Cc=0.315, Cr=0.04,
              e0_top=0.945, e0_bot=0.945, cv=2.0, sp_add=20.0),
        Layer(11.2, 15.0, "GW", **gw)])
    return {"BH-1": bh1, "BH-2": bh2, "BH-3": bh3}

# Column loads (service, before lambda), brief table. C4 is NOT in the brief's table -> ASSUMPTION below.
LOAD_TYPES = {"corner": (650.0, 0.0), "edge": (1000.0, 0.0), "interior": (1450.0, 0.0)}
C4_ASSUMED = dict(P=1450.0, M=150.0)   # ASSUMPTION: interior-type load + 150 kNm moment about the long axis

GRID = 5.0
LINES = [1, 2, 3, 4, 5, 6, 7]         # west -> east, x = (line-1)*5
ROWS = ["A", "B", "C", "D"]           # y = index*5

def column_type(row, line):
    if row == "C" and line == 4:
        return "C4"
    corner = row in ("A", "D") and line in (1, 7)
    if corner:
        return "corner"
    if row in ("A", "D") or line in (1, 7):
        return "edge"
    return "interior"

def borehole_for(line):
    return "BH-2" if line <= 2 else ("BH-1" if line <= 5 else "BH-3")
