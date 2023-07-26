# Run a docker container.
# this is just a wrapper.


from subprocess import run, STDOUT, PIPE
from configparser import ConfigParser, ExtendedInterpolation

import sys

def read_config(file_cfg: str, section):
    """
    Read the config file and return a section
    """

    cfg = ConfigParser(interpolation=ExtendedInterpolation)
    cfg.read(file_cfg)

    return cfg[section]


def main() -> None:
    """
    Run a docker container.
    """

    file_cfg = sys.argv[1]

    av_config = read_config(file_cfg, "CLAMAV")

    
if __name__ == "__main__":
    main()
