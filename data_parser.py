import json
import math
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


def _get_component_raw(ids, go, component):
    for c in go['m_Component']:
        obj = ids[c['component']['m_PathID']]
        if obj.type.name == 'MonoBehaviour':
            _component = obj.read_typetree()
            if _component['m_Script']['m_PathID'] == component.SCRIPT:
                return _component


def _get_components_raw(ids, go, component):
    out = []
    for c in go['m_Component']:
        obj = ids[c['component']['m_PathID']]
        if obj.type.name == 'MonoBehaviour':
            _component = obj.read_typetree()
            if _component['m_Script']['m_PathID'] == component.SCRIPT:
                out.append(_component)
    return out


def _get_child_raw(ids, game_object, child_index):
    transform = ids[game_object['m_Component'][0]['component']['m_PathID']].read_typetree()
    children = transform['m_Children']
    if len(children) > child_index:
        child_transform = ids[children[child_index]['m_PathID']].read_typetree()
        return ids[child_transform['m_GameObject']['m_PathID']].read_typetree()


def _get_component(ids, prefab_id, component, keep_path_id=False):
    if not prefab_id:
        return None
    for c in ids[prefab_id]['m_Component']:
        _id = c['component']['m_PathID']
        if _id in ids:
            _component = ids[_id]
            if 'm_Script' in _component and _component['m_Script']['m_PathID'] == component.SCRIPT:
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


def _get_transform(ids, obj_id):
    if not obj_id:
        return
    for c in ids[obj_id]['m_Component']:
        _id = c['component']['m_PathID']
        if _id in ids:
            _component = ids[_id]
            if 'm_LocalPosition' in _component:
                return _component


def _extract_names(src_path=LANGUAGE_DIR):
    names = {}
    with open(path.join(src_path, 'output.json'), encoding='utf8') as f:
        for line in f.readlines():
            m = re.match('.*"([A-Z0-9_]+_NAME)".*:.*"(.*)".*\n', line)
            if m:
                names[m.group(1)] = m.group(2)
    return names


def _find_newt_group(groups, ids):
    for group in groups:
        if all(_is_newt_statue(o['m_PathID'], ids) for o in group['objects']):
            return group['minEnabled'], group['maxEnabled']


def _is_newt_statue(obj_id, ids):
    if _get_component(ids, obj_id, PortalStatueBehavior):
        return True
    # The statue could be nested in a child object which needs to be identified
    transform = _get_transform(ids, obj_id)
    if transform:
        return any(_is_newt_statue(ids[child['m_PathID']]['m_GameObject']['m_PathID'], ids)
                   for child in transform['m_Children'] if child['m_PathID'] in ids)
    return False


