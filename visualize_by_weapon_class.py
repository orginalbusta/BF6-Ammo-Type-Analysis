import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

# Read data
falloff_df = pd.read_csv('data/Battlefield 6 Damage Fall Off - V2.csv', skiprows=1)
ammo_df = pd.read_csv('Weapon_Ammo_Types.csv')
stk_df = pd.read_csv('STK_Categorization_One_Headshot.csv')

# Clean up column names
falloff_df = falloff_df.rename(columns={
    'Gun (!!! -> Missing)': 'Gun',
    'Dmg': 'DMG_Close',
    '10m': 'DMG_10M',
    '75m': 'DMG_75M'
})

# Name mapping
name_mapping = {
    'TR7': 'TR-7',
    'M/60': 'M60',
    'M240L': 'M240L',
    'M123K': 'M123K',
    'M433': 'M433',
    'SCW-10': 'SCW-10',
    'DRS-IAR': 'DRS-IAR',
    'M277': 'M277',
    'B36A4': 'B36A4',
    'L110': 'L110',
    'M250': 'M250 !!!',
    'M417 A2': 'M417A2',
    'L85A3': 'L85A3',
    'SOR-300SC': 'SOR-300SC',
    'SOR-556 MK2': 'SOR-556 MK2',
    'RPKM': 'RPKM',
    'KTS100 MK8': 'KTS100 MK8',
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

def extrapolate_damage_100m(dmg_10m, dmg_75m):
    """Linearly extrapolate damage to 100m"""
    damage_loss_per_meter = (dmg_10m - dmg_75m) / (75 - 10)
    range_beyond_75 = 100 - 75
    extrapolated_dmg = dmg_75m - (damage_loss_per_meter * range_beyond_75)
    return max(extrapolated_dmg, 10)

def interpolate_max_range_100m(row, multiplier, num_hs, num_body):
    """Interpolate to find exact range where N HS + M Body = 100 damage"""
    
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

def create_class_visualization(weapon_class, num_hs, suffix):
    """Create visualization for a weapon class with N headshots"""
    
    # Get all weapons for this class from STK data
    class_map = {
        'AR': 'AR',
        'Carbine': 'CARBINE',
        'LMG': 'LMG',
        'SMG': 'SMG'
    }
    
    stk_type = class_map[weapon_class]
    weapons_orig = stk_df[stk_df['Type'] == stk_type]['Gun'].tolist()
    weapons_mapped = [name_mapping.get(gun, gun) for gun in weapons_orig]
    
    # Merge data
    df = falloff_df[falloff_df['Gun'].isin(weapons_mapped)].copy()
    df = df[df['Gun'] != 'M250 !!!'].copy()  # Remove M250
    
    if len(df) == 0:
        print(f"No weapons found for {weapon_class}")
        return
    
    # Add extrapolated 100m damage
    df['DMG_Close'] = pd.to_numeric(df['DMG_Close'], errors='coerce')
    df['DMG_10M'] = pd.to_numeric(df['DMG_10M'], errors='coerce')
    df['DMG_75M'] = pd.to_numeric(df['DMG_75M'], errors='coerce')
    df['DMG_100M'] = df.apply(lambda row: extrapolate_damage_100m(row['DMG_10M'], row['DMG_75M']), axis=1)
    
    # Map gun names back for ammo lookup
    reverse_mapping = {v: k for k, v in name_mapping.items()}
    df['Gun_Original'] = df['Gun'].map(lambda x: reverse_mapping.get(x, x))
    
    # Merge with ammo and STK data
    ammo_temp = ammo_df[['Gun', 'Ammo Type', 'Actual Multiplier']].copy()
    df = df.merge(ammo_temp, left_on='Gun_Original', right_on='Gun', how='left', suffixes=('_falloff', '_ammo'))
    df['Gun'] = df['Gun_falloff']
    df = df.drop(columns=['Gun_ammo', 'Gun_falloff'])
    
    # Get STK for each weapon
    stk_temp = stk_df[['Gun', 'STK at 20M']].copy()
    df = df.merge(stk_temp, left_on='Gun_Original', right_on='Gun', how='left', suffixes=('', '_stk'))
    df = df.drop(columns=['Gun_stk'])
    
    print(f"\n{weapon_class} ({num_hs} Headshot{'s' if num_hs > 1 else ''}): {len(df)} weapons")
    print("="*80)
    
    results = []
    
    for idx, row in df.iterrows():
        gun = row['Gun']
        weapon_type_full = row['Type']
        ammo_type = row['Ammo Type']
        stk = row['STK at 20M']
        
        # Calculate number of body shots needed
        num_body = int(stk) - num_hs
        
        if num_body < 0:
            # Not enough shots for this many headshots
            continue
        
        base_range = interpolate_max_range_100m(row, BASE_HS_MULT, num_hs, num_body)
        hp_range = interpolate_max_range_100m(row, HP_MULT, num_hs, num_body)
        synth_range = interpolate_max_range_100m(row, SYNTH_MULT, num_hs, num_body)
        
        results.append({
            'Gun': gun,
            'Type': weapon_type_full,
            'Ammo Type': ammo_type,
            'STK': stk,
            'HS': num_hs,
            'Body': num_body,
            'Base Range (1.34x)': base_range,
            'HP Range (1.5x)': hp_range,
            'Synthetic Range (1.75x)': synth_range,
            'HP Extension': hp_range - base_range,
            'Synth Extension': synth_range - base_range
        })
        
        print(f"{gun:15} ({int(stk)} shots: {num_hs}HS+{num_body}B) | {ammo_type:13} | "
              f"Base: {base_range:.1f}m | HP: {hp_range:.1f}m | Synth: {synth_range:.1f}m")
    
    if len(results) == 0:
        print(f"No valid weapons for {weapon_class} with {num_hs} headshot(s)")
        return
    
    df_results = pd.DataFrame(results)
    df_results.to_csv(f'{weapon_class}_{suffix}_Range_Analysis_100m.csv', index=False)
    
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
        weapon_type_full = data['Type']
        ammo_type = data['Ammo Type']
        stk = int(data['STK'])
        num_hs_shots = int(data['HS'])
        num_body_shots = int(data['Body'])
        base_range = data['Base Range (1.34x)']
        hp_range = data['HP Range (1.5x)']
        synth_range = data['Synthetic Range (1.75x)']
        
        # Draw circles from bottom to top: Synthetic (bottom), HP, Base, then center dot (top)
        # Larger circles more transparent, smaller circles less transparent
        # Using desaturated colors for better visual clarity
        # Only show Synthetic if weapon has access
        if synth_range > 0 and ammo_type == 'Synthetic':
            circle_synth = Circle((0, 0), synth_range,
                                 facecolor='#B8A0D0',  # Desaturated purple
                                 alpha=0.3, linewidth=1.5, edgecolor='#9B7FB8',
                                 linestyle='-',
                                 label=f'Synthetic (1.75x): {synth_range:.1f}m',
                                 zorder=1)
            ax.add_patch(circle_synth)
        
        if hp_range > 0:
            circle_hp = Circle((0, 0), hp_range,
                              facecolor='#E0A870',  # Desaturated orange
                              alpha=0.5, linewidth=1.5, edgecolor='#C89050',
                              label=f'Hollow Point (1.5x): {hp_range:.1f}m',
                              zorder=2)
            ax.add_patch(circle_hp)
        
        if base_range > 0:
            circle_base = Circle((0, 0), base_range,
                                facecolor='#A0A0A0',  # Slightly lighter gray
                                alpha=0.7, linewidth=1.5, edgecolor='#606060',
                                label=f'Base (1.34x): {base_range:.1f}m',
                                zorder=3)
            ax.add_patch(circle_base)
        
        # Center dot on top with smaller size (50% smaller: 10 -> 5)
        ax.plot(0, 0, 'ko', markersize=5, zorder=100)
        
        # Always set max range to 100m
        max_range = 100
        ax.set_xlim(-max_range*1.2, max_range*1.2)
        ax.set_ylim(-max_range*1.2, max_range*1.2)
        ax.set_aspect('equal')
        
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('Distance (m)', fontsize=10)
        ax.set_ylabel('Distance (m)', fontsize=10)
        
        # Calculate percentage increases
        hp_pct = (data['HP Extension'] / base_range * 100) if base_range > 0 else 0
        synth_pct = (data['Synth Extension'] / base_range * 100) if base_range > 0 else 0
        
        title = f"{gun}\n{stk} shots ({num_hs_shots}HS+{num_body_shots}B) | {ammo_type}\n"
        title += f"HP: +{data['HP Extension']:.1f}m ({hp_pct:.1f}%)"
        if ammo_type == 'Synthetic':
            title += f"\nSynth: +{data['Synth Extension']:.1f}m ({synth_pct:.1f}%)"
        
        ax.set_title(title, fontsize=11, fontweight='bold',
                    color=type_colors.get(weapon_type_full, 'black'), pad=10)
        
        if base_range > 0 or hp_range > 0 or synth_range > 0:
            ax.legend(loc='upper right', fontsize=8, framealpha=0.95)
    
    for idx in range(num_weapons, len(axes)):
        axes[idx].axis('off')
    
    # Change title based on number of headshots
    if num_hs == 1:
        hs_text = '1 Incidental Headshot'
    else:
        hs_text = f'{num_hs} Headshots'
    
    plt.suptitle(f'{weapon_class}s: Range Analysis with {hs_text}\n' +
                 'Circle radius = Maximum effective range',
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    plt.savefig(f'visualizations/{weapon_class}_{suffix}_Range_Circles_100m.png', dpi=300, bbox_inches='tight')
    print(f"\n{'='*80}")
    print(f"Saved: visualizations/{weapon_class}_{suffix}_Range_Circles_100m.png")
    print(f"Saved: {weapon_class}_{suffix}_Range_Analysis_100m.csv")
    print("="*80)

# Create all visualizations
weapon_classes = ['AR', 'Carbine', 'LMG', 'SMG']

for weapon_class in weapon_classes:
    create_class_visualization(weapon_class, 1, '1HS')
    create_class_visualization(weapon_class, 2, '2HS')

print("\n" + "="*80)
print("ALL WEAPON CLASS VISUALIZATIONS COMPLETE!")
print("="*80)

