"""Live Geometry Nodes cards on meshes/curves and optional Ivy vine geometry."""
import math
import colorsys
import bpy
import bmesh
from . import instance_cards, paths

PAIRED_PATH_PATTERNS={'Opposite','Conifer','Palm'}
ARRANGED_PATH_PATTERNS=PAIRED_PATH_PATTERNS|{'Alternate','Spiral','Whorl'}


def supported(settings):
    if settings.kind not in {'Tree','Foliage','Ivy'} or not settings.controller or settings.controller.type not in {'MESH','CURVE'}:
        raise ValueError('Live Geometry Cards need Tree, Foliage, or Ivy and a mesh or curve controller')
    if settings.kind=='Tree' and (settings.controller.type!='MESH' or settings.pattern not in ARRANGED_PATH_PATTERNS|{'Banana'}):
        raise ValueError('Live Tree mesh canopy needs an arranged Leaf Type or Broad Lamina')
    if settings.kind=='Ivy' and settings.controller.type=='MESH' and settings.mode not in {'Auto','Surface'}:
        raise ValueError('Live Ivy mesh controllers use Auto or Surface mode')
    if settings.kind=='Ivy' and settings.controller.type=='MESH' and settings.target and settings.target!=settings.controller:
        raise ValueError('Live Ivy mesh growth uses its controller as the surface; use a Curve controller for a separate target')
    if settings.kind=='Ivy' and settings.target:
        if settings.target==settings.id_data or settings.target.type!='MESH':
            raise ValueError('Live Ivy surface target must be a separate mesh object')
        evaluated_target=settings.target.evaluated_get(bpy.context.evaluated_depsgraph_get())
        target_mesh=evaluated_target.to_mesh()
        try:
            if not target_mesh.polygons:
                raise ValueError('Live Ivy surface target needs at least one face')
        finally: evaluated_target.to_mesh_clear()
    if settings.kind=='Ivy' and settings.ivy_projection=='CUSTOM' and sum(v*v for v in settings.ivy_ray_direction)<1e-12:
        raise ValueError('Custom Ivy ray direction must be nonzero')
    if settings.controller==settings.id_data:
        raise ValueError('Live Geometry Cards controller cannot be its own generator')
    if settings.controller.type=='CURVE':
        if settings.mode not in {'Auto','Path'}:
            raise ValueError('Live curve controllers use Auto or Path mode')
        curve=settings.controller.data
        if curve.bevel_depth or curve.extrude or curve.bevel_object:
            raise ValueError('Live Path needs an unbeveled centerline curve; Ivy and arranged Foliage generate their own stems')
        if not any(len(path)>1 and any((b-a).length>1e-5 for a,b in zip(path,path[1:]))
                   for path in paths.curve_paths(settings.controller)):
            raise ValueError('Live Path controller needs a nonzero-length spline')
        mode='Path'
    else:
        if settings.mode not in {'Auto','Surface','Volume'}:
            raise ValueError('Live mesh controllers use Surface, Volume, or Auto mode')
        evaluated=settings.controller.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=evaluated.to_mesh()
        try:
            if not mesh.polygons:
                raise ValueError('Live Geometry Cards controller needs faces')
            bm=bmesh.new()
            try:
                bm.from_mesh(mesh)
                closed=bool(bm.faces) and all(edge.is_manifold for edge in bm.edges)
                enclosed_volume=abs(bm.calc_volume(signed=True)) if closed else 0
            finally: bm.free()
            mode=('Surface' if settings.kind=='Ivy' else 'Volume' if closed else 'Surface') if settings.mode=='Auto' else settings.mode
            if mode=='Volume' and not closed:
                raise ValueError('Live Volume requires a closed manifold mesh; use Surface for an open controller')
            if mode=='Volume' and enclosed_volume<1e-7:
                raise ValueError('Live Volume controller encloses no usable volume; check its faces and scale')
        finally: evaluated.to_mesh_clear()
    if settings.pattern in ARRANGED_PATH_PATTERNS and settings.kind not in {'Tree','Foliage'}:
        raise ValueError('Live arranged leaf patterns require a Tree or Foliage generator')
    if settings.pattern=='Banana' and settings.kind not in {'Tree','Foliage'}:
        raise ValueError('Live Broad Lamina blades require a Tree or Foliage generator')
    return mode


def localize(source):
    """A duplicated asset needs its own driver targets before a live edit."""
    modifier=instance_cards.modifier(source)
    if not modifier or not modifier.node_group: return None
    group=modifier.node_group
    if group.users>1:
        original=group
        group=original.copy()
        modifier.node_group=group
        if group.animation_data:
            for curve in group.animation_data.drivers:
                for variable in curve.driver.variables:
                    for target in variable.targets:
                        if target.id and target.id.type=='MESH' and target.id!=source:
                            target.id=source
    if source.get('lp_live_mode')=='TreePath':
        for node in group.nodes:
            if node.type!='OBJECT_INFO': continue
            guide=node.inputs['Object'].default_value
            if not guide or not guide.get('lp_tree_frond_guide') or guide.parent==source: continue
            local=guide.copy(); local.data=guide.data.copy()
            (source.users_collection[0] if source.users_collection else bpy.context.scene.collection).objects.link(local)
            local.parent=source; local.matrix_parent_inverse.identity()
            local.hide_set(True)
            node.inputs['Object'].default_value=local
    return group


def _prototype(source,number,slot,material,settings):
    size=slot.size*.45
    pivot=slot.pivot-.5 if settings.kind in {'Foliage','Tree'} and settings.pattern in ARRANGED_PATH_PATTERNS else slot.pivot
    if settings.card=='Valley' and settings.subdivisions==1:
        coords=[(0,0),(1,0),(1,1),(0,1),(.5,.5)]
        faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4)]
    else:
        n=settings.subdivisions
        coords=[(x/n,y/n) for y in range(n+1) for x in range(n+1)]
        faces=[(y*(n+1)+x,y*(n+1)+x+1,(y+1)*(n+1)+x+1,(y+1)*(n+1)+x)
               for y in range(n) for x in range(n)]
    vertices=[]
    for u,v in coords:
        x=(u-.5)*size*slot.aspect*(1-settings.card_taper*v)
        z=(v-pivot)*size
        depth=(0 if settings.random_card_shape else settings.bend*z*z)+settings.curl*math.sin(v*math.pi)*size+settings.twist*x*z
        if settings.card=='Valley' and not settings.random_card_shape:
            depth-=settings.valley*math.sin(math.pi*u)*math.sin(math.pi*v)*size
        vertices.append((x,depth,z))
    mesh=bpy.data.meshes.new(source.name+f' • Live Card {number}')
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    mesh.materials.append(material)
    uv=mesh.uv_layers.new(name='UVMap')
    u0,v0,u1,v1=slot.uv_region
    for face in mesh.polygons:
        for loop,vertex in zip(face.loop_indices,face.vertices):
            u,v=coords[vertex]
            uv.data[loop].uv=(u0+u*(u1-u0),v0+v*(v1-v0))
    for name in ('lp_leaf_wind','lp_wind'):
        attr=mesh.attributes.new(name,'FLOAT','POINT')
        for index,item in enumerate(attr.data): item.value=coords[index][1]**2
    for name,values in [('lp_card_u',[u for u,_ in coords]),('lp_card_v',[v for _,v in coords]),
                        ('lp_card_local_z',[(v-pivot)*size for _,v in coords]),
                        ('lp_card_size',[size]*len(coords))]:
        attr=mesh.attributes.new(name,'FLOAT','POINT')
        for item,value in zip(attr.data,values): item.value=value
    card=mesh.attributes.new('lp_card','BOOLEAN','FACE')
    for item in card.data: item.value=True
    return bpy.data.objects.new(source.name+f' • Live Card {number}',mesh)


