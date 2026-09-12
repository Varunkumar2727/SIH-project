from typing import Dict, Any, List, Optional
import math

class HotspotAnalysisService:
    """
    Part 9: Spatial Hotspot Clustering.
    Identifies geographic clusters of discrepancies, changes, and physical access concerns
    using spatial binning and density metrics.
    """

    @classmethod
    def identify_hotspots(
        cls,
        items: List[Dict[str, Any]],
        grid_size_px: float = 200.0,
        min_cluster_size: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Groups spatial points/polygons into geographic density clusters.
        """
        bins: Dict[str, List[Dict[str, Any]]] = {}

        for item in items:
            coords = item.get("polygon") or item.get("nearest_access_point")
            if not coords:
                continue

            # Extract center of mass or first point
            if isinstance(coords[0], list):
                cx = sum(p[0] for p in coords) / len(coords)
                cy = sum(p[1] for p in coords) / len(coords)
            else:
                cx, cy = coords[0], coords[1]

            bin_x = int(cx // grid_size_px)
            bin_y = int(cy // grid_size_px)
            bin_key = f"{bin_x}_{bin_y}"

            if bin_key not in bins:
                bins[bin_key] = []
            bins[bin_key].append({
                "id": item.get("id") or item.get("change_id") or item.get("ai_parcel_id"),
                "cx": cx,
                "cy": cy,
                "raw": item
            })

        hotspots = []
        for b_key, cluster_members in bins.items():
            if len(cluster_members) >= min_cluster_size:
                avg_x = sum(m["cx"] for m in cluster_members) / len(cluster_members)
                avg_y = sum(m["cy"] for m in cluster_members) / len(cluster_members)
                hotspots.append({
                    "cluster_id": f"hotspot_{b_key}",
                    "item_count": len(cluster_members),
                    "centroid_px": [round(avg_x, 2), round(avg_y, 2)],
                    "item_ids": [m["id"] for m in cluster_members],
                    "density_level": "HIGH" if len(cluster_members) >= 5 else "MODERATE"
                })

        return sorted(hotspots, key=lambda x: x["item_count"], reverse=True)
