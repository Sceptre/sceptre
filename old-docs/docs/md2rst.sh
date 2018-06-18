#!/usr/bin/env bash




for file in $(ls docs); do

    filename=$(basename -- "$file")
    extension="${filename##*.}"
    filename="${filename%.*}"

    pandoc --wrap=preserve --columns=10000 --from=markdown --to=rst --output="_pd/${filename}.rst" "_docs/${file}"

done;