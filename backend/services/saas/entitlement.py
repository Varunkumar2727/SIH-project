from typing import Dict, Any, Set

class EntitlementService:
    """
    Part 14: Entitlement & Feature Flag Engine.
    Enforces plan capabilities without any fake billing logic.
    """

    PLANS = {
        "FREE": {
            "max_projects": 3,
            "max_storage_mb": 500,
            "features": {"AI_DETECTION", "REPORTING"}
        },
        "PRO": {
            "max_projects": 25,
            "max_storage_mb": 5000,
            "features": {
                "AI_DETECTION", "TEMPORAL_ANALYSIS", "CADASTRAL_COMPARISON",
                "REPORTING", "API_ACCESS", "EXTERNAL_INTEGRATIONS"
            }
        },
        "ENTERPRISE": {
            "max_projects": 9999,
            "max_storage_mb": 500000,
            "features": {
                "AI_DETECTION", "TEMPORAL_ANALYSIS", "CADASTRAL_COMPARISON",
                "REPORTING", "API_ACCESS", "EXTERNAL_INTEGRATIONS", "CUSTOM_MODELS"
            }
        }
    }

    @classmethod
    def can_use_feature(cls, plan_tier: str, feature: str) -> bool:
        plan = cls.PLANS.get(plan_tier.upper(), cls.PLANS["FREE"])
        return feature.upper() in plan["features"]

    @classmethod
    def get_plan_limits(cls, plan_tier: str) -> Dict[str, Any]:
        return cls.PLANS.get(plan_tier.upper(), cls.PLANS["FREE"])
