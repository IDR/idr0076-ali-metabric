#!/usr/bin/env bash

set -e
set -u
set -x
set -o pipefail

FULL=$1; shift
CELL=$1; shift

. /opt/omero/server/venv3/bin/activate
omero login demo@localhost -w ${PASSWORD}
export OMERODIR=/opt/omero/server/OMERO.server
IMAGE=$(omero import --transfer=ln_s -T "Project:name:idr0076-ali-metabric/experimentA/Dataset:name:Breast Cancer" $FULL)
python direct-rois.py ${IMAGE} ${CELL}
omero -s demo@localhost -w ${PASSWORD} render set ${IMAGE} render.yaml
