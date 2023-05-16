from ._utils import round_value


class SkillDef:
    SCRIPT = 7610544427805846859

    @staticmethod
    def parse(asset):
        return {
            'class': 'SkillDef',
            'name': asset['skillName'],
            'recharge': round_value(asset['baseRechargeInterval']),
            'stock': asset['baseMaxStock'],
            'recharge_stock': asset['rechargeStock'],
            'required_stock': asset['requiredStock'],
            'stock_consume': asset['stockToConsume'],
            'cancel_sprinting': bool(asset['cancelSprintingOnActivation']),
            'cancel_from_sprinting': bool(asset['canceledFromSprinting']),
            'is_combat_skill': bool(asset['isCombatSkill']),
        }


class CaptainOrbitalSkillDef(SkillDef):
    SCRIPT = -8444492761160495637

    @staticmethod
    def parse(asset):
        data = super(CaptainOrbitalSkillDef, CaptainOrbitalSkillDef).parse(asset)
        data.update({'class': 'CaptainOrbitalSkillDef'})
        return data


class CaptainSupplyDropSkillDef(CaptainOrbitalSkillDef):
    SCRIPT = -1520831171531849662

    @staticmethod
    def parse(asset):
        data = super(CaptainSupplyDropSkillDef, CaptainSupplyDropSkillDef).parse(asset)
        data.update({'class': 'CaptainSupplyDropSkillDef'})
        return data


class ComboSkillDef(SkillDef):
    SCRIPT = None

    @staticmethod
    def parse(asset):
        data = super(ComboSkillDef, ComboSkillDef).parse(asset)
        data.update({'class': 'ComboSkillDef'})
        return data


class ConditionalSkillDef(SkillDef):
    SCRIPT = None

    @staticmethod
    def parse(asset):
        data = super(ConditionalSkillDef, ConditionalSkillDef).parse(asset)
        data.update({'class': 'ConditionalSkillDef'})
        return data


class EngiMineDeployerSkillDef(SkillDef):
    SCRIPT = -8649664645951429598

    @staticmethod
    def parse(asset):
        data = super(EngiMineDeployerSkillDef, EngiMineDeployerSkillDef).parse(asset)
        data.update({'class': 'EngiMineDeployerSkillDef'})
        return data


class GroundedSkillDef(SkillDef):
    SCRIPT = -7873569907532699362

    @staticmethod
    def parse(asset):
        data = super(GroundedSkillDef, GroundedSkillDef).parse(asset)
        data.update({'class': 'GroundedSkillDef'})
        return data


class HuntressTrackingSkillDef(SkillDef):
    SCRIPT = 3554056196578853390

    @staticmethod
    def parse(asset):
        data = super(HuntressTrackingSkillDef, HuntressTrackingSkillDef).parse(asset)
        data.update({'class': 'HuntressTrackingSkillDef'})
        return data


class LunarDetonatorSkill(SkillDef):
    SCRIPT = -8772907472353264501

    @staticmethod
    def parse(asset):
        data = super(LunarDetonatorSkill, LunarDetonatorSkill).parse(asset)
        data.update({'class': 'LunarDetonatorSkill'})
        return data


class LunarPrimaryReplacementSkill(SkillDef):
    SCRIPT = 7336042660754702565

    @staticmethod
    def parse(asset):
        data = super(LunarPrimaryReplacementSkill, LunarPrimaryReplacementSkill).parse(asset)
        data.update({'class': 'LunarPrimaryReplacementSkill'})
        return data


class LunarSecondaryReplacementSkill(SkillDef):
    SCRIPT = -3218674271630078367

    @staticmethod
    def parse(asset):
        data = super(LunarSecondaryReplacementSkill, LunarSecondaryReplacementSkill).parse(asset)
        data.update({'class': 'LunarSecondaryReplacementSkill'})
        return data


