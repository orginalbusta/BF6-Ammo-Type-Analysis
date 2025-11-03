import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

# Read data
weapon_df = pd.read_csv('data/BF6 DPS Chart v2.1 _SEASON 1 UPDATES_.xlsx - All Guns by Weapon Type.csv')
ammo_df = pd.read_csv('Weapon_Ammo_Types.csv')
stk_df = pd.read_csv('STK_Categorization_One_Headshot.csv')

# Merge data
df = weapon_df.merge(ammo_df[['Gun', 'Ammo Type', 'Actual Multiplier']], on='Gun', how='left')

# Get 3-shot kill weapons at 20M
three_shot_weapons = stk_df[stk_df['STK at 20M'] == 3]['Gun'].tolist()
df_3shot = df[df['Gun'].isin(three_shot_weapons)].copy()

print(f"\n3-Shot Kill Weapons (2 HS + 1 Body): {len(df_3shot)}")
print("="*80)

# Parse damage values
df_3shot['DMG_10M'] = pd.to_numeric(df_3shot['DMG at 10M'], errors='coerce')
df_3shot['DMG_20M'] = pd.to_numeric(df_3shot['DMG at 20M'], errors='coerce')
df_3shot['DMG_35M'] = pd.to_numeric(df_3shot['DMG at 35M'], errors='coerce')
df_3shot['HS_Multiplier'] = pd.to_numeric(df_3shot['Actual Multiplier'], errors='coerce')

BASE_HS_MULT = 1.34
HP_MULT = 1.5
SYNTH_MULT = 1.75

def calc_damage_3shot(hs_dmg, body_dmg):
    """Calculate total damage for 2 HS + 1 Body"""
    return (hs_dmg * 2) + body_dmg

def interpolate_max_range(row, multiplier):
    """Interpolate to find the exact range where 2 HS + 1 Body = 100 damage"""
    
    # Check each range bracket
    ranges = [(0, 10, row['DMG_10M']), 
              (10, 20, row['DMG_20M']), 
              (20, 35, row['DMG_35M'])]
    
    max_range = 0
    
    for start_range, end_range, end_dmg in ranges:
        if pd.isna(end_dmg):
            continue
            
        hs_dmg = end_dmg * multiplier
        total_dmg = calc_damage_3shot(hs_dmg, end_dmg)
        
        if total_dmg >= 100:
            max_range = end_range
        else:
            # If we can't kill at this range, try to interpolate within the previous bracket
            if max_range > 0:
                # Get previous range data
                if end_range == 20:
                    prev_dmg = row['DMG_10M']
                    prev_range = 10
                elif end_range == 35:
                    prev_dmg = row['DMG_20M']
                    prev_range = 20
                else:
                    continue
                
                # Interpolate to find where we cross 100 HP threshold
                prev_hs = prev_dmg * multiplier
                prev_total = calc_damage_3shot(prev_hs, prev_dmg)
                
                if prev_total >= 100 and total_dmg < 100:
                    # Linear interpolation between the two points
                    # We need to find where total damage = 100
                    range_diff = end_range - prev_range
                    damage_diff = prev_total - total_dmg
                    
                    if damage_diff > 0:
                        # How much damage do we need to lose to reach exactly 100?
                        damage_to_lose = prev_total - 100
                        fraction = damage_to_lose / damage_diff
                        interpolated_range = prev_range + (range_diff * fraction)
                        return interpolated_range
            
            break
    
    return max_range

# Calculate ranges for each weapon
results = []

for idx, row in df_3shot.iterrows():
    gun = row['Gun']
    weapon_type = row['Type']
    ammo_type = row['Ammo Type']
    
    base_range = interpolate_max_range(row, BASE_HS_MULT)
    hp_range = interpolate_max_range(row, HP_MULT)
    synth_range = interpolate_max_range(row, SYNTH_MULT)
    
    results.append({
        'Gun': gun,
        'Type': weapon_type,
        'Ammo Type': ammo_type,
        'Base Range (1.34x)': base_range,
        'HP Range (1.5x)': hp_range,
        'Synthetic Range (1.75x)': synth_range,
        'HP Extension': hp_range - base_range,
        'Synth Extension': synth_range - base_range
    })
    
    print(f"{gun:15} ({weapon_type:3}) | {ammo_type:13} | "
          f"Base: {base_range:.1f}m | HP: {hp_range:.1f}m (+{hp_range-base_range:.1f}m) | "
          f"Synth: {synth_range:.1f}m (+{synth_range-base_range:.1f}m)")

