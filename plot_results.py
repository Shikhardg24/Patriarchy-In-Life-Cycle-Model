import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq
from src.education_model import calculate_expected_values

# ==========================================
# PART 1: INDIFFERENCE CURVES
# ==========================================

def simple_solve_household(w_man_type, w_woman_type, gamma, w_val, ignore_constraints):
    """
    A standalone, simplified solver specifically for plotting boundaries.
    It returns 'is_feasible=False' IMMEDIATELY if physics are violated.
    This creates the clean 'Cliff' needed for brentq to draw the line.
    """
    wx = w_val if w_man_type == 'H' else 1.0
    wy = w_val if w_woman_type == 'H' else 1.0

    # 1. Solve for r
    a = wy
    b = wy * (1 - gamma) - wx
    c = -wx
    delta = b**2 - 4*a*c
    
    if delta < 0: return {'is_feasible': False}
    r = (-b + np.sqrt(delta)) / (2 * a)

    # 2. Solve for Housework (n)
    denom = 2 * r * wy * ((1 + r)**2 - gamma) + (1 + r) * (wx + wy * (r**2))
    if denom <= 0: return {'is_feasible': False}

    nx = ((wx + wy) * (1 + r)) / denom
    ny = (r**2) * nx 
    
    # 3. Solve for Value (v)
    v = nx * ((1 + r)**2 - gamma)
    if v <= 0: return {'is_feasible': False}

    # 4. Solve for Consumption (c) and Leisure (l)
    cx = (v * r * wy) / (2 * (1 + r))
    lx = cx / wx
    ly = cx / wy
    
    # 5. STRICT FEASIBILITY CHECK (The "Cliff")
    if not ignore_constraints:
        # If time > 1, we kill the match. 
        # This forces the Utility Difference to jump to +Infinity.
        if (lx + nx > 1.0001) or (ly + ny > 1.0001):
            return {'is_feasible': False}

    return {
        'is_feasible': True,
        'U_man': cx * lx * v,
        'U_woman': cx * ly * v
    }

# ==========================================
# 2. PLOTTING LOGIC
# ==========================================

def find_indifference_point(gamma, agent_type, mode='paper'):
    ignore = True if mode == 'paper' else False
    
    # Start strictly above 1 to avoid singularity
    search_range = (1.001, 60.0) 

    def utility_diff(w):
        # 1. Baseline (Assortative)
        res_HH = simple_solve_household('H', 'H', gamma, w, ignore)
        if not res_HH['is_feasible']: return 1e9

        # 2. Mixed Match
        if agent_type == 'man':
            res_Mixed = simple_solve_household('H', 'L', gamma, w, ignore)
            if not res_Mixed['is_feasible']: return -1e9 # Impossible -> Strictly prefers HH
            return res_HH['U_man'] - res_Mixed['U_man']
            
        elif agent_type == 'woman':
            res_Mixed = simple_solve_household('L', 'H', gamma, w, ignore)
            if not res_Mixed['is_feasible']: return -1e9 # Impossible -> Strictly prefers HH
            return res_HH['U_woman'] - res_Mixed['U_woman']

    try:
        u_low = utility_diff(search_range[0])
        u_high = utility_diff(search_range[1])
        
        # Standard Crossing
        if u_low * u_high < 0:
            return brentq(utility_diff, search_range[0], search_range[1])
            
        # If no crossing:
        # For 'reality' mode, u_low is usually negative (Mixed preferred at low wage)
        # and u_high is positive (Assortative preferred at high wage).
        # If brentq didn't catch it, it might be due to the jump discontinuity.
        
        return None
    except:
        return None

