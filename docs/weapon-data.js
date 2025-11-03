const weaponData = {
    // Assault Rifles
    'AK4D': {
        ttkImage: 'visualizations/TTK_ANALYSIS/Assault Rifle/AK4D.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/AK4D_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/AK4D_2HS.png',
        recommendations: [
            '<strong>Hollow Point is EXCELLENT</strong> <span class="ammo-badge badge-hp">BEST IN CLASS</span> - Ranks #1 overall with 117ms average TTK improvement',
            '<strong>Verdict:</strong> Always use Hollow Point. Despite the extra cost, the massive TTK reduction makes this the best HP user in the game. Dominates in 3-shot kill scenarios with exceptional range extension.'
        ]
    },
    'B36A4': {
        ttkImage: 'visualizations/TTK_ANALYSIS/Assault Rifle/B36A4.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/B36A4_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/B36A4_2HS.png',
        recommendations: [
            '<strong>Synthetic is STRONG</strong> <span class="ammo-badge badge-synthetic">SYNTHETIC ACCESS</span> - 83ms average improvement, consistent across ranges',
            '<strong>Verdict:</strong> Use Synthetic for long-range engagements and HP for mid-range. Both provide identical TTK improvements, but Synthetic offers better range extension for 2+ headshot scenarios.'
        ]
    },
    'M433': {
        ttkImage: 'visualizations/TTK_ANALYSIS/Assault Rifle/M433.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/M433_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/M433_2HS.png',
        recommendations: [
            '<strong>Hollow Point is GOOD</strong> <span class="ammo-badge badge-hp">HP ONLY</span> - 72ms average TTK improvement',
            '<strong>Verdict:</strong> Use HP for consistent TTK benefits. While not top-tier, it provides reliable improvements across most engagement ranges. Base ammo viable if conserving credits.'
        ]
    },
    'SOR-556 MK2': {
        ttkImage: 'visualizations/TTK_ANALYSIS/Assault Rifle/SOR-556 MK2.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/SOR-556 MK2_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/SOR-556 MK2_2HS.png',
        recommendations: [
            '<strong>Synthetic is EXCELLENT</strong> <span class="ammo-badge badge-synthetic">TOP 3</span> - Ranks #3 overall with 106ms average improvement',
            '<strong>Verdict:</strong> Always use Synthetic/HP. Ties for consistent performance across all ranges. One of the best special ammo users in the AR class.'
        ]
    },

    // Carbines
    'GRT-BC': {
        ttkImage: 'visualizations/TTK_ANALYSIS/Carbine/GRT-BC.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/GRT-BC_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/GRT-BC_2HS.png',
        recommendations: [
            '<strong>Hollow Point is GOOD</strong> <span class="ammo-badge badge-hp">HP ONLY</span> - 72ms average TTK improvement',
            '<strong>Verdict:</strong> Use HP for better performance in 5-shot kill scenarios. Provides solid range extension and TTK improvements. Best value in medium-range engagements.'
        ]
    },
    'M277': {
        ttkImage: 'visualizations/TTK_ANALYSIS/Carbine/M277.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/M277_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/M277_2HS.png',
        recommendations: [
            '<strong>Hollow Point is STRONG</strong> <span class="ammo-badge badge-hp">HP ONLY</span> - 83ms average improvement, zero damage falloff to 100m!',
            '<strong>Verdict:</strong> Use HP. Already dominates with zero falloff, and HP makes it even deadlier. Maintains 100m effective range with all ammo types - unmatched consistency.'
        ]
    },
    'M4A1': {
        ttkImage: 'visualizations/TTK_ANALYSIS/Carbine/M4A1.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/M4A1_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/M4A1_2HS.png',
        recommendations: [
            '<strong>Hollow Point is DECENT</strong> <span class="ammo-badge badge-hp">HP ONLY</span> - 67ms average TTK improvement',
            '<strong>Verdict:</strong> Use HP for competitive advantage. Most beneficial at 50m+ ranges and in 2-headshot scenarios. Base ammo acceptable for close quarters to save credits.'
        ]
    },

    // Light Machine Guns
    'DRS-IAR': {
        ttkImage: 'visualizations/TTK_ANALYSIS/LMG/DRS-IAR.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/DRS-IAR_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/DRS-IAR_2HS.png',
        recommendations: [
            '<strong>Synthetic is GOOD</strong> <span class="ammo-badge badge-synthetic">SYNTHETIC ACCESS</span> - 78ms average improvement',
            '<strong>Verdict:</strong> Use Synthetic for long-range suppression. Provides consistent 78ms TTK reduction across many scenarios. HP and Synth perform identically in most cases.'
        ]
    },
    'L110': {
        ttkImage: 'visualizations/TTK_ANALYSIS/LMG/L110.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/L110_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/L110_2HS.png',
        recommendations: [
            '<strong>Hollow Point is STRONG</strong> <span class="ammo-badge badge-hp">HP ONLY</span> - 83ms average TTK improvement',
            '<strong>Verdict:</strong> Use HP. Solid all-around improvement for sustained fire. Particularly effective in defensive positions where range matters.'
        ]
    },
    'M123K': {
        ttkImage: 'visualizations/TTK_ANALYSIS/LMG/M123K.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/M123K_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/M123K_2HS.png',
        recommendations: [
            '<strong>Hollow Point is GOOD</strong> <span class="ammo-badge badge-hp">HP ONLY</span> - 72ms average TTK improvement',
            '<strong>Verdict:</strong> Use HP for better suppression effectiveness. Benefits most in 4-shot kill ranges with incidental headshots. Good value for defensive LMG play.'
        ]
    },
    'RPKM': {
        ttkImage: 'visualizations/TTK_ANALYSIS/LMG/RPKM.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/RPKM_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/RPKM_2HS.png',
        recommendations: [
            '<strong>Synthetic is EXCEPTIONAL</strong> <span class="ammo-badge badge-synthetic">BEST IN CLASS</span> - Ranks #1 for Synthetic with 109ms average improvement',
            '<strong>Verdict:</strong> ALWAYS use special ammo. Dominates both HP and Synthetic tierlists - the ultimate special ammo weapon. Synthetic provides unmatched long-range TTK reduction.'
        ]
    },

    // Submachine Guns
    'KV9': {
        ttkImage: 'visualizations/TTK_ANALYSIS/SMG/KV9.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/KV9_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/KV9_2HS.png',
        recommendations: [
            '<strong>Hollow Point is WEAK</strong> <span class="ammo-badge badge-base">BASE VIABLE</span> - Only 56ms average improvement (lowest in class)',
            '<strong>Verdict:</strong> Base ammo recommended. HP provides minimal benefit due to low damage and steep falloff. Save credits and play close range where this SMG excels.'
        ]
    },
    'PW5A3': {
        ttkImage: 'visualizations/TTK_ANALYSIS/SMG/PW5A3.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/PW5A3_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/PW5A3_2HS.png',
        recommendations: [
            '<strong>Synthetic is STRONG</strong> <span class="ammo-badge badge-synthetic">SYNTHETIC ACCESS</span> - 96ms average, 156ms max improvement',
            '<strong>Verdict:</strong> Use Synthetic for maximum TTK reduction. Particularly deadly with 2+ headshots. One of the better SMGs for special ammo utilization.'
        ]
    },
    'SGX': {
        ttkImage: 'visualizations/TTK_ANALYSIS/SMG/SGX.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/SGX_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/SGX_2HS.png',
        recommendations: [
            '<strong>Hollow Point is GOOD</strong> <span class="ammo-badge badge-hp">HP ONLY</span> - 72ms average TTK improvement',
            '<strong>Verdict:</strong> Use HP for consistent close-range performance. Provides solid improvements within SMG effective range. Best utilized under 40m.'
        ]
    },
    'UMG-40': {
        ttkImage: 'visualizations/TTK_ANALYSIS/SMG/UMG-40.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/UMG-40_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/UMG-40_2HS.png',
        recommendations: [
            '<strong>Synthetic is EXCEPTIONAL</strong> <span class="ammo-badge badge-synthetic">TOP 2</span> - 107ms average, 189ms max improvement!',
            '<strong>Verdict:</strong> ALWAYS use Synthetic. Exceptional scaling with peak 189ms improvements. Best SMG for long-range viability - can compete with carbines at 100m with 2 headshots.'
        ]
    },
    'USG-90': {
        ttkImage: 'visualizations/TTK_ANALYSIS/SMG/USG-90.png',
        rangeImage1HS: 'visualizations/INDIVIDUAL_WEAPONS/USG-90_1HS.png',
        rangeImage2HS: 'visualizations/INDIVIDUAL_WEAPONS/USG-90_2HS.png',
        rangeImage3HS: 'visualizations/INDIVIDUAL_WEAPONS/USG-90_3HS.png',
        recommendations: [
            '<strong>Hollow Point is DECENT</strong> <span class="ammo-badge badge-hp">HP ONLY</span> - 67ms average TTK improvement',
            '<strong>Verdict:</strong> Use HP for mid-range engagements. Solid all-around SMG that benefits from HP in 50-60m ranges. Base ammo viable for close quarters.'
        ]
    }
};
