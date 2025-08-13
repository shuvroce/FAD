# constants
PI = 3.1416
inf = 1e10


def concrete_strength(concrete_grade):
    if concrete_grade == "M20":
        f_c = 20
    elif concrete_grade == "M25":
        f_c = 25
    elif concrete_grade == "M30":
        f_c = 30
    elif concrete_grade == "M35":
        f_c = 35
    elif concrete_grade == "M40":
        f_c = 40
    elif concrete_grade == "M45":
        f_c = 45
    elif concrete_grade == "M50":
        f_c = 50
    elif concrete_grade == "M55":
        f_c = 55
    elif concrete_grade == "3500 psi":
        f_c = 24.1
    elif concrete_grade == "4000 psi":
        f_c = 27.5
    elif concrete_grade == "4500 psi":
        f_c = 31
    return f_c


def bolt_strength(bolt_grade):
    if bolt_grade == "Grade 4.6":
        fy = 240  # yield strength of anchor bolt (N/mm^2)
        fu = 400  # ultimate strength of anchor bolt (N/mm^2)
    elif bolt_grade == "Grade 5.8":
        fy = 400
        fu = 500
    elif bolt_grade == "Grade 6.8":
        fy = 480
        fu = 600
    elif bolt_grade == "Grade 8.8":
        fy = 640
        fu = 800
    elif bolt_grade == "ASTM A307":
        fy = 250
        fu = 415
    elif bolt_grade == "ASTM A325":
        fy = 660
        fu = 830
    elif bolt_grade == "SS A4-70":
        fy = 450
        fu = 700
    return fy, fu


def aluminum_strength(alum_grade):
    if alum_grade == "6063-T5":
        fy = 110    # N/mm^2
        fu = 150    # N/mm^2
    elif alum_grade == "6063-T6":
        fy = 172
        fu = 207
    elif alum_grade == "6061-T6":
        fy = 241
        fu = 262
    return fy, fu


def steel_strength(steel_grade):
    if steel_grade == "A36":
        fy = 250
        fu = 400
    elif steel_grade == "A500 Gr. B":
        fy = 317
        fu = 400
    elif steel_grade == "A572 Gr. 50":
        fy = 345
        fu = 450
    elif steel_grade == "SS 304":
        fy = 205
        fu = 515
    return fy, fu


def electrode_strength(electrode_grade):
    if electrode_grade == "E60xx":
        fy = 344.8
        fu = 427.6
    elif electrode_grade == "E70xx":
        fy = 393.1
        fu = 482.8
    elif electrode_grade == "E80xx":
        fy = 462.1
        fu = 551.7
    elif electrode_grade == "E90xx":
        fy = 531.0
        fu = 620.7
    elif electrode_grade == "E100xx":
        fy = 600.0
        fu = 689.7
    elif electrode_grade == "E110xx":
        fy = 655.2
        fu = 758.6
    elif electrode_grade == "E120xx":
        fy = 737.9
        fu = 827.6
    return fy, fu


def thread_pitch(bolt_dia):
    if bolt_dia == 10:
        P_coarse = 1.5
        P_fine = 1.25
    elif bolt_dia == 12:
        P_coarse = 1.75
        P_fine = 1.25
    elif bolt_dia == 14:
        P_coarse = 2.0
        P_fine = 1.5
    elif bolt_dia == 16:
        P_coarse = 2.0
        P_fine = 1.5
    elif bolt_dia == 18:
        P_coarse = 2.5
        P_fine = 1.5
    elif bolt_dia == 20:
        P_coarse = 2.5
        P_fine = 1.5
    elif bolt_dia == 22:
        P_coarse = 2.5
        P_fine = 1.5
    elif bolt_dia == 24:
        P_coarse = 3.0
        P_fine = 2.0
    elif bolt_dia == 27:
        P_coarse = 3.0
        P_fine = 2.0
    elif bolt_dia == 30:
        P_coarse = 3.5
        P_fine = 2.0
    elif bolt_dia == 33:
        P_coarse = 3.5
        P_fine = 2.0
    elif bolt_dia == 36:
        P_coarse = 4.0
        P_fine = 3.0
    elif bolt_dia == 39:
        P_coarse = 4.0
        P_fine = 3.0
    elif bolt_dia == 42:
        P_coarse = 4.5
        P_fine = 3.0
    elif bolt_dia == 48:
        P_coarse = 5.0
        P_fine = 3.0
    return P_coarse, P_fine


def eff_tensile_area(bolt_dia):
    P_coarse, P_fine = thread_pitch(bolt_dia)
    A_seN = (PI / 4) * (bolt_dia - 0.9382 * P_coarse) ** 2
    return A_seN


