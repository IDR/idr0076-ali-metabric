#! /usr/bin/env python
#
# Attach the original CSV tables to the top-level screen


import argparse
import logging
import omero
from omero.cli import cli_login
from omero.gateway import BlitzGateway
from omero.model import FileAnnotationI
from omero_upload import upload_ln_s
import os.path
import sys


OMERO_DATA_DIR = "/data/OMERO"
NAMESPACE = 'openmicroscopy.org/idr/analysis/original'
MIMETYPE = 'text/csv'
FILESET_PATH = "/uod/idr/filesets/idr0076-ali-metabric"
log = logging.getLogger()


def upload_and_link(conn, attachment, image):
    fo = upload_ln_s(conn.c, attachment, OMERO_DATA_DIR, MIMETYPE)
    fa = FileAnnotationI()
    fa.setFile(fo._obj)
    fa.setNs(omero.rtypes.rstring(NAMESPACE))
    fa = conn.getUpdateService().saveAndReturnObject(fa)
    fa = omero.gateway.FileAnnotationWrapper(conn, fa)
    image.linkAnnotation(fa)


def attach_tables(conn):
    
    TABLE_DIR = "20191223-ftp/new_metabric_tables/"
    filenames = ('cell_neighbour_relationships.csv', 'single_cell_data.csv')
    screen = conn.getObject('Screen', attributes={
        'name': 'idr0076-ali-metabric/screenA'})

    for filename in filenames:
        table_path = FILESET_PATH + TABLE_DIR + filename
        log.info(f"Uploading and linking {table_path}")
        upload_and_link(conn, table_path, screen)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--verbose', '-v', action='count', default=0,
        help='Increase the command verbosity')
    parser.add_argument(
        '--quiet', '-q', action='count', default=0,
        help='Decrease the command verbosity')
    parser.add_argument(
        '--dry-run', '-n', action='store_true',
        help='Run command in dry-run mode')
    args = parser.parse_args(argv)

    default_level = logging.INFO - 10 * args.verbose + 10 * args.quiet
    logging.basicConfig(level=default_level)
    with cli_login() as c:
        conn = BlitzGateway(client_obj=c.get_client())
        attach_tables(conn)


if __name__ == "__main__":
    main(sys.argv[1:])
