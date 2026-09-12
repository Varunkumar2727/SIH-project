from typing import Dict, Any, List, Optional

class DecisionScoringEngine:
    """
    Part 9: Advanced Land Analytics & Decision Intelligence Engine.
    Computes explainable, deterministic 0–100 composite scores:
      - Development Readiness Score (higher = better infrastructure & readiness)
      - Cadastral Risk Score (higher = higher probability of boundary dispute / verification need)
    """

    @classmethod
    def evaluate_parcel_readiness(
        cls,
        parcel: Dict[str, Any],
        cadastral_comp: Optional[Dict[str, Any]] = None,
        temporal_changes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculates explainable development readiness and discrepancy risk scores.
        """
        factors = []
        readiness_score = 50.0 # Base

        # 1. Access Factor
        acc = parcel.get("accessibility", {})
        acc_status = acc.get("access_status", "UNASSESSED")
        if acc_status == "DIRECT_ACCESS":
            readiness_score += 30.0
            factors.append({"factor": "Road Frontage", "impact": "+30", "detail": "Direct physical frontage detected."})
        elif acc_status == "MARGINAL_ACCESS":
            readiness_score += 10.0
            factors.append({"factor": "Marginal Access", "impact": "+10", "detail": "Secondary road access within 60px."})
        else:
            readiness_score -= 30.0
            factors.append({"factor": "Access Concern", "impact": "-30", "detail": "No detected direct physical road connection."})

        # 2. Compactness / Geometry Factor
        compactness = parcel.get("compactness", 0.7)
        if compactness >= 0.6:
            readiness_score += 10.0
            factors.append({"factor": "Regular Lot Geometry", "impact": "+10", "detail": f"High compactness ({compactness})."})
        elif compactness < 0.3:
            readiness_score -= 15.0
            factors.append({"factor": "Irregular Shape", "impact": "-15", "detail": f"Low compactness ({compactness}), sliver risk."})

        # 3. Cadastral Alignment Factor
        risk_score = 10.0 # Base risk
        if cadastral_comp:
            status = cadastral_comp.get("status")
            iou = cadastral_comp.get("iou", 0.0)
            if status == "MATCHED":
                readiness_score += 10.0
                risk_score += 5.0
                factors.append({"factor": "Cadastral Concordance", "impact": "+10", "detail": f"High alignment with survey records (IoU {iou})."})
            elif status == "DISCREPANCY_DETECTED":
                readiness_score -= 15.0
                risk_score += 45.0
                factors.append({"factor": "Cadastral Discrepancy", "impact": "-15", "detail": "Discrepancy detected between AI parcel and authoritative survey."})
            elif status == "UNMATCHED_SURVEY":
                readiness_score -= 20.0
                risk_score += 60.0
                factors.append({"factor": "Unregistered Parcel", "impact": "-20", "detail": "No registered cadastral parcel found for structure footprint."})

        # 4. Temporal Stability Factor
        if temporal_changes:
            # Check if this parcel is associated with recent new construction or demolition
            p_id = parcel.get("id")
            associated_changes = [c for c in temporal_changes if c.get("t2_feature_id") == p_id or c.get("t1_feature_id") == p_id]
            if associated_changes:
                risk_score += 25.0
                factors.append({"factor": "Recent Temporal Change", "impact": "Risk +25", "detail": "Structural footprint altered across survey epochs."})

        final_readiness = max(0.0, min(100.0, readiness_score))
        final_risk = max(0.0, min(100.0, risk_score))

        # Risk Classification
        if final_risk >= 70.0:
            risk_category = "HIGH_VERIFICATION_PRIORITY"
        elif final_risk >= 35.0:
            risk_category = "MODERATE_PRIORITY"
        else:
            risk_category = "ROUTINE_MONITORING"

        return {
            "parcel_id": parcel.get("id"),
            "development_readiness_score": round(final_readiness, 1),
            "discrepancy_risk_score": round(final_risk, 1),
            "priority_category": risk_category,
            "explainability_factors": factors,
            "legal_note": "Scores are decision-support indicators and do not dictate statutory land valuation."
        }
