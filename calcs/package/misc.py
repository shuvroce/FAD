from package import material_properties as mp


def silicone_bite(q, b, sigma_s):
    t_req = (q * b) / (2 * sigma_s)
    e_req = t_req / 3
    return t_req, e_req

def weld_resistance(electrode_grade, D_leg):
    phi = 0.75
    fy_exx, fu_exx = mp.electrode_strength(electrode_grade)
    phi_R_n = phi * 0.6 * fu_exx * 0.707 * D_leg
    return phi_R_n

def pvb_R(h_inner):
    if h_inner == 0.38:
        return 4
    elif h_inner == 0.76:
        return 5.5
    elif h_inner == 1.14:
        return 6
    elif h_inner == 1.52:
        return 7
    elif h_inner == 2.28:
        return 8.2

def eff_area(h, b):
    A_eff = max((h * b), (h * (h/3)))
    return A_eff

def frame_load_share_factor(moi_a, moi_s, E_a, E_s):
    n = E_s / E_a
    ls_a = moi_a / (moi_a + 3 * moi_s)
    ls_s = (3 * moi_s) / (moi_a + n * moi_s)
    return ls_a, ls_s