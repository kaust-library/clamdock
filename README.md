# Clamdock

 Running ClamAV inside Docker

## Running Container

Running the ClamAV container directly from command line as test.

The container will mount the local file system with mount _bind_.

Running from command line. Interestingly when there is a space in the path, docker only works with `-v` option

```
PS C:\Users\garcm0b\Downloads\autoarchive\2018batch\Image_Files> docker run -it --rm --name clam_test -v 'C:\Users\garcm0b\Downloads\autoarchive\2018batch\Image_Files\Image Files\Heno:/app' clamav/clamav:latest
Starting Freshclamd
Starting ClamAV
(...)
```
