from ._utils import round_value


class CharacterBody:
    SCRIPT = 4977618279312766071

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self._name

    @staticmethod
    def parse(asset, token_names):
        return {
            '_name': asset['baseNameToken'],
            'name': token_names.get(asset['baseNameToken'], ''),
            'flags': asset['bodyFlags'],
            'health': (round_value(asset['baseMaxHealth']),
                       round_value(asset['levelMaxHealth'])),
            'regen': (round_value(asset['baseRegen']),
                      round_value(asset['levelRegen'])),
            'damage': (round_value(asset['baseDamage']),
                       round_value(asset['levelDamage'])),
            'attack_speed': round_value(asset['baseAttackSpeed']),
            'crit': asset['baseCrit'],
            'luck': asset['wasLucky'],
            'speed': round_value(asset['baseMoveSpeed']),
            'sprint_multiplier': round_value(asset['sprintingSpeedMultiplier']),
            'acceleration': round_value(asset['baseAcceleration']),
            'jump': asset['baseJumpCount'],
            'jump_power': round_value(asset['baseJumpPower']),
            'armor': round_value(asset['baseArmor']),
            'is_champion': bool(asset['isChampion']),
            # To be filled out once all file ids have been collected
            'item_drop': asset['m_GameObject']['m_PathID'],
        }


class CharacterMaster:
    SCRIPT = -7300313650832695883


class DeathRewards:
    SCRIPT = 8463862091779802982
