from typing import Dict, Any, List, Optional
from datetime import datetime
from shapely.geometry import Polygon
from shapely.validation import make_valid

class TemporalChangeDetector:
    """
    Part 6: Temporal Change Detection & Land Change Intelligence Engine.
    Compares multi-temporal imagery / feature scenes (Baseline T1 vs. Current T2)
    with chronological verification and feature-level change classification.
    """

    IOU_IDENTITY_THRESHOLD = 0.75
    AREA_CHANGE_THRESHOLD = 0.15 # 15% delta qualifies as footprint modification

    @classmethod
    def validate_chronology(cls, t1_date: str, t2_date: str) -> None:
        """
        Validates that baseline scene date strictly precedes current scene date.
        """
        try:
            d1 = datetime.fromisoformat(t1_date.replace("Z", "+00:00"))
            d2 = datetime.fromisoformat(t2_date.replace("Z", "+00:00"))
            if d1 >= d2:
                raise ValueError(
                    f"Temporal chronology violation: Baseline date ({t1_date}) must precede Current date ({t2_date})."
                )
        except Exception as e:
            if "chronology violation" in str(e):
                raise
            # If dates are in YYYY-MM-DD or standard strings
            if str(t1_date) >= str(t2_date):
                raise ValueError(
                    f"Temporal chronology violation: Baseline date ({t1_date}) must precede Current date ({t2_date})."
                )

    @classmethod
    def detect_changes(
        cls,
        scene_t1: Dict[str, Any],
        scene_t2: Dict[str, Any],
        t1_date: str = "2024-01-01",
        t2_date: str = "2025-01-01"
    ) -> Dict[str, Any]:
        """
        Detects structural and land-cover changes between T1 and T2 feature sets.
        """
        cls.validate_chronology(t1_date, t2_date)

        features_t1 = scene_t1.get("features", {})
        features_t2 = scene_t2.get("features", {})

        bldgs_t1 = features_t1.get("buildings", [])
        bldgs_t2 = features_t2.get("buildings", [])

        changes = []
        matched_t1_bldg_ids = set()

        # Check T2 buildings against T1
        for b2 in bldgs_t2:
            coords_2 = b2.get("polygon", [])
            if len(coords_2) < 3:
                continue
            p2 = make_valid(Polygon(coords_2))
            
            matched_b1 = None
            max_iou = 0.0

            for b1 in bldgs_t1:
                coords_1 = b1.get("polygon", [])
                if len(coords_1) < 3:
                    continue
                p1 = make_valid(Polygon(coords_1))

                if p2.intersects(p1):
                    inter = p2.intersection(p1).area
                    union = p2.union(p1).area
                    iou = inter / (union + 1e-6)
                    if iou > max_iou:
                        max_iou = iou
                        matched_b1 = (b1, p1)

            if matched_b1 is None or max_iou < 0.10:
                # Completely new building in T2
                changes.append({
                    "change_id": f"chg_new_{b2.get('id', 'b')}",
                    "change_type": "NEW_CONSTRUCTION",
                    "feature_class": "building",
                    "t1_feature_id": None,
                    "t2_feature_id": b2.get("id"),
                    "area_delta_px": round(float(p2.area), 2),
                    "confidence": round(float(b2.get("confidence", 0.8)), 3),
                    "polygon": coords_2,
                    "status": "UNREVIEWED",
                    "description": "Detected new structural construction between survey epochs."
                })
            else:
                b1_obj, p1_geom = matched_b1
                matched_t1_bldg_ids.add(b1_obj.get("id"))
                area_ratio = abs(p2.area - p1_geom.area) / (p1_geom.area + 1e-6)

                if max_iou < cls.IOU_IDENTITY_THRESHOLD or area_ratio >= cls.AREA_CHANGE_THRESHOLD:
                    # Modified footprint
                    changes.append({
                        "change_id": f"chg_mod_{b2.get('id', 'b')}",
                        "change_type": "MODIFIED_FOOTPRINT",
                        "feature_class": "building",
                        "t1_feature_id": b1_obj.get("id"),
                        "t2_feature_id": b2.get("id"),
                        "area_delta_px": round(float(p2.area - p1_geom.area), 2),
                        "iou": round(float(max_iou), 3),
                        "confidence": round(float(min(b2.get("confidence", 0.8), b1_obj.get("confidence", 0.8))), 3),
                        "polygon": coords_2,
                        "status": "UNREVIEWED",
                        "description": f"Building footprint altered by {round(area_ratio * 100, 1)}%."
                    })

        # Check for demolished buildings in T1 not present in T2
        for b1 in bldgs_t1:
            b1_id = b1.get("id")
            if b1_id not in matched_t1_bldg_ids:
                coords_1 = b1.get("polygon", [])
                if len(coords_1) >= 3:
                    p1 = make_valid(Polygon(coords_1))
                    changes.append({
                        "change_id": f"chg_dem_{b1_id}",
                        "change_type": "STRUCTURE_REMOVAL",
                        "feature_class": "building",
                        "t1_feature_id": b1_id,
                        "t2_feature_id": None,
                        "area_delta_px": -round(float(p1.area), 2),
                        "confidence": round(float(b1.get("confidence", 0.8)), 3),
                        "polygon": coords_1,
                        "status": "UNREVIEWED",
                        "description": "Structure detected in baseline epoch is absent in current epoch."
                    })

        summary = {
            "t1_date": t1_date,
            "t2_date": t2_date,
            "total_changes_detected": len(changes),
            "new_constructions": sum(1 for c in changes if c["change_type"] == "NEW_CONSTRUCTION"),
            "modified_footprints": sum(1 for c in changes if c["change_type"] == "MODIFIED_FOOTPRINT"),
            "structure_removals": sum(1 for c in changes if c["change_type"] == "STRUCTURE_REMOVAL")
        }

        return {
            "changes": changes,
            "summary": summary
        }
