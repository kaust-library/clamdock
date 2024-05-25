import logging as log
import sys


from configparser import ConfigParser, ExtendedInterpolation
from pathlib import Path
from typing import List
from subprocess import run, PIPE, STDOUT
from tempfile import NamedTemporaryFile
from os import chdir
from datetime import date, timedelta


def str2list(ss: str) -> List:
    """
    Convert a comma separated string ("aa, bb, cc") into a list ['aa', 'bb', 'cc'].
    """

    return [sss.strip() for sss in ss.split(",")]


def is_av_vol(vol_name: str) -> bool:
    """Check if volume for persistent anti-virus database already exists"""
    inspect_vol = f"docker volume inspect {vol_name}"

    result = run(inspect_vol, shell=True, stdout=PIPE, stderr=STDOUT, text=True)
    vol = result.stdout.strip().split()
    if vol[0] == "[]":
        return False
    else:
        return True


def create_av_vol(vol_name: str) -> None:
    """Create volume 'vol_name' for anti-virus persistent database"""

    create_vol = f"docker volume create {vol_name}"
    result = run(create_vol, shell=True, stdout=PIPE, stderr=STDOUT, text=True)
    vol_created = result.stdout.strip()
    print(vol_name, vol_created)
    if vol_created != vol_name:
        log.critical("Something went wrong creating the antivirus volume!")
        raise Exception("Error creating AV volume")
    else:
        log.info("Volume for anti-virus database created successfully")


def is_infected(av_log: str) -> bool:
    """Check if there is an infected file in the antivirus log"""

    is_infected = True
    text = av_log.strip().split("\n")
    print(text)
    total_line = text[-7]
    infect_line = text[-6]
    scanned_files = total_line.split()[-1]
    infect_field, infect_num = infect_line.split()[0], infect_line.split()[2]
    if int(scanned_files) == 0:
        log.critical(f"No scanned files. Something wrong. Please check AV logs.")
        sys.exit(1)
    print(f"Scanned {scanned_files} files")
    if infect_field == "Infected" and int(infect_num) == 0:
        print(f"OK: no infected files")
        is_infected = False
    elif infect_line == "Infected" and int(infect_num) != 0:
        if int(infect_num) == 1:
            print(f"Caution: there is 1 infected file!!!!!")
        else:
            print(f"Caution: there are {infect_num} infected files!!!!!")
    else:
        print(f"Error: could not find 'Infected' line in the output")

    return is_infected


def runAV(av_config: ConfigParser) -> None:
    dt_run_av = date.today().strftime("%Y%m%d")

    #
    # Check if volume exists.
    av_vol = av_config["av_volume"]
    if not is_av_vol(av_vol):
        log.warning(f"Volume for AV database not found. Creating volume {av_vol}")
        create_av_vol(av_vol)
    else:
        log.info(f"Volume '{av_vol}'for AV database found")
    #
    # Update antivirus database.
    log.info("Updating AV database")
    av_update = """docker run -it --rm --name 'freshclamdb'  \
    --mount source=clamdb,target=/var/lib/clamav  \
    clamav/clamav:latest freshclam"""
    result = run(av_update, shell=True, stdout=PIPE, stderr=STDOUT, text=True)
    log.info("Update of AV database done")
    log.debug("Output of AV database update:")
    log.debug(result.stdout)

    #
    # Antivirus.
    av_log_file = f"clamAVlog{av_config['av_accession']}_{dt_run_av}.txt"
    docker_run = f"docker run --rm --name clamAV "
    # docker_user = f"--user={av_config['uid']}:{av_config['gid']}"
    docker_user = f"--user=root:root"
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
        av_check = f"{docker_run} {docker_user} {docker_dest} {docker_log_target} {clam_db} {clam_run} {log_av} {clam_options}"
        log.info(f"AV scanning: '{av_target_dir}'")
        log.debug(f"Antivirus check: {av_check}")
        result = run(av_check, shell=True, stdout=PIPE, stderr=STDOUT, text=True)
        result.check_returncode
        if is_infected(result.stdout):
            raise (f"Possible infected file in {{av_target_dir}}")


