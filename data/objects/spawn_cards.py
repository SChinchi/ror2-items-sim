from ._utils import round_value


class SpawnCard:
    SCRIPT = 4691379092647972189

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        delattr(self, 'class')

    def __repr__(self):
        return self._name
    
    @staticmethod
    def parse(asset):
        return {
            'class': 'SpawnCard',
            '_name': asset['m_Name'],
            # To be filled out once all file ids have been collected
            'name': asset['prefab']['m_PathID'],
            'required_flags': asset['requiredFlags'],
            'forbidden_flags': asset['forbiddenFlags'],
            'cost': asset['directorCreditCost'],
        }


class InteractableSpawnCard(SpawnCard):
    SCRIPT = -1452994546013412074
    
    @staticmethod
    def parse(asset):
        data = super(InteractableSpawnCard, InteractableSpawnCard).parse(asset)
        data.update({
            'class': 'InteractableSpawnCard',
            'skip_with_sacrifice': bool(asset['skipSpawnWhenSacrificeArtifactEnabled']),
            'sacrifice_weight': round_value(asset['weightScalarWhenSacrificeArtifactEnabled']),
            'limit': asset['maxSpawnsPerStage'],
            # To be filled out once all file ids have been collected
            'drop_table': asset['prefab']['m_PathID'],
            # To be filled out once all file ids have been collected
            'controller': asset['prefab']['m_PathID'],
            # To be filled out once all file ids have been collected
            'offers_choice': asset['prefab']['m_PathID'],
            # To be filled out once all file ids have been collected
            'can_reset': asset['prefab']['m_PathID'],
            # To be filled out once all file ids have been collected
            'is_sale_star_compatible': asset['prefab']['m_PathID'],
            # To be filled out once all file ids have been collected
            'expansion': asset['prefab']['m_PathID'],
        })
        return data


class CharacterSpawnCard(SpawnCard):
    SCRIPT = -2671867307903452571
    
    @staticmethod
    def parse(asset):
        data = super(CharacterSpawnCard, CharacterSpawnCard).parse(asset)
        data.update({
            'class': 'CharacterSpawnCard',
            'elite_rules': asset['eliteRules'],
            'no_elites': bool(asset['noElites']),
            'forbidden_as_boss': bool(asset['forbiddenAsBoss']),
            # To be filled out once all file ids have been collected
            'equipment': [e['m_PathID'] for e in asset['equipmentToGrant']],
            # To be filled out once all file ids have been collected
            'items': [(i['itemDef']['m_PathID'], i['count']) for i in asset['itemsToGrant']],
            # To be filled out once all file ids have been collected
            'body': asset['prefab']['m_PathID'],
            # To be filled out once all file ids have been collected
            'master': asset['prefab']['m_PathID'],
        })
        return data


class MultiCharacterSpawnCard(CharacterSpawnCard):
    SCRIPT = 4835371849398150560

    @staticmethod
    def parse(asset):
        data = super(MultiCharacterSpawnCard, MultiCharacterSpawnCard).parse(asset)
        data.update({'class': 'MultiCharacterSpawnCard'})
        return data
