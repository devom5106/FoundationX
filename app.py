"""
app.py - Streamlit Interface for CE 402 Geotechnical Engineering Design Platform (FOUNDATIONX).
Compliant with IS 6403:1981, IS 2131:1981, IS 1904:1986, Schmertmann et al. (1978), and Terzaghi 1-D consolidation.
Incorporates verified corrections from AI Audit Findings 1-4.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import geotech as gt

# Page Configuration
st.set_page_config(
    page_title="FOUNDATIONX - Shallow Foundation Design Platform (CE 402)",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# House styling for matplotlib plots
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#e0e0e0'
plt.rcParams['grid.linestyle'] = '--'

# ---------------------------------------------------------------------------
# Default Starter Profile (Can be modified or replaced by any user input)
# ---------------------------------------------------------------------------
def get_default_profile() -> gt.SoilProfile:
    layers = [
        gt.Layer("Layer 1 - Fill", 0.0, 0.6, 16.5, 16.5, "fill", c=0.0, phi=26.0, Es=10000.0),
        gt.Layer("Layer 2 - Silty Sand (SM)", 0.6, 3.4, 18.0, 20.0, "sand", c=0.0, phi=30.0, Es=35000.0,
                 spt_data=[{"depth": 1.5, "N": 13}, {"depth": 3.0, "N": 16}]),
        gt.Layer("Layer 3 - Sand w/ Gravel (SP)", 3.4, 5.8, 19.0, 20.4, "sand", c=0.0, phi=34.0, Es=50000.0,
                 spt_data=[{"depth": 4.5, "N": 24}]),
        gt.Layer("Layer 4 - Silty Clay (CI)", 5.8, 10.6, 18.6, 18.6, "clay", c=28.5, phi=0.0, Es=15000.0,
                 e0=0.918, Cc=0.32, Cr=0.045, sigma_p=98.0, cv=8.9e-8,
                 spt_data=[{"depth": 6.0, "N": 6}, {"depth": 7.5, "N": 5}, {"depth": 9.0, "N": 22}, {"depth": 10.5, "N": 8}]),
        gt.Layer("Layer 5 - Sandy Gravel (GW)", 10.6, 15.0, 21.5, 21.5, "gravel", c=0.0, phi=42.0, Es=120000.0,
                 spt_data=[{"depth": 12.0, "N": 100}, {"depth": 13.5, "N": 100}])
    ]
    return gt.SoilProfile(name="Default Profile (BH-1)", layers=layers, wt_measured=2.6, wt_design=1.0)


# Initialize session state profile
if "profile" not in st.session_state:
    st.session_state.profile = get_default_profile()

# ---------------------------------------------------------------------------
# Sidebar Navigation & JSON IO
# ---------------------------------------------------------------------------
st.sidebar.title("🏗️ FOUNDATIONX")
st.sidebar.caption("CE 402 Geotechnical Engineering Design Platform")
st.sidebar.markdown("**Standards:** IS 6403:1981 · IS 2131:1981 · IS 1904:1986")

module = st.sidebar.radio(
    "Select Module:",
    ["P1 Soil Profile", "P2 Parameter Tools", "P3 Bearing Capacity", "P4 Stress Increase", "P5 Settlement"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Profile Presets & JSON")

examples_dir = os.path.join(os.path.dirname(__file__), "examples")
col_b1, col_b2, col_b3 = st.sidebar.columns(3)
if col_b1.button("BH-1"):
    p_path = os.path.join(examples_dir, "BH1.json")
    if os.path.exists(p_path):
        with open(p_path) as f:
            st.session_state.profile = gt.SoilProfile.from_dict(json.load(f))
        st.sidebar.success("Loaded BH-1")

if col_b2.button("BH-2"):
    p_path = os.path.join(examples_dir, "BH2.json")
    if os.path.exists(p_path):
        with open(p_path) as f:
            st.session_state.profile = gt.SoilProfile.from_dict(json.load(f))
        st.sidebar.success("Loaded BH-2")

if col_b3.button("BH-3"):
    p_path = os.path.join(examples_dir, "BH3.json")
    if os.path.exists(p_path):
        with open(p_path) as f:
            st.session_state.profile = gt.SoilProfile.from_dict(json.load(f))
        st.sidebar.success("Loaded BH-3")

uploaded_file = st.sidebar.file_uploader("Import Soil Profile (JSON)", type=["json"])
if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        st.session_state.profile = gt.SoilProfile.from_dict(data)
        st.sidebar.success("Uploaded profile successfully!")
    except Exception as e:
        st.sidebar.error(f"Error parsing JSON: {e}")

prof_json = json.dumps(st.session_state.profile.to_dict(), indent=2)
st.sidebar.download_button("💾 Download Profile JSON", prof_json, file_name="soil_profile.json", mime="application/json")


# ---------------------------------------------------------------------------
# MODULE P1: Soil Profile
# ---------------------------------------------------------------------------
if module == "P1 Soil Profile":
    st.header("Module P1: Soil Stratigraphy & Geostatic Stress Profile")
    st.markdown("""
    Define any layered soil profile with distinct **Measured GWT** (used for SPT overburden corrections) 
    and **Design GWT** (seasonal high, used for bearing capacity and settlement).
    """)

    prof = st.session_state.profile

    col1, col2 = st.columns(2)
    with col1:
        wt_m = st.number_input("Measured Water Table (m bgl) - at time of boring:", value=float(prof.wt_measured), step=0.1, min_value=0.0)
        prof.wt_measured = wt_m
    with col2:
        wt_d = st.number_input("Design Water Table (m bgl) - seasonal highest:", value=float(prof.wt_design), step=0.1, min_value=0.0)
        prof.wt_design = wt_d

    st.subheader("Soil Stratigraphy Table")
    table_data = []
    for L in prof.layers:
        table_data.append({
            "Layer Name": L.name,
            "Top (m)": L.top,
            "Bottom (m)": L.bot,
            "Type": L.kind,
            "γ_moist (kN/m³)": L.gamma_m,
            "γ_sat (kN/m³)": L.gamma_sat,
            "c' (kPa)": L.c,
            "φ' (deg)": L.phi,
            "Es (kPa)": L.Es,
            "e₀": L.e0,
            "Cc": L.Cc,
            "Cr": L.Cr,
            "σ'p (kPa)": L.sigma_p,
            "cv (m²/s)": L.cv
        })
    df_layers = pd.DataFrame(table_data)
    st.dataframe(df_layers, use_container_width=True)

    # Plotting Profile & Stresses
    st.subheader("Geotechnical Profile & Vertical Stress Distribution")
    max_plot_depth = st.slider("Plot Depth Range (m bgl):", min_value=float(prof.z_bot), max_value=30.0, value=20.0, step=1.0)

    # Check for extrapolation warning (AI Audit Finding 4)
    if max_plot_depth > prof.z_bot:
        st.warning(
            f"⚠️ **UI Notice (Audit Finding 4 Compliance):** Depth exceeds borehole termination depth ({prof.z_bot:.1f} m). "
            f"Total stress is extrapolated using the deepest stratum's unit weight ({prof.layers[-1].gamma_sat:.1f} kN/m³), "
            f"preventing unphysical drops in effective stress below borehole base."
        )

    z_vals = np.linspace(0.0, max_plot_depth, 200)
    sig_v_vals = []
    sig_eff_vals = []
    u_vals = []

    for z in z_vals:
        sv, sve, _ = gt.sigma_v_total_eff(prof, z, prof.wt_design)
        u = max(0.0, z - prof.wt_design) * gt.GAMMA_W
        sig_v_vals.append(sv)
        sig_eff_vals.append(sve)
        u_vals.append(u)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), sharey=True)

    # Soil Stratigraphy Graphic Log
    color_map = {"fill": "#c2b280", "sand": "#e0c068", "clay": "#8ba8d0", "gravel": "#9e9e9e"}
    for L in prof.layers:
        c = color_map.get(L.kind, "#d0d0d0")
        ax1.axhspan(L.top, L.bot, facecolor=c, alpha=0.6, edgecolor="#444444", linewidth=1.0)
        ax1.text(0.5, (L.top + L.bot) / 2.0, f"{L.name}\n({L.kind.upper()})",
                 ha="center", va="center", fontsize=9, weight="bold")

    if max_plot_depth > prof.z_bot:
        ax1.axhspan(prof.z_bot, max_plot_depth, facecolor="#f0f0f0", hatch="//", alpha=0.4, edgecolor="#888888")
        ax1.text(0.5, (prof.z_bot + max_plot_depth) / 2.0, "Extrapolated Strata\n(Deepest Layer)", ha="center", va="center", fontsize=8, style="italic")

    ax1.axhline(prof.wt_measured, color="blue", linestyle=":", linewidth=2, label=f"Measured GWT ({prof.wt_measured} m)")
    ax1.axhline(prof.wt_design, color="red", linestyle="--", linewidth=2, label=f"Design GWT ({prof.wt_design} m)")
    ax1.set_ylim(max_plot_depth, 0.0)
    ax1.set_xlim(0, 1)
    ax1.set_xticks([])
    ax1.set_ylabel("Depth below ground level (m bgl)", fontsize=11)
    ax1.set_title("Soil Stratigraphy", fontsize=12, weight="bold")
    ax1.legend(loc="lower left", fontsize=8)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # Stresses Plot
    ax2.plot(sig_v_vals, z_vals, color="#333333", linewidth=2.0, label="Total Stress σ_v (kPa)")
    ax2.plot(sig_eff_vals, z_vals, color="#2e7d32", linewidth=2.0, label="Effective Stress σ'_v (kPa)")
    ax2.plot(u_vals, z_vals, color="#1565c0", linestyle="--", linewidth=1.5, label="Pore Pressure u (kPa)")
    ax2.axhline(prof.z_bot, color="purple", linestyle=":", label=f"Borehole Base ({prof.z_bot} m)")
    ax2.set_xlabel("Stress (kPa)", fontsize=11)
    ax2.set_title("Vertical Stress Distribution (Design GWT)", fontsize=12, weight="bold")
    ax2.legend(loc="lower right", fontsize=8)
    ax2.grid(True, linestyle="--", alpha=0.5)

    st.pyplot(fig)
    plt.close()


# ---------------------------------------------------------------------------
# MODULE P2: Parameter Tools
# ---------------------------------------------------------------------------
elif module == "P2 Parameter Tools":
    st.header("Module P2: Geotechnical Parameter Tools")
    st.markdown("""
    - **IS 2131:1981 SPT Corrections:** Evaluates overburden and dilatancy corrections step by step.
    - **Direct Shear Fitting:** Fits $c'$ and $\phi'$ to normal and peak shear stress by least squares.
    """)

    tab_spt, tab_shear = st.tabs(["IS 2131:1981 SPT Corrections", "Direct Shear Analysis"])

    with tab_spt:
        st.subheader("IS 2131:1981 Standard Penetration Test Corrections")
        st.info(
            "📌 **Engineering Audit Compliance (Findings 2 & Group 4):**\n"
            "1. Overburden correction $C_N$ uses effective stress at **measured** water table (October).\n"
            "2. Closed-form formula: $C_N = 0.77 \\log_{10}(1920 / \\sigma'_v)$ capped at $C_N \\le 2.0$.\n"
            "3. For cohesive layers (`kind == 'clay'`), $C_N = 1.0$, dilatancy is bypassed, and field $N$ is retained."
        )

        prof = st.session_state.profile
        spt_rows = []
        for L in prof.layers:
            for s in L.spt_data:
                depth = s["depth"]
                N_val = s["N"]
                _, sv_eff_meas, _ = gt.sigma_v_total_eff(prof, depth, prof.wt_measured)
                is_sub = (depth >= prof.wt_measured and L.kind == "sand")
                is_clay = (L.kind == "clay")

                corr = gt.spt_corrections(N_val, sv_eff_meas, is_sub, is_clay=is_clay)
                spt_rows.append({
                    "Stratum": L.name,
                    "Depth (m)": depth,
                    "Soil Kind": L.kind.upper(),
                    "Field N": N_val,
                    "σ'_v (meas, kPa)": round(sv_eff_meas, 2),
                    "C_N": round(corr["CN"], 3),
                    "N' (Overburden)": corr["N_overburden"],
                    "Dilatancy Applied?": "Yes" if corr["applied_dilatancy"] else "No",
                    "Design N''": corr["N_design"],
                    "Standard Note": corr["note"]
                })

        df_spt = pd.DataFrame(spt_rows)
        st.dataframe(df_spt, use_container_width=True)

    with tab_shear:
        st.subheader("Mohr-Coulomb Direct Shear Fit (IS 2720 Part 13: 1986)")
        col_ds1, col_ds2 = st.columns(2)
        with col_ds1:
            st.markdown("Enter Direct Shear Test Data (Normal and Peak Shear Stresses):")
            ds_input = st.text_area(
                "Normal stress, Shear stress (one pair per line, in kPa):",
                "50, 37.0\n100, 67.0\n150, 97.2"
            )
            data_pairs = []
            for line in ds_input.strip().split("\n"):
                if "," in line:
                    parts = line.split(",")
                    try:
                        data_pairs.append((float(parts[0].strip()), float(parts[1].strip())))
                    except:
                        pass

        with col_ds2:
            if len(data_pairs) >= 2:
                sig_n = [p[0] for p in data_pairs]
                tau = [p[1] for p in data_pairs]
                c_p, phi_p, r2 = gt.fit_direct_shear(sig_n, tau)

                st.success(f"**Cohesion c':** {c_p:.2f} kPa")
                st.success(f"**Friction Angle φ':** {phi_p:.2f}°")
                st.info(f"**Coefficient of Determination R²:** {r2:.4f}")
                st.markdown(f"**Fitted Envelope:** $\\tau_f = {c_p:.2f} + \\sigma_n \\tan({phi_p:.2f}^\\circ)$")

                fig_ds, ax_ds = plt.subplots(figsize=(6, 4))
                ax_ds.scatter(sig_n, tau, color="red", zorder=5, label="Test Points (IS 2720)")
                x_fit = np.linspace(0, max(sig_n) * 1.2, 50)
                y_fit = c_p + x_fit * np.tan(np.radians(phi_p))
                ax_ds.plot(x_fit, y_fit, color="blue", linestyle="--", label=f"Fit (R²={r2:.3f})")
                ax_ds.set_xlabel("Normal Stress σ_n (kPa)")
                ax_ds.set_ylabel("Shear Stress τ (kPa)")
                ax_ds.set_title("Direct Shear Failure Envelope")
                ax_ds.set_xlim(0, max(sig_n) * 1.25)
                ax_ds.set_ylim(0, max(tau) * 1.3)
                ax_ds.legend()
                ax_ds.grid(True, linestyle="--", alpha=0.5)
                st.pyplot(fig_ds)
                plt.close()


# ---------------------------------------------------------------------------
# MODULE P3: Bearing Capacity (IS 6403:1981)
# ---------------------------------------------------------------------------
elif module == "P3 Bearing Capacity":
    st.header("Module P3: Shallow Foundation Bearing Capacity (IS 6403:1981)")
    st.markdown("""
    Calculates **net ultimate ($q_{nu}$)** and **net safe ($q_{ns}$)** bearing capacity per IS 6403:1981.
    Displays all shape, depth, and inclination factors, water-table factor $W'$, and effective area for eccentric loads.
    """)

    prof = st.session_state.profile

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("1. Footing Geometry")
        shape = st.selectbox("Footing Shape:", ["square", "rect", "strip", "circle"])
        B = st.number_input("Physical Width B (m):", value=3.0, step=0.1, min_value=0.5)
        L = st.number_input("Physical Length L (m):", value=3.0, step=0.1, min_value=0.5)
        Df = st.number_input("Founding Depth Df (m):", value=1.5, step=0.1, min_value=0.5)
        ex = st.number_input("Eccentricity in X, ex (m):", value=0.3, step=0.05, min_value=0.0)
        ey = st.number_input("Eccentricity in Y, ey (m):", value=0.0, step=0.05, min_value=0.0)

    with col2:
        st.subheader("2. Soil & Water Parameters")
        c_val = st.number_input("Cohesion c' (kPa):", value=0.0, step=1.0, min_value=0.0)
        phi_val = st.number_input("Friction Angle φ' (deg):", value=30.0, step=0.5, min_value=0.0, max_value=50.0)
        gamma_val = st.number_input("Unit Weight γ (kN/m³):", value=18.0, step=0.5, min_value=10.0)
        dw_val = st.number_input("Design GWT Depth (m bgl):", value=float(prof.wt_design), step=0.1, min_value=0.0)
        FoS = st.number_input("Factor of Safety FoS:", value=3.0, step=0.1, min_value=1.5)

    with col3:
        st.subheader("3. Shear Mode")
        shear_mode = st.radio("Shear Failure Mode:", ["general", "local", "blended"])
        spt_for_blend = None
        if shear_mode == "blended":
            spt_for_blend = st.slider("Founding Stratum SPT N:", min_value=5, max_value=35, value=20)

    # Perform Bearing Capacity Calculation
    res = gt.bearing_capacity_is6403(
        c=c_val, phi_deg=phi_val, Df=Df, B=B, L=L, shape=shape,
        gamma=gamma_val, dw_design=dw_val, ex=ex, ey=ey,
        shear_mode=shear_mode, N_spt=spt_for_blend, FoS=FoS
    )

    st.markdown("---")
    st.subheader("Bearing Capacity Results & IS 6403 Factors Breakdown")

    # Highlighting AI Audit Finding 1
    if shape == "square" and (ex > 0 or ey > 0):
        st.info(
            f"📌 **Audit Finding 1 Enforced:** Eccentric square footing transformed to effective rectangular area "
            f"($B' = {res['B_eff']:.2f}$ m, $L' = {res['L_eff']:.2f}$ m, $B'/L' = {res['B_eff']/res['L_eff']:.2f}$). "
            f"Rectangular shape factors are used ($s_q = {res['sq']:.3f}, s_\\gamma = {res['sgamma']:.3f}$) and "
            f"physical width $B = {res['B_physical']:.2f}$ m is preserved for depth factors ($d_q = d_\\gamma = {res['dq']:.3f}$)."
        )

    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    col_res1.metric("Effective Dimensions", f"{res['B_eff']} m × {res['L_eff']} m", f"A' = {res['A_eff']} m²")
    col_res2.metric("Net Ultimate (q_nu)", f"{res['q_nu']} kPa")
    col_res3.metric("Net Safe (q_ns)", f"{res['q_ns']} kPa", f"FoS = {FoS}")
    col_res4.metric("Safe Vertical Capacity", f"{res['P_safe_kN']} kN")

    # Factors Table
    factors_df = pd.DataFrame([
        {"Category": "Bearing Capacity Factors", "Nc": res["Nc"], "Nq": res["Nq"], "Nγ": res["Ngamma"]},
        {"Category": "Shape Factors (IS 6403 Table 2)", "sc": res["sc"], "sq": res["sq"], "sγ": res["sgamma"]},
        {"Category": "Depth Factors (IS 6403 Cl. 5.1.2.2)", "dc": res["dc"], "dq": res["dq"], "dγ": res["dgamma"]},
        {"Category": "Water Table & Surcharge", "W' factor": res["W_prime"], "Overburden q (kPa)": res["q_overburden"], "Gross Safe (kPa)": res["q_gross_safe"]}
    ])
    st.table(factors_df)

    st.markdown(f"""
    **Equation Components (IS 6403:1981 Cl. 5.1):**
    - Cohesion Term: $c N_c s_c d_c i_c = {res['term_c']:.2f}$ kPa
    - Surcharge Term: $q (N_q - 1) s_q d_q i_q = {res['term_q']:.2f}$ kPa
    - Self-Weight Term: $0.5 B' \\gamma N_\\gamma s_\\gamma d_\\gamma i_\\gamma W' = {res['term_gamma']:.2f}$ kPa
    - **Total Net Ultimate:** $q_{{nu}} = {res['term_c']:.2f} + {res['term_q']:.2f} + {res['term_gamma']:.2f} = \\mathbf{{{res['q_nu']:.2f}}}$ kPa
    """)


# ---------------------------------------------------------------------------
# MODULE P4: Stress Increase
# ---------------------------------------------------------------------------
elif module == "P4 Stress Increase":
    st.header("Module P4: Vertical Stress Increase in Soil Mass")
    st.markdown("""
    Calculates vertical stress increase $\\Delta \\sigma_z$ below a rectangular loaded area:
    - **Boussinesq Centre:** Evaluated by 4-quadrant superposition.
    - **Boussinesq Corner:** Evaluated from Newmark's closed form.
    - **2:1 Dispersion Method:** Simplified empirical stress spread.
    """)

    col1, col2 = st.columns(2)
    with col1:
        B_val = st.number_input("Footing Width B (m):", value=3.0, step=0.1, min_value=0.5)
        L_val = st.number_input("Footing Length L (m):", value=3.0, step=0.1, min_value=0.5)
    with col2:
        dp_val = st.number_input("Net Contact Pressure Δp (kPa):", value=200.0, step=10.0, min_value=1.0)
        z_max_p4 = st.number_input("Max Depth to Evaluate (m below footing):", value=15.0, step=1.0, min_value=2.0)

    z_depths = np.linspace(0.1, z_max_p4, 100)
    sig_b_center = [gt.boussinesq_center_stress(dp_val, B_val, L_val, z) for z in z_depths]
    sig_b_corner = [gt.boussinesq_corner_influence(B_val / z, L_val / z) * dp_val for z in z_depths]
    sig_2to1 = [gt.two_to_one_stress(dp_val, B_val, L_val, z) for z in z_depths]

    fig_p4, ax_p4 = plt.subplots(figsize=(8, 6))
    ax_p4.plot(sig_b_center, z_depths, "r-", linewidth=2.0, label="Boussinesq (Centre)")
    ax_p4.plot(sig_b_corner, z_depths, "g--", linewidth=1.8, label="Boussinesq (Corner)")
    ax_p4.plot(sig_2to1, z_depths, "b-.", linewidth=1.8, label="2:1 Method")
    ax_p4.set_ylim(z_max_p4, 0.0)
    ax_p4.set_xlabel("Vertical Stress Increase Δσ_z (kPa)", fontsize=11)
    ax_p4.set_ylabel("Depth below base of footing z (m)", fontsize=11)
    ax_p4.set_title(f"Stress Increase Distribution (B={B_val}m, L={L_val}m, Δp={dp_val} kPa)", fontsize=12, weight="bold")
    ax_p4.legend()
    ax_p4.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig_p4)
    plt.close()


# ---------------------------------------------------------------------------
# MODULE P5: Settlement
# ---------------------------------------------------------------------------
elif module == "P5 Settlement":
    st.header("Module P5: Foundation Settlement Analysis")
    st.markdown("""
    - **Granular Layers:** Schmertmann et al. (1978) Strain Influence Factor method with dynamic time creep.
    - **Cohesive Layers:** 1-D Terzaghi Consolidation using thin sublayers ($\\Delta z \\le 0.5$ m) with OCR and NC/OC handling.
    - **Time–Settlement Curve:** Time-dependent evolution combining logarithmic creep and primary consolidation.
    """)

    prof = st.session_state.profile

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("1. Footing & Load")
        B_foot = st.number_input("Footing Width B (m):", value=2.5, step=0.1, min_value=0.5)
        L_foot = st.number_input("Footing Length L (m):", value=2.5, step=0.1, min_value=0.5)
        Df_foot = st.number_input("Founding Depth Df (m):", value=1.5, step=0.1, min_value=0.5)
        dp_foot = st.number_input("Net Pressure Δp (kPa):", value=200.0, step=10.0, min_value=1.0)

    with col2:
        st.subheader("2. Time & Creep Parameters")
        years_design = st.number_input("Design Period (Years):", value=5.0, step=1.0, min_value=0.1)
        sublayer_max = st.slider("Max Clay Sublayer Thickness Δz (m):", 0.1, 0.5, 0.3, 0.05)

    with col3:
        st.subheader("3. Clay Drainage Option")
        drainage = st.radio("Consolidation Drainage:", ["double", "single"])
        cv_custom = st.number_input("cv (m²/s) [default from profile]:", value=8.9e-8, format="%.2e")

    # Run Schmertmann Settlement
    schmert_res = gt.schmertmann_settlement(prof, B_foot, L_foot, Df_foot, dp_foot, years=years_design)

    # Run 1-D Consolidation Settlement
    consol_res = gt.consolidation_settlement_sublayers(prof, B_foot, L_foot, Df_foot, dp_foot, max_dz=sublayer_max)

    total_design_settlement = schmert_res["S_mm"] + consol_res["Sc_total_mm"]

    st.markdown("---")
    st.subheader("Settlement Summary")
    c_s1, c_s2, c_s3, c_s4 = st.columns(4)
    c_s1.metric("Immediate Granular S₀", f"{schmert_res['S0_mm']} mm")
    c_s2.metric(f"Granular @ {years_design} yr (Creep C₂)", f"{schmert_res['S_mm']} mm", f"C₂ = {schmert_res['C2']:.3f}")
    c_s3.metric("Clay Primary Consolidation Sc", f"{consol_res['Sc_total_mm']} mm")
    c_s4.metric("Total Settlement (Design)", f"{total_design_settlement:.2f} mm")

    # Permissible settlement limits (IS 1904:1986)
    st.markdown("""
    **IS 1904:1986 Permissible Settlement Criteria:**
    - Isolated Footings on Clay: Permissible Total Settlement = **75 mm**; Angular Distortion Limit = **1/666** (RC framed buildings).
    - Raft Foundation on Clay: Permissible Total Settlement = **100 mm**.
    """)

    # AI Audit Finding 3 Compliance
    st.info(
        "📌 **Audit Finding 3 Compliance:** Time–settlement curve dynamically scales granular settlement with logarithmic "
        "creep $S_{gran}(t) = S_0 [1 + 0.2 \\log_{10}(\\max(t, 0.1)/0.1)]$ instead of plotting the design creep value as instantaneous."
    )

    # Clay Sublayer Breakdown Table
    with st.expander("🔍 View Clay Consolidation Sublayers Breakdown (IS 1904 Compliance)"):
        if consol_res["sublayers"]:
            df_subs = pd.DataFrame(consol_res["sublayers"])
            st.dataframe(df_subs, use_container_width=True)
        else:
            st.write("No clay layers encountered below footing depth.")

    # Time-Settlement Curve
    st.subheader("Dynamic Time–Settlement Plot (0.01 to 50 Years)")
    t_curve_years = np.logspace(-2, 1.7, 100)  # 0.01 to 50 years

    # Find clay layer thickness
    clay_thick = 4.8  # Default
    for L in prof.layers:
        if L.kind == "clay":
            clay_thick = L.thickness

    t_eval = gt.terzaghi_time_factor_curve(cv_custom, clay_thick, drainage=drainage, t_points_years=list(t_curve_years))

    t_vals = [pt[0] for pt in t_eval]
    u_vals = [pt[2] for pt in t_eval]

    s_gran_dynamic = [schmert_res["S0_mm"] * (1.0 + 0.2 * np.log10(max(t, 0.1) / 0.1)) for t in t_vals]
    s_clay_dynamic = [(u / 100.0) * consol_res["Sc_total_mm"] for u in u_vals]
    s_tot_dynamic = [g + c for g, c in zip(s_gran_dynamic, s_clay_dynamic)]

    fig_time, ax_time = plt.subplots(figsize=(10, 5))
    ax_time.plot(t_vals, s_tot_dynamic, "r-", linewidth=2.5, label="Total Settlement S_total(t)")
    ax_time.plot(t_vals, s_clay_dynamic, "b--", linewidth=1.8, label="Clay Consolidation U(t)·Sc")
    ax_time.plot(t_vals, s_gran_dynamic, "g-.", linewidth=1.8, label="Granular Settlement S_gran(t) w/ Creep")
    ax_time.set_xscale("log")
    ax_time.set_xlabel("Time (Years, Log Scale)", fontsize=11)
    ax_time.set_ylabel("Settlement (mm)", fontsize=11)
    ax_time.set_title("Time–Settlement Curve (Combining Granular Creep & Primary Consolidation)", fontsize=12, weight="bold")
    ax_time.legend(fontsize=10)
    ax_time.grid(True, which="both", linestyle="--", alpha=0.5)
    st.pyplot(fig_time)
    plt.close()
