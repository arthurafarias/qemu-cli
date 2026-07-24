import configparser


def read_ini(path: str) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path)
    return cfg
