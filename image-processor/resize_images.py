import configparser
import re
from os import listdir
from os.path import exists, isfile, join

import xdg.BaseDirectory
from PIL import Image, ImageFilter, ImageOps, ImageStat
from pillow_heif import register_heif_opener


def resize_images():
    # Apple iOS might send us .heif files as well as plain .jpg files.
    register_heif_opener()

    # Load the config containing our cache and output directories.
    config_file = join(xdg.BaseDirectory.load_first_config("image-processor"), "config")
    config = configparser.ConfigParser()
    config.read(config_file)

    # Our cached, extracted, photos' filenames are in the format of
    # '1701959084.886AB79A-1C1F-4759-A021-B72D7CCC9F0E.1.IMG_2462.HEIC'.
    filename_re = re.compile(r"^([0-9]+)\.([0-9a-fA-F-]+)\.([0-9]+)\.(.*)$")

    # Find all the extracted images in the cache.
    extract_cache = config["image-processor"].get("extractcache")
    extracted_images = [
        f for f in listdir(extract_cache) if isfile(join(extract_cache, f))
    ]

    for f in extracted_images:
        # Build a consistent output filename.
        filename_matches = filename_re.match(f)
        sent_date = filename_matches.group(1)
        message_id = filename_matches.group(2)
        idx = filename_matches.group(3)
        output = config["image-processor"].get("output")
        output_filename = "{}.{}.{}.jpg".format(sent_date, message_id, idx)
        output_file = join(output, output_filename)

        # If the output file already exists on disk, skip it.
        if exists(output_file) == False or isfile(output_file) == False:
            # If not, carry on and resize the image.
            with open(join(extract_cache, f), "rb") as input_fp:
                # Read in the image.
                image = Image.open(input_fp)

                # Fix the rotation of portrait photographs.
                upright = ImageOps.exif_transpose(image)

                # The foreground component should be sized down to fit on the
                # 1920x1080 display.
                foreground = ImageOps.contain(upright, (1920, 1080))

                # The background component should be stretched to completely
                # fill the 1920x1080 display.
                cover = ImageOps.cover(upright, (1920, 1080))

                # Unless we were very lucky with a perfectly 16:9 aspect image,
                # our cover image will need cropped down to our final 1920x1080
                # size.
                cover_w_diff = cover.width - 1920
                cover_h_diff = cover.height - 1080
                left_crop = int(cover_w_diff / 2)
                right_crop = int(cover_h_diff / 2)
                cropped = cover.crop(
                    (left_crop, right_crop, left_crop + 1920, right_crop + 1080)
                )

                # The background should be really blurred out as not to steal
                # focus.
                blurred = cropped.filter(ImageFilter.GaussianBlur(radius=60))

                # We need to horizontally centre the foreground within the
                # background.
                background_centre = int(blurred.width / 2)
                foreground_centre = int(foreground.width / 2)
                foreground_left = background_centre - foreground_centre

                # Similarly, the foreground should be vertically centred on the
                # background along their middles.
                background_middle = int(blurred.height / 2)
                foreground_middle = int(foreground.height / 2)
                foreground_top = background_middle - foreground_middle

                # Paste the foreground in the correct location over the top of
                # the blurred background.
                blurred.paste(foreground, (foreground_left, foreground_top))

                # Save the finished image to our output directory.
                blurred.save(output_file, quality=85, optimize=True, progressive=True)

                # Calculate an average rgb for each image to use as an initial
                # background color.
                stats = ImageStat.Stat(blurred)
                r, g, b = stats.mean
                with open(output_file + ".rgb", "w") as colour_fp:
                    colour_fp.write("{}, {}, {}".format(int(r), int(g), int(b)))

                # Build a small, lowsrc version of the photo as an intermediate
                # background image.
                lowres = blurred.resize((160, 90))
                lowres.save(
                    output_file + ".lowres", format="JPEG", quality=65, optimize=True
                )


if __name__ == "__main__":
    resize_images()
