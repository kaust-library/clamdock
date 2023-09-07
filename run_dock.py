# Run a docker container.
# this is just a wrapper.


from subprocess import run, STDOUT, PIPE
from configparser import ConfigParser, ExtendedInterpolation
import sys

class ConfigIngestion:
    def __init__(self) -> None:
        pass

    def getConfigSections(self) -> list[str]:
        """
        Returns a list with the sections available on the config file.
        """

        config = ConfigParser()
        config.read(ingestion.config_file)

        print(f"ConfigIngestion: sections: {config.sections}")

        return config.sections()

class Ingestion:
    """
    Base class for ingesting objects with the digital preservation workflow
    """

    def __init__(self, config_file: str) -> None:
        self.config_file = config_file
        self.sections = []

    config = ConfigIngestion()
    config.getConfigSections()


    
def main() -> None:
    """
    Run a docker container.
    """

    config_file = sys.argv[1]

    # av_config = read_config(file_cfg, "CLAMAV")

    Ingestion(config_file)


if __name__ == "__main__":
    main()
