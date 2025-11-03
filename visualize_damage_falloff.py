import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read falloff data
falloff_df = pd.read_csv('data/Battlefield 6 Damage Fall Off - V2.csv', skiprows=1)

# Clean up column names
falloff_df = falloff_df.rename(columns={
    'Gun (!!! -> Missing)': 'Gun',
    'Dmg': 'DMG_Close',
    '10m': 'DMG_10M',
    '75m': 'DMG_75M'
})

# Filter out summary rows and guns we don't want
exclude_guns = ['MIN', 'MAX', 'AVG']
exclude_types = ['DMR', 'Shotgun', 'Handgun']
df = falloff_df[~falloff_df['Gun'].isin(exclude_guns) & ~falloff_df['Type'].isin(exclude_types)].copy()

# Parse damage values
df['DMG_Close'] = pd.to_numeric(df['DMG_Close'], errors='coerce')
df['DMG_10M'] = pd.to_numeric(df['DMG_10M'], errors='coerce')
df['DMG_75M'] = pd.to_numeric(df['DMG_75M'], errors='coerce')

# Remove any rows with missing data
df = df.dropna(subset=['DMG_Close', 'DMG_10M', 'DMG_75M'])

print(f"Visualizing damage falloff for {len(df)} weapons")
print("="*80)

# Color scheme
type_colors = {
    'Assault Rifle': '#FF6B6B',
    'Carbine': '#4ECDC4', 
    'LMG': '#95E1D3',
    'SMG': '#FFD93D'
}

def extrapolate_damage(dmg_10m, dmg_75m, target_range):
    """Linearly extrapolate damage to a target range based on 10m-75m falloff rate"""
    # Calculate damage loss per meter from 10m to 75m
    damage_loss_per_meter = (dmg_10m - dmg_75m) / (75 - 10)
    
    # Extrapolate from 75m to target range
    range_beyond_75 = target_range - 75
    extrapolated_dmg = dmg_75m - (damage_loss_per_meter * range_beyond_75)
    
    # Don't let damage go below 10 (reasonable minimum)
    return max(extrapolated_dmg, 10)

# === CREATE VISUALIZATION BY WEAPON TYPE ===
fig, axes = plt.subplots(2, 2, figsize=(20, 16))
axes = axes.flatten()

weapon_types = ['Assault Rifle', 'Carbine', 'LMG', 'SMG']

