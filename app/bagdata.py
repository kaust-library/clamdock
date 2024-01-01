from bagit import make_bag
from os import environ


def main():
    BagIt_test = {
        "Source-Organization": f"{environ['SOURCE_ORGANIZATION']}",
        "External-Identifier": f"{environ['EXTERNAL_IDENTIFIER']}",
        "Internal-Sender-Description": f"{environ['INTERNAL_SENDER_DESCRIPTION']}",
        "Title": f"{environ['TITLE']}",
        "Date-Start": f"{environ['DATE_START']}",
        "Record-Creators": f"{environ['RECORD_CREATORS']}",
        "Record-Type": f"{environ['RECORD_TYPE']}",
        "Extend-Size": f"{environ['EXTEND_SIZE']}",
        "Subjects": f"{environ['SUBJECTS']}",
        "Office": f"{environ['OFFICE']}",
    }

    bag_path = environ["BAG_PATH"]

    my_bag = make_bag(bag_path, BagIt_test, checksums=["sha256"])

    my_bag.save()


if __name__ == "__main__":
    main()
