import random

from ._utils import round_value


class Category:
    def __init__(self, name, weight, cards):
        self.name = name
        self.weight = weight
        self.cards = cards

    def __repr__(self):
        return self.name


class DirectorCardCategorySelection:
    SCRIPT = -9065466171340090710

    def __init__(self, data=None):
        if data:
            for attr, value in data.items():
                setattr(self, attr, value)
            delattr(self, 'class')
        else:
            self.name = ''
            self.categories = []
        self.expansions_in_effect = set()
    
    def __repr__(self):
        return self.name

    @staticmethod
    def parse(asset):
        categories = []
        for category in asset['categories']:
            cards = []
            for card in category['cards']:
                cards.append({
                    # To be filled out once all file ids have been collected
                    'spawn_card': card['spawnCard']['m_PathID'],
                    'weight': round_value(card['selectionWeight']),
                    'min_stages_cleared': card['minimumStageCompletions'],
                })
            categories.append({
                'name': category['name'],
                'weight': round_value(category['selectionWeight']),
                'cards': cards,
            })
        return {
            'class': 'DirectorCardCategorySelection',
            'name': asset['m_Name'],
            'categories': categories,
        }

    def add_category(self, name, weight, cards):
        """
        Add a new category.

        Parameters
        ----------
        name : str
            Name of the category.
        weight : float
            Selection weight of the category.
        cards : list
            List of the director cards in the category.

        Returns
        -------
        None
        """
        self.categories.append(Category(name, weight, cards))

    def generate_card_weighted_selection(self, stages_cleared, expansions, is_sacrifice_enabled=False):
        """
        Generate all available interactable spawn cards for the scene.

        Parameters
        ----------
        stages_cleared : int
            The number of cleared stages, which affects which interactables
            will be available.
        expansions : set
            The currently enabled expansions, which can affect which
            interactables ill be available.
        is_sacrifice_enabled : bool, default False
            Whether the Artifact of Sacrifice is enabled. This can affect what
            interactables can spawn.

        Returns
        -------
        weighted_selections : list
            The list of available cards.

        Notes
        -----
        An implementation of
        `RoR2.DirectorCardCategorySelection.GenerateDirectorCardWeightedSelection`.
        """
        weighted_selections = []
        for category in self.categories:
            category_weight = category.weight
            cards = category.cards
            total_weight = sum(card.weight for card in cards
                               if card.is_available(stages_cleared, expansions))
            if total_weight > 0:
                modifier = category_weight / total_weight
                for card in cards:
                    if card.is_available(stages_cleared, expansions):
                        weight = card.weight * modifier
                        if is_sacrifice_enabled:
                            weight *= card.sacrifice_weight
                        weighted_selections.append((card, weight))
        return weighted_selections   

    def is_available(self, stages_cleared):
        """
        Whether this DCCS meets the requirements.

        Parameters
        ----------
        stages_cleared : int
            The number of stages cleared.

        Returns
        -------
        bool

        Notes
        -----
        An implementation of `RoR2.DirectorCardCategorySelection.IsAvailable`.
        """
        return True

    def get_category_index(self, name):
        """
        Find a category index by its name.

        Parameters
        ----------
        name : str
            The name of the category.

        Returns
        -------
        int

        Notes
        -----
        An implementation of
        `RoR2.DirectorCardCategorySelection.FindCategoryIndexByName`.
        """
        for i, category in enumerate(self.categories):
            if category.name == name:
                return i
        return -1


