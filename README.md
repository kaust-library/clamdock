# Clamdock

Running ClamAV inside Docker

## Apache Airflow

Running Airflow on Linux requires [setting AIRFLOW_UID](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#setting-the-right-airflow-user):

```
a-garcm0b@library-docker-test:~/Work/clamdock$ AIRFLOW_UID=50000
a-garcm0b@library-docker-test:~/Work/clamdock$ mkdir -p ./dags ./logs ./plugins ./config
a-garcm0b@library-docker-test:~/Work/clamdock$ echo -e "AIRFLOW_UID=$(id -u)" > .env
a-garcm0b@library-docker-test:~/Work/clamdock$ docker compose up
[+] Running 7/7
✔ Container clamdock-postgres-1           Created
(...)
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

## Copy Container

Using a container to copy files for the bagIt folder

```
PS C:\Users\garcm0b\Work> docker run -it --rm --name cp_test `
>> -v "C:\Users\garcm0b\OneDrive - KAUST\Pictures\social_hour:/src" `
>> -v "C:\Users\garcm0b\Work\test_cp_container:/dest" `
>> debian:bookworm-slim cp -pr /src /dest
PS C:\Users\garcm0b\Work>
```

## BagIt

### Building

Build the container using the `Dockerfile.bagit`

```
PS C:\Users\mgarcia\Work\clamdock> docker build -f Dockerfile.bagit -t mybagit .
[+] Building 3.0s (6/6) FINISHED
docker:default
 => [internal] load .dockerignore                                0.0s
 => => transferring context: 2B
 (...)
```

### Running

After building the container, you can use it to create a _bag_ file

```
PS C:\Users\mgarcia\Work\clamdock> mkdir mybag
PS C:\Users\mgarcia\Work\clamdock> docker run -it --rm -v "C:\Users\mgarcia\Work\clamdock\mybag:/mydir" --name mgbagit mybagit bagit.py --contact-name 'john' /mydir
2023-10-14 17:38:37,726 - INFO - Creating bag for directory /mydir
2023-10-14 17:38:37,733 - INFO - Creating data directory
(...)
```

## Jhove

Installing Jhove on the container

```
PS C:\Users\garcm0b\Work\clamdock> docker run -it --rm -v "C:\Users\garcm0b\Work\clamdock\files:/work" --name jhove ibmjava
root@2e4e123483a9:/work# java -jar jhove-latest.jar auto-install.xml
root@2e4e123483a9:/opt/jhove# ./jhove
Jhove (Rel. 1.28.0, 2023-05-18)
 Date: 2023-08-14 06:39:56 GMT
 App:
  API: 1.28.0, 2023-05-18
  Configuration: /opt/jhove/conf/jhove.conf
(...)
```

Or building, and running, our own container with Jhove

```
PS C:\Users\garcm0b\Work\clamdock> docker build -f Dockerfile.jhove -t myjhove .
PS C:\Users\garcm0b\Work\clamdock> docker run -it --rm -v 'C:\Users\mgarcia\Documents:/myfiles' --name mgjhove myjhove -m PDF-hul /myfiles/2020.nlpcovid19-acl.1.pdf
Jhove (Rel. 1.28.0, 2023-05-18)
 Date: 2023-08-25 14:54:58 GMT
 RepresentationInformation: /myfiles/2020.nlpcovid19-acl.1.pdf
  ReportingModule: PDF-hul, Rel. 1.12.4 (2023-03-16)
  LastModified: 2022-04-07 18:56:01 GMT
  Size: 3536281
  Format: PDF
  Version: 1.5
  Status: Well-Formed and valid
  (...)
```

## DROID

### Prequisite

Download [DROID](https://www.nationalarchives.gov.uk/information-management/manage-information/preserving-digital-records/droid/) for all platforms (instead of the Windows version), and extract the archive into the _files_ directory

```
PS C:\Users\mgarcia\Downloads> expand-Archive -path '.\droid-binary-6.6.1-bin.zip' -destination 'C:\Users\mgarcia\Work\clamdock\files\droid'
```

Building the container

```
PS C:\Users\mgarcia\Work\clamdock> docker build -f Dockerfile.droid -t mydroid .
```

Running the DROID contaner

```
PS C:\Users\mgarcia\Downloads> docker run -it --rm -v 'C:\Users\mgarcia\Documents\Sparkasse\:/mydata' --name mgdroid mydroid -a /mydata --recurse
"ID","PARENT_ID","URI","FILE_PATH","NAME","METHOD","STATUS","SIZE","TYPE","EXT","LAST_MODIFIED","EXTENSION_MISMATCH","HASH","FORMAT_COUNT","PUID","MIME_TYPE","FORMAT_NAME","FORMAT_VERSION"
"1","","file:/mydata/","/mydata","mydata","","Done","","Folder","","2023-08-25T11:05:54","false","","","","","",""
"2","1","file:/mydata/20211021_Deka_Kauf_von_Wertpapieren.PDF","/mydata/20211021_Deka_Kauf_von_Wertpapieren.PDF","20211021_Deka_Kauf_von_Wertpapieren.PDF","Signature","Done","83206","File","pdf","2021-10-31T14:47:49","false","","1","fmt/354","application/pdf","Acrobat PDF/A - Portable Document Format","1b"
(...)
```
