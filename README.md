# RoR2 Stage Item Simulator

Simulate item generation for any stage and collect statistics for the spawned interactables, or simulate a run session to see how many and what items are encountered.

_Targetting game version 1.3.8, but some Seekers of the Storm features have not been implemented fully, mainly the new item effects for the run simulator._

## How to use

Numpy is required to run the code, as is UnityPy if one requires extracting more data from the assets. For UnityPy version 1.21.0 is recommended.

### Interactable generation simulation

The `SceneDirector` is responsible for the spawning logic of interactables for all stages.

```
from constants import SceneName
from scene_director import SceneDirector

director = SceneDirector(SceneName.DR)
director.populate_scene()                     # Generate items once and print the result
director.populate_scene(5)                    # The number of stages cleared can affect the result
director.populate_scene(print_result=False)   # Return the generated items for further use instead of printing them
director.collect_statistics()                 # Gather statistics of how likely each spawnable interactable is
```

The class also provides functionality for changing the stage, enable expansions/artifacts, whether the Environment Log has been collected, and whether the cave on Abyssal Depths is open, all of which can affect which interactables can spawn and with what frequency.

```
director.change_scene(Scene.AD)
director.set_enabled_expansions({})          # Vanilla
director.num_players = 2
director.is_bonus_credits_available = True
director.is_log_available = False
director.is_command_enabled = True
director.is_sacrifice_enabled = True
```

The `CampDirector` is responsible for interactable generation for the Void Seeds and is a simpler version of the `SceneDirector` as it doesn't depend on most of its variables for the outcome. Note that the game spawns two such directors; one for interactables and void enemies, and the other for kelp and voidtouched stage enemies.

```
from directors import CampDirector
director1 = CampDirector()                   # Type 1 director
director1.populate_camp()                    # The number of stages cleared doesn't affect the result
director2 = CampDirector(spawns_kelp=True)   # Type 2 director
director2.populate_camp(print_result=False)  # Return the generated spawn cards as they have no display name
```

### Run full loot simulation

The `Run` class is an implementation of a run session, which can be used to analyse how many items of each tier one can obtain by full looting a number of stages. Since it has no intelligent agent to make context-related decisions, it is limited in some aspects. For example,

- While it supports multiplayer, it cannot make decisions for how to split the loot. For the purposes of this simulation loot distribution is irrelevant, therefore, a unified inventory is used.
- It randomly selects an item to purchase from a multishop, but it will aggressively search for an Executive Card from equipment multishops.
- Due to their interactive and rare nature, Adaptive Chests are not looted but their encounter is logged.
- It doesn't utilise printers and scrappers to optimise the build, as this technically doesn't change the number of items within an item tier.
- Void items don't corrupt their normal counterparts both as a consequence of using a unified inventory and for decision-making reasons.
- While it can handle items which spawn more interactables, e.g., Rusted Key, the lack of corruption means the Encrusted Cache will not spawn.
- It selects the highest tier choice for Void Potentials and Shipping Request Forms.
- The mechanics of items that can change the inventory, i.e., Egocentrism, Eulogy Zero, and Benthic Bloom, are not implemented, even though they are picked up.
- The Lunar Cauldrons and Shop in the Bazaar Between Time are not utilised as they are only about context-related decisions. However, one can set a stage preference for the Lunar Seer for a bias towards specific stages. One can also control when or whether to visit the Void Fields at all.
- The code calculates how many Newt Altars can spawn on each stage, but it does not take into account whether they are reachable in order to open a Blue Portal. It is assumed that if at least one altar has spawned, it can be reached. Only one of the Distant Roost variants has a true chance of not spawning any altars, in which case the Lunar Seer cannot be used. However, a portal is forcefully opened for the Void Fields, simulating the scenario where if the player wants to visit the Void Fields after the first stage and is unable to, they restart the game.
- The choice to use the Gold/Artifact portals can be toggled. If more than one portal options are available on the same stage, the priority is Blue (for Void Fields) > Artifact > Gold > Blue (for Lunar Seer) > normal stage RNG.
- Bulwark's Ambry assumes the Artifact of Command is selected, which affects interactable generation.

Throughout the stages it keeps track of various things, e.g., on which stage the Executive Card was found, how many multishops were purchased with it, how many Regenerating Scrap the player had at the end of each stage, etc.

```
from run import Run

r = Run()
# Up to Sky Meadow and doing the Void Fields after the first stage, no Lunar Seer bias
r.loot_stages(5, 1)
stats = r.stats.consolidate_data()
print(stats['tiers'])

# No Void Fields, prioritise Abandonded Aqueduct > Gilded Coast if available for the Lunar Seer for Stage 2
run.loot_stages(10, stage_preferences={1: [SceneName.AA, SceneName.GC]})
```


### Scripts

There are two prepared scripts for statistical analysis.

#### sim_items.py

Compare how many items are likely to be found in a run with and without the DLC enabled.

```
from sim_items import simulate_run
simulate_run(5)
simulate_run(10, 1, 2)   # Visiting the Void Fields after stage 1, 2 players
```

#### sim_horde.py

Compute the Horde of Many chance for any stage on Monsoon difficulty. As this depends on the credits available for the Teleporter Boss Director, the chance is broken down in credit thresholds. Along with it, it provides the maximum time for that threshold to not be crossed for 0-3 activated Shrines of the Mountain.

```
from constants import SceneName
from sim_horde import compute_horde_chance

for threshold, p, times in compute_horde_chance(SceneName.AD, 3):
	times = ''.join('{:>10s}'.format(str(t) if t else 'N/A') for t in times)
	print(f'{str(threshold):<20s}{p:^8.3f}|{times}')

# 2 players, DLC disabled
for threshold, p, times in compute_horde_chance(SceneName.AD, 3, 2, False):
    pass
```

A helper function that already prints the above result in a nice format is `print_horde_chance`.


## Data

Some of the game's data has been extracted and stored in `json` files under `data/extracted`. The `data_loader.py` script imports all of this in objects, ensuring any referenced data from various files is coupled. The type of data that has been parsed includes:

- Items & Equipment
- Item Tiers
- Droptables
- Spawn Cards
- Bodies & Masters
- Skills
- Director Card Category Selection
- Scenes & Void Seed
- Simulacrum Waves

The extraction script can be run from `data_parser.py` and one only needs to change `DIR_TO_STREAM` within the script, which is the directory to Stream.

```
from data_parser import extract_file_data
extract_file_data()
```