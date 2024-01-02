import datetime as dt
import logging as log
import sys


from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from typing import List
from subprocess import run, PIPE, STDOUT
from tempfile import NamedTemporaryFile


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

    # Scan each directory in the input list.
    av_target_list = str2list(av_config["av_location"])
    for av_target_dir in av_target_list:
        docker_dest_name = Path(av_target_dir).name
        docker_dest = f'-v "{av_target_dir}:/{docker_dest_name}"'
        clam_run = f"clamav/clamav:latest clamscan /{docker_dest_name}"
        av_check = f"{docker_run} {docker_dest} {docker_log_target} {clam_db} {clam_run} {log_av} {clam_options}"
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
    docker_dest = f'-v "{dest}:/dest"'
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
            f"{docker_run} {docker_source} {docker_dest} {docker_image} {copy_cmd}"
        )
        log.debug(f"Running command: {copy_files}")
        result = run(copy_files, stdout=PIPE, stderr=STDOUT)
        result.returncode


def createBag(config, bag_data):
    """
    Create a Bag structure with `bag_data` in directory `dest_dir` specified
    in `config`. The bag_data is passed to the docker container via a
    temporary file with the environment variables.
    """

    bag_dest_dir = Path(config["dest_dir"])

    # Start defining the parameters for docker run.
    docker_run = "docker run --rm --name mkbag"
    docker_dest = f'-v "{bag_dest_dir}:/mydir"'
    docker_image = "mybagit"

    # Here we create the temporary file with the data for the Bag. Once the
    # context manager (CM) finishes the file deleted, therefore we call
    # docker inside the it.
    with NamedTemporaryFile(mode="w", delete_on_close=False) as ff:
        ff.write(f"SOURCE_ORGANIZATION={bag_data['Source-Organization']}\n")
        ff.write(f"EXTERNAL_IDENTIFIER={bag_data['External-Identifier']}\n")
        ff.write(
            f"INTERNAL_SENDER_DESCRIPTION={bag_data['Internal-Sender-Description']}\n"
        )
        ff.write(f"TITLE={bag_data['Title']}\n")
        ff.write(f"DATE_START={bag_data['Date-Start']}\n")
        ff.write(f"RECORD_CREATORS={bag_data['Record-Creators']}\n")
        ff.write(f"RECORD_TYPE={bag_data['Record-Type']}\n")
        ff.write(f"EXTEND_SIZE={bag_data['Extend-Size']}\n")
        ff.write(f"SUBJECTS={bag_data['Subjects']}\n")
        ff.write(f"OFFICE={bag_data['Office']}\n")
        ff.write(f"BAG_PATH={config['dest_dir']}")
        ff.close()

        docker_env_file = f"--env-file {ff.name}"
        mk_bag = f"{docker_run} {docker_env_file} {docker_dest} {docker_image} "
        log.debug("Docker command:")
        log.debug(mk_bag)
        result = run(mk_bag, stdout=PIPE, stderr=STDOUT)
        # CM end.

    log.debug("Output from th docker command:")
    log.debug(result.stdout)
    result.returncode


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

    # Update the ClamAV with extra variables. This is just convenience.
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

    # Create the bag.

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
