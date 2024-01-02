import configparser
import email
import email.utils
import re
from os import listdir
from os.path import exists, isfile, join

import xdg.BaseDirectory


def extract_images():
    # Load the config containing our input and cache directories.
    config_file = join(xdg.BaseDirectory.load_first_config("image-processor"), "config")
    config = configparser.ConfigParser()
    config.read(config_file)

    # Message IDs are in the format of
    # '<701B09B3-0E36-49A6-8598-A119B04968CD@mikecoats.com>'
    message_re = re.compile(
        r"^<([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})@.*>$"
    )

    # Find all the files in the read and unread mail directories.
    maildir = config["image-processor"].get("maildir")
    unread_emails = [
        join(maildir, "new", f)
        for f in listdir(join(maildir, "new"))
        if isfile(join(maildir, "new", f))
    ]
    read_emails = [
        join(maildir, "cur", f)
        for f in listdir(join(maildir, "cur"))
        if isfile(join(maildir, "cur", f))
    ]

    # Grab each of the emails in turn.
    for email_file in unread_emails + read_emails:
        with open(email_file, "r") as input_fp:
            # Load and parse the email file.
            message = email.message_from_file(input_fp)

            # Get the timestamp from the mail.
            sent_date = str(
                int(email.utils.parsedate_to_datetime(message["Date"]).timestamp())
            )

            # Get the ID from the mail.
            message_id = message_re.match(message["Message-id"]).group(1)

            # Grab a list of images from the list of attachments.
            images = [
                part
                for part in message.walk()
                if part.get_content_type().lower().startswith("image/")
            ]

            # We increment an index to ensure images have unique filenames.
            idx = -1
            for image in images:
                idx += 1

                # Grab the sender's filename.
                image_file = image.get_filename()

                # Construct a new extracted filename, including the extension
                # of the attachment.
                output_filename = "{}.{}.{}.{}".format(
                    sent_date, message_id, str(idx), image_file
                )

                # Find a place for it in the output directory.
                extract_cache = config["image-processor"].get("extractcache")
                output_file = join(extract_cache, output_filename)

                # If the file already exists on disk, skip it.
                if exists(output_file) == False or isfile(output_file) == False:
                    # If not, dump the file to disk.
                    with open(output_file, "wb") as output_fp:
                        image_bytes = image.get_payload(decode=True)
                        output_fp.write(image_bytes)


if __name__ == "__main__":
    extract_images()
