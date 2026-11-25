import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import site_data as sd

COLS = ["Name", "Type", "Top (m)", "Bottom (m)", "γ moist (kN/m³)", "γ sat (kN/m³)", "c′ (kPa)", "φ′ (°)",
        "cu (kPa)", "SPT N (blows/0.3 m)", "qc/N (kPa per blow)", "E user (kPa)", "Cc (–)", "Cr (–)",
        "e0 top (–)", "e0 bottom (–)", "cv (m²/yr)", "OCR (–)", "σ′p add (kPa)"]
DS = {  # BH-1 lab sheet, soaked SM: used as the example direct-shear table
    "direct_shear": [{"σn (kPa)": 50.0, "τf (kPa)": 29.8}, {"σn (kPa)": 100.0, "τf (kPa)": 58.9},
                     {"σn (kPa)": 150.0, "τf (kPa)": 87.5}]}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples")
for bh, p in sd.profiles().items():
    layers = []
    for L in p.layers:
        layers.append(dict(zip(COLS, [L.name, L.kind, L.top, L.bot, L.gamma, L.gamma_sat, L.c, L.phi, L.cu, L.N,
                                      L.qc_factor, L.E, L.Cc, L.Cr, L.e0_top, L.e0_bot, L.cv, L.ocr, L.sp_add])))
    spt = [{"Depth (m)": z, "N (blows/0.3 m)": n,
            "Saturated fine/silty sand? (dilatancy)": bool(p.layer_at(z).kind == "sand" and z >= p.wt_measured)}
           for z, n in sd.SPT[bh]]
    d = dict(wt_measured=p.wt_measured, wt_design=p.wt_design, layers=layers, spt=spt, **DS)
    json.dump(d, open(os.path.join(out, f"mandi_hostel_{bh}.json"), "w"), indent=1, ensure_ascii=False)
    print("wrote", bh)
