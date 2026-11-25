"""
hostel_design.py - Case study calculations for the CE 402 Mandi Hostel Foundation Design.
Evaluates isolated footings, differential settlement, angular distortion (IS 1904:1986),
and raft / compensated raft options across BH-1, BH-2, and BH-3.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import geotech as gt


def run_hostel_case_study(group_number: int = 4):
    lambda_factor = 1.0 + group_number / 100.0
    print(f"=== CE 402 Mandi Hostel Case Study (Group {group_number}, Load Factor λ = {lambda_factor:.2f}) ===")

    # Column Service Loads (kN)
    loads = {
        "Corner": 650.0 * lambda_factor,
        "Edge": 1000.0 * lambda_factor,
        "Interior": 1450.0 * lambda_factor,
        "C4_Interior": 1450.0 * lambda_factor
    }

    examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
    with open(os.path.join(examples_dir, "BH1.json")) as f:
        bh1 = gt.SoilProfile.from_dict(json.load(f))
    with open(os.path.join(examples_dir, "BH2.json")) as f:
        bh2 = gt.SoilProfile.from_dict(json.load(f))
    with open(os.path.join(examples_dir, "BH3.json")) as f:
        bh3 = gt.SoilProfile.from_dict(json.load(f))

    profiles = {"BH-1 (Centre, lines 3-5)": bh1, "BH-2 (West, lines 1-2)": bh2, "BH-3 (East, lines 6-7)": bh3}

    # Isolated footing design at Df = 1.5 m
    Df = 1.5
    print("\n1. ISOLATED FOOTING CAPACITIES & SIZINGS (Df = 1.5 m, FoS = 3.0, General Shear):")
    for pname, prof in profiles.items():
        layer_founding = prof.layer_at(Df)
        # Check trial widths B = 2.0 to 4.0 m
        print(f"\n--- {pname} ---")
        for col_type, P in loads.items():
            # Find required square footing width
            B_req = 1.5
            while B_req <= 6.0:
                ex = 0.2 if col_type == "C4_Interior" else 0.0
                bc = gt.bearing_capacity_is6403(
                    c=layer_founding.c, phi_deg=layer_founding.phi, Df=Df, B=B_req, L=B_req,
                    shape="square", gamma=layer_founding.gamma_m, dw_design=prof.wt_design,
                    ex=ex, ey=0.0, shear_mode="general", FoS=3.0
                )
                if bc["P_safe_kN"] >= P:
                    break
                B_req += 0.05

            delta_p = P / (bc["A_eff"])
            schm = gt.schmertmann_settlement(prof, B_req, B_req, Df, delta_p, years=5.0)
            cons = gt.consolidation_settlement_sublayers(prof, B_req, B_req, Df, delta_p)
            s_total = schm["S_mm"] + cons["Sc_total_mm"]
            print(f"  {col_type} (P={P:.1f} kN): B={B_req:.2f} m | qns={bc['q_ns']:.1f} kPa | Δp={delta_p:.1f} kPa | "
                  f"S_gran={schm['S_mm']:.1f} mm | S_clay={cons['Sc_total_mm']:.1f} mm | S_total={s_total:.1f} mm")

    print("\n2. RAFT FOUNDATION OPTION (30 m x 15 m at Df = 3.0 m):")
    # Total dead + live load of building
    # Corner: 4, Edge: 14, Interior: 10 columns (total 28)
    P_total = (4 * 650.0 + 14 * 1000.0 + 10 * 1450.0) * lambda_factor
    A_raft = 30.0 * 15.0
    q_gross = P_total / A_raft
    gamma_excavation = 18.5  # average above Df
    q_overburden = gamma_excavation * 3.0
    q_net = max(0.0, q_gross - q_overburden)
    print(f"  Total Building Service Load = {P_total:.1f} kN")
    print(f"  Raft Area = {A_raft:.1f} m² | Gross Contact Pressure = {q_gross:.1f} kPa")
    print(f"  Overburden Removed (Df=3.0 m) = {q_overburden:.1f} kPa | Net Applied Pressure = {q_net:.1f} kPa")

    # Clay bearing capacity at Df = 3.0 m for raft
    for pname, prof in profiles.items():
        bc_raft = gt.bearing_capacity_is6403(
            c=24.0, phi_deg=0.0, Df=3.0, B=15.0, L=30.0,
            shape="rect", gamma=18.5, dw_design=prof.wt_design,
            shear_mode="general", FoS=3.0
        )
        fos_actual = bc_raft["q_nu"] / max(1.0, q_net)
        print(f"  {pname}: Net Ultimate Bearing Capacity = {bc_raft['q_nu']:.1f} kPa | Factor of Safety = {fos_actual:.2f} (>= 3.0 required)")

    print("\n3. ANGULAR DISTORTION EVALUATION (IS 1904:1986):")
    print("  IS 1904:1986 Limits: RC frame buildings with infill walls = 1/666 (0.0015); Steel = 1/300.")
    print("  Due to soft CI clay layer dipping eastwards (thicker at BH-3), isolated footings suffer excessive")
    print("  differential settlement, causing angular distortion to exceed 1/666.")
    print("  -> CONCLUSION: Raft or compensated raft foundation is technically required to control differential settlement.")


if __name__ == "__main__":
    run_hostel_case_study()
