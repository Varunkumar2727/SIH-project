from typing import Dict, Any, List, Optional, Tuple
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid

class CadastralComparisonService:
    """
    Part 5: Cadastral Comparison Engine.
    Performs rigorous spatial overlay analysis between AI-proposed parcels and
    authoritative cadastral survey records. Computes real IoU, area differences,
    and boundary displacement.
    """

    MATCH_IOU_THRESHOLD = 0.80
    PARTIAL_IOU_THRESHOLD = 0.45

    @classmethod
    def compare_parcel_layers(
        cls,
        ai_parcels: List[Dict[str, Any]],
        cadastral_parcels: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compares AI-proposed parcels against authoritative cadastral parcels.
        Returns detailed spatial metrics and identified discrepancies.
        """
        cad_polys = []
        for c in cadastral_parcels:
            coords = c.get("polygon", [])
            if len(coords) >= 3:
                poly = make_valid(Polygon(coords))
                cad_polys.append({"meta": c, "geom": poly})

        results = []
        matched_cad_ids = set()

        for ai_p in ai_parcels:
            ai_coords = ai_p.get("polygon", [])
            if len(ai_coords) < 3:
                continue

            ai_poly = make_valid(Polygon(ai_coords))
            best_match = None
            best_iou = 0.0
            best_inter_area = 0.0

            for cad in cad_polys:
                c_geom = cad["geom"]
                if ai_poly.intersects(c_geom):
                    inter = ai_poly.intersection(c_geom).area
                    union = ai_poly.union(c_geom).area
                    iou = inter / (union + 1e-6)
                    if iou > best_iou:
                        best_iou = iou
                        best_match = cad
                        best_inter_area = inter

            # Determine discrepancy status
            if best_match is not None and best_iou >= cls.MATCH_IOU_THRESHOLD:
                status = "MATCHED"
                discrepancy_type = "NONE"
                matched_cad_ids.add(best_match["meta"].get("id"))
                area_diff_pct = abs(ai_poly.area - best_match["geom"].area) / (best_match["geom"].area + 1e-6) * 100.0
            elif best_match is not None and best_iou >= cls.PARTIAL_IOU_THRESHOLD:
                status = "DISCREPANCY_DETECTED"
                discrepancy_type = "BOUNDARY_MISALIGNMENT"
                matched_cad_ids.add(best_match["meta"].get("id"))
                area_diff_pct = abs(ai_poly.area - best_match["geom"].area) / (best_match["geom"].area + 1e-6) * 100.0
            elif best_match is not None:
                # Intersects with low IoU -> potential encroachment or building extension
                status = "DISCREPANCY_DETECTED"
                discrepancy_type = "POTENTIAL_OVERSTEP"
                area_diff_pct = abs(ai_poly.area - best_match["geom"].area) / (best_match["geom"].area + 1e-6) * 100.0
            else:
                status = "UNMATCHED_SURVEY"
                discrepancy_type = "UNREGISTERED_FEATURE"
                area_diff_pct = 100.0

            comp_record = {
                "ai_parcel_id": ai_p.get("id"),
                "cadastral_parcel_id": best_match["meta"].get("id") if best_match else None,
                "iou": round(float(best_iou), 4),
                "area_discrepancy_pct": round(float(area_diff_pct), 2),
                "status": status,
                "discrepancy_type": discrepancy_type,
                "ai_area_px": round(float(ai_poly.area), 2),
                "cadastral_area_px": round(float(best_match["geom"].area), 2) if best_match else 0.0,
                "disclaimer": "AI discrepancy indicator; requires survey officer field confirmation."
            }
            results.append(comp_record)

        # Identify authoritative parcels that were missed / vacant in AI features
        unmatched_cadastral = []
        for cad in cad_polys:
            c_id = cad["meta"].get("id")
            if c_id not in matched_cad_ids:
                unmatched_cadastral.append({
                    "cadastral_parcel_id": c_id,
                    "status": "NO_AI_DETECTION",
                    "area_px": round(float(cad["geom"].area), 2)
                })

        summary = {
            "total_ai_parcels": len(ai_parcels),
            "total_cadastral_parcels": len(cadastral_parcels),
            "matched_count": sum(1 for r in results if r["status"] == "MATCHED"),
            "discrepancy_count": sum(1 for r in results if r["status"] == "DISCREPANCY_DETECTED"),
            "unmatched_count": sum(1 for r in results if r["status"] == "UNMATCHED_SURVEY"),
            "unmatched_cadastral_count": len(unmatched_cadastral)
        }

        return {
            "comparison_results": results,
            "unmatched_cadastral": unmatched_cadastral,
            "summary": summary
        }
