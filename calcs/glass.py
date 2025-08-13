import numpy as np
import math


class GlassCalculatorBase:
    def __init__(self, wind_load, length, width):
        self.wind_load = wind_load
        self.length = length
        self.width = width
        self.E = 71700 * 1000
        self.rho = 2500
        self.sigma_s = 140
        self.nu_glass = 0.22
        self.nu_pvb = 0.49
        self.nu_sgp = 0.49
        self.G_glass = self.E / (2 * (1 + self.nu_glass)) # Glass shear modulus
        self.G_pvb = 200 * 1000
        self.G_sgp = 200 * 1000
        
        # auto-derived properties
        self.glass_length = max(length, width)
        self.glass_width = min(length, width)
        self.aspect_ratio = max(self.glass_length / self.glass_width, 1)
        self.eff_area = max((self.glass_length * self.glass_width), (self.glass_length**2 / 3)) / 1000**2
        self.load_area_square = self.wind_load * (self.glass_length/1000 * self.glass_width/1000)**2
        # self.load_length_free = self.wind_load * (self.glass_length/1000)**4
        
        # coefficients for deflection calculation
        self.r_0 = 0.553 - 3.83 * (self.aspect_ratio) + 1.11 * (self.aspect_ratio)**2 - 0.0969 * (self.aspect_ratio)**3
        self.r_1 = -2.29 + 5.83 * (self.aspect_ratio) - 2.17 * (self.aspect_ratio)**2 + 0.2067 * (self.aspect_ratio)**3
        self.r_2 = 1.485 - 1.908 * (self.aspect_ratio) + 0.815 * (self.aspect_ratio)**2 - 0.0822 * (self.aspect_ratio)**3

    def minimum_thickness(self, thk):
        # to calculate deflection using equation as per ASTM (for using chart, min thk not required)
        thk_min = {
            2.5: 2.16, 2.7: 2.59, 3.0: 2.92, 4.0: 3.78, 5.0: 4.57,
            6.0: 5.56, 8.0: 7.42, 10.0: 9.02, 12.0: 11.91, 16.0: 15.09,
            19.0: 18.26, 22.0: 21.44
        }
        if thk not in thk_min:
            raise ValueError(f"Unknown glass thickness: {thk}")
        return thk_min[thk]
    
    def compute_silicone_bite(self):
        t_req = (self.wind_load * self.glass_width) / (2 * self.sigma_s)
        e_req = t_req / 3
        
        return {
            "sigma_s": round(self.sigma_s, 2),
            "t_req": round(t_req, 2),
            "t_pro": round(math.ceil(t_req), 2),
            "e_req": round(e_req, 2),
            "e_pro": round(max(math.ceil(e_req), 6), 2)
        }



class SGUCalculator(GlassCalculatorBase):
    def __init__(self, length, width, thickness, glass_type, support_type,
                wind_load, nfl):
        super().__init__(wind_load, length, width)
        
        self.thickness = thickness
        self.glass_type = glass_type
        self.support_type = support_type
        self.nfl = nfl

    def compute_params(self):
        return {
            "length": self.glass_length,
            "width": self.glass_width,
            "thickness": self.thickness,
            "eff_area": self.eff_area,
            "wind_load": self.wind_load,
            "glass_type": self.glass_type,
            "support_type": self.support_type,
            "aspect_ratio": round(self.aspect_ratio, 2),
            "load_area_square": round(self.load_area_square, 2)
        }
    
    def glass_type_factor(self):
        factors = {"AN": 1.0, "HS": 2.0, "FT": 4.0}
        if self.glass_type not in factors:
            raise ValueError(f"Unknown glass type: {self.glass_type}")
        return factors[self.glass_type]

    def compute_load_resistance(self):
        gtf = self.glass_type_factor()
        lr = self.nfl * gtf
        
        return {
            "nfl": round(self.nfl, 1),
            "gtf": round(gtf, 1),
            "lr": round(lr, 1),
            "ratio": round(self.wind_load / lr, 2)
        }
    
    def compute_glass_deflection(self):
        min_thk = self.minimum_thickness(self.thickness)
        x = np.log(np.log(self.wind_load * (self.glass_length * self.glass_width)**2 / (self.E * min_thk**4)))
        delta = min_thk * np.exp(self.r_0 + self.r_1 * x + self.r_2 * x**2)
        delta_a = self.glass_width / 60
        
        return {
            "r_0": round(self.r_0, 2),
            "r_1": round(self.r_1, 2),
            "r_2": round(self.r_2, 2),
            "min_thk": round(min_thk, 2),
            "x": round(x, 2),
            "delta": round(delta, 2),
            "delta_a": round(delta_a, 2),
            "ratio": round(delta / delta_a, 2)
        }

    # add calculation for other than 4 edges
    # def compute_glass_deflection(self, free_length, delta):
    #     if self.support_type == "Four Edges":
    #         x = np.log(np.log(self.wind_load * (self.glass_length * self.glass_width)**2 / (self.E * self.thickness**4)))
    #         delta = self.thickness * np.exp(self.r_0 + self.r_1 * x + self.r_2 * x**2)
    #         delta_a = self.glass_width / 60
            
    #         return {
    #             "r_0": round(self.r_0, 2),
    #             "r_1": round(self.r_1, 2),
    #             "r_2": round(self.r_2, 2),
    #             "x": round(x, 2),
    #             "delta": round(delta, 2),
    #             "delta_a": round(delta_a, 2),
    #             "ratio": round(delta / delta_a, 2)
    #         }
    #     else:
    #         return {
    #             "load_free_length4": self.wind_load * (free_length/1000)**4,
    #             "delta": delta,
    #             "delta_a": round(free_length / 175, 1),
    #             "ratio": round(delta / delta_a, 2)
    #         }
    
    def sound_transmission_class(self):
        density = self.thickness * 2.5
        STC = 13.3 * np.log10(density) + 13
        return {
            "density": round(density, 2),
            "STC": round(STC, 1)
        }
    
    def summary(self):
        return {
            "params": self.compute_params(),
            "load_resistance": self.compute_load_resistance(),
            "deflection": self.compute_glass_deflection(),
            "silicone_bite": self.compute_silicone_bite(),
            "stc": self.sound_transmission_class()
        }



