import random

from ._utils import round_value


class Run:
    SCRIPT = -1835672323730203791

    @staticmethod
    def parse(asset, ids):
        return {'class': 'Run'}


class InfiniteTowerRun(Run):
    SCRIPT = -5287072886721368087

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        delattr(self, 'class')

    @staticmethod
    def parse(asset, ids):
        data = super(InfiniteTowerRun, InfiniteTowerRun).parse(asset, ids)
        data.update({
            'class': 'InfiniteTowerRun',
            'interactable_credits': asset['interactableCredits'],
            'blacklisted_tags': asset['blacklistedTags'],
            'blacklisted_items': [ids[item['m_PathID']]['m_Name']
                                  for item in asset['blacklistedItems']],
            # To be filled out later
            'wave_categories': [InfiniteTowerWaveCategory.parse(ids[category['m_PathID']], ids)
                                for category in asset['waveCategories']],
        })
        return data


class InfiniteTowerWaveCategory:
    SCRIPT = 7024568621037390213

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        self.waves = [WeightedWave(wave) for wave in self.waves]

    def __repr__(self):
        return self.name

    @staticmethod
    def parse(asset, ids):
        data = ({
            'name': asset['m_Name'],
            'waves': [WeightedWave.parse(wave, ids) for wave in asset['wavePrefabs']],
            'availability_period': asset['availabilityPeriod'],
            'min_wave': asset['minWaveIndex'],
        })
        return data

    def is_available(self, run):
        """
        Check whether this category is available for selection.

        Parameters
        ----------
        run : InfiniteTowerRun
            The Simulacrum run instance.

        Returns
        -------
        bool

        Notes
        -----
        An implementation of `RoR2.InfiniteTowerWaveCategory.IsAvailable`.
        """
        condition1 = self.availability_period > 0 and self.availability_period % run._wave == 0
        condition2 = run._wave >= self.min_wave
        if condition1 and condition2 and self.waves:
            for wave in self.waves:
                if wave.is_available(run):
                    return True
        return False

    def select_wave(self, run):
        """
        Select a weighted wave from this category.

        Parameters
        ----------
        run : InfiniteTowerRun
            The Simulacrum run instance.

        Returns
        -------
        InfiniteTowerWaveController
            The selected wave.

        Notes
        -----
        An implementation of `RoR2.InfiniteTowerWaveCategory.SelectWavePrefab`.
        """
        waves = []
        weights = []
        for wave in self.waves:
            if wave.is_available(run):
                waves.append(wave.wave)
                weights.append(wave.weight)
        return random.choices(waves, weights)[0]


class WeightedWave:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        self.wave = eval(self.wave['class'])(self.wave)

    def is_available(self, run):
        """
        Check whether this wave is available.

        Parameters
        ----------
        run : InfiniteTowerRun
            The Simulacrum run instance.

        Returns
        -------
        bool

        Notes
        -----
        An implementation of `RoR2.InfiniteTowerWavePrerequisites.AreMet`.
        """
        p = self.prerequisites
        return p is None or p == 'Wave11OrGreaterPrerequisite' and run._wave >= 11

    @staticmethod
    def parse(data, ids):
        prerequisites = data['prerequisites']['m_PathID']
        return {
            # To be filled out later
            'wave': data['wavePrefab']['m_PathID'],
            'prerequisites': ids[prerequisites]['m_Name'] if prerequisites else None,
            'weight': round_value(data['weight']),
        }


class InfiniteTowerWaveController:
    SCRIPT = -6484494821379467026

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        delattr(self, 'class')

    def __repr__(self):
        return self.name

    @staticmethod
    def parse(asset, ids):
        data = {
            'class': 'InfiniteTowerWaveController',
            # To be filled out later,
            'name': '',
            'credits': round_value(asset['baseCredits']),
            'wave_period': round_value(asset['wavePeriodSeconds']),
            'immediate_credits_fraction': round_value(asset['immediateCreditsFraction']),
            'max_squad': asset['maxSquadSize'],
            'drop_table': ids[asset['rewardDropTable']['m_PathID']]['m_Name'],
        }
        return data


class InfiniteTowerBossWaveController(InfiniteTowerWaveController):
    SCRIPT = -3908559451701991716

    @staticmethod
    def parse(asset, ids):
        data = super(InfiniteTowerBossWaveController, InfiniteTowerBossWaveController).parse(asset, ids)
        data.update({
            'class': 'InfiniteTowerBossWaveController',
            'guarantee_champion': bool(asset['guaranteeInitialChampion']),
        })
        return data


class InfiniteTowerExplicitWaveController(InfiniteTowerWaveController):
    SCRIPT = -4436197429497956349

    @staticmethod
    def parse(asset, ids):
        data = super(InfiniteTowerExplicitWaveController, InfiniteTowerExplicitWaveController).parse(asset, ids)
        spawn_list = asset['spawnList']
        data.update({
            'class': 'InfiniteTowerExplicitWaveController',
            'spawn_list': [
                (ids[spawn_info['spawnCard']['m_PathID']]['m_Name'], spawn_info['count'])
                for spawn_info in asset['spawnList']
            ]
        })
        return data
