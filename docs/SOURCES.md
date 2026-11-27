# Sources for the equations in the code

Generated from the `SOURCE:` comments in `geotech.py`. Tags: [IS6403] IS 6403:1981; [IS2131] IS 2131:1981; [IS1904] IS 1904:1986; [Das] B. M. Das, *Principles of Foundation Engineering*; [Newm] Newmark (1935); [Schm78] Schmertmann, Hartman and Brown (1978); [Terz] Terzaghi. Items marked in the report as ‘to be confirmed’ must be checked against your own copies.

| Function | Line | Source comment |
|---|---|---|
| `(module)` | 4 | Every equation carries a SOURCE comment. Units: kN, kPa, m, mm (SI) unless stated. |
| `sigma_v_total_eff` | 66 | sigma_v = sum(gamma_i h_i); u = gamma_w (z - wt); sigma' = sigma - u  [Terz, Ch.1] |
| `spt_corrections` | 91 | [IS2131] cl.5.2.1 / Fig.2 gives CN as a CHART; the closed form used here is the |
| `spt_corrections` | 95 | [IS2131] dilatancy correction; Terzaghi & Peck (1948) |
| `phi_from_N` | 107 | Wolff (1989), in Das Ch.3 |
| `fit_cphi` | 112 | ordinary least squares, [Das] Ch.1 (Mohr-Coulomb). |
| `bc_factors` | 129 | [IS6403] Table 1 / cl.5.1.2: |
| `shape_factors` | 142 | [IS6403] Table 2 (as recalled: square/circle sc=1.3,sq=1.2,sg=0.8/0.6; rect per B/L). |
| `depth_factors` | 155 | [IS6403] cl.5.1.2.2:  dc = 1 + 0.2 (Df/B) sqrt(Nphi); |
| `inclination_factors` | 167 | [IS6403] cl.5.1.2.3: ic = iq = (1 - a/90)^2 ; ig = (1 - a/phi)^2 |
| `water_table_factor` | 174 | [IS6403] cl.5.1.2.2 : W' = 0.5 if WT at/above base (zw<=Df); |
| `gamma_avg_below_base` | 188 | [IS6403] cl.5.1.2.2 (gamma = weighted average of soil within failure zone). |
| `bearing_capacity` | 203 | [IS6403] cl.5.1.2: |
| `local_general_weight` | 234 | Terzaghi & Peck (loose -> local shear, dense -> general shear); IS 6403 cl.5.1.2.1 allows |
| `I_corner` | 248 | [Newm]; [Das] Eq. (Boussinesq/Newmark). Uses atan2 so that the branch is correct when |
| `dsig_corner` | 258 | [Newm]/[Das]. |
| `dsig_center` | 263 | [Das]. |
| `dsig_2to1` | 268 | [Das], approximate stress spread. |
| `dsig_rect_point` | 280 | [Newm] superposition principle. |
| `modulus_granular` | 290 | [Schm78] Es = 2.5 qc (square) / 3.5 qc (L/B>=10); qc = qc_factor * N (user parameter). |
| `schmertmann` | 300 | [Schm78] |
| `Tv_from_U` | 372 | Terzaghi 1-D consolidation, [Das]: Tv = pi/4 U^2 (U<0.6); Tv = -0.933 log10(1-U) - 0.085. |
| `time_settlement` | 380 | Terzaghi; [Das]. |
| `check_limits` | 405 | [IS1904] Table 1 (limits are USER INPUTS; verify against your copy). |

## Full references

1. IS 6403:1981, Code of practice for determination of bearing capacity of shallow foundations.
2. IS 2131:1981, Method for standard penetration test for soils.
3. IS 1904:1986, Code of practice for design and construction of foundations in soils: general requirements.
4. B. M. Das, *Principles of Foundation Engineering* (edition and equation numbers to be confirmed from your copy).
5. Peck, Hanson and Thornburn (1974), *Foundation Engineering*, 2nd ed.
6. Terzaghi and Peck (1967), *Soil Mechanics in Engineering Practice*.
7. Newmark (1935), Simplified computation of vertical pressures in elastic foundations.
8. Meyerhof (1953), The bearing capacity of foundations under eccentric and inclined loads.
9. Schmertmann, Hartman and Brown (1978), Improved strain influence factor diagrams, J. Geotech. Eng. Div. ASCE 104(GT8).
10. Terzaghi (1925), *Erdbaumechanik*.
11. Casagrande (1936), The determination of the pre-consolidation load.
12. Skempton (1944), Notes on the compressibility of clays; Skempton and MacDonald (1956); Bjerrum (1963).
