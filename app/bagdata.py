from bagit import make_bag
from os import environ


def main():
    BagIt_test = {
        "Source-Organization": environ["SOURCE_ORGANIZATION"],
        "External-Identifier": environ["EXTERNAL_IDENTIFIER"],
        "Internal-Sender-Description": environ["INTERNAL_SENDER_DESCRIPTION"],
        "Title": environ["TITLE"],
        "Date-Start": environ["DATE_START"],
        "Record-Creators": environ["RECORD_CREATORS"],
        "Record-Type": environ["RECORD_TYPE"],
        "Extend-Size": environ["EXTEND_SIZE"],
        "Subjects": environ["SUBJECTS"],
        "Office": environ["OFFICE"],
    }

    bag_path = "/mydir"

    my_bag = make_bag(bag_path, BagIt_test, checksums=["sha256"])

    my_bag.save()


if __name__ == "__main__":
    main()
