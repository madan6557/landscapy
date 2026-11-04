"""Landscapy Asset Library Manager (100% Original Stylized Nature Assets).
Loads, links, and appends modular stylized assets, node groups, and collections
from the bundled assets/landscapy_library.blend file.
"""
import bpy
from pathlib import Path

LIBRARY_PATH = Path(__file__).parent / 'assets' / 'landscapy_library.blend'

FOLIAGE_COLLECTIONS = [
    ('LeafSolid', 'Solid Clumps', 'Faceted chunky, art-directed foliage clumps'),
    ('LeafDome', 'Dome Puffs', 'Layered silhouette puffs for stylized canopy crowns'),
    ('LeafPalm', 'Pinnate Palm Cards', 'Continuous notched blades with a raised central fold'),
    ('LeafBanana', 'Broad Lamina Cards', 'Continuous broad leaves with a shaped, folded silhouette'),
]

FLOWER_OBJECTS = [
    ('LP_Flower_Blue', 'Blue Flower', '4-triangle quad flower with sunken valley center'),
    ('LP_Flower_Red', 'Red Flower', '4-triangle quad flower with sunken valley center'),
    ('LP_Flower_White', 'White Flower', '4-triangle quad flower with sunken valley center'),
    ('LP_Flower_Violet', 'Violet Flower', 'Original four-triangle valley flower'),
    ('LP_Flower_Amber', 'Amber Flower', 'Original four-triangle valley flower'),
]

FRUIT_OBJECTS = [
    ('LP_BananaBunch', 'Banana Bunch', 'Yellow banana finger tiers with maroon terminal bud'),
    ('LP_CoconutCluster', 'Coconut Cluster', 'Green coconut cluster at crown collar'),
    ('LP_AppleCluster', 'Apple Cluster', 'Small axillary fruit cluster'),
    ('LP_GrapeCluster', 'Grape Cluster', 'Tapered hanging fruit cluster'),
    ('LP_MangoPanicle', 'Mango Panicle', 'Elongated hanging fruit cluster'),
]

PROP_OBJECTS = [
    ('LP_Rock', 'Stylized Rock', 'Faceted low-poly stone boulder'),
    ('LP_HollowTrunk', 'Hollow Trunk', 'Decayed hollow stump with exposed wood rim'),
    ('LP_Mushroom', 'Stylized Mushroom', 'Cap + gills + stem with glow support'),
    ('LP_ShelfMushroom', 'Tree Shelf Mushroom', 'Bracket oyster mushroom that clings to tree bark'),
    ('LP_Rock_Rounded', 'Rounded Rock', 'Original faceted low-poly boulder variation'),
    ('LP_Rock_Shard', 'Shard Rock', 'Original angular faceted rock variation'),
    ('LP_MushroomCluster', 'Glowing Mushroom Cluster', 'Three original cap-and-stem forms with cap emission'),
    ('LP_OysterCluster', 'Oyster Mushroom Cluster', 'Layered bracket mushroom forms for tree surfaces'),
]

TREE_PRESETS = [
    ('OAK', 'Stylized Broadleaf / Oak', 'Classic chunky low-poly tree with solid foliage clumps'),
    ('ANIME_DOME', 'Anime Puffy Dome Tree', 'Ghibli-style volumetric cloud domes with smooth shading'),
    ('PALM', 'Coconut Palm', 'Curved sweeping trunk with 1 continuous blade per frond and coconuts'),
    ('BANANA', 'Banana Tree', 'Flared base pseudostem with broad lamina rosettes and hanging fruit bunch'),
    ('BONSAI', 'Mountain Bonsai', 'Artfully twisted crooked trunk with low-poly foliage pads'),
    ('DEAD_TREE', 'Dead Bare Tree', 'Old skeletal trunk and tapering bare branches with no foliage'),
]

LIBRARY_ASSET_COUNTS = {
    'LeafSolid': 4,
    'LeafDome': 3,
    'LeafPalm': 3,
    'LeafBanana': 3,
}


def ensure_library_loaded():
    """Ensure that key collections and node groups from the library are available in current blend."""
    return LIBRARY_PATH.exists()


def append_node_group(group_name='LP_TreeEngine'):
    """Append a GeometryNodeTree from the library if not already loaded."""
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]
    if not LIBRARY_PATH.exists():
        return None
    with bpy.data.libraries.load(str(LIBRARY_PATH), link=False) as (data_from, data_to):
        if group_name in data_from.node_groups:
            data_to.node_groups = [group_name]
    return bpy.data.node_groups.get(group_name)


def append_collection(collection_name):
    """Append a library collection (e.g. leaf or flower set) into the scene."""
    existing = bpy.data.collections.get(collection_name)
    if existing:
        return existing
    if not LIBRARY_PATH.exists():
        return None
    with bpy.data.libraries.load(str(LIBRARY_PATH), link=False) as (data_from, data_to):
        if collection_name in data_from.collections:
            data_to.collections = [collection_name]
    col = bpy.data.collections.get(collection_name)
    if col and col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col


def collection_variant_count(collection):
    """Return the number of direct mesh/curve choices exposed by Collection Info."""
    if isinstance(collection, str):
        collection = bpy.data.collections.get(collection)
    if not collection:
        return 0
    return sum(obj.type in {'MESH', 'CURVE'} for obj in collection.objects)


def append_object(object_name):
    """Append a standalone mesh object (e.g. Rock, Hollow Trunk, Mushroom, Fruit)."""
    existing = bpy.data.objects.get(object_name)
    if existing:
        return existing
    if not LIBRARY_PATH.exists():
        return None
    with bpy.data.libraries.load(str(LIBRARY_PATH), link=False) as (data_from, data_to):
        if object_name in data_from.objects:
            data_to.objects = [object_name]
    ob = bpy.data.objects.get(object_name)
    if ob and ob.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(ob)
    return ob
