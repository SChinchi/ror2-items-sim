import random

from ._utils import check_roll
from .droptables import _filter_tier_items


_TRIPLE_SHOP_HIDDEN_CHANCE = .2
_FREE_CHEST_HIDDEN_CHANCE = 1.


class ShopTerminalBehavior:
    SCRIPT = 5408283236048349533

    @staticmethod
    def generate_purchase_action(isc, tier_droplists, inventory):
        drop = isc.drop_table.generate_loot_drop_action(tier_droplists)
        # Caution, this is not a list!
        return lambda: drop()


class MultiShopController:
    SCRIPT = -7922445689230849788

    @staticmethod
    def _drop_tripleshop_loot(drop, max_drops, inventory):
        loot = [[drop(), True]]
        for _ in range(1, max_drops):
            loot.append([drop(), random.random() > _TRIPLE_SHOP_HIDDEN_CHANCE])
        return loot

    @staticmethod
    def _drop_freechest_loot(drop_table, tier_droplists, max_drops, inventory):
        weights = drop_table.weights[:3]
        n = inventory.count_by_name('FreeChest')
        weights = (weights[0], weights[1] * n, weights[2] * n**2)
        items = tier_droplists[:3]
        loot = [[random.choice(random.choices(items, weights)[0]), True]]
        for _ in range(1, max_drops):
            loot.append([
                random.choice(random.choices(items, weights)[0]),
                random.random() > _FREE_CHEST_HIDDEN_CHANCE,
            ])
        return loot

    @staticmethod
    def generate_purchase_action(isc, tier_droplists, inventory):
        if isc._name == 'iscFreeChest':
            isc.drop_table.bind_inventory(inventory)
            max_drops = 2
        else:
            max_drops = 3
        drop = isc.drop_table.generate_loot_drop_action(tier_droplists)
        if 'TripleShop' in isc._name:
            return lambda: MultiShopController._drop_tripleshop_loot(drop, max_drops, inventory)
        elif isc._name == 'iscFreeChest':
            return lambda: MultiShopController._drop_freechest_loot(
                isc.drop_table, tier_droplists, max_drops, inventory
            )
        else:
            raise ValueError(f'Unknown Multishop type encountered: {isc._name}')


class ScrapperController:
    SCRIPT = 7544738841730975347


class PurchaseInteraction:
    SCRIPT = -1109085999899981170


class BarrelInteraction:
    SCRIPT = -6402843602939064730


class GenericDisplayNameProvider:
    SCRIPT = 3766062818251561924


class ChestBehavior:
    SCRIPT = 3064004133398835955

    @staticmethod
    def generate_purchase_action(isc, tier_droplists, inventory):
        if 'Backpack' not in isc._name:
            drop = isc.drop_table.generate_loot_drop_action(tier_droplists)
            return lambda: [drop()]
        else:
            # The Scavenger's backpack doesn't use the droptable API, which
            # means its drops won't be rerolled for lunar items.
            if 'Lunar' in isc._name:
                raise ValueError("The Lunar Coin isn't implemented.")
            else:
                items, weights = _filter_tier_items(isc.drop_table, tier_droplists)
                drop = lambda: random.choice(random.choices(items, weights)[0])
            max_drops = 10
            return lambda: [drop() for _ in range(max_drops)]


class RouletteChestController:
    SCRIPT = 3253615885668395195


class ShrineChanceBehavior:
    SCRIPT = -5094190573479519615
    DOLL_ITEM = None
    DOLL_DROPTABLE = None

    @staticmethod
    def generate_purchase_action(isc, tier_droplists, inventory):
        def generate_loot():
            max_drops = 2
            loot = []
            # The loot is not added to the inventory at this point, so we need
            # to keep track if the first item is a Chance Doll so it can
            # influence the second drop.
            found_doll = False
            for _ in range(max_drops):
                doll_stacks = found_doll + inventory.count(ShrineChanceBehavior.DOLL_ITEM)
                use_doll = False
                if doll_stacks:
                    use_doll = check_roll(30 + doll_stacks * 10, inventory)
                loot.append(doll_drop() if use_doll else normal_drop())
                found_doll = loot[-1] == ShrineChanceBehavior.DOLL_ITEM
            return loot

        normal_drop = isc.drop_table.generate_loot_drop_action(tier_droplists)
        doll_drop = ShrineChanceBehavior.DOLL_DROPTABLE.generate_loot_drop_action(tier_droplists)
        return generate_loot


class OptionChestBehavior:
    SCRIPT = 1140539183348208526

    @staticmethod
    def _drop_unique_loot(items, weights, max_drops):
        items = items.copy()
        weights = weights.copy()
        drops = []
        for _ in range(max_drops):
            index = random.choices(range(len(items)), weights)[0]
            drops.append(items.pop(index))
            weights.pop(index)
        return drops
        
    @staticmethod
    def generate_purchase_action(drop_table, tier_droplists, max_drops):
        items, weights = _filter_tier_items(drop_table, tier_droplists)
        all_items = []
        all_weights = []
        for tier_items, weight in zip(items, weights):
            all_items.extend(tier_items)
            all_weights.extend([weight] * len(tier_items))
        return lambda: OptionChestBehavior._drop_unique_loot(all_items, all_weights, max_drops)


class HalcyoniteShrineInteractable:
    SCRIPT = 1412567959929496626

    @staticmethod
    def _drop_combined_unique_loot(items, weights, storm_items, storm_weights, max_options):
        items = items.copy()
        weights = weights.copy()
        storm_items = storm_items.copy()
        storm_weights = storm_weights.copy()
        drops = []
        normal_drops = storm_drops = 0
        for _ in range(max_options):
            if storm_drops <= normal_drops - 2:
                index = random.choices(range(len(storm_items)), storm_weights)[0]
                drops.append(storm_items.pop(index))
                storm_weights.pop(index)
                storm_drops += 1
            else:
                index = random.choices(range(len(items)), weights)[0]
                drops.append(items.pop(index))
                weights.pop(index)
                normal_drops += 1
        return drops
    
    @staticmethod
    def generate_purchase_action(normal_droptable, storm_droptable, tier_droplists, max_options):
        items, weights = _filter_tier_items(normal_droptable, tier_droplists)
        all_items = []
        all_weights = []
        for tier_items, weight in zip(items, weights):
            all_items.extend(tier_items)
            all_weights.extend([weight] * len(tier_items))
        storm_items, storm_weights = _filter_tier_items(storm_droptable, tier_droplists)
        all_storm_items = []
        all_storm_weights = []
        for tier_items, weight in zip(storm_items, storm_weights):
            all_storm_items.extend(tier_items)
            all_storm_weights.extend([weight] * len(tier_items))
        return lambda: HalcyoniteShrineInteractable._drop_combined_unique_loot(
            all_items, all_weights, all_storm_items, all_storm_weights, max_options
        )


class DelusionChestController:
    SCRIPT = -3197331057398115314


class PortalStatueBehavior:
    SCRIPT = -6683459890407175108

