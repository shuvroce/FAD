import numpy as np
import math


location_wind_speeds = {
        "Angarpota": 47.8, "Bagerhat": 77.5, "Bandarban": 62.5, "Barguna": 80.0,
        "Barisal": 78.7, "Bhola": 69.5, "Bogra": 61.9, "Brahmanbaria": 56.7,
        "Chandpur": 50.6, "Chapai Nawabganj": 41.4, "Chittagong": 80.0,
        "Chuadanga": 61.9, "Comilla": 61.4, "Cox’s Bazar": 80.0, "Dahagram": 47.8,
        "Dhaka": 65.7, "Dinajpur": 41.4, "Faridpur": 63.1, "Feni": 64.1,
        "Gaibandha": 65.6, "Gazipur": 66.5, "Gopalganj": 74.5, "Habiganj": 54.2,
        "Hatiya": 80.0, "Ishurdi": 69.5, "Joypurhat": 56.7, "Jamalpur": 56.7,
        "Jessore": 64.1, "Jhalakati": 80.0, "Jhenaidah": 65.0, "Khagrachhari": 56.7,
        "Khulna": 73.3, "Kutubdia": 80.0, "Kishoreganj": 64.7, "Kurigram": 65.6,
        "Kushtia": 66.9, "Lakshmipur": 51.2, "Lalmonirhat": 63.7, "Madaripur": 68.1,
        "Magura": 65.0, "Manikganj": 58.2, "Meherpur": 58.2, "Maheshkhali": 80.0,
        "Moulvibazar": 53.0, "Munshiganj": 57.1, "Mymensingh": 67.4, "Naogaon": 55.2,
        "Narail": 68.6, "Narayanganj": 61.1, "Narsinghdi": 59.7, "Natore": 61.9,
        "Netrokona": 65.6, "Nilphamari": 44.7, "Noakhali": 57.1, "Pabna": 63.1,
        "Panchagarh": 41.4, "Patuakhali": 80.0, "Pirojpur": 80.0, "Rajbari": 59.1,
        "Rajshahi": 49.2, "Rangamati": 56.7, "Rangpur": 65.3, "Satkhira": 57.6,
        "Shariatpur": 61.9, "Sherpur": 62.5, "Sirajganj": 50.6, "Srimangal": 50.6,
        "St. Martin’s Island": 80.0, "Sunamganj": 61.1, "Sylhet": 61.1,
        "Sandwip": 80.0, "Tangail": 50.6, "Teknaf": 80.0, "Thakurgaon": 41.4
    }

def location_wind_load_bd(location):
    location = location.strip()
    return location_wind_speeds[location]



def importance_factor(occupancy_cat):
    if occupancy_cat == "I":
        Imp = 0.77
    elif occupancy_cat == "II":
        Imp = 1.0
    elif occupancy_cat == "III":
        Imp = 1.15
    elif occupancy_cat == "IV":
        Imp = 1.15
    return Imp


def topographic_factor(topography_type, Ht, Lh, x, z, exposure_cat, topo_crest_side):
    # Normalize inputs
    exposure_cat = exposure_cat.upper()
    # topo_crest_side = topo_crest_side.lower()
    # topography_type = topography_type.lower()

    # K1 Table
    K1_table = {
        '2-Dimensional Ridge': {'A': 1.30, 'B': 1.45, 'C': 1.55},
        '2-Dimensional Escarpment': {'A': 0.75, 'B': 0.85, 'C': 0.95},
        '3-Dimensional Hill': {'A': 0.95, 'B': 1.05, 'C': 1.15}
    }

    # γ and μ values
    gamma_values = {'2-Dimensional Ridge': 3.0, '2-Dimensional Escarpment': 2.5, '3-Dimensional Hill': 4.0}
    mu_values = {
        '2-Dimensional Ridge': {'Upwind': 1.5, 'Downwind': 1.5},
        '2-Dimensional Escarpment': {'Upwind': 1.5, 'Downwind': 4.0},
        '3-Dimensional Hill': {'Upwind': 1.5, 'Downwind': 1.5}
    }

    if topography_type == "Homogeneous":
        return 1.0
    
    try:
        K1_base = K1_table[topography_type][exposure_cat]
        K1 = K1_base * (Ht / Lh)

        gamma = gamma_values[topography_type]
        mu = mu_values[topography_type][topo_crest_side]

        # Compute K2 and K3
        K2 = max(0, 1 - abs(x) / (mu * Lh))  # Ensure K2 ≥ 0
        K3 = math.exp(-gamma * z / Lh)

        # Final Kzt
        Kzt = (1 + K1 * K2 * K3) ** 2
        return round(Kzt, 3)

    except KeyError as e:
        raise ValueError(f"Invalid input: {e}")



