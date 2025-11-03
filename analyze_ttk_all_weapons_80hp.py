import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import os

# Read data
falloff_df = pd.read_csv('data/Battlefield 6 Damage Fall Off - V2.csv', skiprows=1)
weapon_df = pd.read_csv('data/BF6 DPS Chart v2.1 _SEASON 1 UPDATES_.xlsx - All Guns by Weapon Type.csv')
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

# Extrapolate damage to more ranges
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
        dmg_100m = max(dmg_100m, 10)  # Floor at 10 damage
        return np.interp(target_range, [75, 100], [dmg_75m, dmg_100m])

# Constants
BASE_HS_MULT = 1.34
HP_MULT = 1.5
SYNTH_MULT = 1.75
RANGES = [0, 10, 20, 30, 40, 50, 60, 75, 100]
MAX_HS = 5

def calculate_stk_ttk(base_dmg, rof, hs_mult, num_hs, target_hp):
    """Calculate STK and TTK for given parameters"""
    if base_dmg <= 0 or rof <= 0:
        return np.inf, np.inf
    
    # Find minimum shots needed
    best_stk = np.inf
    best_ttk = np.inf
    
    # Try different numbers of body shots
    for body_shots in range(20):  # Max 20 body shots to consider
        total_shots = num_hs + body_shots
        total_damage = (base_dmg * hs_mult * num_hs) + (base_dmg * body_shots)
        
        if total_damage >= target_hp:
            stk = total_shots
            ttk = (stk - 1) * (60 / rof) * 1000  # in ms
            if stk < best_stk:
                best_stk = stk
                best_ttk = ttk
            break
    
    return int(best_stk) if best_stk != np.inf else np.inf, best_ttk

# Create output directories
os.makedirs('visualizations/TTK_ANALYSIS_80HP', exist_ok=True)
unique_classes = df['Type'].unique()
for weapon_class in unique_classes:
    os.makedirs(f'visualizations/TTK_ANALYSIS_80HP/{weapon_class}', exist_ok=True)

print(f"\n{'='*80}")
print(f"GENERATING TTK ANALYSIS FOR ALL WEAPONS (80 HP with 100 HP color scale)")
print(f"{'='*80}\n")

