# The code to compute gaseous attenuation and rain attenuation
# Author G. Klopotek
# gaseous attenuation based on ITU-R P.676-6

import numpy as np
import matplotlib.pyplot as plt

f = 30                          # GHZ
elev = 10  # An elevation angle at which the atennuation needs to be computed
p = 937
temp = 10.7                     # in C
lat = 47.881
rho = 7.13                      # g/m3


def Xi(no, pressure, temperature):
    """
    -phi: lattidue in deg
    """
    r_p = pressure/1013.0
    r_t = 288.0/(273.0+temperature)
    a = b = c = d = 0.0

    if no == 1:
        a = 0.0717
        b = -1.8132
        c = 0.0156
        d = -1.6515
    if no == 2:
        a = 0.5146
        b = -4.6368
        c = -0.1921
        d = -5.7416
    if no == 3:
        a = 0.3414
        b = -6.5851
        c = 0.2130
        d = -8.5854
    return np.power(r_p, a)*np.power(r_t, b)*np.exp(c*(1-r_p)+d*(1-r_t))


def g_ff(frequency, fi):
    return 1+np.power(((frequency-fi)/(frequency+fi)), 2)


def gammaDry(frequency, pressure, temperature):
    """
    Returns dry specific attenuation (dB/km) for frequencies <= 54 GHz:
    - frequency: in GHz
    - pressure: in hPa
    - temperature: in C where mean temperature values can be obtained from maps
    given in Recommendation ITU-R P.1510, when no adequate temperature data
    are available
    """
    r_p = pressure/1013.0
    r_t = 288.0/(273.0+temperature)
    # ITU-R P.676-6 eq 22a
    term1 = 7.2 * np.power(r_t, 2.8) / (np.power(frequency, 2.0) + 0.34 * np.power(r_p, 2.0) * np.power(r_t, 1.6))
    term2 = 0.62 * Xi(3, pressure, temperature) / (np.power(54.0 - frequency, 1.16 * Xi(1, pressure, temperature))
                                                   + 0.83 * Xi(2, pressure, temperature))
    return (term1 + term2) * np.power(frequency, 2.0) * np.power(r_p, 2.0) * 1e-3


def gammaWet(frequency, pressure, temperature, rho):
    """
    Returns specific attenuation (dB/km) for the water vapour:
    - frequency: in GHz
    - pressure: in hPa
    - temperature: in C where mean temperature values can be obtained from maps
    given in Recommendation ITU-R P.1510, when no adequate temperature data
    are available
    - rho - water vapour density (g/m3)
    """
    r_p = pressure / 1013.0
    r_t = 288.0 / (273.0 + temperature)

    eta_1 = 0.955 * r_p * np.power(r_t, 0.68) + 0.006 * rho
    eta_2 = 0.735 * r_p * np.power(r_t, 0.5) + 0.0353 * np.power(r_t, 4) * rho
    # ITU-R P.676-6 eq 23a
    term1 = 3.98 * eta_1 * np.exp(2.23 * (1 - r_t)) * g_ff(frequency, 22.0) / (np.power(f - 22.235, 2.0) + 9.42 * np.power(eta_1, 2))
    term2 = 11.96 * eta_1 * np.exp(0.7 * (1 - r_t)) / (np.power(frequency - 183.31, 2.0) + 11.14 * np.power(eta_1, 2.0))
    term3 = 0.081 * eta_1 * np.exp(6.44 * (1 - r_t)) / (np.power(frequency - 321.226, 2.0) + 6.29 * np.power(eta_1, 2.0))
    term4 = 3.66 * eta_1 * np.exp(1.6 * (1 - r_t)) / (np.power(frequency - 325.153, 2) + 9.22 * np.power(eta_1, 2.0))
    term5 = 25.37 * eta_1 * np.exp(1.09 * (1 - r_t)) / (np.power(frequency - 380.0, 2.0))
    term6 = 17.4 * eta_1 * np.exp(1.46 * (1 - r_t)) / (np.power(frequency - 448, 2.0))
    term7 = 844.6 * eta_1 * np.exp(0.17 * (1 - r_t)) * g_ff(frequency, 557.0) / (np.power(frequency - 557, 2.0))
    term8 = 290 * eta_1 * np.exp(0.41 * (1 - r_t)) * g_ff(frequency, 752.0) / (np.power(frequency - 752, 2.0))
    term9 = 8.3328 * 1e4 * eta_2 * np.exp(0.99 * (1 - r_t)) * g_ff(frequency, 1780.0) / (np.power(frequency - 1780, 2.0))

    term_sum = np.sum((term1, term2, term3, term4, term5, term6, term7, term8, term9))
    return term_sum * np.power(frequency, 2.0) * np.power(r_t, 2.5) * rho * 1e-4