def copyFiles(f_config: ConfigParser) -> None:
    src = str2list(f_config["source_dir"])
    dest = Path(f_config["dest_dir"])

    if not dest.exists():
        log.info(f"Creating destination directory: '{dest}'")
        dest.mkdir()

    #
    # Docker container to copy files
    docker_run = "docker run --rm --name copy_files"
    docker_dest = f'-v "{dest}:/dest"'
    docker_user = f"--user={f_config['uid']}:{f_config['gid']}"
    docker_image = "debian:bookworm-slim"

    for ss in src:
        log.info(f"Copying files from '{ss}' to '{dest}'")
        ss_name = Path(ss).name
        if not Path(ss).is_dir():
            log.critical(f"Source '{ss}' is not a directory is not accessible")
            raise Exception("Source directory invalid")
        docker_source = f'-v "{ss}:/{ss_name}"'
        copy_cmd = f"cp -pr /{ss_name} /dest"

        copy_files = f"{docker_run} {docker_user} {docker_source} {docker_dest} {docker_image} {copy_cmd}"
        log.debug(f"Running command: {copy_files}")
        result = run(copy_files, shell=True, stdout=PIPE, stderr=STDOUT)
        result.returncode


def createBag(config: ConfigParser, bag_data: dict) -> None:
    """
    Create a Bag structure with `bag_data` in directory `dest_dir` specified
    in `config`. The bag_data is passed to the docker container via a
    temporary file with the environment variables.
    """

    bag_dest_dir = Path(config["dest_dir"])

    # Start defining the parameters for docker run.
    docker_run = "docker run --rm --name mkbag"
    docker_user = f"--user={config['uid']}:{config['gid']}"
    docker_dest = f'-v "{bag_dest_dir}:/mydir"'
    docker_image = "mybagit"

    # Here we create the temporary file with the data for the Bag. Once the
    # context manager (CM) finishes the file deleted, therefore we call
    # docker inside the it.
    with NamedTemporaryFile(mode="w", delete=False) as ff:
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
        mk_bag = f"{docker_run} {docker_user} {docker_env_file} {docker_dest} {docker_image} "
        log.debug("Docker command:")
        log.debug(mk_bag)
        result = run(mk_bag, shell=True, stdout=PIPE, stderr=STDOUT)
        # Remove the temporary file
        log.info("Removing temporary file")
        Path(ff.name).unlink()
        # CM end.

    log.debug("Output from th docker command:")
    log.debug(result.stdout)
    result.returncode


