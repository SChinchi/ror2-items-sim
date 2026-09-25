from collections import Counter, defaultdict
import random

from constants import SceneName, Portal, Expansion, ALL_EXPANSIONS
from data_loader import ItemTiers, Items, Equipment, isc, droptables, bodies, scenes
from data.objects import EquipmentDef, ItemDef
from data.objects.dccs import FamilyDirectorCardCategorySelection
from data.objects.interactables import *
from directors import SceneDirector, CampDirector


BLUE_PORTAL_CHANCE = .05
PURPLE_PORTAL_CHANCE = .1
BOSS_DROP_CHANCE = .15

CARD_BIAS_ENABLED = True
LOCKBOX_ALLOWED = True
FREE_CHEST_ALLOWED = True
TRADE_REGEN_SCRAP = True

USE_GOLD_PORTAL = False
USE_ARTIFACT_PORTAL = False
USE_GREEN_PORTAL = False
USE_ENCRYPTED_PORTAL = False

# All items are picked up indiscriminately for item tier statistics, but Purity
# can have negative effects for luck rolls, so we need to know whether in a
# normal run one intends to actually pick it up.
USE_PURITY = False

class LootReport:
    """Logger for stats about spawned interactables and loot during a run."""
    def __init__(self, tier_droplists, inventory):
        """
        Create a loot logger.
        
        Parameters
        ----------
        tier_droplists : list
            A list of all the items available for each tier.
        inventory : Inventory
            The unified inventory of the survivors for the run.

        Returns
        -------
        None
        """
        self._tier_droplists = tier_droplists
        self._inventory = inventory
        self.scenes = []
        self.portals = []
        self.dccs = []
        self.interactables = []
        self.loot = []
        self.item_count = []
        self.free_chest_items = []
        self.card_multibuys = []
        self.delusion_loot = []

    def reset_data(self):
        """Reset the logger data."""
        self.scenes.clear()
        self.portals.clear()
        self.dccs.clear()
        self.interactables.clear()
        self.loot.clear()
        self.item_count.clear()
        self.free_chest_items.clear()
        self.card_multibuys.clear()
        self.delusion_loot.clear()

    def update_data(self, scene_name, spawned_portals, dccs, interactables,
                    loot, free_chest_items, card_multibuys, delusion_loot):
        """
        Update the logger data.

        This should be called at the end of each stage.

        Parameters
        ----------
        scene_name : str
            The name of the current scene.
        spawned_portals : list
            A list of booleans for the portals spawned. They are expected to be
            in the order Blue, Gold, and Purple Portal. The Celestial, Artifact,
            and Deep Purple Portals are not tracked as they have predictable
            spawn conditions.
        dccs : DirectorCardCategorySelection
            The selected scene DCCS for spawning mosters. This can be used to
            check if a family event was triggered.
        interactables : list
            A list of the interactable spawn cards for the stage.
        loot : list
            A list of all loot obtained for the stage, including any boss drops.
        free_chest_items : list
            Any loot obtained from Shipping Request Forms.
        card_multibuys : list
            A list of multishop interactables for which all loot was purchased
            using an Executive Card.
        delusion_loot : list
            A list of all loot from chests that can be reset with this Artifact.

        Returns
        -------
        None
        """
        self.scenes.append(scene_name)
        self.portals.append(spawned_portals)
        self.dccs.append(dccs.name if dccs else 'None')
        self.interactables.append(interactables)
        self.loot.append(loot)
        item_count = [self._inventory.count(item) for item in
            (Items.TreasureCache, Items.TreasureCacheVoid, Items.FreeChest, Items.RegeneratingScrap)
        ]
        item_count.append(item_count[-1] * ('iscDuplicatorLarge' in interactables))
        self.item_count.append(item_count)
        self.free_chest_items.append(free_chest_items)
        self.card_multibuys.append(card_multibuys)
        self.delusion_loot.append(delusion_loot)

    def consolidate_data(self):
        """
        Consolidate and report the results spanning the whole run.

        Returns
        -------
        out : dict
            A dictionary of various stats and data:
            - 'scenes': The internal name of all visited environments. For
                Abyssal Depths it also marks whether the cave was open.
            - 'portals': The total number of Blue/Gold/Purple portals spawned.
            - 'interactables': A counter with all spawned interactables.
            - 'items': A counter with all items collected.
            - 'equipment': A counter with all equipment collected.
            - 'tiers': A counter for how many items of each tier the player has
                acquired by the end of the run. Derivative from the inventory.
            - 'free_chest_item_tiers': A list of the tier of all items purchased
                from any Shipping Request Forms. This represents the number of
                Common, Uncommon, and Legendary items in order.
            - 'at_least_once': A counter for the total number of various
                interactables spawning at least once per stage, e.g., Scrapper.
            - 'at_stage_end': A counter for the amount of specific items the
                player had at the end of each stage. This is mostly for items
                with the 'OnStageBegin' tag, such as, Rusted Keys.
            - 'total': A counter fcr the total number of various interactables
                and items encountered during the run. This is derivative from
                other data, but it's generally useful to have convenient access.
            - 'card': Data about the Executive Card, i.e., on which stage it
                was first found (-1 for never), the total number of Multishop
                Terminals encountered, and the number of Multishop Terminals
                purchased while holding the Executive Card. The data regarding
                the Multishops are in a list of 4 numbers, related to Common,
                Uncommon, Equipment, and Shipping Request Form respectively.
            - 'delusion_bonus': The number of items of the tiers 1-3 obtained
                by interacting with chests that are reset by the respective
                artifact. For each stage it is a list of 3 values, one for each
                tier.
        """
        out = {
            'scenes': self.scenes,
            'portals': [sum(portal in stage_portals for stage_portals in self.portals)
                        for portal in (Portal.B, Portal.G, Portal.V)],
        }
        isc_counter = Counter()
        for interactables in self.interactables:
            isc_counter.update(interactables)
        out['interactables'] = isc_counter
        out['items'] = dict(self._inventory.items)
        equipment_counter = Counter()
        for loot in self.loot:
            equipment_counter.update(loot[EquipmentDef])
        out['equipment'] = equipment_counter
        item_tiers = [0] * len(self._tier_droplists)
        tier_lookup = {
            ItemTiers.Tier1: 0,
            ItemTiers.Tier2: 1,
            ItemTiers.Tier3: 2,
            ItemTiers.BossTier: 3,
            ItemTiers.LunarTier: 5,
            ItemTiers.VoidTier1: 8,
            ItemTiers.VoidTier2: 9,
            ItemTiers.VoidTier3: 10,
            ItemTiers.VoidBoss: 11,
        }
        for item, count in self._inventory.items.items():
            item_tiers[tier_lookup[item.tier]] += count
        for item, count in equipment_counter.items():
            if item.is_lunar:
                item_tiers[4] += count
            else:
                item_tiers[7] += count
        item_tiers[6] = item_tiers[4] + item_tiers[5]
        out['tiers'] = item_tiers
        free_chest_item_tiers = [item.tier._tier for stage_items in self.free_chest_items for item in stage_items]
        free_chest_item_tiers = [free_chest_item_tiers.count(i) for i in range(3)]
        out['free_chest_item_tiers'] = free_chest_item_tiers
        at_least_once = {}
        for isc_name, name in (
            ('iscScrapper', 'scrapper'),
            ('iscShrineCleanse', 'cleansing_pool'),
            ('iscVoidCamp', 'void_seed'),
        ):
            at_least_once[name] = sum(any(isc_name in isc for isc in stage_isc) for stage_isc in self.interactables)
        out['at_least_once'] = at_least_once
        item_count = zip(*self.item_count)
        out['at_stage_end'] = {
            name: value
            for name, value in zip(
                ('rusted_key', 'encrusted_key', 'SRF', 'regen_scrap', 'regen_scrap_used'),
                item_count
            )
        }
        total = {'family_event': sum(bool(dccs) and isinstance(dccs, FamilyDirectorCardCategorySelection)
                                     for dccs in self.dccs)}
        for isc_name, name in (
            ('iscShrineBoss', 'mountain_shrine'),
            ('iscChest1Stealthed', 'cloaked_chect'),
            ('iscLockbox', 'rusted_lockbox'),
            ('iscLockboxVoid', 'encrusted_lockbox'),
            ('iscCasinoChest', 'adaptive_chest'),
            ('iscVoidCamp', 'void_seed'),
            ('iscVoidChest', 'void_cradle'),
            ('iscShrineHalcyonite', 'halcyonite'),
            ('iscTemporaryItemsShop', 'temp_item_shop'),
            ('iscTripleDroneShop', 'drone_shop'),
            ('iscDroneCombinerStation', 'drone_combiner'),
            ('iscDroneScrapper', 'drone_scrapper')
        ):
            total[name] = isc_counter.get(isc_name, 0)
        total['mountain_shrine'] += isc_counter.get('iscShrineBossSandy', 0)
        total['mountain_shrine'] += isc_counter.get('iscShrineBossSnowy', 0)
        total['void_cradle'] += isc_counter.get('iscVoidChestSacrificeOn', 0)
        total['halcyonite'] += isc_counter.get('iscShrineHalcyoniteTier1', 0)
        total['drones'] = sum(count for isc, count in isc_counter.items() if 'iscBroken' in isc)
        total['tricorn'] = equipment_counter.get(Equipment.BossHunter, 0)
        out['total'] = total
        stage_card_found = -1
        for stage, loot in enumerate(self.loot):
            if Equipment.MultiShopCard in loot[EquipmentDef]:
                # This isn't necessary the number of cleared stages if Hidden
                # Realms have been visited. Use the result from `out['scenes']`
                # to deduce that.
                stage_card_found = stage
                break
        terminals = (
            'iscTripleShop',
            'iscTripleShopLarge',
            'iscTripleShopEquipment',
            'iscFreeChest',
        )
        multishops = []
        for terminal in terminals:
            multishops.append(isc_counter.get(terminal, 0))
        card_multishops = [0, 0, 0, 0]
        for card_multibuys in self.card_multibuys:
            if card_multibuys:
                for i, terminal in enumerate(terminals):
                    card_multishops[i] += card_multibuys.count(terminal)
        out['card'] = {
            'stage': stage_card_found,
            'multishops': multishops,
            'card_multishops': card_multishops,
        }
        delusion = [Counter([item.tier._tier for item in loot]) for loot in self.delusion_loot]
        out['delusion_bonus'] = [[d.get(i, 0) for i in range(3)] for d in delusion]
        return out


