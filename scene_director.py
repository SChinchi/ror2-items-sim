import random
import warnings

import numpy as np

from constants import Version
from data_parser import load_scene_data


# TODO: See if these can be automatically extracted from the game data
COMMAND_BANNED_ITEMS = {'iscTripleShop', 'iscTripleShopLarge', 'iscDuplicator',
                        'iscDuplicatorLarge', 'iscDuplicatorMilitary', 'iscDuplicatorWild',
                        'iscScrapper', 'iscShrineCleanse'}

SCENE_DATA, SPAWN_CARDS = load_scene_data()


class Category:
    def __init__(self, name, weight, cards):
        self.name = name
        self.weight = weight
        self.cards = cards


class Card:
    def __init__(self, min_stage, weight, spawn_card, index):
        self.name = spawn_card['name']
        self.cost = spawn_card['cost']
        self.min_stage = min_stage
        self.weight = weight
        self.sacrifice_weight = spawn_card['sacrifice_weight']
        self.limit = spawn_card['limit']
        self.index = index


class WeightedCard:
    def __init__(self, card, weight):
        self.card = card
        self.weight = weight


class SceneDirector:
    """Handle scene interactable generation."""    
    def __init__(self, scene_name,
                 num_players=1,
                 is_command_enabled=False,
                 is_sacrifice_enabled=False,
                 is_bonus_credits_available=False,
                 is_log_available=True,
                 is_dlc_enabled=True,
                 ):
        """
        Instantiate the scene director.

        Parameters
        ----------
        scene_name : str
            The internal name of the stage
        num_players : int, default 1
            The number of players. This affects the available amount of
            interactable credits for scene population.
        is_command_enabled : bool, default False
            Whether the Artifact of Command is available. This affects which
            interactables are available for scene population.
        is_sacrifice_enabled : bool, default False
            Whether the Artifact of Sacrifice is available. This affects which
            interactables are available for scene population.
        is_bonus_credits_available : bool, default False
            Whether the vault in Abyssal Depths is open for extra credits.
        is_log_available : bool, default True
            Whether the environmental log has already been found. If yes, the
            radio scanner will not be available for scene population.
        is_dlc_enabled : bool, default True
            Whether the Survivors of the Void DLC is enabled, which adds new
            scenes and interactables.
        
        Warns
        -----
        UserWarning
            If the DLC is currently disabled and the scene requires it, it
            will be automatically enabled.
        """
        self._scene_name = scene_name
        self._scene_data = SCENE_DATA[scene_name]
        if not is_dlc_enabled and scene_data[scene_name]['requires_dlc']:
            warnings.warn('The current scene requires the DLC, which will now be enabled.')
            is_dlc_enabled = True
        self._is_dlc_enabled = is_dlc_enabled
        self.num_players = num_players
        self.is_command_enabled = is_command_enabled
        self.is_sacrifice_enabled = is_sacrifice_enabled
        self.is_bonus_credits_available = is_bonus_credits_available
        self.is_log_available = is_log_available

    def _start(self, stages_cleared):
        """One-off compute variables before populating the scene.

        Parameters
        ----------
        stages_cleared : int
            The number of stages cleared. It's expected to be zero or a positive
            integer.

        Returns
        -------
        interactable_credit : int
            The interactable credits for the scene.
        items : list
            A list of all interactable categories -and their respective items-
            available based on whether the Artifact of Command/Sacrifice or the
            DLC are enabled.
        deck : list
            List of the filtered weighted spawn cards.
        item_num : int
            The total number of interactables in `items`.
        """
        interactable_credit = int(self._scene_data['credits'] * (.5 + self.num_players * .5))
        if self.is_bonus_credits_available:
            interactable_credit += self._scene_data['bonus_credits']
        if self.is_sacrifice_enabled:
            interactable_credit //= 2
        items = self._generate_interactable_card_selection()
        deck = self._generate_card_weighted_selection(items, stages_cleared)
        item_num = sum(len(category.cards) for category in items)
        return interactable_credit, items, deck, item_num
        
    def _generate_interactable_card_selection(self):
        """
        Generate all valid interactable cards.

        An implementation of
        `RoR2.SceneDirector.GenerateInteractablesCardSelection()`.

        Returns
        -------
        out : list
            The list of available categories defined using the `Category` class.
        """
        version = Version.DLC1 if self._is_dlc_enabled else Version.BASE
        categories = []
        # Since we'll need to access the index of a card in a list a lot,
        # we store it in the `Card` object for quick access.
        index = 0
        for name, category in self._scene_data[version].items():
            cards = []
            for card in category['cards']:
                spawn_card = SPAWN_CARDS[card['spawn_card_id']]
                skip_command = self.is_command_enabled and spawn_card['name'] in COMMAND_BANNED_ITEMS
                skip_sacrifice = self.is_sacrifice_enabled and spawn_card['sacrifice_skip']
                skip_log = self.is_log_available and spawn_card['name'] == 'iscRadarTower'
                if skip_command or skip_sacrifice or skip_log:
                    continue
                cards.append(Card(card['min_stage'], card['weight'], spawn_card, index))
                index += 1
            categories.append(Category(name, category['weight'], cards))
        return categories

    def _generate_card_weighted_selection(self, interactables, stages_cleared):
        """
        Generate all available interactable spawn cards for the scene.

        An implementation of
        `RoR2.DirectorCardCategorySelection.GenerateDirectorCardWeightedSelection()`.

        Parameters
        ----------
        interactables : list
            A list of categories of any available interactables.
        stages_cleared : int
            The number of cleared stages, which affects which interactables
            will be available.

        Returns
        -------
        weighted_selection : list
            The list of available cards using the `Card` class.
        """
        weighted_selection = []
        for category in interactables:
            category_weight = category.weight
            cards = category.cards
            total_weight = sum(card.weight for card in cards if stages_cleared >= card.min_stage)
            if total_weight > 0:
                modifier = category_weight / total_weight
                for card in cards:
                    if stages_cleared >= card.min_stage:
                        weight = card.weight * modifier
                        if self.is_sacrifice_enabled:
                            weight *= card.sacrifice_weight
                        weighted_selection.append(WeightedCard(card, weight))
        return weighted_selection

    def _select_card(self, deck, max_cost):
        """
        Select a random interactable from the list of available spawn cards.

        An implementation of `RoR2.SceneDirector.SelectCard()`.
        
        Parameters
        ----------
        deck : list
            List of the available spawn cards defined with the `Card` class.
        msx_cost : int
            The remaining scene credits, as cards more expensive than this
            cannot be selected.

        Returns
        -------
        out : Card
            The selected card.
        """
        selections = []
        weights = []
        for card in deck:
            if card.card.cost <= max_cost:
                selections.append(card.card)
                weights.append(card.weight)
        if not selections:
            return
        return random.choices(selections, weights)[0]

    def _populate_scene(self, interactable_credit, deck, item_counter):
        """
        Populate the scene with valid interactables.

        A partial implementation of `RoR2.SceneDirector.PopulateScene()`.

        Parameters
        ----------
        interactable_credit : int
            The available credits for the scene.
        deck : list
            List of the available spawn cards defined with the `Card` class.
        item_counter : list_like
            An initialised list with zeroes, which will be incremented to count
            any items spawned according to their index in the list. This is a
            mutable operation.

        Returns
        -------
        None
        """
        card_limits = {}
        while interactable_credit > 0:
            card = self._select_card(deck, interactable_credit)
            if not card:
                break
            if card not in card_limits:
                card_limits[card] = card.limit if card.limit > 0 else np.inf
            if card_limits[card] > 0:
                card_limits[card] -= 1
                # Incrementing a counter for each spawned item's index is a
                # design choice isntead of storing the literal items in a list,
                # since this allows efficient statistical computations.
                item_counter[card.index] += 1
                interactable_credit -= card.cost

    def populate_scene(self, stages_cleared=-1):
        """
        Populate the scene with valid interactables and print the results.

        Parameters
        ----------
        stages_cleared : int, optional, default -1
            The number of stages cleared, which affects which interactables
            will be available. Any positive integer or zero is allowed to
            account for the Artifact of Dissonance or looping. Any negative
            value will cause a default value to be calculated.

        Returns
        -------
        None
        """
        if stages_cleared < 0:
            stages_cleared = self._scene_data['stage_order']
        interactable_credit, interactables, deck, item_num = self._start(stages_cleared)
        item_counter = [0] * item_num
        self._populate_scene(interactable_credit, deck, item_counter)
        for category in interactables:
            for card in category.cards:
                count = item_counter[card.index]
                if count:
                    print(f'Spawned {card.name} {count} times.')

    def print_statistics(self, stages_cleared=-1, iterations=10000):
        """
        Gather interactable spawn statistics.

        Parameters
        ----------
        stages_cleared : int, optional, default -1
            The number of stages cleared, which affects which interactables
            will be available. Any positive integer or zero is allowed to
            account for the Artifact of Dissonance or looping. Any negative
            value will cause a default value to be calculated.
        iterations: int, optional
            The number of times the scene interactables will be generated.

        Returns
        -------
        None
        """
        if stages_cleared < 0:
            stages_cleared = self._scene_data['stage_order']
        interactable_credit, interactables, deck, item_num = self._start(stages_cleared)
        item_counter = np.zeros((iterations, item_num), dtype=np.int32)
        for i in range(iterations):
            self._populate_scene(interactable_credit, deck, item_counter[i])
        mean = item_counter.mean(axis=0)
        std = item_counter.std(axis=0)
        for category in interactables:
            print(f'---{category.name}---')
            for card in category.cards:
                name = card.name
                index = card.index
                if mean[index]:
                    print(f'{name} spawned {mean[index]:.3f} times (SD = {std[index]:.3f}) on average.')
                else:
                    print(f'{name} did not spawn.')
            print()

    def change_scene(self, name):
        """
        Change the scene.

        Parameters
        ----------
        name : str
            The internal name of the new stage.

        Returns
        -------
        None

        Warns
        -----
        UserWarning
            If the DLC is currently disabled and the new scene requires it, it
            will be automatically enabled.
        """
        self._scene_name = name
        self._scene_data = SCENE_DATA[name]
        if not self._is_dlc_enabled and self._scene_data['requires_dlc']:
            warnings.warn('The new scene requires the DLC, which will now be enabled.')
            self._is_dlc_enabled = True

    def enable_dlc(self, is_enabled):
        """
        Enable/disable the Survivors of the Void DLC.

        Parameters
        ----------
        is_enabled : boolean
            Change whether the DLC is active. This affects what interactables
            can spawn in a stage.

        Returns
        -------
        None

        Warns
        -----
        UserWarning
            If the currently selected scene requires the DLC, attempting to
            disable it will fail.
        """
        if not is_enabled and self._scene_data['requires_dlc']:
            warnings.warn('The current scene requires the DLC content enabled.')
            return
        self._is_dlc_enabled = is_enabled
