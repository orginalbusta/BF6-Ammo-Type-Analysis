import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import os

# Read data
falloff_df = pd.read_csv('data/Battlefield 6 Damage Fall Off - V2.csv', skiprows=1)
ammo_df = pd.read_csv('analysis_results/Weapon_Ammo_Types.csv')
stk_df = pd.read_csv('analysis_results/STK_Categorization_One_Headshot.csv')

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

# Convert to numeric and add extrapolated 100m damage
df['DMG_Close'] = pd.to_numeric(df['DMG_Close'], errors='coerce')
df['DMG_10M'] = pd.to_numeric(df['DMG_10M'], errors='coerce')
df['DMG_75M'] = pd.to_numeric(df['DMG_75M'], errors='coerce')

def extrapolate_damage_100m(dmg_10m, dmg_75m):
    """Linearly extrapolate damage to 100m"""
    damage_loss_per_meter = (dmg_10m - dmg_75m) / (75 - 10)
    range_beyond_75 = 100 - 75
    extrapolated_dmg = dmg_75m - (damage_loss_per_meter * range_beyond_75)
    return max(extrapolated_dmg, 10)

df['DMG_100M'] = df.apply(lambda row: extrapolate_damage_100m(row['DMG_10M'], row['DMG_75M']), axis=1)

df = df.merge(ammo_df[['Gun', 'Ammo Type']], on='Gun', how='left')

# Merge with STK data
stk_temp = stk_df[['Gun', 'STK at 20M']].copy()
df = df.merge(stk_temp, on='Gun', how='left')

df = df.dropna(subset=['DMG_Close', 'DMG_10M', 'DMG_75M', 'ROF', 'Ammo Type', 'Type', 'STK at 20M'])

# Constants
BASE_HS_MULT = 1.34
HP_MULT = 1.5
SYNTH_MULT = 1.75
TARGET_HP = 100

def interpolate_max_range_100m(row, multiplier, num_hs, num_body):
    """Interpolate to find exact range where N HS + M Body = 100 damage - EXACT COPY from working code"""
    
    dmg_close = row['DMG_Close']
    dmg_10m = row['DMG_10M']
    dmg_75m = row['DMG_75M']
    dmg_100m = row['DMG_100M']
    
    if pd.isna(dmg_close) or pd.isna(dmg_10m) or pd.isna(dmg_75m) or pd.isna(dmg_100m):
        return 0
    
    def calc_damage(hs_dmg, body_dmg):
        return (hs_dmg * num_hs) + (body_dmg * num_body)
    
    ranges = [
        (0, 10, dmg_close, dmg_10m),
        (10, 75, dmg_10m, dmg_75m),
        (75, 100, dmg_75m, dmg_100m)
    ]
    
    max_range = 0
    
    for start_range, end_range, start_dmg, end_dmg in ranges:
        hs_dmg_end = end_dmg * multiplier
        total_dmg_end = calc_damage(hs_dmg_end, end_dmg)
        
        if total_dmg_end >= TARGET_HP:
            max_range = end_range
        else:
            hs_dmg_start = start_dmg * multiplier
            total_dmg_start = calc_damage(hs_dmg_start, start_dmg)
            
            if total_dmg_start >= TARGET_HP:
                # Target is somewhere in this range, interpolate
                for test_range in np.arange(start_range, end_range + 0.1, 0.1):
                    ratio = (test_range - start_range) / (end_range - start_range)
                    interpolated_dmg = start_dmg + (end_dmg - start_dmg) * ratio
                    hs_dmg = interpolated_dmg * multiplier
                    total_dmg = calc_damage(hs_dmg, interpolated_dmg)
                    
                    if total_dmg < TARGET_HP:
                        max_range = max(0, test_range - 0.1)
                        break
                else:
                    max_range = end_range
                break
    
    return max_range

