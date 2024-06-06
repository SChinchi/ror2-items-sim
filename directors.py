import random
import warnings

import numpy as np

from constants import Expansion, ALL_EXPANSIONS, IT_STAGES
from data.objects.dccs import DirectorCardCategorySelection
from data_loader import scenes, voidseed, simulacrum


class IndexedDirectorCard:
    def __init__(self, card, index):
        self.card = card
        self._name = card.spawn_card._name
        self.name = card.spawn_card.name
        self.cost = card.spawn_card.cost
        # We're dealing with both SpawnCard and InteractableSpawnCard objects,
        # and the former do not have some fields, for which we need some
        # defaults.
        self.limit = getattr(card.spawn_card, 'limit', np.inf)
        self.weight = card.weight
        self.skip_with_sacrifice = getattr(card.spawn_card, 'skip_with_sacrifice', False)
        self.sacrifice_weight = getattr(card.spawn_card, 'sacrifice_weight', 1.0)
        self.min_stages_cleared = card.min_stages_cleared
        self.index = index

    def is_available(self, stages_cleared, expansions):
        return self.card.is_available(stages_cleared, expansions)


class BaseSceneDirector:
    def _select_card(self, deck, max_cost):
        """
        Select a random interactable from the list of available spawn cards.
        
        Parameters
        ----------
        deck : list
            List of the available spawn cards.
        msx_cost : int
            The remaining scene credits, as cards more expensive than this
            cannot be selected.

        Returns
        -------
        IndexedDirectorCard
            The selected card.

        Notes
        -----
        An implementation of `RoR2.SceneDirector.SelectCard()`.
        """
        values = []
        weights = []
        for card, weight in deck:
            if card.cost <= max_cost:
                values.append(card)
                weights.append(weight)
        if not values:
            return
        return random.choices(values, weights)[0]

    def _process_generated_interactables(self, interactables, item_counter, print_result):
        """
        Print or return the generated interactables.

        Parameters
        ----------
        interactables : DirectorCardCategorySelection
            The DCCS with the interactable categories and their items.
        item_counter : list
            Spawn counter for each available interactable.
        print_result : bool
            Whether to print or return the result.

        Returns
        -------
        out : None or list
            If `print_result` is set to False, the generated interactables will
            be returned in a list.
        """
        if print_result:
            for category in interactables.categories:
                for card in category.cards:
                    count = item_counter[card.index]
                    if count:
                        print(f'Spawned {card.name} {count} times.')
            return
        out = []
        for category in interactables.categories:
            for card in category.cards:
                count = item_counter[card.index]
                if count:
                    # The internal card name is more useful for lookups
                    out.extend([card._name] * count)
        return out

    def _process_statistics(sef, interactables, item_counter, print_result):
        """
        Print or return the interactable spawn statistics.

        Parameters
        ----------
        interactables : DirectorCardCategorySelection
            The DCCS with the interactable categories and their items.
        item_counter : array
            Spawn counter for each available interactable for each iteration.
        print_result : bool
            Whether to print or return the result.

        Returns
        -------
        out : None or list
            A list of with info about each interactable in tuples. This is the
            name of the interactable, the mean value, its standard deviation,
            and the probability the item will spawn at least once.
        """
        mean = item_counter.mean(axis=0)
        std = item_counter.std(axis=0)
        once = (item_counter > 0).mean(axis=0)
        if print_result:
            result = []
            for category in interactables.categories:
                string = [f'---{category.name}---']
                for card in category.cards:
                    name = card.name
                    index = card.index
                    if mean[index]:
                        string.append(
                            f'{name} spawned {mean[index]:.3f} times (SD = {std[index]:.3f}) on average. At least once {once[index]*100:.1f}% of the time.'
                        )
                    else:
                        string.append(f'{name} did not spawn.')
                result.append('\n'.join(string))
            print('\n\n'.join(result))
            return
        out = []
        for category in interactables.categories:
            for card in category.cards:
                # The internal card name is more useful for lookups
                out.append((card._name, mean[card.index], std[card.index], once[card.index]))
        return out
    

