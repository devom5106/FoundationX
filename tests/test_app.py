"""
test_app.py - Smoke test verifying all modules work across bundled example profiles (BH1, BH2, BH3).
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import geotech as gt


def test_example_profiles():
    examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
    files = ["BH1.json", "BH2.json", "BH3.json"]

    for fname in files:
        fpath = os.path.join(examples_dir, fname)
        assert os.path.exists(fpath), f"Missing {fpath}"
        with open(fpath) as f:
            data = json.load(f)
        prof = gt.SoilProfile.from_dict(data)

        # 1. P1 Stresses
        sig_v, sig_eff, ext = gt.sigma_v_total_eff(prof, 3.0, prof.wt_design)
        assert sig_eff > 0

        # 2. P2 SPT on first layer with SPT
        for L in prof.layers:
            for s in L.spt_data:
                _, sv_m, _ = gt.sigma_v_total_eff(prof, s["depth"], prof.wt_measured)
                corr = gt.spt_corrections(
                    s["N"], sv_m,
                    is_submerged_fine_sand=(s["depth"] >= prof.wt_measured and L.kind == "sand"),
                    is_clay=(L.kind == "clay")
                )
                assert corr["N_design"] > 0
                if L.kind == "clay":
                    assert corr["CN"] == 1.0

        # 3. P3 Bearing capacity for 2.5m square footing at Df=1.5m
        founding_layer = prof.layer_at(1.5)
        res_bc = gt.bearing_capacity_is6403(
            c=founding_layer.c, phi_deg=founding_layer.phi, Df=1.5, B=2.5, L=2.5,
            shape="square", gamma=founding_layer.gamma_m, dw_design=prof.wt_design,
            ex=0.0, ey=0.0, shear_mode="general", FoS=3.0
        )
        assert res_bc["q_ns"] > 0

        # 4. P4 Stress increase at z=2m
        ds_bouss = gt.boussinesq_center_stress(delta_p=150.0, B=2.5, L=2.5, z=2.0)
        ds_2to1 = gt.two_to_one_stress(delta_p=150.0, B=2.5, L=2.5, z=2.0)
        assert ds_bouss > 0
        assert ds_2to1 > 0

        # 5. P5 Settlement
        schmert = gt.schmertmann_settlement(prof, B=2.5, L=2.5, Df=1.5, delta_p=150.0, years=5.0)
        assert schmert["S_mm"] >= 0
        assert schmert["S0_mm"] >= 0

        consol = gt.consolidation_settlement_sublayers(prof, B=2.5, L=2.5, Df=1.5, delta_p=150.0)
        assert consol["Sc_total_mm"] >= 0

        print(f"[PASS] {fname} passed all smoke tests.")


if __name__ == "__main__":
    test_example_profiles()
    print("\nALL SMOKE TESTS PASSED!")
