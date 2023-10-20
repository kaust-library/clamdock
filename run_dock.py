# Run a docker container.
# this is just a wrapper.


import subprocess as sp
import configparser as cp
import pathlib as pl
import datetime as dt
import logging as log
import sys


# def checkAV(av_config):
#     """
#     Run the antivirus part:
#     1. Run the first time and create a quarantine file
#     2. Check if the quarantine is over:
#     2.1 If quarantine is over, run the antivirus one more time.
#     2.2 If ingestion is still under quarantine, just exit.
#     """

#     quarentine_dir = pl.Path(av_config["quarantine_dir"])
#     if not quarentine_dir.exists():
#         log.warning(f"Creating quarantine dir '{quarentine_dir}'")
#         quarentine_dir.mkdir()

#     quarentine_file = (
#         pl.Path(pl.Path.cwd())
#         .joinpath(av_config["quarantine_dir"])
#         .joinpath(av_config["av_accession"])
#     )


def runAV(av_config):
    dt_run_av = dt.datetime.today().strftime("%Y%m%d")

    #
    # Update antivirus database.
    log.info("Updating AV database")
    av_update = """docker run -it --rm 
    --name fresh_clam_db --mount source=clam_db,target=/var/lib/clamav 
    clamav/clamav:latest freshclam"""
    result = sp.run(av_update, stdout=sp.PIPE, stderr=sp.STDOUT, text=True)

    #
    # Antivirus.
    av_log_file = f"clamAVlog{av_config['av_accession']}_{dt_run_av}.txt"
    docker_run = f"docker run --rm --name aa_docker"
    docker_target = f"-v \"{av_config['av_location']}:/scandir\""
    docker_log_target = f"-v \"{av_config['av_logs_root']}:/logs\""
    clam_db = "--mount source=clam_db,target=/var/lib/clamav"
    clam_run = "clamav/clamav:latest clamscan /scandir"
    clam_options = " --recursive=yes --verbose"
    log_av = f"--log=/logs/{av_log_file}"
    av_check = f"{docker_run} {docker_target} {docker_log_target} {clam_db} {clam_run} {log_av} {clam_options}"
    log.info(f"Antivirus check: {av_check}")
    result = sp.run(av_check, stdout=sp.PIPE, stderr=sp.STDOUT)
    result.check_returncode
    av_log = result.stdout


def copyFiles(f_config):
    src = [ff.strip() for ff in f_config["source_dir"].split(",")]
    dest = f_config["dest_dir"]

    #
    # Docker container to copy files
    docker_run = "docker run --rm --name copy_files"
    docker_target = f"-v {dest}:/dest"
    docker_image = "debian:bookworm-slim"
    copy_cmd = "cp -pr /src /dest"

    for ss in src:
        log.info(f"Copying files from '{ss}' to '{dest}'")
        docker_source = f"-v {ss}:/src"
        copy_files = (
            f"{docker_run} {docker_source} {docker_target} {docker_image} {copy_cmd}"
        )
        result = sp.run(copy_files, stdout=sp.PIPE, stderr=sp.STDOUT)
        result.returncode


def main() -> None:
    #
    # Logging
    log.basicConfig(level=log.INFO, format="%(asctime)s %(message)s")
    #
    # Input file
    config_file = sys.argv[1]

    #
    # Set system configuration
    log.info(f"Reading configuration file '{config_file}'")
    config = cp.ConfigParser(interpolation=cp.ExtendedInterpolation())
    config.read(config_file)

    config["CLAMAV"].update({"av_location": config["BAGGER"]["source_dir"]})
    config["CLAMAV"].update({"av_accession": config["ACCESSION"]["accession_id"]})
    config["CLAMAV"].update({"quarantine_dir": "quarantine"})

    #
    # ClamAV
    # runAV(config['CLAMAV'])

    #
    # Copy source files to destination folder
    log.info("Copying files")
    copyFiles(config["BAGGER"])

    BagIt_test = {
        "Source-Organization": "KAUST",
        "External-Identifier": "My External Identifier",
        "Internal-Sender-Description": "My Internal Sender",
        "Title": "Test Title",
        "Date-Start": "2020-10-10",
        "Record-Creators": "Marcelo",
        "Record-Type": "Photos",
        "Extend-Size": "23456",
        "Subjects": "My subjects",
        "Office": "Library",
    }


if __name__ == "__main__":
    main()
