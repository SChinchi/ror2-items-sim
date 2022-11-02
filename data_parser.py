import json
import os
import os.path as path
import re

import UnityPy

from data.dirpaths import *
from data.objects import *


DIR_TO_STEAM = 'C:/Games'  # Just change this
ASSETS_DIR = path.join(DIR_TO_STEAM, 'Steam/steamapps/common/Risk of Rain 2/Risk of Rain 2_Data/StreamingAssets')
LANGUAGE_DIR = path.join(ASSETS_DIR, 'Language/en')
FILES_DIR = path.join(ASSETS_DIR, 'aa/StandaloneWindows64')


def _get_component(ids, prefab_id, component, keep_path_id=False):
    for c in ids[prefab_id]['m_Component']:
        _id = c['component']['m_PathID']
        if _id in ids:
            _component = ids[_id]
            if _component['m_Script']['m_PathID'] == component.SCRIPT:
                if keep_path_id:
                    return _component, _id
                return _component


def _get_all_components(ids, prefab_id, component, keep_path_id=False):
    out = []
    for c in ids[prefab_id]['m_Component']:
        _id = c['component']['m_PathID']
        if _id in ids:
            _component = ids[_id]
            if _component['m_Script']['m_PathID'] == component.SCRIPT:
                if keep_path_id:
                    out.append((_component, _id))
                else:
                    out.append(_component)
    return out


def _extract_names(src_path=LANGUAGE_DIR):
    names = {}
    for file in ('Equipment', 'InfiniteTower', 'Interactors', 'Items', 'CharacterBodies'):
        enc = 'utf8' if file == 'CharacterBodies' else None
        with open(path.join(src_path, f'{file}.txt'), encoding=enc) as f:
            for line in f.readlines():
                m = re.match('.*"([A-Z0-9_]+_NAME)".*:.*"(.*)".*\n', line)
                if m:
                    names[m.group(1)] = m.group(2)
    return names


