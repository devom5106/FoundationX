import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Phase 2/3 design run: isolated footings for the Mandi hostel. Uses geotech.py + site_data.py."""
import math, json
from geotech import *
import site_data as sd

PROF = sd.profiles()
FOS = 3.0


def spt_table(bh):
    p = PROF[bh]
    rows = []
    for z, N in sd.SPT[bh]:
        L = p.layer_at(z)
        # SPT correction describes the stress state AT THE TIME OF TEST -> MEASURED water table (Oct 2026),
        # not the design (August high) water table, which is used only for bearing capacity and settlement.
        _, sv = sigma_v_total_eff(p, z, p.wt_measured)
        if L.kind == "sand":
            sat_fine = z >= p.wt_measured
            r = spt_corrections(N, sv, sat_fine)
            r["z"] = z; r["layer"] = L.name
            rows.append(r)
    return rows


def founding_N(bh, Df):
    """Mean design N'' of SPT tests in the founding sand layer at/below base."""
    p = PROF[bh]
    lay = p.layer_at(Df)
    vals = [r["N_design"] for r in spt_table(bh) if r["layer"] == lay.name and r["z"] >= Df - 0.01]
    return sum(vals) / len(vals), lay


def qns_design(bh, B, L, shape, Df, ex=0.0, ey=0.0):
    p = PROF[bh]
    Nd, lay = founding_N(bh, Df)
    w = local_general_weight(Nd)
    g = bearing_capacity(p, B, L, shape, Df, lay.c, lay.phi, FoS=FOS, ex=ex, ey=ey)
    l = bearing_capacity(p, B, L, shape, Df, lay.c, lay.phi, local_shear=True, FoS=FOS, ex=ex, ey=ey)
    q = (1 - w) * g["qns"] + w * l["qns"]
    return q, dict(N_design=Nd, w_local=w, general=g, local=l)


def size_square(bh, P, Df):
    B = 1.0
    while B < 8:
        q, info = qns_design(bh, B, B, "square", Df)
        if P / (B * B) <= q:
            return B, q, info
        B += 0.05
    return None, None, None


def size_C4(bh, P, M, Df):
    e = M / P
    best = None
    B = 1.5
    while B < 6:
        Lf = B + 0.6
        q, info = qns_design(bh, B, Lf, "rect", Df, ey=e)
        Beff, Leff = B, Lf - 2 * e
        if P / (Beff * Leff) <= q:
            return B, Lf, q, info
        B += 0.05
    return None


def build_footings():
    foot = {}
    for ri, row in enumerate(sd.ROWS):
        for line in sd.LINES:
            ct = sd.column_type(row, line)
            bh = sd.borehole_for(line)
            x, y = (line - 1) * sd.GRID, ri * sd.GRID
            if ct == "C4":
                P = sd.C4_ASSUMED["P"] * sd.LAMBDA; M = sd.C4_ASSUMED["M"] * sd.LAMBDA
                B, Lf, q, info = size_C4(bh, P, M, sd.DF)
            else:
                P = sd.LOAD_TYPES[ct][0] * sd.LAMBDA
                B, q, info = size_square(bh, P, sd.DF); Lf = B
            foot[f"{row}{line}"] = dict(x=x, y=y, B=B, L=Lf, P=P, type=ct, bh=bh, qns=q,
                                        qnet=P / (B * Lf), info=info)
    return foot


def settlement_all(foot, years=5.0, force_nc=False):
    out = {}
    for name, f in foot.items():
        p = PROF[f["bh"]]
        ss = schmertmann(p, min(f["B"], f["L"]), max(f["B"], f["L"]), sd.DF, f["qnet"], years=years)

        def dsig(z, f=f):
            zb = z - sd.DF
            tot = 0.0
            for g in foot.values():
                tot += dsig_rect_point(g["qnet"], g["x"] - g["B"] / 2, g["x"] + g["B"] / 2,
                                       g["y"] - g["L"] / 2, g["y"] + g["L"] / 2, f["x"], f["y"], zb)
            return tot
        cs = consolidation(p, dsig, wt=p.wt_design, force_nc=force_nc)
        clay = [L for L in p.layers if L.kind == "clay"][0]
        out[name] = dict(S_sand=ss["S_mm"], S_clay=cs["S_mm"], S_tot=ss["S_mm"] + cs["S_mm"],
                         dsig_top=dsig(clay.top + 0.01), clay=clay)
    return out


def adjacency():
    pairs = []
    for ri, row in enumerate(sd.ROWS):
        for line in sd.LINES:
            a = f"{row}{line}"
            if line < 7: pairs.append((a, f"{row}{line + 1}", sd.GRID))
            if ri < 3: pairs.append((a, f"{sd.ROWS[ri + 1]}{line}", sd.GRID))
    return pairs


if __name__ == "__main__":
    print(f"lambda = {sd.LAMBDA}")
    for bh in PROF:
        print(f"\n=== {bh}  design WT {PROF[bh].wt_design} m ===")
        for r in spt_table(bh):
            print(f"  z={r['z']:4.1f} {r['layer']:9s} N={r['N']:4.0f} s'v={r['sigma_v_eff']:5.1f} CN={r['CN']:.2f} "
                  f"N'={r['N_overburden']:5.1f} dil={r['dilatancy_applied']} N''={r['N_design']:5.1f}")
        Nd, lay = founding_N(bh, sd.DF)
        print(f"  founding layer {lay.name}: N_design={Nd:.1f}  w_local={local_general_weight(Nd):.2f}")
    foot = build_footings()
    print("\nFOOTING SIZES")
    seen = set()
    for n, f in foot.items():
        key = (f["bh"], f["type"])
        if key in seen: continue
        seen.add(key)
        print(f"  {f['bh']} {f['type']:8s} P={f['P']:7.1f} kN  B x L = {f['B']:.2f} x {f['L']:.2f}  qns={f['qns']:.0f} kPa  qnet={f['qnet']:.0f} kPa")
    S = settlement_all(foot)
    print("\nSETTLEMENT (mm)  [sand / clay / total]   stress at clay top (kPa)")
    for ri, row in enumerate(sd.ROWS):
        print(f" {row}: " + "  ".join(f"{S[row+str(l)]['S_tot']:5.1f}" for l in sd.LINES))
    for n in ("A1", "B2", "C4", "B5", "B6", "B7", "D7"):
        s = S[n]
        print(f"  {n}: sand {s['S_sand']:.1f} clay {s['S_clay']:.1f} tot {s['S_tot']:.1f}  dsig@clay top {s['dsig_top']:.1f}")
    tot = {n: s["S_tot"] for n, s in S.items()}
    chk = check_limits(tot, sd.GRID, 50.0, 0.0015, 1 / 666.0, adjacency())
    print("\nIS 1904 check (50 mm / 0.0015L / 1:666):", chk)
    # footing clear spacing
    print("\nlargest footing width:", max(f["B"] for f in foot.values()), " -> clear gap to neighbour =",
          sd.GRID - max(f["B"] for f in foot.values()))
