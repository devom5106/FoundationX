# FoundationX --- Shallow Foundation Design Platform
CE 402 Geotechnical Engineering \| School of Civil and Environmental
Engineering, IIT Mandi \| Group 4

FoundationX is a browser-based geotechnical engineering platform for
analysing shallow foundations. It combines a Streamlit interface with a
calculation engine for soil-profile processing, SPT corrections,
bearing-capacity calculations, stress distribution and settlement
analysis.

-   Live application: https://foundationx.streamlit.app/
-   GitHub repository: https://github.com/devom5106/FoundationX

The platform uses SI units throughout: kN, kPa, m and mm. It is designed
to accept user-defined soil profiles and footing inputs rather than
relying on the Mandi hostel example data.

------------------------------------------------------------------------

## Team --- Group 4

1.  Kiran Dabaria --- B24080
2.  Devom Garg --- B24071
3.  Saransh Goyal --- B24092
4.  Ayushi Mathur --- B24066
5.  Gauri Agarwal --- B24077

------------------------------------------------------------------------

## Features and assignment modules

  -----------------------------------------------------------------------
  Module                              Functionality
  ----------------------------------- -----------------------------------
  **P1 --- Soil Profile**             Define a layered soil profile with
                                      layer depths, soil type, moist and
                                      saturated unit weights, strength,
                                      stiffness and consolidation
                                      parameters. Enter measured and
                                      design groundwater levels
                                      separately. View the soil profile
                                      and stress plots, and import/export
                                      profiles as JSON.

  **P2 --- Parameter Tools**          Apply SPT overburden and applicable
                                      dilatancy corrections with
                                      intermediate steps displayed.
                                      Estimate effective cohesion, (c'),
                                      and friction angle,
                                      (`\phi`{=tex}'), from direct-shear
                                      observations using least-squares
                                      fitting.

  **P3 --- Bearing Capacity**         Calculate net ultimate and net safe
                                      bearing capacity for strip, square,
                                      rectangular and circular footings.
                                      Includes general and local shear
                                      options, shape, depth and
                                      inclination factors, groundwater
                                      correction (W'), and effective
                                      dimensions for eccentric loading.
                                      Calculation factors are displayed.

  **P4 --- Stress Increase**          Calculate Boussinesq vertical
                                      stress increase below the centre,
                                      corner and selected points of a
                                      uniformly loaded rectangle using
                                      superposition. Includes the 2:1
                                      method and
                                      stress-increase-versus-depth plots.

  **P5 --- Settlement**               Estimate granular-soil settlement
                                      using the Schmertmann
                                      strain-influence-factor method and
                                      clay consolidation settlement for
                                      normally consolidated and
                                      overconsolidated conditions.
                                      Consolidation is evaluated in
                                      sublayers no thicker than 0.5 m,
                                      with time--settlement curves and
                                      selectable drainage conditions.
  -----------------------------------------------------------------------

### General capabilities

-   User-defined soil layers and footing geometry.
-   Separate measured and design groundwater levels.
-   Intermediate calculation steps and displayed factors.
-   JSON input and output for soil profiles.
-   SI units shown for engineering inputs and outputs.
-   Example datasets for the three boreholes in the CE 402 Mandi hostel
    assignment.

------------------------------------------------------------------------

## Technology stack

-   **Python**
-   **Streamlit** --- browser-based user interface
-   **NumPy** --- numerical calculations
-   **Pandas** --- tabular data handling
-   **Matplotlib** --- plots and visualisations

------------------------------------------------------------------------

## Repository structure

``` text
FoundationX/
├── app.py
├── geotech.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── examples/
│   ├── mandi_hostel_BH-1.json
│   ├── mandi_hostel_BH-2.json
│   └── mandi_hostel_BH-3.json
├── tests/
│   ├── test_app.py
│   └── test_benchmarks.py
└── case_study/
    ├── site_data.py
    ├── design_isolated.py
    ├── design_raft.py
    ├── design_compensated.py
    └── make_examples.py
```

### Main files

-   **`app.py`** --- Streamlit user interface and module navigation.
-   **`geotech.py`** --- reusable geotechnical calculation engine.
-   **`requirements.txt`** --- Python dependencies.
-   **`examples/`** --- sample JSON profiles corresponding to BH-1, BH-2
    and BH-3.
-   **`tests/`** --- calculation benchmark checks and application smoke
    tests.
-   **`case_study/`** --- scripts for the Mandi hostel foundation case
    study. These scripts are separate from the generic platform
    workflow.

------------------------------------------------------------------------

## Run locally

### 1. Clone the repository

``` bash
git clone https://github.com/devom5106/FoundationX.git
cd FoundationX
```

### 2. Install dependencies

``` bash
pip install -r requirements.txt
```

### 3. Launch the application

``` bash
streamlit run app.py
```

Open the local URL printed in the terminal (typically
`http://localhost:8501`).

------------------------------------------------------------------------

## Using the platform

1.  Open the [live FoundationX
    application](https://foundationx.streamlit.app/).
2.  Select the required analysis module.
3.  Enter the soil profile and footing/loading parameters, including
    units.
4.  Enter the measured groundwater level and design groundwater level
    separately wherever required.
5.  Review the calculation steps, intermediate factors, results and
    plots.
6.  In P1, use the JSON import/export controls to reuse a soil profile.
    The files in `examples/` illustrate the expected JSON structure.

The bundled Mandi borehole profiles are examples for the assignment.
They are not required to use the platform with a different site.

------------------------------------------------------------------------

## Mandi hostel case study

The repository includes a separate case study for the proposed student
hostel in Mandi, Himachal Pradesh. The site has a 30 m × 15 m footprint
on a 5 m column grid, lies in seismic Zone V, and is near a perennial
stream.

The case-study scripts examine:

-   Isolated footing sizing and settlement at the specified minimum
    founding depth.
-   A raft foundation at the minimum founding depth.
-   A compensated raft at greater founding depth.

### Design interpretation

The case-study calculations indicate that isolated footings satisfy the
bearing-capacity sizing checks but do not satisfy the adopted settlement
and differential-settlement criteria. A raft at the minimum founding
depth also has unsatisfactory checks in the underlying weak clay. The
report therefore proposes a compensated raft founded at approximately
**3.5 m**.

The report identifies the following matters as assumptions or items
requiring confirmation:

-   The assignment does not provide the C4 column load and moment; the
    case study assumes an interior-type load and an eccentric moment.
-   Clay parameters at BH-2 and BH-3 are transferred or estimated using
    BH-1 laboratory data and available index properties.
-   Some code factors and settlement limits were reproduced from
    secondary references and must be checked against the relevant
    editions of the standards.
-   The compensated-raft proposal requires construction-stage
    dewatering, waterproofing and uplift considerations. It is a
    geotechnical case-study proposal, not a complete structural raft
    design.

Refer to the group's foundation design report for the detailed
assumptions, calculations, results and limitations.

------------------------------------------------------------------------

## Tests and verification

Run the benchmark tests from the repository root:

``` bash
python tests/test_benchmarks.py
```

Run the application smoke test:

``` bash
python tests/test_app.py
```

The benchmark suite includes checks against selected bearing-capacity
factors, stress-influence values, consolidation time factors and
independent hand calculations.

A successful benchmark run is useful evidence, but it does not replace
engineering review of the equations, input assumptions, code provisions
and site-specific parameters. The application smoke test should also be
run in an environment with the dependencies installed.

------------------------------------------------------------------------

## Engineering methods and references

The implementation and case study refer to the following standards and
texts. Users should verify applicable clauses, tables and equation forms
against their own authoritative copies before using results for design.

-   **IS 6403:1981** --- Code of practice for determination of bearing
    capacity of shallow foundations.
-   **IS 2131:1981** --- Method for standard penetration test for soils.
-   **IS 1904:1986** --- Code of practice for design and construction of
    foundations in soils: general requirements.
-   Peck, Hanson and Thornburn (1974), *Foundation Engineering*, 2nd
    edition.
-   Terzaghi and Peck (1967), *Soil Mechanics in Engineering Practice*.
-   B. M. Das, *Principles of Foundation Engineering*.
-   Newmark (1935), simplified computation of vertical pressures.
-   Meyerhof (1953), bearing capacity of foundations under eccentric and
    inclined loads.
-   Schmertmann, Hartman and Brown (1978), settlement of foundations on
    sand.
-   Terzaghi, one-dimensional consolidation theory.
-   Casagrande (1936), determination of preconsolidation load.
-   Skempton (1944), correlations for compression index.
-   Skempton and MacDonald (1956), and Bjerrum (1963),
    angular-distortion and building-damage considerations.

The source list prepared by Group 4 maps equation families to their
references. The AI audit records errors found during development and the
checks/corrections made by the group.

------------------------------------------------------------------------

## Important assumptions and limitations

FoundationX is an academic engineering platform developed for the CE 402
assignment. Its outputs depend on the quality and completeness of
user-supplied soil and loading data.

-   The measured groundwater table is used for SPT corrections; the
    design groundwater table is used for design calculations such as
    bearing capacity and settlement.
-   Net bearing pressure and net settlement pressure are not
    interchangeable; use the definitions implemented for the relevant
    calculation.
-   The SPT overburden correction is an approximation based on the cited
    Peck--Hanson--Thornburn expression; it should be checked against the
    applicable IS 2131 chart and project requirements.
-   The transition/blending between local and general shear is an
    engineering modelling choice, not a substitute for engineering
    judgement.
-   Soil stiffness correlations used in granular settlement calculations
    are assumptions unless supported by site-specific test data.
-   Some IS 6403 factors and IS 1904 settlement criteria were identified
    in the project documentation as requiring confirmation against the
    original standards.
-   The eccentric circular-footing effective dimension is treated as an
    approximation.
-   The case-study transfer of clay properties to BH-2 and BH-3, and the
    assumed C4 loading, must be reviewed before any real-world use.
-   The platform does not replace a complete geotechnical investigation,
    structural foundation design, seismic/liquefaction assessment,
    construction-stage stability assessment or professional engineering
    review.

**This project is an academic assignment deliverable, not a certified
design tool for construction.**

------------------------------------------------------------------------

## Deployment

The application is deployed using Streamlit Community Cloud:

**Live app:** https://foundationx.streamlit.app/

The source code is maintained in the public GitHub repository:

**Repository:** https://github.com/devom5106/FoundationX

------------------------------------------------------------------------

## Acknowledgement

FoundationX was developed by Group 4 of Civil Engineering Batch 2024-2028, SCENE, IIT Mandi as part of the **CE
402 Geotechnical Engineering** assignment. AI tools were used during
development and review; engineering assumptions, equations, calculations
and final decisions remain the responsibility of the project team.
