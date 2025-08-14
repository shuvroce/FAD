from .package.fixing_base import AnchorCalculator, BasePlateCalculator, FinPlateCalculator

class BoxClumpCalculator():
    def __init__(self, wind_load=30.0, dead_load=8.0, wind_ecc=0, dead_ecc=0,
                    bp_length=250, bp_width=120, steel_grade="A572 Gr. 50",
                    profile_depth=110, profile_width=80, n_anchor=4, anchor_dia=12, embed_depth=70,
                    anchor_grade="Grade 5.8", install_type="post-installed",
                    conc_grade="M25", conc_condition="cracked", conc_weight_type="normal",
                    conc_depth=300, conc_Np5=20, ed1=50, ed2=50, C_a1=100, C_b1=100, C_a2=200, C_b2=200):
        
        self.wind_load = wind_load
        self.dead_load = dead_load
        self.wind_ecc = wind_ecc
        self.dead_ecc = dead_ecc
        self.bp_length = bp_length
        self.bp_width = bp_width
        self.steel_grade = steel_grade
        self.profile_depth = profile_depth
        self.profile_width = profile_width
        self.n_anchor = n_anchor
        self.anchor_dia = anchor_dia
        self.embed_depth = embed_depth
        self.anchor_grade = anchor_grade
        self.install_type = install_type
        self.conc_grade = conc_grade
        self.conc_condition = conc_condition
        self.conc_weight_type = conc_weight_type
        self.conc_depth = conc_depth
        self.conc_Np5 = conc_Np5
        self.ed1 = ed1
        self.ed2 = ed2
        self.C_a1 = C_a1
        self.C_b1 = C_b1
        self.C_a2 = C_a2
        self.C_b2 = C_b2

        # Derived properties
        self.R_y = self.wind_load
        self.R_z = self.dead_load
        self.s1 = self.bp_length - 2 * self.ed1
        self.s2 = self.bp_width - 2 * self.ed2
        
        self.N_ua, self.N_ug, self.V_ua, self.V_ug = self.compute_anchor_load()

    def compute_params(self):
        pass

    def compute_anchor_load(self):
        n_N = 4 if self.n_anchor == 4 else 2
        n_V = 2
        if self.R_z > 0:
            N_ua = self.R_z / self.n_anchor
            N_ug = N_ua * n_N
        else:
            N_ua = 0
            N_ug = 0
        V_ua = self.R_y / self.n_anchor
        V_ug = V_ua * n_V
        return round(N_ua, 2), round(N_ug, 2), round(V_ua, 2), round(V_ug, 2)


    def compute_conc_failure_area_tension(self):
        hxa = min(1.5 * self.embed_depth, self.C_a1)
        hxb = min(1.5 * self.embed_depth, self.C_b1)
        if self.n_anchor == 2:
            A_NC = (3 * self.embed_depth + self.s1) * (hxa + hxb)
        else:
            A_NC = (3 * self.embed_depth + self.s1) * (hxa + self.s2 + hxb)
        return round(A_NC, 2)


    def compute_conc_failure_area_shear(self):      #A_VC
        Cx = min(1.5 * self.C_a1, self.conc_depth)
        return round((3 * self.C_a1 + self.s1) * Cx, 2)


    def compute_box_clump(self):
        A_NC = self.compute_conc_failure_area_tension()
        A_VC = self.compute_conc_failure_area_shear()
        
        self.anchor = AnchorCalculator(
            self.N_ua, self.N_ug, self.V_ua, self.V_ug, self.wind_ecc, self.dead_ecc,
            A_NC, A_VC, self.bp_length, self.bp_width, self.profile_depth, self.profile_width, self.steel_grade,
            self.n_anchor, self.anchor_dia, self.embed_depth, self.anchor_grade, self.install_type,
            self.conc_grade, self.conc_condition, self.conc_weight_type, self.conc_depth, self.conc_Np5,
            self.ed1, self.ed2, self.C_a1, self.C_b1, self.C_a2, self.C_b2
        )
        self.bp = BasePlateCalculator(
            self.dead_load, 0, self.bp_length, self.bp_width, self.profile_depth,
            self.profile_width, self.steel_grade, self.conc_grade, self.ed1, self.ed2
        )
        return self
    
    
    def summary(self):
        return {
            "params": self.compute_params(),
            "steel_strength_tension": self.anchor.steel_strength_tension(),
            "concrete_breakout_tension": self.anchor.concrete_breakout_tension(),
            "pullout_strength_tension": self.anchor.pullout_strength_tension(),
            "steel_strength_shear": self.anchor.steel_strength_shear(),
            "concrete_breakout_shear": self.anchor.concrete_breakout_shear(),
            "pryout_strength_shear": self.anchor.pryout_strength_shear(),
            "anchor_interaction": self.anchor.anchor_interaction(),
            "anchor_torque": self.anchor.anchor_torque(),
            "bp_thk_bearing": self.bp.bp_thk_bearing(),
            "bp_thk_pro": self.bp.bp_thk_pro(),
            "bp_area": self.bp.req_bp_area(self.bp_length),
            "conc_bearing_stress": self.bp.conc_bearing_stress()
        }



