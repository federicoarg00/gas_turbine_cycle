import numpy as np
import logging.config
from ..gases import IdealGas


def create_logger(name=__name__, loggerlevel=logging.INFO, add_file_handler=True,
                  add_console_handler=True, filename='logfile.log', filemode='a', add_datetime=False,
                  add_module_name=False):
    logger = logging.getLogger(name)
    logger.setLevel(loggerlevel)
    logger.propagate = 0
    datetime_template = '%(asctime)s - ' * add_datetime
    module_name_template = '%(name)s - ' * add_module_name
    fmt = datetime_template + module_name_template + '%(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt=fmt,
                                  datefmt='%d\%m\%Y %H:%M:%S')
    if add_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.NOTSET)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    if add_file_handler:
        file_handler = logging.FileHandler(filename, mode=filemode)
        file_handler.setLevel(logging.NOTSET)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def eta_comp_stag(pi_comp_stag, k, eta_comp_stag_p):
    """Адиабатический КПД компрессора в зависимости от политропического"""
    return (pi_comp_stag ** ((k - 1) / k) - 1) / (pi_comp_stag ** ((k - 1) / (k * eta_comp_stag_p)) - 1)


def eta_turb_stag(pi_turb_stag, k, eta_turb_stag_p):
    """Адиабатический КПД турбины в зависимости от политропического"""
    return (1 - pi_turb_stag ** ((1 - k) * eta_turb_stag_p / k)) / (1 - pi_turb_stag ** ((1 - k) / k))


def eta_turb_l(eta_turb_stag, H_turb_stag, H_turb, c_out):
    """Лопаточный КПД турбины через КПД по параметрам торможения"""
    return eta_turb_stag * H_turb_stag / H_turb + c_out ** 2 / (2 * H_turb)


def eta_comp_stag_p(pi_comp_stag, k, eta_comp_stag):
    """Политропический КПД компрессора."""
    log = np.log(1 + (pi_comp_stag ** ((k - 1) / k) - 1) / eta_comp_stag) / np.log(pi_comp_stag)
    return (k - 1) / (k * log)


def eta_turb_stag_p(pi_turb_stag, k, eta_turb_stag):
    """Политропический КПД турбины."""
    log = np.log(1 - eta_turb_stag * (1 - pi_turb_stag ** ((1 - k) / k))) / np.log(pi_turb_stag)
    return k * log / (1 - k)


def get_mixture_temp(comb_products: IdealGas, air: IdealGas, temp_comb_products, temp_air,
                     g_comb_products, g_air, alpha_mixture, precision=0.001):
    """Возвращает значение температуры смеси рабочего и охлаждающего тела, а также истинные теплоемкости газа и
    воздуха при температурах смешения."""
    mixture = type(comb_products)()
    air.__init__()
    mixture.alpha = alpha_mixture

    mix_temp = None
    mixture.T = temp_comb_products
    mix_temp_new = temp_comb_products
    temp_mix_res = 1.

    comb_products.T = temp_comb_products
    air.T = temp_air
    c_p_comb_products_av = comb_products.c_p_av
    c_p_air_av = air.c_p_av

    while temp_mix_res >= precision:
        mix_temp = mix_temp_new
        mixture.T = mix_temp_new
        enthalpy_comb_products = c_p_comb_products_av * (temp_comb_products - comb_products.T0) * g_comb_products
        enthalpy_air = c_p_air_av * (temp_air - air.T0) * g_air
        mix_temp_new = (
                (enthalpy_air + enthalpy_comb_products) / (mixture.c_p_av * (g_air + g_comb_products)) + mixture.T0
        )
        temp_mix_res = abs(mix_temp_new - mix_temp) / mix_temp

    return mix_temp_new, mixture, c_p_comb_products_av, c_p_air_av, mix_temp, temp_mix_res