# Process each weapon
for idx, weapon_row in df.iterrows():
    gun_name = weapon_row['Gun']
    weapon_class = weapon_row['Type']
    dmg_close = float(weapon_row['DMG_Close'])
    dmg_10m = float(weapon_row['DMG_10M'])
    dmg_75m = float(weapon_row['DMG_75M'])
    rof = float(weapon_row['ROF'])
    ammo_type = weapon_row['Ammo Type']
    
    print(f"Processing: {gun_name} ({weapon_class})")
    
    # Calculate TTK for BOTH 100HP and 80HP to find shared color scale
    all_ttk_values = []
    
    for target_hp in [100, 80]:
        for r in RANGES:
            current_dmg = extrapolate_damage(dmg_close, dmg_10m, dmg_75m, r)
            
            for num_hs in range(MAX_HS + 1):
                # Base ammo
                _, base_ttk = calculate_stk_ttk(current_dmg, rof, BASE_HS_MULT, num_hs, target_hp)
                if base_ttk != np.inf:
                    all_ttk_values.append(base_ttk)
                
                # HP ammo
                _, hp_ttk = calculate_stk_ttk(current_dmg, rof, HP_MULT, num_hs, target_hp)
                if hp_ttk != np.inf:
                    all_ttk_values.append(hp_ttk)
                
                # Synthetic ammo (if available)
                if ammo_type == 'Synthetic':
                    _, synth_ttk = calculate_stk_ttk(current_dmg, rof, SYNTH_MULT, num_hs, target_hp)
                    if synth_ttk != np.inf:
                        all_ttk_values.append(synth_ttk)
    
    # Calculate shared color scale for TTK
    global_ttk_min = min(all_ttk_values)
    global_ttk_max = max(all_ttk_values)
    
    # Calculate improvements for BOTH 100HP and 80HP to find shared improvement scale
    all_improvements = []
    
    for target_hp in [100, 80]:
        # Store TTK values for this HP level
        base_ttks = {}
        hp_ttks = {}
        synth_ttks = {}
        
        for r in RANGES:
            current_dmg = extrapolate_damage(dmg_close, dmg_10m, dmg_75m, r)
            
            for num_hs in range(MAX_HS + 1):
                _, base_ttk = calculate_stk_ttk(current_dmg, rof, BASE_HS_MULT, num_hs, target_hp)
                _, hp_ttk = calculate_stk_ttk(current_dmg, rof, HP_MULT, num_hs, target_hp)
                
                base_ttks[(r, num_hs)] = base_ttk
                hp_ttks[(r, num_hs)] = hp_ttk
                
                # Calculate HP improvement
                if base_ttk != np.inf and hp_ttk != np.inf:
                    improvement = base_ttk - hp_ttk
                    all_improvements.append(improvement)
                
                # Synthetic if available
                if ammo_type == 'Synthetic':
                    _, synth_ttk = calculate_stk_ttk(current_dmg, rof, SYNTH_MULT, num_hs, target_hp)
                    synth_ttks[(r, num_hs)] = synth_ttk
                    
                    if base_ttk != np.inf and synth_ttk != np.inf:
                        improvement = base_ttk - synth_ttk
                        all_improvements.append(improvement)
    
    # Calculate shared improvement scale (symmetric around 0 for proper centering)
    if all_improvements:
        max_abs_improvement = max(abs(min(all_improvements)), abs(max(all_improvements)))
        global_imp_min = -max_abs_improvement
        global_imp_max = max_abs_improvement
    else:
        global_imp_min = -100
        global_imp_max = 100
    
    # Now calculate 80HP results for plotting
    results_80hp = []
    for r in RANGES:
        current_dmg = extrapolate_damage(dmg_close, dmg_10m, dmg_75m, r)
        
        for num_hs in range(MAX_HS + 1):
            # Base ammo
            base_stk, base_ttk = calculate_stk_ttk(current_dmg, rof, BASE_HS_MULT, num_hs, 80)
            results_80hp.append({
                'Range': r,
                'Headshots': num_hs,
                'Ammo': 'Base',
                'STK': base_stk,
                'TTK_ms': base_ttk
            })
            
            # HP ammo
            hp_stk, hp_ttk = calculate_stk_ttk(current_dmg, rof, HP_MULT, num_hs, 80)
            results_80hp.append({
                'Range': r,
                'Headshots': num_hs,
                'Ammo': 'HP',
                'STK': hp_stk,
                'TTK_ms': hp_ttk
            })
            
            # Synthetic ammo (if available)
            if ammo_type == 'Synthetic':
                synth_stk, synth_ttk = calculate_stk_ttk(current_dmg, rof, SYNTH_MULT, num_hs, 80)
                results_80hp.append({
                    'Range': r,
                    'Headshots': num_hs,
                    'Ammo': 'Synth',
                    'STK': synth_stk,
                    'TTK_ms': synth_ttk
                })
    
    df_results = pd.DataFrame(results_80hp)
    
    # Create visualizations with SHARED color scale
    if ammo_type == 'Synthetic':
        # 2x3 grid for weapons with Synthetic access
        fig, axes = plt.subplots(2, 3, figsize=(24, 16))
        
        # Prepare TTK pivots
        pivot_base = df_results[df_results['Ammo'] == 'Base'].pivot(index='Headshots', columns='Range', values='TTK_ms')
        pivot_base = pivot_base.iloc[::-1]
        pivot_hp = df_results[df_results['Ammo'] == 'HP'].pivot(index='Headshots', columns='Range', values='TTK_ms')
        pivot_hp = pivot_hp.iloc[::-1]
        pivot_synth = df_results[df_results['Ammo'] == 'Synth'].pivot(index='Headshots', columns='Range', values='TTK_ms')
        pivot_synth = pivot_synth.iloc[::-1]
        
        # USE GLOBAL COLOR SCALE (same as 100HP version)
        ttk_min = global_ttk_min
        ttk_max = global_ttk_max
        
        # Top Row: TTK Heatmaps
        # 1. Base ammo
        ax1 = axes[0, 0]
        sns.heatmap(pivot_base, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax1, 
                    vmin=ttk_min, vmax=ttk_max,
                    cbar_kws={'label': 'TTK (ms)'})
        ax1.set_title(f'{gun_name} - TTK with Base Ammo (1.34x HS) [80 HP]', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Range (m)', fontsize=12)
        ax1.set_ylabel('Number of Headshots', fontsize=12)
        
        # 2. HP ammo
        ax2 = axes[0, 1]
        sns.heatmap(pivot_hp, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax2, 
                    vmin=ttk_min, vmax=ttk_max,
                    cbar_kws={'label': 'TTK (ms)'})
        ax2.set_title(f'{gun_name} - TTK with Hollow Point (1.5x HS) [80 HP]', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Range (m)', fontsize=12)
        ax2.set_ylabel('Number of Headshots', fontsize=12)
        
        # 3. Synthetic ammo
        ax3 = axes[0, 2]
        sns.heatmap(pivot_synth, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax3, 
                    vmin=ttk_min, vmax=ttk_max,
                    cbar_kws={'label': 'TTK (ms)'})
        ax3.set_title(f'{gun_name} - TTK with Synthetic (1.75x HS) [80 HP]', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Range (m)', fontsize=12)
        ax3.set_ylabel('Number of Headshots', fontsize=12)
        
        # Bottom Row: Improvements
        # 4. Blank for Base
        axes[1, 0].axis('off')
        
        # Calculate improvements
        ttk_improvement_hp = pivot_base.iloc[::-1] - pivot_hp.iloc[::-1]
        ttk_improvement_hp = ttk_improvement_hp.iloc[::-1]
        ttk_improvement_synth = pivot_base.iloc[::-1] - pivot_synth.iloc[::-1]
        ttk_improvement_synth = ttk_improvement_synth.iloc[::-1]
        
        # USE GLOBAL IMPROVEMENT SCALE (shared with 100HP, symmetric around 0)
        
        # 5. HP improvement
        ax5 = axes[1, 1]
        sns.heatmap(ttk_improvement_hp, annot=True, fmt='.0f', cmap='RdYlGn', center=0, ax=ax5,
                    vmin=global_imp_min, vmax=global_imp_max,
                    cbar_kws={'label': 'TTK Improvement (ms)'})
        ax5.set_title(f'Hollow Point vs Base - TTK Improvement [80 HP]', fontsize=14, fontweight='bold')
        ax5.set_xlabel('Range (m)', fontsize=12)
        ax5.set_ylabel('Number of Headshots', fontsize=12)
        
        # 6. Synthetic improvement
        ax6 = axes[1, 2]
        sns.heatmap(ttk_improvement_synth, annot=True, fmt='.0f', cmap='RdYlGn', center=0, ax=ax6,
                    vmin=global_imp_min, vmax=global_imp_max,
                    cbar_kws={'label': 'TTK Improvement (ms)'})
        ax6.set_title(f'Synthetic vs Base - TTK Improvement [80 HP]', fontsize=14, fontweight='bold')
        ax6.set_xlabel('Range (m)', fontsize=12)
        ax6.set_ylabel('Number of Headshots', fontsize=12)
        
    else:
        # 2x2 grid for weapons with HP only
        fig, axes = plt.subplots(2, 2, figsize=(16, 16))
        
        # Prepare TTK pivots
        pivot_base = df_results[df_results['Ammo'] == 'Base'].pivot(index='Headshots', columns='Range', values='TTK_ms')
        pivot_base = pivot_base.iloc[::-1]
        pivot_hp = df_results[df_results['Ammo'] == 'HP'].pivot(index='Headshots', columns='Range', values='TTK_ms')
        pivot_hp = pivot_hp.iloc[::-1]
        
        # USE GLOBAL COLOR SCALE (same as 100HP version)
        ttk_min = global_ttk_min
        ttk_max = global_ttk_max
        
        # Top Row: TTK Heatmaps
        # 1. Base ammo
        ax1 = axes[0, 0]
        sns.heatmap(pivot_base, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax1, 
                    vmin=ttk_min, vmax=ttk_max,
                    cbar_kws={'label': 'TTK (ms)'})
        ax1.set_title(f'{gun_name} - TTK with Base Ammo (1.34x HS) [80 HP]', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Range (m)', fontsize=12)
        ax1.set_ylabel('Number of Headshots', fontsize=12)
        
        # 2. HP ammo
        ax2 = axes[0, 1]
        sns.heatmap(pivot_hp, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax2, 
                    vmin=ttk_min, vmax=ttk_max,
                    cbar_kws={'label': 'TTK (ms)'})
        ax2.set_title(f'{gun_name} - TTK with Hollow Point (1.5x HS) [80 HP]', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Range (m)', fontsize=12)
        ax2.set_ylabel('Number of Headshots', fontsize=12)
        
        # Bottom Row: Improvements
        # 3. Blank for Base
        axes[1, 0].axis('off')
        
        # Calculate improvements
        ttk_improvement_hp = pivot_base.iloc[::-1] - pivot_hp.iloc[::-1]
        ttk_improvement_hp = ttk_improvement_hp.iloc[::-1]
        
        # 4. HP improvement
        ax4 = axes[1, 1]
        sns.heatmap(ttk_improvement_hp, annot=True, fmt='.0f', cmap='RdYlGn', center=0, ax=ax4,
                    vmin=global_imp_min, vmax=global_imp_max,
                    cbar_kws={'label': 'TTK Improvement (ms)'})
        ax4.set_title(f'Hollow Point vs Base - TTK Improvement [80 HP]', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Range (m)', fontsize=12)
        ax4.set_ylabel('Number of Headshots', fontsize=12)
    
    plt.tight_layout()
    output_path = f'visualizations/TTK_ANALYSIS_80HP/{weapon_class}/{gun_name}.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  Saved: {output_path} (color scale: {ttk_min:.0f}-{ttk_max:.0f}ms)")

print(f"\n{'='*80}")
print(f"COMPLETED: All 80HP TTK analyses with shared 100HP color scale")
print(f"{'='*80}\n")