class FamilyDirectorCardCategorySelection(DirectorCardCategorySelection):
    SCRIPT = 9070779464185817160

    @staticmethod
    def parse(asset):
        data = super(FamilyDirectorCardCategorySelection, FamilyDirectorCardCategorySelection).parse(asset)
        data.update({
            'class': 'FamilyDirectorCardCategorySelection',
            'min_stages_cleared': asset['minimumStageCompletion'],
            'max_stages_cleared': asset['maximumStageCompletion'],
        })
        return data

    def is_available(self, stages_cleared):
        """
        Whether this DCCS meets the requirements.

        Parameters
        ----------
        stages_cleared : int
            The number of stages cleared.

        Returns
        -------
        bool

        Notes
        -----
        An implementation of `RoR2.FamilyDirectorCardCategorySelection.IsAvailable`.
        """
        return self.min_stages_cleared <= stages_cleared < self.max_stages_cleared


class ConditionalPoolEntry:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.dccs.name

    @staticmethod
    def parse(entry, ids):
        return {
            'dccs': ids[entry['dccs']['m_PathID']]['m_Name'],
            'weight': round_value(entry['weight']),
            'required_dlc': [ids[r['m_PathID']]['m_Name'] for r in entry['requiredExpansions']
                             if r['m_PathID']],
        }


class PoolEntry:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.dccs.name

    @staticmethod
    def parse(entry, ids):
        return {
            'dccs': ids[entry['dccs']['m_PathID']]['m_Name'],
            'weight': round_value(entry['weight']),
        }


class DccsCategory:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        self.always_included = [PoolEntry(dccs_data) for dccs_data in self.always_included]
        self.included_conditions_met = [ConditionalPoolEntry(dccs_data)
                                        for dccs_data in self.included_conditions_met]
        self.included_conditions_not_met = [PoolEntry(dccs_data)
                                            for dccs_data in self.included_conditions_not_met]

    def __repr__(self):
        return self.name

    @staticmethod
    def parse(category, ids):
        return {
            'name': category['name'],
            'weight': round_value(category['categoryWeight']),
            'always_included': [PoolEntry.parse(entry, ids) for entry in category['alwaysIncluded']],
            'included_conditions_met': [ConditionalPoolEntry.parse(entry, ids)
                                        for entry in category['includedIfConditionsMet']],
            'included_conditions_not_met': [PoolEntry.parse(entry, ids)
                                            for entry in category['includedIfNoConditionsMet']],
        }