df_results = pd.DataFrame(results)
df_results.to_csv('visualizations/3Shot_Range_Analysis.csv', index=False)

# === CREATE VISUALIZATION ===
num_weapons = len(df_results)
cols = 2
rows = (num_weapons + cols - 1) // cols

fig, axes = plt.subplots(rows, cols, figsize=(16, 8*rows))
if num_weapons == 1:
    axes = [axes]
else:
    axes = axes.flatten()

# Color scheme
type_colors = {
    'AR': '#FF6B6B',
    'CARBINE': '#4ECDC4', 
    'LMG': '#95E1D3',
    'SMG': '#FFD93D'
}

for idx, (ax, row_tuple) in enumerate(zip(axes, df_results.iterrows())):
    if idx >= num_weapons:
        ax.axis('off')
        continue
    
    _, data = row_tuple
    gun = data['Gun']
    weapon_type = data['Type']
    ammo_type = data['Ammo Type']
    base_range = data['Base Range (1.34x)']
    hp_range = data['HP Range (1.5x)']
    synth_range = data['Synthetic Range (1.75x)']
    
    # Draw circles from largest to smallest for better layering
    # Synthetic (outermost - theoretical max)
    if synth_range > 0:
        circle_synth = Circle((0, 0), synth_range,
                             facecolor='purple',
                             alpha=0.15, linewidth=3, edgecolor='purple',
                             linestyle='--',
                             label=f'Synthetic (1.75x): {synth_range:.1f}m')
        ax.add_patch(circle_synth)
    
    # Hollow Point (middle)
    if hp_range > 0:
        circle_hp = Circle((0, 0), hp_range,
                          facecolor='orange',
                          alpha=0.25, linewidth=3, edgecolor='darkorange',
                          label=f'Hollow Point (1.5x): {hp_range:.1f}m')
        ax.add_patch(circle_hp)
    
    # Base (innermost)
    if base_range > 0:
        circle_base = Circle((0, 0), base_range,
                            facecolor='gray',
                            alpha=0.35, linewidth=3, edgecolor='black',
                            label=f'Base (1.34x): {base_range:.1f}m')
        ax.add_patch(circle_base)
    
    # Add center point (player)
    ax.plot(0, 0, 'ko', markersize=12, zorder=100)
    ax.text(0, -2, 'YOU', ha='center', va='top', fontsize=10, fontweight='bold')
    
    # Set limits
    max_range = max(base_range, hp_range, synth_range)
    ax.set_xlim(-max_range*1.2, max_range*1.2)
    ax.set_ylim(-max_range*1.2, max_range*1.2)
    ax.set_aspect('equal')
    
    # Grid and labels
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlabel('Distance (meters)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Distance (meters)', fontsize=11, fontweight='bold')
    
    # Title
    title = f"{gun} ({weapon_type})\n"
    title += f"Has: {ammo_type}\n"
    
    if ammo_type == 'Hollow Point':
        title += f"HP Extension: +{data['HP Extension']:.1f}m"
    else:
        title += f"Synth Extension: +{data['Synth Extension']:.1f}m"
    
    ax.set_title(title, fontsize=13, fontweight='bold',
                color=type_colors.get(weapon_type, 'black'), pad=15)
    
    # Legend
    ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
    
    # Add range markers
    for range_val in [10, 20, 30]:
        if range_val <= max_range * 1.1:
            circle_ref = Circle((0, 0), range_val, fill=False,
                              color='gray', linestyle=':', linewidth=1, alpha=0.4)
            ax.add_patch(circle_ref)
            ax.text(range_val, 0, f'{range_val}m', 
                   fontsize=9, color='gray', va='bottom', ha='left')

