import json
import os

import UnityPy

from constants import Version


ASSETS_DIRECTORY = r'C:\Games\Steam\steamapps\common\Risk of Rain 2\Risk of Rain 2_Data\StreamingAssets\aa\StandaloneWindows64\\'[:-1]
SCENES_FILE = 'scene_data.json'


def _extract_from_assets(src_path=ASSETS_DIRECTORY, out_path=SCENES_FILE):
    # For most scenes the file 'xxxx_scenes_all.bundle' will not load properly
    # with UnityPy, so I exported the MonoBehaviour files with AssetStudio from
    # each 'xxxx_scenes_all.bundle' file and with a quick script I located where
    # the information was. All of this is hardcoded here with a comment of the
    # PathID for quick reference.
    # TODO: Is there an automated way to do this from here?
    c1 = 'credits'
    c2 = 'bonus_credits'
    scenes_extra = {'arena': {c1: 220, c2: 0},            # 3986
                    'blackbeach': {c1: 220, c2: 0},       # 16016 (15700 obsolete)
                    'dampcavesimple': {c1: 400, c2: 160}, # 23811
                    'foggyswamp': {c1: 280, c2: 0},       # 9313
                    'frozenwall': {c1: 280, c2: 0},       # 7865
                    'golemplains': {c1: 220, c2: 0},      # 1532
                    'goolake': {c1: 220, c2: 0},          # 16180
                    'moon2': {c1: 0, c2: 0},              # 33505
                    'rootjungle': {c1: 400, c2: 0},       # 21227
                    'shipgraveyard': {c1: 400, c2: 0},    # 12666
                    'skymeadow': {c1: 520, c2: 0},        # 34254
                    'wispgraveyard': {c1: 280, c2: 0},    # 65099
                    'ancientloft': {c1: 280, c2: 0},      # 20147
                    'snowyforest': {c1: 300, c2: 0},      # 12986
                    'sulfurpools': {c1: 280, c2: 0},      # 16485
                    'voidstage': {c1: 220, c2: 0},        # 1404
                    }
    spawn_cards = {}
    scenes = {}
    for f in os.listdir(src_path):
        if (f.startswith('ror2-base') or f.startswith('ror2-dlc1')) and 'scenedef' in f:
            f = src_path + f
            scene_def = UnityPy.load(f)
            for def_container in scene_def.container.values():
                asset = def_container.get_obj().read_typetree()
                # Skipping the alternative stage 1 variations
                if asset['baseSceneNameOverride']:
                    continue
                # `sceneType = 1` are playable stages, but the Simulacrum ones and the
                # Planetarium are skipped here.
                # `sceneType = 2` are intermission stages, which are not interesting
                # except from maybe goldshores for monsters.
                # Other types are not playable anyway.
                name = asset['m_Name']
                if asset['sceneType'] == 1 and not name.startswith('it') and name != 'voidraid':
                    data = {'stage_order': asset['stageOrder']-1,
                            'requires_dlc': bool(asset['requiredExpansion']['m_PathID']),
                            **scenes_extra[name],
                            Version.BASE: {},
                            Version.DLC1: {},
                            }
                    scene_file = f.replace('scenedef', 'text')
                    # Manual hack for dampcavesimple and moon2 because they doesn't follow the pattern
                    if 'dampcave' in scene_file:
                        scene_file = scene_file.replace('simple', '')
                    elif 'moon2' in scene_file:
                        scene_file = scene_file.replace('moon2', 'moon')
                    scene_text = UnityPy.load(scene_file)
                    for key, text_container in scene_text.container.items():
                        asset_name = key.split('/')[-1]
                        if 'Interactables' in asset_name:
                            tree = text_container.get_obj().read_typetree()
                            if tree['m_Name'].startswith('dccs'):
                                ics = {}
                                for category in tree['categories']:
                                    cat_name = category['name']
                                    ics[cat_name] = {'weight': category['selectionWeight'],
                                                     'cards': []}
                                    for card in category['cards']:
                                        card_id = card['spawnCard']['m_PathID']
                                        spawn_cards[card_id] = None
                                        ics[cat_name]['cards'].append({
                                             'spawn_card_id': card_id,
                                             'weight': card['selectionWeight'],
                                             'min_stage': card['minimumStageCompletions'],
                                             })
                                # Manual hack because the Void Stage doesn't have DLC1 in the name
                                is_dlc = 'DLC1' in tree['m_Name'] or 'VoidStage' in tree['m_Name']
                                version = Version.DLC1 if is_dlc else Version.BASE
                                data[version] = ics
                    scenes[name] = data
    for f in os.listdir(src_path):
        if (f.startswith('ror2-base') or f.startswith('ror2-dlc1')) and 'text' in f:
            f = src_path + f
            env = UnityPy.load(f)
            for obj in env.objects:
                if obj.path_id in spawn_cards:
                    data = obj.read_typetree()
                    spawn_cards[obj.path_id] = {
                        'name': data['m_Name'],
                        'cost': data['directorCreditCost'],
                        'sacrifice_skip': bool(data['skipSpawnWhenSacrificeArtifactEnabled']),
                        'sacrifice_weight': data['weightScalarWhenSacrificeArtifactEnabled'],
                        'limit': data['maxSpawnsPerStage'],
                        }
    for card_id, data in spawn_cards.items():
        if not data:
            raise ValueError(f'The spawn card with ID {card_id} was not found.')
    with open(out_path, 'w') as f:
        json.dump([scenes, spawn_cards], f, indent=2)

def load_scene_data(src_path=ASSETS_DIRECTORY, out_path=SCENES_FILE):
    if not os.path.exists(out_path):
        print('Parsed data file does not exist. It will take a minute to extract form source.')
        _extract_from_assets(src_path, out_path)
    with open(out_path, 'r') as f:
        scene_data, spawn_cards = json.load(f)
    # The spawn card IDs are stored as strings, so we need to convert back to int
    spawn_cards = {int(key): data for key, data in spawn_cards.items()}
    return scene_data, spawn_cards