def _ivy_target_path(settings,n,link,path_curve,driver,store):
    """Project a resampled Curve guide by nearest point or a directional ray."""
    target=n.new('GeometryNodeObjectInfo')
    target.name='Live Ivy Surface Target'
    target.inputs['Object'].default_value=settings.target or settings.controller
    target.transform_space='RELATIVE'
    resample=n.new('GeometryNodeResampleCurve')
    resample.name='Live Ivy Surface Samples'
    step=n.new('ShaderNodeValue'); driver(step.outputs[0],'ivy_step')
    budget=n.new('ShaderNodeValue'); driver(budget.outputs[0],'ivy_max_steps')
    length=n.new('GeometryNodeSplineLength')
    count=n.new('ShaderNodeMath'); count.operation='DIVIDE'
    link(length.outputs['Length'],count.inputs[0]); link(step.outputs[0],count.inputs[1])
    count_up=n.new('ShaderNodeMath'); count_up.operation='CEIL'
    link(count.outputs[0],count_up.inputs[0])
    plus_end=n.new('ShaderNodeMath'); plus_end.operation='ADD'
    link(count_up.outputs[0],plus_end.inputs[0]); plus_end.inputs[1].default_value=1
    capped=n.new('ShaderNodeMath'); capped.operation='MINIMUM'
    link(plus_end.outputs[0],capped.inputs[0]); link(budget.outputs[0],capped.inputs[1])
    at_least_two=n.new('ShaderNodeMath'); at_least_two.operation='MAXIMUM'
    link(capped.outputs[0],at_least_two.inputs[0]); at_least_two.inputs[1].default_value=2
    link(at_least_two.outputs[0],resample.inputs['Count'])
    link(path_curve,resample.inputs['Curve'])
    path_curve=resample.outputs['Curve']
    position=n.new('GeometryNodeInputPosition')
    probe=n.new('ShaderNodeValue'); driver(probe.outputs[0],'ivy_probe')
    if settings.ivy_projection=='NEAREST':
        nearest=n.new('GeometryNodeProximity'); nearest.target_element='FACES'
        link(target.outputs['Geometry'],nearest.inputs['Geometry'])
        link(position.outputs['Position'],nearest.inputs['Sample Position'])
        sample=n.new('GeometryNodeSampleNearestSurface'); sample.data_type='FLOAT_VECTOR'
        link(target.outputs['Geometry'],sample.inputs['Mesh'])
        normal=n.new('GeometryNodeInputNormal')
        link(normal.outputs['Normal'],sample.inputs['Value'])
        link(position.outputs['Position'],sample.inputs['Sample Position'])
        within=n.new('FunctionNodeCompare'); within.data_type='FLOAT'; within.operation='LESS_EQUAL'
        link(nearest.outputs['Distance'],within.inputs[0]); link(probe.outputs[0],within.inputs[1])
        hit=n.new('FunctionNodeBooleanMath'); hit.operation='AND'
        link(within.outputs[0],hit.inputs[0]); link(nearest.outputs['Is Valid'],hit.inputs[1])
        hit_field=hit.outputs[0]
        surface_point=nearest.outputs['Position']
        surface_normal=sample.outputs['Value']
    else:
        ray=n.new('GeometryNodeRaycast'); ray.name='Live Ivy Directional Raycast'
        link(target.outputs['Geometry'],ray.inputs['Target Geometry'])
        if settings.ivy_projection=='DOWN':
            direction=n.new('ShaderNodeCombineXYZ'); direction.inputs['Z'].default_value=-1
            direction_field=direction.outputs[0]
        else:
            direction=n.new('ShaderNodeCombineXYZ')
            for index,axis in enumerate(('X','Y','Z')):
                driver(direction.inputs[axis],f'ivy_ray_direction[{index}]')
            normalized=n.new('ShaderNodeVectorMath'); normalized.operation='NORMALIZE'
            link(direction.outputs[0],normalized.inputs[0])
            direction_field=normalized.outputs[0]
        # Starting a little behind the guide includes a guide exactly on the
        # target face, while Probe still measures its practical snap range.
        back=n.new('ShaderNodeVectorMath'); back.operation='SCALE'
        link(direction_field,back.inputs[0]); back.inputs['Scale'].default_value=-.001
        origin=n.new('ShaderNodeVectorMath'); origin.operation='ADD'
        link(position.outputs['Position'],origin.inputs[0]); link(back.outputs[0],origin.inputs[1])
        link(origin.outputs[0],ray.inputs['Source Position'])
        link(direction_field,ray.inputs['Ray Direction'])
        ray_length=n.new('ShaderNodeMath'); ray_length.operation='ADD'
        link(probe.outputs[0],ray_length.inputs[0]); ray_length.inputs[1].default_value=.001
        link(ray_length.outputs[0],ray.inputs['Ray Length'])
        hit_field=ray.outputs['Is Hit']
        surface_point=ray.outputs['Hit Position']
        surface_normal=ray.outputs['Hit Normal']
    path_curve=store(path_curve,'lp_surface_hit','BOOLEAN',hit_field)
    offset=n.new('ShaderNodeValue'); driver(offset.outputs[0],'ivy_offset')
    lift=n.new('ShaderNodeVectorMath'); lift.operation='SCALE'
    link(surface_normal,lift.inputs[0]); link(offset.outputs[0],lift.inputs['Scale'])
    destination=n.new('ShaderNodeVectorMath'); destination.operation='ADD'
    link(surface_point,destination.inputs[0]); link(lift.outputs[0],destination.inputs[1])
    displacement=n.new('ShaderNodeVectorMath'); displacement.operation='SUBTRACT'
    link(destination.outputs[0],displacement.inputs[0]); link(position.outputs['Position'],displacement.inputs[1])
    projected=n.new('GeometryNodeSetPosition')
    link(path_curve,projected.inputs['Geometry']); link(hit_field,projected.inputs['Selection'])
    link(displacement.outputs[0],projected.inputs['Offset'])
    fallback=n.new('GeometryNodeSwitch'); fallback.input_type='VECTOR'
    link(hit_field,fallback.inputs['Switch'])
    fallback.inputs['False'].default_value=(0,-1,0)
    link(surface_normal,fallback.inputs['True'])
    return store(projected.outputs['Geometry'],'lp_surface_normal','FLOAT_VECTOR',fallback.outputs[0])


def _ivy_surface_seed(settings,n,link,driver):
    """A live tangent guide from the Ivy seed and direction on a mesh surface."""
    def vector_property(name):
        node=n.new('ShaderNodeCombineXYZ')
        for index,axis in enumerate(('X','Y','Z')):
            driver(node.inputs[axis],f'{name}[{index}]')
        return node.outputs[0]
    start=vector_property('ivy_start')
    direction=vector_property('ivy_direction')
    target=n.new('GeometryNodeObjectInfo')
    target.name='Live Ivy Seed Surface'
    target.inputs['Object'].default_value=settings.controller
    target.transform_space='RELATIVE'
    sample=n.new('GeometryNodeSampleNearestSurface'); sample.data_type='FLOAT_VECTOR'
    link(target.outputs['Geometry'],sample.inputs['Mesh'])
    normal=n.new('GeometryNodeInputNormal')
    link(normal.outputs['Normal'],sample.inputs['Value'])
    link(start,sample.inputs['Sample Position'])
    def tangent(vector):
        dot=n.new('ShaderNodeVectorMath'); dot.operation='DOT_PRODUCT'
        link(vector,dot.inputs[0]); link(sample.outputs['Value'],dot.inputs[1])
        along=n.new('ShaderNodeVectorMath'); along.operation='SCALE'
        link(sample.outputs['Value'],along.inputs[0]); link(dot.outputs['Value'],along.inputs['Scale'])
        across=n.new('ShaderNodeVectorMath'); across.operation='SUBTRACT'
        link(vector,across.inputs[0]); link(along.outputs[0],across.inputs[1])
        return across.outputs[0]
    requested=tangent(direction)
    x=n.new('ShaderNodeCombineXYZ'); x.inputs['X'].default_value=1
    y=n.new('ShaderNodeCombineXYZ'); y.inputs['Y'].default_value=1
    fallback_x=tangent(x.outputs[0]); fallback_y=tangent(y.outputs[0])
    def valid(vector):
        length=n.new('ShaderNodeVectorMath'); length.operation='LENGTH'
        link(vector,length.inputs[0])
        compare=n.new('FunctionNodeCompare'); compare.data_type='FLOAT'; compare.operation='GREATER_THAN'
        link(length.outputs['Value'],compare.inputs[0]); compare.inputs[1].default_value=.001
        return compare.outputs[0]
    choice=n.new('GeometryNodeSwitch'); choice.input_type='VECTOR'
    link(valid(fallback_x),choice.inputs['Switch'])
    link(fallback_y,choice.inputs['False']); link(fallback_x,choice.inputs['True'])
    choose_direction=n.new('GeometryNodeSwitch'); choose_direction.input_type='VECTOR'
    link(valid(requested),choose_direction.inputs['Switch'])
    link(choice.outputs[0],choose_direction.inputs['False'])
    link(requested,choose_direction.inputs['True'])
    normalized=n.new('ShaderNodeVectorMath'); normalized.operation='NORMALIZE'
    link(choose_direction.outputs[0],normalized.inputs[0])
    length=n.new('ShaderNodeValue'); driver(length.outputs[0],'length')
    travel=n.new('ShaderNodeVectorMath'); travel.operation='SCALE'
    link(normalized.outputs[0],travel.inputs[0]); link(length.outputs[0],travel.inputs['Scale'])
    end=n.new('ShaderNodeVectorMath'); end.operation='ADD'
    link(start,end.inputs[0]); link(travel.outputs[0],end.inputs[1])
    line=n.new('GeometryNodeCurvePrimitiveLine')
    link(start,line.inputs['Start']); link(end.outputs[0],line.inputs['End'])
    # Shape the guide before branching so every side vine grows from its
    # current centerline. The envelope anchors both ends as Wander changes.
    count=n.new('ShaderNodeMath'); count.operation='DIVIDE'
    step=n.new('ShaderNodeValue'); driver(step.outputs[0],'ivy_step')
    link(length.outputs[0],count.inputs[0]); link(step.outputs[0],count.inputs[1])
    rounded=n.new('ShaderNodeMath'); rounded.operation='CEIL'
    link(count.outputs[0],rounded.inputs[0])
    plus_end=n.new('ShaderNodeMath'); plus_end.operation='ADD'
    link(rounded.outputs[0],plus_end.inputs[0]); plus_end.inputs[1].default_value=1
    budget=n.new('ShaderNodeValue'); driver(budget.outputs[0],'ivy_max_steps')
    capped=n.new('ShaderNodeMath'); capped.operation='MINIMUM'
    link(plus_end.outputs[0],capped.inputs[0]); link(budget.outputs[0],capped.inputs[1])
    count_two=n.new('ShaderNodeMath'); count_two.operation='MAXIMUM'
    link(capped.outputs[0],count_two.inputs[0]); count_two.inputs[1].default_value=2
    resample=n.new('GeometryNodeResampleCurve')
    link(line.outputs['Curve'],resample.inputs['Curve']); link(count_two.outputs[0],resample.inputs['Count'])
    lateral=n.new('ShaderNodeVectorMath'); lateral.operation='CROSS_PRODUCT'
    link(sample.outputs['Value'],lateral.inputs[0]); link(normalized.outputs[0],lateral.inputs[1])
    tangent_lateral=n.new('ShaderNodeVectorMath'); tangent_lateral.operation='NORMALIZE'
    link(lateral.outputs[0],tangent_lateral.inputs[0])
    factor=n.new('GeometryNodeSplineParameter')
    phase=n.new('ShaderNodeMath'); phase.operation='ADD'
    link(factor.outputs['Factor'],phase.inputs[0])
    driver(phase.inputs[1],'seed')
    noise=n.new('ShaderNodeTexNoise'); noise.noise_dimensions='1D'
    noise.inputs['Scale'].default_value=3.5
    link(phase.outputs[0],noise.inputs['W'])
    centered=n.new('ShaderNodeMath'); centered.operation='SUBTRACT'
    link(noise.outputs['Fac'],centered.inputs[0]); centered.inputs[1].default_value=.5
    envelope=n.new('ShaderNodeMath'); envelope.operation='SINE'
    pi_factor=n.new('ShaderNodeMath'); pi_factor.operation='MULTIPLY'
    link(factor.outputs['Factor'],pi_factor.inputs[0]); pi_factor.inputs[1].default_value=math.pi
    link(pi_factor.outputs[0],envelope.inputs[0])
    wander=n.new('ShaderNodeValue'); driver(wander.outputs[0],'ivy_wander')
    amplitude=n.new('ShaderNodeMath'); amplitude.operation='MULTIPLY'
    link(wander.outputs[0],amplitude.inputs[0]); link(length.outputs[0],amplitude.inputs[1])
    amount=n.new('ShaderNodeMath'); amount.operation='MULTIPLY'
    link(centered.outputs[0],amount.inputs[0]); link(envelope.outputs[0],amount.inputs[1])
    scaled=n.new('ShaderNodeMath'); scaled.operation='MULTIPLY'
    link(amount.outputs[0],scaled.inputs[0]); link(amplitude.outputs[0],scaled.inputs[1])
    offset=n.new('ShaderNodeVectorMath'); offset.operation='SCALE'
    link(tangent_lateral.outputs[0],offset.inputs[0]); link(scaled.outputs[0],offset.inputs['Scale'])
    shaped=n.new('GeometryNodeSetPosition')
    link(resample.outputs['Curve'],shaped.inputs['Geometry']); link(offset.outputs[0],shaped.inputs['Offset'])
    return shaped.outputs['Geometry']