class UClumpCalculator(BoxClumpCalculator):
    def __init__(self, wind_load=30.0, dead_load=8.0, wind_ecc=0, dead_ecc=0, bp_length=250, bp_width=120,
                    fin_length=130, fin_width=120, fin_distance=80, steel_grade="A572 Gr. 50",
                    n_anchor=4, anchor_dia=12, embed_depth=70, anchor_grade="Grade 5.8", install_type="post-installed",
                    conc_grade="M25", conc_condition="cracked", conc_weight_type="normal", conc_depth=300, conc_Np5=20,
                    n_bolt=2, bolt_dia=10, bolt_grade="SS A4-70", weld_grade="E70xx", leg_length=5,
                    ed1=50, ed2=50, C_a1=100, C_b1=100, C_a2=200, C_b2=200,  ed1_f=35, ed2_f=35):
        super().__init__(wind_load, dead_load, wind_ecc, dead_ecc, bp_length, bp_width, steel_grade, fin_width, fin_distance,
                    n_anchor, anchor_dia, embed_depth, anchor_grade, install_type, conc_grade, conc_condition,
                    conc_weight_type, conc_depth, conc_Np5, ed1, ed2, C_a1, C_b1, C_a2, C_b2)
        
        self.fin_length = fin_length
        self.fin_width = fin_width
        self.fin_distance = fin_distance
        self.n_bolt = n_bolt
        self.bolt_dia = bolt_dia
        self.bolt_grade = bolt_grade
        self.weld_grade = weld_grade
        self.leg_length = leg_length
        self.ed1_f = ed1_f
        self.ed2_f = ed2_f
        
        # Derived properties
        self.N_ua, self.N_ug, self.V_ua, self.V_ug = self.compute_anchor_load()

    def compute_params(self):
        pass
    
    
    def compute_anchor_load(self):      # recheck, consider dead load eccentricity
        n_N = 4 if self.n_anchor == 4 else 2
        n_V = 2
        N_ua = self.R_y / self.n_anchor
        V_ua = self.R_z / self.n_anchor
        N_ug = N_ua * n_N
        V_ug = V_ua * n_V
        return round(N_ua, 2), round(N_ug, 2), round(V_ua, 2), round(V_ug, 2)


    def compute_u_clump(self):
        self.fin = FinPlateCalculator(
            self.wind_load, self.dead_load, self.dead_ecc, self.fin_length, self.fin_width,
            self.fin_distance, self.steel_grade, self.n_bolt, self.bolt_dia, self.bolt_grade,
            self.ed1_f, self.ed2_f, self.weld_grade, self.leg_length
        )
        super().compute_box_clump()
        return self
    
    def summary(self):
        base_summary = super().summary()
        base_summary.update({
            "params": self.compute_params(),
            "fin_thk": self.fin.fin_plate_thk(),
            "fin_shear_yield": self.fin.fin_plate_shear_strength_yield(),
            "fin_shear_rupture": self.fin.fin_plate_shear_strength_rupture(),
            "fin_block_shear": self.fin.fin_plate_block_shear_strength(),
            "fin_weld": self.fin.fin_weld_resistance(),
            "bolt_shear": self.fin.bolt_shear_resistance(),
            "bolt_bearing": self.fin.bolt_bearing_resistance(),
            "bolt_torque": self.fin.bolt_torque(),
            "bp_thk_tension": self.bp.bp_thk_tension(),
        })
        return base_summary



if __name__ == "__main__":
    box = BoxClumpCalculator()
    u = UClumpCalculator()
    box.compute_box_clump()
    u.compute_u_clump()
    
    summary = u.summary()
    print(summary)