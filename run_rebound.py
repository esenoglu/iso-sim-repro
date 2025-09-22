#!/usr/bin/env python3
import json, sys, numpy as np, csv, os, datetime, rebound
try:
    import reboundx
except Exception:
    reboundx = None

GMsun = 1.32712440018e20   # m^3 s^-2
AU    = 1.495978707e11     # m

def load_params(path):
    with open(path,'r') as f: return json.load(f)

def vinf_sample(cfg, n):
    vd = cfg["vinf_distribution"]
    if vd["type"]=="normal":
        mu = vd["mu_kms"]; sg = vd["sigma_kms"]; mn = vd["min_kms"]
        v = np.random.normal(mu, sg, n); v[v<mn]=mn
    elif vd["type"]=="fixed":
        v = np.full(n, vd["mu_kms"])
    else:
        raise ValueError("vinf_distribution")
    return v*1000.0

def random_dirs(n):
    u = np.random.rand(n)
    th = np.arccos(1-2*u); ph = 2*np.pi*np.random.rand(n)
    st, ct = np.sin(th), np.cos(th); sp, cp = np.sin(ph), np.cos(ph)
    return np.column_stack([st*cp, st*sp, ct])

def append_manifest_row(mpath, cfg, captured=None, ejected=None):
    exists = os.path.isfile(mpath)
    with open(mpath, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["timestamp","run_id","seed_sim","t0_JD_TDB","ephemeris","engine","integrator",
                        "dt_days","rtol","rclose_rule","ejection_au","t_end_years",
                        "GR_1PN","PR_beta","Yarkovsky_A2_au_d2","C_YORP",
                        "vinf_type","vinf_mu_kms","vinf_sigma_kms","vinf_min_kms",
                        "N_objects","injection_radius_au","captured","ejected","N_total"])
        w.writerow([datetime.datetime.utcnow().isoformat()+"Z",
                    cfg['run_id'], cfg['seed_sim'], cfg['epoch_t0_jd_tdb'], cfg['ephemeris'],
                    cfg['engine'], cfg['integrator'], cfg['dt_days'], cfg.get('rtol',None),
                    cfg['rclose_rule'], cfg['ejection_distance_au'], cfg['t_end_years'],
                    cfg['physics']['GR_1PN'], cfg['physics']['PR_beta'],
                    cfg['physics']['Yarkovsky_A2_au_d2'], cfg['physics']['C_YORP'],
                    cfg['vinf_distribution']['type'], cfg['vinf_distribution'].get('mu_kms',None),
                    cfg['vinf_distribution'].get('sigma_kms',None), cfg['vinf_distribution'].get('min_kms',None),
                    cfg['N_objects'], cfg['injection_radius_au'], captured, ejected, cfg['N_objects']])

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_rebound.py params.json [--manifest manifest.csv]")
        sys.exit(1)
    param_json = sys.argv[1]
    manifest = None
    if len(sys.argv) >= 4 and sys.argv[2] == "--manifest":
        manifest = sys.argv[3]

    cfg = load_params(param_json)
    np.random.seed(cfg["seed_sim"])

    sim = rebound.Simulation(); sim.units=('m','s','kg')
    Msun = GMsun/rebound.G; sim.add(m=Msun)

    # TODO: Gezegenleri DE441 epoch'unda ekleyin (placeholder: tek 'Jüpiter-benzeri')
    sim.add(m=1.898e27, a=5.2*AU, e=0.0489, inc=0.0228, Omega=1.754, omega=0.256, f=0.0)

    if cfg["physics"].get("GR_1PN", False) and reboundx is not None:
        rx = reboundx.Extras(sim); gr = rx.add("gr"); gr.params["c"]=299792458.0

    sim.integrator = cfg["integrator"].lower()
    if sim.integrator=="ias15": sim.ri_ias15.rtol = cfg.get("rtol", 1e-12)

    Rin = cfg["injection_radius_au"]*AU
    N = cfg["N_objects"]
    dirs = random_dirs(N); vinf = vinf_sample(cfg,N)

    for i in range(N):
        x,y,z = dirs[i]*Rin; vx,vy,vz = -vinf[i]*dirs[i]
        sim.add(m=0, x=float(x), y=float(y), z=float(z), vx=float(vx), vy=float(vy), vz=float(vz))

    if manifest:  # başta parametre satırı
        append_manifest_row(manifest, cfg, captured=None, ejected=None)

    sim.move_to_com()
    sim.integrate(cfg["t_end_years"]*365.25*86400.0)

    cap=ej=0
    for p in sim.particles[2:]:
        r = (p.x**2+p.y**2+p.z**2)**0.5; v2 = p.vx**2+p.vy**2+p.vz**2
        eps = 0.5*v2 - GMsun/r
        if eps<0:
            a = -GMsun/(2*eps)
            if a < cfg["ejection_distance_au"]*AU: cap+=1
        else:
            if r > cfg["ejection_distance_au"]*AU: ej+=1

    print(f"RESULT run_id={cfg['run_id']} captured={cap} ejected={ej} of N={N}")
    if manifest:
        append_manifest_row(manifest, cfg, captured=cap, ejected=ej)

if __name__=="__main__":
    main()
