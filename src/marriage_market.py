import numpy as np
from scipy.optimize import brentq
from src.patriarchy_model import solve_household, get_single_utility

def find_exact_indifference_point(gamma, agent_type, mode='paper'):
    """
    Finds wage w where U(Assortative) = U(Mixed).
    mode='paper': Uses unconstrained formulas (Replicates Figures 1 & 2).
    mode='reality': Strictly enforces time constraints.
    """
    ignore_cons = True if mode == 'paper' else False
    
    # We define the search range based on the mode
    # The paper finds roots between 10-15. Reality might push them elsewhere.
    search_range = (1.01, 60.0) 

    def utility_diff(w):
        # 1. Solve Baseline (H,H)
        res_HH = solve_household('H', 'H', gamma, w, ignore_constraints=ignore_cons)
        if not res_HH['is_feasible']: return 1e9

        # 2. Solve Mixed Match
        if agent_type == 'woman':
            # H-Woman vs L-Man
            res_mixed = solve_household('L', 'H', gamma, w, ignore_constraints=ignore_cons)
            if not res_mixed['is_feasible']: 
                return -1e9 # If strictly constrained, she prefers HH (Mixed is impossible)
            return res_HH['U_woman'] - res_mixed['U_woman']
            
        elif agent_type == 'man':
            # H-Man vs L-Woman
            res_mixed = solve_household('H', 'L', gamma, w, ignore_constraints=ignore_cons)
            if not res_mixed['is_feasible']: return -1e9
            return res_HH['U_man'] - res_mixed['U_man']

    try:
        u_low = utility_diff(search_range[0])
        u_high = utility_diff(search_range[1])
        if u_low * u_high > 0: return None
        return brentq(utility_diff, search_range[0], search_range[1])
    except:
        return None