"""Branching, ground-following roots with a smooth radius profile."""
import math
import random
from mathutils import Vector
from . import paths, tube_frames


def preset(settings):
    """Editable root defaults for the selected tree family."""
    plant_profile={
        'Banyan':('BUTTRESS',5.2,.62,.45,0,5,1.8),
        # Massive trees use a few flattened buttress webs. The old defaults
        # made five long, round-ended roots that looked like starfish arms.
        'Giant':('BUTTRESS',4.0,.42,.25,0,4,1.5),
        'Mountain Bonsai':('EXPOSED',5.2,.35,.75,0,4,1.5),
        'Bonsai Tree':('EXPOSED',5.2,.35,.75,0,4,1.5),
        'Twisted Pine':('EXPOSED',4.5,.35,.50,0,4,1.5),
        # Mangrove prop roots read as a few broad descending supports. The
        # main props already spread across the footprint, so extra radial
        # forks make them look like spines and are intentionally disabled.
        'Mangrove':('EXPOSED',6.2,.82,.55,0,8,1.7),
        'Baobab':('BUTTRESS',3.7,.48,.32,0,4,1.45),
        'Palm':('SURFACE',3.0,.32,.15,0,3,1.6), 'Coconut':('SURFACE',3.0,.32,.15,0,3,1.6),
        'Pine':('SURFACE',3.5,.36,.20,0,4,1.6),
        'Banana':('SURFACE',2.6,.30,.12,0,3,1.6),
        'Apple':('SURFACE',3.7,.42,.25,0,4,1.6),
        'Mango':('SURFACE',4.2,.45,.30,0,4,1.6),
        'Grape Vine':('SURFACE',3.0,.34,.22,0,3,1.6),
    }
    trunk_profiles={
        'BRANCHED':('SURFACE',3.8,.46,.30,0,4,1.6),
        'CONIFER':('SURFACE',3.5,.36,.20,0,4,1.6),
        'TWISTED_CONIFER':('EXPOSED',4.5,.35,.50,0,4,1.5),
        'PALM':('SURFACE',3.0,.32,.15,0,3,1.6),
        'PSEUDOSTEM':('SURFACE',2.6,.30,.12,0,3,1.6),
        'BONSAI':('EXPOSED',5.2,.35,.75,0,4,1.5),
        'STILT':('EXPOSED',6.2,.62,.55,0,8,1.7),
        'WILLOW':('SURFACE',4.2,.42,.28,0,4,1.6),
        'UMBRELLA':('SURFACE',3.8,.44,.28,0,4,1.6),
        'BAOBAB':('BUTTRESS',3.7,.48,.32,0,4,1.45),
        'DEAD':('SURFACE',3.4,.42,.24,0,3,1.6),
        'VINE':('SURFACE',3.0,.34,.22,0,3,1.6),
    }
    style,length,width,lift,forks,count,buttress_height=(trunk_profiles.get(settings.trunk_type)
        if settings.trunk_type!='AUTO' else plant_profile.get(settings.preset,('SURFACE',3.8,.46,.30,1,4,1.6)))
    settings.root_style=style
    settings.root_length=length
    settings.root_width=width
    settings.root_lift=lift
    settings.root_forks=forks
    settings.roots=count
    settings.root_buttress_height=buttress_height
    settings.root_tip=.22 if settings.preset in {'Broadleaf','Pine','Conifer','Palm','Coconut','Banana','Apple','Mango','Grape Vine'} else .28 if settings.preset in {'Mangrove','Banyan','Giant','Baobab','Bonsai Tree','Mountain Bonsai'} else .18
    settings.root_taper=1.15


def _ground_height(settings,owner,point,depsgraph,fallback_z):
    ground=settings.root_ground
    if not ground: return fallback_z
    if ground.type!='MESH' or ground==owner:
        raise ValueError('Root Ground must be a separate mesh surface')
    world=owner.matrix_world@point
    world.z+=max(2.,settings.height,settings.radius*settings.root_length)
    inverse=ground.matrix_world.inverted()
    origin=inverse@world
    direction=(inverse.to_3x3()@Vector((0,0,-1))).normalized()
    evaluated=ground.evaluated_get(depsgraph)
    hit,location,_,_=evaluated.ray_cast(origin,direction)
    if not hit:
        settings['lp_root_ground_misses']=settings.get('lp_root_ground_misses',0)+1
        return fallback_z
    return (owner.matrix_world.inverted()@(ground.matrix_world@location)).z


