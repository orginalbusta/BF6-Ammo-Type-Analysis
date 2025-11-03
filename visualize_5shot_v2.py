import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

# Read new falloff data
falloff_df = pd.read_csv('data/Battlefield 6 Damage Fall Off - V2.csv', skiprows=1)
ammo_df = pd.read_csv('Weapon_Ammo_Types.csv')
stk_df = pd.read_csv('STK_Categorization_One_Headshot.csv')

# Clean up column names and parse data
falloff_df = falloff_df.rename(columns={
    'Gun (!!! -> Missing)': 'Gun',
    'Dmg': 'DMG_Close',
    '10m': 'DMG_10M',
    '75m': 'DMG_75M'
})

# Create name mapping to handle differences between files
name_mapping = {
    'KV9': 'KV9',
    'M4A1': 'M4A1',
    'GRT-BC': 'GRT-BC',
    'SGX': 'SGX',
    'QBZ': 'QBZ-192',
    'PW5A3': 'PW5A3',
    'SG 553R': 'SG 553R',
    'SL9': 'SL9',
    'NVO-228E': 'NVO-228E',
    'UMG-40': 'UMG-40'
}

# Get 5-shot kill weapons at 20M
five_shot_weapons_orig = stk_df[stk_df['STK at 20M'] == 5]['Gun'].tolist()
five_shot_weapons = [name_mapping.get(gun, gun) for gun in five_shot_weapons_orig]

# Merge data
df = falloff_df[falloff_df['Gun'].isin(five_shot_weapons)].copy()

# Map gun names back for ammo lookup
reverse_mapping = {v: k for k, v in name_mapping.items()}
df['Gun_Original'] = df['Gun'].map(lambda x: reverse_mapping.get(x, x))

# Merge with ammo data using original names
ammo_temp = ammo_df[['Gun', 'Ammo Type', 'Actual Multiplier']].copy()
df = df.merge(ammo_temp, left_on='Gun_Original', right_on='Gun', how='left', suffixes=('_falloff', '_ammo'))
df['Gun'] = df['Gun_falloff']
df = df.drop(columns=['Gun_ammo', 'Gun_falloff'])

# Parse damage values
df['DMG_Close'] = pd.to_numeric(df['DMG_Close'], errors='coerce')
df['DMG_10M'] = pd.to_numeric(df['DMG_10M'], errors='coerce')
df['DMG_75M'] = pd.to_numeric(df['DMG_75M'], errors='coerce')
df['HS_Multiplier'] = pd.to_numeric(df['Actual Multiplier'], errors='coerce')

BASE_HS_MULT = 1.34
HP_MULT = 1.5
SYNTH_MULT = 1.75
HP_THRESHOLD = 100

# Color scheme
type_colors = {
    'Assault Rifle': '#FF6B6B',
    'Carbine': '#4ECDC4', 
    'LMG': '#95E1D3',
    'SMG': '#FFD93D'
}

def interpolate_max_range(row, multiplier, num_hs, num_body):
    """Interpolate to find the exact range where N HS + M Body = 100 damage"""
    
    dmg_close = row['DMG_Close']
    dmg_10m = row['DMG_10M']
    dmg_75m = row['DMG_75M']
    
    if pd.isna(dmg_close) or pd.isna(dmg_10m) or pd.isna(dmg_75m):
        return 0
    
    def calc_damage(hs_dmg, body_dmg):
        return (hs_dmg * num_hs) + (body_dmg * num_body)
    
    ranges = [
        (0, 10, dmg_close, dmg_10m),
        (10, 75, dmg_10m, dmg_75m)
    ]
    
    max_range = 0
    
    for start_range, end_range, start_dmg, end_dmg in ranges:
        hs_dmg_end = end_dmg * multiplier
        total_dmg_end = calc_damage(hs_dmg_end, end_dmg)
        
        if total_dmg_end >= HP_THRESHOLD:
            max_range = end_range
        else:
            hs_dmg_start = start_dmg * multiplier
            total_dmg_start = calc_damage(hs_dmg_start, start_dmg)
            
            if total_dmg_start >= HP_THRESHOLD:
                range_diff = end_range - start_range
                damage_diff = total_dmg_start - total_dmg_end
                
                if damage_diff > 0:
                    damage_to_lose = total_dmg_start - HP_THRESHOLD
                    fraction = damage_to_lose / damage_diff
                    interpolated_range = start_range + (range_diff * fraction)
                    return interpolated_range
            break
    
    return max_range

