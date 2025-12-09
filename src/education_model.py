import numpy as np
from src.patriarchy_model import solve_household, get_single_utility

def calculate_expected_values(pm, pf, gamma, w, mode='paper'):
    # Determine constraint mode
    ignore = True if mode == 'paper' else False
    
    # 1. Get Utilities for all possible Matches
    # (H,H), (H,L), (L,H), (L,L)
    u_hh = solve_household('H', 'H', gamma, w, ignore)
    u_hl = solve_household('H', 'L', gamma, w, ignore)
    u_lh = solve_household('L', 'H', gamma, w, ignore)
    u_ll = solve_household('L', 'L', gamma, w, ignore)
    
    # 2. Get Utilities for being Single (The "Floor")
    u_h_single = get_single_utility('H', w)
    u_l_single = get_single_utility('L', w)

    # --- CRITICAL FIX: THE SINGLEHOOD CHECK ---
    # Agents only marry if Utility(Marriage) > Utility(Single).
    # If a match is 'Infeasible' (physically impossible), they stay Single.
    
    def get_val(res, key, u_single_fallback):
        # Case A: Match is physically impossible (Time > 24h)
        if not res['is_feasible']:
            return u_single_fallback
            
        # Case B: Match is possible, but is it better than being single?
        return max(res[key], u_single_fallback)

    # Apply the check to every scenario
    val_HH_M = get_val(u_hh, 'U_man', u_h_single)
    val_HH_F = get_val(u_hh, 'U_woman', u_h_single)
    
    val_HL_M = get_val(u_hl, 'U_man', u_h_single)
    val_HL_F = get_val(u_hl, 'U_woman', u_l_single) # Note: Wife is Low Type
    
    val_LH_M = get_val(u_lh, 'U_man', u_l_single)   # Note: Husband is Low Type
    val_LH_F = get_val(u_lh, 'U_woman', u_h_single)
    
    val_LL_M = get_val(u_ll, 'U_man', u_l_single)
    val_LL_F = get_val(u_ll, 'U_woman', u_l_single)

    # 3. Marriage Market Probabilities (Simplified Gale-Shapley)
    # This logic approximates the matching based on population scarcity
    
    # --- MEN ---
    if pm > 0:
        # If Men are abundant (pm > pf), they compete for H-Women.
        # Prob of getting H-Woman = pf / pm
        prob_hm_gets_hf = min(1.0, pf / pm)
    else:
        prob_hm_gets_hf = 0.0
    
    # V_m(H) = P(Match H)*U(Match H) + P(Match L)*U(Match L)
    V_mH = prob_hm_gets_hf * val_HH_M + (1 - prob_hm_gets_hf) * val_HL_M
    
    # L-Men Logic:
    # If pf > pm, there are surplus H-Women available for L-Men.
    if pf > pm:
        surplus_hf = pf - pm
        l_men = 1.0 - pm
        prob_lm_gets_hf = min(1.0, surplus_hf / l_men) if l_men > 0 else 0.0
    else:
        prob_lm_gets_hf = 0.0
        
    V_mL = prob_lm_gets_hf * val_LH_M + (1 - prob_lm_gets_hf) * val_LL_M


    # --- WOMEN ---
    if pf > 0:
        # If Women are abundant (pf > pm), they compete for H-Men.
        prob_hf_gets_hm = min(1.0, pm / pf)
    else:
        prob_hf_gets_hm = 0.0
        
    V_fH = prob_hf_gets_hm * val_HH_F + (1 - prob_hf_gets_hm) * val_LH_F
    
    # L-Women Logic:
    # If pm > pf, there are surplus H-Men available for L-Women.
    if pm > pf:
        surplus_hm = pm - pf
        l_women = 1.0 - pf
        prob_lf_gets_hm = min(1.0, surplus_hm / l_women) if l_women > 0 else 0.0
    else:
        prob_lf_gets_hm = 0.0
        
    V_fL = prob_lf_gets_hm * val_HL_F + (1 - prob_lf_gets_hm) * val_LL_F

    return V_mH, V_mL, V_fH, V_fL

def find_equilibrium_education(gamma, w, mode='paper', initial_guess=None):
    """
    Simulates education choices. 
    initial_guess: Tuple (pm_start, pf_start). If None, defaults to asymmetric 0.6/0.4.
    """
    # 1. Handle Initial Conditions
    if initial_guess:
        pm, pf = initial_guess
    else:
        pm, pf = 0.6, 0.4 # Default "Patriarchal Seed"
        
    history = [] 
    
    for i in range(2000):
        # Record
        history.append({'Generation': i, 'Men': pm, 'Women': pf})
        
        # Calculate Incentives
        VmH, VmL, VfH, VfL = calculate_expected_values(pm, pf, gamma, w, mode)
        
        # Update
        new_pm = max(0.001, min(0.999, VmH - VmL))
        new_pf = max(0.001, min(0.999, VfH - VfL))
        
        # Convergence Check
        if abs(new_pm - pm) < 1e-5 and abs(new_pf - pf) < 1e-5:
            # Add final state to history for cleaner plotting
            history.append({'Generation': i+1, 'Men': new_pm, 'Women': new_pf})
            return {
                'converged': True, 'pm': new_pm, 'pf': new_pf, 
                'iter': i, 'history': history
            }
            
        # Damping
        pm = 0.9 * pm + 0.1 * new_pm
        pf = 0.9 * pf + 0.1 * new_pf
        
    return {'converged': False, 'pm': pm, 'pf': pf, 'history': history}

if __name__ == "__main__":
    # Test Parameters from Paper
    gamma = 0.9
    w = 2
    
    print(f"Running Simulation (Gamma={gamma}, Wage={w})...")
    res = find_equilibrium_education(gamma, w)
    
    if res['converged']:
        print(f"Equilibrium Found in {res['iter']} iterations:")
        print(f"  Men (High Ed):   {res['pm']:.4f}")
        print(f"  Women (High Ed): {res['pf']:.4f}")
        print(f"  Difference:      {res['pm'] - res['pf']:.4f}")
    else:
        print("Simulation did not converge.")