"""
Version helper.

Checks the directory 'build_dir' and return list of last 7 versions.
[dev, tag, tag-1, tag-2,..., tag-5]

Then updates file version-helper.js, which takes care of injecting versions
into rtd template.
Return paths, for old versions to be removed.
"""
import os
from operator import attrgetter
import sys

try:
    build_dir = str(sys.argv[1])
except IndexError:
    sys.exit("Missing build dir path: python /path/docs")

dirs = [item for item in os.scandir(build_dir) if item.is_dir()]
sorted_dirs = sorted(dirs, reverse=True, key=attrgetter('name'))
with open(build_dir + "/version-helper.js", "w+") as outf:
    # select 7 latest versions
    outf.write(f"let versions = {[item.name for item in sorted_dirs[:7]]};")
# print out old versions to be removed
print(",".join([item.path for item in sorted_dirs[7:]]))
