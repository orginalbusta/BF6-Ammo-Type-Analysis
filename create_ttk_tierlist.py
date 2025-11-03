import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read data
falloff_df = pd.read_csv('data/Battlefield 6 Damage Fall Off - V2.csv', skiprows=1)
ammo_df = pd.read_csv('analysis_results/Weapon_Ammo_Types.csv')

# Clean up falloff data
falloff_df = falloff_df.rename(columns={
    'Gun (!!! -> Missing)': 'Gun',
    'Dmg': 'DMG_Close',
    '10m': 'DMG_10M',
    '75m': 'DMG_75M',
    'ROF': 'ROF'
})

# Name mapping for consistency
name_mapping = {
    'TR7': 'TR-7',
    'M/60': 'M60',
    'M240L': 'M240L',
    'QBZ': 'QBZ-192',
    'AK205': 'AK-205'
}
falloff_df['Gun'] = falloff_df['Gun'].replace(name_mapping)

# Merge dataframes
df = falloff_df[['Gun', 'Type', 'DMG_Close', 'DMG_10M', 'DMG_75M', 'ROF']].copy()
df = df.merge(ammo_df[['Gun', 'Ammo Type']], on='Gun', how='left')

# Filter out weapons without complete data
df = df.dropna(subset=['DMG_Close', 'DMG_10M', 'DMG_75M', 'ROF', 'Ammo Type', 'Type'])

# Extrapolate damage
def extrapolate_damage(dmg_close, dmg_10m, dmg_75m, target_range):
    """Linear interpolation/extrapolation"""
    if target_range <= 0:
        return dmg_close
    elif target_range <= 10:
        return np.interp(target_range, [0, 10], [dmg_close, dmg_10m])
    elif target_range <= 75:
        return np.interp(target_range, [10, 75], [dmg_10m, dmg_75m])
    else:  # Extrapolate beyond 75m
        slope = (dmg_75m - dmg_10m) / (75 - 10)
        dmg_100m = dmg_75m + slope * (100 - 75)
        dmg_100m = max(dmg_100m, 10)
        return np.interp(target_range, [75, 100], [dmg_75m, dmg_100m])

# Constants
BASE_HS_MULT = 1.34
HP_MULT = 1.5
SYNTH_MULT = 1.75
TARGET_HP = 100
RANGES = [0, 10, 20, 30, 40, 50, 60, 75, 100]
MAX_HS = 5

def calculate_stk_ttk(base_dmg, rof, hs_mult, num_hs):
    """Calculate STK and TTK for given parameters"""
    if base_dmg <= 0 or rof <= 0:
        return np.inf, np.inf
    
    best_stk = np.inf
    best_ttk = np.inf
    
    for body_shots in range(20):
        total_shots = num_hs + body_shots
        total_damage = (base_dmg * hs_mult * num_hs) + (base_dmg * body_shots)
        
        if total_damage >= TARGET_HP:
            stk = total_shots
            ttk = (stk - 1) * (60 / rof) * 1000
            if stk < best_stk:
                best_stk = stk
                best_ttk = ttk
            break
    
    return int(best_stk) if best_stk != np.inf else np.inf, best_ttk

print(f"\n{'='*80}")
print(f"ANALYZING TTK IMPROVEMENTS FOR ALL WEAPONS")
print(f"{'='*80}\n")

# Analyze each weapon
weapon_analysis = []