def create_circle_plot(gun_name, weapon_class, row, ammo_type, num_hs, output_path):
    """Create a single circle plot for a weapon"""
    
    # Get actual STK from data
    stk = int(row['STK at 20M'])
    num_body = stk - num_hs
    
    if num_body < 0:
        # Not enough shots for this many headshots
        return False
    
    # Calculate ranges
    base_range = interpolate_max_range_100m(row, BASE_HS_MULT, num_hs, num_body)
    hp_range = interpolate_max_range_100m(row, HP_MULT, num_hs, num_body)
    synth_range = interpolate_max_range_100m(row, SYNTH_MULT, num_hs, num_body)
    
    # Calculate extensions
    hp_extension = hp_range - base_range
    synth_extension = synth_range - base_range
    hp_pct = (hp_extension / base_range * 100) if base_range > 0 else 0
    synth_pct = (synth_extension / base_range * 100) if base_range > 0 else 0
    
    # Create plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    
    # Draw circles from bottom to top: Synthetic (bottom), HP, Base, then center dot (top)
    # Using the exact same approach as visualize_by_weapon_class.py
    if synth_range > 0 and ammo_type == 'Synthetic':
        circle_synth = Circle((0, 0), synth_range,
                             facecolor='#B8A0D0',  # Desaturated purple
                             alpha=0.3, linewidth=1.5, edgecolor='#9B7FB8',
                             linestyle='-',
                             label=f'Synthetic: {synth_range:.1f}m (+{synth_pct:.0f}%)',
                             zorder=1)
        ax.add_patch(circle_synth)
    
    if hp_range > 0:
        circle_hp = Circle((0, 0), hp_range,
                          facecolor='#E0A870',  # Desaturated orange
                          alpha=0.5, linewidth=1.5, edgecolor='#C89050',
                          label=f'Hollow Point: {hp_range:.1f}m (+{hp_pct:.0f}%)',
                          zorder=2)
        ax.add_patch(circle_hp)
    
    if base_range > 0:
        circle_base = Circle((0, 0), base_range,
                            facecolor='#A0A0A0',  # Slightly lighter gray
                            alpha=0.7, linewidth=1.5, edgecolor='#606060',
                            label=f'Base: {base_range:.1f}m',
                            zorder=3)
        ax.add_patch(circle_base)
    
    # Center dot on top with smaller size
    ax.plot(0, 0, 'ko', markersize=5, zorder=100)
    
    # Set limits
    max_range = 100
    ax.set_xlim(-max_range*1.2, max_range*1.2)
    ax.set_ylim(-max_range*1.2, max_range*1.2)
    ax.set_aspect('equal')
    
    # Grid and labels
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('Distance (m)', fontsize=12)
    ax.set_ylabel('Distance (m)', fontsize=12)
    
    # Title
    hs_text = f"{num_hs} Incidental Headshot" if num_hs == 1 else f"{num_hs} Headshots"
    title = f"{gun_name} - Effective Range ({hs_text})\n{weapon_class} | {ammo_type}"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    
    # Legend
    if base_range > 0 or hp_range > 0 or synth_range > 0:
        ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return True

# Create output directory
os.makedirs('visualizations/INDIVIDUAL_WEAPONS', exist_ok=True)

print(f"\n{'='*80}")
print(f"GENERATING INDIVIDUAL WEAPON RANGE CIRCLES (FIXED)")
print(f"{'='*80}\n")

# Process each weapon
for idx, weapon_row in df.iterrows():
    gun_name = weapon_row['Gun']
    weapon_class = weapon_row['Type']
    ammo_type = weapon_row['Ammo Type']
    base_dmg = weapon_row['DMG_Close']
    
    print(f"Processing: {gun_name} (Base DMG: {base_dmg})")
    
    # Always create 1HS and 2HS versions
    result = create_circle_plot(gun_name, weapon_class, weapon_row, ammo_type, 1, 
                      f'visualizations/INDIVIDUAL_WEAPONS/{gun_name}_1HS.png')
    if result is not False:
        print(f"  Saved: {gun_name}_1HS.png")
    
    result = create_circle_plot(gun_name, weapon_class, weapon_row, ammo_type, 2, 
                      f'visualizations/INDIVIDUAL_WEAPONS/{gun_name}_2HS.png')
    if result is not False:
        print(f"  Saved: {gun_name}_2HS.png")
    
    # Create 3HS version for weapons with < 25 damage
    if base_dmg < 25:
        result = create_circle_plot(gun_name, weapon_class, weapon_row, ammo_type, 3, 
                          f'visualizations/INDIVIDUAL_WEAPONS/{gun_name}_3HS.png')
        if result is not False:
            print(f"  Saved: {gun_name}_3HS.png")

print(f"\n{'='*80}")
print(f"COMPLETED: All individual weapon range circles saved")
print(f"{'='*80}\n")

