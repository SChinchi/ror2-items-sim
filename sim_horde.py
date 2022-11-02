import math

from data_loader import dccs, scenes


IS_HONOR_ENABLED = False
ELITE_COST_MULTIPLIER = 6
HONOR_COST_MULTIPLIER = 3.5
MAX_SPAWNS = 6


class Endpoint:
    """Data class for interval endpoints."""
    TRANSITIONS = {')': '[', ']': '(', '(': ']', '[': ')'}

    def __init__(self, value, boundary):
        """
        Create an endpoint.

        Parameters
        ----------
        value : float
            The value at the endpoint.
        boundary : {')', ']', '(', '[}
            The boundary type, i.e., open or closed.

        Raises
        ------
        ValueError
            If `boundary` is not one of the excepted choices.
        """
        if boundary not in Endpoint.TRANSITIONS:
            raise ValueError(f'Unknown boundary type. Must be one of {list(Endpoint.TRANSITIONS)}.')
        self.value = value
        self.boundary = boundary
        self.direction = 1 if boundary in ('(', '[') else -1

    def __repr__(self):
        if self.direction > 0:
            return f'{self.boundary}{self.value}'
        return f'{self.value}{self.boundary}'

    def get_complementary_endpoint(self):
        """Returns the complementary boundary, e.g open right to closed left."""
        return Endpoint(self.value, Endpoint.TRANSITIONS[self.boundary])


class Interval:
    """Data class for arithmetic intervals."""
    def __init__(self, lower, upper):
        """
        Create an interval.

        Parameters
        ----------
        lower, upper : Endpoint
            The lower and upper value endpoints.

        Raises
        ------
        ValueError
            The lower endpoint must be a left one and the right endpoint must be
            a right one. The lower endpoint must also be lower than the upper.
        """
        if lower.value > upper.value or lower.direction < 0 or upper.direction > 0:
            raise ValueError('The endpoints "{lower}" and "{upper}" do not create a valid interval.')
        self.lower = lower
        self.upper = upper

    def __repr__(self):
        return f'{repr(self.lower)}, {repr(self.upper)}'

    def overlaps(self, interval):
        """Check if an interval overlaps with another."""
        l0 = self.lower.value
        u0 = self.upper.value
        l1 = interval.lower.value
        u1 = interval.upper.value
        if l1 < l0 and u0 < u1:
            return True
        if l0 <= l1 <= u0 or l0 <= u1 <= u0:
            if u0 == l1 and (self.upper.boundary == ')' or interval.lower.boundary == '('):
                return False
            elif l0 == u1 and (self.lower.boundary == '(' or interval.upper.boundary == ')'):
                return False
            return True
        return False


class EliteTierDef:
    """Elite Tier data class as defined in `RoR2.CombatDirector`."""
    def __init__(self, multiplier, types, is_available, can_select_default):
        self.multiplier = multiplier
        self.types = types
        self.is_available = is_available
        self.can_select_default = can_select_default

    def can_select(self, rules, stages_cleared):
        return self.is_available(rules, stages_cleared) and (self.can_select_default or self.types)


# As defined in `RoR2.CombatDirector.Init`.
elite_tiers = (
    EliteTierDef(
        1,
        [''],
        lambda rules, stages_cleared: not IS_HONOR_ENABLED,
        True,
    ),
    EliteTierDef(
        ELITE_COST_MULTIPLIER,
        ['Lightning', 'Ice', 'Fire', 'Earth'],
        lambda rules, stages_cleared: not IS_HONOR_ENABLED and rules == 0,
        False,
    ),
    EliteTierDef(
        HONOR_COST_MULTIPLIER,
        ['LightningHonor', 'IceHonor', 'FireHonor', 'EarthHonor'],
        lambda rules, stages_cleared: IS_HONOR_ENABLED,
        False,
    ),
    EliteTierDef(
        ELITE_COST_MULTIPLIER * 6,
        ['Poison', 'Haunted'],
        lambda rules, stages_cleared: stages_cleared >= 5 and rules == 0,
        False,
    ),
    EliteTierDef(
        ELITE_COST_MULTIPLIER,
        ['Lunar'],
        lambda rules, stages_cleared: rules == 2,
        False,
    ),
)


