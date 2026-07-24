import configparser

from .debug_log import trace


@trace
def read_ini(path: str) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(path)
    return cfg
