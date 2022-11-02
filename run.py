from collections import Counter, defaultdict
import random

from constants import SceneName, STAGES, ALL_EXPANSIONS
from data_loader import ItemTiers, Items, Equipment, isc, droptables, scenes
from data.objects import EquipmentDef, ItemDef
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

    def update_data(self, scene_name, spawned_portals, dccs,
                    interactables, loot, free_chest_items, card_multibuys):
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

        Returns
        -------
        None
        """
        self.scenes.append(scene_name)
        self.portals.append(spawned_portals)
        self.dccs.append(dccs.name)
        self.interactables.append(interactables)
        self.loot.append(loot)
        item_count = [self._inventory.count(item) for item in
            (Items.TreasureCache, Items.TreasureCacheVoid, Items.FreeChest, Items.RegeneratingScrap)
        ]
        item_count.append(item_count[-1] * ('iscDuplicatorLarge' in interactables))
        self.item_count.append(item_count)
        self.free_chest_items.append(free_chest_items)
        self.card_multibuys.append(card_multibuys)

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
        """
        out = {
            'scenes': self.scenes,
            'portals': list(map(sum, zip(*self.portals))),
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
        total = {'family_event': sum('Family' in dccs for dccs in self.dccs)}
        for isc_name, name in (
            ('iscShrineBoss', 'mountain_shrine'),
            ('iscChest1Stealthed', 'cloaked_chect'),
            ('iscLockbox', 'rusted_lockbox'),
            ('iscLockboxVoid', 'encrusted_lockbox'),
            ('iscCasinoChest', 'adaptive_chest'),
            ('iscVoidCamp', 'void_seed'),
            ('iscVoidChest', 'void_cradle'),
        ):
            total[name] = isc_counter.get(isc_name, 0)
        total['mountain_shrine'] += isc_counter.get('iscShrineBossSandy', 0)
        total['mountain_shrine'] += isc_counter.get('iscShrineBossSnowy', 0)
        total['void_cradle'] += isc_counter.get('iscVoidChestSacrificeOn', 0)
        total['drones'] = sum(count for isc, count in isc_counter.items() if 'Drone' in isc)
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
        self.items[item] += count
        
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
        if isinstance(item, ItemDef) and item in self.items:
            self.items[item] -= count
            if self.items[item] <= 0:
                del self.items[item]

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


class Run:
    """Simulates a run by full looting a number of stages."""
    def __init__(self, num_players=1, expansions=ALL_EXPANSIONS):
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

        Returns
        -------
        None
        """
        self._num_players = num_players
        self._expansions = set(expansions)
        self._is_command_enabled = False
        self._is_sacrifice_enabled = False
        # Bogus scene just to initialise the director; it will be rerolled
        self._scene_director = SceneDirector(
            'blackbeach',
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
        self._stage_order = 0
        self._scene_name = self._select_scene(self._stage_order)
        self._scene_director.change_scene(self._scene_name)
        self._next_scene_name = None
        self._blue_portals_opened = 0
        self._void_fields_visited = False
        self._inventory.reset()
        self.stats.reset_data()

    def _generate_drop_actions(self):
        """Initialise the loot dropped from various interactables."""
        # By not storing something by its ISC name, we ensure stage looting will
        # not loot that interactable and we can manually control when to
        # generate drops for it.
        actions = {}
        interactables = [
            # Chests - no Adaptive Chest
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
        for cell_type in ('Tier1', 'Tier2', 'Tier3'):
            actions[f'cell_{cell_type.lower()}'] = OptionChestBehavior.generate_purchase_action(
                droptables[f'dt{cell_type}Item'], self._tier_droplists, 3
            )
        # Green printer
        actions['green_printer'] = ShopTerminalBehavior.generate_purchase_action(
            isc['iscDuplicatorLarge'], self._tier_droplists, self._inventory
        )
        # Boss drops
        actions['teleporter_drop'] = lambda: random.choice(self._tier_droplists[1])
        actions['AWU_drop'] = lambda: random.choice(self._tier_droplists[2])
        return actions

    def _select_scene(self, order):
        """
        Select the next scene.

        Parameters
        ----------
        order : int
            The current stage order we're moving to. For example, Distant Roost
            is 0 and Sky Meadow is 4. Then it loops back to 0.

        Returns
        str
            The internal name of the selected scene.
        """
        available_scenes = [
            scene for scene in STAGES[order % len(STAGES)]
            if not scenes[scene].required_dlc or scenes[scene].required_dlc in self._expansions
        ]
        return random.choice(available_scenes)

    def _generate_interactables(self):
        """
        Generate interactables for a stage.

        Returns
        -------
        interactables : list
            A list of all the interactable spawn card names generated.

        Notes
        -----
        Fixed stage spawns are also handled here.
        """
        interactables = self._scene_director.populate_scene(self._stages_cleared, False)
        for _ in range(interactables.count('iscVoidCamp')):
            interactables.extend(self._camp_director.populate_camp(False))
        if self._scene_name in (SceneName.AD, SceneName.SG):
            interactables.append('iscGoldChest')
        elif self._scene_name == SceneName.GS:
            interactables.extend(['iscChest1'] * 4)
        if scenes[self._scene_name].scene_type == 1:
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

    def _loot_teleporter(self, dccs, shrines_activated):
        """
        Collect all the loot dropped from the teleporter event.

        Parameters
        ----------
        dccs : DirectorCardCategorySelection
            The monster DCCS selected for the scene.
        shrines_activated : int
            The number of the Shrines of the Mountain that have been activated.
            Each one provides 100% more loot.

        Returns
        -------
        loot : dict
            A dictionary of the various item dropped and their amounts.

        Notes
        -----
        The algorithm doesn't take into account the time the teleporter is
        activated. This has a direct consequence of not knowing whether the
        selected monster will be too cheap/expensive to spawn, thus altering
        the real probability of a Horde of Many event occurring. Therefore, this
        doesn't exactly correspond to the real chance of boss loot dropping.
        """
        total_drops = self._num_players * (shrines_activated + 1)
        boss = Run.spawn_teleporter_boss(dccs, self._stages_cleared)
        if boss.body.item_drop:
            green_item_count = sum(random.random() > BOSS_DROP_CHANCE for _ in range(total_drops))
        else:
            green_item_count = total_drops
        boss_item_count = total_drops - green_item_count
        loot = {}
        if green_item_count:
            green_item = self._actions['teleporter_drop']()
            loot[green_item] = green_item_count
        if boss_item_count:
            loot[boss.body.item_drop] = boss_item_count
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
                        if item != Equipment.BossHunter:
                            item = self._reroll_item(equipment)
                            if equipment == Equipment.MultiShopCard:
                                self.has_recycler = False
                                self.can_recycle = False
                    else:
                        self.can_recycle = True
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
        free_chest_items : list
            All items collected from Shipping Request Forms.
        card_multibuys : list
            The names of the interactable spawn card of any multishop that was
            fully looted using an Executive Card.
        gold_orb_spawned : bool
            Whether a Shrine of Gold was encountered.
        """
        loot = {ItemDef: [], EquipmentDef: []}
        boss_shrines = 0
        free_chest_items = []
        card_multibuys = []
        gold_orb_spawned = False
        for isc in interactables:
            if isc in self._actions:
                if 'TripleShop' in isc or 'FreeChest' in isc:
                    if self._inventory.has_card:
                        card_multibuys.append(isc)
                    drops = self._actions[isc]()
                    collected_loot = self._loot_multishop(isc, drops)
                    for item in collected_loot:
                        loot[type(item)].append(item)
                    if isc == 'iscFreeChest':
                        free_chest_items.extend(collected_loot)
                elif isc == 'iscVoidTriple':
                    drops = self._actions[isc]()
                    item = max(drops, key=lambda x: x.tier._tier)
                    self._inventory.give_item(item)
                    loot[type(item)].append(item)
                else:
                    for item in self._actions[isc]():
                        if isinstance(item, ItemDef):
                            self._inventory.give_item(item)
                        elif isinstance(item, EquipmentDef):
                            item = self._collect_equipment(item)
                        loot[type(item)].append(item)
            elif 'ShrineBoss' in isc:
                boss_shrines += 1
            elif 'Goldshores' in isc:
                gold_orb_spawned = True
        return loot, boss_shrines, free_chest_items, card_multibuys, gold_orb_spawned
    
    def _loot_stage(self):
        """Fully loot a normal stage."""
        scene_name = self._scene_name
        if scene_name == SceneName.AD:
            scene_name += '-open' if self._scene_director.is_bonus_credits_available else '-closed'
        stage_dccs = (
            scenes[self._scene_name].stage_info.monsters
            .generate_weighted_selection(self._expansions, self._stages_cleared)
        )
        blue_orb_spawned = random.random() <= BLUE_PORTAL_CHANCE / (self._blue_portals_opened + 1)
        purple_orb_spawned = random.random() <= PURPLE_PORTAL_CHANCE and self._stages_cleared >= 6

        interactables = self._generate_interactables()
        loot, boss_shrines, free_chest_items, card_multibuys, gold_orb_spawned = self._loot_interactables(interactables)

        for item, count in self._loot_teleporter(stage_dccs, boss_shrines).items():
            self._inventory.give_item(item, count)
            loot[ItemDef].extend([item] * count)
        if blue_orb_spawned:
            self._blue_portals_opened += 1

        regen_scraps = self._inventory.count(Items.RegeneratingScrap)
        if TRADE_REGEN_SCRAP and regen_scraps and 'iscDuplicatorLarge' in interactables:
            item = self._actions['green_printer']()
            self._inventory.give_item(item, regen_scraps)
            loot[ItemDef].extend([item] * regen_scraps)
        if self._scene_name == SceneName.AA:
            self._inventory.give_item(Items.IceRing)
            self._inventory.give_item(Items.FireRing)
            loot[ItemDef].extend([Items.IceRing, Items.FireRing])
        elif self._scene_name == SceneName.SC:
            item = self._actions['AWU_drop']()
            self._inventory.give_item(item, self._num_players)
            loot[ItemDef].extend([item] * self._num_players)

        if USE_GOLD_PORTAL and gold_orb_spawned:
            self._next_scene_name = 'goldshores'
        if USE_ARTIFACT_PORTAL and self._scene_name == 'skymeadow':
            self._next_scene_name = 'artifactworld'

        self.stats.update_data(
            scene_name,
            (blue_orb_spawned, gold_orb_spawned, purple_orb_spawned),
            stage_dccs,
            interactables,
            loot,
            free_chest_items,
            card_multibuys,
        )
        return

    def _loot_void_fields(self):
        """Fully loot the Void Fields."""
        scene_name = self._scene_name
        stage_dccs = (
            scenes[scene_name].monsters
            .generate_weighted_selection(self._expansions, self._stages_cleared)
        )

        interactables = self._generate_interactables()
        loot, _, free_chest_items, card_multibuys, _ = self._loot_interactables(interactables)
        for cell in range(9):
            if cell < 4:
                tier = 'tier1'
            elif cell < 8:
                tier = 'tier2'
            else:
                tier = 'tier3'
            potential = self._actions[f'cell_{tier}']()
            for _ in range(self._num_players):
                item = random.choice(potential)
                self._inventory.give_item(item)
                loot[ItemDef].append(item)

        regen_scraps = self._inventory.count(Items.RegeneratingScrap)
        if TRADE_REGEN_SCRAP and regen_scraps and 'iscDuplicatorLarge' in interactables:
            item = self._actions['green_printer']()
            self._inventory.give_item(item, regen_scraps)
            loot[ItemDef].extend([item] * regen_scraps)

        self.stats.update_data(
            scene_name,
            (False, False, True),
            stage_dccs,
            interactables,
            loot,
            free_chest_items,
            card_multibuys,
        )
        self._void_fields_visited = True
        return

    def _loot_gilded_coast(self):
        """Fully loot the Gilded Coast."""
        scene_name = self._scene_name
        stage_dccs = (
            scenes[scene_name].monsters
            .generate_weighted_selection(self._expansions, self._stages_cleared)
        )
        interactables = self._generate_interactables()
        loot, _, free_chest_items, card_multibuys, _ = self._loot_interactables(interactables)
        self._inventory.give_item(Items.TitanGoldDuringTP, self._num_players)
        loot[ItemDef].extend([Items.TitanGoldDuringTP] * self._num_players)
        
        self.stats.update_data(
            scene_name,
            (False, False, False),
            stage_dccs,
            interactables,
            loot,
            free_chest_items,
            card_multibuys,
        )
        return

    def _loot_bulwark_ambry(self):
        """Fully loot Bulwark's Ambry with the Artifact of Command."""
        scene_name = self._scene_name
        stage_dccs = (
            scenes[scene_name].monsters
            .generate_weighted_selection(self._expansions, self._stages_cleared)
        )
        # Cache whether the Artifact of Command is enabled, as it will be turned
        # on for this stage.
        is_command_enabled = self._scene_director.is_command_enabled
        self._scene_director.is_command_enabled = True
        interactables = self._generate_interactables()
        self._scene_director.is_command_enabled = is_command_enabled
        loot, _, free_chest_items, card_multibuys, _ = self._loot_interactables(interactables)

        regen_scraps = self._inventory.count(Items.RegeneratingScrap)
        if TRADE_REGEN_SCRAP and regen_scraps and 'iscDuplicatorLarge' in interactables:
            item = self._actions['green_printer']()
            self._inventory.give_item(item, regen_scraps)
            loot[ItemDef].extend([item] * regen_scraps)

        self.stats.update_data(
            scene_name,
            (False, False, True),
            stage_dccs,
            interactables,
            loot,
            free_chest_items,
            card_multibuys,
        )
        return

    def _advance_stage(self):
        """Advance to the next stage."""
        if scenes[self._scene_name].scene_type == 1:
            self._stages_cleared += 1
            if self._scene_name != 'arena':
                self._stage_order = (scenes[self._scene_name].stage_order + 1) % len(STAGES)
        if not self._next_scene_name:
            self._next_scene_name = self._select_scene(self._stage_order)
        self._scene_name = self._next_scene_name
        self._next_scene_name = None
        self._scene_director.change_scene(self._scene_name)
        if self._scene_name == SceneName.AD:
            self._scene_director.is_bonus_credits_available = random.random() > .5

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
    def spawn_teleporter_boss(dccs, stages_cleared):
        """
        Select a monster for the teleporter.

        Parameters
        ----------
        dccs : DirectorCardCategorySelection
            The selected DCCS for the stage.
        stages_cleared : int
            The number of stages cleared, which affects which monsters are
            available for selection.

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
        monsters = dccs.generate_card_weighted_selection(stages_cleared)
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

    def loot_stages(self, num_stages=5, void_fields=-1):
        """
        Simulate a run by full looting a number of stages.

        Parameters
        ----------
        num_stages : int, optional
            The number of normal stages to loot. This doesn't include any Hidden
            Realms, even if they increase the stages cleared counter.
        void_fields : int, optional
            After what stage to visit the Void Fields. It is assumed it will be
            completed and looted fully. If on the same stage a Gold Portal
            spawns, visiting the Void Fields will still take priority. The
            default setting is to not visit it at all during a run.

        Returns
        -------
        None
        """
        loot_scene = {scene_name: self._loot_stage for scene_name in
                      (scene_name for stage in STAGES for scene_name in stage)}
        loot_scene['arena'] = self._loot_void_fields
        loot_scene['goldshores'] = self._loot_gilded_coast
        loot_scene['artifactworld'] = self._loot_bulwark_ambry
        self._restart()
        if num_stages <= 0:
            return
        if void_fields == 0:
            void_fields = -1
        elif void_fields >= 1:
            num_stages += 1
        while self._stages_cleared < num_stages:
            loot_scene[self._scene_name]()
            if self._stages_cleared == void_fields:
                self._next_scene_name = 'arena'
            self._advance_stage()