def compute_horde_chance(scene_name, stages_cleared, num_players=1, is_dlc_enabled=True):
    """
    Compute the Horde of Many (HoM) chance for the Teleporter Boss.

    Parameters
    ----------
    scene_name : str
        The internal name of the scene. This will use the default monster pool,
         as any Family Events always have either 0% or 100% chance.
    stages_cleared : int
        The number of cleared stages. This affects which monsters and elite
        tiers will be available for selection.
    num_players : int, optional
        The number of players. This only affects the maximum time a credit
        threshold will not be crossed.
    is_dlc_enabled : bool, optional
        The monster pool is different between the vanilla and DLC versions of
        the game. By default the DLC is enabled.

    Returns
    -------
    combined_intervals : list
        A list of lists, where each sublist contains a credit interval, the HoM
        chance related to that interval, and the times for which this credit
        interval will not be exceeded by activating 0-3 Shrines of the Mountain.
        The time shown may be too low a number to reach normally, but it is
        possible with speedrunning or by using mods to skip to any stage.
    """
    if scenes[scene_name].required_dlc and not is_dlc_enabled:
        raise ValueError('The selected scene requires the DLC to be enabled.')
    stage_info = scenes[scene_name].stage_info
    if not stage_info:
        raise ValueError('There is no DCCS related to this scene.')
    dccs_category = stage_info.monsters.categories[0]
    if is_dlc_enabled:
        selected_dccs = dccs_category.included_conditions_met[0].dccs
    else:
        selected_dccs = dccs_category.included_conditions_not_met[0].dccs
            
    monsters = selected_dccs.generate_card_weighted_selection(stages_cleared, False)
    monsters = dict([(m[0].spawn_card, m[1]) for m in monsters])
    credit_thresholds = {}
    for card, weight in monsters.items():
        min_value = card.cost
        max_value = min_value
        if not card.no_elites:
            for tier in elite_tiers:
                if tier.can_select(card.elite_rules, stages_cleared):
                    max_value = max(max_value, min_value * tier.multiplier)
        max_value *= MAX_SPAWNS
        credit_thresholds[card] = (
            Interval(Endpoint(min_value, '['), Endpoint(max_value, ']')), weight,
        )
    most_expensive = max(interval.upper.value for interval, _ in credit_thresholds.values())
    
    boss_cards = []
    for card in monsters.keys():
        if card.body.is_champion and not card.forbidden_as_boss:
            boss_cards.append(card)
    boss_thresholds = set([(600, ')')])
    for card in boss_cards:
        interval, _ = credit_thresholds[card]
        boss_thresholds.add((interval.lower.value, ')'))
        boss_thresholds.add((interval.upper.value, '('))
    boss_thresholds.add((most_expensive, '('))
    boss_thresholds = [Endpoint(val, boundary) for val, boundary in sorted(boss_thresholds)]

    intervals = []
    for previous, current in zip(boss_thresholds[:-1], boss_thresholds[1:]):
        if previous.direction < 0:
            previous = previous.get_complementary_endpoint()
            if current.direction < 0:
                intervals.extend(_reroll(boss_cards, credit_thresholds, previous, current))
            else:
                current = current.get_complementary_endpoint()
                intervals.append((Interval(previous, current), .0))
        else:
            if current.direction > 0:
                current = current.get_complementary_endpoint()
            intervals.extend(_reroll(boss_cards, credit_thresholds, previous, current))
    # Past the most expensive spawn card, Horde of Many will either never or
    # always occur, depending on whether the most expensive card is a Champion.
    for spawn_card, (interval, _) in credit_thresholds.items():
        if interval.upper.value == most_expensive:
            next_endpoint = Endpoint(most_expensive, '(')
            chance = .0 if spawn_card.body.is_champion and not spawn_card.forbidden_as_boss else 1.
            intervals.append((Interval(next_endpoint, Endpoint(math.inf, ')')), chance))
            break

    combined_intervals = []
    interval = intervals[0]
    for i in range(1, len(intervals)):
        if intervals[i][1] == interval[1]:
            interval[0].upper = intervals[i][0].upper
        else:
            threshold = interval[0].upper.value
            combined_intervals.append(interval + (get_time(threshold, stages_cleared, num_players),))
            interval = intervals[i]
    combined_intervals.append(interval + ([],))
    return combined_intervals


