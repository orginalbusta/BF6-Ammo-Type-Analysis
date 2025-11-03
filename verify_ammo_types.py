import pandas as pd

# Read the original stat card values
stat_card_df = pd.read_csv('data/BF6 DPS Chart v2.1 _SEASON 1 UPDATES_.xlsx - Stat Card Values.csv')
current_ammo_df = pd.read_csv('Weapon_Ammo_Types.csv')
stk_df = pd.read_csv('STK_Categorization_One_Headshot.csv')

# Get all guns we're visualizing (3-shot, 4-shot, 5-shot kills)
visualized_guns = set()
for stk in [3, 4, 5]:
    guns = stk_df[stk_df['STK at 20M'] == stk]['Gun'].tolist()
    visualized_guns.update(guns)

print("AMMO TYPE VERIFICATION")
print("="*100)
print(f"Total guns being visualized: {len(visualized_guns)}")
print("="*100)

# Check each gun
issues_found = []

for gun in sorted(visualized_guns):
    # Get current classification
    current_row = current_ammo_df[current_ammo_df['Gun'] == gun]
    
    # Get original data
    stat_card_row = stat_card_df[stat_card_df['Gun'] == gun]
    
    if current_row.empty:
        print(f"[X] {gun:20} - NOT FOUND in Weapon_Ammo_Types.csv")
        issues_found.append(f"{gun} - Missing from ammo types file")
        continue
    
    if stat_card_row.empty:
        print(f"[!] {gun:20} - NOT FOUND in Stat Card Values (check name mapping)")
        issues_found.append(f"{gun} - Missing from stat card (possible name mismatch)")
        continue
    
    current_ammo = current_row.iloc[0]['Ammo Type']
    
    # Determine correct ammo type by checking Syn/HP value vs base damage
    # Synthetic = 1.75x, Hollow Point = 1.5x
    dmg = stat_card_row.iloc[0]['DMG']
    syn_hp_value = stat_card_row.iloc[0]['Syn/HP']
    
    # Calculate what the multiplier is
    if pd.notna(syn_hp_value) and pd.notna(dmg) and dmg > 0:
        multiplier = syn_hp_value / dmg
        if abs(multiplier - 1.75) < 0.01:
            correct_ammo = 'Synthetic'
        elif abs(multiplier - 1.5) < 0.01:
            correct_ammo = 'Hollow Point'
        else:
            correct_ammo = f'Unknown (mult={multiplier:.2f})'
    else:
        correct_ammo = 'Unknown (missing data)'
    
    if current_ammo == correct_ammo:
        print(f"[OK] {gun:20} - {current_ammo:13} - CORRECT")
    else:
        print(f"[X] {gun:20} - Current: {current_ammo:13} | Should be: {correct_ammo:13} - WRONG!")
        issues_found.append(f"{gun} - Should be {correct_ammo}, currently {current_ammo}")

print("\n" + "="*100)
if issues_found:
    print(f"FOUND {len(issues_found)} ISSUES:")
    print("="*100)
    for issue in issues_found:
        print(f"  - {issue}")
else:
    print("[OK] ALL AMMO TYPES ARE CORRECT!")
print("="*100)

# Also print a summary by weapon type
print("\nSUMMARY BY WEAPON TYPE:")
print("="*100)

for weapon_type in ['AR', 'CARBINE', 'LMG', 'SMG']:
    guns_of_type = current_ammo_df[current_ammo_df['Type'] == weapon_type]['Gun'].tolist()
    guns_of_type = [g for g in guns_of_type if g in visualized_guns]
    
    hp_guns = [g for g in guns_of_type if current_ammo_df[current_ammo_df['Gun'] == g]['Ammo Type'].iloc[0] == 'Hollow Point']
    synth_guns = [g for g in guns_of_type if current_ammo_df[current_ammo_df['Gun'] == g]['Ammo Type'].iloc[0] == 'Synthetic']
    
    print(f"\n{weapon_type}:")
    print(f"  Hollow Point: {', '.join(hp_guns) if hp_guns else 'None'}")
    print(f"  Synthetic:    {', '.join(synth_guns) if synth_guns else 'None'}")

