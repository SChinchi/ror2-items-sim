from ._utils import round_value
from .dccs import DccsPool, DCCSBlender, FamilyDirectorCardCategorySelection


class SceneDef:
    SCRIPT = 8840691853520611451

    @staticmethod
    def parse(asset, fname):
        return {
            'scene_type': asset['sceneType'],
            'stage_order': asset['stageOrder']-1,
            # To be filled out once all file_ids have been collected
            'required_dlc': asset['requiredExpansion']['m_PathID'],
            # To be filled out once all file_ids have been collected
            'destinations': asset['destinationsGroup']['m_PathID'],
            # To be filled out once all file_ids have been collected
            'destinations_loop': asset['loopedDestinationsGroup']['m_PathID'],
            'use_looping_destinations': bool(asset['shouldUpdateSceneCollectionAfterLooping']),
            'skip_devotion': bool(asset['needSkipDevotionRespawn']),
            'stage_file': fname,
            'stage_info': None,
            'scene_director': None,
            'combat_director': None,
            'newt': None,
        }

class ClassicStageInfo:
    SCRIPT = 5201196302767144762

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def rebuild_cards(self, expansions, stages_cleared):
        """
        Generate the monster and interctable DCCS for the stage.

        Parameters
        ----------
        expansions
            The expansions enabled, which affects which selections are available.
        stages_cleared : int
            The number of stages cleared, which also affects which selections
            are available.

        Returns
        -------
        List of DirectorCardCategorySelection

        Notes
        -----
        A partial implementation of `RoR2.ClassicStageInfo.RebuildCards`.
        """
        monsters = None
        interactables = None
        if self.monsters:
            monster_pool_category = self.monsters.generate_weighted_category_selection(
                expansions, stages_cleared,
            )
            if not self.is_category_selection_family(monster_pool_category):
                monsters = DCCSBlender.get_blended_dccs(
                    monster_pool_category, expansions, stages_cleared, None
                )
            else:
                monsters = self.monsters.generate_weight_selection_from_single_category(
                    monster_pool_category, expansions, stages_cleared
                )
        if monsters and self.interactables:
            if monsters.expansions_in_effect:
                interactables = DCCSBlender.get_blended_dccs(
                    self.interactables.categories[0], expansions, stages_cleared,
                    monsters.expansions_in_effect
                )
            else:
                interactables = DCCSBlender.get_blended_dccs(
                    self.interactables.categories[0], expansions, stages_cleared,
                    None
                )
        return monsters, interactables

    def is_category_selection_family(self, category):
        """
        Whether a DccsPoolCategory contains FamilyDirectorCardCategorySelection.
        """
        for entry in category.always_included:
            if isinstance(entry.dccs, FamilyDirectorCardCategorySelection):
                return True
        for entry in category.included_conditions_met:
            if isinstance(entry.dccs, FamilyDirectorCardCategorySelection):
                return True
        for entry in category.included_conditions_not_met:
            if isinstance(entry.dccs, FamilyDirectorCardCategorySelection):
                return True
        return False

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
    SCRIPT = 3381815531761594789

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
    SCRIPT = 8029171733164660570

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
    SCRIPT = -9115761788320711521

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
    SCRIPT = 255001275373988943