for idx, weapon_row in df.iterrows():
    gun_name = weapon_row['Gun']
    weapon_class = weapon_row['Type']
    dmg_close = float(weapon_row['DMG_Close'])
    dmg_10m = float(weapon_row['DMG_10M'])
    dmg_75m = float(weapon_row['DMG_75M'])
    rof = float(weapon_row['ROF'])
    ammo_type = weapon_row['Ammo Type']
    
    # Calculate average TTK improvement across all ranges and headshot counts
    hp_improvements = []
    synth_improvements = []
    
    for r in RANGES:
        current_dmg = extrapolate_damage(dmg_close, dmg_10m, dmg_75m, r)
        
        for num_hs in range(MAX_HS + 1):
            base_stk, base_ttk = calculate_stk_ttk(current_dmg, rof, BASE_HS_MULT, num_hs)
            hp_stk, hp_ttk = calculate_stk_ttk(current_dmg, rof, HP_MULT, num_hs)
            
            if base_ttk != np.inf and hp_ttk != np.inf:
                improvement = base_ttk - hp_ttk
                if improvement > 0:
                    hp_improvements.append(improvement)
            
            if ammo_type == 'Synthetic':
                synth_stk, synth_ttk = calculate_stk_ttk(current_dmg, rof, SYNTH_MULT, num_hs)
                if base_ttk != np.inf and synth_ttk != np.inf:
                    improvement = base_ttk - synth_ttk
                    if improvement > 0:
                        synth_improvements.append(improvement)
    
    # Calculate statistics
    avg_hp_improvement = np.mean(hp_improvements) if hp_improvements else 0
    max_hp_improvement = max(hp_improvements) if hp_improvements else 0
    scenarios_with_hp_improvement = len(hp_improvements)
    
    avg_synth_improvement = np.mean(synth_improvements) if synth_improvements else 0
    max_synth_improvement = max(synth_improvements) if synth_improvements else 0
    scenarios_with_synth_improvement = len(synth_improvements)
    
    weapon_analysis.append({
        'Gun': gun_name,
        'Type': weapon_class,
        'Ammo Type': ammo_type,
        'Avg HP Improvement (ms)': avg_hp_improvement,
        'Max HP Improvement (ms)': max_hp_improvement,
        'HP Scenarios': scenarios_with_hp_improvement,
        'Avg Synth Improvement (ms)': avg_synth_improvement,
        'Max Synth Improvement (ms)': max_synth_improvement,
        'Synth Scenarios': scenarios_with_synth_improvement
    })

# Create DataFrame
analysis_df = pd.DataFrame(weapon_analysis)

# Sort by HP improvement
hp_tierlist = analysis_df.sort_values('Avg HP Improvement (ms)', ascending=False)
print("\n" + "="*80)
print("HOLLOW POINT TIERLIST (by Average TTK Improvement)")
print("="*80)
print(hp_tierlist[['Gun', 'Type', 'Avg HP Improvement (ms)', 'Max HP Improvement (ms)', 'HP Scenarios']].to_string(index=False))

# Sort by Synth improvement (only weapons with Synth access)
synth_df = analysis_df[analysis_df['Ammo Type'] == 'Synthetic']
synth_tierlist = synth_df.sort_values('Avg Synth Improvement (ms)', ascending=False)
print("\n" + "="*80)
print("SYNTHETIC TIERLIST (by Average TTK Improvement)")
print("="*80)
print(synth_tierlist[['Gun', 'Type', 'Avg Synth Improvement (ms)', 'Max Synth Improvement (ms)', 'Synth Scenarios']].to_string(index=False))

# Save to CSV
hp_tierlist.to_csv('analysis_results/HP_Tierlist.csv', index=False)
synth_tierlist.to_csv('analysis_results/Synth_Tierlist.csv', index=False)

print(f"\n{'='*80}")
print(f"Saved: analysis_results/HP_Tierlist.csv")
print(f"Saved: analysis_results/Synth_Tierlist.csv")
print(f"{'='*80}\n")

# Create markdown summary for README
with open('analysis_results/TIERLIST_SUMMARY.md', 'w') as f:
    f.write("# Ammo Type Tierlist\n\n")
    
    f.write("## Hollow Point (HP) Tierlist\n\n")
    f.write("Ranked by average TTK improvement across all ranges and headshot combinations.\n\n")
    f.write("| Rank | Weapon | Class | Avg TTK Improvement | Max TTK Improvement |\n")
    f.write("|------|--------|-------|---------------------|---------------------|\n")
    for i, row in hp_tierlist.head(10).iterrows():
        f.write(f"| {i+1} | {row['Gun']} | {row['Type']} | {row['Avg HP Improvement (ms)']:.1f}ms | {row['Max HP Improvement (ms)']:.1f}ms |\n")
    
    f.write("\n## Synthetic Tierlist\n\n")
    f.write("Ranked by average TTK improvement across all ranges and headshot combinations.\n\n")
    f.write("| Rank | Weapon | Class | Avg TTK Improvement | Max TTK Improvement |\n")
    f.write("|------|--------|-------|---------------------|---------------------|\n")
    rank = 1
    for i, row in synth_tierlist.iterrows():
        f.write(f"| {rank} | {row['Gun']} | {row['Type']} | {row['Avg Synth Improvement (ms)']:.1f}ms | {row['Max Synth Improvement (ms)']:.1f}ms |\n")
        rank += 1

print(f"Saved: analysis_results/TIERLIST_SUMMARY.md")