def _ivy_surface_branches(settings,n,link,driver,main_curve,store):
    """Add evenly spaced side guides before surface projection."""
    def value(name):
        node=n.new('ShaderNodeValue'); driver(node.outputs[0],name)
        return node.outputs[0]
    def math_node(operation,a,b):
        node=n.new('ShaderNodeMath'); node.operation=operation
        for index,argument in enumerate((a,b)):
            if isinstance(argument,(int,float)): node.inputs[index].default_value=argument
            else: link(argument,node.inputs[index])
        return node.outputs[0]
    length=value('length')
    spacing=value('ivy_branch_spacing')
    limit=value('ivy_branches')
    count=math_node('MINIMUM',limit,math_node('FLOOR',math_node('DIVIDE',length,spacing),0))
    unit=n.new('GeometryNodeCurvePrimitiveLine')
    unit.inputs['Start'].default_value=(0,0,0)
    unit.inputs['End'].default_value=(1,0,0)
    duplicates=n.new('GeometryNodeDuplicateElements'); duplicates.domain='SPLINE'
    link(unit.outputs['Curve'],duplicates.inputs['Geometry'])
    link(count,duplicates.inputs['Amount'])
    branch_curve=store(duplicates.outputs['Geometry'],'lp_ivy_branch_index','INT',duplicates.outputs['Duplicate Index'],'CURVE')
    branch_index=n.new('GeometryNodeInputNamedAttribute'); branch_index.data_type='INT'
    branch_index.inputs['Name'].default_value='lp_ivy_branch_index'
    factor=math_node('MINIMUM',.95,math_node('DIVIDE',math_node('MULTIPLY',
        math_node('ADD',branch_index.outputs['Attribute'],1),spacing),length))
    sample=n.new('GeometryNodeSampleCurve')
    link(main_curve,sample.inputs['Curves']); link(factor,sample.inputs['Factor'])
    target=n.new('GeometryNodeObjectInfo')
    target.inputs['Object'].default_value=settings.controller
    target.transform_space='RELATIVE'
    nearest=n.new('GeometryNodeSampleNearestSurface'); nearest.data_type='FLOAT_VECTOR'
    link(target.outputs['Geometry'],nearest.inputs['Mesh'])
    normal=n.new('GeometryNodeInputNormal')
    link(normal.outputs['Normal'],nearest.inputs['Value'])
    link(sample.outputs['Position'],nearest.inputs['Sample Position'])
    sign=math_node('SUBTRACT',math_node('MULTIPLY',
        math_node('FLOORED_MODULO',branch_index.outputs['Attribute'],2),2),1)
    wander=value('ivy_wander')
    random_angle=n.new('FunctionNodeRandomValue'); random_angle.data_type='FLOAT'
    link(math_node('MULTIPLY',wander,-1),random_angle.inputs['Min'])
    link(wander,random_angle.inputs['Max'])
    link(branch_index.outputs['Attribute'],random_angle.inputs['ID'])
    driver(random_angle.inputs['Seed'],'seed',701)
    angle=math_node('ADD',math_node('MULTIPLY',sign,value('ivy_branch_angle')),
                    random_angle.outputs['Value'])
    rotation=n.new('FunctionNodeAxisAngleToRotation')
    link(nearest.outputs['Value'],rotation.inputs['Axis'])
    link(angle,rotation.inputs['Angle'])
    direction=n.new('FunctionNodeRotateVector')
    link(sample.outputs['Tangent'],direction.inputs['Vector'])
    link(rotation.outputs['Rotation'],direction.inputs['Rotation'])
    branch_length=math_node('MULTIPLY',length,value('ivy_branch_length'))
    t=n.new('GeometryNodeSplineParameter')
    travel=n.new('ShaderNodeVectorMath'); travel.operation='SCALE'
    link(direction.outputs['Vector'],travel.inputs[0])
    link(math_node('MULTIPLY',branch_length,t.outputs['Factor']),travel.inputs['Scale'])
    position=n.new('ShaderNodeVectorMath'); position.operation='ADD'
    link(sample.outputs['Position'],position.inputs[0]); link(travel.outputs[0],position.inputs[1])
    shaped=n.new('GeometryNodeSetPosition')
    link(branch_curve,shaped.inputs['Geometry']); link(position.outputs[0],shaped.inputs['Position'])
    no_branch=n.new('FunctionNodeInputInt'); no_branch.integer=-1
    main_curve=store(main_curve,'lp_ivy_branch_index','INT',no_branch.outputs[0],'CURVE')
    joined=n.new('GeometryNodeJoinGeometry')
    link(main_curve,joined.inputs[0]); link(shaped.outputs['Geometry'],joined.inputs[0])
    return joined.outputs['Geometry']


