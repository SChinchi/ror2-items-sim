class ExpansionRequirementComponent:
    SCRIPT = -6164247658379296987

    @staticmethod
    def parse(asset, ids):
        return ids[asset['requiredExpansion']['m_PathID']]['m_Name']
