# from package import wind_parameters as wp
from .package import wind_parameters as wp


class WindLoadCalculator:
    def __init__(self, structure_type, b_type, enclosure_type, roof_type,
                    location, wind_speed, b_rigidity, b_freq, damping,
                    b_height, b_width, b_length, parapet_height,
                    exposure_cat, exposure_note, occupancy_cat, occupancy_note,
                    topography_type, topo_height, topo_length, topo_distance, topo_crest_side, topography_note,
                    floor_heights, eff_area, selected_levels):
        
        self.structure_type = structure_type
        self.b_type = b_type
        self.enclosure_type = enclosure_type
        self.roof_type = roof_type
        self.location = location
        self.wind_speed = wind_speed
        self.b_rigidity = b_rigidity
        self.b_freq = b_freq
        self.damping = damping
        self.b_height = b_height
        self.b_width = b_width
        self.b_length = b_length
        self.parapet_height = parapet_height
        self.exposure_cat = exposure_cat
        self.exposure_note = exposure_note
        # self.location_map = location_map
        self.occupancy_cat = occupancy_cat
        self.occupancy_note = occupancy_note
        self.topography_type = topography_type
        self.topo_height = topo_height
        self.topo_length = topo_length
        self.topo_distance = topo_distance
        self.topo_crest_side = topo_crest_side
        self.topography_note = topography_note
        self.floor_heights = floor_heights
        self.eff_area = eff_area
        self.selected_levels = selected_levels
        
        # Auto-derived
        self.cumu_heights = self.calculate_cumulative_heights()
        # self.facade_elev = self.get_facade_elev()
        
        self.K_ht = wp.topographic_factor(
            self.topography_type, self.topo_height, self.topo_length,
            self.topo_distance, self.b_height, self.exposure_cat, self.topo_crest_side
        )
        self.Imp = wp.importance_factor(self.occupancy_cat)
        self.K_d = wp.directionality_factor(self.structure_type)
        self.gust_factor = 0.85 if self.b_rigidity == "Rigid" else wp.gust_factor(
            self.b_height, self.b_length, self.b_width,
            self.wind_speed, self.b_freq, self.damping, self.exposure_cat
        )
        self.GC_pi = wp.internal_pressure_coeff(self.enclosure_type)
        self.C_pw, self.C_pl, self.C_ps = wp.external_pressure_coeff(
            self.b_length, self.b_width)
        self.q_zk = 0.000613 * self.K_d * self.wind_speed** 2 * self.Imp      # in terms of Kz Kzt


    def compute_params(self):
        return {
            "b_tstructure_typeype": self.structure_type,
            "b_type": self.b_type,
            "enclosure_type": self.enclosure_type,
            "roof_type": self.roof_type,
            "location": self.location,
            "wind_speed": self.wind_speed,
            "b_rigidity": self.b_rigidity,
            "b_freq": self.b_freq,
            "damping": self.damping,
            "b_height": self.b_height,
            "b_width": self.b_width,
            "b_length": self.b_length,
            "exposure_cat": self.exposure_cat,
            "exposure_note": self.exposure_note,
            "occupancy_cat": self.occupancy_cat,
            "occupancy_note": self.occupancy_note,
            "topography_type": self.topography_type,
            "topo_height": self.topo_height,
            "topo_length": self.topo_length,
            "topo_distance": self.topo_distance,
            "topo_crest_side": self.topo_crest_side,
            "topography_note": self.topography_note,
            "Imp": self.Imp,
            "K_d": self.K_d,
            "gust_factor": round(self.gust_factor, 2),
            "q_zk": round(self.q_zk, 2),
            "b_aspect_ratio": round(self.b_length / self.b_width, 2),
            "C_pl": round(self.C_pl, 2),
            "C_ps": round(self.C_ps, 2),
            "GC_pi": round(self.GC_pi, 2)
        }
    
    def calculate_cumulative_heights(self):
        cumu = 0
        cumu_heights = []
        for h in self.floor_heights:
            cumu += h
            cumu_heights.append(cumu)
        return cumu_heights

    def get_facade_elev(self, level):
        if 1 <= level <= len(self.cumu_heights):
            return self.cumu_heights[level - 1]
        raise ValueError("Invalid level")

    def compute_mwfrs_pressures(self):
        K_h = wp.velocity_pressure_coeff(self.exposure_cat, self.b_height, WFRS="MWFRS")
        q_h = 0.000613 * K_h * self.K_ht * self.K_d * self.wind_speed** 2 * self.Imp
        P_hi = q_h * self.GC_pi
        P_hl = q_h * self.gust_factor * self.C_pl - P_hi
        P_hs = q_h * self.gust_factor * self.C_ps - P_hi
        
        results = []
        for level, height in enumerate(self.floor_heights, start=1):
            cumu_height = self.cumu_heights[level - 1]
            K_z = wp.velocity_pressure_coeff(self.exposure_cat, cumu_height, WFRS="MWFRS")
            K_zt = wp.topographic_factor(
                self.topography_type, self.topo_height, self.topo_length,
                self.topo_distance, cumu_height, self.exposure_cat, self.topo_crest_side
            )
            q_z = self.q_zk * K_z * K_zt
            P_zw = q_z * self.gust_factor * self.C_pw + P_hi
            
            results.append({
                "level": level,
                "height": height,
                "cumu_height": round(cumu_height, 2),
                "K_z": round(K_z, 2),
                "K_zt": round(K_zt, 2),
                "q_z": round(q_z, 2),
                "P_zw": round(P_zw, 2)
            })
        return {
            "K_h": round(K_h, 2),
            "K_ht": round(self.K_ht, 2),
            "q_h": round(q_h, 2),
            "P_hi": round(P_hi, 2),
            "P_hl": round(P_hl, 2),
            "P_hs": round(P_hs, 2)
        }, results

    def compute_mwfrs_parapet_pressure(self):
        if self.parapet_height > 0:
            pp_height = self.b_height + self.parapet_height
        else:
            pp_height = 0
        
        K_p = wp.velocity_pressure_coeff(self.exposure_cat, pp_height, WFRS="MWFRS")
        K_pt = wp.topographic_factor(
            self.topography_type, self.topo_height, self.topo_length,
            self.topo_distance, pp_height, self.exposure_cat, self.topo_crest_side
        )
        q_p = self.q_zk * K_p * K_pt
        
        GC_pn_w = 1.5
        GC_pn_l = -1.0

        P_pw = q_p * GC_pn_w
        P_pl = q_p * GC_pn_l

        return {
            "height": self.parapet_height,
            "cumu_height": pp_height,
            "K_p": round(K_p, 2),
            "K_pt": round(K_pt, 2),
            "q_p": round(q_p, 2),
            "P_pw": round(P_pw, 2),
            "P_pl": round(P_pl, 2),
        }

    def compute_cladding_pressures(self, eff_area=None):
        wall_results, roof_results = {}, {}

        # Choose area list
        area_list = [eff_area] if eff_area is not None else self.eff_area

        for A_eff in area_list:
            GC_p_z4_pos, GC_p_z4_neg, GC_p_z5_pos, GC_p_z5_neg = wp.ext_pressure_coeff_wall_cladd(A_eff)
            GC_p_z1_neg, GC_p_z2_neg, GC_p_z3_neg = wp.ext_pressure_coeff_roof_cladd(A_eff)

            wall_rows = []
            roof_rows = []

            for level in self.selected_levels:
                if level > len(self.cumu_heights):
                    continue

                height = self.cumu_heights[level - 1]
                K_z = wp.velocity_pressure_coeff(self.exposure_cat, height, WFRS="C&C")
                K_zt = wp.topographic_factor(
                    self.topography_type, self.topo_height, self.topo_length,
                    self.topo_distance, height, self.exposure_cat, self.topo_crest_side
                )
                q_z = self.q_zk * K_z * K_zt
                P_zi = q_z * self.GC_pi

                wall_rows.append({
                    "level": level,
                    "A_eff": A_eff,
                    "height": round(height, 2),
                    "K_z": round(K_z, 2),
                    "K_zt": round(K_zt, 2),
                    "q_z": round(q_z, 2),
                    "P_zi": round(P_zi, 2),
                    "P_z4_pos": round(q_z * GC_p_z4_pos + P_zi, 2),
                    "P_z4_neg": round(q_z * GC_p_z4_neg - P_zi, 2),
                    "P_z5_pos": round(q_z * GC_p_z5_pos + P_zi, 2),
                    "P_z5_neg": round(q_z * GC_p_z5_neg - P_zi, 2),
                })

                roof_rows.append({
                    "level": level,
                    "A_eff": A_eff,
                    "height": round(height, 2),
                    "K_z": round(K_z, 2),
                    "K_zt": round(K_zt, 2),
                    "q_z": round(q_z, 2),
                    "P_zi": round(P_zi, 2),
                    "P_z1_neg": round(q_z * GC_p_z1_neg - P_zi, 2),
                    "P_z2_neg": round(q_z * GC_p_z2_neg - P_zi, 2),
                    "P_z3_neg": round(q_z * GC_p_z3_neg - P_zi, 2),
                })

            wall_results[A_eff] = wall_rows
            roof_results[A_eff] = roof_rows

        return wall_results, roof_results

    def summary(self):
        mwfrs_h, mwfrs_z = self.compute_mwfrs_pressures()
        wall, roof = self.compute_cladding_pressures()
        return {
            "params": self.compute_params(),
            "mwfrs": {
                "mwfrs_h": mwfrs_h,
                "mwfrs_z": mwfrs_z
            },
            "parapet": self.compute_mwfrs_parapet_pressure(),
            "cladding": {
                "wall": wall,
                "roof": roof
            }
        }

    
    def get_cladding_pressure(self, effective_area, elevation, zone):
        cladding_type = "wall" if zone in ["Zone 4", "Zone 5"] else "roof"

        wall_results, roof_results = self.compute_cladding_pressures(eff_area=effective_area)
        target_results = wall_results if cladding_type == "wall" else roof_results

        area_results = target_results.get(effective_area)

        if not area_results:
            raise ValueError(f"No pressure data computed for area {effective_area:.2f} m²")

        # Loop through all rows (1 per level), and pick one with closest height
        closest_row = min(area_results, key=lambda row: abs(row["height"] - elevation))

        # Get pressure based on zone
        if cladding_type == "wall":
            if zone == "Zone 4":
                return max(abs(closest_row["P_z4_pos"]), abs(closest_row["P_z4_neg"]))
            elif zone == "Zone 5":
                return max(abs(closest_row["P_z5_pos"]), abs(closest_row["P_z5_neg"]))
            else:
                raise ValueError(f"Unsupported wall zone: {zone}")
        elif cladding_type == "roof":
            if zone == "Zone 1":
                return abs(closest_row["P_z1_neg"])
            elif zone == "Zone 2":
                return abs(closest_row["P_z2_neg"])
            elif zone == "Zone 3":
                return abs(closest_row["P_z3_neg"])
            else:
                raise ValueError(f"Unsupported roof zone: {zone}")

        raise ValueError(f"Invalid cladding type {cladding_type} or zone {zone}")

