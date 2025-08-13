class ConnCalculator():
    """
    Connection Calculator for Screws in Aluminum Members.
    
    Parameters:
        t1 : float - Thickness of member in contact with screw head (mm)
        t2 : float - Thickness of member not in contact with screw head (mm)
        d : float - Nominal diameter of screw (mm)
        head_dia : float - Diameter of screw head (mm)
        d_pen : float - Screw penetration depth (mm)
        wind_load : float - Applied wind load (kN)
        dead_load : float - Applied dead load (kN)
        t1_grade : str - Material grade of the contact member
        t2_grade : str - Material grade of the non-contact member
    """
    
    def __init__(self, screw_config, t1, t2, t1_grade, t2_grade, 
                    dia, screw_length, head_dia, wind_load, dead_load):
        self.screw_config = screw_config
        self.t1 = t1
        self.t2 = t2
        self.dia = dia
        self.screw_length = screw_length
        self.head_dia = head_dia
        self.wind_load = wind_load
        self.dead_load = dead_load
        
        self.t1_grade = t1_grade
        self.t2_grade = t2_grade
        
        # derived properties
        self.factored_fy = wind_load * 1.6
        self.factored_fz = dead_load * 1.2
        
        self.F_y1, self.F_u1 = self.member_strength(t1_grade)
        self.F_y2, self.F_u2 = self.member_strength(t2_grade)
    
    def compute_params(self):
        return {
            "t1": self.t1,
            "t2": self.t2,
            "t1_grade": self.t1_grade,
            "t2_grade": self.t2_grade,
            "dia": self.dia,
            "screw_length": self.screw_length,
            "head_dia": self.head_dia,
            # "d_pen": self.d_pen,
            "F_u1": self.F_u1,
            "F_u2": self.F_u2,
            
            "wind_load": self.wind_load,
            "dead_load": self.dead_load,
            "factored_fy": round(self.factored_fy, 2),
            "factored_fz": round(self.factored_fz, 2),
            
            "n": self.design_load()["n"],
            "R_ya": round(self.design_load()["R_ya"], 2),
            "R_za": round(self.design_load()["R_za"], 2),
            "R_yb": round(self.design_load()["R_yb"], 2),
            "R_zb": round(self.design_load()["R_zb"], 2),
            "Vu": round(self.design_load()["Vu"], 2),
            "Tu": round(self.design_load()["Tu"], 2),
        }
    
    def member_strength(self, member_grade):
        strengths = {
            "6063-T5": (110, 150),
            "6063-T6": (172, 207),
            "6061-T6": (241, 262)
        }
        if member_grade not in strengths:
            raise ValueError(f"Unknown material grade: {member_grade}")
        return strengths[member_grade]
    
    def no_of_screw(self):
        options = { "Option 1": 2, "Option 2": 3, "Option 3": 4, "Option 4": 6 }
        if self.screw_config not in options:
            raise ValueError(f"Unknown screw configuration: {self.screw_config}")
        return options[self.screw_config]

    def design_load(self):
        n = self.no_of_screw()                      # no. of screw per side
        self.R_ya = self.factored_fy / n            # shear     # for screw A1, A2.. in transom
        self.R_za = self.factored_fz / n            # tension
        self.R_yb = self.factored_fy / n            # shear     # for screw B1, B2.. in mullion
        self.R_zb = self.factored_fz / n            # shear
        Vu = (self.R_yb**2 + self.R_zb**2)**0.5
        Tu = self.R_za
        
        return {
            "n": n,
            "R_ya": self.R_ya,
            "R_za": self.R_za,
            "R_yb": self.R_yb,
            "R_zb": self.R_zb,
            "Vu": Vu,
            "Tu": Tu
        }
    
    def compute_shear_tilting_bearing(self):
        phi = 0.5
        self.Vu = self.design_load()["Vu"]
        self.Tu = self.design_load()["Tu"]
        if self.t2 / self.t1 <= 1:
            P_nv1 = 4.2 * (self.t2**3 * self.dia)**0.5 * self.F_u2
            P_nv2 = 2.7 * self.t1 * self.dia * self.F_u1
            P_nv3 = 2.7 * self.t2 * self.dia * self.F_u2
            phi_P_nv = phi * min(P_nv1, P_nv2, P_nv3) / 1000    # 1000 to convert to kN
            ratio = self.Vu / phi_P_nv
        else:
            phi_P_nv = None     # calculate later
            ratio = None
        
        return {
            "phi": phi,
            "phi_P_nv": round(phi_P_nv, 2),
            "ratio": round(ratio, 2)
        }
    
    def compute_pullout_tension(self):
        phi = 0.5
        d_pen = min(self.screw_length, self.t2)
        tc = min(d_pen, self.t2)
        phi_P_not = phi * 0.85 * tc * self.dia * self.F_u2 / 1000
        ratio = self.Tu / phi_P_not

        return {
            "phi": phi,
            "tc": tc,
            "phi_P_not": round(phi_P_not, 2),
            "ratio": round(ratio, 2)
        }
    
    def compute_pullover_tension(self):
        phi = 0.5
        d_w_prime = min(self.head_dia, 19.1)
        phi_P_nov = phi * 1.5 * self.t1 * d_w_prime * self.F_u1 / 1000
        ratio = self.Tu / phi_P_nov

        return {
            "phi": phi,
            "d_w_prime": d_w_prime,
            "phi_P_nov": round(phi_P_nov, 2),
            "ratio": round(ratio, 2)
        }
    
    def compute_comb_shear_pullover(self):
        phi = 0.65
        P_nv = self.compute_shear_tilting_bearing()["phi_P_nv"] / phi
        P_nov = self.compute_pullover_tension()["phi_P_nov"] / phi
        beta = self.Vu / P_nv + 0.71 * self.Tu / P_nov
        
        return {
            "phi": phi,
            "P_nv": round(P_nv, 2),
            "P_nov": round(P_nov, 2),
            "beta": round(beta, 2)
        }
    
    def compute_comb_shear_pullout(self):
        phi = 0.6
        P_nv = self.compute_shear_tilting_bearing()["phi_P_nv"] / phi
        P_not = self.compute_pullout_tension()["phi_P_not"] / phi
        beta = self.Vu / P_nv + self.Tu / P_not
        
        return {
            "phi": phi,
            "P_nv": round(P_nv, 2),
            "P_not": round(P_not, 2),
            "beta": round(beta, 2)
        }
    
    def summary(self):
        return {
            "params": self.compute_params(),
            "shear_tilting": self.compute_shear_tilting_bearing(),
            "pullout_tension": self.compute_pullout_tension(),
            "pullover_tension": self.compute_pullover_tension(),
            "comb_shear_pullover": self.compute_comb_shear_pullover(),
            "comb_shear_pullout": self.compute_comb_shear_pullout()
        }



if __name__ == "__main__":
    conn = ConnCalculator("option 2", 3.5, 2.5, "6063-T6", "6063-T6", 4.8, 25, 10.5, 1.6, 0.57)
    summary = conn.summary()
    print(summary)