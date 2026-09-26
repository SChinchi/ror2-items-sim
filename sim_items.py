import numpy as np

from constants import SceneName, Expansion, ALL_EXPANSIONS, NO_EXPANSIONS
from run import Run


def _print_results(data, headers, fmt):
    """
    Tabulate data from a list of lists.

    Parameters
    ----------
    data : list of lists
        The rows for the table.
    headers : list
        The column names.
    fmt : list
        The format to use for each column. It should have the same size as
        `headers`. For each column the information is packed in a tuple of
        (alignment, length, type), where alignment can be {'', '<', '^', '>'},
        length is the length of the column and type can be {str, int, float}.
        If the type is float, length is a tuple of (total length, fractional).

    Returns
    -------
    None
    """
    header_fmt = {}
    table_fmt = {}
    for f in fmt:
        if f not in header_fmt:
            align, length, ftype = f
            if ftype == float:
                length = length[0]
            this_fmt = '{:' + f'{align}{length}s' + '}'
            header_fmt[f] = this_fmt
        if f not in table_fmt:
            align, length, ftype = f
            if ftype == str:
                ftype = 's'
            elif ftype == int:
                ftype = 'd'
            elif ftype == float:
                length = '{}.{}'.format(*length)
                ftype = 'f'
            else:
                raise ValueError('Unknown value type')
            this_fmt = '{:' + f'{align}{length}{ftype}' + '}'
            table_fmt[f] = this_fmt
    header = '|'.join(header_fmt[f].format(name) for f, name in zip(fmt, headers))
    header_separator = ''.join('-' if c != '|' else '+' for c in header)
    print(header)
    print(header_separator)
    for entry in data.items():
        if isinstance(entry[1], (list, np.ndarray)):
            entry = [entry[0], *entry[1]]
        row = '|'.join(table_fmt[f].format(e) for f, e in zip(fmt, entry))
        print(row)


def simulate_run(stages, void_fields=-1, num_players=1, iterations=40000, is_delusion_enabled=False):
    """
    Print a table with the number of items per tier that can be found in a run.

    There is a further breakdown for runs where the Executive Card was found on
    any stage number.

    The 'TOTAL' column is the sum of items excluding any equipment encountered.

    Parameters
    ----------
    stages : int
        The number of normal stages to loot. This checks when `stages_cleared`
        in the `Run` has reached the desired number. If any intermission
        stages are done in the between, a run can visit more environments than
        the number here states.
    void_fields : int, optional
        After which normal stage to visit and completely loot the Void Fields.
        If it is not a positive integer, it will not be visited. This is the
        default behaviour.
    num_players : int, optional
        The number of players in the run.
    iterations : int, optional
        The number of iterations to run statistics for. The default value has
        been chosen so that there is minimal variation in the output. A lower
        value may hurt the results, but may be necessary to reduce the
        computation time if `stage` is large enough.
    is_delusion_enabled : bool, optional
        Whether the Artifact of Delusion is enabled. This can heavily affect the
        accumulated loot.

    Returns
    -------
    None
    """
    expansions = ALL_EXPANSIONS
    NO_CARD = '-'
    VOID_FIELDS = 'V FIELDS'

    # Dictionary counters
    stage_names = list(map(str, range(1, stages+1)))
    delusion_extra = {name: [0] * 4 for name in stage_names}
    delusion_extra['TOTAL'] = [0] * 4
    if Expansion.SOTV in expansions:
        if void_fields > 0:
            stage_names.insert(void_fields, VOID_FIELDS)
        tiers = {name: [] for name in stage_names}
    else:
        tiers = {}
    tiers[NO_CARD] = []

    # Collect data
    run = Run(num_players=num_players, expansions=expansions,
              is_delusion_enabled=is_delusion_enabled)
    total = {key: 0 for key in run.stats.consolidate_data()['total']}
    for _ in range(iterations):
        run.loot_stages(stages, void_fields)
        data = run.stats.consolidate_data()
        for key, value in data['total'].items():
            total[key] += value / iterations
        card_stage = data['card']['stage']
        card_stage = str(card_stage + 1) if card_stage >= 0 else NO_CARD
        if data['card']['name'] == SceneName.VF:
            card_stage = VOID_FIELDS
        tiers[card_stage].append(data['tiers'])
        for j in range(len(data['delusion_bonus'])):
            stage_name = str(j+1)
            for k in range(3):
                delusion_extra[stage_name][k] += data['delusion_bonus'][j][k] / iterations
            delusion_extra[stage_name][-1] = sum(delusion_extra[stage_name][:-1])

    # Item tier data
    num_tiers = len(Run.build_tier_droplists())
    for key, values in tiers.items():
        iters = len(values)
        values = np.mean(values, axis=0) if values else np.zeros(num_tiers)
        # Remove the 'Lunar Combined' tier
        values = np.delete(values, 6)
        # Not counting equipment for the total
        total_value = values.sum() - (values[4] + values[6])
        tiers[key] = [*values, total_value, iters]
    tier_names = (
        'T1', 'T2', 'T3', 'BOSS', 'L EQ', 'L ITEM', 'EQ', 'V T1', 'V T2', 'V T3', 'V BOSS', 'TOTAL',
    )
    tier_fmt = [('^', (6, 2), float)] * len(tier_names)
    # The Void Boss tier occurs so rarely that we need higher decimal precision
    tier_fmt[-2] = ('^', (6, 4), float)
    _print_results(tiers, ('CARD', *tier_names, 'ITERS'), [('<', 9, str), *tier_fmt, ('>', 6, int)])
    print()

    # Delusion item tier data
    if is_delusion_enabled:
        print('The Artifact of Delusion contributed this many items in the tally above.\n')
        delusion_extra['TOTAL'] = np.array(tuple(delusion_extra.values())).sum(axis=0)
        col_fmt = ('^', (9, 2), float)
        _print_results(
            delusion_extra,
            ('STAGE', 'T1', 'T2', 'T3', 'TOTAL'),
            [('<', 9, str), col_fmt, col_fmt, col_fmt, col_fmt]
        )
        print()

    # Other trackers
    col_fmt = ('>', (10, 2), float)
    _print_results(total, ('STAT', 'AVERAGE'), [('<', 20, str), col_fmt])
