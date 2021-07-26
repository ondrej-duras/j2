#!/usr/bin/env python2
##!/usr/bin/env python2
##!/usr/bin/env python3

VERSION = "2021.072601"
MANUAL  = """
NAME: 8-DIGIT Digests for HSRP authentication on NX9K
FILE: hsrp8.py

DESCRIPTION:
  Takes any argument from the command line
  (The VLAN name at the best)
  and calculates 8-digit decimal digest.
  8-digit long digests are useful for 
  HSRP authentication on Nexus switches

SYNTAX:
  hsrp8.py <any_string> [any_string2 ...]

EXAMPLE:
  hsrp8.py STP_MANAGEMENT_VLAN

SECURITY:
  Feel free to share this script, BUT IF YOU SHARE
  this script outside your network team, then 
  please DO NOT FORGET to change SOME_SECRET variable
  to any other value. Thanks.

SEE ALSO:
  https://github.com/ondrej-duras/

VERSION: %s
""" % (VERSION)
  
import sys
import hashlib

SOME_SECRET = 9182375617856
def hsrp8(any_string):
  myd = hashlib.md5(any_string)
  return (((int(myd.hexdigest()[1:10],16)) + SOME_SECRET) % 100000000)
  
if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(MANUAL)
    exit()

  print("hsrp8(" ".join(sys.argv[1:])))

# --- end ---



