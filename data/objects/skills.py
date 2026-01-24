from ._utils import round_value


class SkillDef:
    SCRIPT = 2927579589029976309

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
            'scales_with_attack_speed': bool(asset['attackSpeedBuffsRestockSpeed']),
            'attack_speed_scaling': round_value(asset['attackSpeedBuffsRestockSpeed_Multiplier']),
        }


class CaptainOrbitalSkillDef(SkillDef):
    SCRIPT = -2673451021167082982

    @staticmethod
    def parse(asset):
        data = super(CaptainOrbitalSkillDef, CaptainOrbitalSkillDef).parse(asset)
        data.update({'class': 'CaptainOrbitalSkillDef'})
        return data


class CaptainSupplyDropSkillDef(CaptainOrbitalSkillDef):
    SCRIPT = 4401919094338014678

    @staticmethod
    def parse(asset):
        data = super(CaptainSupplyDropSkillDef, CaptainSupplyDropSkillDef).parse(asset)
        data.update({'class': 'CaptainSupplyDropSkillDef'})
        return data


class ChefOilSpillSkillDef(SkillDef):
    SCRIPT = -2600163013373336914

    @staticmethod
    def parse(asset):
        data = super(ChefOilSpillSkillDef, ChefOilSpillSkillDef).parse(asset)
        data.update({'class': 'ChefOilSpillSkillDef'})
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


class DrifterSkillDef(SkillDef):
    SCRIPT = -1725364921308895059

    @staticmethod
    def parse(asset):
        data = super(DrifterSkillDef, DrifterSkillDef).parse(asset)
        data.update({'class': 'DrifterSkillDef'})
        return data


class DrifterTrackingSkillDef(SkillDef):
    SCRIPT = 6499377863185516973

    @staticmethod
    def parse(asset):
        data = super(DrifterTrackingSkillDef, DrifterTrackingSkillDef).parse(asset)
        data.update({'class': 'DrifterTrackingSkillDef'})
        return data


class DroneTechDroneSkillDef(SkillDef):
    SCRIPT = -5273846027766992056

    @staticmethod
    def parse(asset):
        data = super(DroneTechDroneSkillDef, DroneTechDroneSkillDef).parse(asset)
        data.update({'class': 'DroneTechDroneSkillDef'})
        return data


class DroneTechTrackingSkillDef(SkillDef):
    SCRIPT = None

    @staticmethod
    def parse(asset):
        data = super(DroneTechTrackingSkillDef, DroneTechTrackingSkillDef).parse(asset)
        data.update({'class': 'DroneTechTrackingSkillDef'})
        return data


class EngiMineDeployerSkillDef(SkillDef):
    SCRIPT = -6723418498616801824

    @staticmethod
    def parse(asset):
        data = super(EngiMineDeployerSkillDef, EngiMineDeployerSkillDef).parse(asset)
        data.update({'class': 'EngiMineDeployerSkillDef'})
        return data


class EnsureDroneMasterSkillDef(SkillDef):
    SCRIPT = -2680229100660702278

    @staticmethod
    def parse(asset):
        data = super(EnsureDroneMasterSkillDef, EnsureDroneMasterSkillDef).parse(asset)
        data.update({'class': 'EnsureDroneMasterSkillDef'})
        return data


class GroundedSkillDef(SkillDef):
    SCRIPT = -8460994096625872245

    @staticmethod
    def parse(asset):
        data = super(GroundedSkillDef, GroundedSkillDef).parse(asset)
        data.update({'class': 'GroundedSkillDef'})
        return data


class HuntressTrackingSkillDef(SkillDef):
    SCRIPT = 8672060334066177547

    @staticmethod
    def parse(asset):
        data = super(HuntressTrackingSkillDef, HuntressTrackingSkillDef).parse(asset)
        data.update({'class': 'HuntressTrackingSkillDef'})
        return data


class LunarDetonatorSkill(SkillDef):
    SCRIPT = 3569604752828954706

    @staticmethod
    def parse(asset):
        data = super(LunarDetonatorSkill, LunarDetonatorSkill).parse(asset)
        data.update({'class': 'LunarDetonatorSkill'})
        return data


class LunarPrimaryReplacementSkill(SkillDef):
    SCRIPT = -4480967723486249262

    @staticmethod
    def parse(asset):
        data = super(LunarPrimaryReplacementSkill, LunarPrimaryReplacementSkill).parse(asset)
        data.update({'class': 'LunarPrimaryReplacementSkill'})
        return data


class LunarSecondaryReplacementSkill(SkillDef):
    SCRIPT = 6740114260963895876

    @staticmethod
    def parse(asset):
        data = super(LunarSecondaryReplacementSkill, LunarSecondaryReplacementSkill).parse(asset)
        data.update({'class': 'LunarSecondaryReplacementSkill'})
        return data


class MasterSpawnSlotSkillDef(SkillDef):
    SCRIPT = -3004543828381520369

    @staticmethod
    def parse(asset):
        data = super(MasterSpawnSlotSkillDef, MasterSpawnSlotSkillDef).parse(asset)
        data.update({'class': 'MasterSpawnSlotSkillDef'})
        return data


