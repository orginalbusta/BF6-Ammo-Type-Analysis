import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

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

# Focus on DRS-IAR
gun_name = 'DRS-IAR'

print(f"\n{'='*80}")
print(f"TTK ANALYSIS: {gun_name}")
print(f"{'='*80}\n")

# Get weapon data
gun_falloff = falloff_df[falloff_df['Gun'] == gun_name].iloc[0]
gun_weapon = weapon_df[weapon_df['Gun'] == gun_name].iloc[0]
gun_ammo = ammo_df[ammo_df['Gun'] == gun_name].iloc[0]

dmg_close = float(gun_falloff['DMG_Close'])
dmg_10m = float(gun_falloff['DMG_10M'])
dmg_75m = float(gun_falloff['DMG_75M'])
rof = float(gun_falloff['ROF'])
ammo_type = gun_ammo['Ammo Type']

print(f"Weapon Stats:")
print(f"  Base Damage: {dmg_close}")
print(f"  Damage at 10m: {dmg_10m}")
print(f"  Damage at 75m: {dmg_75m}")
print(f"  Rate of Fire: {rof} RPM")
print(f"  Ammo Type: {ammo_type}")
print(f"  Time between shots: {60/rof*1000:.1f}ms\n")

# Extrapolate damage to more ranges
def extrapolate_damage(dmg_10m, dmg_75m, target_range):
    """Linear extrapolation"""
    if target_range <= 10:
        return dmg_10m
    damage_loss_per_meter = (dmg_10m - dmg_75m) / (75 - 10)
    return max(dmg_75m - (damage_loss_per_meter * (target_range - 75)), 10)

# Define ranges to analyze
ranges = [0, 10, 20, 30, 40, 50, 60, 75, 100]

# Get damage at each range
damage_at_range = {}
for r in ranges:
    if r == 0:
        damage_at_range[r] = dmg_close
    elif r == 10:
        damage_at_range[r] = dmg_10m
    elif r == 75:
        damage_at_range[r] = dmg_75m
    elif r < 10:
        damage_at_range[r] = dmg_close
    elif r < 75:
        # Interpolate between 10m and 75m
        frac = (r - 10) / (75 - 10)
        damage_at_range[r] = dmg_10m - (frac * (dmg_10m - dmg_75m))
    else:
        damage_at_range[r] = extrapolate_damage(dmg_10m, dmg_75m, r)

# Multipliers
BASE_MULT = 1.34
HP_MULT = 1.5
SYNTH_MULT = 1.75

# Maximum headshots to consider (up to 8 shots total scenario)
max_headshots = 5

# Calculate STK and TTK for each combination
results = []

for range_m in ranges:
    body_dmg = damage_at_range[range_m]
    
    for num_hs in range(0, max_headshots + 1):
        # Calculate for each ammo type
        for ammo, mult in [('Base', BASE_MULT), ('HP', HP_MULT), ('Synth', SYNTH_MULT)]:
            # Skip Synth if weapon doesn't have access
            if ammo == 'Synth' and ammo_type != 'Synthetic':
                continue
            
            hs_dmg = body_dmg * mult
            
            # Calculate minimum body shots needed
            # Total damage = (hs_dmg * num_hs) + (body_dmg * num_body) >= 100
            # num_body = ceil((100 - hs_dmg * num_hs) / body_dmg)
            
            damage_from_hs = hs_dmg * num_hs
            if damage_from_hs >= 100:
                # Headshots alone are enough
                stk = num_hs
                num_body = 0
            else:
                remaining_damage = 100 - damage_from_hs
                num_body = int(np.ceil(remaining_damage / body_dmg))
                stk = num_hs + num_body
            
            # TTK = (STK - 1) * (60 / ROF) seconds = (STK - 1) * (60000 / ROF) milliseconds
            ttk_ms = (stk - 1) * (60000 / rof)
            
            results.append({
                'Range': range_m,
                'Headshots': num_hs,
                'Ammo': ammo,
                'Body_Dmg': body_dmg,
                'HS_Dmg': hs_dmg,
                'Num_Body': num_body,
                'STK': stk,
                'TTK_ms': ttk_ms
            })

df_results = pd.DataFrame(results)

# For each range and headshot combo, find the best ammo type
print(f"\n{'='*80}")
print(f"TTK COMPARISON (milliseconds)")
print(f"{'='*80}\n")