def gust_factor(H, L, B, V, n1, beta, exposure_cat):
    # Exposure-dependent values
    exposure_data = {
        "A": {"alpha": 0.25, "b": 0.45, "c": 0.30},
        "B": {"alpha": 0.20, "b": 0.35, "c": 0.25},
        "C": {"alpha": 0.15, "b": 0.25, "c": 0.20}
    }

    # Constants
    alpha = exposure_data[exposure_cat]["alpha"]
    b = exposure_data[exposure_cat]["b"]
    c = exposure_data[exposure_cat]["c"]

    epsilon = 0.333
    z_min = 9.14  # 30 ft
    g_Q = 3.4
    ll = 97.54
    g_v = 3.4

    z = max(0.6 * H, z_min)
    I_z = c * (10 / z) ** (1 / 6)
    L_z = ll * (z / 10) ** epsilon

    Q = (1 / (1 + 0.63 * ((B + H) / L_z) ** 0.63)) ** 0.5
    log_term = np.log(3600 * n1)
    g_R = (2 * log_term) ** 0.5 + 0.577 / (2 * log_term) ** 0.5

    V_z = b * ((z / 10) ** alpha) * V
    N1 = (n1 * L_z) / V_z
    R_n = (7.47 * N1) / ((1 + 10.3 * N1) ** (5 / 3))

    def eta_R(eta):
        return (1 / eta) - (1 / (2 * eta**2)) * (1 - np.exp(-2 * eta))

    eta_h = 4.6 * n1 * (H / V_z)
    eta_B = 4.6 * n1 * (B / V_z)
    eta_L = 15.4 * n1 * (L / V_z)

    R_h = eta_R(eta_h)
    R_B = eta_R(eta_B)
    R_L = eta_R(eta_L)

    R = ((1 / beta) * R_n * R_h * R_B * (0.53 + 0.47 * R_L)) ** 0.5

    temp1 = (g_Q * Q) ** 2
    temp2 = (g_R * R) ** 2
    temp3 = (temp1 + temp2) ** 0.5
    temp4 = (1 + 1.7 * I_z * temp3) / (1 + 1.7 * g_v * I_z)

    G_f = 0.925 * temp4
    return G_f



def velocity_pressure_coeff(exposure_cat, H, WFRS):
    # WFRS = Wind Force Resisting System (MWFRS or C&C)
    heights = [
        4.6, 6.1, 7.6, 9.1, 12.2, 15.2, 18.0, 21.3, 24.4, 27.41, 30.5,
        36.6, 42.7, 48.8, 54.9, 61.0, 76.2, 91.4, 106.7, 121.9, 137.2, 152.4
    ]

    data = {
        ("A", "C&C"): [0.7, 0.7, 0.7, 0.7, 0.76, 0.81, 0.85, 0.89, 0.93, 0.96, 0.99,
                        1.04, 1.09, 1.13, 1.17, 1.2, 1.28, 1.35, 1.41, 1.47, 1.52, 1.56],
        ("A", "MWFRS"): [0.57, 0.62, 0.66, 0.7, 0.76, 0.81, 0.85, 0.89, 0.93, 0.96, 0.99,
                        1.04, 1.09, 1.13, 1.17, 1.2, 1.28, 1.35, 1.41, 1.47, 1.52, 1.56],
        ("B", ""): [0.85, 0.9, 0.94, 0.98, 1.04, 1.09, 1.13, 1.17, 1.21, 1.24, 1.26,
                        1.31, 1.36, 1.39, 1.43, 1.46, 1.53, 1.59, 1.64, 1.69, 1.73, 1.77],
        ("C", ""): [1.03, 1.08, 1.12, 1.16, 1.22, 1.27, 1.31, 1.34, 1.38, 1.4, 1.43,
                        1.48, 1.52, 1.55, 1.58, 1.61, 1.68, 1.73, 1.78, 1.82, 1.86, 1.89],
    }

    if exposure_cat == "A":
        key = (exposure_cat, WFRS)
    else:
        key = (exposure_cat, "")

    # Interpolate to get Kz
    kz_values = data[key]
    K_z = float(np.interp(H, heights, kz_values))
    return K_z


def directionality_factor(structure_type):
    structure_type = structure_type.lower().strip()

    if structure_type in [
        "buildings", 
        "solid sign", 
        "open sign", 
        "lattice framework", 
        "trussed tower (rectangular)", 
        "trussed tower (square)", 
        "trussed tower (triangular)"
    ]:
        K_d =  0.85

    elif structure_type in [
        "chimney, tanks (hexagonal)", 
        "chimney, tanks (round)"
    ]:
        K_d =  0.95

    elif structure_type == "chimney, tanks (square)":
        K_d =  0.90

    elif structure_type == "trussed tower (others)":
        K_d =  0.95

    else:
        raise ValueError(f"Unknown structure type: {structure_type}")
    
    return K_d


