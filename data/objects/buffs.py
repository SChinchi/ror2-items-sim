class BuffDef:
    SCRIPT = 4179898196218652458

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self._name

    @staticmethod
    def parse(asset):
        return {
            '_name': asset['m_Name'],
            'can_stack': bool(asset['canStack']),
            'is_debuff': bool(asset['isDebuff']),
            'ignore_growth_nectar': bool(asset['ignoreGrowthNectar']),
            'is_cooldown': bool(asset['isCooldown']),
            }
