# Run a docker container.
# this is just a wrapper.


import datetime as dt
import logging as log
import sys


from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from typing import List
from subprocess import run, PIPE, STDOUT


def str2list(ss: str) -> List:
    """
    Convert a comma separated string ("aa, bb, cc") into a list ['aa', 'bb', 'cc'].
    """

    return [sss.strip() for sss in ss.split(",")]


def runAV(av_config):
    dt_run_av = dt.datetime.today().strftime("%Y%m%d")

    #
    # Update antivirus database.
    log.info("Updating AV database")
    av_update = """docker run -it --rm --name 'freshclamdb' 
    --mount source=clamdb,target=/var/lib/clamav 
    clamav/clamav:latest freshclam"""
    result = run(av_update, stdout=PIPE, stderr=STDOUT, text=True)
    log.info("Update of AV database done")

    #
    # Antivirus.
    av_log_file = f"clamAVlog{av_config['av_accession']}_{dt_run_av}.txt"
    docker_run = f"docker run --rm --name clamAV"
    docker_log_target = f"-v \"{av_config['av_logs_root']}:/logs\""
    clam_db = "--mount source=clamdb,target=/var/lib/clamav"
    clam_options = " --recursive=yes --verbose"
    log_av = f"--log=/logs/{av_log_file}"

    av_target_list = str2list(av_config["av_location"])
    for av_target_dir in av_target_list:
        docker_target_name = Path(av_target_dir).name
        docker_target = f'-v "{av_target_dir}:/{docker_target_name}"'
        clam_run = f"clamav/clamav:latest clamscan /{docker_target_name}"
        av_check = f"{docker_run} {docker_target} {docker_log_target} {clam_db} {clam_run} {log_av} {clam_options}"
        log.info(f"AV scanning: '{av_target_dir}'")
        log.debug(f"Antivirus check: {av_check}")
        result = run(av_check, stdout=PIPE, stderr=STDOUT)
        result.check_returncode


def copyFiles(f_config):
    src = str2list(f_config["source_dir"])
    dest = f_config["dest_dir"]

    #
    # Docker container to copy files
    docker_run = "docker run --rm --name copy_files"
    docker_target = f'-v "{dest}:/dest"'
    docker_image = "debian:bookworm-slim"

    for ss in src:
        log.info(f"Copying files from '{ss}' to '{dest}'")
        ss_name = Path(ss).name
        if not Path(ss).is_dir():
            log.critical(f"Source '{ss}' is not a directory is not accessible")
            raise Exception("Source directory invalid")
        docker_source = f'-v "{ss}:/{ss_name}"'
        copy_cmd = f"cp -pr /{ss_name} /dest"

        copy_files = (
            f"{docker_run} {docker_source} {docker_target} {docker_image} {copy_cmd}"
        )
        log.debug(f"Running command: {copy_files}")
        result = run(copy_files, stdout=PIPE, stderr=STDOUT)
        result.returncode


def createBag(config, bag_data):
    docker_env = """
        -e SOURCE_ORGANIZATION=f"{bag_data['Source-Organization']}" \
        -e EXTERNAL_IDENTIFIER=f"{bag_data['External-Identifier']}" \
        -e INTERNAL_SENDER_DESCRIPTION=f"{bag_data['Internal-Sender-Description']}" \
        -e TITLE=f"{bag_data['Title']}" \
        -e DATE_START=f"{bag_data['Date-Start']}" \
        -e RECORD_CREATORS=f"{bag_data['Record-Creators']}" \
        -e RECORD_TYPE=f"{bag_data['Record-Type']}" \
        -e EXTEND_SIZE=f"{bag_data[''Extend-Size]}" \
        -e SUBJECTS=f"{bag_data['Subjects']}" \
        -e OFFICE=f"{bag_data['Office']}"
    """


def main() -> None:
    #
    # Logging
    log.basicConfig(level=log.INFO)
    #
    # Input file
    try:
        config_file = sys.argv[1]
    except IndexError:
        log.error("Input file must be provided")

    #
    # Set system configuration
    try:
        log.info(f"Reading configuration file '{config_file}'")
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.read(config_file)
    except UnboundLocalError:
        log.error("Probably the config file parameter was not provded")
        raise Exception("Variable with file has a problem")

    config["CLAMAV"].update({"av_location": config["BAGGER"]["source_dir"]})
    config["CLAMAV"].update({"av_accession": config["ACCESSION"]["accession_id"]})
    config["CLAMAV"].update({"quarantine_dir": "quarantine"})

    #
    # ClamAV
    runAV(config["CLAMAV"])

    #
    # TODO
    # Add quarantine.

    #
    # Copy source files to destination folder
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

    log.info("Creating bag")
    createBag(config["BAGGER"], BagIt_test)


if __name__ == "__main__":
    main()
