import pandas as pd
import numpy as np

# Read data
df = pd.read_csv('data/BF6 DPS Chart v2.1 _SEASON 1 UPDATES_.xlsx - All Guns by Weapon Type.csv')

# Parse damage values at different ranges
df['DMG_10M'] = pd.to_numeric(df['DMG at 10M'], errors='coerce')
df['DMG_20M'] = pd.to_numeric(df['DMG at 20M'], errors='coerce')
df['DMG_35M'] = pd.to_numeric(df['DMG at 35M'], errors='coerce')
df['Base_DMG'] = pd.to_numeric(df['DMG'], errors='coerce')

BASE_HS_MULT = 1.34

def calculate_stk_with_one_hs(body_damage):
    """Calculate shots to kill with 1 headshot + body shots"""
    if pd.isna(body_damage) or body_damage <= 0:
        return None
    
    hs_damage = body_damage * BASE_HS_MULT
    remaining_damage = 100 - hs_damage
    
    if remaining_damage <= 0:
        return 1  # 1 headshot kills
    
    body_shots_needed = np.ceil(remaining_damage / body_damage)
    total_shots = 1 + body_shots_needed
    
    return int(total_shots)

# Calculate STK at each range
results = []

for idx, row in df.iterrows():
    gun = row['Gun']
    weapon_type = row['Type']
    base_dmg = row['Base_DMG']
    
    # Calculate STK at each range
    stk_10m = calculate_stk_with_one_hs(row['DMG_10M'])
    stk_20m = calculate_stk_with_one_hs(row['DMG_20M'])
    stk_35m = calculate_stk_with_one_hs(row['DMG_35M'])
    
    results.append({
        'Gun': gun,
        'Type': weapon_type,
        'Base Damage': base_dmg,
        'STK at 10M': stk_10m,
        'STK at 20M': stk_20m,
        'STK at 35M': stk_35m,
        'Damage at 10M': row['DMG_10M'],
        'Damage at 20M': row['DMG_20M'],
        'Damage at 35M': row['DMG_35M']
    })

df_results = pd.DataFrame(results)

# Sort by STK at 20M (most relevant engagement range)
df_results = df_results.sort_values(['STK at 20M', 'Type', 'Gun'])

# Save to CSV
df_results.to_csv('STK_Categorization_One_Headshot.csv', index=False)

print("="*80)
print("WEAPON CATEGORIZATION BY SHOTS TO KILL")
print("(Assuming 1 Headshot + Body Shots, Standard 1.34x Multiplier)")
print("="*80)

# Group by STK at different ranges
print("\n" + "="*80)
print("CATEGORIZATION BY STK AT 20M (Most Relevant Range)")
print("="*80)

for stk in sorted(df_results['STK at 20M'].dropna().unique()):
    weapons_in_category = df_results[df_results['STK at 20M'] == stk]
    print(f"\n{'='*80}")
    print(f"{int(stk)}-SHOT KILL (1 Headshot + {int(stk-1)} Body) - {len(weapons_in_category)} Weapons")
    print(f"{'='*80}")
    
    # Group by weapon type
    for wtype in ['AR', 'CARBINE', 'LMG', 'SMG']:
        type_weapons = weapons_in_category[weapons_in_category['Type'] == wtype]
        if len(type_weapons) > 0:
            print(f"\n{wtype}s ({len(type_weapons)}):")
            for _, weapon in type_weapons.iterrows():
                dmg_info = f"DMG: {weapon['Damage at 20M']:.1f}"
                # Show if STK changes at other ranges
                stk_changes = []
                if weapon['STK at 10M'] != stk:
                    stk_changes.append(f"10M={int(weapon['STK at 10M'])}shot")
                if weapon['STK at 35M'] != stk:
                    stk_changes.append(f"35M={int(weapon['STK at 35M'])}shot")
                
                change_info = f" [{', '.join(stk_changes)}]" if stk_changes else ""
                print(f"  - {weapon['Gun']:20} | {dmg_info}{change_info}")

# Summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS AT 20M")
print("="*80)

stk_counts = df_results['STK at 20M'].value_counts().sort_index()
for stk, count in stk_counts.items():
    percentage = (count / len(df_results)) * 100
    print(f"{int(stk)}-Shot Kill: {count:2} weapons ({percentage:.1f}%)")

print("\n" + "="*80)
print("BREAKDOWN BY WEAPON TYPE AT 20M")
print("="*80)

for wtype in ['AR', 'CARBINE', 'LMG', 'SMG']:
    type_df = df_results[df_results['Type'] == wtype]
    print(f"\n{wtype} ({len(type_df)} weapons):")
    stk_dist = type_df['STK at 20M'].value_counts().sort_index()
    for stk, count in stk_dist.items():
        print(f"  {int(stk)}-shot: {count} weapons")

# Show range-dependent weapons
print("\n" + "="*80)
print("WEAPONS WITH RANGE-DEPENDENT STK")
print("="*80)

range_dependent = df_results[
    (df_results['STK at 10M'] != df_results['STK at 20M']) | 
    (df_results['STK at 20M'] != df_results['STK at 35M'])
]

if len(range_dependent) > 0:
    print(f"\n{len(range_dependent)} weapons have different STK at different ranges:")
    for _, weapon in range_dependent.iterrows():
        print(f"  {weapon['Gun']:20} ({weapon['Type']:8}) | "
              f"10M: {int(weapon['STK at 10M'])}shot | "
              f"20M: {int(weapon['STK at 20M'])}shot | "
              f"35M: {int(weapon['STK at 35M'])}shot")
else:
    print("\nNo weapons have range-dependent STK changes.")

print("\n" + "="*80)
print("Analysis complete! Data saved to: STK_Categorization_One_Headshot.csv")
print("="*80)