class MercDashSkillDef(SkillDef):
    SCRIPT = 1650509664295044365

    @staticmethod
    def parse(asset):
        data = super(MercDashSkillDef, MercDashSkillDef).parse(asset)
        data.update({
            'class': 'MercDashSkillDef',
            'max_dashes': asset['maxDashes'],
            'timeout': round_value(asset['timeoutDuration']),
        })
        return data


class NoRechargeSkillDef(SkillDef):
    SCRIPT = None

    @staticmethod
    def parse(asset):
        data = super(NoRechargeSkillDef, NoRechargeSkillDef).parse(asset)
        data.update({'class': 'NoRechargeSkillDef'})
        return data


class PassiveItemSkillDef(SkillDef):
    SCRIPT = 1540930104905984482

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
    SCRIPT = 7296964618599511131

    @staticmethod
    def parse(asset):
        data = super(RailgunSkillDef, RailgunSkillDef).parse(asset)
        data.update({'class': 'RailgunSkillDef'})
        return data

    
class ReloadSkillDef(SkillDef):
    SCRIPT = -9080018864626768989

    @staticmethod
    def parse(asset):
        data = super(ReloadSkillDef, ReloadSkillDef).parse(asset)
        data.update({
            'class': 'ReloadSkillDef',
            'grace_duration': round_value(asset['graceDuration']),
            })
        return data


class ReusableSkillDef(SkillDef):
    SCRIPT = None

    @staticmethod
    def parse(asset):
        data = super(ReusableSkillDef, ReusableSkillDef).parse(asset)
        data.update({'class': 'ReusableSkillDef'})
        return data


class SeekerWeaponSkillDef(SkillDef):
    SCRIPT = 7949365122622623176

    @staticmethod
    def parse(asset):
        data = super(SeekerWeaponSkillDef, SeekerWeaponSkillDef).parse(asset)
        data.update({'class': 'SeekerWeaponSkillDef'})
        return data


class SolusHeartComboSkillDef(SkillDef):
    SCRIPT = 8666446819309190569

    @staticmethod
    def parse(asset):
        data = super(SolusHeartComboSkillDef, SolusHeartComboSkillDef).parse(asset)
        data.update({'class': 'SolusHeartComboSkillDef'})
        return data


class SolusHeartTeleportSkillDef(SkillDef):
    SCRIPT = 8229852426038494749

    @staticmethod
    def parse(asset):
        data = super(SolusHeartTeleportSkillDef, SolusHeartTeleportSkillDef).parse(asset)
        data.update({'class': 'SolusHeartTeleportSkillDef'})
        return data


class SolusWingLaserGridSkillDef(SkillDef):
    SCRIPT = 6166010912192768675

    @staticmethod
    def parse(asset):
        data = super(SolusWingLaserGridSkillDef, SolusWingLaserGridSkillDef).parse(asset)
        data.update({'class': 'SolusWingLaserGridSkillDef'})
        return data


class SteppedSkillDef(SkillDef):
    SCRIPT = 2654350612606756206

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
    SCRIPT = -6630013004447834050

    @staticmethod
    def parse(asset):
        data = super(ToolbotWeaponSkillDef, ToolbotWeaponSkillDef).parse(asset)
        data.update({'class': 'ToolbotWeaponSkillDef'})
        return data


class TrackingSkillDef(SkillDef):
    SCRIPT = -2067494168930530403

    @staticmethod
    def parse(asset):
        data = super(TrackingSkillDef, TrackingSkillDef).parse(asset)
        data.update({'class': 'TrackingSkillDef'})
        return data


class VoidRaidCrabBodySkillDef(SkillDef):
    SCRIPT = -1032510644754718512

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
    SCRIPT = -8428730001527203593

    @staticmethod
    def parse(asset):
        data = super(VoidSurvivorSkillDef, VoidSurvivorSkillDef).parse(asset)
        data.update({
            'class': 'VoidSurvivorSkillDef',
            'min_corruption': asset['minimumCorruption'],
            'max_corruption': asset['maximumCorruption'],
        })
        return data


ALL_SKILL_DEFS = (
    SkillDef,
    CaptainOrbitalSkillDef,
    CaptainSupplyDropSkillDef,
    ChefOilSpillSkillDef,
    ComboSkillDef,
    ConditionalSkillDef,
    DrifterSkillDef,
    DrifterTrackingSkillDef,
    DroneTechDroneSkillDef,
    DroneTechTrackingSkillDef,
    EngiMineDeployerSkillDef,
    EnsureDroneMasterSkillDef,
    GroundedSkillDef,
    HuntressTrackingSkillDef,
    LunarDetonatorSkill,
    LunarPrimaryReplacementSkill,
    LunarSecondaryReplacementSkill,
    MasterSpawnSlotSkillDef,
    MercDashSkillDef,
    NoRechargeSkillDef,
    PassiveItemSkillDef,
    RailgunSkillDef,
    ReloadSkillDef,
    ReusableSkillDef,
    SeekerWeaponSkillDef,
    SolusHeartComboSkillDef,
    SolusHeartTeleportSkillDef,
    SolusWingLaserGridSkillDef,
    SteppedSkillDef,
    ToolbotWeaponSkillDef,
    TrackingSkillDef,
    VoidRaidCrabWeaponSkillDef,
    VoidRaidCrabBodySkillDef,
    VoidSurvivorSkillDef,
)
