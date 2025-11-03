import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

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
df = df.dropna(subset=['DMG_Close', 'DMG_10M', 'DMG_75M', 'ROF', 'Ammo Type', 'Type'])

# Constants
BASE_HS_MULT = 1.34
HP_MULT = 1.5
SYNTH_MULT = 1.75
TARGET_HP = 100

# Extrapolate damage
def extrapolate_damage(dmg_close, dmg_10m, dmg_75m, target_range):
    if target_range <= 0:
        return dmg_close
    elif target_range <= 10:
        return np.interp(target_range, [0, 10], [dmg_close, dmg_10m])
    elif target_range <= 75:
        return np.interp(target_range, [10, 75], [dmg_10m, dmg_75m])
    else:
        slope = (dmg_75m - dmg_10m) / (75 - 10)
        dmg_100m = dmg_75m + slope * (100 - 75)
        dmg_100m = max(dmg_100m, 10)
        return np.interp(target_range, [75, 100], [dmg_75m, dmg_100m])

def find_max_range(dmg_close, dmg_10m, dmg_75m, num_hs, num_body, hs_mult):
    """Find maximum range for a kill combination"""
    for test_range in np.arange(0, 101, 0.1):
        dmg = extrapolate_damage(dmg_close, dmg_10m, dmg_75m, test_range)
        total_dmg = (dmg * hs_mult * num_hs) + (dmg * num_body)
        if total_dmg < TARGET_HP:
            return max(0, test_range - 0.1)
    return 100

def create_circle_plot(gun_name, weapon_class, dmg_close, dmg_10m, dmg_75m, ammo_type, num_hs, output_path):
    """Create a circle plot for a specific headshot scenario"""
    
    # Calculate ranges for each ammo type
    base_range = find_max_range(dmg_close, dmg_10m, dmg_75m, num_hs, 10, BASE_HS_MULT)
    hp_range = find_max_range(dmg_close, dmg_10m, dmg_75m, num_hs, 10, HP_MULT)
    synth_range = find_max_range(dmg_close, dmg_10m, dmg_75m, num_hs, 10, SYNTH_MULT) if ammo_type == 'Synthetic' else 0
    
    # Calculate percentage increases
    hp_increase = ((hp_range - base_range) / base_range * 100) if base_range > 0 else 0
    synth_increase = ((synth_range - base_range) / base_range * 100) if base_range > 0 and synth_range > 0 else 0
    
    # Create plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    ax.set_xlim(-110, 110)
    ax.set_ylim(-110, 110)
    ax.set_aspect('equal')
    
    # Plot circles (order: Synth, HP, Base, then dot on top) - FIXED: use facecolor instead of color
    if synth_range > 0:
        circle_synth = patches.Circle((0, 0), synth_range, facecolor='purple', alpha=0.3, linewidth=2, 
                                      edgecolor='purple', label=f'Synthetic: {synth_range:.1f}m (+{synth_increase:.0f}%)')
        ax.add_patch(circle_synth)
    
    circle_hp = patches.Circle((0, 0), hp_range, facecolor='orange', alpha=0.3, linewidth=2, 
                               edgecolor='orange', label=f'Hollow Point: {hp_range:.1f}m (+{hp_increase:.0f}%)')
    ax.add_patch(circle_hp)
    
    circle_base = patches.Circle((0, 0), base_range, facecolor='gray', alpha=0.5, linewidth=2, 
                                 edgecolor='black', label=f'Base: {base_range:.1f}m')
    ax.add_patch(circle_base)
    
    # Player position (smaller dot on top)
    player_dot = patches.Circle((0, 0), 2, facecolor='black', zorder=1000)
    ax.add_patch(player_dot)
    
    # Grid lines
    for distance in [25, 50, 75, 100]:
        circle = patches.Circle((0, 0), distance, fill=False, color='white', 
                               linestyle='--', alpha=0.2, linewidth=0.5)
        ax.add_patch(circle)
        ax.text(0, distance + 3, f'{distance}m', ha='center', va='bottom', 
               color='white', fontsize=8, alpha=0.5)
    
    # Crosshairs
    ax.axhline(y=0, color='white', linestyle='--', alpha=0.2, linewidth=0.5)
    ax.axvline(x=0, color='white', linestyle='--', alpha=0.2, linewidth=0.5)
    
    # Title and labels
    hs_text = f"{num_hs} Incidental Headshot" if num_hs == 1 else f"{num_hs} Headshots"
    ax.set_title(f'{gun_name} - Effective Range ({hs_text})\n{weapon_class}', 
                fontsize=16, fontweight='bold', color='white', pad=20)
    ax.set_xlabel('Distance (meters)', fontsize=12, color='white')
    ax.set_ylabel('Distance (meters)', fontsize=12, color='white')
    
    # Legend
    ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    # Style
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#16213e')
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#16213e')
    plt.close()

# Create output directory
os.makedirs('visualizations/INDIVIDUAL_WEAPONS', exist_ok=True)

print(f"\n{'='*80}")
print(f"GENERATING INDIVIDUAL WEAPON RANGE CIRCLES (MULTI-HS VERSIONS)")
print(f"{'='*80}\n")

# Process each weapon
for idx, weapon_row in df.iterrows():
    gun_name = weapon_row['Gun']
    weapon_class = weapon_row['Type']
    dmg_close = float(weapon_row['DMG_Close'])
    dmg_10m = float(weapon_row['DMG_10M'])
    dmg_75m = float(weapon_row['DMG_75M'])
    ammo_type = weapon_row['Ammo Type']
    
    print(f"Processing: {gun_name} (Base DMG: {dmg_close})")
    
    # Always create 1HS and 2HS versions
    create_circle_plot(gun_name, weapon_class, dmg_close, dmg_10m, dmg_75m, ammo_type, 1, 
                      f'visualizations/INDIVIDUAL_WEAPONS/{gun_name}_1HS.png')
    print(f"  Saved: {gun_name}_1HS.png")
    
    create_circle_plot(gun_name, weapon_class, dmg_close, dmg_10m, dmg_75m, ammo_type, 2, 
                      f'visualizations/INDIVIDUAL_WEAPONS/{gun_name}_2HS.png')
    print(f"  Saved: {gun_name}_2HS.png")
    
    # Create 3HS version for weapons with < 25 damage
    if dmg_close < 25:
        create_circle_plot(gun_name, weapon_class, dmg_close, dmg_10m, dmg_75m, ammo_type, 3, 
                          f'visualizations/INDIVIDUAL_WEAPONS/{gun_name}_3HS.png')
        print(f"  Saved: {gun_name}_3HS.png")

print(f"\n{'='*80}")
print(f"COMPLETED: All individual weapon range circles saved")
print(f"{'='*80}\n")