class SceneDirector(BaseSceneDirector):
    """Handle scene interactable generation."""
    
    def __init__(self,
                 scene_name,
                 num_players=1,
                 is_command_enabled=False,
                 is_sacrifice_enabled=False,
                 is_bonus_credits_available=False,
                 is_log_available=True,
                 expansions=ALL_EXPANSIONS):
        """
        Instantiate the scene director.

        Parameters
        ----------
        scene_name : str
            The internal name of the scene.
        num_players : int, optional
            The number of players. This affects the available amount of
            interactable credits for scene population.
        is_command_enabled, is_sacrifice_enabled : bool, optional
            Whether the respective artifacts are enabled, which affects which
            interactables are available for scene population.
        is_bonus_credits_available : bool, optional
            Whether the vault in Abyssal Depths is open for extra credits.
        is_log_available : bool, optional
            Whether the environmental log has already been found. If yes, the
            radio scanner will not be available for scene population.
        expansions : set, optional
            The list of enabled expansions, which adds new scenes and
            interactables. By default they are all enabled.

        Warns
        -----
        UserWarning
            If a required DLC is not enabled, it will be automatically enabled.
        """
        self._scene_name = scene_name
        self._scene_data = scenes[scene_name]
        if self._scene_data.required_dlc and self._scene_data.required_dlc not in expansions:
            warnings.warn('The current scene requires the DLC, which will now be enabled.')
            expansions.add(required_dlc)
        self._expansions = expansions
        self.num_players = num_players
        self.is_command_enabled = is_command_enabled
        self.is_sacrifice_enabled = is_sacrifice_enabled
        self.is_bonus_credits_available = is_bonus_credits_available
        self.is_log_available = is_log_available

    def _start(self, stages_cleared):
        """
        Prepare variables before populating the scene.

        Parameters
        ----------
        stages_cleared : int
            The number of stages cleared. It should really be zero or a positive
            integer, but negative values will behave like a zero.

        Returns
        -------
        interactable_credit : int
            The interactable credits for the scene.
        interactables : DirectorCardCategorySelection
            The DCCS with the interactable categories and their items available
            based on whether the Artifact of Command/Sacrifice or the DLC are
            enabled.
        deck : list
            List of the filtered weighted spawn cards.
        item_num : int
            The total number of interactables in `interactables`.
        """
        stage_info = self._scene_data.stage_info
        if stage_info:
            interactable_credit = int(stage_info.interactable_credits * (.5 + self.num_players * .5))
            if self.is_bonus_credits_available:
                interactable_credit += stage_info.bonus_credits
            if self._scene_name in IT_STAGES:
                interactable_credit = simulacrum.interactable_credits
            if self.is_sacrifice_enabled:
                interactable_credit //= 2
        else:
            interactable_credit = 0
        interactables = self._generate_interactable_card_selection(stages_cleared)
        deck = interactables.generate_card_weighted_selection(
            stages_cleared, self._expansions, self.is_sacrifice_enabled
        )
        item_num = sum(len(category.cards) for category in interactables.categories)
        return interactable_credit, interactables, deck, item_num
        
    def _generate_interactable_card_selection(self, stages_cleared):
        """
        Generate all valid interactable cards.

        Parameters
        ----------
        stages_cleared : int
            The number of stages cleared.

        Returns
        -------
        categories : list
            The list of available categories.

        Notes
        -----
        An implementation of
        `RoR2.SceneDirector.GenerateInteractableCardSelection()`.
        """
        categories = DirectorCardCategorySelection()
        stage_info = self._scene_data.stage_info
        if not stage_info or not stage_info.interactables:
            return categories
        interactables = stage_info.interactables.generate_weighted_selection(
            self._expansions, stages_cleared
        )
        index = 0
        for category in interactables.categories:
            cards = []
            for card in category.cards:
                spawn_card = card.spawn_card
                skip_command = self.is_command_enabled and spawn_card.offers_choice
                skip_sacrifice = self.is_sacrifice_enabled and spawn_card.skip_with_sacrifice
                skip_log = self.is_log_available and spawn_card._name == 'iscRadarTower'
                if skip_command or skip_sacrifice or skip_log:
                    continue
                # Since we'll need to access the index of a card in a list a lot,
                # we store it in the card object for quick access.
                cards.append(IndexedDirectorCard(card, index))
                index += 1
            categories.add_category(category.name, category.weight, cards)
        return categories

    def _select_card(self, deck, max_cost):
        """
        Select a random interactable from the list of available spawn cards.
        
        Parameters
        ----------
        deck : list
            List of the available spawn cards.
        msx_cost : int
            The remaining scene credits, as cards more expensive than this
            cannot be selected.

        Returns
        -------
        IndexedDirectorCard
            The selected card.

        Notes
        -----
        An implementation of `RoR2.SceneDirector.SelectCard()`.
        """
        values = []
        weights = []
        for card, weight in deck:
            if card.cost <= max_cost:
                values.append(card)
                weights.append(weight)
        if not values:
            return
        return random.choices(values, weights)[0]
    
    def _populate_scene(self, interactable_credit, deck, item_counter):
        """
        Populate the scene with valid interactables.

        Parameters
        ----------
        interactable_credit : int
            The available credits for the scene.
        deck : list
            List of the available spawn cards.
        item_counter : list_like
            An initialised list with zeroes, which will be incremented to count
            any items spawned according to their index in the list. This is a
            mutable operation.

        Returns
        -------
        None

        Notes
        -----
        A partial implementation of `RoR2.SceneDirector.PopulateScene()`.
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
                interactable_credit -= card.cost
                # In the game's source code after paying for the card, it attempts
                # to spawn it, but this can still fail for a few reasons. We're
                # implementing the skip for the Artifact of Sacrifice here.
                if not self.is_sacrifice_enabled or not card.skip_with_sacrifice:
                    # Incrementing a counter for each spawned item's index is a
                    # design choice isntead of storing the literal items in a
                    # list, since this allows efficient statistical computations.
                    item_counter[card.index] += 1

    def populate_scene(self, stages_cleared=-1, print_result=True):
        """
        Populate the scene with valid interactables.

        Parameters
        ----------
        stages_cleared : int, default -1
            The number of stages cleared, which affects which interactables
            will be available. Any positive integer or zero is allowed. Any
            negative value will use the default stage value for the scene. Do
            not to use the default for any Hidden Realms, because they have
            nonsensical values.
        print_result: bool, optional
            Whether to print the generated interactables or return them.

        Returns
        -------
        None or list
            If the `print_result` argument is set to False, the list of the
            generated interactables will be returned.
        """
        if stages_cleared < 0:
            stages_cleared = self._scene_data.stage_order
        interactable_credit, interactables, deck, item_num = self._start(stages_cleared)
        item_counter = [0] * item_num
        self._populate_scene(interactable_credit, deck, item_counter)
        return self._process_generated_interactables(interactables, item_counter, print_result)

    def collect_statistics(self, stages_cleared=-1, iterations=10000, print_result=True):
        """
        Gather interactable spawn statistics.

        Parameters
        ----------
        stages_cleared : int, default -1
            The number of stages cleared, which affects which interactables
            will be available. Any positive integer or zero is allowed. Any
            negative value will use the default stage value for the scene. Try
            not to use the default for any Hidden Realms, because they large
            values.
        iterations: int, optional
            The number of times the scene interactables will be generated.
        print_result: bool, optional
            Whether to print the result or return it.

        Returns
        -------
        None, list
            If the `print_result` argument is set to False, the generated
            interactables will be returned as a list of tuple info for each
            interactable.
        """
        if stages_cleared < 0:
            stages_cleared = self._scene_data.stage_order
        interactable_credit, interactables, deck, item_num = self._start(stages_cleared)
        item_counter = np.zeros((iterations, item_num), dtype=np.int32)
        for i in range(iterations):
            self._populate_scene(interactable_credit, deck, item_counter[i])
        return self._process_statistics(interactables, item_counter, print_result)

    def change_scene(self, scene_name):
        """
        Change the scene.

        Parameters
        ----------
        scene_name : str
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
        self._scene_name = scene_name
        self._scene_data = scenes[scene_name]
        required_dlc = self._scene_data.required_dlc
        if required_dlc and required_dlc not in self._expansions:
            warnings.warn('The new scene requires a DLC, which will now be enabled.')
            self._expansions.add(required_dlc)

    def set_enabled_expansions(self, expansions):
        """
        Select which expansions will be enabled.

        Parameters
        ----------
        expansions : iterable
            The expansions to be enabled, represented by their internal name.

        Returns
        -------
        None

        Warns
        -----
        UserWarning
            If the currently selected scene requires a DLC, attempting to
            disable it will fail.
        """
        required_dlc = self._scene_data.required_dlc
        if required_dlc and required_dlc not in expansions:
            warnings.warn('The current scene requires specific DLC content enabled.')
            return
        self._expansions = set(expansions)


