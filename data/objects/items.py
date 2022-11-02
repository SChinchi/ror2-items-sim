from ._utils import round_value


class ItemTierDef:
    SCRIPT = 4020630569963760157

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self._name

    @staticmethod
    def parse(asset):
        return {
            '_name': asset['m_Name'],
            '_tier': asset['_tier'],
            'is_droppable': bool(asset['isDroppable']),
            'can_scrap': bool(asset['canScrap']),
            'can_restack': bool(asset['canRestack']),
        }


class ItemDef:
    SCRIPT = 7272334662194190074

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.name

    @staticmethod
    def parse(asset, token_names):
        return {
            '_name': asset['m_Name'],
            'name': token_names.get(asset['nameToken'], asset['nameToken']),
            'tier': asset['deprecatedTier'],
            'hidden': bool(asset['hidden']),
            'can_remove': bool(asset['canRemove']),
            # To be filled out once all file ids have been collected
            'required_dlc': asset['requiredExpansion']['m_PathID'],
            'tags': asset['tags'],
        }


class EquipmentDef:
    SCRIPT = -6609762232512421743

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.name

    @staticmethod
    def parse(asset, token_names):
        return {
            '_name': asset['m_Name'],
            'name': token_names.get(asset['nameToken'], asset['nameToken']),
            'cooldown': asset['cooldown'],
            'can_drop': asset['canDrop'],
            'death_drop_chance': round_value(asset['dropOnDeathChance']),
            'enigma_compatible': bool(asset['enigmaCompatible']),
            'is_lunar': bool(asset['isLunar']),
            'is_boss': bool(asset['isBoss']),
            # To be filled out once all file ids have been collected
            'required_dlc': asset['requiredExpansion']['m_PathID'],
        }
