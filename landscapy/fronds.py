"""Structured fronds. Rachis meshes carry separately UV-mapped leaf cards."""
import math
import random
from mathutils import Vector, Matrix, Quaternion

PATTERNS = {'Opposite', 'Alternate', 'Spiral', 'Whorl', 'Conifer', 'Palm', 'Banana'}


def frame(direction, face):
    z = direction.normalized()
    x = face.cross(z).normalized()
    if x.length < .01:
        x = z.to_track_quat('Z', 'Y') @ Vector((1, 0, 0))
    y = z.cross(x).normalized()
    return Matrix((x, y, z)).transposed()


def boughs(s, anchors, live=False):
    """Order whole boughs so a tight budget fills the crown before adding layers."""
    anchors=[item for item in anchors if len(item)>4 and item[4] in {0,1}]
    if not anchors:
        return []

    # Start with the leader, then cover the major branches at successively
    # finer intervals. This order is shared by Generate and live density.
    leader=[item for item in anchors if item[4]==0]
    primary=[item for item in anchors if item[4]==1]
    order=[]
    pending=[(0,len(primary))]
    while pending:
        following=[]
        for start,end in pending:
            if start>=end: continue
            middle=(start+end)//2
            order.append(primary[middle])
            following.extend(((start,middle),(middle+1,end)))
        pending=following
    tiers={}
    for anchor in primary:
        if len(anchor)>6 and anchor[6] is not None:
            tiers.setdefault(anchor[6],[]).append(anchor)
    # A small budget must reach every vertical tier before revisiting one.
    # Pick in the previous broad-to-fine order within each tier.
    tier_visits={}
    prioritized=[]
    for rank,anchor in enumerate(order,min(1,len(leader))):
        tier=anchor[6] if len(anchor)>6 else None
        visit=tier_visits.get(tier,0) if tier is not None else 0
        if tier is not None:
            tier_visits[tier]=visit+1
        prioritized.append((visit,rank,anchor))
    ordered=list(enumerate(leader[:1]))
    ordered.extend((rank,anchor) for _,rank,anchor in sorted(prioritized))
    ordered.extend(enumerate(leader[1:],len(order)+1))
    bridges={}
    previous=None
    for tier,members in sorted(tiers.items()):
        altitude=sum(item[0].z for item in members)/len(members)
        if previous is not None:
            azimuth=sorted(members,key=lambda item:math.atan2(item[1].y,item[1].x))
            panels=min(3,len(members))
            for index in range(panels):
                member=azimuth[(index*len(members)//panels+tier)%len(members)]
                bridges[member[3]]=altitude-previous
        previous=altitude
    result=[]
    requested=0
    for layer in range(4):
        for rank,(shape_rank,anchor) in enumerate(ordered):
            origin,direction,multiplier,branch_id,level=anchor[:5]
            bridge=layer==1 and branch_id in bridges
            if layer and not bridge and (level==0 or (shape_rank+layer)%3!=0 or
                                        (layer==1 and tiers)):
                continue
            length=s.length*multiplier
            direction=direction.normalized()
            basis=frame(direction,Vector((0,0,1)))
            side=basis.col[0].copy()
            line=anchor[5] if len(anchor)>5 else None
            rng=random.Random(s.seed*1009+shape_rank*9176+layer*83)
            phase=rng.uniform(-.10,.10)
            planes=s.count if layer==0 else 1
            threshold=(10*(rank+.5)/len(ordered) if layer==0 else (16,30,48)[layer-1])
            visible=s.density>=threshold
            if visible:
                requested+=planes
            if not (live or visible):
                continue
            # The primary skirt follows the wood, then hangs. Its shorter
            # side panels fill the space beside it without crossing its root.
            maturity=max(0.,min(1.,(.90-origin.z/max(.01,s.height))/.68))
            for plane in range(planes):
                side_sign=0 if plane==0 else 1 if plane%2 else -1
                spread=(0. if not side_sign else min(1.,.55+.11*(plane-1)))
                fan=side_sign*spread
                if layer:
                    fan=.84 if layer%2 else -.84
                curtain=bridge or (level==1 and plane==2 and origin.z>.28*s.height)
                # Keep the foliage away from the leader and branch collar.
                if curtain:
                    offset=(.015+.56*s.bough_clearance if bridge else .055+.48*s.bough_clearance)
                else:
                    offset=.20*abs(fan)+.09*layer
                    if level==1: offset+=.24*s.bough_clearance
                t=min(.87,s.frond_petiole+(1-s.frond_petiole)*offset)
                if level==1 and len(anchor)>6 and anchor[6] is not None:
                    # The visible support on an automatic bough ends at .58.
                    t=min(t,max(s.frond_petiole,.55))
                position=origin+direction*length*t
                tangent=direction
                if line:
                    station=t*(len(line)-1)
                    lower=min(len(line)-2,int(station))
                    position=line[lower].lerp(line[lower+1],station-lower)
                    segment=line[lower+1]-line[lower]
                    if segment.length_squared>1e-12:
                        tangent=segment.normalized()
                sweep=s.frond_angle*fan
                curtain_face=None
                if curtain:
                    # The spray overlaps foliage on the tier below while
                    # leaving the branch junction and leader open.
                    radial=Vector((tangent.x,tangent.y,0))
                    if radial.length_squared<1e-10: radial=side.cross(Vector((0,0,1)))
                    radial.normalize()
                    axis=(radial*(.32 if bridge else .42)-side*.18+Vector((0,0,-1.))).normalized()
                    curtain_face=radial
                    factor=1.06
                    roll=phase-.15
                elif level==0:
                    axis=(tangent+side*sweep*.72).normalized()
                    factor=1-.14*abs(fan)
                    roll=phase+fan*.42
                else:
                    # Horizontal limbs carry visibly pendulous sprays.
                    horizontal=Vector((tangent.x,tangent.y,0))
                    if horizontal.length_squared<1e-10: horizontal=side.cross(Vector((0,0,1)))
                    horizontal.normalize()
                    droop=.43+.42*maturity+s.frond_droop*.85
                    droop+=.55*abs(fan) if fan>0 else -.12*abs(fan)
                    droop+=.14*layer
                    axis=(horizontal*math.cos(sweep)+side*math.sin(sweep)+Vector((0,0,-droop))).normalized()
                    factor=(1-.28*abs(fan))*(1-.13*layer)
                    roll=phase+fan*.65
                height=min(s.frond_width,max(.15,length*(1-t)*1.30*factor))
                ground_clearance = max(.15,(position.z-.20*s.height)/max(.1,-axis.z)) if axis.z<-.05 else height
                height=min(height,ground_clearance)
                if curtain:
                    # The card fills the interval below its limb. Limiting the
                    # drop also keeps the lower skirt above the ground.
                    room=max(.15,(position.z-.22*s.height)/max(.1,-axis.z))
                    span=(bridges[branch_id]*1.58 if bridge else max(.126*s.height,length*.74))
                    span*=1-.44*s.bough_clearance
                    height=min(height,room,span)
                width=min(s.frond_leaf_width,height*(.76 if curtain else .98-.10*abs(fan)))
                face=Quaternion(axis,roll)@(curtain_face if curtain else Vector((0,0,1)))
                result.append((position,axis,{
                    'frame':frame(axis,face),'width':width,'height':height,
                    'pivot':.02,'segments':4 if s.bough_arch or s.bough_fold else 1,
                    'bough_profile':(s.bough_arch,s.bough_fold*(.40 if curtain else 1.)),
                    'force_quad':True,'branch_id':branch_id,
                    'branch_level':level,'branch_t':t if level==1 else .96,
                    **({'bough_density':threshold} if live else {}),
                }))
    s['lp_frond_requested']=requested
    s['lp_frond_cards']=min(requested,s.limit)
    return result if live else result[:s.limit]


def arrange(builder, s, anchors, pattern=None):
    """Anchors are local origin/direction/(optional length multiplier).

    Limit applies to final cards. Even integer quotas cover all retained
    anchors before adding more leaflets; huge input cannot expand unboundedly.
    """
    pattern = pattern or s.pattern
    if pattern=='Conifer' and s.kind=='Tree':
        return boughs(s,anchors)
    if not anchors or s.density <= 0:
        return []
    anchors = list(anchors)
    if len(anchors) > s.limit:
        anchors = [anchors[(i * len(anchors)) // s.limit] for i in range(s.limit)]
    if not anchors:
        s['lp_frond_cards']=0; s['lp_frond_requested']=0
        return []
    stations = s.count
    mode = getattr(s, 'palm_card_mode', 'AUTO')
    is_palm_single = (pattern == 'Palm' and (mode == 'SINGLE' or (mode == 'AUTO' and s.kind == 'Tree')))
    single_card = pattern == 'Banana' or is_palm_single
    per = (1 if single_card else
           stations * (s.frond_whorl if pattern == 'Whorl' else 2 if pattern in {'Palm', 'Conifer', 'Opposite'} else 1))
    total = min(s.limit, len(anchors) * per)
    result = []
    for index, anchor in enumerate(anchors):
        budget = total // len(anchors) + (index < total % len(anchors))
        if not budget:
            continue
        origin, direction = anchor[:2]
        direction = direction.normalized()
        branch_id = anchor[3] if len(anchor)>3 else -1
        branch_level = anchor[4] if len(anchor)>4 else -1
        length = s.length * (anchor[2] if len(anchor) > 2 else 1)
        basis = frame(direction, Vector((0, 0, 1)))
        side = basis.col[0].copy()
        face = basis.col[1].copy()
        sag = Vector((0,0,-1))
        if abs(direction.z) > .9:
            sag = (-face*.65 + sag*.35).normalized()
        def center(t):
            droop_fac = max(0., t - .22)**2 / .61 if pattern in {'Banana', 'Palm'} else t * t
            return origin + direction * length * t + sag * (s.frond_droop * length * droop_fac)
        def tangent(t):
            tangent_droop = (2 * max(0., t - .22) / .61) if pattern in {'Banana', 'Palm'} else (2 * t)
            return (direction + sag * (s.frond_droop * tangent_droop)).normalized()
        path = [center(i / s.frond_segments) for i in range(s.frond_segments + 1)]
        builder.tube(path, s.frond_stem_radius, s.frond_stem_sides, s.frond_stem_tip,branch_id=branch_id,branch_level=branch_level)
        if single_card:
            start = s.frond_petiole
            # One continuous blade/card per branch, following the 3D rachis spine.
            frond_w = s.frond_width * (1.25 if pattern == 'Palm' else 1.0)
            result.append((center(start), direction, {
                'frame': basis, 'width': frond_w, 'height': length * (1-start),
                'pivot': 0., 'segments': max(6, s.frond_segments), 'blade': True,
                'palm': pattern == 'Palm',
                'spine': [center(start+(1-start)*i/s.frond_segments)-center(start) for i in range(s.frond_segments+1)],
                'taper': s.frond_taper,'branch_id':branch_id,'branch_level':branch_level,'branch_t':(start+1)*.5,
            }))
            continue
        for selected in range(budget):
            # Deterministic full-span subset when the final card cap is small.
            j = (selected * per) // budget
            pair = 2 if pattern in {'Palm', 'Conifer', 'Opposite'} else s.frond_whorl if pattern == 'Whorl' else 1
            station, member = divmod(j, pair)
            t = s.frond_petiole + (1-s.frond_petiole) * (station+.5)/stations
            if pattern in {'Palm', 'Conifer', 'Opposite'}:
                radial = side * (1 if member == 0 else -1)
            elif pattern == 'Alternate':
                radial = side * (1 if station % 2 == 0 else -1)
            else:
                angle = (member * math.tau / pair if pattern == 'Whorl' else station * 2.399963)
                radial = side*math.cos(angle)+face*math.sin(angle)
            leaflet_direction=radial
            if pattern=='Palm':
                # The paired leaflets fold down from the rachis into a soft V.
                leaflet_direction=(radial-face*.42).normalized()
            leaf_axis = (leaflet_direction*math.cos(s.frond_angle)+tangent(t)*math.sin(s.frond_angle)).normalized()
            leaf_face = tangent(t).cross(leaflet_direction).normalized()
            if leaf_face.dot(face) < 0:
                leaf_face.negate()
            size = max(.04, 1-s.frond_taper*t)
            span=1.
            if pattern=='Palm':
                progress=(station+.5)/stations
                span=.28+.72*math.sin(math.pi*progress)**.72
            result.append((center(t), leaf_axis, {
                'frame': frame(leaf_axis, leaf_face), 'width': s.frond_leaf_width * size,
                'height': s.frond_width * .5 * size * span, 'pivot': 0.,
                'segments': s.subdivisions, 'leaf_droop': s.frond_leaf_droop,
                'branch_id':branch_id,'branch_level':branch_level,'branch_t':t,
            }))
    s['lp_frond_cards'] = len(result)
    s['lp_frond_requested'] = len(anchors) * per
    return result


def preset(s, name=None):
    """Only shape settings; never replace user texture/material slots."""
    config = {
        # Pinnate fronds use fewer, broader paired leaflets so the compound
        # leaf reads as a single sweeping silhouette at gameplay distance.
        'Palm': (13, 1.80, .28, .40, .46, .33, .18),
        # A banana blade is one continuous card with a curved rachis, not a
        # bundle of small leaflets.
        'Banana': (1, 1.46, .15, .36, .38, .18, .18),
        'Conifer': (22, 1.25, .18, .78, .12, .62, .08),
        'Twisted Pine': (18, 1.05, .16, .80, .12, .58, .1),
    }.get(name or s.preset, (12,1.2,.28,.7,.2,.35,.15) if (name or s.preset) in PATTERNS else None)
    if config:
        s.count, s.frond_width, s.frond_leaf_width, s.frond_taper, s.frond_droop, s.frond_angle, s.frond_petiole = config
        s.frond_segments = 8
        s.frond_stem_radius = .018 if (name or s.pattern) in {'Palm', 'Banana'} else .012
        s.frond_leaf_droop = .15
        s.size_min = .92; s.size_max = 1.08
        s.yaw = .12; s.pitch = .08; s.roll = .08
        s.bend = .03; s.curl = .015; s.twist = 0
        if (name or s.pattern)=='Banana':
            s.blade_edge_tear=.20; s.blade_tear_chance=.24
    if (name or s.pattern)=='Conifer' and s.kind=='Tree':
        # A Tree Needle Spray is a large bough canopy cluster on each primary
        # whorl branch. Three crossed editable quads establish a broad mass.
        s.count=3; s.frond_width=2.85; s.frond_leaf_width=2.65
        s.frond_taper=.18; s.frond_petiole=.10; s.frond_angle=.48
        s.frond_droop=.10; s.frond_leaf_droop=0; s.bough_clearance=.75
        s.bough_arch=0.; s.bough_fold=.29
        s.size_min=.92; s.size_max=1.08
        s.yaw=.14; s.pitch=.08; s.roll=.08


def draw(layout, s):
    if s.kind not in {'Tree','Foliage'} or s.pattern not in PATTERNS:
        return
    branch_spray=s.kind=='Tree' and s.pattern=='Conifer'
    head, body = layout.panel('LP_Fronds', default_closed=False)
    head.label(text='Leaf Type Shape')
    if body:
        live_path=s.kind=='Foliage' and s.live_surface and s.controller and s.controller.type=='CURVE' and s.pattern in {'Opposite','Alternate','Spiral','Whorl','Conifer','Palm','Banana'}
        live_mesh=s.kind=='Foliage' and s.live_surface and s.controller and s.controller.type=='MESH' and s.pattern in PATTERNS
        live_tree=s.kind=='Tree' and s.live_surface and s.instance_cards and s.pattern in PATTERNS
        tree_bough=branch_spray and not (s.controller and s.controller.type=='MESH')
        body.operator('landscapy.frond_preset')
        body.operator('landscapy.starter_texture')
        if tree_bough:
            for name in ('bough_clearance','bough_arch','bough_fold'): body.prop(s,name)
        for name in ['count', 'length', 'frond_width', 'frond_leaf_width', 'frond_taper', 'frond_petiole', 'frond_angle', 'frond_droop', 'frond_leaf_droop', 'frond_stem_radius', 'frond_stem_tip', 'frond_stem_sides', 'frond_segments']:
            if (live_path and name=='length') or ((live_path or live_mesh or live_tree) and s.pattern=='Banana' and name in {'count','frond_leaf_width','frond_angle'}): continue
            if tree_bough and name in {'frond_taper','frond_leaf_droop','frond_stem_radius','frond_stem_tip','frond_stem_sides','frond_segments'}: continue
            label=('Quads per Needle Cluster' if tree_bough and name=='count' else
                   'Cluster Length' if tree_bough and name=='frond_width' else
                   'Cluster Width' if tree_bough and name=='frond_leaf_width' else None)
            body.prop(s, name, text=label) if label else body.prop(s, name)
        if s.pattern == 'Whorl':
            body.prop(s, 'frond_whorl')
        if s.pattern == 'Palm':
            body.prop(s, 'palm_card_mode')
        if s.pattern == 'Banana':
            for name in ('blade_edge_tear','blade_tear_chance','blade_tear_seed'):
                body.prop(s,name)
        if (live_mesh or live_tree and s.controller and s.controller.type=='MESH') and s.mode in {'Auto','Volume'}:
            body.prop(s,'canopy_alignment')
        body.label(text='Density and Limit update live. Regenerate after shape edits.' if live_tree and tree_bough else
                   'Tree mesh canopy scatters live rachises; Density counts fronds per area/volume.' if live_tree and s.controller and s.controller.type=='MESH' else
                   'Tree branch guides feed live frond cards; Regenerate after changing Tree structure.' if live_tree else
                   'Mesh scatters whole Banana blades; Density counts blades per area/volume.' if live_mesh and s.pattern=='Banana' else
                   'One blade per Curve spline; Curve sets length and shape.' if live_path and s.pattern=='Banana' else
                   'Curve sets rachis length and shape.' if live_path else
                   'Mesh scatters live rachises; Density counts fronds per area/volume.' if live_mesh else
                   'Limit caps final leaf cards, including all fronds.')