class DccsPool:
    SCRIPT = 5634676413805604316
    
    def __init__(self, data):
        self.name = data['name']
        self.categories = [DccsCategory(category) for category in data['categories']]

    def __repr__(self):
        return self.name

    @staticmethod
    def parse(asset, ids):
        return {
            'name': asset['m_Name'],
            'categories': [DccsCategory.parse(category, ids) for category in asset['poolCategories']],
        }

    def generate_weighted_category_selection(self, expansions, stages_cleared):
        """
        Select a valid category from the pool.

        Parameters
        ----------
        expansions : set
            The expansions enabled, which affects which selections are available.
        stages_cleared : int
            The number of stages cleared, which also affects which selections
            are available.
            
        Returns
        -------
        weighted_selection : DccsPoolCategory
            The selected object.

        Notes
        -----
        An implementation of `RoR2.DccsPool.GenerateWeightedCategorySelection`.
        """
        values = []
        weights = []
        for category in self.categories:
            if self.category_has_necessary_expansion_or_default_content(category, expansions, stages_cleared):
                values.append(category)
                weights.append(category.weight)
        return random.choices(values, weights)[0]

    def category_has_necessary_expansion_or_default_content(self, category, expansions, stages_cleared):
        """
        Check whether the DccsPoolCategory is valid for selection.

        Parameters
        ----------
        category : DccsPoolCategory
            The selected category.
        expansions : set
            The expansions enabled, which affects which selections are available.
        stages_cleared : int
            The number of stages cleared, which also affects which selections
            are available.

        Returns
        -------
        bool

        Notes
        -----
        An implementation of `RoR2.DccsPool.CategoryHasNecessaryExpansionOrDefaultContent`.
        """
        if category.always_included:
            return True
        if category.included_conditions_not_met:
            return True
        for entry in category.included_conditions_met:
            if (entry.dccs.is_available(stages_cleared) and
                self.are_conditions_met(entry, expansions)):
                return True
        return False

    def are_conditions_met(self, entry, expansions):
        """
        Whether the pool entry's expansion is available.

        Parameters
        ----------
        entry : ConditionalPoolEntry
            The selected object.
        expansions : set
            The enabled expansions.

        Returns
        -------
        bool

        Notes
        -----
        An implementation of `RoR2.DccsPool.AreConditionsMet`.
        """
        return all(dlc in expansions for dlc in entry.required_dlc)

    def generate_weight_selection_from_single_category(self, category, expansions, stages_cleared):
        """
        Select a DCCS object from the available ones.

        Parameters
        ----------
        category : PoolEntry or ConditionalPoolEntry
            The selected DccsPool entry.
        expansions : set
            The expansions enabled, which affects which selections are available.
        stages_cleared : int
            The number of stages cleared, which also affects which selections
            are available.

        Returns
        -------
        DirectorCardCategorySelection

        Notes
        -----
        An implementation of `RoR2.DccsPool.GenerateWeightSelectionFromSingleCategory`.
        """
        values = []
        weights = []
        total_weight = 0
        for entry in category.always_included:
            if entry.dccs.is_available(stages_cleared):
                total_weight += entry.weight
        conditions_met = False
        for entry in category.included_conditions_met:
            if entry.dccs.is_available(stages_cleared) and self.are_conditions_met(entry, expansions):
                total_weight += entry.weight
                conditions_met = True
        if not conditions_met:
            for entry in category.included_conditions_not_met:
                if entry.dccs.is_available(stages_cleared):
                    total_weight += entry.weight
        if total_weight:
            modifier = category.weight / total_weight
            for entry in category.always_included:
                if entry.dccs.is_available(stages_cleared):
                    values.append(entry.dccs)
                    weights.append(entry.weight * modifier)
            conditions_met = False
            for entry in category.included_conditions_met:
                if entry.dccs.is_available(stages_cleared) and self.are_conditions_met(entry, expansions):
                    values.append(entry.dccs)
                    weights.append(entry.weight * modifier)
                    conditions_met = True
            if not conditions_met:
                for entry in category.included_conditions_not_met:
                    if entry.dccs.is_available(stages_cleared):
                        values.append(entry.dccs)
                        weights.append(entry.weight * modifier)
        return random.choices(values, weights)[0]


