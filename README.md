# Patriarchal Gender Norms Model: Analysis & Replication 

> **Project Status:** Complete.(Might add quality of life improvements later)

> **Key Finding:** The original paper's equilibrium relies on physically impossible labor hours ($>24h/day$). When time constraints are enforced, the predicted gender education gap decreases by a significant margin.

## Overview

This project replicates the mathematical model from the paper *"Patriarchal Gender Norms: A life-cycle model of education, marriage, and labor supply choice"* (Garg, 2024). It models how cultural norms affect education, marriage, and labor supply.

I built a **Python simulation engine** to verify the theoretical claims. During replication, I discovered that the paper's analytical derivation assumes interior solutions that violate the time constraint ($l + n \le 1$).

## The Dashboard

I built an interactive **Streamlit Dashboard** to visualize the divergence between the paper's theoretical predictions and physical reality.

**Features:**

* **Toggle Modes:** Switch between "Paper Mode" (Unconstrained) and "Reality Mode" (Physically Valid).
* **Monte Carlo Analysis:** Simulates 20 parallel generations to test Global Stability.
* **Nash Equilibrium Solver:** Visualizes Best Response curves to find the stable population state.

![Home Screen](<src/Screenshot 2025-12-10 042037.png>)
-----------
![Education Level Simulation](<src/Screenshot 2025-12-10 042601.png>)
-----------
![**Monte Carlo Runs**](<src/Screenshot 2025-12-10 042622.png>)

## Key Research Findings

### 1. The "Impossible Region"

The paper predicts an indifference curve starting at Wage Ratio $\approx 11.45$. My simulation proves that to sustain this indifference, the lower-wage spouse must work **~25 hours/day**.

* **Paper Prediction:** Indifference at $w=11.45$.
* **Physical Reality:** Indifference collapses at $w=1.67$.

### 2. The Collapse of the Education Gap

In "Reality Mode," where time constraints are enforced, the "Patriarchal Equilibrium" (where men get educated and women don't) often collapses.

* **Reason:** Men cannot exploit unlimited female labor, so the economic incentive to "marry down" vanishes. The dominant strategy becomes Assortative Matching, which drives up female education.

## Tech Stack

* **Simulation:** Python, NumPy, SciPy (Optimization via SLSQP & BrentQ).
* **Visualization:** Matplotlib, Altair (Expected in a future update).
* **Interface:** Streamlit.

## How to Run

1. Clone the repository:

    ```bash
    git clone [https://github.com/Shikhardg24/Patriarchy-In-Life-Cycle-Model](https://github.com/Shikhardg24/Patriarchy-In-Life-Cycle-Model)
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Launch the dashboard:

    ```bash
    streamlit run dashboard.py
    ```