def create_visualization(num_hs, num_body, suffix, title_text):
    """Create visualization for a specific headshot/body shot combination"""
    
    print(f"\n5-Shot Kill Weapons ({num_hs} HS + {num_body} Body): {len(df)}")
    print("="*80)
    
    results = []
    
    for idx, row in df.iterrows():
        gun = row['Gun']
        weapon_type = row['Type']
        ammo_type = row['Ammo Type']
        
        base_range = interpolate_max_range(row, BASE_HS_MULT, num_hs, num_body)
        hp_range = interpolate_max_range(row, HP_MULT, num_hs, num_body)
        synth_range = interpolate_max_range(row, SYNTH_MULT, num_hs, num_body)
        
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
        
        print(f"{gun:15} ({weapon_type:13}) | {ammo_type:13} | "
              f"Base: {base_range:.1f}m | HP: {hp_range:.1f}m (+{hp_range-base_range:.1f}m) | "
              f"Synth: {synth_range:.1f}m (+{synth_range-base_range:.1f}m)")
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(f'5Shot_{suffix}_Range_Analysis.csv', index=False)
    
    # === CREATE VISUALIZATION ===
    num_weapons = len(df_results)
    cols = 4
    rows = (num_weapons + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(20, 5*rows))
    if rows == 1 and cols == 1:
        axes = [axes]
    elif rows == 1 or cols == 1:
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
    else:
        axes = axes.flatten()
    
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
        
        if synth_range > 0:
            circle_synth = Circle((0, 0), synth_range,
                                 facecolor='purple',
                                 alpha=0.15, linewidth=3, edgecolor='purple',
                                 linestyle='--' if ammo_type == 'Hollow Point' else '-',
                                 label=f'Synthetic (1.75x): {synth_range:.1f}m')
            ax.add_patch(circle_synth)
        
        if hp_range > 0:
            circle_hp = Circle((0, 0), hp_range,
                              facecolor='orange',
                              alpha=0.25, linewidth=3, edgecolor='darkorange',
                              label=f'Hollow Point (1.5x): {hp_range:.1f}m')
            ax.add_patch(circle_hp)
        
        if base_range > 0:
            circle_base = Circle((0, 0), base_range,
                                facecolor='gray',
                                alpha=0.35, linewidth=3, edgecolor='black',
                                label=f'Base (1.34x): {base_range:.1f}m')
            ax.add_patch(circle_base)
        
        ax.plot(0, 0, 'ko', markersize=10, zorder=100)
        ax.text(0, -1.5, 'YOU', ha='center', va='top', fontsize=9, fontweight='bold')
        
        max_range = max(base_range, hp_range, synth_range)
        if max_range == 0:
            max_range = 10
        ax.set_xlim(-max_range*1.2, max_range*1.2)
        ax.set_ylim(-max_range*1.2, max_range*1.2)
        ax.set_aspect('equal')
        
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('Distance (m)', fontsize=10)
        ax.set_ylabel('Distance (m)', fontsize=10)
        
        title = f"{gun} ({weapon_type})\n{ammo_type}\n"
        if ammo_type == 'Hollow Point':
            title += f"HP: +{data['HP Extension']:.1f}m"
        else:
            title += f"Synth: +{data['Synth Extension']:.1f}m"
        
        ax.set_title(title, fontsize=11, fontweight='bold',
                    color=type_colors.get(weapon_type, 'black'), pad=10)
        
        if base_range > 0 or hp_range > 0 or synth_range > 0:
            ax.legend(loc='upper right', fontsize=8, framealpha=0.95)
        
        for range_val in [10, 20, 30, 40, 50, 60, 70]:
            if range_val <= max_range * 1.1:
                circle_ref = Circle((0, 0), range_val, fill=False,
                                  color='gray', linestyle=':', linewidth=0.8, alpha=0.4)
                ax.add_patch(circle_ref)
                ax.text(range_val, 0, f'{range_val}m', 
                       fontsize=8, color='gray', va='bottom', ha='left')
    
    for idx in range(num_weapons, len(axes)):
        axes[idx].axis('off')
    
    plt.suptitle(f'{title_text}\n' +
                 'Circle radius = Maximum effective range with continuous damage falloff',
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    plt.savefig(f'visualizations/5Shot_{suffix}_Range_Circles.png', dpi=300, bbox_inches='tight')
    print(f"\n{'='*80}")
    print(f"Saved: visualizations/5Shot_{suffix}_Range_Circles.png")
    print(f"Saved: 5Shot_{suffix}_Range_Analysis.csv")
    print("="*80)

# Create both visualizations
create_visualization(1, 4, '1HS', '5-Shot Kill Weapons: 1 Headshot + 4 Body Shots')
create_visualization(2, 3, '2HS', '5-Shot Kill Weapons: 2 Headshots + 3 Body Shots')

print("\n" + "="*80)
print("ALL 5-SHOT VISUALIZATIONS COMPLETE!")
print("="*80)