class DGUCalculator(GlassCalculatorBase):
    def __init__(self, length, width, thickness1, gap, thickness2, glass1_type, glass2_type,
                support_type, wind_load, nfl1, nfl2):
        super().__init__(wind_load, length, width)

        self.thickness1 = thickness1
        self.gap = gap
        self.thickness2 = thickness2
        self.glass1_type = glass1_type
        self.glass2_type = glass2_type
        self.support_type = support_type
        self.nfl1 = nfl1
        self.nfl2 = nfl2
    
    def compute_params(self):
        return {
            "length": self.glass_length,
            "width": self.glass_width,
            "thickness1": self.thickness1,
            "gap": self.gap,
            "thickness2": self.thickness2,
            "eff_area": self.eff_area,
            "wind_load": self.wind_load,
            "glass1_type": self.glass1_type,
            "glass2_type": self.glass2_type,
            "support_type": self.support_type,
            "aspect_ratio": round(self.aspect_ratio, 2),
            "load_area_square": round(self.load_area_square, 2)
        }
    
    def glass_type_factor(self):
        gtf_table = {
            "AN": {"AN": (0.9, 0.9), "HS": (1.0, 1.9), "FT": (1.0, 3.8)},
            "HS": {"AN": (1.9, 1.0), "HS": (1.8, 1.8), "FT": (1.9, 3.8)},
            "FT": {"AN": (3.8, 1.0), "HS": (3.8, 1.9), "FT": (3.6, 3.6)},
        }
        try:
            return gtf_table[self.glass1_type][self.glass2_type]
        except KeyError:
            raise ValueError(f"Invalid glass type combination: {self.glass1_type}, {self.glass2_type}")

    def load_share_factor(self):
        ls1 = ((self.thickness1**3 + self.thickness2**3) / self.thickness1**3)
        ls2 = ((self.thickness1**3 + self.thickness2**3) / self.thickness2**3)
        return ls1, ls2

    def compute_load_resistance(self):
        gtf1, gtf2 = self.glass_type_factor()
        ls1, ls2 = self.load_share_factor()
        lr1 = self.nfl1 * gtf1 * ls1
        lr2 = self.nfl2 * gtf2 * ls2
        lr = min(lr1, lr2)
        
        return {
            "nfl1": round(self.nfl1, 1),
            "nfl2": round(self.nfl2, 1),
            "gtf1": round(gtf1, 1),
            "gtf2": round(gtf2, 1),
            "ls1": round(ls1, 2),
            "ls2": round(ls2, 2),
            "lr1": round(lr1, 1),
            "lr2": round(lr2, 1),
            "lr": round(lr, 1),
            "ratio": round(self.wind_load / lr, 2)
        }
    
    def compute_glass_deflection(self):
        ls1, ls2 = self.load_share_factor()
        q1 = self.wind_load / ls1
        q2 = self.wind_load / ls2
        
        min_thk1 = self.minimum_thickness(self.thickness1)
        min_thk2 = self.minimum_thickness(self.thickness2)
        
        x1 = np.log(np.log(q1 * (self.glass_length * self.glass_width)**2 / (self.E * min_thk1**4)))
        x2 = np.log(np.log(q2 * (self.glass_length * self.glass_width)**2 / (self.E * min_thk2**4)))

        delta1 = min_thk1 * np.exp(self.r_0 + self.r_1 * x1 + self.r_2 * x1**2)
        delta2 = min_thk2 * np.exp(self.r_0 + self.r_1 * x2 + self.r_2 * x2**2)
        delta = max(delta1, delta2)
        delta_a = self.glass_width / 60
        
        return {
            "q1": round(q1, 2),
            "q2": round(q2, 2),
            "r_0": round(self.r_0, 2),
            "r_1": round(self.r_1, 2),
            "r_2": round(self.r_2, 2),
            "min_thk1": round(min_thk1, 2),
            "min_thk2": round(min_thk2, 2),
            "x1": round(x1, 2),
            "x2": round(x2, 2),
            "delta1": round(delta1, 2),
            "delta2": round(delta2, 2),
            "delta": round(delta, 2),
            "delta_a": round(delta_a, 2),
            "ratio": round(delta / delta_a, 2)
        }
    
    def sound_transmission_class(self):
        density1 = self.thickness1 * 2.5
        density2 = self.thickness2 * 2.5
        R1 = 0.1 * self.gap
        STC = 13.3 * np.log10(density1 + density2) + 13 + R1
        
        return {
            "density1": round(density1, 2),
            "density2": round(density2, 2),
            "R1": round(R1, 2),
            "STC": round(STC, 1)
        }
    
    def summary(self):
        return {
            "params": self.compute_params(),
            "load_resistance": self.compute_load_resistance(),
            "deflection": self.compute_glass_deflection(),
            "silicone_bite": self.compute_silicone_bite(),
            "stc": self.sound_transmission_class()
        }



