class CraftableDef:
    SCRIPT = 6241384122443657236

    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        self.recipes = [Recipe(recipe) for recipe in self.recipes]

    def __repr__(self):
        return repr(self.pickup)

    @staticmethod
    def parse(asset):
        return {
            '_name': asset['m_Name'],
            # To be filled out once all file ids have been collected
            'pickup': asset['pickup']['m_PathID'],
            'recipes': [Recipe.parse(recipe) for recipe in asset['recipes']],
        }


class Recipe:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        return f'({self.amount}, {self.ingredients})'

    @staticmethod
    def parse(asset):
        return {
            'amount': asset['amountToDrop'],
            # To be filled out once all file ids have been collected
            'ingredients': [obj['pickup']['m_PathID']
                            for obj in asset['ingredients']],
        }
