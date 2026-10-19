#!/bin/sh
set -eu
test -f /.dockerenv || { echo 'This build must run inside Docker.' >&2; exit 1; }
mkdir -p output qa
printf 'Docker build and verification: RUNNING\n' > qa/docker-status.txt
python scripts/build.py
python scripts/verify.py
python scripts/verify-vertical.py
python scripts/verify-specimen.py
python scripts/stretch.py
python scripts/docker-provenance.py
python scripts/package.py