class TGUCalculator(GlassCalculatorBase):       # need checking (Out of ASTM E1300 scope)
    def __init__(self, length, width, thickness1, gap1, thickness2, gap2, thickness3,
                glass1_type, glass2_type, glass3_type,
                support_type, wind_load, nfl1, nfl2, nfl3):
        super().__init__(wind_load, length, width)

        self.thickness1 = thickness1
        self.gap1 = gap1
        self.thickness2 = thickness2
        self.gap2 = gap2
        self.thickness3 = thickness3
        self.glass1_type = glass1_type
        self.glass2_type = glass2_type
        self.glass3_type = glass3_type
        self.support_type = support_type
        self.nfl1 = nfl1
        self.nfl2 = nfl2
        self.nfl3 = nfl3



class LGUCalculator(GlassCalculatorBase):
    def __init__(self, length, width, thickness1, thickness_inner, thickness2,
                glass_type, support_type, wind_load, nfl):
        super().__init__(wind_load, length, width)
        
        self.thickness1 = thickness1
        self.thickness_inner = thickness_inner
        self.thickness2 = thickness2
        self.glass_type = glass_type
        self.support_type = support_type
        self.nfl = nfl

        # Auto-derived
        self.thickness = self.thickness1 + self.thickness2
    
    def compute_params(self):
        return {
            "length": self.glass_length,
            "width": self.glass_width,
            "thickness1": self.thickness1,
            "thickness_inner": self.thickness_inner,
            "thickness2": self.thickness2,
            "thickness": self.thickness,
            "eff_area": self.eff_area,
            "wind_load": self.wind_load,
            "glass_type": self.glass_type,
            "support_type": self.support_type,
            "aspect_ratio": round(self.aspect_ratio, 2),
            "load_area_square": round(self.load_area_square, 2)
        }

    def effective_thickness_lgu(self):
        self.min_thk1 = self.minimum_thickness(self.thickness1)
        self.min_thk2 = self.minimum_thickness(self.thickness2)
        gamma = self.G_pvb / self.G_glass
        h_eff = (self.min_thk1**3 + self.min_thk2**3 + 3 * gamma * self.min_thk1 * self.min_thk2 * (self.min_thk1 + self.min_thk2)) ** (1 / 3)
        return h_eff

    def glass_type_factor(self):
        factors = {"AN": 1.0, "HS": 2.0, "FT": 4.0}
        if self.glass_type not in factors:
            raise ValueError(f"Unknown glass type: {self.glass_type}")
        return factors[self.glass_type]

    def compute_load_resistance(self):
        gtf = self.glass_type_factor()
        lr = self.nfl * gtf
        
        return {
            "nfl": round(self.nfl, 1),
            "gtf": round(gtf, 1),
            "lr": round(lr, 1),
            "ratio": round(self.wind_load / lr, 2)
        }
    
    def compute_glass_deflection(self):
        h_eff = self.effective_thickness_lgu()
        x = np.log(np.log(self.wind_load * (self.glass_length * self.glass_width)**2 / (self.E * h_eff**4)))
        delta = h_eff * np.exp(self.r_0 + self.r_1 * x + self.r_2 * x**2)
        delta_a = self.glass_width / 60
        
        return {
            "r_0": round(self.r_0, 2),
            "r_1": round(self.r_1, 2),
            "r_2": round(self.r_2, 2),
            "min_thk1": round(self.min_thk1, 2),
            "min_thk2": round(self.min_thk2, 2),
            "h_eff": round(h_eff, 2),
            "x": round(x, 2),
            "delta": round(delta, 2),
            "delta_a": round(delta_a, 2),
            "ratio": round(delta / delta_a, 2)
        }
    
    def sound_transmission_class(self):
        density1 = self.thickness1 * 2.5
        density2 = self.thickness2 * 2.5
        
        def R1(self):
            factors = {0.38: 4.0, 0.76: 5.5, 1.14: 6.0, 1.52: 7.0, 2.28: 8.14}
            if self.thickness_inner not in factors:
                raise ValueError(f"Unknown glass type: {self.thickness_inner}")
            return factors[self.thickness_inner]

        R1 = R1(self)
        STC = 13.3 * np.log10(density1 + density2) + 13 + R1

        return {
            "density1": round(density1, 2),
            "density2": round(density2, 2),
            "R1": round(R1, 2),
            "STC": round(STC, 1)
        }

    def summary(self):
        return {
            "params": self.compute_params(),
            "load_resistance": self.compute_load_resistance(),
            "deflection": self.compute_glass_deflection(),
            "silicone_bite": self.compute_silicone_bite(),
            "stc": self.sound_transmission_class()
        }