def _group(source,settings,slots,prototypes,materials,mode,tree_guide=None):
    arranged_mesh=mode in {'Surface','Volume'} and settings.kind in {'Tree','Foliage'} and settings.pattern in ARRANGED_PATH_PATTERNS
    arranged_path=settings.kind in {'Foliage','Tree'} and settings.pattern in ARRANGED_PATH_PATTERNS and (mode=='Path' or arranged_mesh)
    ivy_surface=settings.kind=='Ivy' and mode=='Surface'
    path_mode=mode=='Path' or ivy_surface or arranged_mesh
    group=bpy.data.node_groups.new('LP Live '+mode+' '+source.name,'GeometryNodeTree')
    group.is_modifier=True
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    n=group.nodes; link=group.links.new
    output=n.new('NodeGroupOutput')
    def driver(socket,property_name,offset=0):
        d=socket.driver_add('default_value').driver
        d.type='SCRIPTED' if offset else 'AVERAGE'
        variable=d.variables.new(); variable.name='value'
        variable.targets[0].id=source
        variable.targets[0].data_path='landscapy.'+property_name
        if offset: d.expression=f'value+{offset}'
    def number(op,a,b=None):
        node=n.new('ShaderNodeMath'); node.operation=op
        for index,value in enumerate((a,b)):
            if value is None: continue
            if isinstance(value,(float,int)): node.inputs[index].default_value=value
            else: link(value,node.inputs[index])
        return node.outputs[0]
    def random(kind,minimum,maximum,seed,id_field,seed_property=None,offset=0):
        node=n.new('FunctionNodeRandomValue'); node.data_type=kind
        node.inputs['Min'].default_value=minimum
        node.inputs['Max'].default_value=maximum
        node.inputs['Seed'].default_value=seed
        if seed_property: driver(node.inputs['Seed'],seed_property,offset)
        link(id_field,node.inputs['ID'])
        return node.outputs['Value']
    def store(geometry,name,kind,value,domain='POINT'):
        node=n.new('GeometryNodeStoreNamedAttribute'); node.data_type=kind
        node.domain=domain; node.inputs['Name'].default_value=name
        link(geometry,node.inputs['Geometry']); link(value,node.inputs['Value'])
        return node.outputs['Geometry']

    controller=n.new('GeometryNodeObjectInfo')
    controller.inputs['Object'].default_value=tree_guide or settings.controller
    controller.transform_space='RELATIVE'
    if mode in {'Surface','Volume'} and not ivy_surface:
        triangulate=n.new('GeometryNodeTriangulate')
        link(controller.outputs['Geometry'],triangulate.inputs['Mesh'])

    def mesh_points():
        """Scatter rachis anchors or individual cards from one mesh controller."""
        if mode=='Surface':
            scatter=n.new('GeometryNodeDistributePointsOnFaces')
            scatter.distribute_method='POISSON'
            link(triangulate.outputs['Mesh'],scatter.inputs['Mesh'])
            driver(scatter.inputs['Density Max'],'density')
            driver(scatter.inputs['Distance Min'],'spacing')
            driver(scatter.inputs['Seed'],'seed')
            if settings.mask:
                weight=n.new('GeometryNodeInputNamedAttribute'); weight.data_type='FLOAT'
                weight.inputs['Name'].default_value=settings.mask
                link(weight.outputs['Attribute'],scatter.inputs['Density Factor'])
            return scatter.outputs['Points'],scatter,None,None

        volume=n.new('GeometryNodeMeshToVolume')
        volume.inputs['Resolution Mode'].default_value='Amount'
        driver(volume.inputs['Voxel Amount'],'live_volume_grid_cells')
        link(controller.outputs['Geometry'],volume.inputs['Mesh'])
        random_points=n.new('GeometryNodeDistributePointsInVolume')
        random_points.inputs['Mode'].default_value='Random'
        link(volume.outputs['Volume'],random_points.inputs['Volume'])
        driver(random_points.inputs['Density'],'density')
        driver(random_points.inputs['Seed'],'seed')
        grid=n.new('GeometryNodeDistributePointsInVolume')
        grid.inputs['Mode'].default_value='Grid'
        link(volume.outputs['Volume'],grid.inputs['Volume'])
        bounds=n.new('GeometryNodeBoundBox')
        link(controller.outputs['Geometry'],bounds.inputs['Geometry'])
        extent=n.new('ShaderNodeVectorMath'); extent.operation='SUBTRACT'
        link(bounds.outputs['Max'],extent.inputs[0]); link(bounds.outputs['Min'],extent.inputs[1])
        diagonal=n.new('ShaderNodeVectorMath'); diagonal.operation='LENGTH'
        link(extent.outputs[0],diagonal.inputs[0])
        requested=n.new('ShaderNodeValue'); driver(requested.outputs[0],'spacing')
        grid_detail=n.new('ShaderNodeValue'); driver(grid_detail.outputs[0],'live_volume_grid_cells')
        effective=number('MAXIMUM',requested.outputs[0],number('MAXIMUM',.02,number('DIVIDE',diagonal.outputs['Value'],grid_detail.outputs[0])))
        grid_spacing=n.new('ShaderNodeCombineXYZ')
        for axis in ('X','Y','Z'): link(effective,grid_spacing.inputs[axis])
        link(grid_spacing.outputs[0],grid.inputs['Spacing'])
        density=n.new('ShaderNodeValue'); driver(density.outputs[0],'density')
        grid_rate=number('MINIMUM',1.,number('MULTIPLY',density.outputs[0],number('POWER',effective,3.)))
        volume_index=n.new('GeometryNodeInputIndex')
        mask=None
        if settings.mask:
            weight=n.new('GeometryNodeInputNamedAttribute'); weight.data_type='FLOAT'
            weight.inputs['Name'].default_value=settings.mask
            nearest=n.new('GeometryNodeSampleNearestSurface'); nearest.data_type='FLOAT'
            link(triangulate.outputs['Mesh'],nearest.inputs['Mesh'])
            link(weight.outputs['Attribute'],nearest.inputs['Value'])
            position=n.new('GeometryNodeInputPosition')
            link(position.outputs['Position'],nearest.inputs['Sample Position'])
            mask=nearest.outputs['Value']
        def thin_volume(geometry,rate,offset):
            chance=random('FLOAT',0.,1.,settings.seed+offset,volume_index.outputs['Index'],'seed',offset)
            probability=number('MULTIPLY',rate,mask) if mask else rate
            excess=n.new('FunctionNodeCompare'); excess.data_type='FLOAT'; excess.operation='GREATER_THAN'
            link(chance,excess.inputs[0]); link(probability,excess.inputs[1])
            delete=n.new('GeometryNodeDeleteGeometry'); delete.domain='POINT'; delete.mode='ALL'
            link(geometry,delete.inputs['Geometry']); link(excess.outputs[0],delete.inputs['Selection'])
            return delete.outputs['Geometry']
        random_geometry=thin_volume(random_points.outputs['Points'],number('ADD',1.,0.),912) if mask else random_points.outputs['Points']
        grid_geometry=thin_volume(grid.outputs['Points'],grid_rate,913)
        choose_grid=n.new('FunctionNodeCompare'); choose_grid.data_type='FLOAT'; choose_grid.operation='GREATER_THAN'
        link(requested.outputs[0],choose_grid.inputs[0]); choose_grid.inputs[1].default_value=.000001
        switch=n.new('GeometryNodeSwitch'); switch.input_type='GEOMETRY'
        link(choose_grid.outputs[0],switch.inputs['Switch'])
        link(random_geometry,switch.inputs['False']); link(grid_geometry,switch.inputs['True'])
        return switch.outputs[0],None,choose_grid,effective

    if arranged_mesh:
        frond_anchors,scatter,choose_grid,effective=mesh_points()
        anchor_index=n.new('GeometryNodeInputIndex')
        per_frond=n.new('ShaderNodeValue'); driver(per_frond.outputs[0],'count')
        if settings.pattern in PAIRED_PATH_PATTERNS: per_frond_count=number('MULTIPLY',per_frond.outputs[0],2.)
        elif settings.pattern=='Whorl':
            whorl=n.new('ShaderNodeValue'); driver(whorl.outputs[0],'frond_whorl')
            per_frond_count=number('MULTIPLY',per_frond.outputs[0],whorl.outputs[0])
        else: per_frond_count=per_frond.outputs[0]
        limit=n.new('ShaderNodeValue'); driver(limit.outputs[0],'limit')
        anchor_cap=number('MAXIMUM',1.,number('FLOOR',number('DIVIDE',limit.outputs[0],number('MAXIMUM',1.,per_frond_count))))
        over_cap=n.new('FunctionNodeCompare'); over_cap.data_type='INT'; over_cap.operation='GREATER_EQUAL'
        link(anchor_index.outputs['Index'],over_cap.inputs[0]); link(anchor_cap,over_cap.inputs[1])
        limited=n.new('GeometryNodeDeleteGeometry'); limited.domain='POINT'; limited.mode='ALL'
        link(frond_anchors,limited.inputs['Geometry']); link(over_cap.outputs[0],limited.inputs['Selection'])
        frond_anchors=limited.outputs['Geometry']
        if settings.kind=='Tree':
            from . import live_tree_fronds
            frond_anchors,tree_rotation,tree_distance=live_tree_fronds.attach_mesh_anchors(n,link,frond_anchors)
    if path_mode:
        if arranged_mesh:
            length=n.new('ShaderNodeValue'); driver(length.outputs[0],'length')
            endpoint=n.new('ShaderNodeCombineXYZ'); link(length.outputs[0],endpoint.inputs['Z'])
            rachis=n.new('GeometryNodeCurvePrimitiveLine')
            if settings.kind=='Tree': rachis.inputs['End'].default_value=(0,0,1)
            else: link(endpoint.outputs[0],rachis.inputs['End'])
            if settings.kind=='Tree': base=tree_rotation
            elif mode=='Surface': base= scatter.outputs['Rotation']
            else:
                axis=random('FLOAT_VECTOR',(-math.pi,)*3,(math.pi,)*3,
                            settings.rotation_seed+707,anchor_index.outputs['Index'],'rotation_seed',707)
                random_axis=n.new('FunctionNodeEulerToRotation')
                link(axis,random_axis.inputs['Euler'])
                random_direction=n.new('FunctionNodeRotateVector')
                random_direction.inputs['Vector'].default_value=(0,0,1)
                link(random_axis.outputs['Rotation'],random_direction.inputs['Rotation'])
                nearest=n.new('GeometryNodeSampleNearestSurface'); nearest.data_type='FLOAT_VECTOR'
                link(triangulate.outputs['Mesh'],nearest.inputs['Mesh'])
                normal=n.new('GeometryNodeInputNormal')
                link(normal.outputs['Normal'],nearest.inputs['Value'])
                anchor_position=n.new('GeometryNodeInputPosition')
                link(anchor_position.outputs['Position'],nearest.inputs['Sample Position'])
                alignment=n.new('ShaderNodeValue'); driver(alignment.outputs[0],'canopy_alignment')
                random_weight=n.new('ShaderNodeVectorMath'); random_weight.operation='SCALE'
                link(random_direction.outputs['Vector'],random_weight.inputs[0])
                link(number('SUBTRACT',1.,alignment.outputs[0]),random_weight.inputs['Scale'])
                outward_weight=n.new('ShaderNodeVectorMath'); outward_weight.operation='SCALE'
                link(nearest.outputs['Value'],outward_weight.inputs[0])
                link(alignment.outputs[0],outward_weight.inputs['Scale'])
                direction=n.new('ShaderNodeVectorMath'); direction.operation='ADD'
                link(random_weight.outputs[0],direction.inputs[0])
                link(outward_weight.outputs[0],direction.inputs[1])
                base_axis=n.new('FunctionNodeAlignRotationToVector'); base_axis.axis='Z'
                link(direction.outputs[0],base_axis.inputs['Vector'])
                base=base_axis.outputs['Rotation']
            tilt=random('FLOAT_VECTOR',(-settings.pitch,-settings.roll,-settings.yaw),
                        (settings.pitch,settings.roll,settings.yaw),settings.rotation_seed+808,
                        anchor_index.outputs['Index'],'rotation_seed',808)
            tilt_rotation=n.new('FunctionNodeEulerToRotation'); link(tilt,tilt_rotation.inputs['Euler'])
            orient=n.new('FunctionNodeRotateRotation'); orient.rotation_space='LOCAL'
            link(base,orient.inputs['Rotation']); link(tilt_rotation.outputs['Rotation'],orient.inputs['Rotate By'])
            make_rachis=n.new('GeometryNodeInstanceOnPoints')
            link(frond_anchors,make_rachis.inputs['Points'])
            link(rachis.outputs['Curve'],make_rachis.inputs['Instance'])
            link(orient.outputs['Rotation'],make_rachis.inputs['Rotation'])
            if settings.kind=='Tree':
                size=n.new('ShaderNodeCombineXYZ')
                size.inputs['X'].default_value=1.; size.inputs['Y'].default_value=1.
                link(tree_distance,size.inputs['Z'])
                link(size.outputs[0],make_rachis.inputs['Scale'])
            realize_rachis=n.new('GeometryNodeRealizeInstances')
            link(make_rachis.outputs['Instances'],realize_rachis.inputs['Geometry'])
            if settings.kind=='Tree':
                radius=n.new('GeometryNodeSetCurveRadius')
                link(realize_rachis.outputs['Geometry'],radius.inputs['Curve'])
                radius.inputs['Radius'].default_value=1.
                path_curve=radius.outputs['Curve']
            else: path_curve=realize_rachis.outputs['Geometry']
        else:
            if tree_guide:
                edge_curves=n.new('GeometryNodeMeshToCurve')
                edge_curves.name='Tree Branch Frond Guides'
                link(controller.outputs['Geometry'],edge_curves.inputs['Mesh'])
                guide_radius=n.new('GeometryNodeSetCurveRadius')
                guide_radius.name='Tree Frond Guide Radius'
                link(edge_curves.outputs['Curve'],guide_radius.inputs['Curve'])
                guide_radius.inputs['Radius'].default_value=1.
                path_curve=guide_radius.outputs['Curve']
            else:
                path_curve=_ivy_surface_seed(settings,n,link,driver) if ivy_surface else controller.outputs['Geometry']
        if ivy_surface:
            path_curve=_ivy_surface_branches(settings,n,link,driver,path_curve,store)
        spline_parameter=n.new('GeometryNodeSplineParameter')
        path_curve=store(path_curve,'lp_path_factor','FLOAT',spline_parameter.outputs['Factor'])
        if settings.kind=='Ivy' and (settings.target or ivy_surface):
            path_curve=_ivy_target_path(settings,n,link,path_curve,driver,store)
        if arranged_path:
            stem_resample=n.new('GeometryNodeResampleCurve')
            driver(stem_resample.inputs['Count'],'frond_segments',1)
            link(path_curve,stem_resample.inputs['Curve'])
            path_curve=store(stem_resample.outputs['Curve'],'lp_path_factor','FLOAT',spline_parameter.outputs['Factor'])
            tangent=n.new('GeometryNodeInputTangent')
            gravity=n.new('ShaderNodeVectorMath'); gravity.operation='SCALE'
            gravity.inputs[0].default_value=(0,0,1)
            gravity.inputs['Scale'].default_value=-1
            dot=n.new('ShaderNodeVectorMath'); dot.operation='DOT_PRODUCT'
            link(tangent.outputs['Tangent'],dot.inputs[0]); link(gravity.outputs[0],dot.inputs[1])
            along=n.new('ShaderNodeVectorMath'); along.operation='SCALE'
            link(tangent.outputs['Tangent'],along.inputs[0]); link(dot.outputs['Value'],along.inputs['Scale'])
            transverse=n.new('ShaderNodeVectorMath'); transverse.operation='SUBTRACT'
            link(gravity.outputs[0],transverse.inputs[0]); link(along.outputs[0],transverse.inputs[1])
            transverse_length=n.new('ShaderNodeVectorMath'); transverse_length.operation='LENGTH'
            link(transverse.outputs[0],transverse_length.inputs[0])
            normalized=n.new('ShaderNodeVectorMath'); normalized.operation='NORMALIZE'
            link(transverse.outputs[0],normalized.inputs[0])
            weight=number('MINIMUM',1.,number('DIVIDE',transverse_length.outputs['Value'],.35))
            fallback=n.new('ShaderNodeVectorMath'); fallback.operation='SCALE'
            fallback.inputs[0].default_value=(0,-1,0)
            link(number('SUBTRACT',1.,weight),fallback.inputs['Scale'])
            projected=n.new('ShaderNodeVectorMath'); projected.operation='SCALE'
            link(normalized.outputs[0],projected.inputs[0]); link(weight,projected.inputs['Scale'])
            blended=n.new('ShaderNodeVectorMath'); blended.operation='ADD'
            link(fallback.outputs[0],blended.inputs[0]); link(projected.outputs[0],blended.inputs[1])
            sag=n.new('ShaderNodeVectorMath'); sag.operation='NORMALIZE'
            link(blended.outputs[0],sag.inputs[0])
            droop=n.new('ShaderNodeValue'); driver(droop.outputs[0],'frond_droop')
            length=n.new('GeometryNodeSplineLength')
            amount=number('MULTIPLY',droop.outputs[0],number('MULTIPLY',length.outputs['Length'],number('POWER',spline_parameter.outputs['Factor'],2.)))
            offset=n.new('ShaderNodeVectorMath'); offset.operation='SCALE'
            link(sag.outputs[0],offset.inputs[0]); link(amount,offset.inputs['Scale'])
            bend=n.new('GeometryNodeSetPosition')
            link(path_curve,bend.inputs['Geometry']); link(offset.outputs[0],bend.inputs['Offset'])
            path_curve=bend.outputs['Geometry']
            tip=n.new('ShaderNodeValue'); driver(tip.outputs[0],'frond_stem_tip')
            radius=n.new('GeometryNodeInputRadius')
            stem_scale=number('MULTIPLY',radius.outputs['Radius'],number('SUBTRACT',1.,number('MULTIPLY',number('SUBTRACT',1.,tip.outputs[0]),spline_parameter.outputs['Factor'])))
        if settings.kind=='Ivy' or arranged_path:
            path_curve=store(path_curve,'lp_wind','FLOAT',number('POWER',spline_parameter.outputs['Factor'],2.))
        path_density=n.new('ShaderNodeValue'); driver(path_density.outputs[0],'density')
        if arranged_mesh:
            interval=number('DIVIDE',length.outputs[0],number('MAXIMUM',2.,per_frond.outputs[0]))
        else:
            path_spacing=n.new('ShaderNodeValue')
            driver(path_spacing.outputs[0],'ivy_leaf_spacing' if settings.kind=='Ivy' else 'spacing')
            interval=number('MAXIMUM',path_spacing.outputs[0],
                            number('DIVIDE',1.,number('MAXIMUM',.001,path_density.outputs[0])))
        spline_length=n.new('GeometryNodeSplineLength')
        station_count=number('ADD',number('FLOOR',number('DIVIDE',spline_length.outputs['Length'],interval)),1.)
        if arranged_path:
            max_stations=n.new('ShaderNodeValue'); driver(max_stations.outputs[0],'count')
            station_count=number('MINIMUM',station_count,max_stations.outputs[0])
            # One requested station still needs a base and a tip sample; the
            # bare petiole removes the base, leaving the intended leaf pair.
            station_count=number('MAXIMUM',2.,station_count)
        path_points=n.new('GeometryNodeCurveToPoints'); path_points.mode='COUNT'
        link(path_curve,path_points.inputs['Curve'])
        link(station_count,path_points.inputs['Count'])
        disabled=n.new('FunctionNodeCompare'); disabled.data_type='FLOAT'; disabled.operation='LESS_EQUAL'
        link(path_density.outputs[0],disabled.inputs[0]); disabled.inputs[1].default_value=0
        remove_zero=n.new('GeometryNodeDeleteGeometry'); remove_zero.domain='POINT'; remove_zero.mode='ALL'
        link(path_points.outputs['Points'],remove_zero.inputs['Geometry'])
        link(disabled.outputs[0],remove_zero.inputs['Selection'])
        scattered_points=remove_zero.outputs['Geometry']
        if arranged_path:
            factor=n.new('GeometryNodeInputNamedAttribute'); factor.data_type='FLOAT'
            factor.inputs['Name'].default_value='lp_path_factor'
            start=n.new('ShaderNodeValue'); driver(start.outputs[0],'frond_petiole')
            bare=n.new('FunctionNodeCompare'); bare.data_type='FLOAT'; bare.operation='LESS_THAN'
            link(factor.outputs['Attribute'],bare.inputs[0]); link(start.outputs[0],bare.inputs[1])
            trim=n.new('GeometryNodeDeleteGeometry'); trim.domain='POINT'; trim.mode='ALL'
            link(scattered_points,trim.inputs['Geometry']); link(bare.outputs[0],trim.inputs['Selection'])
            scattered_points=trim.outputs['Geometry']
    else:
        scattered_points,scatter,choose_grid,effective=mesh_points()
    index=n.new('GeometryNodeInputIndex')
    compare=n.new('FunctionNodeCompare'); compare.data_type='INT'; compare.operation='GREATER_EQUAL'
    driver(compare.inputs[1],'limit')
    link(index.outputs['Index'],compare.inputs[0])
    cap=n.new('GeometryNodeDeleteGeometry'); cap.domain='POINT'; cap.mode='ALL'
    link(scattered_points,cap.inputs['Geometry'])
    link(compare.outputs[0],cap.inputs['Selection'])
    points=cap.outputs['Geometry']
    if arranged_path:
        station_index=n.new('GeometryNodeInputIndex')
        points=store(points,'lp_frond_station','INT',station_index.outputs['Index'])
        zero_member=n.new('FunctionNodeInputInt')
        zero_member.integer=0
        points=store(points,'lp_frond_member','INT',zero_member.outputs[0])
        if settings.pattern in PAIRED_PATH_PATTERNS|{'Whorl'}:
            duplicate=n.new('GeometryNodeDuplicateElements'); duplicate.domain='POINT'
            link(points,duplicate.inputs['Geometry'])
            if settings.pattern=='Whorl': driver(duplicate.inputs['Amount'],'frond_whorl')
            else: duplicate.inputs['Amount'].default_value=2
            points=store(duplicate.outputs['Geometry'],'lp_frond_member','INT',duplicate.outputs['Duplicate Index'])
            final_index=n.new('GeometryNodeInputIndex')
            final_limit=n.new('FunctionNodeCompare'); final_limit.data_type='INT'; final_limit.operation='GREATER_EQUAL'
            link(final_index.outputs['Index'],final_limit.inputs[0]); driver(final_limit.inputs[1],'limit')
            final_cap=n.new('GeometryNodeDeleteGeometry'); final_cap.domain='POINT'; final_cap.mode='ALL'
            link(points,final_cap.inputs['Geometry']); link(final_limit.outputs[0],final_cap.inputs['Selection'])
            points=final_cap.outputs['Geometry']
    point_id=n.new('GeometryNodeInputIndex')
    ids=point_id.outputs['Index']
    if mode=='Volume':
        reported_spacing=n.new('GeometryNodeSwitch'); reported_spacing.input_type='FLOAT'
        link(choose_grid.outputs[0],reported_spacing.inputs['Switch'])
        reported_spacing.inputs['False'].default_value=0
        link(effective,reported_spacing.inputs['True'])
        points=store(points,'lp_distribution_spacing','FLOAT',reported_spacing.outputs[0])
    elif path_mode:
        points=store(points,'lp_distribution_spacing','FLOAT',interval)
    if settings.jitter:
        displacement=random('FLOAT_VECTOR',(-settings.jitter,)*3,(settings.jitter,)*3,settings.seed+101,ids,'seed',101)
        move=n.new('GeometryNodeSetPosition')
        link(points,move.inputs['Geometry']); link(displacement,move.inputs['Offset'])
        points=move.outputs['Geometry']
    points=store(points,'lp_card_source_id','INT',ids)
    anchor_position=n.new('GeometryNodeInputPosition')
    points=store(points,'lp_anchor','FLOAT_VECTOR',anchor_position.outputs['Position'])
    stable_id=n.new('GeometryNodeInputNamedAttribute'); stable_id.data_type='INT'
    stable_id.inputs['Name'].default_value='lp_card_source_id'
    ids=stable_id.outputs['Attribute']
    if mode=='Volume' and not arranged_mesh:
        directions=random('FLOAT_VECTOR',(-math.pi,)*3,(math.pi,)*3,settings.rotation_seed+303,ids,'rotation_seed',303)
        direction_euler=n.new('FunctionNodeEulerToRotation')
        link(directions,direction_euler.inputs['Euler'])
        base_rotation=direction_euler.outputs['Rotation']
    elif mode=='Surface' and not ivy_surface and not arranged_mesh:
        base_rotation=scatter.outputs['Rotation']
    else:
        base_rotation=path_points.outputs['Rotation']
        if settings.kind=='Ivy' and (settings.target or ivy_surface):
            surface_normal=n.new('GeometryNodeInputNamedAttribute'); surface_normal.data_type='FLOAT_VECTOR'
            surface_normal.inputs['Name'].default_value='lp_surface_normal'
            inward=n.new('ShaderNodeVectorMath'); inward.operation='SCALE'
            link(surface_normal.outputs['Attribute'],inward.inputs[0]); inward.inputs['Scale'].default_value=-1
            surface_rotation=n.new('FunctionNodeAxesToRotation')
            surface_rotation.primary_axis='Z'; surface_rotation.secondary_axis='Y'
            link(path_points.outputs['Tangent'],surface_rotation.inputs['Primary Axis'])
            link(inward.outputs[0],surface_rotation.inputs['Secondary Axis'])
            base_rotation=surface_rotation.outputs['Rotation']
    
    selection=random('FLOAT',0.,1.,settings.seed+717,ids,'seed',717)
    ratio=n.new('ShaderNodeValue'); ratio.name='Preview Ratio'
    ratio.outputs[0].default_value=1. if settings.ornaments_enabled else settings.preview_ratio if settings.preview_enabled else 1.
    over=n.new('FunctionNodeCompare'); over.data_type='FLOAT'; over.operation='GREATER_THAN'
    link(selection,over.inputs[0]); link(ratio.outputs[0],over.inputs[1])
    viewport=n.new('GeometryNodeIsViewport')
    viewport_only=n.new('FunctionNodeBooleanMath'); viewport_only.operation='AND'
    link(over.outputs[0],viewport_only.inputs[0]); link(viewport.outputs[0],viewport_only.inputs[1])
    thin=n.new('GeometryNodeDeleteGeometry'); thin.domain='POINT'; thin.mode='ALL'
    link(points,thin.inputs['Geometry']); link(viewport_only.outputs[0],thin.inputs['Selection'])
    points=thin.outputs['Geometry']

    total=sum(slot.weight for slot in slots)
    texture=random('FLOAT',0.,total,settings.texture_seed,ids,'texture_seed')
    chosen=None
    for slot_index in reversed(range(len(slots)-1)):
        threshold=sum(slot.weight for slot in slots[:slot_index+1])
        less=n.new('FunctionNodeCompare'); less.data_type='FLOAT'; less.operation='LESS_THAN'
        link(texture,less.inputs[0]); less.inputs[1].default_value=threshold
        switch=n.new('GeometryNodeSwitch'); switch.input_type='INT'
        link(less.outputs[0],switch.inputs['Switch'])
        switch.inputs['True'].default_value=slot_index
        if chosen is None: switch.inputs['False'].default_value=len(slots)-1
        else: link(chosen,switch.inputs['False'])
        chosen=switch.outputs[0]
    if chosen is None:
        constant=n.new('FunctionNodeInputInt'); constant.integer=0
        chosen=constant.outputs[0]
    points=store(points,'lp_template','INT',chosen)

    base_hue,base_saturation,base_value=colorsys.rgb_to_hsv(*settings.color)
    hue=random('FLOAT',settings.hue_min,settings.hue_max,settings.color_seed,ids,'color_seed')
    saturation=random('FLOAT',settings.saturation_min,settings.saturation_max,settings.color_seed+101,ids,'color_seed',101)
    value=random('FLOAT',settings.value_min,settings.value_max,settings.color_seed+202,ids,'color_seed',202)
    tint=random('FLOAT_VECTOR',tuple(settings.tint_min),tuple(settings.tint_max),settings.color_seed+303,ids,'color_seed',303)
    wrap=number('FLOORED_MODULO',number('ADD',base_hue,hue),1.)
    sat=number('MINIMUM',1.,number('MULTIPLY',base_saturation,saturation))
    val=number('MINIMUM',1.,number('MULTIPLY',base_value,value))
    hsv=n.new('FunctionNodeCombineColor'); hsv.mode='HSV'
    link(wrap,hsv.inputs[0]); link(sat,hsv.inputs[1]); link(val,hsv.inputs[2])
    multiply=n.new('ShaderNodeVectorMath'); multiply.operation='MULTIPLY'
    link(hsv.outputs['Color'],multiply.inputs[0]); link(tint,multiply.inputs[1])
    points=store(points,'lp_color','FLOAT_COLOR',multiply.outputs[0])
    opacity=random('FLOAT',settings.opacity_min,settings.opacity_max,settings.color_seed+404,ids,'color_seed',404)
    points=store(points,'lp_opacity','FLOAT',opacity)
    card_phase=random('FLOAT',0.,math.tau,settings.seed+505,ids,'seed',505)
    points=store(points,'lp_card_phase','FLOAT',card_phase)
    # Quantize the rest positions so neighboring cards move as a loose clump.
    # The higher-frequency card phase remains independent of this cell ID.
    cell_size=max(.2,settings.cluster_radius*2)
    phase_position=n.new('GeometryNodeInputPosition')
    phase_axes=n.new('ShaderNodeSeparateXYZ'); link(phase_position.outputs['Position'],phase_axes.inputs[0])
    cell_id=number('ADD',number('ADD',
        number('MULTIPLY',number('FLOOR',number('DIVIDE',phase_axes.outputs['X'],cell_size)),157),
        number('MULTIPLY',number('FLOOR',number('DIVIDE',phase_axes.outputs['Y'],cell_size)),263)),
        number('MULTIPLY',number('FLOOR',number('DIVIDE',phase_axes.outputs['Z'],cell_size)),379))
    cluster_phase=random('FLOAT',0.,math.tau,settings.seed+606,cell_id,'seed',606)
    points=store(points,'lp_cluster_phase','FLOAT',cluster_phase)

    yaw=random('FLOAT',-settings.yaw,settings.yaw,settings.rotation_seed,ids,'rotation_seed')
    pitch=random('FLOAT',-settings.pitch,settings.pitch,settings.rotation_seed+101,ids,'rotation_seed',101)
    roll=random('FLOAT',-settings.roll,settings.roll,settings.rotation_seed+202,ids,'rotation_seed',202)
    rotation=n.new('ShaderNodeCombineXYZ')
    link(pitch,rotation.inputs['X']); link(roll,rotation.inputs['Y']); link(yaw,rotation.inputs['Z'])
    euler=n.new('FunctionNodeEulerToRotation'); link(rotation.outputs[0],euler.inputs['Euler'])
    orient=n.new('FunctionNodeRotateRotation')
    if settings.kind=='Ivy' and (settings.target or ivy_surface): orient.rotation_space='LOCAL'
    link(base_rotation,orient.inputs['Rotation'])
    link(euler.outputs['Rotation'],orient.inputs['Rotate By'])
    card_rotation=orient.outputs['Rotation']
    if settings.kind=='Ivy':
        parity=number('FLOORED_MODULO',ids,2.)
        spread_amount=n.new('ShaderNodeValue'); driver(spread_amount.outputs[0],'ivy_leaf_spread')
        side_angle=number('MULTIPLY',number('SUBTRACT',number('MULTIPLY',parity,2.),1.),spread_amount.outputs[0])
        side_euler=n.new('ShaderNodeCombineXYZ')
        link(side_angle,side_euler.inputs['Y'])
        side_rotation=n.new('FunctionNodeEulerToRotation')
        link(side_euler.outputs[0],side_rotation.inputs['Euler'])
        spread=n.new('FunctionNodeRotateRotation')
        if settings.target or ivy_surface: spread.rotation_space='LOCAL'
        link(card_rotation,spread.inputs['Rotation'])
        link(side_rotation.outputs['Rotation'],spread.inputs['Rotate By'])
        card_rotation=spread.outputs['Rotation']
    elif arranged_path:
        station=n.new('GeometryNodeInputNamedAttribute'); station.data_type='INT'
        station.inputs['Name'].default_value='lp_frond_station'
        member=n.new('GeometryNodeInputNamedAttribute'); member.data_type='INT'
        member.inputs['Name'].default_value='lp_frond_member'
        if settings.pattern in PAIRED_PATH_PATTERNS:
            side=number('SUBTRACT',number('MULTIPLY',member.outputs['Attribute'],2.),1.)
            spin=0.
        elif settings.pattern=='Alternate':
            side=number('SUBTRACT',number('MULTIPLY',number('FLOORED_MODULO',station.outputs['Attribute'],2.),2.),1.)
            spin=0.
        elif settings.pattern=='Spiral':
            side=1.
            spin=number('MULTIPLY',station.outputs['Attribute'],2.399963229728653)
        else:
            side=1.
            members=n.new('ShaderNodeValue'); driver(members.outputs[0],'frond_whorl')
            spin=number('MULTIPLY',member.outputs['Attribute'],number('DIVIDE',math.tau,members.outputs[0]))
        if spin!=0.:
            spin_euler=n.new('ShaderNodeCombineXYZ'); link(spin,spin_euler.inputs['Z'])
            spin_rotation=n.new('FunctionNodeEulerToRotation'); link(spin_euler.outputs[0],spin_rotation.inputs['Euler'])
            rotate=n.new('FunctionNodeRotateRotation')
            link(card_rotation,rotate.inputs['Rotation']); link(spin_rotation.outputs['Rotation'],rotate.inputs['Rotate By'])
            card_rotation=rotate.outputs['Rotation']
        sweep=n.new('ShaderNodeValue'); driver(sweep.outputs[0],'frond_angle')
        side_angle=number('MULTIPLY',side,number('SUBTRACT',math.pi*.5,sweep.outputs[0]))
        droop=n.new('ShaderNodeValue'); driver(droop.outputs[0],'frond_leaf_droop')
        leaf_euler=n.new('ShaderNodeCombineXYZ')
        fold=number('ADD',droop.outputs[0],math.atan(.42)) if settings.pattern=='Palm' else droop.outputs[0]
        link(fold,leaf_euler.inputs['X']); link(side_angle,leaf_euler.inputs['Y'])
        leaf_rotation=n.new('FunctionNodeEulerToRotation'); link(leaf_euler.outputs[0],leaf_rotation.inputs['Euler'])
        spread=n.new('FunctionNodeRotateRotation')
        link(card_rotation,spread.inputs['Rotation']); link(leaf_rotation.outputs['Rotation'],spread.inputs['Rotate By'])
        card_rotation=spread.outputs['Rotation']
    uniform=random('FLOAT',settings.size_min,settings.size_max,settings.size_seed,ids,'size_seed')
    axis=random('FLOAT_VECTOR',tuple(settings.axis_min),tuple(settings.axis_max),settings.size_seed+101,ids,'size_seed',101)
    axis_scale=n.new('ShaderNodeVectorMath'); axis_scale.operation='MULTIPLY'
    link(axis,axis_scale.inputs[0]); axis_scale.inputs[1].default_value=settings.scale_axes
    scale=n.new('ShaderNodeVectorMath'); scale.operation='SCALE'
    link(axis_scale.outputs[0],scale.inputs[0]); link(uniform,scale.inputs['Scale'])
    card_scale=scale.outputs[0]
    if settings.kind=='Ivy':
        leaf_size=n.new('ShaderNodeValue'); driver(leaf_size.outputs[0],'ivy_leaf_size')
        sized=n.new('ShaderNodeVectorMath'); sized.operation='SCALE'
        link(card_scale,sized.inputs[0])
        link(number('DIVIDE',leaf_size.outputs[0],.45),sized.inputs['Scale'])
        card_scale=sized.outputs[0]
    elif arranged_path:
        width=n.new('ShaderNodeValue'); driver(width.outputs[0],'frond_leaf_width')
        length=n.new('ShaderNodeValue'); driver(length.outputs[0],'frond_width')
        factor=n.new('GeometryNodeInputNamedAttribute'); factor.data_type='FLOAT'
        factor.inputs['Name'].default_value='lp_path_factor'
        span=1.
        if settings.pattern=='Palm':
            petiole=n.new('ShaderNodeValue'); driver(petiole.outputs[0],'frond_petiole')
            progress=number('DIVIDE',number('SUBTRACT',factor.outputs['Attribute'],petiole.outputs[0]),
                            number('SUBTRACT',1.,petiole.outputs[0]))
            progress=number('MINIMUM',1.,number('MAXIMUM',0.,progress))
            curve=number('POWER',number('MAXIMUM',0.,number('SINE',number('MULTIPLY',math.pi,progress))),.72)
            span=number('ADD',.28,number('MULTIPLY',.72,curve))
        proportions=n.new('ShaderNodeCombineXYZ')
        link(number('DIVIDE',width.outputs[0],.45),proportions.inputs['X'])
        proportions.inputs['Y'].default_value=1.
        link(number('MULTIPLY',number('DIVIDE',length.outputs[0],.9),span),proportions.inputs['Z'])
        shaped=n.new('ShaderNodeVectorMath'); shaped.operation='MULTIPLY'
        link(card_scale,shaped.inputs[0]); link(proportions.outputs[0],shaped.inputs[1])
        taper=n.new('ShaderNodeValue'); driver(taper.outputs[0],'frond_taper')
        retained=number('MAXIMUM',.04,number('SUBTRACT',1.,number('MULTIPLY',taper.outputs[0],factor.outputs['Attribute'])))
        narrowed=n.new('ShaderNodeVectorMath'); narrowed.operation='SCALE'
        link(shaped.outputs[0],narrowed.inputs[0]); link(retained,narrowed.inputs['Scale'])
        card_scale=narrowed.outputs[0]
    if settings.random_card_shape:
        points=store(points,'lp_live_scale','FLOAT_VECTOR',card_scale)
        bend=random('FLOAT',settings.bend_min,settings.bend_max,settings.shape_seed,ids,'shape_seed')
        valley=random('FLOAT',settings.valley_min,settings.valley_max,settings.shape_seed+101,ids,'shape_seed',101)
        points=store(points,'lp_live_bend','FLOAT',bend)
        points=store(points,'lp_live_valley','FLOAT',valley)
    template=n.new('GeometryNodeInputNamedAttribute'); template.data_type='INT'
    template.inputs['Name'].default_value='lp_template'
    joined=n.new('GeometryNodeJoinGeometry')
    for slot_index,(slot,prototype) in enumerate(zip(slots,prototypes)):
        match=n.new('FunctionNodeCompare'); match.data_type='INT'; match.operation='EQUAL'
        match.inputs[1].default_value=slot_index
        link(template.outputs['Attribute'],match.inputs[0])
        separate=n.new('GeometryNodeSeparateGeometry'); separate.domain='POINT'
        link(points,separate.inputs['Geometry']); link(match.outputs[0],separate.inputs['Selection'])
        info=n.new('GeometryNodeObjectInfo'); info.inputs['Object'].default_value=prototype
        instance=n.new('GeometryNodeInstanceOnPoints')
        link(info.outputs['Geometry'],instance.inputs['Instance'])
        rotate=n.new('FunctionNodeRotateRotation')
        link(card_rotation,rotate.inputs['Rotation'])
        rotate.inputs['Rotate By'].default_value=(0,0,slot.rotation)
        selected=separate.outputs['Selection']
        if settings.random_card_shape:
            depth_direction=n.new('FunctionNodeRotateVector')
            depth_direction.inputs['Vector'].default_value=(0,1,0)
            link(rotate.outputs['Rotation'],depth_direction.inputs['Rotation'])
            selected=store(selected,'lp_live_depth_direction','FLOAT_VECTOR',depth_direction.outputs['Vector'])
        link(rotate.outputs['Rotation'],instance.inputs['Rotation'])
        link(card_scale,instance.inputs['Scale'])
        link(selected,instance.inputs['Points'])
        link(instance.outputs['Instances'],joined.inputs[0])
    realize=n.new('GeometryNodeRealizeInstances')
    link(joined.outputs[0],realize.inputs['Geometry'])
    geometry=realize.outputs['Geometry']
    if settings.random_card_shape:
        def attribute(name,kind):
            node=n.new('GeometryNodeInputNamedAttribute'); node.data_type=kind
            node.inputs['Name'].default_value=name
            return node.outputs['Attribute']
        u=attribute('lp_card_u','FLOAT'); v=attribute('lp_card_v','FLOAT')
        z=attribute('lp_card_local_z','FLOAT'); card_size=attribute('lp_card_size','FLOAT')
        bend=attribute('lp_live_bend','FLOAT'); valley=attribute('lp_live_valley','FLOAT')
        scales=attribute('lp_live_scale','FLOAT_VECTOR')
        separate_scale=n.new('ShaderNodeSeparateXYZ'); link(scales,separate_scale.inputs[0])
        local_z=number('MULTIPLY',z,separate_scale.outputs['Z'])
        bend_depth=number('MULTIPLY',bend,number('MULTIPLY',local_z,local_z))
        peak=number('MULTIPLY',number('SINE',number('MULTIPLY',u,math.pi)),
                    number('SINE',number('MULTIPLY',v,math.pi)))
        valley_depth=number('MULTIPLY',valley,number('MULTIPLY',peak,card_size))
        depth=number('SUBTRACT',bend_depth,valley_depth if settings.card=='Valley' else 0.)
        depth=number('MULTIPLY',depth,separate_scale.outputs['Y'])
        offset=n.new('ShaderNodeVectorMath'); offset.operation='SCALE'
        link(attribute('lp_live_depth_direction','FLOAT_VECTOR'),offset.inputs[0])
        link(depth,offset.inputs['Scale'])
        shape=n.new('GeometryNodeSetPosition')
        link(geometry,shape.inputs['Geometry']); link(offset.outputs[0],shape.inputs['Offset'])
        geometry=shape.outputs['Geometry']
    if settings.kind=='Ivy' or arranged_path:
        path_factor=n.new('GeometryNodeInputNamedAttribute'); path_factor.data_type='FLOAT'
        path_factor.inputs['Name'].default_value='lp_path_factor'
        geometry=store(geometry,'lp_wind','FLOAT',number('POWER',path_factor.outputs['Attribute'],2.))
        profile=n.new('GeometryNodeCurvePrimitiveCircle')
        profile.name='Live Path Stem Profile'
        driver(profile.inputs['Resolution'],'ivy_vine_sides' if settings.kind=='Ivy' else 'frond_stem_sides')
        radius=n.new('ShaderNodeValue'); driver(radius.outputs[0],'ivy_radius' if settings.kind=='Ivy' else 'frond_stem_radius')
        link(radius.outputs[0],profile.inputs['Radius'])
        tube=n.new('GeometryNodeCurveToMesh')
        link(path_curve,tube.inputs['Curve'])
        link(profile.outputs['Curve'],tube.inputs['Profile Curve'])
        if arranged_path: link(stem_scale,tube.inputs['Scale'])
        vine_material=n.new('GeometryNodeSetMaterial')
        vine_material.inputs['Material'].default_value=materials[0]
        link(tube.outputs['Mesh'],vine_material.inputs['Geometry'])
        negative_id=n.new('FunctionNodeInputInt'); negative_id.integer=-1
        solid=store(vine_material.outputs['Geometry'],'lp_card_source_id','INT',negative_id.outputs[0])
        joined_solid=n.new('GeometryNodeJoinGeometry')
        link(geometry,joined_solid.inputs[0]); link(solid,joined_solid.inputs[0])
        geometry=joined_solid.outputs['Geometry']
    card_id=n.new('GeometryNodeInputNamedAttribute'); card_id.data_type='INT'
    card_id.inputs['Name'].default_value='lp_card_source_id'
    faces=store(geometry,'lp_card_id','INT',card_id.outputs['Attribute'],'FACE')
    if settings.kind=='Tree':
        source_mesh=n.new('NodeGroupInput')
        combined=n.new('GeometryNodeJoinGeometry')
        link(source_mesh.outputs['Geometry'],combined.inputs[0])
        link(faces,combined.inputs[0])
        link(combined.outputs['Geometry'],output.inputs['Geometry'])
    else:
        link(faces,output.inputs['Geometry'])
    return group


