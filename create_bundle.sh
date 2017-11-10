#!/bin/bash

full_dir=$(dirname "$0")
[ "$full_dir" = "." ] && full_dir=$(pwd -P)

prog_dir=$(basename "$full_dir")

cd "$full_dir"

dt=$(date +"%Y%m%d-%H%M")
gc=$(git describe --tags --dirty --always)
dst_name="${prog_dir}-${dt}-${gc}.py"
tmpfile="TMP_${dst_name}"

test -f "${dst_name}" && rm "${dst_name}"

zip -r "${tmpfile}" . \
	-x '*.pyc' \
	-x 'TMP_*' \
	-x 'nasdktop*' \
	-x '\.*' >/dev/null

cat > "${dst_name}" << EOF
#!/usr/bin/env python
# -*- coding: utf-8 -*-

EOF

cat "${tmpfile}" >> "${dst_name}"
chmod +x "${dst_name}"

echo "Binary file created: '${dst_name}'"

rm -f "${tmpfile}"
ln -sf "${dst_name}" nasdktop.py
