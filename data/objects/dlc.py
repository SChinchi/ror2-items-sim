class ExpansionRequirementComponent:
    SCRIPT = -6227066436339345797

    @staticmethod
    def parse(asset, ids):
        return ids[asset['requiredExpansion']['m_PathID']]['m_Name']
