"""
Version helper updates file version-helper.js
which takes care of injecting versions into rtd template.
After version-helper.js is updated,
script prints paths of old versions to be removed.

EXAMPLE

docs directory (sceptre.github.io) contains following directories

    ├── 1.5.0
    ├── 2.1.3
    ├── 2.1.4
    ├── 2.1.5
    ├── 2.2.0
    ├── 2.2.1
    ├── dev
    └── latest -> 2.2.1 (symlink)

Script settings:
KEEP_SPECIFIC_VERSIONS = ["1.5.0"]
KEEP_ACTIVE_VERSIONS = 3

The content of version-helper.js will be:
    ['latest', 'dev', '2.2.1', '2.2.0', '2.1.5', '1.5.0']
    (where latest points to 2.2.1)
Output of versions to remove will be:
    <path>/2.1.4
    <path>/2.1.3

"""
import os
from operator import attrgetter
import sys
import re

VERSION_RE = re.compile(r"\d+.\d+.\d+")
KEEP_SPECIFIC_VERSIONS = ["1.5.0"]  # these versions won't be removed
# number of active versions to keep, eg. len([2.2.1, 2.2.0, 2.1.9]) == 3
KEEP_ACTIVE_VERSIONS = 3


def main():
    try:
        build_dir = str(sys.argv[1])
    except IndexError:
        sys.exit("Missing build dir path: python /path/docs")

    # directories which contain docs
    dirs = [
        item
        for item in os.scandir(build_dir)
        if item.is_dir() and VERSION_RE.match(item.name)
    ]

    sorted_dirs = sorted(dirs, reverse=True, key=attrgetter("name"))
    active_versions = (
        ["latest", "dev"]
        + [item.name for item in sorted_dirs[:KEEP_ACTIVE_VERSIONS]]
        + KEEP_SPECIFIC_VERSIONS
    )
    versions_to_remove = (
        item.path
        for item in sorted_dirs[KEEP_ACTIVE_VERSIONS:]
        if item.name not in KEEP_SPECIFIC_VERSIONS
    )
    with open(build_dir + "/version-helper.js", "w+") as outf:
        # select 7 latest versions
        outf.write("let versions = {};".format(active_versions))
    # print out old versions to be removed
    print(",".join(versions_to_remove))


if __name__ == "__main__":
    main()
