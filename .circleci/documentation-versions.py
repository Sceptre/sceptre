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


def main():
    try:
        build_dir = str(sys.argv[1])
    except IndexError:
        sys.exit("Missing build dir path: python /path/docs")

    ignored_dirs = {".git"}
    dirs = [
        item
        for item in os.scandir(build_dir)
        if item.is_dir() and item.name not in ignored_dirs
    ]
    sorted_dirs = sorted(dirs, reverse=True, key=attrgetter("name"))
    active_versions = [item.name for item in sorted_dirs[:7]]
    versions_to_remove = (item.path for item in sorted_dirs[7:])
    with open(build_dir + "/version-helper.js", "w+") as outf:
        # select 7 latest versions
        outf.write("let versions = {};".format(active_versions))
    # print out old versions to be removed
    print(",".join(versions_to_remove))


if __name__ == "__main__":
    main()
