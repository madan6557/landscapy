"""Editable stylized rock families with separate rock, crack and moss surfaces."""
import math
import random

import bmesh
from mathutils import Vector


KINDS={'Pebble','Boulder','Flat Rock','Shard','Stack'}


def _wear(direction,seed,erosion):
    # Silhouette wear stays on broad, low-frequency planes. Fine directional
    # noise made high-detail boulders look pebbled instead of stylized.
    broad=math.sin(direction.x*3.9+seed*.31)*math.cos(direction.y*3.2-seed*.17)
    secondary=math.sin(direction.x*6.1+direction.z*3.7+seed*.23)*math.cos(direction.y*5.3)
    return 1+.075*broad+.026*secondary-erosion*(.10*abs(broad)+.035*abs(secondary))


def _crack(direction,settings,index=0):
    if not settings.rock_cracks: return False
    angle=math.atan2(direction.y,direction.x)
    for k in range(settings.rock_cracks):
        start=math.tau*(k+.31)/settings.rock_cracks+settings.seed*.173+index*.83
        path=start+.22*math.sin(direction.z*5.4+k*2.7+settings.seed*.11)
        distance=abs((angle-path+math.pi)%math.tau-math.pi)
        radial=math.hypot(direction.x,direction.y)
        width=settings.rock_crack_width*(.68+.19*math.sin(direction.z*8.7+k*3.1))
        if distance<width and radial>.28+.12*math.sin(k*2.3) and direction.z>-.65: return True
    return False


def _face_material(points,settings,center,index):
    average=sum((Vector(point) for point in points),Vector())/len(points)
    direction=(average-center).normalized()
    if _crack(direction,settings,index): return 1
    normal=(Vector(points[1])-Vector(points[0])).cross(Vector(points[2])-Vector(points[0])).normalized()
    if settings.rock_moss>0 and normal.z>-.15:
        patch=.5+.27*math.sin(average.x*9.1+settings.seed*.47)*math.cos(average.y*7.3-index*1.8)
        patch+=.12*math.sin(average.z*13.4+average.x*4.7)
        if settings.rock_moss>patch: return 2
    return 0


def _append(builder,vertices,faces,settings,center,index,spherical=False):
    start=len(builder.f); uv_start=len(builder.uv)
    builder.add(vertices,faces)
    cursor=uv_start
    for face in faces:
        builder.mi[start]=_face_material([vertices[i] for i in face],settings,center,index)
        if spherical:
            directions=[(Vector(vertices[i])-center).normalized() for i in face]
            us=[(math.atan2(v.y,v.x)/math.tau)%1 for v in directions]
            if max(us)-min(us)>.5: us=[u+1 if u<.5 else u for u in us]
            for u,direction in zip(us,directions):
                builder.uv[cursor]=(u,math.acos(max(-1,min(1,direction.z)))/math.pi)
                cursor+=1
        else: cursor+=len(face)
        start+=1


def _ico(builder,settings,kind):
    subdivisions=max(1,min(4,round(settings.rock_facets*builder.detail_scale/2)))
    bm=bmesh.new(); bmesh.ops.create_icosphere(bm,subdivisions=subdivisions,radius=1)
    bm.verts.ensure_lookup_table(); bm.verts.index_update()
    axes=Vector(settings.rock_axes)
    width=1.05 if kind=='Boulder' else .72 if kind=='Pebble' else .68
    depth=.9 if kind=='Boulder' else .67 if kind=='Pebble' else .58
    height=.85 if kind=='Boulder' else .34 if kind=='Pebble' else 1.65
    vertices=[]
    for vertex in bm.verts:
        direction=vertex.co.normalized()
        wear=_wear(direction,settings.seed,settings.rock_erosion)
        if kind=='Shard':
            tip=max(0,direction.z)
            wear*=1-.36*tip*tip
        point=Vector((direction.x*width*axes.x,direction.y*depth*axes.y,direction.z*height*axes.z))*settings.crown*wear
        if _crack(direction,settings): point*=1-settings.rock_crack_depth*.6
        if kind=='Shard': point.x+=.19*settings.crown*max(0,direction.z)
        vertices.append(point)
    floor=min(point.z for point in vertices)
    for point in vertices: point.z-=floor
    center=sum(vertices,Vector())/len(vertices)
    faces=[tuple(vertex.index for vertex in face.verts) for face in bm.faces]
    _append(builder,vertices,faces,settings,center,0,spherical=True)
    bm.free()