class MasterSpawnSlotSkillDef(SkillDef):
    SCRIPT = 825776219089779548

    @staticmethod
    def parse(asset):
        data = super(MasterSpawnSlotSkillDef, MasterSpawnSlotSkillDef).parse(asset)
        data.update({'class': 'MasterSpawnSlotSkillDef'})
        return data


class MercDashSkillDef(SkillDef):
    SCRIPT = 8003891935907968607

    @staticmethod
    def parse(asset):
        data = super(MercDashSkillDef, MercDashSkillDef).parse(asset)
        data.update({
            'class': 'MercDashSkillDef',
            'max_dashes': asset['maxDashes'],
            'timeout': round_value(asset['timeoutDuration']),
        })
        return data


class PassiveItemSkillDef(SkillDef):
    SCRIPT = -2197157784230743673

    @staticmethod
    def parse(asset):
        data = super(PassiveItemSkillDef, PassiveItemSkillDef).parse(asset)
        data.update({
            'class': 'PassiveItemSkillDef',
            # To be filled out once all file ids have been collected
            'passive_item': asset['passiveItem']['m_PathID'],
        })
        return data


class RailgunSkillDef(SkillDef):
    SCRIPT = -8442111192690701832

    @staticmethod
    def parse(asset):
        data = super(RailgunSkillDef, RailgunSkillDef).parse(asset)
        data.update({'class': 'RailgunSkillDef'})
        return data

    
class ReloadSkillDef(SkillDef):
    SCRIPT = 6857858682788383752

    @staticmethod
    def parse(asset):
        data = super(ReloadSkillDef, ReloadSkillDef).parse(asset)
        data.update({
            'class': 'ReloadSkillDef',
            'grace_duration': round_value(asset['graceDuration']),
            })
        return data


class SteppedSkillDef(SkillDef):
    SCRIPT = -5073821918752729770

    @staticmethod
    def parse(asset):
        data = super(SteppedSkillDef, SteppedSkillDef).parse(asset)
        data.update({
            'class': 'SteppedSkillDef',
            'step_count': asset['stepCount'],
            'step_grace_duration': asset['stepGraceDuration'],
        })
        return data


class ToolbotWeaponSkillDef(SkillDef):
    SCRIPT = -3469430727944110720

    @staticmethod
    def parse(asset):
        data = super(ToolbotWeaponSkillDef, ToolbotWeaponSkillDef).parse(asset)
        data.update({'class': 'ToolbotWeaponSkillDef'})
        return data


class VoidRaidCrabBodySkillDef(SkillDef):
    SCRIPT = -909698154011760121

    @staticmethod
    def parse(asset):
        data = super(VoidRaidCrabBodySkillDef, VoidRaidCrabBodySkillDef).parse(asset)
        data.update({'class': 'VoidRaidCrabBodySkillDef'})
        return data


class VoidRaidCrabWeaponSkillDef(SkillDef):
    SCRIPT = None

    @staticmethod
    def parse(asset):
        data = super(VoidRaidCrabWeaponSkillDef, VoidRaidCrabWeaponSkillDef).parse(asset)
        data.update({'class': 'VoidRaidCrabWeaponSkillDef'})
        return data


class VoidSurvivorBlasterSkillDef(SteppedSkillDef):
    SCRIPT = None

    @staticmethod
    def parse(asset):
        data = super(VoidSurvivorBlasterSkillDef, VoidSurvivorBlasterSkillDef).parse(asset)
        data.update({'class': 'VoidSurvivorBlasterSkillDef'})
        return data


class VoidSurvivorSkillDef(SkillDef):
    SCRIPT = -3301321226602919904

    @staticmethod
    def parse(asset):
        data = super(VoidSurvivorSkillDef, VoidSurvivorSkillDef).parse(asset)
        data.update({
            'class': 'VoidSurvivorSkillDef',
            'min_corruption': asset['minimumCorruption'],
            'max_corruption': asset['maximumCorruption'],
        })
        return data