class LDGUCalculator(GlassCalculatorBase):
    def __init__(self, length, width, thickness1_1, thickness_inner, thickness1_2, gap,
                thickness2, glass1_type, glass2_type, support_type, wind_load, nfl1, nfl2):
        super().__init__(wind_load, length, width)

        self.thickness1_1 = thickness1_1
        self.thickness_inner = thickness_inner
        self.thickness1_2 = thickness1_2
        self.thickness1 = self.thickness1_1 + self.thickness1_2
        self.gap = gap
        self.thickness2 = thickness2
        self.glass1_type = glass1_type
        self.glass2_type = glass2_type
        self.support_type = support_type
        self.nfl1 = nfl1
        self.nfl2 = nfl2
    
    def compute_params(self):
        return {
            "length": self.glass_length,
            "width": self.glass_width,
            "thickness1_1": self.thickness1_1,
            "thickness_inner": self.thickness_inner,
            "thickness1_2": self.thickness1_2,
            "thickness1": self.thickness1,
            "gap": self.gap,
            "thickness2": self.thickness2,
            "eff_area": self.eff_area,
            "wind_load": self.wind_load,
            "glass1_type": self.glass1_type,
            "glass2_type": self.glass2_type,
            "support_type": self.support_type,
            "aspect_ratio": round(self.aspect_ratio, 2),
            "load_area_square": round(self.load_area_square, 2)
        }

    def effective_thickness_lgu(self):
        self.min_thk1_1 = self.minimum_thickness(self.thickness1_1)
        self.min_thk1_2 = self.minimum_thickness(self.thickness1_2)
        gamma = self.G_pvb / self.G_glass
        h_eff = (self.min_thk1_1**3 + self.min_thk1_2**3 + 3 * gamma * self.min_thk1_1 * self.min_thk1_2 * (self.min_thk1_1 + self.min_thk1_2)) ** (1 / 3)
        return h_eff
    
    def glass_type_factor(self):
        gtf_table = {
            "AN": {"AN": (0.9, 0.9), "HS": (1.0, 1.9), "FT": (1.0, 3.8)},
            "HS": {"AN": (1.9, 1.0), "HS": (1.8, 1.8), "FT": (1.9, 3.8)},
            "FT": {"AN": (3.8, 1.0), "HS": (3.8, 1.9), "FT": (3.6, 3.6)},
        }
        try:
            return gtf_table[self.glass1_type][self.glass2_type]
        except KeyError:
            raise ValueError(f"Invalid glass type combination: {self.glass1_type}, {self.glass2_type}")

    def load_share_factor(self):
        ls1 = ((self.thickness1**3 + self.thickness2**3) / self.thickness1**3)
        ls2 = ((self.thickness1**3 + self.thickness2**3) / self.thickness2**3)
        return ls1, ls2

    def compute_load_resistance(self):
        gtf1, gtf2 = self.glass_type_factor()
        ls1, ls2 = self.load_share_factor()
        lr1 = self.nfl1 * gtf1 * ls1
        lr2 = self.nfl2 * gtf2 * ls2
        lr = min(lr1, lr2)
        
        return {
            "nfl1": round(self.nfl1, 1),
            "nfl2": round(self.nfl2, 1),
            "gtf1": round(gtf1, 1),
            "gtf2": round(gtf2, 1),
            "ls1": round(ls1, 2),
            "ls2": round(ls2, 2),
            "lr1": round(lr1, 1),
            "lr2": round(lr2, 1),
            "lr": round(lr, 1),
            "ratio": round(self.wind_load / lr, 2)
        }
    
    def compute_glass_deflection(self):
        ls1, ls2 = self.load_share_factor()
        q1 = self.wind_load / ls1
        q2 = self.wind_load / ls2
        
        h1_eff = self.effective_thickness_lgu()
        x1 = np.log(np.log(q1 * (self.glass_length * self.glass_width)**2 / (self.E * h1_eff**4)))
        x2 = np.log(np.log(q2 * (self.glass_length * self.glass_width)**2 / (self.E * self.thickness2**4)))

        delta1 = h1_eff * np.exp(self.r_0 + self.r_1 * x1 + self.r_2 * x1**2)
        delta2 = self.thickness2 * np.exp(self.r_0 + self.r_1 * x2 + self.r_2 * x2**2)
        delta = max(delta1, delta2)
        delta_a = self.glass_width / 60
        
        return {
            "q1": round(q1, 2),
            "q2": round(q2, 2),
            "r_0": round(self.r_0, 2),
            "r_1": round(self.r_1, 2),
            "r_2": round(self.r_2, 2),
            "min_thk1_1": round(self.min_thk1_1, 2),
            "min_thk1_2": round(self.min_thk1_2, 2),
            "h1_eff": round(h1_eff, 2),
            "x1": round(x1, 2),
            "x2": round(x2, 2),
            "delta1": round(delta1, 2),
            "delta2": round(delta2, 2),
            "delta": round(delta, 2),
            "delta_a": round(delta_a, 2),
            "ratio": round(delta / delta_a, 2)
        }
    
    def sound_transmission_class(self):
        density1_1 = self.thickness1_1 * 2.5
        density1_2 = self.thickness1_2 * 2.5
        density2 = self.thickness2 * 2.5
        
        def R1(self):
            factors = {0.38: 4.0, 0.76: 5.5, 1.14: 6.0, 1.52: 7.0, 2.28: 8.14}
            if self.thickness_inner not in factors:
                raise ValueError(f"Unknown glass type: {self.thickness_inner}")
            return factors[self.thickness_inner]
        
        R1 = R1(self)
        R2 = 0.1 * self.gap
        STC = 13.3 * np.log10(density1_1 + density1_2 + density2) + 13 + R1 + R2
        
        return {
            "density1_1": round(density1_1, 2),
            "density1_2": round(density1_2, 2),
            "density2": round(density2, 2),
            "R1": round(R1, 2),
            "R2": round(R2, 2),
            "STC": round(STC, 1)
        }
    
    def summary(self):
        return {
            "params": self.compute_params(),
            "load_resistance": self.compute_load_resistance(),
            "deflection": self.compute_glass_deflection(),
            "silicone_bite": self.compute_silicone_bite(),
            "stc": self.sound_transmission_class()
        }





if __name__ == "__main__":
    sgu = SGUCalculator(1500, 1200, 8, "FT", "Four Edges", 4.0, 2.5)
    dgu = DGUCalculator(1500, 1200, 8, 12, 8, "FT", "FT", "Four Edges", 4.0, 2.5, 2.5)
    lgu = LGUCalculator(1500, 1200, 8, 1.52, 8, "FT", "Four Edges", 4.0, 3.0)
    ldgu = LDGUCalculator(1500, 1200, 6, 1.52, 6, 12, 8, "FT", "FT", "Four Edges", 4.0, 3.0, 2.5)
    summary = ldgu.summary()
    print(summary)