for idx, weapon_type in enumerate(weapon_types):
    ax = axes[idx]
    df_type = df[df['Type'] == weapon_type].copy()
    
    print(f"\n{weapon_type}s: {len(df_type)} weapons")
    
    for _, row in df_type.iterrows():
        gun = row['Gun']
        dmg_close = row['DMG_Close']
        dmg_10m = row['DMG_10M']
        dmg_75m = row['DMG_75M']
        
        # Actual data points
        ranges_actual = [0, 10, 75]
        damages_actual = [dmg_close, dmg_10m, dmg_75m]
        
        # Extrapolated data points
        ranges_extrapolated = [75, 85, 100]
        dmg_85m = extrapolate_damage(dmg_10m, dmg_75m, 85)
        dmg_100m = extrapolate_damage(dmg_10m, dmg_75m, 100)
        damages_extrapolated = [dmg_75m, dmg_85m, dmg_100m]
        
        color = type_colors.get(weapon_type, 'gray')
        
        # Plot actual data (solid line)
        ax.plot(ranges_actual, damages_actual, 
                marker='o', linewidth=2, markersize=6, 
                label=gun, color=color, alpha=0.7)
        
        # Plot extrapolated data (dashed line)
        ax.plot(ranges_extrapolated, damages_extrapolated,
                linestyle='--', linewidth=2, color=color, alpha=0.4)
        
        print(f"  {gun:20} | Close: {dmg_close:.0f} | 10m: {dmg_10m:.0f} | "
              f"75m: {dmg_75m:.0f} | 100m (est): {dmg_100m:.1f}")
    
    # Add vertical line at 75m to show where extrapolation begins
    ax.axvline(x=75, color='red', linestyle=':', linewidth=2, alpha=0.5, label='Extrapolation starts')
    
    ax.set_xlabel('Range (meters)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Damage per Shot', fontsize=13, fontweight='bold')
    ax.set_title(f'{weapon_type} Damage Falloff', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-2, 105)
    ax.set_ylim(10, max(df_type['DMG_Close'].max() + 5, 40))
    
    # Add legend (but make it smaller if too many weapons)
    if len(df_type) <= 8:
        ax.legend(fontsize=9, loc='best', framealpha=0.9)
    else:
        ax.legend(fontsize=7, loc='best', ncol=2, framealpha=0.9)
    
    # Add annotation
    ax.text(0.02, 0.98, 'Solid line = Actual data\nDashed line = Extrapolated',
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.suptitle('Weapon Damage Falloff: Actual Data (0m-75m) + Extrapolation (75m-100m)',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('visualizations/Damage_Falloff_By_Type.png', dpi=300, bbox_inches='tight')
print(f"\n{'='*80}")
print("Saved: visualizations/Damage_Falloff_By_Type.png")

# === CREATE INDIVIDUAL WEAPON COMPARISON ===
# Group weapons by base damage to make comparison easier
df['DMG_Group'] = df['DMG_Close'].apply(lambda x: f"{int(x)} DMG")
damage_groups = df['DMG_Group'].unique()

print(f"\n{'='*80}")
print("Creating damage group comparisons...")

for dmg_group in sorted(damage_groups):
    df_group = df[df['DMG_Group'] == dmg_group].copy()
    
    if len(df_group) == 0:
        continue
    
    print(f"\n{dmg_group} Weapons: {len(df_group)}")
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for _, row in df_group.iterrows():
        gun = row['Gun']
        weapon_type = row['Type']
        dmg_close = row['DMG_Close']
        dmg_10m = row['DMG_10M']
        dmg_75m = row['DMG_75M']
        
        # Actual data points
        ranges_actual = [0, 10, 75]
        damages_actual = [dmg_close, dmg_10m, dmg_75m]
        
        # Extrapolated data points
        ranges_extrapolated = [75, 85, 100]
        dmg_85m = extrapolate_damage(dmg_10m, dmg_75m, 85)
        dmg_100m = extrapolate_damage(dmg_10m, dmg_75m, 100)
        damages_extrapolated = [dmg_75m, dmg_85m, dmg_100m]
        
        color = type_colors.get(weapon_type, 'gray')
        
        # Plot actual data (solid line with markers)
        ax.plot(ranges_actual, damages_actual, 
                marker='o', linewidth=2.5, markersize=8, 
                label=f"{gun} ({weapon_type})", color=color, alpha=0.8)
        
        # Plot extrapolated data (dashed line, no markers)
        ax.plot(ranges_extrapolated, damages_extrapolated,
                linestyle='--', linewidth=2.5, color=color, alpha=0.5)
    
    # Add vertical line at 75m
    ax.axvline(x=75, color='red', linestyle=':', linewidth=3, alpha=0.6, 
               label='Data ends / Extrapolation begins')
    
    # Add horizontal line at 100 HP for reference
    ax.axhline(y=25, color='green', linestyle='-.', linewidth=2, alpha=0.4,
               label='25 Damage (4-shot kill reference)')
    ax.axhline(y=33.33, color='orange', linestyle='-.', linewidth=2, alpha=0.4,
               label='33.33 Damage (3-shot kill reference)')
    
    ax.set_xlabel('Range (meters)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Damage per Shot', fontsize=13, fontweight='bold')
    ax.set_title(f'{dmg_group} Weapons: Damage Falloff Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-2, 105)
    
    # Set y-axis to show full range
    y_min = min(df_group['DMG_75M'].min() - 3, 10)
    y_max = df_group['DMG_Close'].max() + 3
    ax.set_ylim(y_min, y_max)
    
    ax.legend(fontsize=10, loc='best', framealpha=0.9)
    
    # Add annotation
    ax.text(0.02, 0.98, 'Solid line = Actual data\nDashed line = Linear extrapolation',
            transform=ax.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
    
    plt.tight_layout()
    
    # Create safe filename
    safe_dmg_group = dmg_group.replace(' ', '_')
    plt.savefig(f'visualizations/Damage_Falloff_{safe_dmg_group}.png', dpi=300, bbox_inches='tight')
    print(f"Saved: visualizations/Damage_Falloff_{safe_dmg_group}.png")
    plt.close()

print(f"\n{'='*80}")
print("ALL DAMAGE FALLOFF VISUALIZATIONS COMPLETE!")
print("="*80)