class CampDirector(BaseSceneDirector):
    """Handle void seed interactable generation."""
    
    def __init__(self, spawns_kelp=False, is_sacrifice_enabled=False, expansions={Expansion.SOTV}):
        """
        Instantiate the void seed director.

        Parameters
        ----------
        spawns_kelp : bool, optional
            Decide which of the two `CampDirector` types to initialise. The
            default value is for Interactables & Void Monsters, while the other
            one is for Kelp Props & Voidtouched Stage Monsters.
        is_sacrifice_enabled : bool, optional
            Whether the Artifact of Sacrifice is enabled, which will affect
            which interactables can spawn. By default it's disabled.
        expansions : set, optional
            The list of enabled expansions, which adds new scenes and
            interactables. By default the Survivors of the Void expansion is
            enabled and even if it is not included in the argument, it will be
            forcefully included as it is required for the Void Seeds to exist.

        Returns
        -------
        None
        """
        camp_type = 'camp1' if not spawns_kelp else 'camp2'
        self._data = voidseed[camp_type]
        self.is_sacrifice_enabled = is_sacrifice_enabled
        self._expansions = expansions.union({Expansion.SOTV})

    def _start(self):
        """
        Prepare variables before populating the void seed.

        Returns
        -------
        interactable_credit : int
            The interactable credits for the void seed.
        interactables : DirectorCardCategorySelection
            The DCCS with the interactable categories and their items.
        deck : list
            List of the filtered weighted spawn cards.
        item_num : int
            The total number of interactables in `interactables`.
        """
        interactable_credit = self._data.interactable_credits
        interactables = self._generate_interactable_card_selection()
        deck = interactables.generate_card_weighted_selection(
            0, self._expansions, self.is_sacrifice_enabled
        )
        item_num = sum(len(category.cards) for category in interactables.categories)
        return interactable_credit, interactables, deck, item_num

    def _generate_interactable_card_selection(self):
        """
        Generate all valid interactable cards.

        Returns
        -------
        categories : list
            The list of available categories.

        Notes
        -----
        An implementation of
        `RoR2.CampDirector.GenerateInteractableCardSelection()`.
        """
        interactables = self._data.interactables
        categories = DirectorCardCategorySelection()
        index = 0
        for category in interactables.categories:
            cards = []
            for card in category.cards:
                # Since we'll need to access the index of a card in a list a lot,
                # we store it in the card object for quick access.
                cards.append(IndexedDirectorCard(card, index))
                index += 1
            categories.add_category(category.name, category.weight, cards)
        return categories
    
    def _populate_camp(self, interactable_credit, deck, item_counter):
        """
        Populate the void seed with valid interactables.

        Parameters
        ----------
        interactable_credit : int
            The available credits for the scene.
        deck : list
            List of the available spawn cards.
        item_counter : list_like
            An initialised list with zeroes, which will be incremented to count
            any items spawned according to their index in the list. This is a
            mutable operation.

        Returns
        -------
        None

        Notes
        -----
        A partial implementation of `RoR2.CampDirector.PopulateCamp()`.
        """
        while interactable_credit > 0:
            card = self._select_card(deck, interactable_credit)
            if not card:
                break
            interactable_credit -= card.cost
            # In the game's source code after paying for the card, it attempts
            # to spawn it, but this can still fail for a few reasons. We're
            # implementing the skip for the Artifact of Sacrifice here.
            if not self.is_sacrifice_enabled or not card.skip_with_sacrifice:
                # Incrementing a counter for each spawned item's index is a
                # design choice isntead of storing the literal items in a
                # list, since this allows efficient statistical computations.
                item_counter[card.index] += 1

    def populate_camp(self, print_result=True):
        """
        Populate the void seed with valid interactables.

        Parameters
        ----------
        print_result: bool, optional
            Whether to print the generated interactables or return them.

        Returns
        -------
        None or list
            If the `print_result` argument is set to False, the list of the
            generated interactables will be returned.
        """
        interactable_credit, interactables, deck, item_num = self._start()
        item_counter = [0] * item_num
        self._populate_camp(interactable_credit, deck, item_counter)
        return self._process_generated_interactables(interactables, item_counter, print_result)

    def collect_statistics(self, iterations=10000, print_result=True):
        """
        Gather interactable spawn statistics.

        Parameters
        ----------
        iterations: int, optional
            The number of times the interactables will be generated.
        print_result: bool, optional
            Whether to print or return the result.

        Returns
        -------
        None, list
            If the `print_result` argument is set to False, the generated
            interactables will be returned as a list of tuple info for each
            interactable.
        """
        interactable_credit, interactables, deck, item_num = self._start()
        item_counter = np.zeros((iterations, item_num), dtype=np.int32)
        for i in range(iterations):
            self._populate_camp(interactable_credit, deck, item_counter[i])
        return self._process_statistics(interactables, item_counter, print_result)