# Hide unused subplots
for idx in range(num_weapons, len(axes)):
    axes[idx].axis('off')

plt.suptitle('3-Shot Kill Weapons: Range Extension Analysis (INTERPOLATED)\n' +
             '(2 Headshots + 1 Body Shot = Kill)\n' +
             'Circle radius = Maximum effective range with continuous damage falloff',
             fontsize=16, fontweight='bold', y=0.98)

plt.tight_layout()
plt.savefig('visualizations/3Shot_Range_Circles.png', dpi=300, bbox_inches='tight')
print(f"\n{'='*80}")
print("Saved: visualizations/3Shot_Range_Circles.png")
print("Saved: visualizations/3Shot_Range_Analysis.csv")
print("="*80)

# === OVERLAY VERSION ===
fig, ax = plt.subplots(figsize=(14, 14))

# Sort by synthetic range
df_sorted = df_results.sort_values('Synthetic Range (1.75x)', ascending=False)

max_overall = df_sorted['Synthetic Range (1.75x)'].max()

for idx, row in df_sorted.iterrows():
    gun = row['Gun']
    weapon_type = row['Type']
    synth_range = row['Synthetic Range (1.75x)']
    
    # Calculate angle for label placement
    angle = idx * (360 / len(df_sorted)) * np.pi / 180
    
    # Draw synth circle
    if synth_range > 0:
        circle = Circle((0, 0), synth_range,
                       facecolor=type_colors.get(weapon_type, '#CCCCCC'),
                       alpha=0.12, linewidth=2,
                       edgecolor=type_colors.get(weapon_type, 'black'),
                       linestyle='-')
        ax.add_patch(circle)
        
        # Label at edge
        label_dist = synth_range * 1.08
        label_x = label_dist * np.cos(angle)
        label_y = label_dist * np.sin(angle)
        
        ax.annotate(gun, xy=(synth_range * np.cos(angle), synth_range * np.sin(angle)),
                   xytext=(label_x, label_y),
                   fontsize=10, fontweight='bold',
                   color=type_colors.get(weapon_type, 'black'),
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.4',
                           facecolor=type_colors.get(weapon_type, 'white'),
                           alpha=0.8, edgecolor='black'))

# Add player position
ax.plot(0, 0, 'ko', markersize=15, zorder=100)
ax.text(0, -2, 'YOU', ha='center', va='top', fontsize=12, fontweight='bold')

# Add reference circles
for range_ring in [10, 20, 30]:
    if range_ring <= max_overall * 1.1:
        circle_ref = Circle((0, 0), range_ring, fill=False,
                           color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
        ax.add_patch(circle_ref)
        ax.text(0, range_ring+1, f'{range_ring}m', ha='center', va='bottom',
               fontsize=11, color='gray', fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

ax.set_xlim(-max_overall*1.25, max_overall*1.25)
ax.set_ylim(-max_overall*1.25, max_overall*1.25)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
ax.set_xlabel('Distance (meters)', fontsize=13, fontweight='bold')
ax.set_ylabel('Distance (meters)', fontsize=13, fontweight='bold')

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=type_colors['AR'], label='AR', edgecolor='black', alpha=0.6),
    Patch(facecolor=type_colors['LMG'], label='LMG', edgecolor='black', alpha=0.6)
]
ax.legend(handles=legend_elements, title='Weapon Type', loc='upper left', fontsize=12)

ax.set_title('3-Shot Kill Weapons: Overlaid Maximum Ranges (INTERPOLATED)\n' +
             '(Showing Synthetic 1.75x range with continuous damage falloff)\n' +
             'Circle size = Kill range with 2 Headshots + 1 Body Shot',
             fontsize=15, fontweight='bold', pad=20)

plt.savefig('visualizations/3Shot_Range_Circles_Overlay.png', dpi=300, bbox_inches='tight')
print("Saved: visualizations/3Shot_Range_Circles_Overlay.png")
print("="*80)

