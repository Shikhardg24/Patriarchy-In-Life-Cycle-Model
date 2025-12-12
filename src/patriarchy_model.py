import numpy as np
from scipy.optimize import minimize

def solve_household(w_man_type, w_woman_type, gamma, w_val, ignore_constraints=False):
    """
    Solves Stage 3 with a 'Safety Net'.
    1. Tries Analytical Solution (Paper's Method).
    2. If that violates physics AND ignore_constraints is False:
       It switches to a Numerical Solver to find the 'Inner Value' (Corner Solution).
    """
    # 1. Determine Wages
    wx = w_val if w_man_type == 'H' else 1.0
    wy = w_val if w_woman_type == 'H' else 1.0

    # 2. Try Analytical Solution first (Fast & Precise for interior regions)
    res_analytical = _solve_analytical_core(wx, wy, gamma)
    
    # 3. Check Feasibility
    is_physically_possible = True
    if res_analytical['is_feasible']:
        # Check time constraints
        if (res_analytical['l_man'] + res_analytical['n_man'] > 1.0001) or \
           (res_analytical['l_woman'] + res_analytical['n_woman'] > 1.0001):
            is_physically_possible = False
    else:
        is_physically_possible = False

    # 4. DECISION LOGIC
    # If we want the Paper's numbers, we return the analytical result even if impossible.
    if ignore_constraints:
        return res_analytical

    # If we want Reality, and the analytical failed physics, we FIND THE INNER VALUE.
    if not is_physically_possible:
        return _solve_numerical_corner(wx, wy, gamma)
    
    return res_analytical

# --- INTERNAL HELPER: The Paper's Formulas ---
def _solve_analytical_core(wx, wy, gamma):
    a = wy
    b = wy * (1 - gamma) - wx
    c = -wx
    delta = b**2 - 4*a*c
    
    if delta < 0: return {'is_feasible': False, 'reason': 'Complex r'}
    r = (-b + np.sqrt(delta)) / (2 * a)
    if r <= 0: return {'is_feasible': False, 'reason': 'Negative r'}

    denom = 2 * r * wy * ((1 + r)**2 - gamma) + (1 + r) * (wx + wy * (r**2))
    if denom <= 0: return {'is_feasible': False, 'reason': 'Singularity'}

    nx = ((wx + wy) * (1 + r)) / denom
    ny = (r**2) * nx 
    v = nx * ((1 + r)**2 - gamma)
    
    if v <= 0: return {'is_feasible': False, 'reason': 'Negative Value'}

    cx = (v * r * wy) / (2 * (1 + r))
    lx = cx / wx
    ly = cx / wy
    
    return {
        'is_feasible': True,
        'U_man': cx * lx * v,
        'U_woman': cx * ly * v,
        'l_man': lx, 'n_man': nx,
        'l_woman': ly, 'n_woman': ny
    }

# --- INTERNAL HELPER: Reality (Corner Solution) ---
def _solve_numerical_corner(wx, wy, gamma):
    """
    Maximizes utility subject to strict T <= 1 constraints.
    Finds the best possible 'Inner Value'.
    """
    # Objective: Maximize Log Utility (sum of logs)
    # maximizing f is same as minimizing -f
    def objective(x):
        nx, ny, lx, ly = x
        
        # Penalties for bounds violations (soft constraints)
        if nx < 1e-6 or ny < 1e-6 or lx < 1e-6 or ly < 1e-6: return 1e11
        
        # Physics of Marriage Value
        sqrt_term = np.sqrt(nx) + np.sqrt(ny)
        v = sqrt_term**2 - gamma * nx
        if v <= 1e-6: return 1e11
        
        # Budget Constraint (Consumption)
        income = wx*(1 - lx - nx) + wy*(1 - ly - ny)
        if income <= 1e-6: return 1e11
        c = income / 2  # Equal sharing in unitary model
        
        # Utility Function: 2*ln(c) + ln(lx) + ln(ly) + 2*ln(v)
        # We assume sum of utilities U_m + U_f = Total Household U
        # U_m = ln(c) + ln(lx) + ln(v)
        # U_f = ln(c) + ln(ly) + ln(v)
        # Total = 2ln(c) + ln(lx) + ln(ly) + 2ln(v)
        
        return -(2*np.log(c) + np.log(lx) + np.log(ly) + 2*np.log(v))

    # Strict Constraints for the optimizer
    cons = (
        {'type': 'ineq', 'fun': lambda x: 1 - x[0] - x[2]}, # 1 - nx - lx >= 0
        {'type': 'ineq', 'fun': lambda x: 1 - x[1] - x[3]}  # 1 - ny - ly >= 0
    )
    
    # Initial Guess: Balanced approach
    x0 = [0.2, 0.2, 0.3, 0.3]
    bnds = [(0.01, 0.99) for _ in range(4)]
    
    res = minimize(objective, x0, method='SLSQP', bounds=bnds, constraints=cons, tol=1e-5)
    
    if not res.success:
        return {'is_feasible': False, 'reason': 'Optimization Failed'}
        
    # Reconstruct Utility in Levels
    nx, ny, lx, ly = res.x
    v = (np.sqrt(nx) + np.sqrt(ny))**2 - gamma * nx
    c = (wx*(1 - lx - nx) + wy*(1 - ly - ny)) / 2
    
    U_man = c * lx * v
    U_woman = c * ly * v
    
    return {
        'is_feasible': True,
        'U_man': U_man,
        'U_woman': U_woman,
        'l_man': lx, 'n_man': nx,
        'l_woman': ly, 'n_woman': ny,
        'note': 'Corner Solution'
    }

def get_single_utility(w_type, w_val):
    """
    Calculates utility for a single person.
    Matches Appendix A.3 comparison logic.
    Constraint: c = w(1 - l - n), v = n.
    Max U = c * l * n implies l = n = 1/3.
    """
    w = w_val if w_type == 'H' else 1.0
    
    # Optimal solution for single (Cobb-Douglas with weights 1,1,1)
    l = 1/3
    n = 1/3
    c = w * (1 - l - n) # = w/3
    v = n               # = 1/3
    
    # U = c * l * v = (w/3) * (1/3) * (1/3) = w/27
    return (w / 27.0)