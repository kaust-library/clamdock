# Run a docker container.
# this is just a wrapper.


from subprocess import run, STDOUT, PIPE
from configparser import ConfigParser, ExtendedInterpolation
import sys

class Container:
    """
    Base class for container execution
    """

    def __init__(self, bin_dir: str, exe: str, parameters: list[str]) -> None:
        self.bin_dir = bin_dir
        self.exe = exe
        self.parameters = parameters


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

class quarantine:
    pass

class anti_virus(Container):
    def __init__(self, bin_dir: str, exe: str, parameters: list[str]) -> None:
        super().__init__(bin_dir, exe, parameters)
        
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
