import numpy as np

from constants import ALL_EXPANSIONS, NO_EXPANSIONS
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
    for entries in data:
        row = '|'.join(table_fmt[f].format(entry) for f, entry in zip(fmt, entries))
        print(row)


def simulate_run(stages, void_fields=-1, num_players=1, iterations=40000, is_delusion_enabled=False):
    """
    Print a table with the number of items per tier that can be found in a run.

    This compares stats from having the DLC enabled and finding an Executive
    Card on any or no stage against the DLC disabled.

    The 'TOTAL' column is the sum of items excluding any equipment encountered.

    Parameters
    ----------
    stages : int
        The number of normal stages to loot.
    void_fields : int, optional
        After which normal stage to visit and completely loot the Void Fields.
        If it is not a positive integer, it will not be visited. This is the
        default behaviour.
    num_players : int, optional
        The number of players in the run.
    iterations : int, optional
        The number of iterations to run statistics for. For the DLC, this number
        will be split among any stage categories, representing on which stage
        the Executive Card was found. The default value has been chosen so that
        there is minimal variation in the output. A lower value may hurt the
        results, but may be necessary to reduce the computation time if `stage`
        is large enough.
    is_delusion_enabled : bool, optional
        Whether the Artifact of Delusion is enabled. This can heavily affect the
        accumulated loot.

    Returns
    -------
    None
    """
    NO_CARD = '-'
    NO_DLC = 'NO DLC'
    tiers = {str(i): [] for i in range(1, stages+1+(void_fields>0))}
    delusion_extra = {i: [0] * 6 for i in tiers.keys()}
    tiers[NO_CARD] = []
    tiers[NO_DLC] = []
    r_dlc = Run(num_players=num_players, expansions=ALL_EXPANSIONS,
                is_delusion_enabled=is_delusion_enabled)
    r_no_dlc = Run(num_players=num_players, expansions=NO_EXPANSIONS,
                   is_delusion_enabled=is_delusion_enabled)
    total = {key: [.0, .0] for key in r_dlc.stats.consolidate_data()['total']}
    for _ in range(iterations):
        for i, r in enumerate((r_dlc, r_no_dlc)):
            r.loot_stages(stages, void_fields)
            data = r.stats.consolidate_data()
            for key, value in data['total'].items():
                total[key][i] += value / iterations
            if r == r_dlc:
                card = data['card']['stage']
                card = str(card + 1) if card >= 0 else NO_CARD
            else:
                card = NO_DLC
            offset = 0 if r == r_dlc else 3
            for j in range(len(data['delusion_bonus'])):
                for k in range(3):
                    delusion_extra[str(j+1)][offset+k] += data['delusion_bonus'][j][k] / iterations
            tiers[card].append(data['tiers'])
    num_tiers = len(Run.build_tier_droplists())
    for key, values in tiers.items():
        iters = len(values)
        values = np.mean(values, axis=0) if values else np.zeros(num_tiers)
        # Remove the 'Lunar Combined' tier
        values = np.delete(values, 6)
        # Not counting equipment for the total
        total_value = values.sum() - (values[4] + values[6])
        tiers[key] = [*values, total_value, iters]
    total = [[key, *values] for key, values in total.items()]
    tiers = [[key, *values] for key, values in tiers.items()]
    delusion_extra['TOTAL'] = np.array(tuple(delusion_extra.values())).sum(axis=0)
    delusion_extra = [[key, *values] for key, values in delusion_extra.items()]

    tier_names = (
        'T1', 'T2', 'T3', 'BOSS', 'L EQ', 'L ITEM', 'EQ', 'V T1', 'V T2', 'V T3', 'V BOSS', 'TOTAL',
    )
    tier_fmt = [('^', (6, 2), float)] * len(tier_names)
    # The Void Boss tier occurs so rarely that we need higher decimal precision
    tier_fmt[-2] = ('^', (6, 4), float)
    _print_results(tiers, ('CARD', *tier_names, 'ITERS'), [('<', 6, str), *tier_fmt, ('>', 6, int)])
    print()
    if is_delusion_enabled:
        col_fmt = ('^', (9, 2), float)
        _print_results(
            delusion_extra,
            ('STAGE', 'DLC T1', 'DLC T2', 'DLC T3', 'NO DLC T1', 'NO DLC T2', 'NO DLC T3'),
            [('<', 7, str), col_fmt, col_fmt, col_fmt, col_fmt, col_fmt, col_fmt]
        )
        print()
    col_fmt = ('^', (10, 2), float)
    _print_results(total, ('ENCOUNTERED', 'DLC', 'NO DLC'), [('<', 20, str), col_fmt, col_fmt])
