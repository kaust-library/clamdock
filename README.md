# Clamdock

 Running ClamAV inside Docker

## ER Diagram

```mermaid
erDiagram
    Ingestion || --|| AnvitVirus : scan
    AnvitVirus || -- || Quarantine : wait
    Quarantine || -- || AnvitVirus : run
    Ingestion || -- || Bag : create
    Bag || -- || DROID : metadata
    Bag || -- || JHOVE : metadata
```

## Class Diagram

```mermaid
classDiagram
    Ingestion *-- AntiVirus
    Ingestion o-- Bag
    AntiVirus *-- Quarantine
    Bag o-- Metadata
    Metadata <|-- Droid
    Metadata <|-- JHove

    class Ingestion
    Ingestion: str AccessionID

    class AntiVirus
    AntiVirus: str BinDir
    AntiVirus: str ExeUpdate
    AntiVirus: str ExeScan
    AntiVirus: str LogDir
    AntiVirus: str LogFile

    class Quarantine
    Quarantine: str quarFile
    Quarantine: int quarDays

    class Bag
    Bag: list SourceDirs
    Bag: str SourceDir
    Bag: str DestDir

    class Metadata

    class Droid
    Droid: str DroidDir
    Droid: str DroidExe
    Droid: bool keepProfile

    class JHove
    JHove: str JHoveDir
    JHove: str JHoveExe
    JHove: bool JHoveXML
    JHove: list JHoveModules
```

## Running Container

Running the ClamAV container directly from command line as test.

The container will mount the local file system with mount _bind_.

Running from command line. Interestingly when there is a space in the path, docker only works with `-v` option

```
docker run  --rm --name clam_test -v 'C:\Users\garcm0b\Downloads\autoarchive\2018batch\Image_Files\Image Files\Heno:/scandir' -v 'C:\Users\garcm0b\Downloads\Work_Test:/log' clamav/clamav:latest clamscan /scandir  --verbose  --recursive=yes  --alert --log=/log/test.txt
Starting Freshclamd
Starting ClamAV
(...)
```