def path_stem_snapshot(source,ratio):
    """Realize a live Ivy or arranged frond LOD without changing its source graph."""
    modifier=instance_cards.modifier(source)
    settings=source.landscapy
    arranged=settings.kind in {'Foliage','Tree'} and settings.pattern in ARRANGED_PATH_PATTERNS
    valid_modes={'Path','Surface'} if settings.kind=='Ivy' else {'TreePath','TreeSurface','TreeVolume'} if settings.kind=='Tree' else {'Path','Surface','Volume'}
    if not modifier or source.get('lp_live_mode') not in valid_modes or not (settings.kind=='Ivy' or arranged):
        raise ValueError('Path stem snapshot requires live Ivy or arranged Foliage')
    original=modifier.node_group
    group=original.copy()
    sides=max(3,round((settings.ivy_vine_sides if settings.kind=='Ivy' else settings.frond_stem_sides)*ratio))
    try:
        profile=group.nodes.get('Live Path Stem Profile')
        if not profile: raise ValueError('Live Path has no stem profile node')
        profile.inputs['Resolution'].driver_remove('default_value')
        profile.inputs['Resolution'].default_value=sides
        modifier.node_group=group
        return instance_cards.full_mesh(source),sides
    finally:
        modifier.node_group=original
        if group.users==0: bpy.data.node_groups.remove(group)


