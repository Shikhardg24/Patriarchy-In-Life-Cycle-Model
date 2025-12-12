import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Import logic modules
from src.patriarchy_model import solve_household
from src.education_model import find_equilibrium_education
from plot_results import find_indifference_point, get_best_response

# --- PAGE CONFIG ---
st.set_page_config(page_title="Patriarchy Model Verification", layout="wide", page_icon="🔬")

# --- CUSTOM CSS ---
st.markdown("""
<style>
div[data-testid="stMetricValue"] { font-size: 1.0rem; }
div[data-testid="stMarkdownContainer"] p { font-size: 0.95rem; }
.small-font { font-size: 0.85rem; color: gray; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🔬 Control Panel")
mode_selection = st.sidebar.radio("Simulation Logic:", ("Paper Mode (Unconstrained)", "Reality Mode (Physically Valid)"))
MODE = 'paper' if "Paper" in mode_selection else 'reality'
st.sidebar.markdown("---")
gamma_input = st.sidebar.slider("Bias Parameter (γ)", 0.0, 5.0, 0.5, 0.05)
w_input = st.sidebar.slider("Wage Ratio (w)", 1.0, 25.0, 5.0, 0.25)

# --- MAIN HEADER ---
st.title(f"Research Verification: {mode_selection}")
st.markdown(f"Currently simulating: **{MODE.upper()}** logic.")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🏠 Marriage Market Analysis", "🎓 Education Equilibrium", "📈 Best Response Function Graph"])

# ==========================================
# TAB 1: ALL 4 HOUSEHOLDS
# ==========================================
with tab1:
    st.subheader(f"Marriage Market Matrix (γ={gamma_input}, w={w_input})")
    
    # 1. SOLVE ALL 4 CASES
    ignore = (MODE == 'paper')
    res_HH = solve_household('H', 'H', gamma_input, w_input, ignore)
    res_HL = solve_household('H', 'L', gamma_input, w_input, ignore) # H-Man, L-Woman
    res_LH = solve_household('L', 'H', gamma_input, w_input, ignore) # L-Man, H-Woman
    res_LL = solve_household('L', 'L', gamma_input, w_input, ignore)

    # Helper to extract utility
    def get_u(res, agent): 
        if not res['is_feasible']: return -999.0
        return res[f'U_{agent}']

    # 2. PREFERENCE ANALYSIS
    u_hm_hh, u_hm_hl = get_u(res_HH, 'man'), get_u(res_HL, 'man')
    pref_hm = "Assortative (H-Woman)" if u_hm_hh >= u_hm_hl else "Marrying Down (L-Woman)"
    
    u_hf_hh, u_hf_lh = get_u(res_HH, 'woman'), get_u(res_LH, 'woman')
    pref_hf = "Assortative (H-Man)" if u_hf_hh >= u_hf_lh else "Marrying Down (L-Man)"

    # Preference Display
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.info(f"**H-Man's Choice:** {pref_hm}")
    with col_p2:
        st.info(f"**H-Woman's Choice:** {pref_hf}")
    
    st.markdown("---")

    # 3. DETAILED STATS FOR ALL 4 MATCHES
    c1, c2, c3, c4 = st.columns(4)

    def display_household(col, title, res):
        with col:
            st.markdown(f"#### {title}")
            
            if not res['is_feasible']:
                st.error("❌ Impossible")
                st.caption("Time Constraint Violated")
                return

            # Utilities
            st.metric("Man U", f"{res['U_man']:.2f}")
            st.metric("Woman U", f"{res['U_woman']:.2f}")

            # Time Allocation Table
            # Extract raw values
            nm, lm = res.get('n_man', 0), res.get('l_man', 0)
            nw, lw = res.get('n_woman', 0), res.get('l_woman', 0)
            jm = max(0, 1 - nm - lm)
            jw = max(0, 1 - nw - lw)

            # Create mini-dataframe for clean display
            data = {
                "Role": ["Man", "Woman"],
                "House (n)": [f"{nm:.2f}", f"{nw:.2f}"],
                "Leisure (l)": [f"{lm:.2f}", f"{lw:.2f}"],
                "Job": [f"{jm:.2f}", f"{jw:.2f}"]
            }
            df = pd.DataFrame(data).set_index("Role")
            st.table(df)

            # Violations (Paper Mode Only)
            tm = nm + lm
            tw = nw + lw
            if tm > 1.001: st.warning(f"⚠️ Man Time: {tm:.2f}")
            if tw > 1.001: st.warning(f"⚠️ Woman Time: {tw:.2f}")

    # Display Columns
    display_household(c1, "(H, H)", res_HH)
    display_household(c2, "(H, L)", res_HL)
    display_household(c3, "(L, H)", res_LH)
    display_household(c4, "(L, L)", res_LL)

# ==========================================
# TAB 2: EDUCATION EQUILIBRIUM & MONTE CARLO STABILITY
# ==========================================
with tab2:
    st.subheader("Population Dynamics & Stability")
    
    # --- SECTION A: SINGLE RUN (The detailed view) ---
    st.markdown("### 1. Single Trajectory Analysis")
    col_run, col_res = st.columns([1, 3])
    
    with col_run:
        st.write("Run a single simulation with standard initial conditions.")
        run_single = st.button("Run Simulation", type="primary")
        
    if run_single:
        with st.spinner(f"Finding Equilibrium ({MODE})..."):
            eq = find_equilibrium_education(gamma_input, w_input, mode=MODE)
            
            if eq['converged']:
                c1, c2, c3 = st.columns(3)
                c1.metric("Educated Men", f"{eq['pm']:.3f}")
                c2.metric("Educated Women", f"{eq['pf']:.3f}")
                gap = eq['pm'] - eq['pf']
                c3.metric("Gender Gap", f"{gap:.3f}", delta="Patriarchal" if gap > 0 else "Matriarchal")
                
                # Single Timelapse
                hist_df = pd.DataFrame(eq['history'])
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(hist_df['Generation'], hist_df['Men'], label='Men', color='blue', linewidth=2)
                ax.plot(hist_df['Generation'], hist_df['Women'], label='Women', color='pink', linewidth=2)
                ax.set_title("Convergence Trajectory")
                ax.set_xlabel("Generation"); ax.set_ylim(0, 1)
                ax.legend(); ax.grid(True, alpha=0.3)
                st.pyplot(fig)
            else:
                st.error("Did not converge.")

    st.markdown("---")

    # --- SECTION B: MONTE CARLO ---
    st.markdown("### 2. Monte Carlo Stability Check (20 Random Starts)")
    st.caption("""
    **Testing Robustness:** Instead of assuming men start with an advantage, we simulate 20 parallel worlds 
    with completely random starting education levels.
    * **Light Lines:** Individual simulation runs.
    * **Dark Line:** The average path of society.
    """)
    
    if st.button("Run Monte Carlo Analysis"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Storage for all runs
        all_histories_men = []
        all_histories_women = []
        final_outcomes = []
        
        N_SIMS = 20
        
        for i in range(N_SIMS):
            # Random Start (0.0 to 1.0)
            rand_pm = np.random.rand()
            rand_pf = np.random.rand()
            
            # Run
            res = find_equilibrium_education(gamma_input, w_input, mode=MODE, initial_guess=(rand_pm, rand_pf))
            
            # Process Data for Plotting (Reindex to common length for averaging)
            df = pd.DataFrame(res['history'])
            df.set_index('Generation', inplace=True)
            
            # We assume max 100 generations for visualization to keep graphs clean
            # Reindex extends the line flat if it converged early
            df_reindexed = df.reindex(range(100)).ffill()
            
            all_histories_men.append(df_reindexed['Men'])
            all_histories_women.append(df_reindexed['Women'])
            final_outcomes.append((res['pm'], res['pf']))
            
            progress_bar.progress((i + 1) / N_SIMS)
        
        status_text.text("Processing Visualization...")
        
        # Calculate Averages
        avg_men = pd.concat(all_histories_men, axis=1).mean(axis=1)
        avg_women = pd.concat(all_histories_women, axis=1).mean(axis=1)
        
        # PLOTTING
        fig_mc, ax_mc = plt.subplots(figsize=(12, 6))
        
        # Plot individual "Spaghetti" strands
        for i in range(N_SIMS):
            ax_mc.plot(all_histories_men[i], color='blue', alpha=0.15, linewidth=1)
            ax_mc.plot(all_histories_women[i], color='red', alpha=0.15, linewidth=1)
            
        # Plot Averages
        ax_mc.plot(avg_men, color='navy', linewidth=3, label='Average Men')
        ax_mc.plot(avg_women, color='darkred', linewidth=3, label='Average Women')
        
        ax_mc.set_title(f"Global Stability Analysis ({MODE})")
        ax_mc.set_xlabel("Generations")
        ax_mc.set_ylabel("Proportion Educated")
        ax_mc.set_ylim(0, 1)
        ax_mc.legend(loc='upper right')
        ax_mc.grid(True, alpha=0.3)
        
        st.pyplot(fig_mc)
        
        # Insight Generator
        men_finals = [x[0] for x in final_outcomes]
        men_std = np.std(men_finals)
        
        st.write("#### Analysis Results")
        if men_std < 0.01:
            st.success(f"**Globally Stable Equilibrium:** Regardless of where society started, all {N_SIMS} simulations converged to the exact same outcome.")
        else:
            st.warning(f"**Multiple Equilibria Detected:** Society split into different outcomes depending on initial conditions (Standard Deviation: {men_std:.4f}).")
            st.write("This suggests history matters: a society starting matriarchal might stay matriarchal.")
            
# ==========================================
# TAB 3: VISUAL VERIFICATION
# ==========================================
with tab3:
    st.subheader("Visual Verification Suite")
    
    # Toggle for Graph Type
    graph_type = st.radio("Select Visualization:", 
                          ["Indifference Curves (Wage vs Bias)", "Reaction Functions (Best Response)"], 
                          horizontal=True)
    
    if graph_type == "Indifference Curves (Wage vs Bias)":
        st.caption("Replicates Figures 1 & 2. Shows the 'Impossible Region' where the paper's math fails physics.")
        if st.button("Generate Indifference Curves"):
            with st.spinner("Simulating..."):
                gammas = np.linspace(0.0, 5.0, 30)
                
                # Calculate both modes for comparison
                w_women_p = [find_indifference_point(g, 'woman', 'paper') for g in gammas]
                w_women_r = [find_indifference_point(g, 'woman', 'reality') for g in gammas]
                w_men_p = [find_indifference_point(g, 'man', 'paper') for g in gammas]
                w_men_r = [find_indifference_point(g, 'man', 'reality') for g in gammas]

                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                
                # Women
                ax1.plot(gammas, w_women_p, 'b-', label='Paper (Fig 1)')
                ax1.plot(gammas, w_women_r, 'r--', label='Reality')
                ax1.set_title("H-Type Women Indifference Curve\n(Paper vs Reality)", fontsize=12, fontweight='bold')
                ax1.set_xlabel(r"Bias Parameter ($\gamma$)", fontsize=11)
                ax1.set_ylabel(r"Wage Ratio ($w$)", fontsize=11)
                ax1.set_ylim(0, 60); ax1.legend(); ax1.grid(True, alpha=0.3)
                
                # Men
                ax2.plot(gammas, w_men_p, 'g-', label='Paper (Fig 2)')
                ax2.plot(gammas, w_men_r, 'r--', label='Reality')
                ax2.set_title("H-Men Indifference")
                ax2.set_ylim(0, 25); ax2.legend(); ax2.grid(True, alpha=0.3)
                
                st.pyplot(fig)

    elif graph_type == "Reaction Functions (Best Response)":
        st.caption("Visualizes the Nash Equilibrium. The intersection of Blue and Red lines is the stable population state.")
        st.markdown(f"**Current Parameters:** Gamma={gamma_input}, Wage={w_input}, Mode={MODE}")
        
        if st.button("Generate Reaction Functions"):
            with st.spinner("Calculating Best Responses..."):
                props = np.linspace(0.01, 0.99, 40)
                
                # Calculate curves based on CURRENT mode settings
                men_resp = [get_best_response(p, 'woman', gamma_input, w_input, MODE) for p in props]
                women_resp = [get_best_response(p, 'man', gamma_input, w_input, MODE) for p in props]
                
                fig, ax = plt.subplots(figsize=(8, 8))
                
                # Plot Men's Best Response (y axis) to Women (x axis)
                ax.plot(props, men_resp, 'b-', linewidth=2, label="Men's Response (to Women)")
                
                # Plot Women's Best Response (x axis) to Men (y axis)
                # Note: We plot women_resp on X and props on Y to flip axes for standard "Reaction Function" view
                ax.plot(women_resp, props, 'r-', linewidth=2, label="Women's Response (to Men)")
                
                # Symmetry line
                ax.plot([0,1], [0,1], 'k:', alpha=0.3, label="Symmetry Line")
                
                ax.set_xlabel("Proportion of Educated Women ($p_f$)")
                ax.set_ylabel("Proportion of Educated Men ($p_m$)")
                ax.set_title(f"Nash Equilibrium ({MODE.title()} Mode)")
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 1); ax.set_ylim(0, 1)
                
                st.pyplot(fig)