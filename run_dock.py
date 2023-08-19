# Run a docker container.
# this is just a wrapper.


from subprocess import run, STDOUT, PIPE
from configparser import ConfigParser, ExtendedInterpolation
import sys


class Container:
    """
    Base class for container execution
    """

    def __init__(self, bin_dir: str, exe: str) -> None:
        self.bin_dir = bin_dir
        self.exe = exe

class Quarantine:
    pass    

class anti_virus(Container):
    def __init__(self, av_dir: str, av_bin: str, config) -> None:
        super().__init__(bin_dir=av_dir, exe=av_bin)
        av_update = config.get('av_update')
        log_dir = config.get('av_logs_root', raw=True)
        quarantine = config.getint('quarantine', '30')
        run_it = config.getbool('run_it', 'True')


        

class Ingestion:
    """
    Base class for ingesting objects with the digital preservation workflow
    """

    def __init__(self, config_file:str) -> None:
        self.config_file = config_file

    def read_config(self):
        """Read the ingestion configuration file"""
        cfg = ConfigParser(interpolation=ExtendedInterpolation())
        cfg.read(self.config_file)

        return cfg


def main() -> None:
    """
    Run a docker container.
    """

    file_cfg = sys.argv[1]

    # av_config = read_config(file_cfg, "CLAMAV")

    ingest = Ingestion(file_cfg)

    cfg = ingest.read_config()

    print(cfg['CLAMAV'])


    
if __name__ == "__main__":
    main()
