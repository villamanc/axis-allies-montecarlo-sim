import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set page configuration
st.set_page_config(
    page_title="Axis & Allies Combat Simulator",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set style for plots
sns.set_style("whitegrid")

# ==================== COMBAT SIMULATION FUNCTIONS ====================

def generate_unit_rolls(unit_dict, num_rows=10_000, sides=6, seed=None):
    """Generate a DataFrame of random dice rolls for each individual unit."""
    if seed is not None:
        np.random.seed(seed)

    columns = {}
    for unit, count in unit_dict.items():
        for i in range(1, count + 1):
            col_name = f"{unit}_{i}"
            columns[col_name] = np.random.randint(1, sides + 1, size=num_rows)

    return pd.DataFrame(columns)

def count_hits(roll_df, combat_values, mode="attack"):
    """Count hits for each simulation row based on combat values."""
    if mode not in ("attack", "defense"):
        raise ValueError("mode must be 'attack' or 'defense'")

    hit_columns = {}
    for col in roll_df.columns:
        unit = col.rsplit("_", 1)[0]
        threshold = combat_values.get(unit, {}).get(mode, 0)
        hit_columns[col] = (roll_df[col] > 0) & (roll_df[col] <= threshold)

    hit_df = pd.DataFrame(hit_columns)
    hits_per_sim = hit_df.sum(axis=1)
    hits_by_unit = (
        hit_df
        .rename(columns=lambda c: c.rsplit("_", 1)[0])
        .groupby(axis=1, level=0)
        .sum()
    )
    total_hits = int(hits_per_sim.sum())

    return hit_df, hits_per_sim, hits_by_unit, total_hits

def assign_casualties(unit_df, hits_per_sim):
    """Assign casualties left-to-right per simulation."""
    df = unit_df.copy()
    for i in df.index:
        hits_remaining = hits_per_sim.loc[i]
        if hits_remaining <= 0:
            continue
        for col in df.columns:
            if hits_remaining == 0:
                break
            if df.at[i, col] != 0:
                df.at[i, col] = 0
                hits_remaining -= 1
    return df

def check_if_alive(unit_df):
    """Check which simulations still have living units."""
    return (unit_df != 0).any(axis=1)

def simulate_combat(attacker_units, defender_units, combat_values, num_sims=10_000, seed=None, max_rounds=100):
    """Simulate full combat until one side is eliminated."""
    if seed is not None:
        np.random.seed(seed)
    
    combat_history = {"rounds": []}
    
    attacker_df = generate_unit_rolls(attacker_units, num_rows=num_sims, seed=seed)
    defender_df = generate_unit_rolls(defender_units, num_rows=num_sims, seed=seed if seed is None else seed + 1)
    
    attacker_eliminated_round = pd.Series(0, index=attacker_df.index)
    defender_eliminated_round = pd.Series(0, index=defender_df.index)
    active_simulations = pd.Series(True, index=attacker_df.index)
    
    round_num = 0
    
    while round_num < max_rounds:
        round_num += 1
        
        attacker_alive = check_if_alive(attacker_df)
        defender_alive = check_if_alive(defender_df)
        both_alive = attacker_alive & defender_alive
        active_simulations = both_alive
        
        if not active_simulations.any():
            break
        
        attacker_rolls = generate_unit_rolls(attacker_units, num_rows=num_sims, seed=None)
        defender_rolls = generate_unit_rolls(defender_units, num_rows=num_sims, seed=None)
        
        attacker_rolls = attacker_rolls * (attacker_df != 0).astype(int)
        defender_rolls = defender_rolls * (defender_df != 0).astype(int)
        
        for col in attacker_rolls.columns:
            attacker_rolls.loc[~active_simulations, col] = 0
        for col in defender_rolls.columns:
            defender_rolls.loc[~active_simulations, col] = 0
        
        attacker_hit_info = count_hits(attacker_rolls, combat_values, "attack")
        defender_hit_info = count_hits(defender_rolls, combat_values, "defense")
        
        attacker_hits = attacker_hit_info[1]
        defender_hits = defender_hit_info[1]
        
        attacker_hits[~active_simulations] = 0
        defender_hits[~active_simulations] = 0
        
        defender_df = assign_casualties(defender_df, attacker_hits)
        attacker_df = assign_casualties(attacker_df, defender_hits)
        
        attacker_alive_after = check_if_alive(attacker_df)
        defender_alive_after = check_if_alive(defender_df)
        
        newly_eliminated_attackers = active_simulations & attacker_alive & ~attacker_alive_after
        newly_eliminated_defenders = active_simulations & defender_alive & ~defender_alive_after
        
        attacker_eliminated_round[newly_eliminated_attackers] = round_num
        defender_eliminated_round[newly_eliminated_defenders] = round_num
        
        round_info = {
            "round": round_num,
            "attacker_rolls": attacker_rolls.copy(),
            "defender_rolls": defender_rolls.copy(),
            "attacker_hits": attacker_hits.copy(),
            "defender_hits": defender_hits.copy(),
            "attacker_df": attacker_df.copy(),
            "defender_df": defender_df.copy(),
            "attacker_casualties": attacker_hit_info[2].copy(),
            "defender_casualties": defender_hit_info[2].copy(),
            "active_simulations": active_simulations.copy()
        }
        
        combat_history["rounds"].append(round_info)
    
    combat_history["attacker_eliminated_round"] = attacker_eliminated_round
    combat_history["defender_eliminated_round"] = defender_eliminated_round
    combat_history["total_rounds"] = round_num
    
    attacker_wins = (defender_eliminated_round > 0) & (attacker_eliminated_round == 0)
    defender_wins = (attacker_eliminated_round > 0) & (defender_eliminated_round == 0)
    mutual_destruction = (attacker_eliminated_round > 0) & (defender_eliminated_round > 0)
    
    combat_history["summary"] = {
        "attacker_wins": attacker_wins.sum(),
        "defender_wins": defender_wins.sum(),
        "mutual_destruction": mutual_destruction.sum(),
        "attacker_win_rate": attacker_wins.mean(),
        "defender_win_rate": defender_wins.mean(),
        "mutual_destruction_rate": mutual_destruction.mean(),
        "avg_rounds": pd.Series([
            attacker_eliminated_round[attacker_eliminated_round > 0].mean(),
            defender_eliminated_round[defender_eliminated_round > 0].mean()
        ], index=["attacker_eliminated", "defender_eliminated"])
    }
    
    return combat_history

def create_combat_visualizations(results, attacker_name="Attacker", defender_name="Defender"):
    """Create comprehensive visualizations of combat simulation results."""
    fig = plt.figure(figsize=(20, 12))
    
    # SUBPLOT 1: Win Distribution
    ax1 = plt.subplot(2, 3, 1)
    win_data = [
        results['summary']['attacker_wins'],
        results['summary']['defender_wins'],
        results['summary']['mutual_destruction']
    ]
    colors = ['#2ecc71', '#e74c3c', '#95a5a6']
    labels = [f'{attacker_name}\n({results["summary"]["attacker_win_rate"]:.1%})',
              f'{defender_name}\n({results["summary"]["defender_win_rate"]:.1%})',
              f'Mutual\n({results["summary"]["mutual_destruction_rate"]:.1%})']
    
    wedges, texts, autotexts = ax1.pie(win_data, labels=labels, colors=colors, 
                                         autopct='%d', startangle=90)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(12)
        autotext.set_weight('bold')
    ax1.set_title('Battle Outcomes', fontsize=14, weight='bold')
    
    # SUBPLOT 2: Units Alive Over Rounds
    ax2 = plt.subplot(2, 3, 2)
    rounds_data = []
    for round_idx, round_data in enumerate(results['rounds']):
        round_num = round_idx + 1
        att_alive = (round_data['attacker_df'] != 0).sum(axis=1).mean()
        def_alive = (round_data['defender_df'] != 0).sum(axis=1).mean()
        rounds_data.append({
            'round': round_num,
            'attacker_avg': att_alive,
            'defender_avg': def_alive
        })
    
    rounds_df = pd.DataFrame(rounds_data)
    ax2.plot(rounds_df['round'], rounds_df['attacker_avg'], 
             marker='o', linewidth=2, markersize=8, color='#2ecc71', label=attacker_name)
    ax2.plot(rounds_df['round'], rounds_df['defender_avg'], 
             marker='s', linewidth=2, markersize=8, color='#e74c3c', label=defender_name)
    ax2.set_xlabel('Round', fontsize=12, weight='bold')
    ax2.set_ylabel('Avg Units Alive', fontsize=12, weight='bold')
    ax2.set_title('Average Units Surviving by Round', fontsize=14, weight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # SUBPLOT 3: Hits Per Round
    ax3 = plt.subplot(2, 3, 3)
    hits_data = []
    for round_idx, round_data in enumerate(results['rounds']):
        round_num = round_idx + 1
        att_hits = round_data['attacker_hits'].mean()
        def_hits = round_data['defender_hits'].mean()
        hits_data.append({
            'round': round_num,
            'attacker_hits': att_hits,
            'defender_hits': def_hits
        })
    
    hits_df = pd.DataFrame(hits_data)
    x = np.arange(len(hits_df))
    width = 0.35
    ax3.bar(x - width/2, hits_df['attacker_hits'], width, 
            label=attacker_name, color='#2ecc71', alpha=0.8)
    ax3.bar(x + width/2, hits_df['defender_hits'], width, 
            label=defender_name, color='#e74c3c', alpha=0.8)
    
    ax3.set_xlabel('Round', fontsize=12, weight='bold')
    ax3.set_ylabel('Avg Hits Scored', fontsize=12, weight='bold')
    ax3.set_title('Average Hits Scored by Round', fontsize=14, weight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels([f'R{i+1}' for i in range(len(hits_df))])
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # SUBPLOT 4: Elimination Round Distribution
    ax4 = plt.subplot(2, 3, 4)
    att_elim = results['attacker_eliminated_round'][results['attacker_eliminated_round'] > 0]
    def_elim = results['defender_eliminated_round'][results['defender_eliminated_round'] > 0]
    
    max_round = max(att_elim.max() if len(att_elim) > 0 else 1, 
                    def_elim.max() if len(def_elim) > 0 else 1)
    bins = np.arange(0.5, max_round + 1.5, 1)
    
    ax4.hist(att_elim, bins=bins, alpha=0.6, label=f'{attacker_name} Eliminated', 
             color='#2ecc71', edgecolor='black')
    ax4.hist(def_elim, bins=bins, alpha=0.6, label=f'{defender_name} Eliminated', 
             color='#e74c3c', edgecolor='black')
    
    ax4.set_xlabel('Round', fontsize=12, weight='bold')
    ax4.set_ylabel('Number of Eliminations', fontsize=12, weight='bold')
    ax4.set_title('When Each Side Was Eliminated', fontsize=14, weight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # SUBPLOT 5: Combat Duration Distribution
    ax5 = plt.subplot(2, 3, 5)
    combat_duration = np.maximum(results['attacker_eliminated_round'], 
                                  results['defender_eliminated_round'])
    
    ax5.hist(combat_duration, bins=np.arange(0.5, combat_duration.max() + 1.5, 1),
             color='#3498db', alpha=0.7, edgecolor='black')
    ax5.axvline(combat_duration.mean(), color='red', linestyle='--', 
                linewidth=2, label=f'Mean: {combat_duration.mean():.2f} rounds')
    ax5.axvline(np.median(combat_duration), color='orange', linestyle='--', 
                linewidth=2, label=f'Median: {np.median(combat_duration):.0f} rounds')
    
    ax5.set_xlabel('Rounds Until Combat Ended', fontsize=12, weight='bold')
    ax5.set_ylabel('Number of Simulations', fontsize=12, weight='bold')
    ax5.set_title('Combat Duration Distribution', fontsize=14, weight='bold')
    ax5.legend(fontsize=10)
    ax5.grid(True, alpha=0.3, axis='y')
    
    # SUBPLOT 6: Cumulative Win Probability
    ax6 = plt.subplot(2, 3, 6)
    max_round = int(combat_duration.max())
    cumulative_data = []
    
    for round_num in range(1, max_round + 1):
        att_wins_by_round = ((results['defender_eliminated_round'] <= round_num) & 
                             (results['defender_eliminated_round'] > 0) &
                             (results['attacker_eliminated_round'] == 0)).sum()
        def_wins_by_round = ((results['attacker_eliminated_round'] <= round_num) & 
                             (results['attacker_eliminated_round'] > 0) &
                             (results['defender_eliminated_round'] == 0)).sum()
        
        total_sims = len(results['attacker_eliminated_round'])
        cumulative_data.append({
            'round': round_num,
            'attacker_win_pct': att_wins_by_round / total_sims * 100,
            'defender_win_pct': def_wins_by_round / total_sims * 100
        })
    
    cum_df = pd.DataFrame(cumulative_data)
    ax6.plot(cum_df['round'], cum_df['attacker_win_pct'], 
             marker='o', linewidth=2, markersize=6, color='#2ecc71', label=attacker_name)
    ax6.plot(cum_df['round'], cum_df['defender_win_pct'], 
             marker='s', linewidth=2, markersize=6, color='#e74c3c', label=defender_name)
    
    ax6.set_xlabel('Round', fontsize=12, weight='bold')
    ax6.set_ylabel('Cumulative Win %', fontsize=12, weight='bold')
    ax6.set_title('Cumulative Win Probability by Round', fontsize=14, weight='bold')
    ax6.legend(fontsize=10)
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

# ==================== STREAMLIT APP ====================

def main():
    st.title("⚔️ Axis & Allies Combat Simulator")
    st.markdown("### Simulate battles and analyze outcomes with statistical precision")
    
    # Sidebar for configuration
    st.sidebar.header("⚙️ Simulation Settings")
    
    num_sims = st.sidebar.slider(
        "Number of Simulations",
        min_value=1000,
        max_value=50000,
        value=10000,
        step=1000,
        help="More simulations = more accurate results (but slower)"
    )
    
    use_seed = st.sidebar.checkbox("Use Random Seed (for reproducibility)", value=True)
    seed = 42 if use_seed else None
    
    st.sidebar.markdown("---")
    
    # Combat values (default Axis & Allies values)
    combat_values = {
        "infantry": {"attack": 1, "defense": 2},
        "artillery": {"attack": 2, "defense": 2},
        "mech": {"attack": 1, "defense": 2},
        "tank": {"attack": 3, "defense": 3},
        "aaa": {"attack": 0, "defense": 1},
        "fighter": {"attack": 3, "defense": 4},
        "bomber": {"attack": 4, "defense": 1},
        "submarine": {"attack": 2, "defense": 2},
        "destroyer": {"attack": 3, "defense": 3},
        "cruiser": {"attack": 3, "defense": 3},
        "battleship": {"attack": 4, "defense": 4},
        "aircraft_carrier": {"attack": 1, "defense": 3},
        "transport": {"attack": 0, "defense": 1}
    }
    
    # Main content area - two columns for attacker and defender
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🔴 Attacker Forces")
        attacker_units = {}
        
        land_units = ["infantry", "artillery", "mech", "tank", "aaa"]
        air_units = ["fighter", "bomber"]
        sea_units = ["submarine", "destroyer", "cruiser", "battleship", "aircraft_carrier", "transport"]
        
        with st.expander("Land Units", expanded=True):
            for unit in land_units:
                count = st.number_input(
                    f"{unit.capitalize()} (A:{combat_values[unit]['attack']}/D:{combat_values[unit]['defense']})",
                    min_value=0,
                    max_value=50,
                    value=4 if unit == "infantry" else 0,
                    step=1,
                    key=f"att_{unit}"
                )
                attacker_units[unit] = count
        
        with st.expander("Air Units"):
            for unit in air_units:
                count = st.number_input(
                    f"{unit.capitalize()} (A:{combat_values[unit]['attack']}/D:{combat_values[unit]['defense']})",
                    min_value=0,
                    max_value=50,
                    value=0,
                    step=1,
                    key=f"att_{unit}"
                )
                attacker_units[unit] = count
        
        with st.expander("Sea Units"):
            for unit in sea_units:
                count = st.number_input(
                    f"{unit.capitalize()} (A:{combat_values[unit]['attack']}/D:{combat_values[unit]['defense']})",
                    min_value=0,
                    max_value=50,
                    value=0,
                    step=1,
                    key=f"att_{unit}"
                )
                attacker_units[unit] = count
    
    with col2:
        st.header("🔵 Defender Forces")
        defender_units = {}
        
        with st.expander("Land Units", expanded=True):
            for unit in land_units:
                count = st.number_input(
                    f"{unit.capitalize()} (A:{combat_values[unit]['attack']}/D:{combat_values[unit]['defense']})",
                    min_value=0,
                    max_value=50,
                    value=4 if unit == "infantry" else 0,
                    step=1,
                    key=f"def_{unit}"
                )
                defender_units[unit] = count
        
        with st.expander("Air Units"):
            for unit in air_units:
                count = st.number_input(
                    f"{unit.capitalize()} (A:{combat_values[unit]['attack']}/D:{combat_values[unit]['defense']})",
                    min_value=0,
                    max_value=50,
                    value=0,
                    step=1,
                    key=f"def_{unit}"
                )
                defender_units[unit] = count
        
        with st.expander("Sea Units"):
            for unit in sea_units:
                count = st.number_input(
                    f"{unit.capitalize()} (A:{combat_values[unit]['attack']}/D:{combat_values[unit]['defense']})",
                    min_value=0,
                    max_value=50,
                    value=0,
                    step=1,
                    key=f"def_{unit}"
                )
                defender_units[unit] = count
    
    # Check if both sides have units
    attacker_total = sum(attacker_units.values())
    defender_total = sum(defender_units.values())
    
    st.markdown("---")
    
    # Run simulation button
    if st.button("🎲 Run Combat Simulation", type="primary", use_container_width=True):
        if attacker_total == 0 or defender_total == 0:
            st.error("⚠️ Both sides need at least one unit to simulate combat!")
        else:
            with st.spinner(f"Running {num_sims:,} simulations..."):
                results = simulate_combat(
                    attacker_units,
                    defender_units,
                    combat_values,
                    num_sims=num_sims,
                    seed=seed
                )
            
            st.success("✅ Simulation complete!")
            
            # Display summary statistics
            st.header("📊 Battle Summary")
            
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.metric(
                    "Attacker Wins",
                    f"{results['summary']['attacker_wins']:,}",
                    f"{results['summary']['attacker_win_rate']:.1%}"
                )
            
            with summary_col2:
                st.metric(
                    "Defender Wins",
                    f"{results['summary']['defender_wins']:,}",
                    f"{results['summary']['defender_win_rate']:.1%}"
                )
            
            with summary_col3:
                st.metric(
                    "Mutual Destruction",
                    f"{results['summary']['mutual_destruction']:,}",
                    f"{results['summary']['mutual_destruction_rate']:.1%}"
                )
            
            # Additional stats
            st.markdown("---")
            stat_col1, stat_col2 = st.columns(2)
            
            with stat_col1:
                st.metric(
                    "Avg Rounds (Attacker Eliminated)",
                    f"{results['summary']['avg_rounds']['attacker_eliminated']:.2f}"
                )
            
            with stat_col2:
                st.metric(
                    "Avg Rounds (Defender Eliminated)",
                    f"{results['summary']['avg_rounds']['defender_eliminated']:.2f}"
                )
            
            # Visualizations
            st.header("📈 Detailed Analysis")
            
            fig = create_combat_visualizations(results, "Attacker", "Defender")
            st.pyplot(fig)
            
            # Round-by-round details
            with st.expander("🔍 View Round-by-Round Statistics"):
                for round_idx, round_data in enumerate(results['rounds']):
                    round_num = round_idx + 1
                    
                    st.subheader(f"Round {round_num}")
                    
                    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
                    
                    with r_col1:
                        active = round_data['active_simulations'].sum()
                        st.metric("Active Simulations", f"{active:,}")
                    
                    with r_col2:
                        att_alive_avg = (round_data['attacker_df'] != 0).sum(axis=1).mean()
                        st.metric("Attacker Units (Avg)", f"{att_alive_avg:.2f}")
                    
                    with r_col3:
                        def_alive_avg = (round_data['defender_df'] != 0).sum(axis=1).mean()
                        st.metric("Defender Units (Avg)", f"{def_alive_avg:.2f}")
                    
                    with r_col4:
                        att_hits = round_data['attacker_hits'].mean()
                        def_hits = round_data['defender_hits'].mean()
                        st.metric("Avg Hits (A/D)", f"{att_hits:.2f} / {def_hits:.2f}")
                    
                    st.markdown("---")

if __name__ == "__main__":
    main()
