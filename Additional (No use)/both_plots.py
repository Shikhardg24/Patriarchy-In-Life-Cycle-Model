import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

# ==========================================
# CORE SOLVER LOGIC (The "Physics Engine")
# ==========================================

def solve_household(w_man_type, w_woman_type, gamma, w_val, ignore_constraints=False):
    """
    Solves for Household Utility.
    ignore_constraints=True  -> Replicates Paper (Allows time > 1)
    ignore_constraints=False -> Replicates Reality (Enforces time <= 1)
    """
    # 1. Determine Wages
    wx = w_val if w_man_type == 'H' else 1.0
    wy = w_val if w_woman_type == 'H' else 1.0

    # 2. Calculate 'r' (Ratio of Housework)
    # Quadratic: wy*r^2 + [wy(1-gamma) - wx]*r - wx = 0
    a = wy
    b = wy * (1 - gamma) - wx
    c = -wx
    
    delta = b**2 - 4*a*c
    if delta < 0: return {'is_feasible': False} # Complex r
    
    r = (-b + np.sqrt(delta)) / (2 * a)
    if r <= 0: return {'is_feasible': False} # Negative r

    # 3. Calculate Housework (n)
    denom = 2 * r * wy * ((1 + r)**2 - gamma) + (1 + r) * (wx + wy * (r**2))
    if denom <= 0: return {'is_feasible': False} # Singularity

    nx = ((wx + wy) * (1 + r)) / denom
    ny = (r**2) * nx 
    
    # 4. Calculate Value (v)
    v = nx * ((1 + r)**2 - gamma)
    if v <= 0: return {'is_feasible': False} # Negative Value

    # 5. Calculate Consumption (c) and Leisure (l)
    cx = (v * r * wy) / (2 * (1 + r))
    lx = cx / wx
    ly = cx / wy
    
    # 6. Feasibility Check (The Switch)
    if not ignore_constraints:
        if (lx + nx > 1.0001) or (ly + ny > 1.0001):
            return {'is_feasible': False}

    # 7. Return Utility (Levels)
    return {
        'is_feasible': True,
        'U_man': cx * lx * v,
        'U_woman': cx * ly * v
    }

def find_indifference_point(gamma, agent_type, mode='paper'):
    """
    Finds wage 'w' where Agent is indifferent between H and L partners.
    """
    ignore = True if mode == 'paper' else False
    
    # Range covers both Figure 1 and Figure 2 domains
    search_range = (1.01, 60.0) 

    def utility_diff(w):
        # Baseline: Match with H-Type (Assortative)
        res_HH = solve_household('H', 'H', gamma, w, ignore_constraints=ignore)
        if not res_HH['is_feasible']: return 1e9

        # Comparison: Match with L-Type (Mixed)
        if agent_type == 'man':
            # H-Man compares HH vs HL
            res_Mixed = solve_household('H', 'L', gamma, w, ignore_constraints=ignore)
            if not res_Mixed['is_feasible']: return -1e9 # Strictly prefers HH if HL impossible
            return res_HH['U_man'] - res_Mixed['U_man']
            
        elif agent_type == 'woman':
            # H-Woman compares HH vs LH
            res_Mixed = solve_household('L', 'H', gamma, w, ignore_constraints=ignore)
            if not res_Mixed['is_feasible']: return -1e9 # Strictly prefers HH if LH impossible
            return res_HH['U_woman'] - res_Mixed['U_woman']

    try:
        # Check bounds to avoid Brentq errors
        u_low = utility_diff(search_range[0])
        u_high = utility_diff(search_range[1])
        if u_low * u_high > 0: return None
        return brentq(utility_diff, search_range[0], search_range[1])
    except:
        return None

# ==========================================
# PLOTTING LOGIC
# ==========================================

def generate_full_comparison():
    print("Simulating Equilibrium Surfaces... this may take a moment.")
    
    gammas = np.linspace(0.0, 5.0, 100)
    
    # --- Data Containers ---
    women_paper, women_reality = [], []
    men_paper, men_reality = [], []
    
    # --- Simulation Loop ---
    for g in gammas:
        # 1. H-Type Women
        women_paper.append(find_indifference_point(g, 'woman', mode='paper'))
        women_reality.append(find_indifference_point(g, 'woman', mode='reality'))
        
        # 2. H-Type Men
        men_paper.append(find_indifference_point(g, 'man', mode='paper'))
        men_reality.append(find_indifference_point(g, 'man', mode='reality'))

    # --- Plotting ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # === SUBPLOT 1: H-TYPE WOMEN ===
    ax1.plot(gammas, women_paper, 'b-', linewidth=2, label="Paper (Fig 1)")
    ax1.plot(gammas, women_reality, 'r--', linewidth=2, label="Reality (Feasible)")
    
    # Annotations for Women
    ax1.set_title("H-Type Women Indifference\n(Paper vs Reality)", fontsize=14)
    ax1.set_xlabel(r"Bias ($\gamma$)")
    ax1.set_ylabel(r"Wage Ratio ($w$)")
    ax1.set_ylim(0, 60)
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Highlight the gap
    ax1.fill_between(gammas, 
                     [x if x else 0 for x in women_reality], 
                     [x if x else 60 for x in women_paper], 
                     color='gray', alpha=0.1)
    ax1.text(2.5, 30, "IMPOSSIBLE REGION\n(L-Husband works >24h)", 
             ha='center', va='center', fontsize=10, fontweight='bold', color='gray')

    # === SUBPLOT 2: H-TYPE MEN ===
    ax2.plot(gammas, men_paper, 'g-', linewidth=2, label="Paper (Fig 2)")
    ax2.plot(gammas, men_reality, 'r--', linewidth=2, label="Reality (Feasible)")
    
    # Annotations for Men
    ax2.set_title("H-Type Men Indifference\n(Paper vs Reality)", fontsize=14)
    ax2.set_xlabel(r"Bias ($\gamma$)")
    ax2.set_ylim(0, 25) # Scale matches Fig 2
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Highlight the gap
    ax2.annotate(f"Paper: Starts at w ~ 11.45", xy=(0.1, 11.45), xytext=(1.5, 15),
                 arrowprops=dict(facecolor='black', shrink=0.05))
    ax2.annotate(f"Reality: Starts at w ~ 1.67", xy=(0.1, 1.67), xytext=(1.5, 5),
                 arrowprops=dict(facecolor='red', shrink=0.05))
    
    ax2.text(2.5, 10, "IMPOSSIBLE REGION\n(L-Wife works >24h)", 
             ha='center', va='center', fontsize=10, fontweight='bold', color='gray')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    generate_full_comparison()