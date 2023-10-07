# Run a docker container.
# this is just a wrapper.


import subprocess as sb
import configparser as cp
import pathlib as pl
import logging as log
import sys


def checkAV(av_config):
    """
    Run the antivirus part:
    1. Run the first time and create a quarantine file
    2. Check if the quarantine is over:
    2.1 If quarantine is over, run the antivirus one more time.
    2.2 If ingestion is still under quarantine, just exit.
    """

    quarentine_dir = pl.Path(av_config["quarantine_dir"])
    if not quarentine_dir.exists():
        log.warning(f"Creating quarantine dir '{quarentine_dir}'")
        quarentine_dir.mkdir()

    quarentine_file = (
        pl.Path(pl.Path.cwd())
        .joinpath(av_config["quarantine_dir"])
        .joinpath(av_config["av_accession"])
    )


def main() -> None:
    """
    Run a docker container.
    """

    config_file = sys.argv[1]

    # av_config = read_config(file_cfg, "CLAMAV")

    log.info(f"Reading configuration file '{config_file}'")
    config = cp.ConfigParser(interpolation=cp.ExtendedInterpolation())
    config.read(config_file)

    config["CLAMAV"].update({"av_location": config["BAGGER"]["source_dir"]})
    config["CLAMAV"].update({"av_accession": config["ACCESSION"]["accession_id"]})
    config["CLAMAV"].update({"quarantine_dir": "quarantine"})

    #
    # ClamAV

    #
    # Copy source files to destination folder


if __name__ == "__main__":
    main()
