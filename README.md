### Shallow foundation design platform (CE 402)
A browser-based tool for shallow-foundation design in SI units (kN, kPa, m, mm). It accepts  **any**  soil profile and footing: no site value is hard-coded in app.py or geotech.py.
| Module | What it does |
| ------ | ------ |
| P1 Soil profile | Layered profile, measured and design water tables, profile plot, stress profile, JSON import/export |
| P2 Parameter tools | IS 2131 SPT corrections (overburden, dilatancy) step by step; c′ and φ′ from direct shear by least squares |
| P3 Bearing capacity | IS 6403:1981 net ultimate and net safe capacity: strip, square, rectangular, circular; general, local or blended shear; every factor shown; W′; effective area for eccentric loads |
| P4 Stress increase | Boussinesq below centre, corner and any point of a uniform rectangle (superposition); 2:1 method; Δσz–depth plot |
| P5 Settlement | Schmertmann (1978) for granular layers; 1-D consolidation (NC and OC) in sublayers ≤ 0.5 m; time–settlement with selectable drainage |

#### Run it locally
```bash
pip install -r requirements.txt
streamlit run app.py

```
Then open the address shown (normally http://localhost:8501).
#### Deploy to a public URL (Streamlit Community Cloud, free)
1. Push this folder to a public GitHub repository (the app.py file must be in the repository root).
2. Go to https://share.streamlit.io, sign in with GitHub, choose  **New app** , pick the repository, branch main, main file app.py.
3. Click  **Deploy** . The public URL appears after about a minute; put it in your report.
#### Using your own data
*  P1: edit the table, or upload a JSON file (see examples/ for the format), or download the current profile as JSON.
*  Examples in examples/ are the three boreholes of the CE 402 hostel problem. They are  **data files** , not part of the code: delete them and the platform still works.
#### Files
*  geotech.py – calculation engine. Every equation has a SOURCE: comment (code clause or textbook).
*  app.py – Streamlit interface; calls the engine only.
*  tests/test_benchmarks.py – checks against IS 6403 Table 1, published influence factors, Terzaghi time factors and an independent hand calculation.
*  tests/test_app.py – smoke test that the interface runs on the starter data and on each bundled example.
*  case_study/ – scripts that design the hostel foundations (isolated footings, raft, compensated raft). Not used by the platform.
Run the tests: python tests/test_benchmarks.py and python tests/test_app.py.
#### Method notes and limits (read before using the numbers)
*   **Water tables.**  The  *measured*  level is used for SPT corrections (stress state during the test); the  *design*  level is used for bearing capacity and settlement. Capillary rise is ignored.
*   **Net pressure.**  IS 6403 net ultimate capacity already removes the overburden q. Settlement needs the  *net*  pressure Δp = gross − overburden removed.
*   **IS 2131 overburden factor**  is the closed form of Peck, Hanson & Thornburn (1974) quoted in Das, an approximation of the chart in the standard.
*   **Local vs general shear.**  The blend between them from SPT N″ is an engineering judgement (thresholds are inputs).
*   **Schmertmann**  uses Es = 2.5–3.5 qc with qc = (qc/N)·N unless an Es is entered.
*  Code tables (IS 6403 shape and depth factors, IS 1904 limits) were checked against secondary sources; verify against your own copy of the standards.
*  Eccentric circular footings use B′ = D − 2e as an approximation.
#### Team and commits
Each member should commit their own contribution (use your own GitHub account; git log must show every member).
