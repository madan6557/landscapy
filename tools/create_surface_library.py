"""Rebuild Landscapy's original, stylized solid-surface PNG library."""
from pathlib import Path

import numpy as np
from PIL import Image


OUT = Path(__file__).resolve().parents[1] / 'landscapy' / 'textures'
OUT.mkdir(parents=True, exist_ok=True)
SIZE = 512
y, x = np.mgrid[:SIZE, :SIZE].astype(np.float32) / SIZE
rng = np.random.default_rng(20261102)


def quantize(value, steps=6):
    return np.floor(np.clip(value, 0, 1) * steps) / steps


def colorize(name, value, dark, light, accent=None, mask=None):
    dark = np.asarray(dark, dtype=np.float32)
    light = np.asarray(light, dtype=np.float32)
    rgb = dark + (light - dark) * quantize(value)[..., None]
    if accent is not None:
        rgb = np.where(mask[..., None], np.asarray(accent, dtype=np.float32), rgb)
    rgba = np.concatenate((np.clip(rgb, 0, 1), np.ones((SIZE, SIZE, 1), dtype=np.float32)), axis=-1)
    Image.fromarray(np.uint8(np.round(rgba * 255)), 'RGBA').save(OUT / (name + '.png'), optimize=True)


def periodic_cells(count, seed):
    points = np.random.default_rng(seed).random((count, 2))
    dx = abs(x[..., None] - points[:, 0]); dx = np.minimum(dx, 1 - dx)
    dy = abs(y[..., None] - points[:, 1]); dy = np.minimum(dy, 1 - dy)
    radius = dx * dx + dy * dy
    nearest = radius.argmin(axis=-1)
    return np.sqrt(radius.min(axis=-1)), nearest


# The cylinder UV uses X around the trunk and Y along its height. Keep the
# grooves vertical with only a slight, slow irregularity so ordinary trunks
# do not look like twisted cables in the default material.
grain = (.5 + .26 * np.sin(46 * np.pi * x + .16 * np.sin(4 * np.pi * y))
         + .12 * np.sin(82 * np.pi * x + .09 * np.sin(6 * np.pi * y))
         + .06 * np.sin(10 * np.pi * x + 2 * np.pi * y))
colorize('Bark_Grooves', grain, (.13, .075, .05), (.58, .36, .20))

distance, patch = periodic_cells(46, 11)
patch_tone = np.random.default_rng(12).random(46)
flaking = .2 + .65 * patch_tone[patch] + .1 * np.sin(24 * np.pi * y)
colorize('Bark_Flakes', flaking, (.12, .08, .055), (.65, .45, .27),
         accent=(.17, .095, .055), mask=distance < .008)

waves = .5 + .32 * np.sin(14 * np.pi * x + 4 * np.sin(4 * np.pi * y)) + .10 * np.sin(39 * np.pi * x)
colorize('Bark_Waves', waves, (.16, .09, .05), (.69, .42, .23))

radius = np.sqrt((x - .5) ** 2 + (y - .5) ** 2)
rings = .50 + .39 * np.sin(55 * radius + 2 * np.sin(6 * np.pi * x) * np.sin(6 * np.pi * y))
colorize('Wood_Rings', rings, (.34, .18, .09), (.92, .72, .39))

strata = .52 + .33 * np.sin(19 * np.pi * y + 1.2 * np.sin(8 * np.pi * x)) + .1 * np.sin(7 * np.pi * y)
colorize('Stone_Strata', strata, (.18, .24, .27), (.67, .73, .70))

distance, facet = periodic_cells(58, 19)
facet_tone = np.random.default_rng(20).random(58)
facets = .20 + .65 * facet_tone[facet]
colorize('Stone_Facets', facets, (.17, .20, .22), (.68, .71, .68),
         accent=(.10, .14, .16), mask=distance < .006)

distance, pebble = periodic_cells(96, 23)
pebble_tone = np.random.default_rng(24).random(96)
pebbles = .26 + .5 * pebble_tone[pebble] - .13 * (distance > .048)
colorize('Stone_Pebbles', pebbles, (.16, .20, .17), (.76, .73, .57))

distance, spot = periodic_cells(48, 31)
spot_size = np.random.default_rng(32).uniform(.024, .049, 48)
cap = .44 + .18 * np.sin(6 * np.pi * x) * np.sin(6 * np.pi * y)
colorize('Mushroom_Spots', cap, (.32, .06, .035), (.87, .35, .14),
         accent=(.98, .85, .55), mask=distance < spot_size[spot])

ribs = .51 + .34 * np.sin(28 * np.pi * x + 1.0 * np.sin(4 * np.pi * y))
colorize('Mushroom_Ribs', ribs, (.29, .14, .20), (.82, .57, .44))

distance, mottled = periodic_cells(63, 41)
mottle_tone = np.random.default_rng(42).random(63)
mottle = .22 + .67 * mottle_tone[mottled] - .15 * (distance < .009)
colorize('Mushroom_Mottle', mottle, (.13, .13, .26), (.64, .46, .75))

distance, moss = periodic_cells(72, 51)
moss_tone = np.random.default_rng(52).random(72)
moss_value = .21 + .67 * moss_tone[moss] - .17 * (distance > .05)
colorize('Moss_Patches', moss_value, (.06, .15, .065), (.49, .67, .22))

print('SURFACE_LIBRARY', len(list(OUT.glob('*.png'))))