def _path(settings,owner,origin,angle,length,width,style,rng,depsgraph,base_ground_z,secondary=False):
    radial=Vector((math.cos(angle),math.sin(angle),0))
    sideways=Vector((-radial.y,radial.x,0))
    sign=rng.choice((-1,1))
    phase=rng.uniform(.7,1.45)
    count=settings.root_segments
    points=[]; radii=[]
    departure=0 if secondary else settings.radius*settings.root_departure
    reach_power={'SURFACE':1.35,'BUTTRESS':1.6,'EXPOSED':1.05}[style]
    for step in range(count+1):
        t=step/count
        radius=width*(settings.root_tip+(1-settings.root_tip)*(1-t)**settings.root_taper)
        if style=='BUTTRESS' and not secondary: radius*=1+.28*(1-t)**3
        lateral=sign*settings.root_wander*settings.radius*math.sin(math.pi*t*phase)*t
        reach=1-(1-t)**reach_power
        point=origin+radial*(departure+(length-departure)*reach)+sideways*lateral
        ground=_ground_height(settings,owner,point,depsgraph,base_ground_z)
        ground=base_ground_z+(ground-base_ground_z)*settings.root_ground_follow+settings.root_ground_offset
        settle={'SURFACE':.28,'BUTTRESS':.32,'EXPOSED':.76}[style]
        blend=min(1.,(t/settle)**1.25)
        start=origin.z if secondary else origin.z+settings.radius*({'SURFACE':.35,'BUTTRESS':.4,'EXPOSED':.85}[style])
        arch=settings.root_lift*settings.radius*math.sin(math.pi*t)*({'SURFACE':.08,'BUTTRESS':.10,'EXPOSED':1.}[style])
        bury_t=min(1.,max(0.,(t-.55)/.45))
        burial=width*settings.root_tip_bury*bury_t*bury_t*(3-2*bury_t)
        point.z=start*(1-blend)+(ground-radius*settings.root_sink)*blend+arch-burial
        points.append(point); radii.append(radius)
    return points,radii


def _tube(builder,path,radii,settings,branch_id,buttress=False):
    steps=max(1,math.ceil(builder.detail_scale))
    if steps>1:
        smooth=[]; smooth_r=[]
        for i in range(len(path)-1):
            p0=path[max(0,i-1)]; p1=path[i]
            p2=path[i+1]; p3=path[min(len(path)-1,i+2)]
            for j in range(steps):
                t=j/steps; t2=t*t; t3=t2*t
                smooth.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t2+(-p0+3*p1-3*p2+p3)*t3))
                smooth_r.append(radii[i]*(1-t)+radii[i+1]*t)
        path=smooth+[path[-1]]; radii=smooth_r+[radii[-1]]
    sides=max(6,round(8*builder.detail_scale))
    vertices=[]; faces=[]
    for station,(point,radius,(x,y)) in enumerate(zip(path,radii,tube_frames.frames(path))):
        along=station/(len(path)-1)
        vertical=settings.root_flatten
        if buttress:
            vertical+=(settings.root_buttress_height-vertical)*(1-along)**2
        for side in range(sides):
            theta=side*math.tau/sides
            radial=radius*(x*math.cos(theta)+y*math.sin(theta))
            radial.z*=vertical
            vertices.append(point+radial)
    faces.append(tuple(reversed(range(sides))))
    for station in range(len(path)-1):
        for side in range(sides):
            faces.append((station*sides+side,station*sides+(side+1)%sides,
                          (station+1)*sides+(side+1)%sides,(station+1)*sides+side))
    faces.append(tuple((len(path)-1)*sides+side for side in range(sides)))
    uv_start=len(builder.uv)
    builder.add(vertices,faces,branch_id=branch_id,branch_level=0,
                branch_t=[i/(len(path)-1) for i in range(len(path)) for _ in range(sides)])
    distance=[0.]
    for a,b in zip(path,path[1:]): distance.append(distance[-1]+(b-a).length)
    cursor=uv_start+sides
    for station in range(len(path)-1):
        for side in range(sides):
            builder.uv[cursor:cursor+4]=[(side/sides,distance[station]),((side+1)/sides,distance[station]),
                                         ((side+1)/sides,distance[station+1]),(side/sides,distance[station+1])]
            cursor+=4


def _even_stations(line,count):
    lengths=[(b-a).length for a,b in zip(line,line[1:])]
    total=sum(lengths)
    if total<.001: raise ValueError('Root guide spline must have length')
    samples=[]
    for station in range(count):
        target=total*station/(count-1)
        walked=0.
        for i,length in enumerate(lengths):
            if walked+length>=target or i==len(lengths)-1:
                samples.append(line[i].lerp(line[i+1],min(1.,max(0.,(target-walked)/max(length,1e-9)))))
                break
            walked+=length
    return samples