class Inventory:
    """Storage for the items and equipments acquired during a run."""
    def __init__(self):
        """Create an inventory."""
        self.items = defaultdict(int)
        self.equipment = []
        self.has_recycler = False
        self.can_recycle = False
        self.has_card = False
        self.luck = 0

    def _update_luck(self):
        self.luck = self.count(Items.Clover) + USE_PURITY * self.count(Items.LunarBadLuck)
        
    def give_item(self, item, count=1):
        """
        Grant an item to the player.

        Parameters
        ----------
        item : ItemDef
            The picked up item.
        count : int, optional
            The number of copies to grant.

        Returns
        -------
        None
        """
        if not isinstance(item, ItemDef):
            raise ValueError(f'{item} is not an ItemDef.')
        if count < 0:
            self.remove_item(item, -count)
            return
        self.items[item] += count
        self._update_luck()
        
    def remove_item(self, item, count=1):
        """
        Take away an amount from an item.

        Parameters
        ----------
        item : ItemDef
            The item to remove.
        count : int, optional
            The number of copies to remove. If all copies are removed, the item
            will completely leave the inventory.

        Returns
        -------
        None
        """
        if not isinstance(item, ItemDef):
            raise ValueError(f'{item} is not an ItemDef.')
        if count < 0:
            self.give_item(item, -count)
            return
        if item in self.items:
            self.items[item] -= count
            if self.items[item] <= 0:
                del self.items[item]
            self._update_luck()

    def count(self, item):
        """
        Count how many copies of an item exist in the inventory.

        Parameters
        ----------
        item : ItemDef
            The item of interest.

        Returns
        -------
        int
            The number of copies. If the item doesn't exist, it will be zero.
        """
        return self.items.get(item, 0)

    def count_by_name(self, item_name):
        """
        Count how many copies of an item exist in the inventory.

        This uses a lookup of the item based on its internal name.

        Parameters
        ----------
        item_name : str
            The internal name of the item.

        Returns
        -------
        int
            The number of copies. If the item doesn't exist, it will be zero.
        """
        item = getattr(Items, item_name)
        return self.count(item)

    def reset(self):
        """Reset the Inventory state."""
        self.items.clear()
        self.equipment.clear()
        self.has_card = False
        self.has_recycler = False
        self.can_recycle = False
        self.luck = 0


