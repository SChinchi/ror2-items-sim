import random

from ._utils import round_value
from .items import EquipmentDef, ItemDef


_WEIGHT_NAMES = (
    'tier1Weight', 'tier2Weight', 'tier3Weight', 'bossWeight',
    'lunerEquipmentWeight', 'lunarItemWeight', 'lunarCombinedWeight',
    'equipmentWeight',
    'voidTier1Weight', 'voidTier2Weight', 'voidTier3Weight', 'voidBossWeight',
)


def _filter_tier_items(drop_table, tier_droplists):
    items = []
    weights = []
    required_tags = set(drop_table.required_tags)
    banned_tags = set(drop_table.banned_tags)
    for tier_items, weight in zip(tier_droplists, drop_table.weights):
        if weight <= 0 or not tier_items:
            continue
        if required_tags:
            tier_items = [
                item for item in tier_items
                if (isinstance(item, ItemDef) and required_tags.intersection(item.tags)) or
                    isinstance(item, EquipmentDef)
            ]
        tier_items = [
            item for item in tier_items
            if (isinstance(item, ItemDef) and not banned_tags.intersection(item.tags)) or
                isinstance(item, EquipmentDef)
        ]
        if tier_items:
            items.append(tier_items)
            weights.append(weight)
    return items, weights


class PickupDropTable:
    SCRIPT = None

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        raise NotImplementedError

    @staticmethod
    def parse(asset):
        return {
            'class': 'PickupDropTable',
            'can_be_replaced': bool(asset['canDropBeReplaced']),
        }

    def generate_loot_drop_action(self, tier_droplists):
        raise NotImplementedError


class ArenaMonsterItemDropTable(PickupDropTable):
    SCRIPT = 6355564085484888252

    def __init__(self, data):
        super().__init__(data)
        delattr(self, 'class')

    def __repr__(self):
        out = {
            'can_be_replaced': self.can_be_replaced,
            'required_tags': self.required_tags,
            'banned_tags': self.banned_tags,
            'weights': self.weights,
        }
        return repr(out)

    @staticmethod
    def parse(asset):
        data = super(ArenaMonsterItemDropTable, ArenaMonsterItemDropTable).parse(asset)
        data.update({
            'class': 'ArenaMonsterItemDropTable',
            'required_tags': asset['requiredItemTags'],
            'banned_tags': asset['bannedItemTags'],
            'weights': [round_value(asset.get(weight, 0)) for weight in _WEIGHT_NAMES],
        })
        return data

    def generate_loot_drop_action(self, tier_droplists):
        items, weights = _filter_tier_items(self, tier_droplists)
        return lambda: random.choice(random.choices(items, weights)[0])

    
class BasicPickupDropTable(PickupDropTable):
    SCRIPT = -3444164123217549294

    def __init__(self, data):
        super().__init__(data)
        delattr(self, 'class')

    def __repr__(self):
        out = {
            'can_be_replaced': self.can_be_replaced,
            'required_tags': self.required_tags,
            'banned_tags': self.banned_tags,
            'weights': self.weights,
        }
        return repr(out)

    @staticmethod
    def parse(asset):
        data = super(BasicPickupDropTable, BasicPickupDropTable).parse(asset)
        data.update({
            'class': 'BasicPickupDropTable',
            'required_tags': asset['requiredItemTags'],
            'banned_tags': asset['bannedItemTags'],
            'weights': [round_value(asset.get(weight, 0)) for weight in _WEIGHT_NAMES],
        })
        return data

    def generate_loot_drop_action(self, tier_droplists):
        items, weights = _filter_tier_items(self, tier_droplists)
        # The way an item is chosen in the game is defined in
        # `RoR2.BasicPickupDropTable.GenerateWeightedSelection`, which adds all
        # items in a flat list, with each item of a tier having a weight
        # "<tier>Weight". This creates an obvious bias towards tiers that have
        # more items, which we recreate here.
        total = sum(map(len, items))
        weights = [w * len(i) / total for i, w in zip(items, weights)]
        return lambda: random.choice(random.choices(items, weights)[0])


class DoppelgangerDropTable(PickupDropTable):
    SCRIPT = 8229327428296551755

    def __init__(self, data):
        super().__init__(data)
        delattr(self, 'class')

    def __repr__(self):
        out = {
            'can_be_replaced': self.can_be_replaced,
            'required_tags': self.required_tags,
            'banned_tags': self.banned_tags,
            'weights': self.weights,
        }
        return repr(out)

    @staticmethod
    def parse(asset):
        data = super(DoppelgangerDropTable, DoppelgangerDropTable).parse(asset)
        data.update({
            'class': 'DoppelgangerDropTable',
            'required_tags': asset['requiredItemTags'],
            'banned_tags': asset['bannedItemTags'],
            'weights': [round_value(asset.get(weight, 0)) for weight in _WEIGHT_NAMES],
        })
        return data

    def generate_loot_drop_action(self, tier_droplists):
        items, weights = _filter_tier_items(self, tier_droplists)
        return lambda: random.choice(random.choices(items, weights)[0])


class ExplicitPickupDropTable(PickupDropTable):
    SCRIPT = -8185837855437012288

    def __init__(self, data):
        super().__init__(data)
        delattr(self, 'class')

    def __repr__(self):
        out = {
            'can_be_replaced': self.can_be_replaced,
            'entries': self.entries,
        }
        return repr(out)

    @staticmethod
    def parse(asset):
        data = super(ExplicitPickupDropTable, ExplicitPickupDropTable).parse(asset)
        data.update({
            'class': 'ExplicitPickupDropTable',
            'entries': [[e['pickupDef']['m_PathID'], e['pickupWeight']]
                        for e in asset['pickupEntries']],
        })
        return data

    def generate_loot_drop_action(self, tier_droplists):
        items, weights = zip(self.entries)
        return lambda: random.choice(random.choices(items, weights)[0])


class FreeChestDropTable(PickupDropTable):
    SCRIPT = 3728958355032723917

    def __init__(self, data):
        super().__init__(data)
        delattr(self, 'class')

    def __repr__(self):
        out = {
            'can_be_replaced': self.can_be_replaced,
            'weights': self.weights,
        }
        return repr(out)

    @staticmethod
    def parse(asset):
        data = super(FreeChestDropTable, FreeChestDropTable).parse(asset)
        data.update({
            'class': 'FreeChestDropTable',
            'weights': [round_value(asset.get(weight, 0)) for weight in _WEIGHT_NAMES],
        })
        return data

    def bind_inventory(self, inventory):
        self.inventory = inventory

    def generate_loot_drop_action(self, tier_droplists):
        # Unused
        return
