"""Distinct stylized wood props with editable bark, end grain, and inner wood."""
import math
import random

import bpy
from mathutils import Vector
from . import tube_frames


WOOD_KINDS = {'Stump', 'Hollow Log', 'Fallen Trunk', 'Broken Branch', 'Root', 'Vine'}
CUT_KINDS = {'Stump', 'Hollow Log', 'Fallen Trunk', 'Broken Branch'}


def cut_material(color):
    """Simple concentric end grain; users can replace it in the Cut Wood slot."""
    name='LP Cut Wood '+','.join(f'{channel:.3f}' for channel in color)
    existing=bpy.data.materials.get(name)
    if existing: return existing
    mat=bpy.data.materials.new(name); mat.use_nodes=True; mat['lp_role']='Cut Wood'
    nodes=mat.node_tree.nodes; links=mat.node_tree.links
    bsdf=nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value=.88
    coord=nodes.new('ShaderNodeTexCoord')
    center=nodes.new('ShaderNodeVectorMath'); center.operation='SUBTRACT'; center.inputs[1].default_value=(.5,.5,0)
    length=nodes.new('ShaderNodeVectorMath'); length.operation='LENGTH'
    wave=nodes.new('ShaderNodeMath'); wave.operation='MULTIPLY'; wave.inputs[1].default_value=80
    sine=nodes.new('ShaderNodeMath'); sine.operation='SINE'
    ramp=nodes.new('ShaderNodeValToRGB')
    dark=tuple(max(0,channel*.58) for channel in color)
    light=tuple(min(1,channel*1.28+.08) for channel in color)
    ramp.color_ramp.elements[0].color=(*dark,1)
    ramp.color_ramp.elements[1].color=(*light,1)
    links.new(coord.outputs['UV'],center.inputs[0]); links.new(center.outputs['Vector'],length.inputs[0])
    links.new(length.outputs['Value'],wave.inputs[0]); links.new(wave.outputs[0],sine.inputs[0])
    links.new(sine.outputs[0],ramp.inputs[0]); links.new(ramp.outputs[0],bsdf.inputs['Base Color'])
    return mat


def _append(builder, vertices, faces, materials, uvs):
    face_start=len(builder.f); uv_start=len(builder.uv)
    builder.add(vertices,faces)
    cursor=uv_start
    for index,(face,material,face_uv) in enumerate(zip(faces,materials,uvs)):
        builder.mi[face_start+index]=material
        builder.uv[cursor:cursor+len(face)]=face_uv
        cursor+=len(face)


def _loft(builder,centers,radii,seed,sides=12,cut_start=False,cut_end=False,jagged=False):
    centers=[Vector(point) for point in centers]
    sides=max(5,round(sides*builder.detail_scale))
    vertices=[]
    distances=[0.]
    for a,b in zip(centers,centers[1:]): distances.append(distances[-1]+(b-a).length)
    for index,(center,radius,(x_axis,y_axis)) in enumerate(zip(centers,radii,tube_frames.frames(centers))):
        tangent=(centers[min(index+1,len(centers)-1)]-centers[max(index-1,0)]).normalized()
        phase=index/max(1,len(centers)-1)
        for side in range(sides):
            angle=math.tau*side/sides
            bark=1+.035*math.sin(angle*5+seed*.73+phase*3)+.018*math.sin(angle*11-seed*.31-phase*2)
            splinter=(radius*.55*(.5+.5*math.sin(angle*3+seed*1.7))) if jagged and index==len(centers)-1 else 0
            vertices.append(center+radius*bark*(x_axis*math.cos(angle)+y_axis*math.sin(angle))+tangent*splinter)
    faces=[]; materials=[]; uvs=[]
    face=tuple(reversed(range(sides))); faces.append(face); materials.append(1 if cut_start else 0)
    uvs.append([(.5+.46*math.cos(math.tau*side/sides),.5+.46*math.sin(math.tau*side/sides)) for side in face])
    for ring in range(len(centers)-1):
        for side in range(sides):
            next_side=(side+1)%sides
            faces.append((ring*sides+side,ring*sides+next_side,(ring+1)*sides+next_side,(ring+1)*sides+side))
            materials.append(0)
            u0=side/sides; u1=(side+1)/sides
            uvs.append([(u0,distances[ring]),(u1,distances[ring]),(u1,distances[ring+1]),(u0,distances[ring+1])])
    face=tuple((len(centers)-1)*sides+side for side in range(sides))
    faces.append(face); materials.append(1 if cut_end else 0)
    uvs.append([(.5+.46*math.cos(math.tau*side/sides),.5+.46*math.sin(math.tau*side/sides)) for side in range(sides)])
    _append(builder,vertices,faces,materials,uvs)