def commit(source,settings,slots,materials):
    mode=supported(settings)
    banana=settings.kind=='Foliage' and settings.pattern=='Banana' and mode in {'Path','Surface','Volume'}
    old_mesh=source.data
    mesh=bpy.data.meshes.new(source.name+' • Live '+mode+' Source')
    for material in materials: mesh.materials.append(material)
    objects_before=set(bpy.data.objects)
    groups_before=set(bpy.data.node_groups)
    prototypes=[]
    source.data=mesh
    try:
        if banana:
            from . import live_banana
            group=live_banana.group(source,settings,slots,materials,mode)
        else:
            prototypes=[_prototype(source,index,slot,materials[index+1],settings)
                        for index,slot in enumerate(slots)]
            group=_group(source,settings,slots,prototypes,materials,mode)
    except BaseException:
        source.data=old_mesh
        for created in set(bpy.data.node_groups)-groups_before:
            if created.users==0: bpy.data.node_groups.remove(created)
        for created in set(bpy.data.objects)-objects_before:
            if created.users==0:
                data=created.data
                bpy.data.objects.remove(created,do_unlink=True)
                if data and data.users==0: bpy.data.meshes.remove(data)
        if mesh.users==0: bpy.data.meshes.remove(mesh)
        raise
    instance_cards.clear(source)
    old_wind=source.modifiers.get('Landscapy Wind')
    if old_wind:
        wind_group=old_wind.node_group
        source.modifiers.remove(old_wind)
        if wind_group and wind_group.users==0: bpy.data.node_groups.remove(wind_group)
    modifier=source.modifiers.new(instance_cards.NAME,'NODES')
    modifier.node_group=group
    source['lp_live_mode']=mode
    if old_mesh and old_mesh.users==0: bpy.data.meshes.remove(old_mesh)
