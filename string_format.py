from pycnc_config import *
import re

rePattern = re.compile("%([^%]+)%")

# Formats a string by replacing placeholder in the form %CONFIG_PARAM% with configuration parameters

def config_string_format(s):
    while True:
        m = rePattern.search(s)
        if m is None:
            break

        try:
            rep = str(eval(m.group(1)))
        except:
            rep = ""

        s = rePattern.sub(rep, s, 1)

    return s