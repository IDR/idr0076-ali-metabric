#!/usr/bin/env python

# Based on Simon's script
# https://raw.githubusercontent.com/IDR/idr0052-walther-condensinmap/master/scripts/upload_and_create_rois.py

import json
import os
import omero.cli
import omero.clients
from omero.gateway import BlitzGateway
from omero_rois import masks_from_label_image

PROJECT = "idr0076-ali-metabric/experimentA"
RGBA = (255, 255, 255, 128)
DRYRUN = json.loads(os.environ.get("DRYRUN", "false").lower())

def create_rois(im, seg_im):
    print("Processing {} - {}".format(im.name, seg_im.name))
    if im.getSizeZ() != seg_im.getSizeZ():
        print("Z size does not match. Skipping.")
        return []

    rois = []
    n_shapes = 0
    for z in range(0, im.getSizeZ()):
        plane = seg_im.getPrimaryPixels().getPlane(z, 0, 0)
        roi = omero.model.RoiI()
        shapes = masks_from_label_image(plane, rgba=RGBA, z=z, raise_on_no_mask=False)
        if len(shapes) > 0:
            n_shapes += len(shapes)
            for s in shapes:
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
    name = image.name.replace("fullstack", "cellmask")
    try:
        result = conn.getObject('Image', attributes={'name': name})
        return result
    except Exception as e:
        print("Could not find {} for {}".format(name, image.name))
        return None


def main(conn):
    for im in get_images(conn):
        seg_im = get_segmented_image(conn, im)
        if seg_im is None:
            print("Image:%s - No segmented image found" % im.id)
            continue
        try:
            rois = create_rois(im, seg_im)
            if len(rois) == 0:
                print("Image:%s - No ROIs found" % im.id)
            else:
                if DRYRUN:
                    print("Image:%s - Found %s ROIs" % (im.id, len(rois)))
                else:
                    save_rois(conn, im, rois)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    with omero.cli.cli_login() as cli:
        client = cli.get_client()
        with BlitzGateway(client_obj=client) as conn:
            main(conn)
