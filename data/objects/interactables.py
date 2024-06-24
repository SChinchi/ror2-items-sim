import random

from ._utils import round_value
from .droptables import _filter_tier_items


_TRIPLE_SHOP_HIDDEN_CHANCE = .2
_FREE_CHEST_HIDDEN_CHANCE = 1.


class ShopTerminalBehavior:
    SCRIPT = -4129600921950285708

    @staticmethod
    def generate_purchase_action(isc, tier_droplists, inventory):
        drop = isc.drop_table.generate_loot_drop_action(tier_droplists)
        # Caution, this is not a list!
        return lambda: drop()


class MultiShopController:
    SCRIPT = 1424852041901811614

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
    SCRIPT = 1301021428291817354


class PurchaseInteraction:
    SCRIPT = 3424499719950130566


class BarrelInteraction:
    SCRIPT = -3449937006512166558


class GenericDisplayNameProvider:
    SCRIPT = -8577128845896015032


class ChestBehavior:
    SCRIPT = -7227317202796181736

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
    SCRIPT = -1192547833112862499


class ShrineChanceBehavior:
    SCRIPT = -117010359117308110

    @staticmethod
    def generate_purchase_action(isc, tier_droplists, inventory):
        drop = isc.drop_table.generate_loot_drop_action(tier_droplists)
        max_drops = 2
        return lambda: [drop() for _ in range(max_drops)]


class OptionChestBehavior:
    SCRIPT = 6904566514339317880

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


class DelusionChestController:
    SCRIPT = -1406854975882462628


class PortalStatueBehavior:
    SCRIPT = 8917583605525748003
