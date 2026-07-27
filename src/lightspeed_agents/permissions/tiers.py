import enum


class ActionTier(str, enum.Enum):
    T0_AUTO = "T0"
    T1_SOFT = "T1"
    T2_GATE = "T2"
    T3_DUAL = "T3"
    T4_BOARD = "T4"


TIER_RISK_LEVELS = {
    ActionTier.T0_AUTO: 0,
    ActionTier.T1_SOFT: 1,
    ActionTier.T2_GATE: 2,
    ActionTier.T3_DUAL: 3,
    ActionTier.T4_BOARD: 4,
}

TIER_APPROVAL_COUNT = {
    ActionTier.T0_AUTO: 0,
    ActionTier.T1_SOFT: 0,
    ActionTier.T2_GATE: 1,
    ActionTier.T3_DUAL: 2,
    ActionTier.T4_BOARD: 3,
}

TIER_TIMEOUT_MINUTES = {
    ActionTier.T0_AUTO: 0,
    ActionTier.T1_SOFT: 0,
    ActionTier.T2_GATE: 30,
    ActionTier.T3_DUAL: 60,
    ActionTier.T4_BOARD: 1440,
}

TIER_DESCRIPTIONS = {
    ActionTier.T0_AUTO: "Auto - fully autonomous, no approval needed",
    ActionTier.T1_SOFT: "Soft - non-critical writes, optional warning",
    ActionTier.T2_GATE: "Gate - critical writes, single human approval",
    ActionTier.T3_DUAL: "Dual - high-stakes, two human approvals",
    ActionTier.T4_BOARD: "Board - governance/legal, board vote required",
}
