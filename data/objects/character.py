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


class BaseAI:
    SCRIPT = 8404199760932312366

    @staticmethod
    def parse(asset, ids):
        esm_id = asset['stateMachine']['m_PathID']
        esm = ids[esm_id] if esm_id else None
        return {
            'full_vision': bool(asset['fullVision']),
            'no_friendly_fire': bool(asset['neverRetaliateFriendlies']),
            'enemy_attention': asset['enemyAttentionDuration'],
            'initial_state': esm['initialStateType']['_typeName'] if esm else None,
            'main_state': esm['mainStateType']['_typeName'] if esm else None,
        }


class AISkillDriver:
    SCRIPT = -945280087658747711

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.name

    @staticmethod
    def parse(asset):
        return {
            'name': asset['customName'],
            'skill_slot': asset['skillSlot'],
            # To be filled out once all file ids have been collected
            'required_skill': asset['requiredSkill']['m_PathID'],
            'requires_skill_ready': bool(asset['requireSkillReady']),
            'requires_equipment_ready': bool(asset['requireEquipmentReady']),
            'user_hp_range': (round_value(asset['maxUserHealthFraction']),
                              round_value(asset['minUserHealthFraction'])),
            'target_hp_range': (round_value(asset['maxTargetHealthFraction']),
                                round_value(asset['minTargetHealthFraction'])),
            'distance_range': (round_value(asset['minDistance']),
                               round_value(asset['maxDistance'])),
            'require_target_los': bool(asset['selectionRequiresTargetLoS']),
            'require_target_aim': bool(asset['selectionRequiresAimTarget']),
            'require_grounded': bool(asset['selectionRequiresOnGround']),
            'max_times_selected': asset['maxTimesSelected'],
            'move_type': asset['movementType'],
            'target_type': asset['moveTargetType'],
            'aim_type': asset['aimType'],
            'should_sprint': bool(asset['shouldSprint']),
            'should_fire_equipment': bool(asset['shouldFireEquipment']),
            'reset_enemy': bool(asset['resetCurrentEnemyOnNextDriverSelection']),
            'no_repeat': bool(asset['noRepeat']),
            # To be filled out once all file ids have been collected
            'next_high_priority': asset['nextHighPriorityOverride']['m_PathID'],
        }