for range_m in ranges:
    print(f"\n--- {range_m}m ---")
    df_range = df_results[df_results['Range'] == range_m]
    
    for num_hs in range(0, max_headshots + 1):
        df_combo = df_range[df_range['Headshots'] == num_hs]
        
        if len(df_combo) == 0:
            continue
        
        base_row = df_combo[df_combo['Ammo'] == 'Base'].iloc[0]
        hp_row = df_combo[df_combo['Ammo'] == 'HP'].iloc[0]
        
        base_ttk = base_row['TTK_ms']
        hp_ttk = hp_row['TTK_ms']
        
        base_stk = base_row['STK']
        hp_stk = hp_row['STK']
        
        hp_improvement = base_ttk - hp_ttk
        
        if ammo_type == 'Synthetic':
            synth_row = df_combo[df_combo['Ammo'] == 'Synth'].iloc[0]
            synth_ttk = synth_row['TTK_ms']
            synth_stk = synth_row['STK']
            synth_improvement = base_ttk - synth_ttk
            
            best_ammo = 'Base'
            best_ttk = base_ttk
            if hp_ttk < best_ttk:
                best_ammo = 'HP'
                best_ttk = hp_ttk
            if synth_ttk < best_ttk:
                best_ammo = 'Synth'
                best_ttk = synth_ttk
            
            print(f"{num_hs}HS: Base {base_stk}shot/{base_ttk:.0f}ms | HP {hp_stk}shot/{hp_ttk:.0f}ms ({hp_improvement:+.0f}ms) | "
                  f"Synth {synth_stk}shot/{synth_ttk:.0f}ms ({synth_improvement:+.0f}ms) | BEST: {best_ammo}")
        else:
            best_ammo = 'HP' if hp_ttk < base_ttk else 'Base'
            print(f"{num_hs}HS: Base {base_stk}shot/{base_ttk:.0f}ms | HP {hp_stk}shot/{hp_ttk:.0f}ms ({hp_improvement:+.0f}ms) | BEST: {best_ammo}")

