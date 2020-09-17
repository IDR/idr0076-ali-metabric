#!/usr/bin/env python

# Based on Simon's script
# https://raw.githubusercontent.com/IDR/idr0052-walther-condensinmap/master/scripts/upload_and_create_rois.py

import json
import sys
import os
import omero.cli
import omero.clients
import tifffile
from omero.gateway import BlitzGateway
from omero_rois import masks_from_label_image

PROJECT = "idr0076-ali-metabric/experimentA"
RGBA = (0, 0, 128, 128) # Navy
RGBA = (255, 0, 0, 128)  # Red
DRYRUN = json.loads(os.environ.get("DRYRUN", "false").lower())

def create_rois(im, seg_im):
    print("Processing {} - {}".format(im.name, seg_im.shape))
    assert im.getSizeX() == seg_im.shape[1]
    assert im.getSizeY() == seg_im.shape[0]

    rois = []
    n_shapes = 0
    shapes = masks_from_label_image(seg_im, rgba=RGBA, raise_on_no_mask=False)
    if len(shapes) > 0:
        n_shapes += len(shapes)
        for s in shapes:
            roi = omero.model.RoiI()
            roi.addShape(s)
            rois.append(roi)
    print("{} masks created.".format(n_shapes))
    return rois


def save_rois(conn, im, rois):
    print("Saving {} ROIs for image {}:{}".format(len(rois), im.id, im.name))
    us = conn.getUpdateService()
    for roi in rois:
        # Due to a bug need to reload the image for each ROI
        im = conn.getObject('Image', im.id)
        roi.setImage(im._obj)
        roi1 = us.saveAndReturnObject(roi)


def get_images(conn):
    project = conn.getObject('Project', attributes={'name': PROJECT})
    for dataset in project.listChildren():
        for image in dataset.listChildren():
            if image.name.endswith('_cellmask.tiff'):
                print("Skipping mask image: " + image.name)
                continue
            yield image


def get_segmented_image(conn, image):
    paths = [x.clientPath.val for x in image.getFileset().copyUsedFiles()]
    assert len(paths) == 1
    name = '/' + paths[0]
    name = name.replace("fullstack", "cellmask")
    name = name.replace("full_stack", "cell_mask")
    return tifffile.imread(name)


def main(conn):
    for im in get_images(conn):
        seg_im = get_segmented_image(conn, im)
        if seg_im is None:
            print("Image:%s - No segmented image found" % im.id)
            continue
        rois = create_rois(im, seg_im)
        if len(rois) == 0:
            print("Image:%s - No ROIs found" % im.id)
        else:
            if DRYRUN:
                print("Image:%s - Found %s ROIs" % (im.id, len(rois)))
            else:
                save_rois(conn, im, rois)


class IDR0076Control(omero.cli.BaseControl):

    def _configure(self, parser):
        parser.add_login_arguments()
        parser.set_defaults(func=self.__call__)

    def __call__(self, args):
        c = self.ctx.conn(args)
        conn = BlitzGateway(client_obj=c)
        main(conn)


try:
    register("idr0076", IDR0076Control, "help")
except NameError:
    if __name__ == "__main__":
        cli = omero.cli.CLI()
        cli.loadplugins()
        cli.register("idr0076", IDR0076Control, "help")
        cli.invoke(sys.argv[1:])
