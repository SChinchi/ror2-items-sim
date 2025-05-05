class SceneName:
    # Normal
    DR = 'blackbeach'           # Distant Roost
    TP = 'golemplains'          # Titanic Plains
    SF = 'snowyforest'          # Siphoned Forest
    VF2 = 'lakes'               # Verdant Falls (#2 due to Void Fields conflict)
    VF3 = 'lakesnight'          # Viscous Falls
    SA2 = 'village'             # Shattered Abodes
    DI = 'villagenight'         # Disturbed Impact
    AA = 'goolake'              # Abandoned Aqueduct
    WA = 'foggyswamp'           # Wetland Aspects
    AS = 'ancientloft'          # Aphelian Sanctuary
    RA = 'lemuriantemple'       # Reformed Altar
    RD = 'frozenwall'           # Rallypoint Delta
    SA = 'wispgraveyard'        # Scorched Acres
    SP = 'sulfurpools'          # Sulfur Pools
    TC = 'habitat'              # Treeborn Colony
    GD = 'habitatfall'          # Golden Dieback
    AD = 'dampcavesimple'       # Abyssal Depths
    SC = 'shipgraveyard'        # Siren's Call
    SG = 'rootjungle'           # Sundered Grove
    SM = 'skymeadow'            # Sky Meadow
    HH = 'helminthroost'        # Helminth Hatchery
    CO = 'moon2'                # Commencement
    # Void
    VF = 'arena'                # Void Fields
    VL = 'voidstage'            # Void Locus
    PL = 'voidraid'             # The Planetarium
    # Intermission
    BA = 'artifactworld'        # Bulwark's Ambry
    GC = 'goldshores'           # Gilded Coast
    BT = 'bazaar'               # Bazaar Between Time
    MF = 'mysteryspace'         # A Moment, Fractured
    MW = 'limbo'                # A Moment, Whole
    PM = 'meridian'             # Prime Meridian
    # Simulacrum
    STP = 'itgolemplains'       # Simulacrum, Titanic Plains
    SAS = 'itancientloft'       # Simulacrum, Aphelian Sanctuary
    SAA = 'itgoolake'           # Simulacrum, Abandoned Aqueduct
    SRD = 'itfrozenwall'        # Simulacrum, Rallypoint Delta
    SAD = 'itdampcave'          # Simulacrum, Abyssal Depths
    SSM = 'itskymeadow'         # Simulacrum, Sky Meadow
    SCO = 'itmoon'              # Simulacrum, Commencement


class Portal:
    A = 'artifact'
    B = 'blue'
    C = 'celestial'
    D = 'deepvoid'
    G = 'gold'
    N = 'null'
    V = 'void'


class Expansion:
    SOTV = 'DLC1'
    SOTS = 'DLC2'


ALL_EXPANSIONS = set([Expansion.SOTV, Expansion.SOTS])
NO_EXPANSIONS = set()

IT_STAGES = (
    SceneName.STP, SceneName.SAS, SceneName.SAA, SceneName.SRD,
    SceneName.SAD, SceneName.SSM, SceneName.SCO,
)