def external_pressure_coeff(L, B):
    C_pw = 0.8
    C_ps = -0.7
    
    if L/B <= 1.0:
        C_pl = -0.5
    elif L/B > 1.0 and L/B < 4:
        C_pl = -0.3
    elif L/B >= 4:
        C_pl = -0.2
    
    return C_pw, C_pl, C_ps


def internal_pressure_coeff(enclosure_type):
    if enclosure_type == "Open":
        GC_pi = 0
    elif enclosure_type == "Partially Enclosed":
        GC_pi = 0.55
    elif enclosure_type == "Enclosed":
        GC_pi = 0.18
    
    return GC_pi


def eff_area(h, b):
    A_eff = max((h * b), (h * (h/3)))
    return A_eff


def ext_pressure_coeff_wall_cladd(eff_area):
    if eff_area <= 1.9:
        GC_p__z4_pos = GC_p__z5_pos = 0.9
    elif eff_area >= 46.5:
        GC_p__z4_pos = GC_p__z5_pos = 0.6
    else:
        GC_p__z4_pos = GC_p__z5_pos = 0.6 + (0.9 - 0.6) * ((np.log(46.5) - np.log(eff_area)) / (np.log(46.5) - np.log(1.9)))
    
    if eff_area <= 1.9:
        GC_p__z4_neg = 0.9
    elif eff_area >= 46.5:
        GC_p__z4_neg = 0.7
    else:
        GC_p__z4_neg = 0.7 + (0.9 - 0.7) * ((np.log(46.5) - np.log(eff_area)) / (np.log(46.5) - np.log(1.9)))
    
    if eff_area <= 1.9:
        GC_p__z5_neg = 1.8
    elif eff_area >= 46.5:
        GC_p__z5_neg = 1.0
    else:
        GC_p__z5_neg = 1.0 + (1.8 - 1.0) * ((np.log(46.5) - np.log(eff_area)) / (np.log(46.5) - np.log(1.9)))
    
    return GC_p__z4_pos, -GC_p__z4_neg, GC_p__z5_pos, -GC_p__z5_neg


def ext_pressure_coeff_roof_cladd(eff_area):
    if eff_area <= 0.9:
        GC_p__z1_neg = 1.4
    elif eff_area >= 46.5:
        GC_p__z1_neg = 0.9
    else:
        GC_p__z1_neg = 0.9 + (1.4 - 0.9) * ((np.log(46.5) - np.log(eff_area)) / (np.log(46.5) - np.log(0.9)))
    
    if eff_area <= 0.9:
        GC_p__z2_neg = 2.3
    elif eff_area >= 46.5:
        GC_p__z2_neg = 1.6
    else:
        GC_p__z2_neg = 1.6 + (2.3 - 1.6) * ((np.log(46.5) - np.log(eff_area)) / (np.log(46.5) - np.log(0.9)))
    
    if eff_area <= 0.9:
        GC_p__z3_neg = 3.2
    elif eff_area >= 46.5:
        GC_p__z3_neg = 2.3
    else:
        GC_p__z3_neg = 2.3 + (3.2 - 2.3) * ((np.log(46.5) - np.log(eff_area)) / (np.log(46.5) - np.log(0.9)))
    
    return -GC_p__z1_neg, -GC_p__z2_neg, -GC_p__z3_neg


def wall_cladding_wind_pressure(q_z, GC_p__z4_pos, GC_p__z4_neg, GC_p__z5_pos, GC_p__z5_neg, GC_pi):
    P_z__z4_pos = (q_z * (GC_p__z4_pos)) + (q_z * (GC_pi))
    P_z__z4_neg = (q_z * (GC_p__z4_neg)) - (q_z * (GC_pi))
    P_z__z5_pos = (q_z * (GC_p__z5_pos)) + (q_z * (GC_pi))
    P_z__z5_neg = (q_z * (GC_p__z5_neg)) - (q_z * (GC_pi))
    return P_z__z4_pos, P_z__z4_neg, P_z__z5_pos, P_z__z5_neg


def roof_cladding_wind_pressure(q_z, GC_p__z1_neg, GC_p__z2_neg, GC_p__z3_neg, GC_pi):
    P_z__z1_neg = (q_z * (GC_p__z1_neg)) - (q_z * (GC_pi))
    P_z__z2_neg = (q_z * (GC_p__z2_neg)) - (q_z * (GC_pi))
    P_z__z3_neg = (q_z * (GC_p__z3_neg)) - (q_z * (GC_pi))
    return P_z__z1_neg, P_z__z2_neg, P_z__z3_neg