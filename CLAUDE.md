# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clamdock is a digital preservation workflow system that orchestrates multiple Docker containers to process files through antivirus scanning, file format identification, validation, and BagIt package creation. The system is designed for institutional digital preservation workflows.

## Core Architecture

The main orchestration script is `run_dock.py`, which coordinates a multi-stage workflow:

1. **Antivirus Scanning**: Uses ClamAV in Docker to scan source files with quarantine periods
2. **File Copying**: Copies source files to destination using Debian container
3. **BagIt Creation**: Creates BagIt packages with metadata using custom Python container
4. **Format Identification**: Uses DROID container for file format analysis
5. **Validation**: Uses JHOVE container for file format validation

## Key Components

- `run_dock.py`: Main workflow orchestrator (419 lines)
- `app/bagdata.py`: BagIt package creation script for Docker container
- Configuration files (`*.cfg`): Define workflow parameters and tool settings
- Multiple Dockerfiles for different tools (bagit, jhove, droid)

## Development Commands

### Running the Workflow
```bash
python run_dock.py <config_file>
```

### Docker Operations
Build containers:
```bash
docker build -f Dockerfile.bagit -t mybagit .
docker build -f Dockerfile.jhove -t myjhove .
docker build -f Dockerfile.droid -t mydroid .
```

Create ClamAV database volume:
```bash
docker volume create clamdb
```

## Configuration System

The system uses ConfigParser with ExtendedInterpolation. Configuration sections:
- `USER`: UID/GID for Docker containers
- `ACCESSION`: Accession identifier
- `BAGGER`: Source/destination directories  
- `CLAMAV`: Antivirus settings, quarantine configuration
- `DROID`: File format identification settings
- `JHOVE`: Validation settings and module selection

## Workflow Logic

1. **Quarantine Check**: Implements a quarantine period after initial AV scan
2. **Two-Pass AV**: Initial scan creates quarantine file, second scan after quarantine period
3. **Sequential Processing**: Only proceeds to next stage if previous stage succeeds
4. **Error Handling**: Critical failures stop the workflow

## Docker Integration

All processing tools run in isolated Docker containers with volume mounts for:
- Source data (read-only)
- Destination directories
- Log outputs
- Persistent virus database

## Important Notes

- The system requires manual creation of certain directories and Docker volumes before first run
- Quarantine functionality prevents immediate processing of scanned files
- All file operations preserve ownership using configurable UID/GID
- The workflow is designed to be resumable after quarantine periods expire