def extract_file_data(src_path=FILES_DIR):
    """
    Extract data from the asset files in the game and store in json files.

    This includes data on items, equipment, item tiers, droptables, bodies,
    spawn cards, director card categories, and scenes.

    Parameters
    ----------
    src_path : str
        Directory to the asset files.

    Returns
    -------
    None
    """
    token_names = _extract_names()
    skill_defs = (
        SkillDef, CaptainOrbitalSkillDef, CaptainSupplyDropSkillDef, EngiMineDeployerSkillDef,
        GroundedSkillDef, HuntressTrackingSkillDef, LunarDetonatorSkill,
        LunarPrimaryReplacementSkill, LunarSecondaryReplacementSkill, MasterSpawnSlotSkillDef,
        MercDashSkillDef, PassiveItemSkillDef, RailgunSkillDef, ReloadSkillDef, SteppedSkillDef,
        ToolbotWeaponSkillDef, VoidRaidCrabBodySkillDef, VoidSurvivorSkillDef,
    )
    skill_defs = {s.SCRIPT: s for s in skill_defs}
    dt_classes = (
        ArenaMonsterItemDropTable, BasicPickupDropTable, DoppelgangerDropTable,
        ExplicitPickupDropTable, FreeChestDropTable,
    )
    dt_classes = {s.SCRIPT: s for s in dt_classes}
    csc_classes = {s.SCRIPT: s for s in (CharacterSpawnCard, MultiCharacterSpawnCard)}
    dccs_classes = {s.SCRIPT: s for s in (DirectorCardCategorySelection, FamilyDirectorCardCategorySelection)}
    
    ids = {}
    items = []
    equipment = []
    # Initialising the "NoTier" pair here because it's not defined in the game.
    # We define its values here based on how it behaves, but in the game when
    # an item has "NoTier" tier, it passes around its "deprecatedTier" instead.
    item_tiers = {'NoTier': {
        '_name': 'NoTier',
        '_tier': 5,
        'is_droppable': False,
        'can_scrap': False,
        'can_restack': False,        
    }}
    droptables = {}
    sc = {}
    isc = {}
    csc = {}
    bodies = {}
    masters = []
    skills = {'masters': {}, 'AI_driver': {}, 'skills': {}}
    dccs = {}
    for fname in os.listdir(src_path):
        if re.match('(ror2-(base|dlc1|junk)-.*_text)|(ror2-dlc1_assets_all.bundle)', fname):
            env = UnityPy.load(path.join(src_path, fname))
            for obj in env.objects:
                if obj.type.name not in ('GameObject', 'MonoBehaviour'):
                    continue
                asset = obj.read_typetree()
                ids[obj.path_id] = asset
                if obj.type.name == 'MonoBehaviour':
                    script = asset['m_Script']['m_PathID']
                    if script == ItemDef.SCRIPT:
                        items.append(ItemDef.parse(asset, token_names))
                    elif script == EquipmentDef.SCRIPT:
                        equipment.append(EquipmentDef.parse(asset, token_names))
                    elif script == ItemTierDef.SCRIPT:
                        item_tiers[asset['m_Name'].rstrip('Def')] = ItemTierDef.parse(asset)
                    elif script in dt_classes:
                        droptables[asset['m_Name']] = dt_classes[script].parse(asset)
                    elif script == SpawnCard.SCRIPT:
                        sc[asset['m_Name']] = SpawnCard.parse(asset)
                    elif script == InteractableSpawnCard.SCRIPT:
                        isc[asset['m_Name']] = InteractableSpawnCard.parse(asset)
                    elif script in csc_classes:
                        csc[asset['m_Name']] = csc_classes[script].parse(asset)
                    elif script == CharacterBody.SCRIPT:
                        unique_name = f'{asset["baseNameToken"]},{obj.path_id}'
                        bodies[unique_name] = CharacterBody.parse(asset, token_names)
                    elif script == CharacterMaster.SCRIPT:
                        # To be parsed once all file ids have been collected
                        masters.append(asset['m_GameObject']['m_PathID'])
                    elif script == AISkillDriver.SCRIPT:
                        unique_name = f'{asset["customName"]},{obj.path_id}'
                        skills['AI_driver'][unique_name] = AISkillDriver.parse(asset)
                    elif script in skill_defs:
                        unique_name = f'{asset["m_Name"]},{obj.path_id}'
                        skills['skills'][unique_name] = skill_defs[script].parse(asset)
                    elif script in dccs_classes:
                        dccs[asset['m_Name']] = dccs_classes[script].parse(asset)
    for item_type in (items, equipment):
        for item in item_type:
            dlc_id = item['required_dlc']
            item['required_dlc'] = ids[dlc_id]['m_Name'] if dlc_id else None
    for item in items:
        for name, data in item_tiers.items():
            if item['tier'] == data['_tier']:
                item['tier'] = name
                break
    for data in droptables.values():
        if data['class'] == 'ExplicitPickupDropTable':
            for entry in data['entries']:
                entry[0] = ids[entry[0]]['m_Name']
    for data in sc.values():
        data['name'] = ''
    for name, data in isc.items():
        if 'TripleShop' in name or 'FreeChest' in name:
            multishop = _get_component(ids, data['name'], MultiShopController)
            dt = _get_component(
                ids, multishop['terminalPrefab']['m_PathID'], ShopTerminalBehavior
            )
            dt = ids[dt['dropTable']['m_PathID']]['m_Name']
            interaction = _get_component(
                ids, multishop['terminalPrefab']['m_PathID'], PurchaseInteraction
            )
            token = token_names[interaction['displayNameToken']]
            if dt == 'dtTier1Item':
                token += ' (White)'
            elif dt == 'dtTier2Item':
                token += ' (Green)'
            elif dt == 'dtEquipment':
                token += ' (Equipment)'
            else:
                token += ' (Shipping Request Form)'
        elif 'Duplicator' in name:
            dt = _get_component(ids, data['drop_table'], ShopTerminalBehavior)
            dt = ids[dt['dropTable']['m_PathID']]['m_Name']
            interaction = _get_component(ids, data['name'], PurchaseInteraction)
            token = token_names[interaction['displayNameToken']]
            if dt == 'dtDuplicatorTier1':
                token += ' (White)'
            elif dt == 'dtDuplicatorTier2':
                token += ' (Green)'
            elif dt == 'dtDuplicatorWild':
                token += ' (Overgrown)'
        else:
            dt = (
                _get_component(ids, data['drop_table'], ChestBehavior) or
                _get_component(ids, data['drop_table'], RouletteChestController) or
                _get_component(ids, data['drop_table'], ShopTerminalBehavior) or
                _get_component(ids, data['drop_table'], ShrineChanceBehavior) or
                _get_component(ids, data['drop_table'], OptionChestBehavior)
            )
            dt = ids[dt['dropTable']['m_PathID']]['m_Name'] if dt else None
            interaction = (
                _get_component(ids, data['name'], PurchaseInteraction) or
                _get_component(ids, data['name'], BarrelInteraction)
            )
            if interaction:
                token = token_names[interaction['displayNameToken']]
            else:
                token = _get_component(ids, data['name'], GenericDisplayNameProvider)
                token = token_names[token['displayToken']] if token else ''
        data['name'] = token
        data['drop_table'] = dt
        controller_name = None
        for controller in (ChestBehavior, RouletteChestController, MultiShopController,
                           ShopTerminalBehavior, ShrineChanceBehavior, OptionChestBehavior):
            component = _get_component(ids, data['controller'], controller)
            if component:
                controller_name = controller.__name__
        data['controller'] = controller_name
        data['offers_choice'] = bool(
            _get_component(ids, data['offers_choice'], ShopTerminalBehavior) or
            _get_component(ids, data['offers_choice'], MultiShopController) or
            _get_component(ids, data['offers_choice'], ScrapperController)
        )
    for data in csc.values():
        master = _get_component(ids, data['body'], CharacterMaster)
        body, path_id = _get_component(ids, master['bodyPrefab']['m_PathID'], CharacterBody, keep_path_id=True)
        token = body['baseNameToken']
        data['name'] = token_names.get(token, token)
        data['body'] = f'{token},{path_id}'
        data['master'] = ids[master['m_GameObject']['m_PathID']]['m_Name']
    for data in dccs.values():
        for category in data['categories']:
            for card in category['cards']:
                card['spawn_card'] = ids[card['spawn_card']]['m_Name']
    for data in bodies.values():
        item_drop = _get_component(ids, data['item_drop'], DeathRewards)
        if item_drop:
            item_drop = item_drop['bossDropTable']['m_PathID']
            if item_drop:
                item_drop = ids[item_drop]['m_Name']
                item_drop = droptables[item_drop]['entries'][0][0]
            else:
                item_drop = None
        data['item_drop'] = item_drop
    for master_id in masters:
        master_name = ids[master_id]['m_Name']
        ai_skills = _get_all_components(ids, master_id, AISkillDriver, keep_path_id=True)
        ai_skills = [f'{s["customName"]},{path_id}' for s, path_id in ai_skills]
        skills['masters'][master_name] = ai_skills
    for data in skills['AI_driver'].values():
        for key in ('required_skill', 'next_high_priority'):
            path_id = data[key]
            data[key] = f'{ids[path_id]["m_Name"]},{path_id}' if path_id else None
    for data in skills['skills'].values():
        if data['class'] == 'PassiveItemSkillDef':
            data['passive_item'] = ids[data['passive_item']]['m_Name']

    scenes = {}
    for fname in os.listdir(src_path):
        if re.match('ror2-(base|dlc1)-.*_scenedef', fname):
            scene_def = UnityPy.load(path.join(src_path, fname))
            for def_container in scene_def.container.values():
                asset = def_container.get_obj().read_typetree()
                # Skipping the alternative stage 1 variations
                if asset['baseSceneNameOverride']:
                    continue
                # `sceneType == 1` are playable stages
                # `sceneType == 2` are intermission stages
                # Other scene types are not playable
                name = asset['m_Name']
                if asset['sceneType'] in (1, 2):
                    dlc_id = asset['requiredExpansion']['m_PathID']
                    dlc_name = ids[dlc_id]['m_Name'] if dlc_id else None
                    scene_data = {
                        'scene_type': asset['sceneType'],
                        'stage_order': asset['stageOrder']-1,
                        'required_dlc': dlc_name,
                        'stage_info': None,
                        'scene_director': None,
                    }
                    scene_file = fname.replace('scenedef_assets', 'scenes')
                    scene_all = UnityPy.load(path.join(src_path, scene_file))
                    for obj in scene_all.objects:
                        if obj.type.name == 'MonoBehaviour':
                            asset = obj.read_typetree()
                            script = asset['m_Script']['m_PathID']
                            if script == ClassicStageInfo.SCRIPT:
                                # Distant Roost has two files, and we're
                                # skipping the old one with 180 credits.
                                if 'beach' in fname and asset['m_GameObject']['m_PathID'] == 856:
                                    continue
                                stage_info = ClassicStageInfo.parse(asset, ids)
                                stage_info['bonus_credits'] = sum(stage_info['bonus_credits'])
                                # The Simulacrum Abyssal Depths doesn't have a
                                # reference to its Monster DccsPool, so we have
                                # to set it manually.
                                if 'itdampcave' in scene_file:
                                    text_file = fname.replace('scenedef', 'text')
                                    scene_text = UnityPy.load(path.join(src_path, text_file))
                                    for text_obj in scene_text.objects:
                                        if text_obj.type.name == 'MonoBehaviour':
                                            text_asset = text_obj.read_typetree()
                                            if (text_asset['m_Script']['m_PathID'] == DccsPool.SCRIPT and
                                                'Monsters' in text_asset['m_Name']):
                                                stage_info['monsters'] = DccsPool.parse(text_asset, ids)
                                scene_data['stage_info'] = stage_info
                            elif script == SceneDirector.SCRIPT:
                                if 'beach' in fname and asset['m_GameObject']['m_PathID'] == 2312:
                                    continue
                                scene_data['scene_director'] = SceneDirector.parse(asset, ids)
                    scenes[name] = scene_data

    voidcamps = {}
    text_file = 'ror2-dlc1-voidcamp_text_assets_all.bundle'
    scene_text = UnityPy.load(path.join(src_path, text_file))
    for obj in scene_text.objects:
        if obj.type.name in ('GameObject', 'MonoBehaviour'):
            asset = obj.read_typetree()
            ids[obj.path_id] = asset
            if 'Camp 1' in asset['m_Name'] or 'Camp 2' in asset['m_Name']:
                voidcamps[asset['m_Name']] = obj.path_id
    for obj_name, obj_id in voidcamps.items():
        director = _get_component(ids, obj_id, CampDirector)
        data = CampDirector.parse(director)
        data['interactables'] = ids[data['interactables']]['m_Name']
        monsters_file = ids[data['monsters']]['_monsterCards']['m_PathID']
        data['monsters'] = ids[monsters_file]['m_Name'] if monsters_file else None
        voidcamps[obj_name] = data

    simulacrum = {}
    env = UnityPy.load(path.join(FILES_DIR, 'ror2-dlc1-gamemodes-infinitetowerrun-infinitetowerassets-infinitetowerwavecategories_text_assets_all.bundle'))
    for obj in env.objects:
        if obj.type.name == 'MonoBehaviour':
            asset = obj.read_typetree()
            data = []
            for wave in asset['wavePrefabs']:
                requirement = wave['prerequisites']['m_PathID']
                prefab_id = wave['wavePrefab']['m_PathID']
                for cls in (
                    InfiniteTowerWaveController,
                    InfiniteTowerBossWaveController,
                    InfiniteTowerExplicitWaveController,
                ):
                    controller = _get_component(ids, prefab_id, cls)
                    if controller:
                        wave_data = cls.parse(controller, ids)
                        break
                data.append({
                    'name': ids[prefab_id]['m_Name'],
                    'wave': wave_data,
                    'prerequisites': ids[requirement]['m_Name'] if requirement else None,
                    'weight': wave['weight'],
                })
            category = 'common' if 'Common' in asset['m_Name'] else 'boss'
            simulacrum[category] = data

    for fname, data in (
        (ITEMS_FILE, items),
        (EQUIPMENT_FILE, equipment),
        (DROPTABLES_FILE, droptables),
        (TIERS_FILE, item_tiers),
        (SC_FILE, sc),
        (ISC_FILE, isc),
        (CSC_FILE, csc),
        (BODIES_FILE, bodies),
        (SKILLS_FILE, skills),
        (DCCS_FILE, dccs),
        (SCENES_FILE, scenes),
        (CAMP_FILE, voidcamps),
        (SIMULACRUM_FILE, simulacrum),
    ):
        with open(fname, 'w') as f:
            json.dump(data, f, indent=2)