class Run:
    """Simulates a run by full looting a number of stages."""
    def __init__(self, num_players=1, expansions=ALL_EXPANSIONS, is_delusion_enabled=False):
        """
        Initialise the run session.

        Parameters
        ----------
        num_players : int, optional
            The number of players. This affects the available amount of
            interactable credits for scene population.
        expansions : set, optional
            The list of enabled expansions, which adds new scenes and
            interactables. By default they are all enabled.
        is_delusion_enabled : bool, optional
            Whether the Artifact of Delusion is enabled. This guarantees
            double loot from all chests that can be reset at the end of
            the Teleporter Event or Artifact Trial. Assumes that all
            such chests have been looted before the reset and that they
            are all then guessed correctly. Disabled by default.

        Returns
        -------
        None
        """
        self._num_players = num_players
        self._expansions = set(expansions)
        self._is_sotv_enabled = Expansion.SOTV in self._expansions
        self._is_sots_enabled = Expansion.SOTS in self._expansions
        self._is_ac_enabled = Expansion.AC in self._expansions
        self._is_command_enabled = False
        self._is_sacrifice_enabled = False
        self._is_delusion_enabled = is_delusion_enabled
        # Bogus scene just to initialise the director; it will be rerolled
        self._scene_director = SceneDirector(
            SceneName.DR,
            num_players=num_players,
            expansions=self._expansions,
            is_command_enabled=self._is_command_enabled,
            is_sacrifice_enabled=self._is_sacrifice_enabled,
        )
        self._camp_director = CampDirector(self._is_sacrifice_enabled)
        self._tier_droplists = self.build_tier_droplists(self._expansions)
        # This is a unified inventory, shared among all survivors. The only
        # items that matter for spreading evenly are those with on-begin-stage
        # effects, i.e., Rusty Lockbox, Shipping Request Form, and Encrusted
        # Cache. Therefore, on populating a scene we only need to spawn
        # `min(self._inventory.count(<relevant_item>), self._num_players)`.
        # That makes corruption a nightmare to track in general, so this
        # implementation doesn't support the Encrusted Cache.
        self._inventory = Inventory()
        self._actions = self._generate_drop_actions()
        self.stats = LootReport(self._tier_droplists, self._inventory)
        self._restart()

    def _restart(self):
        """Initialise variables for a session."""
        self._stages_cleared = 0
        self._scene_name = self._pick_next_stage_scene(scenes[SceneName.SM].destinations)
        self._scene_data = scenes[self._scene_name]
        self._scene_director.scene_name = self._scene_name
        self._next_scene_name = None
        self._explicit_next_scene_name = None
        self._blue_portals_opened = 0
        self._void_fields_visited = False
        self._meridian_visited = False
        self._false_son_boss_complete = False
        self._solus_wing_defeated = False
        self._solus_heart_defeated = False
        self._inventory.reset()
        self.stats.reset_data()

    def _generate_drop_actions(self):
        """Initialise the loot dropped from various interactables."""
        # By not storing something by its ISC name, we ensure stage looting will
        # not loot that interactable and we can manually control when to
        # generate drops for it.
        actions = {}
        interactables = [
            # Chests - no Adaptive Chest or Temporary Item Distributor
            'iscChest1', 'iscChest2', 'iscEquipmentBarrel', 'iscLunarChest',
            'iscCategoryChestDamage', 'iscCategoryChestHealing', 'iscCategoryChestUtility',
            'iscCategoryChest2Damage', 'iscCategoryChest2Healing', 'iscCategoryChest2Utility',
            'iscGoldChest', 'iscChest1Stealthed',
            # Multishops
            'iscTripleShop', 'iscTripleShopLarge', 'iscTripleShopEquipment', 'iscFreeChest',
            # Shrines of Chance
            'iscShrineChance', 'iscShrineChanceSandy', 'iscShrineChanceSnowy',
            # Corruption chests
            'iscVoidChest', 'iscVoidChestSacrificeOn',
            # Locked chests
            'iscLockbox',
        ]
        for spawn_card in interactables:
            actions[spawn_card] = (
                eval(isc[spawn_card].controller).
                generate_purchase_action(isc[spawn_card], self._tier_droplists, self._inventory)
            )
        # Option chests
        actions['iscVoidTriple'] = OptionChestBehavior.generate_purchase_action(
            droptables['dtVoidTriple'], self._tier_droplists, 3
        )
        # Halcyonite Shrine
        for spawn_card in ('iscShrineHalcyonite', 'iscShrineHalcyoniteTier1'):
            actions[spawn_card] = HalcyoniteShrineInteractable.generate_purchase_action(
                droptables['dtShrineHalcyoniteTier3'], droptables['dtShrineHalcyoniteTier2'],
                self._tier_droplists, 5
            )
        # Green printer
        actions['green_printer'] = ShopTerminalBehavior.generate_purchase_action(
            isc['iscDuplicatorLarge'], self._tier_droplists, self._inventory
        )
        # Void Fields cell drops
        for tier in range(1, 4):
            actions[f'cell{tier}_drop'] = OptionChestBehavior.generate_purchase_action(
                droptables[f'dtTier{tier}Item'], self._tier_droplists, 3
            )
        # Meridian geode mission drops
        actions['meridian_geode'] = HalcyoniteShrineInteractable.generate_purchase_action(
            droptables['dtShrineHalcyoniteTier1'], droptables['dtShrineHalcyoniteTier1'],
            self._tier_droplists, 3
        )
        # Solutional Haunt vault
        actions['vault_han-d'] = lambda: [random.choice(self._tier_droplists[0]) for _ in range(3)]
        # Boss drops
        actions['teleporter_drop'] = lambda: random.choice(self._tier_droplists[1])
        actions['AWU_drop'] = lambda: random.choice(self._tier_droplists[2])
        actions['false_son_drop'] = OptionChestBehavior.generate_purchase_action(
            droptables['dtChest2'], self._tier_droplists, 3
        )
        actions['false_son_aurelionite_drop'] = OptionChestBehavior.generate_purchase_action(
            droptables['AurelioniteHeartPickupDropTable'], self._tier_droplists, 3
        )
        actions['solus_heart_drop'] = droptables['dtSolusHeart'].generate_loot_drop_action(
            self._tier_droplists
        )
        return actions

    def _pick_next_stage_scene(self, destination_group):
        """
        Select the next scene from a collection of valid destinations.

        Parameters
        ----------
        destination_group : list
            A list of (scene_name, weight) for potential destinations.

        Returns
        -------
        str

        Notes
        -----
        An implementation of `RoR2.Run.PickNextStageScene`.
        """
        if not destination_group:
            raise ValueError('No valid destinations found.')
        scene, weight = zip(*destination_group)
        return random.choices(scene, weight)[0]

    def _pick_next_stage_scene_from_current_scene_destinations(self):
        """
        Select the next scene based on the current scene.

        Returns
        -------
        str

        Notes
        -----
        An implementation of `RoR2.Run.PickNextStageSceneFromCurrentSceneDestinations`.
        """
        scene_data = self._scene_data
        collection = scene_data.destinations
        if scene_data.destinations:
            if self._stages_cleared >= 4 and scene_data.use_looping_destinations:
                if scene_data.destinations_loop:
                    collection = scene_data.destinations_loop
        destinations = [d for d in collection if self._can_pick_stage(d[0])]
        return self._pick_next_stage_scene(destinations)

    def _can_pick_stage(self, scene_name):
        """
        Checks whether a scene is available for selection.

        Parameters
        ----------
        scene_name : str
            The internal name of the scene.

        Returns
        -------
        bool

        Notes
        -----
        An implementation of `RoR2.Run.CanPickStage`.
        """
        required_dlc = scenes[scene_name].required_dlc
        return not required_dlc or required_dlc in self._expansions

    def _generate_interactables(self):
        """
        Generate interactables for a stage.

        Returns
        -------
        interactables : list
            A list of all the interactable spawn card names generated.

        Notes
        -----
        - Fixed stage spawns are also handled here.
        - Bulwark's Ambry has the Artifact of Command enabled, which affects
          interactable generation.
        """
        scene_name = self._scene_name
        if scene_name == SceneName.AD:
            self._scene_director.is_bonus_credits_available = random.random() > .5
        if scene_name == SceneName.BA:
            is_command_enabled = self._scene_director.is_command_enabled
            self._scene_director.is_command_enabled = True
        interactables = self._scene_director.populate_scene(self._stages_cleared, False)
        if scene_name == SceneName.BA:
            self._scene_director.is_command_enabled = is_command_enabled
        for _ in range(interactables.count('iscVoidCamp')):
            interactables.extend(self._camp_director.populate_camp(False))

        # Specific scene interactables
        if scene_name in (SceneName.AD, SceneName.SG, SceneName.RP):
            # We deal with Conduit Canyon separately
            interactables.append('iscGoldChest')
        elif scene_name == SceneName.GC:
            interactables.extend(['iscChest1'] * 4)
        elif scene_name == SceneName.VF2:
            interactables.append('iscChest2' if random.random() < .5 else 'iscScrapper')
        elif scene_name == SceneName.PM:
            interactables.extend(['iscChest2'] * 4)
        elif scene_name == SceneName.PP:
            drone = random.choice(('iscBrokenDrone1', 'iscBrokenDrone2',
                                   'iscBrokenMissileDrone', 'iscBrokenHaulerDrone',
                                   'iscBrokenJailerDrone', 'iscBrokenRechargeDrone'))
            interactables.append(drone)
        elif scene_name == SceneName.CC:
            interactables.append('iscShrineRestack')
            interactables.append('iscTemporaryItemsShop')
            interactables.append('iscGoldChest')
            interactables.append('iscTripleShopEquipment')
        elif scene_name == SceneName.CE:
            interactables.append('iscDroneScrapper')
            interactables.append('iscDroneCombinerStation')
            interactables.append('iscDuplicator' if random.random() < .5 else 'iscDuplicatorLarge')
            drones = (
                ('iscBrokenCleanupDrone', 'iscBrokenBombardmentDrone'),
                ('iscBrokenBombardmentDrone', 'iscBrokenHaulerDrone'),
                ('iscBrokenHaulerDrone', 'iscBrokenJunkDrone'),
                ('iscBrokenJailerDrone', 'iscBrokenJunkDrone'),
                ('iscBrokenJailerDrone', 'iscBrokenCopycatDrone'),
                ('iscBrokenCleanupDrone', 'iscBrokenCopycatDrone'),
                ('iscBrokenCleanupDrone', 'iscBrokenHaulerDrone'),
                ('iscBrokenBombardmentDrone', 'iscBrokenJunkDrone'),
                ('iscBrokenHaulerDrone', 'iscBrokenJailerDrone'),
                ('iscBrokenJunkDrone', 'iscBrokenCopycatDrone'),
                ('iscBrokenCleanupDrone', 'iscBrokenJailerDrone'),
                ('iscBrokenBombardmentDrone', 'iscBrokenCopycatDrone'),
                ('iscBrokenCleanupDrone', 'iscBrokenJunkDrone'),
                ('iscDuplicatorWild',),
                ('iscDuplicatorMilitary',),
                ('iscDuplicatorMilitary',),
                ('iscTripleDroneShop',),
                ('iscTripleDroneShop',),
                ('iscTripleDroneShop',),
                ('iscTripleDroneShop',),
            )
            interactables.extend(random.choice(drones))
        elif scene_name == SceneName.SH:
            interactables.append('iscBrokenMegaDrone')
            interactables.append('iscChest2')
            interactables.append('iscChest1Stealthed')
            # Skipping:
            # - BrokenHAND because it doesn't belong in the isc dictionary.
            #   This is handled manually when looting a stage.
            # - DrifterBag because it contains temp items.

        scene_data = self._scene_data
        if scene_data.scene_type in (1, 5) or scene_data.allow_item_spawn:
            if LOCKBOX_ALLOWED:
                # For multiplayer we assume the Rusted Keys are as evenly spread out
                # as possible to maximise spawning Lockboxes.
                lockboxes = min(self._inventory.count(Items.TreasureCache), self._num_players)
                if lockboxes:
                    interactables += ['iscLockbox'] * lockboxes
                    self._inventory.remove_item(Items.TreasureCache, lockboxes)
            if FREE_CHEST_ALLOWED:
                free_chests = self._inventory.count(Items.FreeChest)
                if free_chests:
                    interactables += ['iscFreeChest'] * min(free_chests, self._num_players)
        random.shuffle(interactables)
        return interactables
        
    def _loot_multishop(self, isc, drops):
        """
        Collect any or all loot from a multishop.

        Parameters
        ----------
        isc : str
            The name of the interactable spawn card of the multishop.
        drops : list
            A list of tuples which the items available for purchase and whether
            they are visible.

        Returns
        -------
        list
            The selected items.

        Notes
        -----
        - If the player holds the Executive Card, all items will be collected.
        - For a while/green multishop a random item is selected.
        - For an equipment multishop, it will prioritise an Executive Card, or
          a Recycler in its absence to reroll future equipment until an
          Executive Card is found.
        - For a Shipping Request Form, the highest tier item is selected.
        """
        collected = []
        if isc in {'iscTripleShop', 'iscTripleShopLarge'}:
            if self._inventory.has_card:
                for item, _ in drops:
                    self._inventory.give_item(item)
                    collected.append(item)
            else:
                item = random.choice(drops)[0]
                self._inventory.give_item(item)
                collected.append(item)
        elif isc == 'iscTripleShopEquipment':
            if self._inventory.has_card:
                for item, _ in drops:
                    item = self._collect_equipment(item)
                    collected.append(item)
            else:
                visible = []
                hidden = []
                for item, is_visible in drops:
                    if is_visible:
                        visible.append(item)
                    else:
                        hidden.append(item)
                if Equipment.MultiShopCard in visible:
                    item = self._collect_equipment(Equipment.MultiShopCard)
                elif Equipment.Recycle in visible and not self._inventory.has_recycler:
                    item = self._collect_equipment(Equipment.Recycle)
                elif Equipment.BossHunter in visible:
                    item = self._collect_equipment(Equipment.BossHunter)
                elif hidden:
                    item = self._collect_equipment(hidden[0])
                else:
                    item = self._collect_equipment(visible[0])
                collected.append(item)
        elif isc == 'iscFreeChest':
            if self._inventory.has_card:
                for item, _ in drops:
                    self._inventory.give_item(item)
                    collected.append(item)
            else:
                item = max(drops, key=lambda x: x[0].tier._tier)[0]
                self._inventory.give_item(item)
                collected.append(item)
        return collected

    def _loot_teleporter(self, dccs, shrines_activated, use_access_code):
        """
        Collect all the loot dropped from the teleporter event.

        Parameters
        ----------
        dccs : DirectorCardCategorySelection
            The monster DCCS selected for the scene.
        shrines_activated : int
            The number of the Shrines of the Mountain that have been activated.
            Each one provides 100% more loot.
        use_access_code : bool
            Whether the Solus Amalgamator will spawn along with the normal boss.
            Affects which boss items can be dropped.

        Returns
        -------
        loot : dict
            A dictionary of the various item dropped and their amounts.

        Notes
        -----
        The algorithm does not take into account the time the teleporter is
        activated. This has a direct consequence of not knowing whether the
        selected monster will be too cheap/expensive to spawn, thus altering
        the real probability of a Horde of Many event occurring. Therefore, this
        does not exactly correspond to the real chance of boss loot dropping.
        """
        total_drops = self._num_players * (shrines_activated + 1)
        boss = Run.spawn_teleporter_boss(dccs, self._stages_cleared, self._expansions)
        boss_drops = []
        if boss.body.item_drop:
            boss_drops.append(boss.body.item_drop)
        if use_access_code:
            boss_drops.append(bodies['SolusAmalgamatorBody'].item_drop)
        loot = {}
        green_item = self._actions['teleporter_drop']()
        for _ in range(total_drops):
            drop = green_item
            if boss_drops and random.random() <= BOSS_DROP_CHANCE:
                drop = random.choice(boss_drops)
            if drop not in loot:
                loot[drop] = 0
            loot[drop] += 1
        return loot

    def _collect_equipment(self, equipment):
        """
        Add an equipment to the list of encountered equipment.

        If `CARD_BIAS_ENABLED` is True, the method will try to get hold of a
        Recycler and reroll any future equipment until an Executive Card is
        found.

        Parameters
        ----------
        equipment : EquipmentDef
            The equipment to be picked up.

        Returns
        -------
        equipment : EquipmentDef
            The equipment that is eventually collected, in case it was rerolled
            in the process.

        Notes
        -----
        The cooldown duration is not taken into account and all equipment after
        finding a Recycler will be rerolled. However, this algorithm doesn't
        retroactively reroll equipments that were previously purchased on the
        stage the Recycler was first found.
        """
        inventory = self._inventory
        if CARD_BIAS_ENABLED:
            if not inventory.has_card:
                if equipment == Equipment.MultiShopCard:
                    inventory.has_recycler = False
                    inventory.can_recycle = False
                elif not inventory.has_recycler and equipment == Equipment.Recycle:
                    inventory.has_recycler = True
                if inventory.has_recycler:
                    if inventory.can_recycle:
                        # I imagine it is an unlikely behaviour that someone
                        # would recycle a Trophy Hunter's Tricon for the small
                        # chance of getting an Executive Card, so it is skipped.
                        if equipment != Equipment.BossHunter:
                            equipment = self._reroll_item(equipment)
                            if equipment == Equipment.MultiShopCard:
                                inventory.has_recycler = False
                                inventory.can_recycle = False
                    else:
                        inventory.can_recycle = True
        if equipment == Equipment.MultiShopCard and not inventory.has_card:
            inventory.has_card = True
        inventory.equipment.append(equipment)
        return equipment

    def _reroll_item(self, item):
        """Reroll an item or equipment with the Recycler."""
        for tier in self._tier_droplists:
            if item in tier:
                choices = tier.copy()
                choices.remove(item)
                return random.choice(choices)
        else:
            raise ValueError('Item not found in any tier.')

    def _loot_interactables(self, interactables):
        """
        Interact and loot any interactables spawned on a stage.

        Parameters
        ----------
        interactables : list
            A list of string names of the interactable spawn cards generated.

        Returns
        -------
        loot : dict
            A dict of lists with all the items and equipment that were picked up.
        boss_shrines : int
            The number of Shrines of the Mountain activated.
        gold_shrines : int
            The number of Shrines of Gold encountered.
        free_chest_items : list
            All items collected from Shipping Request Forms.
        card_multibuys : list
            The names of the interactable spawn card of any multishop that was
            fully looted using an Executive Card.
        delusion_loot : list
            The extra stack of items that can be collected if the Artifact of
            Delusion is enabled.
        """
        loot = {ItemDef: [], EquipmentDef: []}
        boss_shrines = 0
        gold_shrines = 0
        free_chest_items = []
        card_multibuys = []
        delusion_loot = []
        for isc_name in interactables:
            if isc_name in self._actions:
                if 'TripleShop' in isc_name or 'FreeChest' in isc_name:
                    if self._inventory.has_card:
                        card_multibuys.append(isc_name)
                    drops = self._actions[isc_name]()
                    collected_loot = self._loot_multishop(isc_name, drops)
                    for item in collected_loot:
                        loot[type(item)].append(item)
                    if isc_name == 'iscFreeChest':
                        free_chest_items.extend(collected_loot)
                elif isc == 'iscVoidTriple':
                    drops = self._actions[isc_name]()
                    item = max(drops, key=lambda x: x.tier._tier)
                    self._inventory.give_item(item)
                    loot[type(item)].append(item)
                elif 'ShrineHalcyonite' in isc_name:
                    for _ in range(self._num_players):
                        drops = self._actions[isc_name]()
                        sorted_items = sorted(drops, key=lambda x: x.tier._tier, reverse=True)
                        for item in sorted_items[:3]:
                            self._inventory.give_item(item)
                else:
                    for item in self._actions[isc_name]():
                        if isinstance(item, ItemDef):
                            self._inventory.give_item(item)
                        elif isinstance(item, EquipmentDef):
                            item = self._collect_equipment(item)
                        loot[type(item)].append(item)
                        if isc[isc_name].can_reset and self._is_delusion_enabled:
                            delusion_loot.append(item)
            elif 'ShrineBoss' in isc_name:
                boss_shrines += 1
            elif 'Goldshores' in isc_name:
                gold_shrines += 1
        return loot, boss_shrines, gold_shrines, free_chest_items, card_multibuys, delusion_loot
    
    def _loot_stage(self, void_fields, stage_preferences):
        """Fully loot a normal stage."""
        scene_name = self._scene_name
        if scene_name == SceneName.VF:
            self._void_fields_visited = True
        elif scene_name == SceneName.PM:
            self._meridian_visited = True
        stage_order = self._scene_data.stage_order
        self._scene_director._start(self._stages_cleared)
        stage_dccs = self._scene_director.monsters
        portals = set()

        scene_director = self._scene_data.scene_director
        teleporter_exists = (scene_director and scene_director.teleporter) or scene_name == SceneName.CC
        if teleporter_exists:
            self._next_scene_name = self._pick_next_stage_scene_from_current_scene_destinations()
            if random.random() <= BLUE_PORTAL_CHANCE / (self._blue_portals_opened + 1):
                portals.add(Portal.B)
            if self._stages_cleared >= 5 and self._stages_cleared % 5 == 2:
                portals.add(Portal.C)
            if self._is_sotv_enabled and random.random() <= PURPLE_PORTAL_CHANCE and self._stages_cleared >= 6:
                portals.add(Portal.V)

        interactables = self._generate_interactables()
        loot, boss_shrines, gold_shrines, free_chest_items, card_multibuys, delusion_loot = self._loot_interactables(interactables)

        if teleporter_exists and not Portal.B in portals:
            # In some cases the only available Newt Statue is either locked
            # behind an inaccessible area, or requires a lot of mobility to get
            # to. While it may not be consistently reachable in the early game
            # with every Survivor, or without clipping through walls, we make
            # the hard assumption that if it exists, it can be activated.
            # If we intend to visit the Void Fields next, we force open the
            # portal whether it exists or not to ensure the condition is met.
            if self._stages_cleared + 1 == void_fields:
                portals.add(Portal.B)
            elif stage_order in stage_preferences:
                newt = self._scene_data.newt
                if newt:
                    newt = random.randint(*newt)
                    if self._scene_name in (SceneName.AA, SceneName.RD, SceneName.SA):
                        newt += 1
                    if newt:
                        portals.add(Portal.B)

        if teleporter_exists:
            use_access_code = (self._is_ac_enabled and not self._solus_wing_defeated and
                              (stage_order == 2 or scene_name == SceneName.RP)
                              and scene_name not in (SceneName.TC, SceneName.GD))
            for item, count in self._loot_teleporter(stage_dccs, boss_shrines, use_access_code).items():
                self._inventory.give_item(item, count)
                loot[ItemDef].extend([item] * count)
            if Portal.B in portals:
                self._blue_portals_opened += 1
            if gold_shrines:
                portals.add(Portal.G)
            if use_access_code or (self._is_ac_enabled and scene_name == SceneName.SC):
                portals.add(Portal.E)

        if (teleporter_exists or scene_name == SceneName.BA) and self._is_delusion_enabled:
            for item in delusion_loot:
                self._inventory.give_item(item)

        if scene_name == SceneName.VF:
            for cell in range(9):
                tier = cell // 4 + 1
                potential = self._actions[f'cell{tier}_drop']()
                for _ in range(self._num_players):
                    item = random.choice(potential)
                    self._inventory.give_item(item)
                    loot[ItemDef].append(item)
            if self._is_sotv_enabled:
                portals.add(Portal.V)
        elif scene_name == SceneName.SM:
            portals.add(Portal.A)
        elif scene_name == SceneName.PM:
            if self._is_ac_enabled:
                portals.add(Portal.E)

        colossus_path_stages = (SceneName.RA, SceneName.TC, SceneName.GD)
        if 'iscShrineHalcyonite' in interactables or 'iscShrineHalcyoniteTier1' in interactables:
            if (stage_order in (0, 1, 2)
                and scene_name not in colossus_path_stages
                and not self._meridian_visited):
                portals.add(Portal.Gr)
            elif stage_order in (3, 4):
                portals.add(Portal.G)
            elif self._meridian_visited:
                portals.add(Portal.G)

        if not self._false_son_boss_complete:
            if scene_name in colossus_path_stages:
                portals.add(Portal.Gr)
            elif scene_name == SceneName.GC and self._is_sots_enabled:
                next_stage_order = scenes[self._next_scene_name].stage_order
                if next_stage_order in (1, 2, 3):
                    portals.add(Portal.Gr)

        regen_scraps = self._inventory.count(Items.RegeneratingScrap)
        if TRADE_REGEN_SCRAP and regen_scraps and 'iscDuplicatorLarge' in interactables:
            item = self._actions['green_printer']()
            self._inventory.give_item(item, regen_scraps)
            loot[ItemDef].extend([item] * regen_scraps)
        if scene_name == SceneName.AA:
            self._inventory.give_item(Items.IceRing)
            self._inventory.give_item(Items.FireRing)
            loot[ItemDef].extend([Items.IceRing, Items.FireRing])
        elif scene_name == SceneName.SC:
            item = self._actions['AWU_drop']()
            self._inventory.give_item(item, self._num_players)
            loot[ItemDef].extend([item] * self._num_players)
        elif scene_name == SceneName.GC:
            self._inventory.give_item(Items.TitanGoldDuringTP, self._num_players)
            loot[ItemDef].extend([Items.TitanGoldDuringTP] * self._num_players)
        elif scene_name == SceneName.PM:
            for _ in range(self._num_players):
                drops = self._actions['meridian_geode']()
                item = max(drops, key=lambda x: x.tier._tier)
                self._inventory.give_item(item)
                loot[ItemDef].append(item)
            self._false_son_boss_complete = True
            boss_drop = ('false_son_drop' if not self._inventory.count(Items.TitanGoldDuringTP)
                        else 'false_son_aurelionite_drop')
            for _ in range(self._num_players):
                drops = self._actions[boss_drop]()
                item = max(drops, key=lambda x: x.tier._tier)
                self._inventory.give_item(item)
                loot[ItemDef].append(item)
        elif scene_name == SceneName.SH:
            items = self._actions['vault_han-d']()
            for item in items:
                self._inventory.give_item(item)
            self._solus_wing_defeated = True
        elif scene_name == SceneName.NS:
            for _ in range(self._num_players):
                item = self._actions['solus_heart_drop']()
                self._inventory.give_item(item)
                loot[ItemDef].append(item)
            self._solus_heart_defeated = True

        if scene_name == SceneName.AD:
            scene_name += '-open' if self._scene_director.is_bonus_credits_available else '-closed'

        self.stats.update_data(
            scene_name,
            portals,
            stage_dccs,
            interactables,
            loot,
            free_chest_items,
            card_multibuys,
            delusion_loot,
        )
        return

    def _choose_next_destination(self, void_fields, stage_preferences):
        """
        Choose whether to use a portal or advance to the next stage naturally.

        The order of preference is Null > Artifact > Green > Encrypted >
        Gold > Lunar Seer > RNG.
        
        Returns
        -------
        None
        """
        portals = self.stats.portals[-1]
        blue = Portal.B in portals
        take_gold_portal = USE_GOLD_PORTAL and Portal.G in portals
        self._explicit_next_scene_name = None
        scene_name = self._scene_name
        next_stage_order = scenes[self._next_scene_name].stage_order
        # First we do stages that chain together, then we check for any portals
        if scene_name == SceneName.CC:
            self._explicit_next_scene_name = SceneName.SH
        elif scene_name == SceneName.SH:
            self._explicit_next_scene_name = SceneName.CE
        elif scene_name == SceneName.CE:
            if not self._solus_heart_defeated:
                self._explicit_next_scene_name = SceneName.NS
        elif blue and self._stages_cleared + 1 == void_fields and not self._void_fields_visited:
            self._explicit_next_scene_name = SceneName.VF
        elif USE_ARTIFACT_PORTAL and Portal.A in portals:
            self._explicit_next_scene_name = SceneName.BA
        elif USE_GREEN_PORTAL and Portal.Gr in portals and not take_gold_portal:
            # If we're on the Colossus path, we can get both a green and a gold
            # portal. Normally, the green portal has higher priority, but it is
            # possible to visit the Gilded Coast before getting back to the
            # path.
            next_stage_order = scenes[self._next_scene_name].stage_order
            if next_stage_order == 1:
                self._explicit_next_scene_name = SceneName.RA
            elif next_stage_order == 2:
                self._explicit_next_scene_name = SceneName.TC
            elif next_stage_order == 3:
                self._explicit_next_scene_name = SceneName.PM
            else:
                raise ValueError('Green portal spawned on some unexpected stage.')
        elif USE_ENCRYPTED_PORTAL and Portal.E in portals:
            # The boss check is for the portal from Prime Meridian.
            if next_stage_order == 3 and not self._solus_wing_defeated:
                self._explicit_next_scene_name = SceneName.CC
            else:
                self._explicit_next_scene_name = SceneName.CE if self._solus_wing_defeated else SceneName.SH
        elif take_gold_portal:
            self._explicit_next_scene_name = SceneName.GC
        elif blue and self._scene_data.stage_order in stage_preferences:
            preferences = stage_preferences[self._scene_data.stage_order]
            if preferences:
                stations = self._setup_seer_stations()
                for preference in preferences:
                    if preference in stations:
                        self._explicit_next_scene_name = preference
                        break

    def _setup_seer_stations(self):
        """
        Generate override scenes with the Lunar Seer.

        Returns
        -------
        stations : list
            The internal name of the selected override scenes.

        Notes
        -----
        An implementation of `RoR2.BazaarController.SetUpSeerStations`.
        """
        if not self._next_scene_name:
            return []
        stage_order = scenes[self._next_scene_name].stage_order
        destinations = [scene for scene, data in scenes.items()
                        if not data.filter_bazaar
                        and data.scene_type != 6
                        and data.stage_order == stage_order
                        and (not data.required_dlc or data.required_dlc in self._expansions)
                        and (self._stages_cleared >= 4 or not data.locked_before_looping)]
        replacements = [SceneName.GC]
        weights = [0.05]
        if self._is_sotv_enabled and self._stages_cleared >= 4:
            replacements.append(SceneName.VL)
            weights.append(0.05)
        if self._is_sots_enabled and not self._false_son_boss_complete:
            replacements.append(SceneName.GC)
            weights.append(0.1)
        replacement_chance = sum(weights)
        
        stations = []
        for _ in range(2):
            if not destinations:
                break
            random.shuffle(destinations)
            target_scene = destinations.pop()
            if random.random() < replacement_chance:
                target_scene = random.choices(replacements, weights)[0]
            stations.append(target_scene)
        return stations

    def _advance_stage(self):
        """Advance to the next stage."""
        if (self._scene_data.scene_type in (1, 5)) and not self._scene_data.prevent_stage_advance:
            self._stages_cleared += 1
        if self._explicit_next_scene_name:
            self._scene_name = self._explicit_next_scene_name
        else:
            self._scene_name = self._next_scene_name
            self._next_scene_name = None
        if self._scene_name in (SceneName.MW, SceneName.CO, SceneName.VL, SceneName.PL):
            raise ValueError(f'Cannot go to {self._scene_name} as this will end the run.')
        self._scene_data = scenes[self._scene_name]
        self._scene_director.scene_name = self._scene_name

    @staticmethod
    def calculate_difficulty_coefficient(time, stages_cleared, players=1, difficulty=3):
        """
        Calculate the difficulty coefficient.

        Parameters
        ----------
        time : int
            Time in minutes that have passed in the game, always round down.
        stages_cleared : int
            The number of stages cleared.
        players : int, optional
            The number of players in a run.
        difficulty : {1, 2, 3}, optional
            The difficulty of the game. 1 for Drizzle, 2 for Rainstorm, and 3
            for Monsoon.

        Returns
        -------
        float

        Notes
        -----
        An implementation of `RoR2.Run.RecalculateDifficultyCoefficientInteral`.
        """
        player_factor = 1 + .3 * (players - 1)
        time_factor = .0506 * difficulty * players**.2
        stage_factor = 1.15**stages_cleared
        return (player_factor + time * time_factor) * stage_factor

    @staticmethod
    def build_tier_droplists(expansions=ALL_EXPANSIONS):
        """
        Generate the tier available droplists for the current run.

        Parameters
        ----------
        expansions : iterable, default {'DLC1'}
            A set of all enabled expansions, which determine which items will
            be available.

        Returns
        -------
        drops : list
            A list of lists with all available droppable items for each tier.

        Notes
        -----
        An implementation of `Ror2.Run.BuildDropTable()`.
        """
        def filter_available(items, expansions):
            return [item for item in items
                    if not item.required_dlc or item.required_dlc in expansions]
        def meets_requirement(item, tier):
            return item.tier == tier and 9 not in item.tags

        items = filter_available(Items._items, expansions)
        equipment = filter_available(Equipment._items, expansions)
        drops = [None] * 12
        drops[0] = [item for item in items if meets_requirement(item, ItemTiers.Tier1)]
        drops[1] = [item for item in items if meets_requirement(item, ItemTiers.Tier2)]
        drops[2] = [item for item in items if meets_requirement(item, ItemTiers.Tier3)]
        drops[3] = [item for item in items if meets_requirement(item, ItemTiers.BossTier)]
        drops[4] = [e for e in equipment if e.is_lunar and e.can_drop]
        drops[5] = [item for item in items if meets_requirement(item, ItemTiers.LunarTier)]
        drops[6] = drops[4] + drops[5]
        drops[7] = [e for e in equipment if not e.is_lunar and e.can_drop]
        drops[8] = [item for item in items if meets_requirement(item, ItemTiers.VoidTier1)]
        drops[9] = [item for item in items if meets_requirement(item, ItemTiers.VoidTier2)]
        drops[10] = [item for item in items if meets_requirement(item, ItemTiers.VoidTier3)]
        drops[11] = [item for item in items if meets_requirement(item, ItemTiers.VoidBoss)]
        return drops

    @staticmethod
    def spawn_teleporter_boss(dccs, stages_cleared, expansions=ALL_EXPANSIONS):
        """
        Select a monster for the teleporter.

        Parameters
        ----------
        dccs : DirectorCardCategorySelection
            The selected DCCS for the stage.
        stages_cleared : int
            The number of stages cleared, which affects which monsters are
            available for selection.
        expansions : set, optional

        Returns
        -------
        CharacterSpawnCard
            The spawn card of the selected monster.

        Notes
        -----
        An implementation of `RoR2.CombatDirector.SetNextSpawnAsBoss`.
        This is not complete though since the selected card may turn out to be
        too cheap/expensive, resulting in another draw using a different
        algorithm. The complete algorithm requires the time the teleporter is
        activated so it can compute the boss director monster credits.
        """
        monsters = dccs.generate_card_weighted_selection(stages_cleared, expansions)
        filtered = []
        weights = []
        for card, weight in monsters:
            spawn_card = card.spawn_card
            if spawn_card.body.is_champion and not spawn_card.forbidden_as_boss:
                filtered.append(spawn_card)
                weights.append(weight)
        if filtered:
            return random.choices(filtered, weights)[0]
        filtered, weights = zip(*monsters)
        return random.choices(filtered, weights)[0].spawn_card

    def loot_stages(self, num_stages=5, void_fields=-1, stage_preferences=dict()):
        """
        Simulate a run by full looting a number of stages.

        Parameters
        ----------
        num_stages : int, optional
            The number of normal stages to loot.
        void_fields : int, optional
            After what stage to visit the Void Fields. It is assumed it will be
            completed and looted fully. If on the same stage a Gold Portal
            spawns, visiting the Void Fields will still take priority. The
            default setting is to not visit it at all during a run.
        stage_preferences : dict, optional
            A dictionary with keys the "stage_order" of the destination scene
            and values a list with the internal name of the preferred
            destinations, ordered from most to least preferred. If the
            destination "stage_order" is not found, or none of the preferred
            scenes have spawned for the Lunar Seer, there will be no overrides
            and the next scene will be chosen at random as normal.

        Returns
        -------
        None
        """
        self._restart()
        if num_stages <= 0:
            return
        if void_fields == 0:
            void_fields = -1
        while self._stages_cleared < num_stages:
            self._loot_stage(void_fields, stage_preferences)
            self._choose_next_destination(void_fields, stage_preferences)
            self._advance_stage()
