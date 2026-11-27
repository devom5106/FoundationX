# Standards verification sheet

The code and report mark these items as not yet confirmed against the standards. Open your own copies, note the clause or table, and tick whether the code matches. Fix `geotech.py` and say so if it does not.

| # | Item | Where used (`geotech.py`) | Standard / clause to check | Clause found | Matches code? | Checked by |
|---|---|---|---|---|---|---|
| 1 | N_c, N_q, N_γ values | `bc_factors` | IS 6403:1981 Table 1 | | | |
| 2 | Shape factors s_c, s_q, s_γ | `shape_factors` | IS 6403:1981 Table 2 | | | |
| 3 | Depth factors d_c, d_q, d_γ | `depth_factors` | IS 6403:1981 cl. 5.1.2.2 | | | |
| 4 | Inclination factors i_c, i_q, i_γ | `inclination_factors` | IS 6403:1981 cl. 5.1.2.3 | | | |
| 5 | Water-table factor W′ | `water_table_factor` | IS 6403:1981 cl. 5.1.2.2 | | | |
| 6 | Local shear: c* = 2c/3, tan φ* = 2 tan φ/3 | `bearing_capacity` | IS 6403 / Terzaghi and Peck | | | |
| 7 | SPT overburden correction C_N | `spt_corrections` | IS 2131:1981 chart | | | |
| 8 | SPT dilatancy correction | `spt_corrections` | IS 2131:1981 | | | |
| 9 | Total settlement limits (50 mm, 75 mm) | `check_limits` and the report | IS 1904:1986 | | | |
| 10 | Differential settlement 0.0015 L | report | IS 1904:1986 | | | |
| 11 | Angular distortion 1/666 (RC frame) | report | IS 1904:1986 | | | |
| 12 | Schmertmann I_z, C_1, C_2, E_s = 2.5 q_c | `schmertmann` | Schmertmann, Hartman and Brown (1978) | | | |

Notes on anything that did not match:
