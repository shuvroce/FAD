# import material_properties as mp
import package.material_properties as mp
import math

PI = math.pi
inf = 1e10

class AnchorCalculator():
    def __init__(self, N_ua, N_ug, V_ua, V_ug, tension_ecc, shear_ecc,
                    A_NC, A_VC, bp_length, bp_width, profile_depth, profile_width, steel_grade,
                    n_anchor, anchor_dia, embed_depth, anchor_grade, install_type,
                    conc_grade, conc_condition, conc_weight_type, conc_depth, conc_Np5,
                    ed1, ed2, C_a1, C_b1, C_a2, C_b2):
        
        self.N_ua = N_ua
        self.N_ug = N_ug
        self.V_ua = V_ua
        self.V_ug = V_ug
        self.tension_ecc = tension_ecc
        self.shear_ecc = shear_ecc
        self.A_NC = A_NC
        self.A_VC = A_VC
        self.bp_length = bp_length
        self.bp_width = bp_width
        self.profile_depth = profile_depth
        self.profile_width = profile_width
        self.steel_grade = steel_grade
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
        
        # derived properties
        self.s1 = self.bp_length - 2 * self.ed1
        self.s2 = self.bp_width - 2 * self.ed2
        
        self.C_amin = min(self.C_a1, self.C_a2, self.C_b1, self.C_b2)
        self.anchor_fy, self.anchor_fu = mp.bolt_strength(self.anchor_grade)
        self.steel_fy, self.steel_fu = mp.steel_strength(self.steel_grade)
        self.f_c = mp.concrete_strength(self.conc_grade)
        self.A_seN = mp.eff_tensile_area(self.anchor_dia)
        self.f_uta = min(860, 1.9 * self.anchor_fy, self.anchor_fu)
        self.anchor_head_dia = self.anchor_dia * 1.7
        self.A_brg = (PI / 4) * self.anchor_head_dia**2

    def steel_strength_tension(self):
        phi = 0.75
        phi_N_sa = phi * self.A_seN * self.f_uta / 1000
        ratio = self.N_ua / phi_N_sa
        
        return {
            "phi": phi,
            "A_seN": round(self.A_seN, 2),
            "f_uta": round(self.f_uta, 2),
            "phi_N_sa": round(phi_N_sa, 2),
            "N_ua": round(self.N_ua, 2),
            "ratio": round(ratio, 2)
        }
    
    def concrete_breakout_tension(self):
        phi, k_c = (0.7, 10) if self.install_type == "cast-in" else (0.65, 7)
        A_NCO = 9 * self.embed_depth**2

        psi_ecN = 1 / (1 + ((2 * self.tension_ecc) / (3 * self.embed_depth)))
        psi_edN = min(0.7 + ((0.3 * self.C_amin) / (1.5 * self.embed_depth)), 1)

        if self.conc_condition == "uncracked":
            psi_cN = 1.25 if self.install_type == "cast-in" else 1.4
        else:
            psi_cN = 1.0

        psi_cpN = 1.0  # factor for spliting
        self.lamda = 1.0 if self.conc_weight_type == "normal" else 0.75
        N_b = k_c * self.lamda * self.f_c**0.5 * self.embed_depth**1.5
        phi_N_cbg = phi * (self.A_NC / A_NCO) * psi_ecN * psi_edN * psi_cN * psi_cpN * N_b / 1000
        ratio = self.N_ug / phi_N_cbg

        return {
            "phi": phi,
            "A_NC": round(self.A_NC, 2),
            "A_NCO": round(A_NCO, 2),
            "C_amin": round(self.C_amin, 2),
            "psi_ecN": round(psi_ecN, 2),
            "psi_edN": round(psi_edN, 2),
            "psi_cN": round(psi_cN, 2),
            "psi_cpN": round(psi_cpN, 2),
            "k_c": round(k_c, 2),
            "lamda": round(self.lamda, 2),
            "N_b": round(N_b, 2),
            "phi_N_cbg": round(phi_N_cbg, 2),
            "N_ug": round(self.N_ug, 2),
            "ratio": round(ratio, 2)
        }
    
    def pullout_strength_tension(self):
        phi = 0.7
        psi_cp = 1.0 if self.conc_condition == "cracked" else 1.4
        if self.install_type == "cast-in":
            N_p = 8 * self.A_brg * self.f_c
        else:
            N_p = self.conc_Np5 * 1000  # Convert kN to N
        phi_N_pn = phi * psi_cp * N_p / 1000
        ratio = self.N_ua / phi_N_pn
        
        return {
            "phi": phi,
            "psi_cp": round(psi_cp, 2),
            "A_brg": round(self.A_brg, 2),
            "N_p": round(N_p, 2),
            "phi_N_pn": round(phi_N_pn, 2),
            "N_ua": round(self.N_ua, 2),
            "ratio": round(ratio, 2)
        }
    
    def sideface_blowout_tension(self):
        phi = 0.7
        N_sb = (13 * self.C_a1 * self.A_brg**0.5) * self.lamda * self.f_c**0.5
        phi_N_sbg = phi * (1 + (self.s1 / (6 * self.C_a1))) * N_sb / 1000
        ratio = self.N_ug / phi_N_sbg
        
        return {
            "phi": phi,
            "lamda": round(self.lamda, 2),
            "A_brg": round(self.A_brg, 2),
            "N_sb": round(N_sb, 2),
            "phi_N_sbg": round(phi_N_sbg, 2),
            "N_ug": round(self.N_ug, 2),
            "ratio": round(ratio, 2)
        }
    
    def steel_strength_shear(self):
        phi = 0.65
        phi_V_sa = phi * 0.6 * self.A_seN * self.f_uta / 1000
        ratio = self.V_ua / phi_V_sa
        
        return {
            "phi": phi,
            "A_seV": round(self.A_seN, 2),
            "f_uta": round(self.f_uta, 2),
            "phi_V_sa": round(phi_V_sa, 2),
            "V_ua": round(self.V_ua, 2),
            "ratio": round(ratio, 2)
        }
    
    def concrete_breakout_shear(self):
        phi = 0.7
        A_VCO = 4.5 * self.C_a1**2
        psi_ecV = 1 / (1 + ((2 * self.shear_ecc) / (3 * self.C_a1)))
        psi_edV = min(0.7 + ((0.3 * self.C_a2) / (1.5 * self.C_a1)), 1)
        psi_cV = 1.0 if self.conc_condition == "cracked" else 1.4
        psi_hV = max(((1.5 * self.C_a1) / self.conc_depth) ** 0.5, 1)
        lamda = 1.0 if self.conc_weight_type == "normal" else 0.75
        l_e = min(self.embed_depth, 8 * self.anchor_dia)
        V_b = 0.6 * ((l_e / self.anchor_dia) ** 0.2) * lamda * (self.anchor_dia * self.f_c) ** 0.5 * (self.C_a1**1.5)
        phi_V_cbg = phi * (self.A_VC / A_VCO) * psi_ecV * psi_edV * psi_cV * psi_hV * V_b / 1000
        ratio = self.V_ug / phi_V_cbg
        
        return {
            "phi": phi,
            "A_VC": round(self.A_VC, 2),
            "A_VCO": round(A_VCO, 2),
            "C_a1": round(self.C_a1, 2),
            "C_a2": round(self.C_a2, 2),
            "conc_depth": round(self.conc_depth, 2),
            "psi_ecV": round(psi_ecV, 2),
            "psi_edV": round(psi_edV, 2),
            "psi_cV": round(psi_cV, 2),
            "psi_hV": round(psi_hV, 2),
            "l_e": round(l_e, 2),
            "V_b": round(V_b, 2),
            "phi_V_cbg": round(phi_V_cbg, 2),
            "V_ug": round(self.V_ug, 2),
            "ratio": round(ratio, 2)
        }
    
    def pryout_strength_shear(self):
        phi = 0.7
        phi_t = 0.7 if self.install_type == "cast-in" else 0.65
        k_cp = 1.0 if self.embed_depth < 65 else 2.0
        N_cp = self.concrete_breakout_shear()["phi_V_cbg"] / phi_t
        phi_V_cp = phi * k_cp * N_cp
        ratio = self.V_ug / phi_V_cp
        
        return {
            "phi": phi,
            "k_cp": round(k_cp, 2),
            "N_cp": round(N_cp, 2),
            "phi_V_cp": round(phi_V_cp, 2),
            "V_ug": round(self.V_ug, 2),
            "ratio": round(ratio, 2)
        }
    
    def anchor_interaction(self):
        zeta = 1.67
        tension_ratios = [
            self.steel_strength_tension()["ratio"],
            self.concrete_breakout_tension()["ratio"],
            self.pullout_strength_tension()["ratio"],
            self.sideface_blowout_tension()["ratio"]
        ]
        shear_ratios = [
            self.steel_strength_shear()["ratio"],
            self.concrete_breakout_shear()["ratio"],
            self.pryout_strength_shear()["ratio"]
        ]
        beta_N = max(tension_ratios)
        beta_V = max(shear_ratios)
        beta = beta_N**zeta + beta_V**zeta
        beta_u = 1.0 if (beta_N < 0.2 or beta_V < 0.2) else 1.2

        return {
            "beta_N": round(beta_N, 2),
            "beta_V": round(beta_V, 2),
            "zeta": round(zeta, 2),
            "beta": round(beta, 2),
            "beta_u": round(beta_u, 2)
        }

    def anchor_torque(self):
        nut_factor = 0.2
        proof_strength = 0.9 * self.anchor_fy
        pre_load = 0.75 * proof_strength * self.A_seN
        torque = nut_factor * self.anchor_dia * pre_load
        
        return {
            "nut_factor": round(nut_factor, 2),
            "anchor_dia": round(self.anchor_dia, 2),
            "proof_strength": round(proof_strength, 2),
            "A_seN": round(self.A_seN, 2),
            "pre_load": round(pre_load, 2),
            "torque": round(torque, 2)
        }


