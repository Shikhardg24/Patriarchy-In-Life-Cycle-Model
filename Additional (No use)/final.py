from src.education_model import find_equilibrium_education

def run_final_verdict():
    # Parameters from Region II of the paper
    gamma = 0.8
    w = 3.0
    
    print(f"--- FINAL VERDICT (Gamma={gamma}, Wage={w}) ---\n")
    
    # 1. The Paper's Theoretical World
    print("Running Simulation in PAPER MODE (Unconstrained)...")
    res_paper = find_equilibrium_education(gamma, w, mode='paper')
    
    if res_paper['converged']:
        pm_p = res_paper['pm']
        pf_p = res_paper['pf']
        gap_p = pm_p - pf_p
        print(f"  [Paper Result] Men: {pm_p:.3f}, Women: {pf_p:.3f}")
        print(f"  [Paper Gap]    {gap_p*100:.1f}% more men educated.")
    else:
        print("  [Paper Result] Did not converge.")

    print("-" * 30)

    # 2. The Physically Valid World
    print("Running Simulation in REALITY MODE (Constrained)...")
    res_real = find_equilibrium_education(gamma, w, mode='reality')
    
    if res_real['converged']:
        pm_r = res_real['pm']
        pf_r = res_real['pf']
        gap_r = pm_r - pf_r
        print(f"  [Reality Result] Men: {pm_r:.3f}, Women: {pf_r:.3f}")
        print(f"  [Reality Gap]    {gap_r*100:.1f}% more men educated.")
    else:
        print("  [Reality Result] Did not converge (likely due to infeasible matches).")

if __name__ == "__main__":
    run_final_verdict()