def _find_object(src_path, fname, object_name):
    env = UnityPy.load(path.join(src_path, fname))
    for obj in env.objects:
        if obj.type.name == 'GameObject':
            asset = obj.read_typetree()
            if asset['m_Name'] == object_name:
                return obj.path_id


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
    buffs = []
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
    masters = {'masters': {}, 'AI_driver': {}}
    skills = {}
    dccs = {}

    for fname in os.listdir(src_path):
        if re.match('(ror2-(base|dlc1|cu8|dlc2|junk)-.*_text)|(ror2-dlc1_assets_all.bundle)|(ror2-cu8_assets_all.bundle)|(ror2-dlc2_assets_all.bundle)', fname):
            env = UnityPy.load(path.join(src_path, fname))
            cabs = [cab for file, cab in env.cabs.items() if '.' not in file]
            for cab in cabs:
                objects = cab.objects
                for obj in objects.values():
                    if obj.type.name not in ('GameObject', 'MonoBehaviour'):
                        continue
                    asset = obj.read_typetree()
                    ids[obj.path_id] = asset
                    if obj.type.name == 'MonoBehaviour':
                        script = asset['m_Script']['m_PathID']
                        if script == BuffDef.SCRIPT:
                            buffs.append(BuffDef.parse(asset))
                        elif script == ItemDef.SCRIPT:
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
                            go = objects[asset['m_GameObject']['m_PathID']].read_typetree()
                            bodies[go['m_Name']] = CharacterBody.parse(asset, token_names)
                        elif script == CharacterMaster.SCRIPT:
                            go = objects[asset['m_GameObject']['m_PathID']].read_typetree()
                            masters['masters'][go['m_Name']] = CharacterMaster.parse(asset)
                        elif script == AISkillDriver.SCRIPT:
                            unique_name = f'{asset["customName"]},{obj.path_id}'
                            masters['AI_driver'][unique_name] = AISkillDriver.parse(asset)
                        elif script in skill_defs:
                            unique_name = f'{asset["m_Name"]},{obj.path_id}'
                            skills[unique_name] = skill_defs[script].parse(asset)
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
                token = token_names.get(token['displayToken'], token['displayToken']) if token else ''
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
        data['can_reset'] = _get_component(ids, data['can_reset'], DelusionChestController) is not None
        purchase = _get_component(ids, data['is_sale_star_compatible'], PurchaseInteraction)
        data['is_sale_star_compatible'] = bool(purchase['saleStarCompatible']) if purchase else False
        expansion = _get_component(ids, data['expansion'], ExpansionRequirementComponent)
        if expansion:
            data['expansion'] = ExpansionRequirementComponent.parse(expansion, ids)
        else:
            data['expansion'] = None
    for data in csc.values():
        master = _get_component(ids, data['body'], CharacterMaster)
        body, path_id = _get_component(ids, master['bodyPrefab']['m_PathID'], CharacterBody, keep_path_id=True)
        token = body['baseNameToken']
        data['name'] = token_names.get(token, token)
        data['body'] = ids[master['bodyPrefab']['m_PathID']]['m_Name']
        data['master'] = ids[master['m_GameObject']['m_PathID']]['m_Name']
        data['equipment'] = [ids[e]['m_Name'] for e in data['equipment'] if e]
        data['items'] = [(ids[i]['m_Name'], c) for i, c in data['items'] if i]
    for data in dccs.values():
        for category in data['categories']:
            for card in category['cards']:
                card['spawn_card'] = ids[card['spawn_card']]['m_Name'] if card['spawn_card'] else None
    for data in bodies.values():
        data['_name'] = ids[data['_name']]['m_Name']
        hurt_state = _get_component(ids, data['pain_threshold'], SetStateOnHurt)
        if hurt_state:
            hurt_state = SetStateOnHurt.parse(hurt_state)
            for key, value in hurt_state.items():
                data[key] = value
        else:
            data['pain_threshold'] = math.inf
            data['can_be_hit_stunned'] = False
            data['can_be_stunned'] = False
            data['can_be_frozen'] = False
        item_drop = _get_component(ids, data['item_drop'], DeathRewards)
        if item_drop:
            item_drop = item_drop['bossDropTable']['m_PathID']
            if item_drop:
                item_drop = ids[item_drop]['m_Name']
                item_drop = droptables[item_drop]['entries'][0][0]
            else:
                item_drop = None
        data['item_drop'] = item_drop
        expansion = _get_component(ids, data['expansion'], ExpansionRequirementComponent)
        if expansion:
            data['expansion'] = ExpansionRequirementComponent.parse(expansion, ids)
        else:
            data['expansion'] = None
    for name, data in masters['masters'].items():
        data['_name'] = name
        data['body'] = ids[data['body']]['m_Name'] if data['body'] else None
        ai = _get_component(ids, data['ai'], BaseAI)
        if ai:
            ai = BaseAI.parse(ai, ids)
            ai_drivers = _get_all_components(ids, data['ai'], AISkillDriver, keep_path_id=True)
            ai['drivers'] = [f'{s["customName"]},{path_id}' for s, path_id in ai_drivers]
        data['ai'] = ai
        pickups = _get_component(ids, data['pickups'], GivePickupsOnStart)
        if pickups:
            pickups = GivePickupsOnStart.parse(pickups, ids)
        data['pickups'] = pickups
    for data in masters['AI_driver'].values():
        for key in ('required_skill', 'next_high_priority'):
            path_id = data[key]
            name = 'm_Name' if key == 'required_skill' else 'customName'
            data[key] = f'{ids[path_id][name]},{path_id}' if path_id else None
    for data in skills.values():
        if data['class'] == 'PassiveItemSkillDef':
            data['passive_item'] = ids[data['passive_item']]['m_Name']

    combat_directors = {}
    d = _get_all_components(
        ids,
        _find_object(src_path, 'ror2-base-common_text_assets_all.bundle', 'Director'),
        CombatDirector,
    )
    for d_ in d:
        data = CombatDirector.parse(d_, ids)
        # Arbitrary limit which fits the pattern so far
        type_name = 'fast' if data['reroll_spawn_interval'][0] < 10 else 'slow'
        combat_directors[type_name] = data
    combat_directors['combat_shrine'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-base-shrinecombat_text_assets_all.bundle', 'ShrineCombat'),
        CombatDirector,
    ), ids)
    combat_directors['gouge'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-base-monstersonshrineuse_text_assets_all.bundle', 'MonstersOnShrineUseEncounter'),
        CombatDirector,
    ), ids)
    d = _get_all_components(
        ids,
        _find_object(src_path, 'ror2-base-teleporters_text_assets_all.bundle', 'Teleporter1'),
        CombatDirector,
    )
    combat_directors['teleporter_monsters'] = CombatDirector.parse(d[0], ids)
    combat_directors['teleporter_boss'] = CombatDirector.parse(d[1], ids)
    combat_directors['arena'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-base-arena_text_assets_all.bundle', 'ArenaMissionController'),
        CombatDirector,
    ), ids)
    combat_directors['moon_battery'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-base-moon2_text_assets_all.bundle', 'MoonBatteryTemplate'),
        CombatDirector,
    ), ids)
    combat_directors['void_battery'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-dlc1-deepvoidportalbattery_text_assets_all.bundle', 'DeepVoidPortalBattery'),
        CombatDirector,
    ), ids)
    combat_directors['voidcamp1'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-dlc1-voidcamp_text_assets_all.bundle', 'Camp 1 - Void Monsters & Interactables'),
        CombatDirector,
    ), ids)
    combat_directors['voidcamp2'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-dlc1-voidcamp_text_assets_all.bundle', 'Camp 2 - Flavor Props & Void Elites'),
        CombatDirector,
    ), ids)
    combat_directors['simulacrum'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-dlc1-gamemodes-infinitetowerrun-infinitetowerassets_text_assets_all.bundle', 'InfiniteTowerWaveDefault'),
        CombatDirector,
    ), ids)
    combat_directors['halcyon_shrine'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-dlc2_assets_all.bundle', 'ShrineHalcyonite'),
        CombatDirector,
    ), ids)
    combat_directors['halcyonite'] = CombatDirector.parse(_get_component(
        ids,
        _find_object(src_path, 'ror2-dlc2_assets_all.bundle', 'Activation and Tier Change Wave'),
        CombatDirector,
    ), ids)

    scenes = {}
    for fname in os.listdir(src_path):
        if re.match('ror2-(base|dlc1|cu8|dlc2)-.*_scenedef', fname):
            scene_def = UnityPy.load(path.join(src_path, fname))
            for def_container in scene_def.container.values():
                asset = def_container.get_obj().read_typetree()
                name = asset['m_Name']
                ids[def_container.get_obj().path_id] = asset
                # `sceneType == -1` are invalid
                # `sceneType == 0` are menu
                # `sceneType == 3` are cutscenes
                if asset['sceneType'] in (-1, 0, 3):
                    continue
                scene_ids = {}
                dlc_id = asset['requiredExpansion']['m_PathID']
                dlc_name = ids[dlc_id]['m_Name'] if dlc_id else None
                scene_data = {
                    'scene_type': asset['sceneType'],
                    'stage_order': asset['stageOrder']-1,
                    'required_dlc': dlc_name,
                    'destinations': asset['destinationsGroup']['m_PathID'],
                    'destinations_loop': asset['loopedDestinationsGroup']['m_PathID'],
                    'use_looping_destinations': bool(asset['shouldUpdateSceneCollectionAfterLooping']),
                    'skip_devotion': bool(asset['needSkipDevotionRespawn']),
                    'stage_info': None,
                    'scene_director': None,
                    'combat_director': None,
                    'newt': None,
                }
                scene_file = fname.replace('scenedef_assets', 'scenes')
                # Is this file changing with every update? Pain...
                if 'villagenight' in fname:
                    scene_file = 'ror2-dlc2-villagenight_scenes_all_162e96e97c434b84c2a48a63cc04280a.bundle'
                scene_all = UnityPy.load(path.join(src_path, scene_file))
                # 'blackbeach' has a test scene cabinet which we ignore
                cabinet = [cab for name, cab in scene_all.cabs.items() if '.' not in name][0]
                objects = cabinet.objects
                scene_info = None
                director = None
                for obj in objects.values():
                    if obj.type.name in ('GameObject', 'Transform', 'MonoBehaviour'):
                        asset = obj.read_typetree()
                        scene_ids[obj.path_id] = asset
                        if obj.type.name == 'GameObject':
                            if asset['m_Name'] == 'SceneInfo':
                                scene_info = asset
                            elif asset['m_Name'] in ('Director', 'InfiniteTowerSceneDirector'):
                                director = asset
                if scene_info:
                    asset = _get_component_raw(objects, scene_info, ClassicStageInfo)
                    if asset:
                        stage_info = ClassicStageInfo.parse(asset, ids)
                        stage_info['bonus_credits'] = sum(stage_info['bonus_credits'])
                        if not stage_info['monsters'] or not stage_info['interactables']:
                            text_file = fname.replace('scenedef', 'text')
                            scene_text = UnityPy.load(path.join(src_path, text_file))
                            for text_obj in scene_text.objects:
                                if text_obj.type.name == 'MonoBehaviour':
                                    text_asset = text_obj.read_typetree()
                                    if text_asset['m_Script']['m_PathID'] != DccsPool.SCRIPT:
                                        continue
                                    if 'Monsters' in text_asset['m_Name']:
                                        stage_info['monsters'] = DccsPool.parse(text_asset, ids)
                                    elif 'Interactables' in text_asset['m_Name']:
                                        stage_info['interactables'] = DccsPool.parse(text_asset, ids)
                        scene_data['stage_info'] = stage_info
                    # The SceneObjectToggleController is a child of
                    # SceneInfo, so we can get it from its transform.
                    toggle_controller = _get_child_raw(objects, scene_info, 0)
                    if toggle_controller:
                        toggle_groups = _get_component_raw(objects, toggle_controller, SceneObjectToggleGroup)
                        if toggle_groups:
                            scene_data['newt'] = _find_newt_group(toggle_groups['toggleGroups'], scene_ids)
                if director:
                    asset = _get_component_raw(objects, director, SceneDirector)
                    if asset:
                        scene_data['scene_director'] = SceneDirector.parse(asset, ids)
                    if director['m_Name'] == 'Director':
                        combat = _get_components_raw(objects, director, CombatDirector)
                        if combat:
                            combat_data = []
                            for i, c in enumerate(combat):
                                c = CombatDirector.parse(c, ids)
                                diff = {}
                                type_name = 'fast' if c['reroll_spawn_interval'][0] < 10 else 'slow'
                                compare_to = combat_directors[type_name]
                                for key, value in c.items():
                                    if value != compare_to[key]:
                                        diff[key] = value
                                combat_data.append({'name': type_name, 'overrides': diff})
                            scene_data['combat_director'] = combat_data
                scenes[name] = scene_data
    for data in scenes.values():
        destinations = []
        path_id = data['destinations']
        if path_id:
            for entry in ids[path_id]['_sceneEntries']:
                scene = ids[entry['sceneDef']['m_PathID']]
                destinations.append((scene['m_Name'], entry['weightMinusOne'] + 1))
        data['destinations'] = destinations
        destinations = []
        path_id = data['destinations_loop']
        if path_id:
            for entry in ids[path_id]['_sceneEntries']:
                scene = ids[entry['sceneDef']['m_PathID']]
                destinations.append((scene['m_Name'], entry['weightMinusOne'] + 1))
        data['destinations_loop'] = destinations
    # The reference in the assets is somehow lost, quick fix
    scenes['blackbeach2']['stage_info']['interactables'] = scenes['blackbeach']['stage_info']['interactables']

    voidcamps = {}
    text_file = 'ror2-dlc1-voidcamp_text_assets_all.bundle'
    scene_text = UnityPy.load(path.join(src_path, text_file))
    for obj in scene_text.objects:
        if obj.type.name in ('GameObject', 'MonoBehaviour'):
            asset = obj.read_typetree()
            ids[obj.path_id] = asset
            if 'Camp 1' in asset['m_Name'] or 'Camp 2' in asset['m_Name']:
                director = _get_component(ids, obj.path_id, CampDirector)
                data = CampDirector.parse(director)
                data['name'] = asset['m_Name']
                data['interactables'] = ids[data['interactables']]['m_Name']
                monsters_file = ids[data['monsters']]['_monsterCards']['m_PathID']
                data['monsters'] = ids[monsters_file]['m_Name'] if monsters_file else None
                voidcamps['camp1' if 'Camp 1' in asset['m_Name'] else 'camp2'] = data

    simulacrum = {}
    env = UnityPy.load(path.join(FILES_DIR, 'ror2-dlc1-gamemodes-infinitetowerrun_text_assets_all.bundle'))
    for obj in env.objects:
        if obj.type.name == 'MonoBehaviour':
            asset = obj.read_typetree()
            if asset['m_Script']['m_PathID'] == InfiniteTowerRun.SCRIPT:
                simulacrum = InfiniteTowerRun.parse(asset, ids)
                for category in simulacrum['wave_categories']:
                    for wave in category['waves']:
                        for cls in (
                            InfiniteTowerWaveController,
                            InfiniteTowerBossWaveController,
                            InfiniteTowerExplicitWaveController,
                        ):
                            controller = _get_component(ids, wave['wave'], cls)
                            if controller:
                                data = cls.parse(controller, ids)
                                data['name'] = ids[wave['wave']]['m_Name']
                                wave['wave'] = data
                                break

    buffs.sort(key=lambda x: x['_name'])
    items.sort(key=lambda x: x['_name'])
    equipment.sort(key=lambda x: x['_name'])
    droptables = {key: droptables[key] for key in sorted(droptables)}
    item_tiers = {key: item_tiers[key] for key in sorted(item_tiers, key=lambda x: item_tiers[x]['_tier'])}
    sc = {key: sc[key] for key in sorted(sc)}
    isc = {key: isc[key] for key in sorted(isc)}
    csc = {key: csc[key] for key in sorted(csc)}
    masters['masters'] = {key: masters['masters'][key] for key in sorted(masters['masters'])}
    drivers_sorted_keys = []
    for master in masters['masters'].values():
        if master['ai']:
            drivers_sorted_keys.extend(master['ai']['drivers'])
    masters['AI_driver'] = {key: masters['AI_driver'][key] for key in drivers_sorted_keys}
    bodies = {key: bodies[key] for key in sorted(bodies)}
    dccs = {key: dccs[key] for key in sorted(dccs)}
    scenes = {key: scenes[key] for key in sorted(scenes)}

    for fname, data in (
        (BUFFS_FILE, buffs),
        (ITEMS_FILE, items),
        (EQUIPMENT_FILE, equipment),
        (DROPTABLES_FILE, droptables),
        (TIERS_FILE, item_tiers),
        (SC_FILE, sc),
        (ISC_FILE, isc),
        (CSC_FILE, csc),
        (MASTERS_FILE, masters),
        (BODIES_FILE, bodies),
        (SKILLS_FILE, skills),
        (DCCS_FILE, dccs),
        (COMBAT_FILE, combat_directors),
        (SCENES_FILE, scenes),
        (CAMP_FILE, voidcamps),
        (SIMULACRUM_FILE, simulacrum),
    ):
        with open(fname, 'w') as f:
            json.dump(data, f, indent=2)