class BasePlateCalculator():
    def __init__(self, compression_load, tension_load, bp_length, bp_width,
                    profile_depth, profile_width, steel_grade, conc_grade, ed1, ed2):

        self.compression_load = compression_load
        self.tension_load = tension_load
        self.bp_length = bp_length
        self.bp_width = bp_width
        self.profile_depth = profile_depth
        self.profile_width = profile_width
        self.steel_grade = steel_grade
        self.conc_grade = conc_grade
        self.ed1 = ed1
        self.ed2 = ed2
        
        # derived properties
        self.steel_fy, self.steel_fu = mp.steel_strength(self.steel_grade)
        self.f_c = mp.concrete_strength(self.conc_grade)

    def bp_thk_bearing(self):
        phi = 0.9
        # m, n is different for I, HSS. consider this too
        m = (self.bp_length - 0.95 * self.profile_depth) / 2
        n = (self.bp_width - 0.8 * self.profile_width) / 2
        lamda = 1.0
        lamda_n = lamda * (((self.profile_depth * self.profile_width)**0.5) / 4)
        l_c = max(m, n, lamda_n)
        A_p = self.bp_length * self.bp_width     # effective plate area (mm^2)
        q = self.compression_load / self.bp_length
        Mu = q * l_c**2 / 2
        self.t_br = l_c * ((2 * self.compression_load) / (phi * self.steel_fy * A_p))**0.5

        return {
            "phi": phi,
            "bp_length": round(self.bp_length, 2),
            "bp_width": round(self.bp_width, 2),
            "A_p": round(A_p, 2),
            "profile_depth": round(self.profile_depth, 2),
            "profile_width": round(self.profile_width, 2),
            "m": round(m, 2),
            "n": round(n, 2),
            "lamda_n": round(lamda_n, 2),
            "l_c": round(l_c, 2),
            "compression_load": round(self.compression_load, 2),
            "q": round(q, 2),
            "Mu": round(Mu, 2),
            "steel_fy": round(self.steel_fy, 2),
            "t": round(self.t_br, 2)
        }
    
    def bp_thk_tension(self):
        phi = 0.9
        x = ((self.bp_length - self.profile_depth) / 2) - self.ed1     # anchor center to flange edge distance (mm)
        Mu = (self.tension_load * 1000) * x
        if self.ed2 > x:
            B_eff = 2 * x
        else:
            B_eff = x + self.ed2
        
        self.t_tn = ((4 * Mu) / (phi * self.steel_fy * B_eff))**0.5
        
        return {
            "phi": phi,
            "Tu": round(self.tension_load, 2),
            "x": round(x, 2),
            "Mu": round(Mu, 2),
            "B_eff": round(B_eff, 2),
            "t": round(self.t_tn, 2)
        }
    
    def bp_thk_pro(self):
        t_br = self.bp_thk_bearing()["t"]
        t_tn = self.bp_thk_tension()["t"]
        t_pro = min(math.ceil(min(t_br, t_tn) * 2) / 2, 5)
        
        return {
            "t_pro": t_pro
        }
    
    def req_bp_area(self, Y):
        phi = 0.65
        area = self.compression_load / (phi * 0.85 * self.f_c)
        area_p = self.bp_width * Y      # Y - bearing length

        return {
            "phi": phi,
            "compression_load": round(self.compression_load, 2),
            "f_c": round(self.f_c, 2),
            "area": round(area, 2),
            "area_p": round(area_p, 2)
        }

    def conc_bearing_stress(self):  #recheck
        phi = 0.65
        A1 = A2 = self.bp_length * self.bp_width     # effective plate area (mm^2) (A1 = A2, conservative)
        f_pmax1 = phi * 0.85 * self.f_c * (A2 / A1)**0.5
        f_pmax2 = phi * 1.7 * self.f_c
        f_pmax = min(f_pmax1, f_pmax2)
        pu_A1 = self.compression_load / A1
        
        return {
            "phi": phi,
            "A1": round(A1, 2),
            "A2": round(A2, 2),
            "f_c": round(self.f_c, 2),
            "f_pmax": round(f_pmax, 2),
            "pu_A1": round(pu_A1, 2)
        }


