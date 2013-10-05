# -*- coding: utf-8 -*-
import scipy.ndimage as ndi
import numpy as np
import Image


def transparent(fname):
    """

    """
    threshold = 200
    dist = 20
    img = Image.open(fname).convert('RGBA')
    # np.asarray(img) is read only. Wrap it in np.array to make it modifiable.
    arr = np.array(np.asarray(img))
    r, g, b, a = np.rollaxis(arr, axis=(-1))
    mask = (
        (r > threshold) &
        (g > threshold) &
        (b > threshold) &
        (np.abs(r - g) < dist) &
        (np.abs(r - b) < dist) &
        (np.abs(g - b) < dist))
    arr[mask, 3] = 0
    img = Image.fromarray(arr, mode='RGBA')
    img.save('/tmp/truck.png')


def autocrop(filename):
    """

    """
    THRESHOLD = 100
    MIN_SHAPE = np.asarray((5, 5))

    im = np.asarray(Image.open(filename))
    gray = im.sum(axis=(-1))
    bw = gray > THRESHOLD
    label, n = ndi.label(bw)
    indices = [np.where(label == ind) for ind in xrange(1, n)]

    slices = [
        [slice(ind[i].min(), ind[i].max()) for i in (0, 1)] + [slice(None)]
        for ind in indices
    ]

    images = [im[s] for s in slices]
    # filter out small images
    images = [im for im in images if not
              np.any(np.asarray(im.shape[:-1]) < MIN_SHAPE)]