# Create visualizations
if ammo_type == 'Synthetic':
    # 2x3 grid for weapons with Synthetic access
    # Top row: TTK for each ammo type
    # Bottom row: TTK improvements (blank for Base, HP improvement, Synth improvement)
    fig, axes = plt.subplots(2, 3, figsize=(24, 16))
    
    # Top Row: TTK Heatmaps
    # 1. Heatmap: TTK for Base ammo
    ax1 = axes[0, 0]
    pivot_base = df_results[df_results['Ammo'] == 'Base'].pivot(index='Headshots', columns='Range', values='TTK_ms')
    pivot_base = pivot_base.iloc[::-1]  # Flip y-axis
    sns.heatmap(pivot_base, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax1, cbar_kws={'label': 'TTK (ms)'})
    ax1.set_title(f'{gun_name} - TTK with Base Ammo (1.34x HS)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Range (m)', fontsize=12)
    ax1.set_ylabel('Number of Headshots', fontsize=12)
    
    # 2. Heatmap: TTK for HP ammo
    ax2 = axes[0, 1]
    pivot_hp = df_results[df_results['Ammo'] == 'HP'].pivot(index='Headshots', columns='Range', values='TTK_ms')
    pivot_hp = pivot_hp.iloc[::-1]  # Flip y-axis
    sns.heatmap(pivot_hp, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax2, cbar_kws={'label': 'TTK (ms)'})
    ax2.set_title(f'{gun_name} - TTK with Hollow Point (1.5x HS)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Range (m)', fontsize=12)
    ax2.set_ylabel('Number of Headshots', fontsize=12)
    
    # 3. Heatmap: TTK for Synthetic ammo
    ax3 = axes[0, 2]
    pivot_synth = df_results[df_results['Ammo'] == 'Synth'].pivot(index='Headshots', columns='Range', values='TTK_ms')
    pivot_synth = pivot_synth.iloc[::-1]  # Flip y-axis
    sns.heatmap(pivot_synth, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax3, cbar_kws={'label': 'TTK (ms)'})
    ax3.set_title(f'{gun_name} - TTK with Synthetic (1.75x HS)', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Range (m)', fontsize=12)
    ax3.set_ylabel('Number of Headshots', fontsize=12)
    
    # Bottom Row: Improvements (Base has no improvement to show, so hide it)
    # 4. Hide the bottom-left subplot (Base has nothing to compare against)
    axes[1, 0].axis('off')
    
    # 5. Heatmap: TTK improvement (Base - HP)
    ax5 = axes[1, 1]
    ttk_improvement_hp = pivot_base.iloc[::-1] - pivot_hp.iloc[::-1]  # Both already flipped, so flip back
    ttk_improvement_hp = ttk_improvement_hp.iloc[::-1]  # Then flip result
    sns.heatmap(ttk_improvement_hp, annot=True, fmt='.0f', cmap='RdYlGn', center=0, ax=ax5, 
                cbar_kws={'label': 'TTK Reduction (ms)'})
    ax5.set_title(f'{gun_name} - TTK Improvement: HP vs Base', fontsize=14, fontweight='bold')
    ax5.set_xlabel('Range (m)', fontsize=12)
    ax5.set_ylabel('Number of Headshots', fontsize=12)
    
    # 6. Heatmap: TTK improvement (Base - Synthetic)
    ax6 = axes[1, 2]
    ttk_improvement_synth = pivot_base.iloc[::-1] - pivot_synth.iloc[::-1]
    ttk_improvement_synth = ttk_improvement_synth.iloc[::-1]
    sns.heatmap(ttk_improvement_synth, annot=True, fmt='.0f', cmap='RdYlGn', center=0, ax=ax6, 
                cbar_kws={'label': 'TTK Reduction (ms)'})
    ax6.set_title(f'{gun_name} - TTK Improvement: Synthetic vs Base', fontsize=14, fontweight='bold')
    ax6.set_xlabel('Range (m)', fontsize=12)
    ax6.set_ylabel('Number of Headshots', fontsize=12)
    
else:
    # 2x2 grid for weapons with only HP
    # Top row: Base TTK, HP TTK
    # Bottom row: (blank), HP improvement
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    
    # 1. Heatmap: TTK for Base ammo
    ax1 = axes[0, 0]
    pivot_base = df_results[df_results['Ammo'] == 'Base'].pivot(index='Headshots', columns='Range', values='TTK_ms')
    pivot_base = pivot_base.iloc[::-1]  # Flip y-axis
    sns.heatmap(pivot_base, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax1, cbar_kws={'label': 'TTK (ms)'})
    ax1.set_title(f'{gun_name} - TTK with Base Ammo (1.34x HS)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Range (m)', fontsize=12)
    ax1.set_ylabel('Number of Headshots', fontsize=12)
    
    # 2. Heatmap: TTK for HP ammo
    ax2 = axes[0, 1]
    pivot_hp = df_results[df_results['Ammo'] == 'HP'].pivot(index='Headshots', columns='Range', values='TTK_ms')
    pivot_hp = pivot_hp.iloc[::-1]  # Flip y-axis
    sns.heatmap(pivot_hp, annot=True, fmt='.0f', cmap='RdYlGn_r', ax=ax2, cbar_kws={'label': 'TTK (ms)'})
    ax2.set_title(f'{gun_name} - TTK with Hollow Point (1.5x HS)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Range (m)', fontsize=12)
    ax2.set_ylabel('Number of Headshots', fontsize=12)
    
    # 3. Hide the bottom-left subplot (Base has nothing to compare against)
    axes[1, 0].axis('off')
    
    # 4. Heatmap: TTK improvement (Base - HP)
    ax4 = axes[1, 1]
    ttk_improvement = pivot_base.iloc[::-1] - pivot_hp.iloc[::-1]
    ttk_improvement = ttk_improvement.iloc[::-1]
    sns.heatmap(ttk_improvement, annot=True, fmt='.0f', cmap='RdYlGn', center=0, ax=ax4, 
                cbar_kws={'label': 'TTK Reduction (ms)'})
    ax4.set_title(f'{gun_name} - TTK Improvement: HP vs Base', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Range (m)', fontsize=12)
    ax4.set_ylabel('Number of Headshots', fontsize=12)

plt.tight_layout()
plt.savefig(f'visualizations/TTK_Analysis_{gun_name}.png', dpi=300, bbox_inches='tight')
print(f"\n{'='*80}")
print(f"Saved: visualizations/TTK_Analysis_{gun_name}.png")
print(f"{'='*80}\n")

# Save detailed results
df_results.to_csv(f'analysis_results/TTK_Analysis_{gun_name}.csv', index=False)
print(f"Saved: analysis_results/TTK_Analysis_{gun_name}.csv")

