#!/usr/bin/env bash
set -e
set -u
set -x
while read full <&3 && read cell <&4; do     
    time ./run.sh $full $cell
done 3< <(cut -f2 full.txt) 4< <(cut -f2 cell.txt)
