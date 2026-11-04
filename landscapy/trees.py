"""Landscapy Library-Based Tree Generator (100% Original Stylized Nature).
Builds art-directed stylized trees using interactive Bezier curve trunks,
the production-ready LP_TreeEngine Geometry Nodes, and modular foliage collections.
"""
import bpy
import math
from mathutils import Vector
from . import library

def create_curve_trunk(name='Stylized Tree', gesture='GENTLE'):
    """Create an interactive Curve object with a stylized Bezier spline gesture."""
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 4

    spline = curve_data.splines.new('BEZIER')
    
    if gesture == 'STRAIGHT':
        points = [
            (Vector((0, 0, 0)), Vector((0, 0, -0.5)), Vector((0, 0, 0.5))),
            (Vector((0, 0, 2.5)), Vector((0, 0, 1.8)), Vector((0, 0, 3.2))),
            (Vector((0, 0, 5.5)), Vector((0, 0, 4.5)), Vector((0, 0, 6.0))),
        ]
    elif gesture == 'PALM':
        points = [
            (Vector((0, 0, 0)), Vector((-0.2, 0, -0.6)), Vector((0.3, 0, 0.8))),
            (Vector((1.1, 0, 2.8)), Vector((0.7, 0, 1.8)), Vector((1.5, 0, 3.8))),
            (Vector((1.8, 0, 5.2)), Vector((1.6, 0, 4.4)), Vector((1.9, 0, 5.6))),
        ]
    elif gesture == 'BANANA':
        points = [
            (Vector((0, 0, 0)), Vector((0, 0, -0.4)), Vector((0, 0, 0.6))),
            (Vector((0.15, 0, 1.8)), Vector((0.05, 0, 1.0)), Vector((0.25, 0, 2.6))),
            (Vector((0.28, 0, 3.4)), Vector((0.22, 0, 2.9)), Vector((0.32, 0, 3.8))),
        ]
    elif gesture == 'BONSAI':
        points = [
            (Vector((0, 0, 0)), Vector((-0.4, 0, -0.5)), Vector((0.5, 0, 0.6))),
            (Vector((1.2, 0.4, 1.6)), Vector((0.6, 0.2, 1.0)), Vector((1.6, 0.5, 2.2))),
            (Vector((0.4, -0.3, 3.0)), Vector((1.0, 0.1, 2.5)), Vector((-0.2, -0.6, 3.4))),
            (Vector((0.6, 0.1, 4.2)), Vector((0.1, -0.2, 3.8)), Vector((0.9, 0.3, 4.5))),
        ]
    else:  # GENTLE
        points = [
            (Vector((0, 0, 0)), Vector((-0.1, 0, -0.5)), Vector((0.1, 0, 0.6))),
            (Vector((0.35, 0.1, 2.2)), Vector((0.15, 0, 1.3)), Vector((0.55, 0.2, 3.1))),
            (Vector((0.5, 0.15, 4.6)), Vector((0.4, 0.1, 3.8)), Vector((0.6, 0.2, 5.2))),
        ]

    spline.bezier_points.add(len(points) - 1)
    for bp, (co, handle_left, handle_right) in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left = handle_left
        bp.handle_right = handle_right
        bp.handle_left_type = 'ALIGNED'
        bp.handle_right_type = 'ALIGNED'

    ob = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    return ob


def setup_tree_modifiers(ob, preset='OAK', leaf_col_name=None, seed=None):
    """Attach and configure LP_TreeEngine Geometry Nodes on the curve object."""
    node_group = library.append_node_group('LP_TreeEngine')
    if not node_group:
        raise RuntimeError("Could not load Geometry Node group LP_TreeEngine from library")

    # Map preset to default leaf collection
    if preset == 'PALM':
        default_leaf = 'LeafPalm'
    elif preset == 'BANANA':
        default_leaf = 'LeafBanana'
    elif preset == 'ANIME_DOME':
        default_leaf = 'LeafDome'
    else:
        default_leaf = 'LeafSolid'

    leaf_target = leaf_col_name or default_leaf
    leaf_col = library.append_collection(leaf_target)

    mod = ob.modifiers.get('Landscapy Tree') or ob.modifiers.new('Landscapy Tree', 'NODES')
    mod.node_group = node_group

    def set_socket(name, val):
        try:
            for item in node_group.interface.items_tree:
                if getattr(item, 'in_out', None) == 'INPUT' and item.name == name:
                    mod[item.identifier] = val
                    return True
        except Exception:
            pass
        return False

    if preset == 'PALM':
        set_socket('TrunkRadius', 0.18)
        set_socket('BottomRadius', 0.42)
        set_socket('LeafScale', 1.35)
        set_socket('LeafDensity', 12)
        set_socket('WindStrength', 0.25)
    elif preset == 'BANANA':
        set_socket('TrunkRadius', 0.22)
        set_socket('BottomRadius', 0.46)
        set_socket('LeafScale', 1.40)
        set_socket('LeafDensity', 10)
        set_socket('WindStrength', 0.20)
    elif preset == 'ANIME_DOME':
        set_socket('TrunkRadius', 0.25)
        set_socket('BottomRadius', 0.48)
        set_socket('LeafScale', 1.60)
        set_socket('LeafDensity', 14)
        set_socket('WindStrength', 0.18)
    elif preset == 'BONSAI':
        set_socket('TrunkRadius', 0.20)
        set_socket('BottomRadius', 0.52)
        set_socket('LeafScale', 0.85)
        set_socket('LeafDensity', 16)
        set_socket('WindStrength', 0.12)
    elif preset == 'DEAD_TREE':
        set_socket('TrunkRadius', 0.24)
        set_socket('BottomRadius', 0.50)
        set_socket('LeafScale', 0.0)
        set_socket('LeafDensity', 0)
    else:  # OAK
        set_socket('TrunkRadius', 0.24)
        set_socket('BottomRadius', 0.50)
        set_socket('LeafScale', 1.0)
        set_socket('LeafDensity', 18)
        set_socket('WindStrength', 0.22)

    if leaf_col:
        set_socket('LeafCollection', leaf_col)
        set_socket('Leaf Variant Count', max(1, library.collection_variant_count(leaf_col)))
    set_socket('Variation Seed', int(ob.get('landscapy_seed', 1) if seed is None else seed))

    ob['landscapy_type'] = 'TREE'
    ob['landscapy_preset'] = preset
    ob['landscapy_leaf_col'] = leaf_target
    return ob
