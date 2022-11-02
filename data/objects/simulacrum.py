from ._utils import round_value


class InfiniteTowerWaveController:
    SCRIPT = -6484494821379467026

    @staticmethod
    def parse(asset, ids):
        data = {
            'class': 'InfiniteTowerWaveController',
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
        data = InfiniteTowerWaveController.parse(asset, ids)
        data.update({
            'class': 'InfiniteTowerBossWaveController',
            'guarantee_champion': bool(asset['guaranteeInitialChampion']),
        })
        return data


class InfiniteTowerExplicitWaveController(InfiniteTowerWaveController):
    SCRIPT = -4436197429497956349

    @staticmethod
    def parse(asset, ids):
        data = InfiniteTowerWaveController.parse(asset, ids)
        data['class'] = 'InfiniteTowerExplicitWaveController'
        spawn_list = asset['spawnList'][0]
        data['spawn'] = {
            'count': spawn_list['count'],
            'spawn_card': ids[spawn_list['spawnCard']['m_PathID']]['m_Name'],
        }
        return data