def _reroll(boss_cards, credit_thresholds, lower, upper):
    total = failed = .0
    reroll_interval = Interval(lower, upper)
    for spawn_card in boss_cards:
        card_interval, weight = credit_thresholds[spawn_card]
        total += weight
        if not reroll_interval.overlaps(card_interval):
            failed += weight
    reroll_chance = failed / total
    if not reroll_chance:
        return [reroll_interval, .0]
    
    internal_thresholds = set()
    for interval, weight in credit_thresholds.values():
        max_cost = interval.upper.value
        if lower.value < max_cost < upper.value:
            internal_thresholds.add(max_cost)
    internal_thresholds.add(upper.value)
    internal_thresholds = sorted(internal_thresholds)
    intervals = []
    lower_threshold = lower.value
    for upper_threshold in internal_thresholds:
        if lower_threshold == lower.value:
            current_lower = lower
        else:
            current_lower = Endpoint(lower_threshold, '(')
        if upper_threshold == upper.value:
            current_upper = upper
        else:
            current_upper = Endpoint(upper_threshold, ']')
        interval = Interval(current_lower, current_upper)
        intervals.append(
            (interval, _calc_horde_reroll_chance(credit_thresholds, interval, reroll_chance))
        )
        lower_threshold = upper_threshold
    return intervals


def _calc_horde_reroll_chance(credit_thresholds, credit_interval, reroll_chance):
    total = failed = .0
    for spawn_card, (interval, weight) in credit_thresholds.items():
        if credit_interval.overlaps(interval):
            total += weight
            if not spawn_card.body.is_champion or spawn_card.forbidden_as_boss:
                failed += weight
    return reroll_chance * (failed / total)


def get_time(monster_credits, stages_cleared, num_players):
    """
    Calculate when the Teleporter Boss Director has certain amount of credits.

    The time is measured in minutes rounded down as the next minute the Director
    would exceed the input amount of credits.

    It returns four possible times, for activating 0-4 Shrines of the Mountain
    respectively. If a time is negative, it will be None.
    """
    return [solve_coeff((monster_credits / (600 * (1 + mountain)))**2, stages_cleared, num_players)
            for mountain in range(4)]


def solve_coeff(coeff, stages_cleared, num_players=1, difficulty=3):
    """
    Calculate the time for difficulty coefficient to have a certain value.

    The time is in minutes and rounded down, as the next minute exceeds the
    input coefficient value.

    Parameters
    ----------
    coeff : float
        The difficulty coefficient value.
    stages_cleared : int
        The number of stages cleared.
    num_players : int
        The number of players.
    difficulty : int, optional
        The difficulty of the current run. 1 for Drizzle, 2 for Rainstorm, and
        3 for Monsoon. Monsoon is selected by default.

    Returns
    -------
    int, None
        The rounded down time in minutes. If the result is negative, it will
        return None.
    """
    player_factor = 1 + .3 * (num_players - 1)
    time_factor = .0506 * difficulty * num_players**.2
    stage_factor = 1.15**stages_cleared
    time = ((coeff / stage_factor) - player_factor) / time_factor
    return int(math.floor(time)) if time >= 0 else None