def _hollow(builder,settings):
    length=max(.12,settings.length); radius=max(.03,settings.radius)
    rings=max(3,round(7*builder.detail_scale)); sides=max(6,round(12*builder.detail_scale))
    vertices=[]; distances=[length*i/rings for i in range(rings+1)]
    for inside in (False,True):
        for ring in range(rings+1):
            t=ring/rings; x=(t-.5)*length
            center=Vector((x,settings.bend*math.sin(math.pi*t)*.22,radius*1.1))
            for side in range(sides):
                angle=math.tau*side/sides
                noise=1+.04*math.sin(angle*5+settings.seed*.43+t*4)
                rr=radius*(.67 if inside else 1)*noise*(1-.15*t)
                vertices.append(center+Vector((0,rr*math.cos(angle),rr*math.sin(angle))))
    faces=[]; materials=[]; uvs=[]; stride=(rings+1)*sides
    for ring in range(rings):
        for side in range(sides):
            next_side=(side+1)%sides; u0=side/sides; u1=(side+1)/sides
            for inside in (False,True):
                base=stride if inside else 0
                face=(base+ring*sides+side,base+ring*sides+next_side,
                      base+(ring+1)*sides+next_side,base+(ring+1)*sides+side)
                if inside: face=tuple(reversed(face))
                faces.append(face); materials.append(2 if inside else 0)
                uv=[(u0,distances[ring]),(u1,distances[ring]),(u1,distances[ring+1]),(u0,distances[ring+1])]
                uvs.append(list(reversed(uv)) if inside else uv)
    for ring in (0,rings):
        for side in range(sides):
            next_side=(side+1)%sides
            outer=ring*sides; inner=stride+ring*sides
            face=(outer+side,inner+side,inner+next_side,outer+next_side)
            uv=[(.5+.46*math.cos(math.tau*side/sides),.5+.46*math.sin(math.tau*side/sides)),
                (.5+.31*math.cos(math.tau*side/sides),.5+.31*math.sin(math.tau*side/sides)),
                (.5+.31*math.cos(math.tau*next_side/sides),.5+.31*math.sin(math.tau*next_side/sides)),
                (.5+.46*math.cos(math.tau*next_side/sides),.5+.46*math.sin(math.tau*next_side/sides))]
            if ring==rings: face=tuple(reversed(face)); uv=list(reversed(uv))
            faces.append(face); materials.append(1)
            uvs.append(uv)
    _append(builder,vertices,faces,materials,uvs)


def build(builder,settings,owner=None):
    kind=settings.prop; rng=random.Random(settings.seed)
    length=max(.12,settings.length); radius=max(.025,settings.radius)
    if kind=='Hollow Log':
        _hollow(builder,settings); return
    if kind=='Stump':
        rings=max(3,round(8*builder.detail_scale))
        centers=[Vector((settings.bend*.07*(i/rings)**2,0,length*i/rings)) for i in range(rings+1)]
        radii=[radius*(1+.43*math.exp(-18*(i/rings)**2)-.13*(i/rings)) for i in range(rings+1)]
        _loft(builder,centers,radii,settings.seed,cut_start=False,cut_end=True)
        for side in range(4):
            angle=math.tau*side/4+.2
            start=Vector((radius*.35*math.cos(angle),radius*.35*math.sin(angle),radius*.24))
            tip=Vector((radius*(1.8+.25*rng.random())*math.cos(angle),radius*(1.8+.25*rng.random())*math.sin(angle),.015))
            builder.tube([start,start.lerp(tip,.55),tip],radius*.22,6,.03)
        return
    if kind=='Fallen Trunk':
        rings=max(3,round(10*builder.detail_scale))
        centers=[Vector(((i/rings-.5)*length,settings.bend*.15*math.sin(math.pi*i/rings),radius*(1.05-.18*i/rings))) for i in range(rings+1)]
        radii=[radius*(1.12-.38*i/rings) for i in range(rings+1)]
        _loft(builder,centers,radii,settings.seed,cut_start=True,cut_end=True)
        for fraction,sign in ((.3,-1),(.67,1)):
            base=centers[round(fraction*rings)]
            builder.tube([base,base+Vector((0,sign*radius*1.6,radius*.8)),
                          base+Vector((length*.07,sign*radius*2.2,radius*1.4))],radius*.24,6,.08)
        return
    if kind=='Broken Branch':
        rings=max(3,round(8*builder.detail_scale))
        centers=[Vector((settings.bend*.3*(i/rings)**2,0,length*i/rings)) for i in range(rings+1)]
        radii=[radius*(1-.62*i/rings) for i in range(rings+1)]
        _loft(builder,centers,radii,settings.seed,cut_start=False,cut_end=True,jagged=True)
        for side in (-1,1):
            start=centers[round(rings*.7)]
            builder.tube([start,start+Vector((side*radius*.7,0,length*.12)),
                          start+Vector((side*radius*1.4,0,length*.2))],radius*.14,5,.015)
        return
    if kind=='Root':
        rings=max(4,round(10*builder.detail_scale))
        centers=[Vector((length*i/rings,settings.bend*.22*math.sin(2*math.pi*i/rings),
                         radius*(.75-.58*i/rings))) for i in range(rings+1)]
        radii=[radius*(1-.85*i/rings) for i in range(rings+1)]
        _loft(builder,centers,radii,settings.seed,cut_start=False,cut_end=False)
        for sign in (-1,1):
            base=centers[round(rings*.4)]
            builder.tube([base,base+Vector((length*.18,sign*radius*1.6,-radius*.12)),
                          base+Vector((length*.45,sign*radius*2.5,-radius*.35))],radius*.32,6,.02)
        return
    if kind=='Vine':
        paths=[]
        if owner and settings.controller and settings.controller.type=='CURVE':
            from . import paths as curve_paths
            transform=owner.matrix_world.inverted()@settings.controller.matrix_world
            paths=[[transform@point for point in path] for path in curve_paths.curve_paths(settings.controller)]
        if not paths:
            turns=2.5+abs(settings.bend)*.5
            steps=max(8,round(16*builder.detail_scale))
            paths=[[Vector((settings.crown*.28*math.cos(math.tau*turns*i/steps),
                            settings.crown*.28*math.sin(math.tau*turns*i/steps),length*i/steps))
                    for i in range(steps+1)]]
        for path in paths:
            if len(path)>=2: builder.tube(path,radius*.32,6,.65)
