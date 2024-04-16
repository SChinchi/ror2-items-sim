### 1.2.0

* Updated the extracted data for game version 1.2.4.4.
* Adapted the SceneDirector to also work for simulacrum stages, which get their interactable credits specifically overriden.
* Added Lunar Seer Station functionality to `Run` with explicit stage preference order to bias towards certain stages in a run.
* Changed the void seed name keys to "camp1" and "camp2" for convenience.
* Changed the bodies keys to the internal body names for better identification.
* Fixed the Radio Scanner not being filtered out from interactable generation even when already unlocked.
* Fixed the Gilded Coast name typo in `SceneName`. "GS" is the abbreviation of the internal stage name.
* Extracted more data which is mostly useful for datamining and wiki maintenance between game updates.
  * More detailed AI data, which is now split off from "skills.json" into the dedicated "masters.json" file.
  * Starting item grants for specific characters, detailed both in the masters and character spawn card data.
  * Bottle of Chaos activation for equipment.
  * Scene next destinations and newt statues.
* Untracked .pyc files which had been previously included by mistake.

### 1.1.2

* Added how to use `data_parser.py` in the README.

### 1.1.1

* Fixed some README typos and code blocks.

### 1.1.0

* Added the CampDirector for Void Seed interactable generation simulation. The script hosting both director classes has been renamed to `directors.py`.
* Built a run simulator around the SceneDirector functionality.
* Restructed the object extraction for easy extensibility. The extracted data now lies in "data/extracted".
* Extracted a lot more data required, such as items, equipment, characters, droptables, scenes, and void seed.
* Added `data_loader.py` which loads all the extracted data in objects for easier usage.
* Added `sim_items.py` which is a convenience script for running and analysing a run simulation.
* Added `sim_horde.py` which calculates the chance of horde of many for any stage.

### 1.0.0

* Release