class FinPlateCalculator():
    def __init__(self, h_shear_load, v_shear_load, v_shear_ecc,
                    fin_length, fin_width, fin_distance, steel_grade,
                    n_bolt, bolt_dia, bolt_grade, ed1_f, ed2_f, weld_grade, leg_length):
        
        self.h_shear_load = h_shear_load
        self.v_shear_load = v_shear_load
        self.v_shear_ecc = v_shear_ecc
        self.fin_length = fin_length
        self.fin_width = fin_width
        self.fin_distance = fin_distance
        self.steel_grade = steel_grade
        self.n_bolt = n_bolt
        self.bolt_dia = bolt_dia
        self.bolt_grade = bolt_grade
        self.ed1_f = ed1_f
        self.ed2_f = ed2_f
        self.weld_grade = weld_grade
        self.leg_length = leg_length

        # derived properties
        self.s1 = max(2 * (self.fin_length - self.v_shear_ecc - self.ed1_f), 0)
        self.s2 = self.fin_width - 2 * self.ed2_f
        self.ed3_f = self.fin_length - self.s1 - self.ed1_f
        
        self.bolt_fy, self.bolt_fu = mp.bolt_strength(self.bolt_grade)
        self.steel_fy, self.steel_fu = mp.steel_strength(self.steel_grade)
        self.weld_fy, self.weld_fu = mp.electrode_strength(self.weld_grade)
        self.A_seN = mp.eff_tensile_area(self.bolt_dia)

    def fin_plate_load(self):
        Vh = self.h_shear_load / 2
        Vv = self.v_shear_load / 2
        Vu = (Vh**2 + Vv**2)**0.5
        
        return {
            "Vh": Vh,
            "Vv": Vv,
            "Vu": round(Vu, 2)
        }

    def fin_plate_thk(self):
        phi = 0.9
        Mu = self.fin_plate_load()["Vv"] * self.v_shear_ecc
        t_req = (4 * Mu) / (phi * self.steel_fy * self.fin_width**2)
        t_pro = min(math.ceil(t_req * 2) / 2, 5)

        return {
            "phi": round(phi, 2),
            "b": round(self.fin_width, 2),
            "Pu": round(self.v_shear_load, 2),
            "e": round(self.v_shear_ecc, 2),
            "Mu": round(Mu, 2),
            "steel_fy": round(self.steel_fy, 2),
            "t_req": round(t_req, 2),
            "t_pro": round(t_pro, 2)
        }
    
    def fin_plate_shear_strength_yield(self):
        phi = 1.0
        self.fin_thk = self.fin_plate_thk()["t_pro"]
        A_gv = self.fin_width * self.fin_thk
        phi_R_n = phi * 0.6 * self.steel_fy * A_gv / 1000
        
        return {
            "phi": round(phi, 2),
            "steel_fy": round(self.steel_fy, 2),
            "b": round(self.fin_width, 2),
            "plate_thk": round(self.fin_thk, 2),
            "A_gv": round(A_gv, 2),
            "phi_R_n": round(phi_R_n, 2),
            "Vu": self.fin_plate_load()["Vu"]
        }
    
    def fin_plate_shear_strength_rupture(self):
        phi = 0.75
        self.d_hole = self.bolt_dia + 2      # diameter of hole
        A_nv = (self.fin_width - self.n_bolt * self.d_hole) * self.fin_thk
        phi_R_n = phi * 0.6 * self.steel_fu * A_nv

        return {
            "phi": round(phi, 2),
            "steel_fu": round(self.steel_fu, 2),
            "b": round(self.fin_width, 2),
            "plate_thk": round(self.fin_thk, 2),
            "n_thb": round(self.n_bolt, 2),
            "d_hole": round(self.d_hole, 2),
            "A_nv": round(A_nv, 2),
            "phi_R_n": round(phi_R_n, 2),
            "Vu": self.fin_plate_load()["Vu"]
        }
    
    def fin_plate_block_shear_strength(self):
        phi = 0.75
        b_gv = self.fin_width - self.ed2_f
        A_gv = b_gv * self.fin_thk
        A_nv = (b_gv - (2 * self.n_bolt - 1) * (self.d_hole / 2)) * self.fin_thk
        U_bs = 1.0
        b_nt = self.fin_length - self.v_shear_ecc
        A_nt = (b_nt - (self.d_hole / 2)) * self.fin_thk
        
        phi_R_n1 = ((phi * 0.6 * self.steel_fu * A_nv) + (U_bs * self.steel_fu * A_nt)) / 1000
        phi_R_n2 = ((phi * 0.6 * self.steel_fy * A_gv) + (U_bs * self.steel_fu * A_nt)) / 1000
        phi_R_n = min(phi_R_n1, phi_R_n2)
        
        return {
            "Phi": phi,
            "steel_fy": self.steel_fy,
            "steel_fu": self.steel_fu,
            "b_gv": round(b_gv, 2),
            "b_nt": round(b_nt, 2),
            "plate_thk": round(self.fin_thk, 2),
            "n": self.n_bolt,
            "d_hole": self.d_hole,
            "A_gv": round(A_gv, 2),
            "A_nv": round(A_nv, 2),
            "A_nt": round(A_nt, 2),
            "U_bs": round(U_bs, 2),
            "phi_R_n1": round(phi_R_n1, 2),
            "phi_R_n2": round(phi_R_n2, 2),
            "phi_R_n": round(phi_R_n, 2),
            "Vu": self.fin_plate_load()["Vu"]
        }
    
    
    def fin_weld_load(self):
        Pu = self.h_shear_load / 2       # 2 fin
        weld_length = 2 * self.fin_width
        f_n = Pu / weld_length
        
        Vu = self.v_shear_load / 2
        f_v = Vu / weld_length
        
        Mu = Vu * self.v_shear_ecc
        Z_w = self.fin_width**2 / 3     # section modulus of weld
        f_b = Mu / Z_w
        
        f_R = (f_n**2 + f_v**2 + f_b**2)**0.5   # resultant stress
        
        return {
            "single_weld_length": self.fin_width,
            "total_weld_length": weld_length,
            "Pu": round(Pu, 2),
            "f_n": round(f_n, 2),
            "Vu": round(Vu, 2),
            "f_v": round(f_v, 2),
            "e": self.v_shear_ecc,
            "Z_w": round(Z_w, 2),
            "f_b": round(f_b, 2),
            "f_R": round(f_R, 2)
        }
    
    def fin_weld_resistance(self):
        phi = 0.75
        phi_R_n = phi * 0.6 * self.weld_fu * 0.707 * self.leg_length
        
        return {
            "phi": phi,
            "weld_fu": self.weld_fu,
            "leg_length": self.leg_length,
            "phi_R_n": round(phi_R_n, 2),
            "f_R": self.fin_weld_load()["f_R"]
        }
    
    
    def bolt_load(self):
        Vh = self.h_shear_load / (2 * self.n_bolt)
        Vv = self.v_shear_load / (2 * self.n_bolt)
        Vu = (Vh**2 + Vv**2)**0.5
        
        return {
            "Vh": Vh,
            "Vv": Vv,
            "Vu": round(Vu, 2)
        }
    
    def bolt_shear_resistance(self):
        phi = 0.75
        F_nv = 0.4 * self.bolt_fu
        A_b = (PI * self.bolt_dia**2) / 4
        phi_R_n = phi * F_nv * A_b / 1000
        Vu = self.bolt_load()["Vu"]
        ratio = Vu / phi_R_n
        
        return {
            "phi": round(phi, 2),
            "bolt_fu": round(self.bolt_fu, 2),
            "F_nv": round(F_nv, 2),
            "bolt_dia": round(self.bolt_dia, 2),
            "A_b": round(A_b, 2),
            "phi_R_n": round(phi_R_n, 2),
            "Vu": round(Vu, 2),
            "ratio": round(ratio, 2)
        }
    
    def bolt_bearing_resistance(self):
        phi = 0.75
        l_c = min(self.ed1_f, self.ed2_f, self.ed3_f, self.s1, self.s2)
        phi_R_nb1 = phi * 1.2 * l_c * self.fin_thk * self.steel_fu
        phi_R_nb2 = phi * 2.4 * self.bolt_dia * self.fin_thk * self.steel_fu
        phi_R_nb = min(phi_R_nb1, phi_R_nb2) / 1000
        Vu = self.bolt_load()["Vu"]
        ratio = Vu / phi_R_nb
        
        return {
            "phi": phi,
            "l_c": round(l_c, 2),
            "plate_thk": round(self.fin_thk, 2),
            "bolt_dia": round(self.bolt_dia, 2),
            "steel_fu": round(self.steel_fu, 2),
            "phi_R_nb1": round(phi_R_nb1, 2),
            "phi_R_nb2": round(phi_R_nb2, 2),
            "phi_R_nb": round(phi_R_nb, 2),
            "Vu": round(Vu, 2),
            "ratio": round(ratio, 2)
        }
    
    def bolt_torque(self):
        nut_factor = 0.2
        proof_strength = 0.9 * self.bolt_fy
        pre_load = 0.75 * proof_strength * self.A_seN
        torque = nut_factor * self.bolt_dia * pre_load
        
        return {
            "nut_factor": round(nut_factor, 2),
            "bolt_dia": round(self.bolt_dia, 2),
            "proof_strength": round(proof_strength, 2),
            "A_seN": round(self.A_seN, 2),
            "pre_load": round(pre_load, 2),
            "torque": round(torque, 2)
        }
