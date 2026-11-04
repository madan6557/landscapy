"""Stable transported ring axes for curved wood tubes."""
from mathutils import Vector


def frames(path):
    """Yield perpendicular X/Y axes without roll jumps along a centerline."""
    if len(path)<2: raise ValueError('Tube needs at least two path points')
    tangents=[]
    for i in range(len(path)):
        tangent=path[min(i+1,len(path)-1)]-path[max(i-1,0)]
        if tangent.length_squared<1e-12:
            tangent=tangents[-1].copy() if tangents else Vector((0,0,1))
        else: tangent.normalize()
        tangents.append(tangent)
    tangent=tangents[0]
    axis=Vector((1,0,0)) if abs(tangent.x)<.85 else Vector((0,0,1))
    x=(axis-tangent*axis.dot(tangent)).normalized()
    previous=tangent
    for tangent in tangents:
        if tangent!=previous:
            x=previous.rotation_difference(tangent)@x
            x=(x-tangent*x.dot(tangent)).normalized()
        yield x,tangent.cross(x).normalized()
        previous=tangent
