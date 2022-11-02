import json

from data_parser import extract_file_data
from data.dirpaths import *
from data.objects import *


class ItemTiers:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, ItemTierDef(value))


class Items:
    def __init__(self, data):
        self._items = []
        for item_data in data:
            item = ItemDef(item_data)
            self._items.append(item)
            setattr(self, item._name, item)


class Equipment:
    def __init__(self, data):
        self._items = []
        for item_data in data:
            item = EquipmentDef(item_data)
            self._items.append(item)
            setattr(self, item._name, item)


class DirectorCard:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        if self.spawn_card.startswith('isc'):
            self.spawn_card = isc[self.spawn_card]
        elif self.spawn_card.startswith('csc'):
            self.spawn_card = csc[self.spawn_card]
        elif self.spawn_card.startswith('sc'):
            self.spawn_card = sc[self.spawn_card]

    def __repr__(self):
        return f'({self.spawn_card._name}, {self.weight}, {self.min_stages_cleared})'


class Scene:
    def __init__(self, name, data):
        self.name = name
        for key, value in data.items():
            setattr(self, key, value)
        if self.stage_info:
            self.stage_info = ClassicStageInfo(self.stage_info)
            if self.stage_info.interactables:
                self.stage_info.interactables =  self._init_dccs_pool(self.stage_info.interactables)
            if self.stage_info.monsters:
                self.stage_info.monsters = self._init_dccs_pool(self.stage_info.monsters)

    def __repr__(self):
        return self.name

    def _init_dccs_pool(self, data):
        dccs_pool = DccsPool(data)
        for category in dccs_pool.categories:
            for category_type in (category.always_included,
                                  category.included_conditions_met,
                                  category.included_conditions_not_met):
                for pool_entry in category_type:
                    pool_entry.dccs = dccs[pool_entry.dccs]
        return dccs_pool


class VoidCamp:
    def __init__(self, name, data):
        self.name = name
        for key, value in data.items():
            setattr(self, key, value)
        self.interactables = dccs[self.interactables]
        if self.monsters:
            self.monsters = dccs[self.monsters]

    def __repr__(self):
        return self.name


def _init_items(data):
    items = Items(data)
    for item in items._items:
        item.tier = getattr(ItemTiers, item.tier)
    return items


def _init_droptable(data):
    dt = eval(data['class'])(data)
    if data['class'] == 'ExplicitPickupDropTable':
        dt.entries = [[getattr(Items, item, item), weight] for item, weight in dt.entries]
    return dt


def _init_isc(data):
    card = InteractableSpawnCard(data)
    if card.drop_table:
        card.drop_table = droptables[card.drop_table]
    return card


def _init_body(data):
    body = CharacterBody(data)
    if body.item_drop:
        body.item_drop = getattr(Items, body.item_drop)
    return body


def _init_csc(data):
    card = eval(data['class'])(data)
    card.body = bodies[card.body]
    # TODO: Assign `self.master`
    return card


def _init_dccs(data):
    dccs = eval(data['class'])(data)
    dccs.categories = []
    for category in data['categories']:
        cards = []
        for card in category['cards']:
            cards.append(DirectorCard(card))
        dccs.add_category(category['name'], category['weight'], cards)
    return dccs


def _init_camp(name, data):
    name = 'camp1' if 'Camp 1' in name else 'camp2'
    camp = VoidCamp(name, data)
    return name, camp


def load_data(category):
    """
    Load data extracted from the game.

    Parameters
    ----------
    category : str
        Keyword to decide which category of data to load. The options include
        'items', 'equipment', 'tiers', 'droptables', 'bodies', 'sc', 'isc',
        'csc', 'skills', 'dccs', 'scenes', and 'voidcamp'.

    Returns
    -------
    out : list, dict
        The loaded data. The equipment/item data will be in a list, while
        everything else in a dictionary.
    """ 
    choices = {
        'items': ITEMS_FILE,
        'equipment': EQUIPMENT_FILE,
        'tiers': TIERS_FILE,
        'droptables': DROPTABLES_FILE,
        'bodies': BODIES_FILE,
        'sc': SC_FILE,
        'isc': ISC_FILE,
        'csc': CSC_FILE,
        'skills': SKILLS_FILE,
        'dccs': DCCS_FILE,
        'scenes': SCENES_FILE,
        'voidcamp': CAMP_FILE,
    }
    fname = choices[category]
    if not os.path.exists(fname):
        print('Parsed data file does not exist. It will take a minute to extract...')
        extract_file_data()
    with open(fname, 'r') as f:
        return json.load(f)


# DO NOT CHANGE - The order of initialisation matters
ItemTiers = ItemTiers(load_data('tiers'))
Items = _init_items(load_data('items'))
Equipment = Equipment(load_data('equipment'))
droptables = {name: _init_droptable(data) for name, data in load_data('droptables').items()}
sc = {name: SpawnCard(data) for name, data in load_data('sc').items()}
isc = {name: _init_isc(data) for name, data in load_data('isc').items()}
bodies = {name: _init_body(data) for name, data in load_data('bodies').items()}
csc = {name: _init_csc(data) for name, data in load_data('csc').items()}
dccs = {name: _init_dccs(data) for name, data in load_data('dccs').items()}
scenes = {name: Scene(name, data) for name, data in load_data('scenes').items()}
voidseed = dict(_init_camp(name, data) for name, data in load_data('voidcamp').items())