class DCCSBlender:
    CONTENT_MIX_LIMIT = 2

    def get_blended_dccs(dccs_category, expansions, stages_cleared, used_expansions=None):
        """
        Blend all available DCCS from the selected category in the DccsPool.

        Parameters
        ----------
        dccs_category : DccsCategory
            The selected DCCS category for the current pool.
        expansions
            The expansions enabled, which affects which selections are available.
        stages_cleared : int
            The number of stages cleared, which also affects which selections
            are available.
        used_expansions : list
            The list of expansions available to satisfy any DCCS requirements.

        Returns
        -------
        blended_dccs : DirectorCardCategorySelection

        Notes
        -----
        An implementation of `RoR2.DCCSBlender.GetBlendedDccs`.
        """
        weighted_selection = DCCSBlender.generate_weighted_category_selections(
            dccs_category, expansions, stages_cleared
        )
        selected_dccs = []
        if used_expansions is None:
            used_expansions = set()
        content_num = 0
        while content_num < DCCSBlender.CONTENT_MIX_LIMIT and weighted_selection:
            index = random.choices(range(len(weighted_selection)),
                                   weights=[w for _, w in weighted_selection])[0]
            pool_entry = weighted_selection[index][0]
            selected_dccs.append((pool_entry.dccs, pool_entry.weight))
            if isinstance(pool_entry, ConditionalPoolEntry):
                used_expansions = used_expansions.union(pool_entry.required_dlc)
            weighted_selection.pop(index)
            content_num += 1
        for pool_entry in dccs_category.always_included:
            if pool_entry.dccs.is_available(stages_cleared):
                selected_dccs.append((pool_entry.dccs, pool_entry.weight))
        blended_dccs = DirectorCardCategorySelection()
        DCCSBlender.ensure_all_categories_exist(blended_dccs, selected_dccs)
        DCCSBlender.merge_categories(blended_dccs, selected_dccs)
        blended_dccs.expansions_in_effect = used_expansions
        return blended_dccs

    def generate_weighted_category_selections(dccs_category, expansions, stages_cleared):
        """
        Collect all available DCCS from the selected category.

        Parameters
        ----------
        dccs_category: DccsCategory
            The selected category.
        expansions : set
            The currently enabled expansions, which affects which spawn cards
            will be available.
        stages_cleared : int
            The number of cleared stages, which affects which spawn cards
            will be available.

        Returns
        -------
        weighted_selections : list
            The list of available pool entries.

        Notes
        -----
        An implementation of `RoR2.DCCSBlender.GenerateWeightedCategorySelections`.
        """
        weighted_selection = []
        has_selected_any_conditional_entries = False
        for pool_entry in dccs_category.included_conditions_met:
            if (pool_entry.dccs.is_available(stages_cleared) and
                DCCSBlender.are_conditions_met(pool_entry, expansions)):
                is_entry_available = True
                if len(expansions) > 0:
                    for dlc in pool_entry.required_dlc:
                        if dlc not in expansions:
                            is_entry_available = False
                            break;
                if is_entry_available:
                    has_selected_any_conditional_entries = True
                    weighted_selection.append((pool_entry, pool_entry.weight))
        if not has_selected_any_conditional_entries:
            for pool_entry in dccs_category.included_conditions_not_met:
                if pool_entry.is_available(stages_cleared):
                    weighted_selection.append((pool_entry, pool_entry.weight))
        return weighted_selection

    def are_conditions_met(pool_entry, expansions):
        """
        Whether this DCCS meets the requirements.

        Parameters
        ----------
        pool_entry: PoolEntry
            The selected pool entry.
        expansions : set
            The currently enabled expansions.

        Returns
        -------
        bool

        Notes
        -----
        An implementation of `RoR2.DCCSBlender.AreConditionsMet`.
        """
        return all(dlc in expansions for dlc in pool_entry.required_dlc)

    def ensure_all_categories_exist(blended_dccs, selected_dccs):
        """
        Add any missing categories a selected DCCS to the blended one.

        Parameters
        ----------
        blended_dccs : DirectorCardCategorySelection
            The blended DCCS. Note that this is modified in place.
        selected_dccs : DirectorCardCategorySelection
            DCCS chosen to be blended in.

        Returns
        -------
        None

        Notes
        -----
        An implementation of `RoR2.DCCSBlender.EnsureAllCategoriesExist`.
        """
        for dccs in selected_dccs:
            for category in dccs[0].categories:
                if blended_dccs.get_category_index(category.name) == -1:
                    blended_dccs.add_category(category.name, 1, [])

    def merge_categories(blended_dccs, selected_dccs):
        """
        Blend all selected DCCS.

        Parameters
        ----------
        blended_dccs : DirectorCardCategorySelection
            The blended DCCS. Note that this is modified in place.
        selected_dccs : list
            All selected DCCS chosen to be blended.

        Returns
        -------
        None

        Notes
        -----
        An implementation of `RoR2.DCCSBlender.MergeCategories`.
        """
        for i, category in enumerate(blended_dccs.categories):
            name = category.name
            num = 0
            weight = 0
            for dccs in selected_dccs:
                index = dccs[0].get_category_index(name)
                dccs_category = dccs[0].categories[index]
                if index != -1:
                    num += 1
                    weight += dccs_category.weight
                    blended_dccs.categories[i].cards.extend(dccs_category.cards)
            blended_dccs.categories[i].weight = weight / num if num > 0 else weight