def runDroid(config: ConfigParser) -> None:
    """
    Run DROID in two steps: create profile, and export profile to CSV.
    """

    droid_dir = Path(config["bag_dir"])
    droid_data = droid_dir.joinpath("data")
    accession_id = config["accession_id"]

    chdir(droid_data)
    docker_run = "docker run --rm --name droid"
    docker_user = f"--user={config['uid']}:{config['gid']}"
    docker_image = "mydroid"

    docker_droid = f"-v {droid_dir}:/droid"
    docker_data = f'-v "{Path.cwd()}:/data"'

    # Create DROID profile
    droid_profile = f"-a /data/ --recurse -p /droid/{accession_id}.droid"
    docker_cmd = f"{docker_run} {docker_user} {docker_droid} {docker_data} {docker_image} {droid_profile}"
    log.info("Creating DROID profile")
    log.debug("DROID profile command:")
    log.debug(docker_cmd)
    result = run(docker_cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    log.debug("Output from the docker command:")
    log.debug(result.stdout)
    result.returncode

    # Convert profile to CSV
    droid_csv = f" -p /droid/{accession_id}.droid -e /droid/{accession_id}.csv"
    docker_cmd = f"{docker_run} {docker_user} {docker_droid} {docker_image} {droid_csv}"
    log.info("Exporting DROID profile to CSV")
    log.debug("DROID csv command:")
    log.debug(docker_cmd)
    result = run(docker_cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    log.debug("Output from the docker command:")
    log.debug(result.stdout)
    result.returncode


def runJhove(config: ConfigParser, modules: ConfigParser) -> None:
    """
    Run JHOVE
    docker run --rm --name jhove \
        -v ~/Work/clamdock_data/dest/000_000_0000:/jhove \
        -v ~/Work/clamdock_data/dest/000_000_0000/data:/data myjhove \
        -o /jhove/test.xml -m PDF-hul -kr /data
    """

    modules_list = [kk for (kk, vv) in modules.items() if modules.getboolean(kk)]

    jhove_dir = Path(config["bag_dir"])
    jhove_data = jhove_dir.joinpath("data")

    accession_id = config["accession_id"]

    docker_run = "docker run --rm --name jhove"
    docker_user = f"--user={config['uid']}:{config['gid']}"
    docker_image = "myjhove"
    docker_bag = f'-v "{jhove_dir}:/jhove"'
    docker_data = f'-v "{jhove_data}:/data"'

    log.info("Running JHOVE container")

    for mm in modules_list:
        # Module name for name of output file
        module_name = mm.split("-")[0]

        if config.getboolean("jhove_xml"):
            module_output = f"-h xml -o /jhove/jhove_{accession_id}_{module_name}.xml"
        else:
            module_output = f"-o /jhove/jhove_{accession_id}_{module_name}.txt"

        docker_cmd = f"{docker_run} {docker_user} {docker_bag} {docker_data} {docker_image} -m {mm} {module_output} -kr /data"

        log.debug(f"Docker command: \n {docker_cmd}")
        result = run(docker_cmd, shell=True, stdout=PIPE, stderr=STDOUT)
        log.debug("Output from the docker command:")
        log.debug(result.stdout)
        result.returncode

    log.info("JHOVE done.")


def is_over_quarantine(quarantine_file: Path) -> bool:
    """Check if quarantine is over:
    today >= creation_date + quarantine days
    """

    with open(quarantine_file, "r") as fin:
        quar_date = fin.readline().strip()
        quar_days = int(fin.readline())

    today = date.today()
    av_check = date.fromisoformat(quar_date)

    return today > av_check + timedelta(days=quar_days)


def create_quarantine_file(config_av: ConfigParser) -> None:
    """Create the quarantine file in the format:
    YYYY-MM-DD (today)
    99 (quarantine_duration)
    """

    av_today = date.today().isoformat()

    with open(config_av["quarantine_file"], "w") as fout:
        fout.write(av_today + "\n")
        fout.write(config_av["quarantine_days"] + "\n")


def get_user(config: ConfigParser) -> str:
    """Check if the user and group were provided in the configuration file.
    If not, then we set 'root' for user and group."""

    if config.has_section("USER"):
        uid = config["USER"].get("uid", "root")
        gid = config["USER"].get("gid", "root")
    else:
        uid = "root"
        gid = "root"

    return uid, gid


def main() -> None:
    #
    # Logging
    log.basicConfig(level=log.DEBUG)
    #
    # Input file
    try:
        config_file = sys.argv[1]
    except IndexError:
        raise FileNotFoundError("Accession configuration file not provided")

    #
    # Set system configuration
    try:
        log.info(f"Reading configuration file '{config_file}'")
        config = ConfigParser(interpolation=ExtendedInterpolation())
        config.read(config_file)
    except UnboundLocalError:
        log.error("Probably the config file parameter was not provded")
        raise Exception("Variable with file has a problem")

    uid, gid = get_user(config)

    # Update the ClamAV with extra variables. This is just convenience.
    config["CLAMAV"].update({"av_location": config["BAGGER"]["source_dir"]})
    config["CLAMAV"].update({"av_accession": config["ACCESSION"]["accession_id"]})
    config["CLAMAV"].update({"uid": uid})
    config["CLAMAV"].update({"gid": gid})

    quarantine_file = Path(config["CLAMAV"]["quarantine_file"])

    log.info("Checking if quarantine is over")
    if quarantine_file.exists():
        if is_over_quarantine(quarantine_file):
            log.info("Quarantine is over")
            log.info("Running AV check for second time")
            runAV(config["CLAMAV"])
        else:
            log.info("Quarantine not over")
            sys.exit(0)
    else:
        log.info("Running first AV check")
        runAV(config["CLAMAV"])
        # if the AV check was successfull, create the quarantine file.
        log.info("Creating quarantine file")
        create_quarantine_file(config["CLAMAV"])
        log.info("Starting the quarantine period. Come back when it's over")
        sys.exit(0)

    #
    # Copy source files to destination folder
    config["BAGGER"].update({"uid": uid})
    config["BAGGER"].update({"gid": gid})
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

    # Add the destination folder and accession id to the 'DROID' section.
    config["DROID"].update({"bag_dir": config["BAGGER"]["dest_dir"]})
    config["DROID"].update({"accession_id": config["ACCESSION"]["accession_id"]})
    config["DROID"].update({"uid": uid})
    config["DROID"].update({"gid": gid})
    runDroid(config["DROID"])

    # Add BagIt folder and accession id to JHOVE section
    config["JHOVE"].update({"bag_dir": config["BAGGER"]["dest_dir"]})
    config["JHOVE"].update({"accession_id": config["ACCESSION"]["accession_id"]})
    config["JHOVE"].update({"uid": uid})
    config["JHOVE"].update({"gid": gid})
    runJhove(config["JHOVE"], config["JHOVE MODULES"])


if __name__ == "__main__":
    main()
