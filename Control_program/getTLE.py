#!/usr/bin/env python2
# Downloads TLEs in an automatic fashion

from ConfigParser import ConfigParser

from controller.util import project_file_path
from controller.tle.tle_ephem import TLEephem


if __name__ == "__main__":
    # Load the config file
    config = ConfigParser()
    config.read(project_file_path("/config/tle.cfg"))
    output_dir = config.get("TLE", "output-dir")
    urls = {c.upper(): url for c, url in config.items("URLS")}

    TLEephem.download_tle(output_dir, urls)