def plot_indifference_curves():
    print("Generating Indifference Curves using Simple Solver...")
    gammas = np.linspace(0.0, 5.0, 50)
    
    # Helper to clean data
    def get_data(agent, mode):
        points = []
        for g in gammas:
            val = find_indifference_point(g, agent, mode)
            points.append(val)
        return points

    women_paper = get_data('woman', 'paper')
    women_reality = get_data('woman', 'reality')
    men_paper = get_data('man', 'paper')
    men_reality = get_data('man', 'reality')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # === PLOT WOMEN ===
    ax1.plot(gammas, women_paper, 'b-', linewidth=2, label="Paper (Unconstrained)")
    ax1.plot(gammas, women_reality, 'r--', linewidth=2, label="Reality (Feasible)")
    
    ax1.set_title("H-Type Women Indifference", fontsize=14)
    ax1.set_xlabel(r"Bias ($\gamma$)"); ax1.set_ylabel(r"Wage Ratio ($w$)")
    ax1.set_ylim(0, 60); ax1.legend(); ax1.grid(True, alpha=0.3)

    # Shade the gap
    clean_real = [x if x else 0 for x in women_reality]
    clean_paper = [x if x else 60 for x in women_paper]
    ax1.fill_between(gammas, clean_real, clean_paper, color='gray', alpha=0.1)
    ax1.text(2.5, 30, "IMPOSSIBLE REGION\n(L-Husband works >24h)", ha='center', color='gray')

    # === PLOT MEN ===
    ax2.plot(gammas, men_paper, 'g-', linewidth=2, label="Paper (Unconstrained)")
    ax2.plot(gammas, men_reality, 'r--', linewidth=2, label="Reality (Feasible)")
    
    ax2.set_title("H-Type Men Indifference", fontsize=14)
    ax2.set_xlabel(r"Bias ($\gamma$)"); ax2.set_ylim(0, 25)
    ax2.legend(); ax2.grid(True, alpha=0.3)
    
    # Annotations
    ax2.annotate("Paper Prediction (~11.45)", xy=(0.1, 11.45), xytext=(1.5, 15),
                 arrowprops=dict(facecolor='green', shrink=0.05))
    ax2.annotate("Reality (~1.67)", xy=(0.1, 1.67), xytext=(1.5, 5),
                 arrowprops=dict(facecolor='red', shrink=0.05))

    plt.tight_layout()
    plt.show()

# ==========================================
# PART 2: BEST RESPONSE CURVES (Equilibrium)
# ==========================================

def get_best_response(fixed_prop, fixed_agent_type, gamma, w, mode):
    """Calculates optimal proportion for Agent A given Agent B is fixed."""
    if fixed_agent_type == 'woman': # Find Men's response to fixed Women
        pf = fixed_prop
        pm = 0.5
        for _ in range(20):
            VmH, VmL, _, _ = calculate_expected_values(pm, pf, gamma, w, mode)
            pm = max(0.001, min(0.999, VmH - VmL))
        return pm
    else: # Find Women's response to fixed Men
        pm = fixed_prop
        pf = 0.5
        for _ in range(20):
            _, _, VfH, VfL = calculate_expected_values(pm, pf, gamma, w, mode)
            pf = max(0.001, min(0.999, VfH - VfL))
        return pf

def plot_best_response(gamma=1.2, w=2.0):
    print(f"Generating Best Response Curves (Gamma={gamma}, w={w})...")
    props = np.linspace(0.01, 0.99, 50)
    
    # Compare Paper vs Reality modes
    modes = ['paper', 'reality']
    colors = {'paper': 'blue', 'reality': 'red'}
    
    plt.figure(figsize=(8, 8))
    
    for mode in modes:
        c = colors[mode]
        ls = '-' if mode == 'paper' else '--'
        
        # Men's Response (y-axis) to Women (x-axis)
        men_resp = [get_best_response(p, 'woman', gamma, w, mode) for p in props]
        plt.plot(props, men_resp, color=c, linestyle=ls, label=f"Men ({mode})")
        
        # Women's Response (x-axis) to Men (y-axis)
        # Note: We plot women_resp on X-axis and props on Y-axis to visualize intersection properly
        women_resp = [get_best_response(p, 'man', gamma, w, mode) for p in props]
        plt.plot(women_resp, props, color=c, linestyle=ls, label=f"Women ({mode})")

    plt.plot([0,1], [0,1], 'k:', alpha=0.3, label="Symmetry Line")
    plt.xlabel("Prop. Educated Women ($p_f$)")
    plt.ylabel("Prop. Educated Men ($p_m$)")
    plt.title(f"Equilibrium Comparison (Gamma={gamma}, w={w})")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.show()

if __name__ == "__main__":
    # You can run either or both functions here
    plot_indifference_curves()
    # plot_best_response()