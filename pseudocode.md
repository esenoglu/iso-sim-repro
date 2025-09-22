# Pseudocode (engine-agnostic)
- Load `params.json`; set RNG seed.
- Build Sun+planets at t0 (DE441).
- Optional physics: GR(1PN), PR(beta), Yarkovsky(A2, C_YORP).
- Inject N ISOs at Rin=1000 au with isotropic directions and v_inf samples.
- Integrate to t_end (IAS15 rtol=1e-12 or MERCURY6 hybrid dt=0.5d, eps=1e-12, rclose=3R_H).
- Classify capture/ejection; log all flags/parameters and the `seed_sim`.
