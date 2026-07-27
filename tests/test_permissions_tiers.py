from lightspeed_agents.permissions.tiers import (
    ActionTier,
    TIER_RISK_LEVELS,
    TIER_APPROVAL_COUNT,
    TIER_TIMEOUT_MINUTES,
    TIER_DESCRIPTIONS,
)


class TestActionTier:

    def test_all_tiers_exist(self):
        assert len(ActionTier) == 5

    def test_tier_values(self):
        assert ActionTier.T0_AUTO.value == "T0"
        assert ActionTier.T1_SOFT.value == "T1"
        assert ActionTier.T2_GATE.value == "T2"
        assert ActionTier.T3_DUAL.value == "T3"
        assert ActionTier.T4_BOARD.value == "T4"

    def test_risk_levels_are_ascending(self):
        tiers = [
            ActionTier.T0_AUTO,
            ActionTier.T1_SOFT,
            ActionTier.T2_GATE,
            ActionTier.T3_DUAL,
            ActionTier.T4_BOARD,
        ]
        risks = [TIER_RISK_LEVELS[t] for t in tiers]
        assert risks == sorted(risks)

    def test_approval_counts(self):
        assert TIER_APPROVAL_COUNT[ActionTier.T0_AUTO] == 0
        assert TIER_APPROVAL_COUNT[ActionTier.T1_SOFT] == 0
        assert TIER_APPROVAL_COUNT[ActionTier.T2_GATE] == 1
        assert TIER_APPROVAL_COUNT[ActionTier.T3_DUAL] == 2
        assert TIER_APPROVAL_COUNT[ActionTier.T4_BOARD] == 3

    def test_timeout_minutes(self):
        assert TIER_TIMEOUT_MINUTES[ActionTier.T0_AUTO] == 0
        assert TIER_TIMEOUT_MINUTES[ActionTier.T1_SOFT] == 0
        assert TIER_TIMEOUT_MINUTES[ActionTier.T2_GATE] == 30
        assert TIER_TIMEOUT_MINUTES[ActionTier.T3_DUAL] == 60
        assert TIER_TIMEOUT_MINUTES[ActionTier.T4_BOARD] == 1440

    def test_descriptions_exist(self):
        for tier in ActionTier:
            assert tier in TIER_DESCRIPTIONS
            assert len(TIER_DESCRIPTIONS[tier]) > 0

    def test_tier_string_comparison(self):
        assert ActionTier.T0_AUTO == "T0"
        assert ActionTier.T2_GATE == "T2"
        assert ActionTier.T4_BOARD == "T4"
