import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import networkx as nx
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from shapely.ops import nearest_points

class AccessPathService:
    """
    Part 4: Access Path Intelligence & Parcel Accessibility Engine.
    Converts detected road polygons into a topological network graph (via NetworkX)
    and evaluates physical parcel frontage and connectivity.
    
    IMPORTANT: Strictly distinguishes physical road proximity from legal rights-of-way / easements.
    """

    DIRECT_ACCESS_THRESHOLD_PX = 15.0   # Pixels proximity to be considered direct frontage
    MARGINAL_ACCESS_THRESHOLD_PX = 60.0 # Pixels proximity for secondary marginal access

    def __init__(self):
        self.graph = nx.Graph()

    def build_road_network(self, road_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds a topological NetworkX graph from road polygons/centerlines.
        """
        self.graph.clear()
        road_segments: List[LineString] = []

        for idx, feat in enumerate(road_features):
            poly_coords = feat.get("polygon", [])
            if len(poly_coords) >= 3:
                poly = Polygon(poly_coords)
                # Extract exterior ring segments or centerline approximation
                exterior_coords = list(poly.exterior.coords)
                for i in range(len(exterior_coords) - 1):
                    p1 = exterior_coords[i]
                    p2 = exterior_coords[i + 1]
                    segment = LineString([p1, p2])
                    if segment.length > 5.0:
                        road_segments.append(segment)
                        u = (round(p1[0], 1), round(p1[1], 1))
                        v = (round(p2[0], 1), round(p2[1], 1))
                        dist = float(segment.length)
                        self.graph.add_edge(u, v, weight=dist, road_id=feat.get("id", f"road_{idx}"))

        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "connected_components": nx.number_connected_components(self.graph) if self.graph.number_of_nodes() > 0 else 0,
            "total_network_length_px": round(sum(d.get("weight", 0) for _, _, d in self.graph.edges(data=True)), 2),
            "segments_count": len(road_segments)
        }

    def evaluate_parcel_access(
        self,
        parcel_polygon: Polygon,
        road_segments: List[LineString]
    ) -> Dict[str, Any]:
        """
        Evaluates physical access for a given parcel polygon against road segments.
        """
        if not road_segments or parcel_polygon.is_empty:
            return {
                "access_status": "PHYSICAL_ACCESS_CONCERN",
                "direct_frontage": False,
                "frontage_length_px": 0.0,
                "distance_to_road_px": 9999.0,
                "nearest_access_point": None,
                "legal_disclaimer": "Physical observation only; does not establish legal right-of-way or easement."
            }

        min_dist = float("inf")
        best_pt_parcel = None
        best_pt_road = None
        frontage_length = 0.0

        for seg in road_segments:
            dist = parcel_polygon.distance(seg)
            if dist < min_dist:
                min_dist = dist
                p_parcel, p_road = nearest_points(parcel_polygon, seg)
                best_pt_parcel = [round(p_parcel.x, 2), round(p_parcel.y, 2)]
                best_pt_road = [round(p_road.x, 2), round(p_road.y, 2)]

            # Check for shared frontage or immediate proximity
            if dist <= self.DIRECT_ACCESS_THRESHOLD_PX:
                # Approximate frontage contact length by intersection of buffered parcel boundary
                buffered = parcel_polygon.exterior.buffer(self.DIRECT_ACCESS_THRESHOLD_PX)
                inter = buffered.intersection(seg)
                if not inter.is_empty:
                    frontage_length += float(inter.length)

        if min_dist <= self.DIRECT_ACCESS_THRESHOLD_PX:
            status = "DIRECT_ACCESS"
        elif min_dist <= self.MARGINAL_ACCESS_THRESHOLD_PX:
            status = "MARGINAL_ACCESS"
        else:
            status = "PHYSICAL_ACCESS_CONCERN"

        return {
            "access_status": status,
            "direct_frontage": (status == "DIRECT_ACCESS"),
            "frontage_length_px": round(frontage_length, 2),
            "distance_to_road_px": round(min_dist, 2),
            "nearest_access_point": best_pt_road,
            "parcel_contact_point": best_pt_parcel,
            "legal_disclaimer": "Physical observation only; does not establish legal right-of-way or easement."
        }

    def analyze_all_parcels(
        self,
        parcels: List[Dict[str, Any]],
        road_features: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Runs accessibility analysis over a collection of parcels and adds physical access attributes.
        """
        self.build_road_network(road_features)
        road_lines: List[LineString] = []
        for feat in road_features:
            coords = feat.get("polygon", [])
            if len(coords) >= 3:
                poly = Polygon(coords)
                road_lines.append(poly.exterior)

        analyzed_parcels = []
        for parcel in parcels:
            coords = parcel.get("polygon", [])
            if len(coords) >= 3:
                p_poly = Polygon(coords)
                eval_res = self.evaluate_parcel_access(p_poly, road_lines)
                updated_parcel = dict(parcel)
                updated_parcel["accessibility"] = eval_res
                analyzed_parcels.append(updated_parcel)
            else:
                analyzed_parcels.append(parcel)

        return analyzed_parcels
