"""Low polygon mushroom families with independent stem/cap/underside materials."""
import math, random
from mathutils import Vector, Quaternion


def _cap_profile(kind,t,thickness):
    if kind=='Funnel': return thickness*(1.1*t*t-.35)
    if kind=='Bell': return thickness*2*(1-t**1.4)-thickness*.15*t**8
    if kind=='Parasol': return thickness*(.9*(1-t*t)-.13*t**10)
    if kind=='Dome': return thickness*1.7*math.sqrt(max(0,1-t*t))
    return thickness*(1-t*t)


def _fan(builder,center,frame,radius,thickness,n,rings,kind,s):
    # Bracket and oyster grow as a single fan attached at the narrow base.
    vertices=[]; faces=[]
    for ring in range(rings+1):
        t=ring/rings; spread=radius*(.01+.99*t)
        for j in range(n+1):
            a=-math.pi/2+math.pi*j/n
            x=spread*math.cos(a); y=spread*math.sin(a)
            z=thickness*(.2 if kind=='Oyster' else .45)*(1-t*t)+s.mushroom_rim*t**8
            vertices.append(center+frame@Vector((x,y,z)))
    for ring in range(rings):
        for j in range(n):
            a=ring*(n+1)+j; faces.append((a,a+1,a+n+2,a+n+1))
    builder.add(vertices,faces,mat=1)
    underside=[center-frame@Vector((0,0,thickness*.09))]
    underside.extend(center+frame@Vector((radius*math.cos(-math.pi/2+math.pi*j/n),radius*math.sin(-math.pi/2+math.pi*j/n),-thickness*.09)) for j in range(n+1))
    builder.add(underside,[(0,j+1,j+2) for j in range(n)],mat=2)
    for j in range(0,n,max(1,n//max(2,s.mushroom_gills))):
        a=-math.pi/2+math.pi*(j+.5)/n
        v=[center+frame@Vector((t*radius*math.cos(a),t*radius*math.sin(a),-thickness*.08)) for t in [.1,1]]
        v += [p-frame@Vector((0,0,thickness*.025)) for p in reversed(v)]
        builder.add(v,[(0,1,2,3)],mat=2)


def _radial(builder,center,frame,radius,thickness,n,rings,kind,s):
    vertices=[]; faces=[]
    if kind in {'Morel','Puffball'}:
        # Closed oval/pear cap, unlike the radial umbrella families.
        for ring in range(rings+1):
            t=ring/rings
            radial=max(.002,radius*math.sin(math.pi*t)**(.75 if kind=='Morel' else 1)*( .68+.32*t if kind=='Morel' else 1))
            z=(1-t)*radius*(2.8 if kind=='Morel' else 1.8)-radius*.25
            for j in range(n):
                a=math.tau*j/n
                # A handful of broad folds gives Morel a readable cap outline;
                # avoid dense micro-ripples that disappear at game distance.
                ripple=(1+.055*math.sin(5*a+ring*.55)) if kind=='Morel' else 1
                pit=.025*radius*math.sin(j*2.1+ring*2.4) if kind=='Morel' else 0
                vertices.append(center+frame@Vector((radial*math.cos(a)*ripple,radial*math.sin(a)*ripple,z+pit)))
    else:
        for ring in range(rings+1):
            t=ring/rings
            radial=max(.002,radius*t)
            z=_cap_profile(kind,t,thickness)+s.mushroom_rim*t**10
            for j in range(n):
                a=math.tau*j/n
                vertices.append(center+frame@Vector((radial*math.cos(a),radial*math.sin(a),z)))
    for ring in range(rings):
        for j in range(n):
            a=ring*n+j; faces.append((a,(ring+1)*n+j,(ring+1)*n+(j+1)%n,ring*n+(j+1)%n))
    builder.add(vertices,faces,mat=1)
    if kind in {'Morel','Puffball'}:
        if s.glow in {'Under','All'}:
            inner=radius*.55
            disk=[center-frame@Vector((0,0,radius*.25))]
            disk.extend(center+frame@Vector((inner*math.cos(math.tau*j/n),inner*math.sin(math.tau*j/n),-radius*.25)) for j in range(n))
            builder.add(disk,[(0,j+1,(j+1)%n+1) for j in range(n)],mat=2)
        return
    underside=[center-frame@Vector((0,0,thickness*.1))]
    underside.extend(center+frame@Vector((radius*.98*math.cos(math.tau*j/n),radius*.98*math.sin(math.tau*j/n),-thickness*.1)) for j in range(n))
    builder.add(underside,[(0,(j+1)%n+1,j+1) for j in range(n)],mat=2)
    if s.mushroom_gills==0: return
    underside=center-frame@Vector((0,0,thickness*.12))
    for j in range(s.mushroom_gills):
        a=math.tau*j/s.mushroom_gills
        def p(t,z): return center+frame@Vector((radius*t*math.cos(a),radius*t*math.sin(a),z))
        builder.add([underside,p(.96,-thickness*.08),p(.96,-thickness*.08-thickness*.035),underside-frame@Vector((0,0,thickness*.04))],[(0,1,2,3)],mat=2)


def build(builder,s,ob):
    rng=random.Random(s.seed); kind=s.mushroom
    world_up=(ob.matrix_world.to_3x3().inverted()@Vector((0,0,1))).normalized()
    count=s.cluster
    for index in range(count):
        a=index*2.399963+rng.uniform(-.25,.25)
        spread=s.mushroom_cluster_radius*math.sqrt((index+.5)/count) if count>1 else 0
        origin=Vector((math.cos(a)*spread,math.sin(a)*spread,0))
        edge=spread/max(.001,s.mushroom_cluster_radius)
        scale=(1-.22*edge)*rng.uniform(.90,1.12)
        h=s.length*scale; radius=s.crown*scale*rng.uniform(.88,1.14)
        bend=s.bend+rng.uniform(-s.mushroom_bend_random,s.mushroom_bend_random)
        lean_angle=a+rng.uniform(-.75,.75)
        lean=Vector((math.cos(lean_angle),math.sin(lean_angle),0))*bend*h
        tip=origin+lean+Vector((0,0,h))
        if kind=='Coral':
            mat=1 if s.glow in {'Cap','All'} else 2 if s.glow=='Under' else 0
            base=origin+Vector((0,0,h*.3)); builder.tube([origin,base],max(.005,s.radius*.6),6,.55,mat=mat)
            for branch in range(7):
                angle=math.tau*branch/7+rng.uniform(-.15,.15)
                direction=Vector((math.cos(angle),math.sin(angle),0))
                joint=base+direction*radius*.42+Vector((0,0,h*.4))
                tip=joint+direction*radius*.38+Vector((0,0,h*rng.uniform(.3,.65)))
                builder.tube([base,joint,tip],max(.004,s.radius*.38),5,.17,mat=mat)
                side=Vector((-direction.y,direction.x,0))
                for sign in [-1,1]:
                    fork=joint.lerp(tip,.68)
                    end=fork+direction*radius*.17+side*sign*radius*.16+Vector((0,0,h*.33))
                    builder.tube([fork,end],max(.003,s.radius*.18),4,.05,mat=mat)
            continue
        stem=[origin,origin+lean*.35+Vector((0,0,h*.48)),tip]
        builder.tube(stem,s.radius,8,max(.08,1-s.mushroom_stem_taper))
        direction=(tip-stem[-2]).normalized()
        crown_axis=direction.lerp(world_up,s.auto_bend).normalized()
        if crown_axis.length<.001: crown_axis=world_up
        tilt_axis=Vector((-math.sin(lean_angle),math.cos(lean_angle),0))
        crown_axis=Quaternion(tilt_axis,rng.uniform(-s.mushroom_bend_threshold,s.mushroom_bend_threshold))@crown_axis
        s['lp_cap_axis']=tuple(crown_axis)
        frame=crown_axis.to_track_quat('Z','Y').to_matrix()
        facets=max(6,round(s.mushroom_cap_facets*s.mesh_detail))
        rings=max(2,round(s.mushroom_cap_rings*s.mesh_detail))
        if kind in {'Bracket','Oyster'}: _fan(builder,tip,frame,radius,s.thickness,facets,rings,kind,s)
        else: _radial(builder,tip,frame,radius,s.thickness,facets,rings,kind,s)
    s['lp_mushroom_count']=count
