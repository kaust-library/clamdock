# Clamdock

Running ClamAV inside Docker

## ClamAV Container

### Input File

Example of input file

```
#
# Configuration file for the digital preservation workflow
# 

# Maybe this only make sense for Linux users, and on Windows
# just remove it.
[USER]
uid = 1000
gid = 1000

[ACCESSION]
accession_id = 000_000_0000

[BAGGER]
# You can specify a comma separated list of directories as source: dir1, dir2, ...
source_dir = /home/mgarcia/Work/clamdock_data/src/libguides
# Using Python ExtendedInterpolation to use the 'accession_id' as target directory
dest_dir = /home/mgarcia/Work/clamdock_data/dest/${ACCESSION:accession_id}
# TODO: This comment below must be verified!
# If 'false' the script will stop the the destination directory already exists.(?)

[CLAMAV]
av_logs_root = /home/mgarcia/Work/clamdock_data/logs
quarantine_dir = /home/mgarcia/Work/clamdock_data/quarantine
quarantine_file = ${quarantine_dir}/${ACCESSION:accession_id}
quarantine_days = 30

[DROID]
# The profile is the database with the metadata in binary format.
keep_profile = yes

[JHOVE]
jhove_xml = yes

[JHOVE MODULES]
AIFF-hul     = no
ASCII-hul    = no
GIF-hul      = no
GZip-kb      = no
HTML-hul     = no
JPEG-hul     = yes
JPEG2000-hul = yes
PDF-hul      = no
TIFF-hul     = no
UTF8-hul     = no
WARC-kb      = no
WAVE-hul     = no
XML-hul      = no
```


### Persisting the Virus Database

Creating a volume for [persisting the virus database](https://docs.clamav.net/manual/Installing/Docker.html#persisting-the-virus-database-volume):

```
a-garcm0b@library-docker-test:~/Work/clamdock/airflow$ docker volume create clamdb
clamdb
a-garcm0b@library-docker-test:~/Work/clamdock/airflow$
```

### Update Virus Database

Next we update the virus database

```
docker run -it --rm \
--name 'freshclamdb' \
--mount source=clamdb,target=/var/lib/clamav \
clamav/clamav:latest freshclam
```

### Scanning a Folder

Running the ClamAV container directly from command line as test.

The container will mount the local file system with mount _bind_.

Running from command line. Interestingly when there is a space in the path, docker only works with `-v` option

```
docker run  --rm --name clam_test \
-v 'C:\Users\garcm0b\Downloads\autoarchive\2018batch\Image_Files\Image Files\Heno:/scandir' \
-v 'C:\Users\garcm0b\Downloads\Work_Test:/log' \
clamav/clamav:latest clamscan /scandir  \
--verbose  --recursive=yes  --alert \
--log=/log/test.txt
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

Build the container image using the `Dockerfile.bagit`

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

Download Java JRE first

```
(clamdock) PS C:\Users\garcm0b\Work\clamdock\files> docker pull ibmjava:jre
```

Next download [DROID](https://www.nationalarchives.gov.uk/information-management/manage-information/preserving-digital-records/droid/) for all platforms (instead of the Windows version), and extract the archive into the _files_ directory

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

Saving the profile. It seems this step is necessary to convert the profile to a CSV file later.

Creating the profile

```
(clamdock) PS C:\Users\garcm0b\Work\clamdock> docker run -it --rm `
>> -v "C:\Users\garcm0b\Work\clamdock_data\000_000_0000:/mydata" `
>> --name mgdroid mydroid -a /mydata --recurse -p /mydata/test.droid
2024-01-02T14:42:45,245  INFO [main] DroidCommandLine:225 - Starting DROID.
2024-01-02T14:42:46,891  INFO [main] ProfileManagerImpl:129 - Creating profile: 1704206566890
(...)
```

Next we export the profile to CSV

```
(clamdock) PS C:\Users\garcm0b\Work\clamdock> docker run -it --rm `
>> -v "C:\Users\garcm0b\Work\clamdock_data\000_000_0000:/mydata" `
>> --name mgdroid mydroid -p /mydata/test.droid -e /mydata/test.csv
2024-01-02T14:45:20,788  INFO [main] DroidCommandLine:225 - Starting DROID.
2024-01-02T14:45:22,563  INFO [main] ProfileManagerImpl:396 - Loading profile from: /mydata/test.droid
2024-01-02T14:45:26,012  INFO [pool-2-thread-1] ExportTask:187 - Exporting profiles to: [/mydata/test.csv]
(...)
```

Checking the CSV

```
PS C:\Users\garcm0b\Work\clamdock_data\000_000_0000> more .\test.csv
"ID","PARENT_ID","URI","FILE_PATH","NAME","METHOD","STATUS","SIZE","TYPE","EXT","LAST_MODIFIED","EXTENSION_MISMATCH","HASH","FORMAT_COUNT","PUID","MIME_TYPE","FORMAT_NAME","FORMAT_VERSION"
"2","","file:/mydata/","/mydata","mydata","","Done","","Folder","","2024-01-02T12:31:26","false","","","","","",""
"4","2","file:/mydata/bag-info.txt","/mydata/bag-info.txt","bag-info.txt","Extension","Done","399","File","txt","2024-01-02T12:31:26","false","","1","x-fmt/111","text/plain","Plain Text File",""
(...)
```
