import pandas as pd

# Read the Stat Card Values which has the actual ammo multiplier data
df = pd.read_csv('data/BF6 DPS Chart v2.1 _SEASON 1 UPDATES_.xlsx - Stat Card Values.csv')

# Calculate actual multiplier
df['Base DMG'] = pd.to_numeric(df['DMG'], errors='coerce')
df['Syn/HP DMG'] = pd.to_numeric(df['Syn/HP'], errors='coerce')
df['Actual Multiplier'] = (df['Syn/HP DMG'] / df['Base DMG']).round(3)

# Categorize ammo type
def categorize_ammo(multiplier):
    if pd.isna(multiplier):
        return 'Unknown'
    elif 1.49 <= multiplier <= 1.51:
        return 'Hollow Point'
    elif 1.74 <= multiplier <= 1.76:
        return 'Synthetic'
    else:
        return f'Non-standard ({multiplier:.2f}x)'

df['Ammo Type'] = df['Actual Multiplier'].apply(categorize_ammo)

# Select relevant columns
ammo_info = df[['Gun', 'Type', 'Base DMG', 'Ammo Type', 'Actual Multiplier']].copy()

# Sort by Type then Gun name
ammo_info = ammo_info.sort_values(['Type', 'Gun'])

# Save to CSV
ammo_info.to_csv('Weapon_Ammo_Types.csv', index=False)

print("="*80)
print("WEAPON AMMO TYPE AVAILABILITY")
print("="*80)

# Summary by ammo type
print("\nSUMMARY:")
print("-"*80)
ammo_counts = ammo_info['Ammo Type'].value_counts()
for ammo_type, count in ammo_counts.items():
    percentage = (count / len(ammo_info)) * 100
    print(f"{ammo_type}: {count} weapons ({percentage:.1f}%)")

# Breakdown by weapon type
print("\n" + "="*80)
print("BREAKDOWN BY WEAPON TYPE")
print("="*80)

for wtype in ['AR', 'CARBINE', 'LMG', 'SMG']:
    type_df = ammo_info[ammo_info['Type'] == wtype]
    print(f"\n{wtype} ({len(type_df)} weapons):")
    
    hp_weapons = type_df[type_df['Ammo Type'] == 'Hollow Point']
    syn_weapons = type_df[type_df['Ammo Type'] == 'Synthetic']
    
    if len(hp_weapons) > 0:
        print(f"  Hollow Point (1.5x): {len(hp_weapons)} weapons")
        for _, weapon in hp_weapons.iterrows():
            print(f"    - {weapon['Gun']}")
    
    if len(syn_weapons) > 0:
        print(f"  Synthetic (1.75x): {len(syn_weapons)} weapons")
        for _, weapon in syn_weapons.iterrows():
            print(f"    - {weapon['Gun']}")

# Detailed listing
print("\n" + "="*80)
print("COMPLETE WEAPON LIST")
print("="*80)

for _, weapon in ammo_info.iterrows():
    mult_display = f"{weapon['Actual Multiplier']:.2f}x"
    print(f"{weapon['Gun']:20} ({weapon['Type']:8}) | {weapon['Base DMG']:5.1f} DMG | "
          f"{weapon['Ammo Type']:15} ({mult_display})")

print("\n" + "="*80)
print("Data saved to: Weapon_Ammo_Types.csv")
print("="*80)

