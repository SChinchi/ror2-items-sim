from ._utils import round_value
from .dccs import DccsPool

class ClassicStageInfo:
    SCRIPT = 8450768357395489424

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    @staticmethod
    def parse(asset, ids):
        interactables_dp = asset['interactableDccsPool']['m_PathID']
        monsters_dp = asset['monsterDccsPool']['m_PathID']
        return {
            'interactable_credits': asset['sceneDirectorInteractibleCredits'],
            'monster_credits': asset['sceneDirectorMonsterCredits'],
            'bonus_credits': [o['points'] for o in asset['bonusInteractibleCreditObjects']
                              if o['objectThatGrantsPointsIfEnabled']['m_PathID']],
            'interactables': DccsPool.parse(ids[interactables_dp], ids) if interactables_dp else None,
            'monsters': DccsPool.parse(ids[monsters_dp], ids) if monsters_dp else None,
        }


class CampDirector:
    SCRIPT = -3655719543255941067

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.name

    @staticmethod
    def parse(asset):
        return {
            # To be filled out once all file_ids have been collected
            'name': asset['m_GameObject']['m_PathID'],
            'interactable_credits': asset['baseInteractableCredit'],
            'monster_credits': asset['baseMonsterCredit'],
            # To be filled out once all file ids have been collected
            'interactables': asset['interactableDirectorCards']['m_PathID'],
            # To be filled out once all file ids have been collected
            'monsters': asset['combatDirector']['m_PathID'],
        }


class CombatDirector:
    SCRIPT = 786565555335027584

    @staticmethod
    def parse(asset, ids):
        cards = asset['_monsterCards']['m_PathID']
        return {
            'credits': round_value(asset['monsterCredit']),
            'exp_coeff': round_value(asset['expRewardCoefficient']),
            'gold_coeff': round_value(asset['goldRewardCoefficient']),
            'series_spawn_interval': (round_value(asset['minSeriesSpawnInterval']),
                                      round_value(asset['maxSeriesSpawnInterval'])),
            'reroll_spawn_interval': (round_value(asset['minRerollSpawnInterval']),
                                      round_value(asset['maxRerollSpawnInterval'])),
            'money_wave_intervals': [(round_value(r['min']), round_value(r['max']))
                                     for r in asset['moneyWaveIntervals']],
            'team': asset['teamIndex'],
            'credit_multiplier': round_value(asset['creditMultiplier']),
            'spawn_one_wave': bool(asset['shouldSpawnOneWave']),
            'skip_if_cheap': bool(asset['skipSpawnIfTooCheap']),
            'max_skips': asset['maxConsecutiveCheapSkips'],
            'reset_monster_card': bool(asset['resetMonsterCardIfFailed']),
            'max_spawns': asset['maximumNumberToSpawnBeforeSkipping'],
            'elite_bias': round_value(asset['eliteBias']),
            'ignore_team_size': bool(asset['ignoreTeamSizeLimit']),
            '_monster_cards': ids[cards]['m_Name'] if cards else None,
        }


class SceneDirector:
    SCRIPT = -2207557892185297087

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.name

    @staticmethod
    def parse(asset, ids):
        teleporter_id = asset['teleporterSpawnCard']['m_PathID']
        return {
            'teleporter': ids[teleporter_id]['m_Name'] if teleporter_id else None,
            'exp_coeff': round_value(asset['expRewardCoefficient']),
            'elite_bias': round_value(asset['eliteBias']),
        }


class SceneObjectToggleGroup:
    SCRIPT = -5674775494453513432