def equivalentHeightDry(frequency, pressure):
    r_p = pressure/1013.0

    term1 = 4.64 / (1 + 0.066 * np.power(r_p, -2.3))
    term2 = np.exp(-1 * np.power((frequency - 59.7) / (2.87 + 12.4 * np.exp(-7.9 * r_p)), 2.0))
    t1 = term1 * term2

    t2 = (0.14 * np.exp(2.12 * r_p)) / (np.power(frequency-118.75, 2.0) + 0.031 * np.exp(2.2 * r_p))

    term3 = 0.0114 * frequency / (1 + 0.14 * np.power(r_p, -2.6))
    term4 = (-0.0247 + 0.0001 * frequency + 1.61 * 1e-6 * np.power(frequency, 2.0)) / (1 - 0.0169 * frequency + 4.1 * 1e-5 * np.power(frequency, 2.0) + 3.2 * 1e-7 * np.power(frequency, 3.0))
    t3 = term3 * term4

    h_o = 6.1 * (1 + t1 + t2 + t3) / (1 + 0.17 * np.power(r_p, -1.1))
    h_constraint = 10.7 * np.power(r_p, 0.3)

    if h_o > h_constraint:
        print "h_0 bigger than the constraint..."
    return h_o


def equivalentHeightWet(frequency, pressure):
    """
    For frequencies <= 350 GHz
    """
    r_p = pressure/1013.0

    sigma_w = 1.013 / (1 + np.exp(-8.6 * (r_p - 0.57)))
    term1 = 1.39 * sigma_w / (np.power(frequency - 22.235, 2.0) + 2.56 * sigma_w)
    term2 = 3.37 * sigma_w / (np.power(frequency - 183.31, 2.0) + 4.69 * sigma_w)
    term3 = 1.58 * sigma_w / (np.power(frequency - 325.1, 2.0) + 2.89 * sigma_w)
    term_sum = np.sum((term1, term2, term3))

    return 1.66 * (1 + term_sum)


if __name__ == "__main__":
    x = list()
    res_dry = list()
    res_wet = list()
    res_tot = list()
    for f in np.arange(1, 50, 0.25, dtype=np.float64):
        gamma_dry = gammaDry(f, p, temp)
        gamma_wet = gammaWet(f, p, temp, rho)
        h_o = equivalentHeightDry(f, p)
        h_w = equivalentHeightWet(f, p)
        print('gamma_0: %5.3f gamma_w: %5.3f ho: %4.2f km hw: %4.2f'
              % (gamma_dry, gamma_wet, h_o, h_w))
        A_zenith = gamma_dry * h_o + gamma_wet * h_w
        A_slant = A_zenith / np.sin(elev * np.pi / 180.0)
        print("Total Zenith attenuation for lat %4.2f freq %4.2f GHz : "
              "%5.3f dB (%5.3f + %5.3f)"
              % (lat, f, A_zenith, gamma_dry * h_o, gamma_wet * h_w))
        print("Slant attenuation for %4.2f deg lat %4.2f freq %4.2f GHz : "
              "%5.3f dB"
              % (elev, lat, f, A_slant))
        res_dry.append(gamma_dry*h_o)
        res_wet.append(gamma_wet*h_w)
        res_tot.append(A_zenith)
        x.append(f)
    plt.plot(x, res_dry)
    plt.plot(x, res_wet)
    plt.plot(x, res_tot)
    plt.ylabel("Total zenith attenuation [dB]")
    plt.yscale("log")
    plt.xscale("log")
    plt.axis([1, 50, 0.001, 1])
    plt.grid(color="k", linestyle="-", linewidth=1)
    plt.grid(which="both", color="k", linestyle="-", linewidth=1)
    plt.show()
