import numpy as np
import matplotlib.pyplot as plt
from src.education_model import calculate_expected_values

def get_best_response(fixed_prop, fixed_agent_type, gamma, w, mode='paper'):
    """
    Calculates the optimal proportion for Agent A given Agent B is fixed.
    """
    # If we are finding Men's response to Women (fixed_pf):
    if fixed_agent_type == 'woman':
        pf = fixed_prop
        # We need to find the pm that satisfies pm = Benefit(pm | pf)
        # Since Benefit depends on pm (via marriage probabilities), this is a mini-fixed-point.
        # However, for a given pf, VmH and VmL are usually monotonic in pm.
        
        # Simple approach: Iterate to find consistent response
        pm_response = 0.5
        for _ in range(20):
            VmH, VmL, _, _ = calculate_expected_values(pm_response, pf, gamma, w, mode)
            benefit = VmH - VmL
            pm_response = max(0.001, min(0.999, benefit))
        return pm_response

    # If we are finding Women's response to Men (fixed_pm):
    elif fixed_agent_type == 'man':
        pm = fixed_prop
        pf_response = 0.5
        for _ in range(20):
            _, _, VfH, VfL = calculate_expected_values(pm, pf_response, gamma, w, mode)
            benefit = VfH - VfL
            pf_response = max(0.001, min(0.999, benefit))
        return pf_response

def plot_reaction_functions():
    # Parameters (Region II/III)
    gamma = 1.2
    w = 2
    mode = 'reality' # 'paper' or 'reality'

    print(f"Generating Best Response Curves (Gamma={gamma}, w={w}, Mode={mode})...")

    grid_size = 500
    proportions = np.linspace(0.01, 0.99, grid_size)
    
    # 1. Men's Reaction Function (Response to Women)
    # x-axis: Women's Prop (pf), y-axis: Men's Optimal (pm)
    men_response_curve = []
    for pf in proportions:
        best_pm = get_best_response(pf, 'woman', gamma, w, mode)
        men_response_curve.append(best_pm)

    # 2. Women's Reaction Function (Response to Men)
    # x-axis: Men's Prop (pm), y-axis: Women's Optimal (pf)
    # NOTE: For plotting intersection, we usually plot pf on x and pm on y.
    # So we want: Given pm, what is pf?
    women_response_curve = []
    for pm in proportions:
        best_pf = get_best_response(pm, 'man', gamma, w, mode)
        women_response_curve.append(best_pf)

    # --- PLOTTING ---
    plt.figure(figsize=(8, 8))
    
    # Plot Men's Best Response (PM vs PF)
    # X = PF (Women), Y = PM (Men)
    plt.plot(proportions, men_response_curve, 'b-', linewidth=2, label="Men's Best Response to Women")
    
    # Plot Women's Best Response (PM vs PF)
    # The 'women_response_curve' is PF given PM. 
    # To plot on the same axes (X=PF, Y=PM), we flip the axes.
    # X = Best PF, Y = Fixed PM
    plt.plot(women_response_curve, proportions, 'r-', linewidth=2, label="Women's Best Response to Men")

    # Add 45-degree line (Symmetry reference)
    plt.plot([0,1], [0,1], 'k:', alpha=0.3, label="Symmetry Line")

    # Labels
    plt.xlabel("Proportion of Educated Women ($p_f$)")
    plt.ylabel("Proportion of Educated Men ($p_m$)")
    plt.title(f"Equilibrium: Intersection of Best Responses\n($\gamma={gamma}, w={w}, mode ={mode}$)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    
    # Annotate Intersection
    # (Visual estimation or numerical intersection finding can be added)
    plt.show()

if __name__ == "__main__":
    plot_reaction_functions()
    