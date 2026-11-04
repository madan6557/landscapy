"""Raycast or nearest-point placement on evaluated target mesh."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def snap(ob,target,mode='DOWN',direction=(0,0,-1),distance=10,offset=.02):
    if not target or target.type!='MESH' or target==ob: raise ValueError('Choose a different mesh target')
    evaluated=target.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=evaluated.to_mesh()
    try:
        mesh.calc_loop_triangles()
        if not mesh.loop_triangles: raise ValueError('Target mesh has no triangles')
        vertices=[target.matrix_world@v.co for v in mesh.vertices]
        tree=BVHTree.FromPolygons(vertices,[tuple(t.vertices) for t in mesh.loop_triangles],all_triangles=True)
        origin=ob.matrix_world.translation.copy()
        if mode=='NEAREST': point,normal,_,range_=tree.find_nearest(origin,distance)
        else:
            direction=Vector((0,0,-1) if mode=='DOWN' else direction)
            if direction.length<1e-6: raise ValueError('Snap direction cannot be zero')
            direction.normalize(); probe=min(.05,distance*.01)
            point,normal,_,range_=tree.ray_cast(origin-direction*probe,direction,distance+probe)
        if point is None: raise ValueError('No target surface hit within Snap Distance; try Nearest or a different ray direction')
        ob.location=point+normal.normalized()*offset
        ob.rotation_euler=normal.normalized().to_track_quat('Z','Y').to_euler()
        return point,normal.normalized()
    finally: evaluated.to_mesh_clear()
