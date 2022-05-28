# RoR2 Stage Items Simulator

A simulator to generate items for a stage based on the game's rules, or to analyse how frequently each item type can spawn.
 
 ## How to use
 
 Numpy and UnityPy are required to run the code.
 
 ```
 from constants import SceneName
 from scene_director import SceneDirector
 
 scene = SceneDirector(SceneName.DR)
 # To generate items once
 scene.populate_scene()
 # To gather statistics
 scene.print_statistics()
 ```
 
 ## Data
 The `scene_data.json` file stores extracted data from the game's files. The format is an array of two objects
 
 ```
 [
    scene_data,
    spawn_cards
 ]
 ```
 
The `scene_data` object contains information for each scene, such as the director credits and what interactables are available in the base and DLC version, referenced by their respective spawn card IDs.
The `spawn_cards` object contains information about each spawn card, e.g., name, director cost, and whether they are banned when the Artifact of Sacrifice is enabled.