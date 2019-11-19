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

VERSION_REGEX = re.compile(r"\d+.\d+.\d+")
KEEP_VERSIONS = ["1.5.0", "1.4.2", "1.3.4"]  # these versions won't be removed
NUMBER_OF_VERSIONS_TO_KEEP = 3


def main():
    try:
        build_dir = str(sys.argv[1])
    except IndexError:
        sys.exit("Missing build dir path: python /path/docs")

    documentation_directories = sorted(
        (
            item
            for item in os.scandir(build_dir)
            if item.is_dir() and VERSION_REGEX.match(item.name)
        ),
        reverse=True,
        key=attrgetter("name")
    )

    active_versions = (
            ["latest", "dev"]
            + [item.name for item in documentation_directories[:NUMBER_OF_VERSIONS_TO_KEEP]]
            + KEEP_VERSIONS
    )
    versions_to_remove = (
        item.path
        for item in documentation_directories[NUMBER_OF_VERSIONS_TO_KEEP:]
        if item.name not in KEEP_VERSIONS
    )
    with open(build_dir + "/version-helper.js", "w+") as outf:
        outf.write("let versions = {};".format(active_versions))
    # print versions_to_remove to stdout for deletion by bash script (github-pages.sh)
    print(",".join(versions_to_remove))


if __name__ == "__main__":
    main()