def _guided(settings,owner,base,depsgraph):
    controller=settings.root_guides
    if not controller or controller.type!='CURVE' or controller==owner:
        raise ValueError('Root Curves needs a separate Curve object with at least one open spline')
    inverse=owner.matrix_world.inverted()
    output=[]
    for index,world_line in enumerate(paths.curve_paths(controller)):
        line=[inverse@point for point in world_line]
        if (line[0]-line[-1]).length<.001:
            raise ValueError('Root guide splines must be open, from trunk toward root tip')
        if (line[-1]-base).length<(line[0]-base).length: line.reverse()
        line=_even_stations(line,max(settings.root_segments+1,min(48,len(line))))
        if (line[0]-base).length>.002: line.insert(0,base.copy())
        else: line[0]=base.copy()
        width=settings.radius*settings.root_width*random.Random(settings.root_seed+index*997).uniform(.88,1.12)
        radii=[]
        for i,point in enumerate(line):
            t=i/(len(line)-1)
            radius=width*(settings.root_tip+(1-settings.root_tip)*(1-t)**settings.root_taper)
            if settings.root_style=='BUTTRESS': radius*=1+.28*(1-t)**3
            radii.append(radius)
            if i and settings.root_guide_ground_follow:
                ground=_ground_height(settings,owner,point,depsgraph,base.z)
                bury_t=min(1.,max(0.,(t-.55)/.45))
                burial=width*settings.root_tip_bury*bury_t*bury_t*(3-2*bury_t)
                target=(base.z+(ground-base.z)*settings.root_ground_follow+
                        settings.root_ground_offset-radius*settings.root_sink-burial)
                point.z+=min(1.,t*4)*settings.root_guide_ground_follow*(target-point.z)
        output.append((index,line,radii))
    if not output: raise ValueError('Root Curves has no usable open splines')
    return output


def _forks(builder,settings,owner,base,depsgraph,path,radii,root_id,index,seed):
    result=[]
    for fork in range(settings.root_forks):
        station=min(len(path)-2,round((len(path)-1)*min(.85,settings.root_fork_start+.18*fork)))
        tangent=path[min(station+1,len(path)-1)]-path[max(0,station-1)]
        direction=math.atan2(tangent.y,tangent.x)+(1 if (index+fork)%2 else -1)*settings.root_fork_angle*(1+.25*fork)
        fork_rng=random.Random(seed*1009+index*97+fork*17)
        extent=sum((b-a).length for a,b in zip(path,path[1:]))*settings.root_fork_reach*(1+.2*fork)*fork_rng.uniform(.85,1.15)
        child,child_radii=_path(settings,owner,path[station],direction,extent,radii[station]*settings.root_fork_width,
                                'SURFACE',fork_rng,depsgraph,base.z,secondary=True)
        child_id=-(1000+index*settings.root_forks+fork+1) if root_id>-2000 else -(3000+index*settings.root_forks+fork+1)
        _tube(builder,child,child_radii,settings,child_id)
        result.append((child_id,root_id,child))
    return result


def build(builder,settings,owner,trunk_base,*,trunk_at,stilt=False):
    """Return (stable negative branch ID, parent ID, path) for branch metadata."""
    settings['lp_root_ground_misses']=0
    if settings.root_guide_mode=='AUTO' and settings.roots<=0: return []
    if settings.root_guide_mode=='HYBRID' and settings.roots<=0 and not settings.root_guides: return []
    depsgraph=None
    if settings.root_ground:
        depsgraph=__import__('bpy').context.evaluated_depsgraph_get()
        depsgraph.update()
    rng=random.Random(settings.root_seed)
    base=Vector(trunk_base)
    result=[]
    count=settings.roots if settings.root_guide_mode!='CURVE' else 0
    for index in range(count):
        # Golden-angle spacing avoids a perfect four/five-spoke star while
        # retaining broad coverage around the trunk.
        angle=index*2.399963229728653+rng.uniform(-settings.root_spread,settings.root_spread)
        length=settings.radius*settings.root_length*rng.uniform(1-settings.root_length_random,1+settings.root_length_random)
        width=settings.radius*settings.root_width*rng.uniform(.88,1.12)
        origin=base.copy()
        if stilt:
            # Mangrove prop roots leave the stem above ground, then descend
            # outward. This gives the preset a stilt-root identity instead of
            # reusing a flat radial root crown.
            height_t=.30+.42*((index%3)/2)+rng.uniform(-.025,.025)
            trunk=trunk_at(height_t)
            radial=Vector((math.cos(angle),math.sin(angle),0))
            origin=trunk+radial*(settings.radius*.62)
            width*=.82+.15*(index%2)
        path,radii=_path(settings,owner,origin,angle,length,width,settings.root_style,rng,depsgraph,base.z)
        root_id=-(index+1)
        _tube(builder,path,radii,settings,root_id,buttress=settings.root_style=='BUTTRESS')
        result.append((root_id,0,path))
        result.extend(_forks(builder,settings,owner,base,depsgraph,path,radii,root_id,index,settings.root_seed))
    if settings.root_guide_mode!='AUTO' and settings.root_guides:
        for index,path,radii in _guided(settings,owner,base,depsgraph):
            root_id=-(2000+index+1)
            _tube(builder,path,radii,settings,root_id,buttress=settings.root_style=='BUTTRESS')
            result.append((root_id,0,path))
            result.extend(_forks(builder,settings,owner,base,depsgraph,path,radii,root_id,index,settings.root_seed))
    elif settings.root_guide_mode=='CURVE':
        raise ValueError('Curves Only needs a Root Curves object')
    return result