def _shard(builder,settings):
    """A tilted five-ridge fracture with many coplanar high-detail facets."""
    sides=max(6,round((5+settings.rock_facets*2)*builder.detail_scale))
    levels=max(3,round(5*builder.detail_scale))
    axes=Vector(settings.rock_axes)
    height=settings.crown*axes.z*2.35
    vertices=[]; faces=[]
    profile=((0,.43),(.18,.92),(.53,.83),(.77,.48),(.94,.2),(1,0))
    def width(t):
        for (a,ra),(b,rb) in zip(profile,profile[1:]):
            if t<=b: return ra+(rb-ra)*(t-a)/(b-a)
        return 0
    for level in range(levels):
        t=level/levels
        center=Vector((.25*settings.crown*t*t,-.1*settings.crown*t,height*t))
        for side in range(sides):
            angle=math.tau*side/sides
            sector=(angle+math.pi/5)%(math.tau/5)-math.pi/5
            polygon=math.cos(math.pi/5)/max(.1,math.cos(sector))
            ridge=1+.13*math.sin(angle*2+settings.seed*.41)
            radius=settings.crown*width(t)*polygon*ridge
            direction=Vector((math.cos(angle),math.sin(angle),t*2-1)).normalized()
            wear=_wear(direction,settings.seed,settings.rock_erosion)
            if _crack(direction,settings): radius*=1-settings.rock_crack_depth*.35
            vertices.append(center+Vector((radius*axes.x*math.cos(angle)*wear,
                                           radius*axes.y*math.sin(angle)*wear,0)))
        if level:
            previous=(level-1)*sides; current=level*sides
            for side in range(sides):
                nxt=(side+1)%sides
                faces.append((previous+side,previous+nxt,current+nxt,current+side))
    tip=len(vertices); vertices.append(Vector((.25*settings.crown,-.1*settings.crown,height)))
    last=(levels-1)*sides
    for side in range(sides): faces.append((last+side,last+(side+1)%sides,tip))
    bottom=len(vertices); vertices.append(Vector((0,0,-.015*settings.crown)))
    for side in range(sides): faces.append((bottom,(side+1)%sides,side))
    _append(builder,vertices,faces,settings,Vector((.1*settings.crown,0,height*.5)),0)


def _slab(builder,settings,index=0,stack=False):
    rng=random.Random(settings.seed*311+index*977)
    detail=builder.detail_scale
    sides=max(7,round((6+settings.rock_facets*4)*detail))
    vertical=max(2,round(3*detail))
    radial=max(1,round(2*detail))
    axes=Vector(settings.rock_axes)
    scale=(.88+.16*rng.random()) if stack else 1
    half_height=settings.crown*axes.z*(.19 if stack else .22)
    base=index*half_height*1.55 if stack else 0
    offset=Vector((rng.uniform(-.13,.13)*settings.crown if stack else 0,
                   rng.uniform(-.11,.11)*settings.crown if stack else 0,base))
    phase=rng.uniform(-.3,.3)
    vertices=[]; faces=[]
    def ring(fraction,radius):
        for side in range(sides):
            angle=math.tau*side/sides+phase
            direction=Vector((math.cos(angle),math.sin(angle),fraction*2-1)).normalized()
            edge=1+.055*math.sin(angle*5+settings.seed*.4+index)
            edge*=1+.045*math.cos(angle*9-settings.seed*.2)
            wear=_wear(direction,settings.seed+index*7,settings.rock_erosion)
            r=radius*scale*settings.crown*edge*wear
            z=offset.z+fraction*half_height*2+.025*settings.crown*math.sin(angle*3+index)
            if _crack(direction,settings,index):
                r*=1-settings.rock_crack_depth*.35
                z-=settings.rock_crack_depth*settings.crown*.5*fraction
            vertices.append(offset+Vector((r*axes.x*math.cos(angle),r*axes.y*math.sin(angle),z-offset.z)))
    for layer in range(vertical+1):
        t=layer/vertical
        outline=.78+.23*math.sin(math.pi*t*.86)+.06*t
        ring(t,outline)
        if layer:
            start=(layer-1)*sides; end=layer*sides
            for side in range(sides):
                nxt=(side+1)%sides
                faces.append((start+side,start+nxt,end+nxt,end+side))
    top=(vertical+1)*sides
    for layer in range(radial):
        ring(1,(.94*(1-(layer+1)/(radial+1))))
        previous=vertical*sides if layer==0 else top+(layer-1)*sides
        current=top+layer*sides
        for side in range(sides):
            nxt=(side+1)%sides
            faces.append((previous+side,previous+nxt,current+nxt,current+side))
    top_center=len(vertices); vertices.append(offset+Vector((0,0,half_height*2)))
    previous=top+(radial-1)*sides
    for side in range(sides): faces.append((previous+side,previous+(side+1)%sides,top_center))
    bottom_center=len(vertices); vertices.append(offset+Vector((0,0,-.015*settings.crown)))
    for side in range(sides): faces.append((bottom_center,(side+1)%sides,side))
    _append(builder,vertices,faces,settings,offset+Vector((0,0,half_height)),index)


def build(builder,settings):
    if settings.prop not in KINDS: raise ValueError(settings.prop)
    if settings.prop in {'Pebble','Boulder'}: _ico(builder,settings,settings.prop)
    elif settings.prop=='Shard': _shard(builder,settings)
    else:
        for index in range(3 if settings.prop=='Stack' else 1):
            _slab(builder,settings,index,settings.prop=='Stack')
