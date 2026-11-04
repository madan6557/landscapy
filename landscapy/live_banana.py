"""UV-mapped banana blades on live Curve, Surface, or Volume rachises."""
import colorsys
import math
import bpy
from . import instance_cards, live_mesh_scatter


def group(source,settings,slots,materials,mode='Path',tree_guide=None):
    graph=bpy.data.node_groups.new('LP Live Banana '+source.name,'GeometryNodeTree')
    graph.is_modifier=True
    graph.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    graph.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=graph.nodes
    link=graph.links.new

    def driver(socket,property_name,offset=0):
        curve=socket.driver_add('default_value').driver
        curve.type='SCRIPTED' if offset else 'AVERAGE'
        variable=curve.variables.new(); variable.name='value'
        variable.targets[0].id=source
        variable.targets[0].data_path='landscapy.'+property_name
        if offset: curve.expression=f'value+{offset}'

    def value(property_name):
        node=nodes.new('ShaderNodeValue')
        driver(node.outputs[0],property_name)
        return node.outputs[0]

    def number(operation,a,b=None):
        node=nodes.new('ShaderNodeMath'); node.operation=operation
        for index,argument in enumerate((a,b)):
            if argument is None: continue
            if isinstance(argument,(int,float)): node.inputs[index].default_value=argument
            else: link(argument,node.inputs[index])
        return node.outputs[0]

    def named(name,kind):
        node=nodes.new('GeometryNodeInputNamedAttribute'); node.data_type=kind
        node.inputs['Name'].default_value=name
        return node.outputs['Attribute']

    def store(geometry,name,kind,value,domain='POINT'):
        node=nodes.new('GeometryNodeStoreNamedAttribute')
        node.data_type=kind; node.domain=domain
        node.inputs['Name'].default_value=name
        link(geometry,node.inputs['Geometry'])
        if isinstance(value,(int,float,bool)): node.inputs['Value'].default_value=value
        else: link(value,node.inputs['Value'])
        return node.outputs['Geometry']

    def random(kind,minimum,maximum,id_field,seed_property,offset=0):
        node=nodes.new('FunctionNodeRandomValue'); node.data_type=kind
        node.inputs['Min'].default_value=minimum
        node.inputs['Max'].default_value=maximum
        driver(node.inputs['Seed'],seed_property,offset)
        link(id_field,node.inputs['ID'])
        return node.outputs['Value']

    info=nodes.new('GeometryNodeObjectInfo')
    info.inputs['Object'].default_value=tree_guide or settings.controller
    info.transform_space='RELATIVE'
    if mode=='Path':
        if tree_guide:
            edge_curves=nodes.new('GeometryNodeMeshToCurve')
            link(info.outputs['Geometry'],edge_curves.inputs['Mesh'])
            set_radius=nodes.new('GeometryNodeSetCurveRadius')
            link(edge_curves.outputs['Curve'],set_radius.inputs['Curve'])
            set_radius.inputs['Radius'].default_value=1.
            raw_path=set_radius.outputs['Curve']
        else: raw_path=info.outputs['Geometry']
    else:
        triangulate=nodes.new('GeometryNodeTriangulate')
        link(info.outputs['Geometry'],triangulate.inputs['Mesh'])
        anchors,scatter,_,_=live_mesh_scatter.points(
            nodes,link,driver,number,settings,mode,
            info.outputs['Geometry'],triangulate.outputs['Mesh'])
        anchor_index=nodes.new('GeometryNodeInputIndex')
        over_limit=nodes.new('FunctionNodeCompare'); over_limit.data_type='INT'
        over_limit.operation='GREATER_EQUAL'
        link(anchor_index.outputs['Index'],over_limit.inputs[0])
        driver(over_limit.inputs[1],'limit')
        cap_anchors=nodes.new('GeometryNodeDeleteGeometry')
        cap_anchors.domain='POINT'; cap_anchors.mode='ALL'
        link(anchors,cap_anchors.inputs['Geometry'])
        link(over_limit.outputs[0],cap_anchors.inputs['Selection'])
        anchors=cap_anchors.outputs['Geometry']
        if settings.kind=='Tree':
            from . import live_tree_fronds
            anchors,tree_rotation,tree_distance=live_tree_fronds.attach_mesh_anchors(nodes,link,anchors)
        line=nodes.new('GeometryNodeCurvePrimitiveLine')
        endpoint=nodes.new('ShaderNodeCombineXYZ')
        link(value('length'),endpoint.inputs['Z'])
        if settings.kind=='Tree': line.inputs['End'].default_value=(0,0,1)
        else: link(endpoint.outputs[0],line.inputs['End'])
        if settings.kind=='Tree': base=tree_rotation
        elif mode=='Surface': base=scatter.outputs['Rotation']
        else:
            position=nodes.new('GeometryNodeInputPosition')
            def random_field(kind,minimum,maximum,seed,id_field,seed_property,offset=0):
                return random(kind,minimum,maximum,id_field,seed_property,offset)
            base=live_mesh_scatter.volume_rotation(
                nodes,link,driver,number,random_field,settings,
                anchor_index.outputs['Index'],triangulate.outputs['Mesh'],
                position.outputs['Position'])
        tilt=random('FLOAT_VECTOR',(-settings.pitch,-settings.roll,-settings.yaw),
                    (settings.pitch,settings.roll,settings.yaw),
                    anchor_index.outputs['Index'],'rotation_seed',808)
        tilt_rotation=nodes.new('FunctionNodeEulerToRotation')
        link(tilt,tilt_rotation.inputs['Euler'])
        orientation=nodes.new('FunctionNodeRotateRotation')
        orientation.rotation_space='LOCAL'
        link(base,orientation.inputs['Rotation'])
        link(tilt_rotation.outputs['Rotation'],orientation.inputs['Rotate By'])
        instances=nodes.new('GeometryNodeInstanceOnPoints')
        link(anchors,instances.inputs['Points'])
        link(line.outputs['Curve'],instances.inputs['Instance'])
        link(orientation.outputs['Rotation'],instances.inputs['Rotation'])
        if settings.kind=='Tree':
            scale=nodes.new('ShaderNodeCombineXYZ')
            scale.inputs['X'].default_value=1.; scale.inputs['Y'].default_value=1.
            link(tree_distance,scale.inputs['Z'])
            link(scale.outputs[0],instances.inputs['Scale'])
        realize=nodes.new('GeometryNodeRealizeInstances')
        link(instances.outputs['Instances'],realize.inputs['Geometry'])
        # Primitive line splines have zero radius after instancing in Blender
        # 5.2. Give generated rachises a real radius before Curve to Mesh.
        set_radius=nodes.new('GeometryNodeSetCurveRadius')
        link(realize.outputs['Geometry'],set_radius.inputs['Curve'])
        set_radius.inputs['Radius'].default_value=1.
        raw_path=set_radius.outputs['Curve']
    index=nodes.new('GeometryNodeInputIndex')
    path=store(raw_path,'lp_spline_id','INT',index.outputs['Index'],'CURVE')
    density=value('density')
    disabled=nodes.new('FunctionNodeCompare'); disabled.data_type='FLOAT'; disabled.operation='LESS_EQUAL'
    link(density,disabled.inputs[0]); disabled.inputs[1].default_value=0
    remove_zero=nodes.new('GeometryNodeDeleteGeometry'); remove_zero.domain='CURVE'; remove_zero.mode='ALL'
    link(path,remove_zero.inputs['Geometry']); link(disabled.outputs[0],remove_zero.inputs['Selection'])
    path=remove_zero.outputs['Geometry']
    limit=nodes.new('FunctionNodeCompare'); limit.data_type='INT'; limit.operation='GREATER_EQUAL'
    link(named('lp_spline_id','INT'),limit.inputs[0]); driver(limit.inputs[1],'limit')
    cap=nodes.new('GeometryNodeDeleteGeometry'); cap.domain='CURVE'; cap.mode='ALL'
    link(path,cap.inputs['Geometry']); link(limit.outputs[0],cap.inputs['Selection'])
    path=cap.outputs['Geometry']
    resample=nodes.new('GeometryNodeResampleCurve')
    resample.name='Banana Rachis Segments'
    driver(resample.inputs['Count'],'frond_segments',1)
    link(path,resample.inputs['Curve'])
    spline_factor=nodes.new('GeometryNodeSplineParameter')
    path=store(resample.outputs['Curve'],'lp_path_factor','FLOAT',spline_factor.outputs['Factor'])

    # Gravity is projected across the tangent. Blend toward a stable lateral
    # direction near vertical sections so the droop does not snap at a threshold.
    tangent=nodes.new('GeometryNodeInputTangent')
    dot=nodes.new('ShaderNodeVectorMath'); dot.operation='DOT_PRODUCT'
    link(tangent.outputs['Tangent'],dot.inputs[0]); dot.inputs[1].default_value=(0,0,-1)
    along=nodes.new('ShaderNodeVectorMath'); along.operation='SCALE'
    link(tangent.outputs['Tangent'],along.inputs[0]); link(dot.outputs['Value'],along.inputs['Scale'])
    transverse=nodes.new('ShaderNodeVectorMath'); transverse.operation='SUBTRACT'
    transverse.inputs[0].default_value=(0,0,-1)
    link(along.outputs[0],transverse.inputs[1])
    distance=nodes.new('ShaderNodeVectorMath'); distance.operation='LENGTH'
    link(transverse.outputs[0],distance.inputs[0])
    normalized=nodes.new('ShaderNodeVectorMath'); normalized.operation='NORMALIZE'
    link(transverse.outputs[0],normalized.inputs[0])
    weight=number('MINIMUM',1.,number('DIVIDE',distance.outputs['Value'],.35))
    fallback=nodes.new('ShaderNodeVectorMath'); fallback.operation='SCALE'
    fallback.inputs[0].default_value=(0,-1,0)
    link(number('SUBTRACT',1.,weight),fallback.inputs['Scale'])
    projected=nodes.new('ShaderNodeVectorMath'); projected.operation='SCALE'
    link(normalized.outputs[0],projected.inputs[0]); link(weight,projected.inputs['Scale'])
    combined=nodes.new('ShaderNodeVectorMath'); combined.operation='ADD'
    link(fallback.outputs[0],combined.inputs[0]); link(projected.outputs[0],combined.inputs[1])
    sag=nodes.new('ShaderNodeVectorMath'); sag.operation='NORMALIZE'
    link(combined.outputs[0],sag.inputs[0])
    length=nodes.new('GeometryNodeSplineLength')
    amount=number('MULTIPLY',value('frond_droop'),number('MULTIPLY',length.outputs['Length'],number('POWER',spline_factor.outputs['Factor'],2.)))
    offset=nodes.new('ShaderNodeVectorMath'); offset.operation='SCALE'
    link(sag.outputs[0],offset.inputs[0]); link(amount,offset.inputs['Scale'])
    bend=nodes.new('GeometryNodeSetPosition')
    link(path,bend.inputs['Geometry']); link(offset.outputs[0],bend.inputs['Offset'])
    path=store(bend.outputs['Geometry'],'lp_wind','FLOAT',number('POWER',spline_factor.outputs['Factor'],2.))

    profile=nodes.new('GeometryNodeCurvePrimitiveCircle')
    profile.name='Live Path Stem Profile'
    driver(profile.inputs['Resolution'],'frond_stem_sides')
    driver(profile.inputs['Radius'],'frond_stem_radius')
    tip=value('frond_stem_tip')
    curve_radius=nodes.new('GeometryNodeInputRadius')
    stem_scale=number('MULTIPLY',curve_radius.outputs['Radius'],
                      number('SUBTRACT',1.,number('MULTIPLY',number('SUBTRACT',1.,tip),spline_factor.outputs['Factor'])))
    stem_mesh=nodes.new('GeometryNodeCurveToMesh')
    link(path,stem_mesh.inputs['Curve']); link(profile.outputs['Curve'],stem_mesh.inputs['Profile Curve'])
    link(stem_scale,stem_mesh.inputs['Scale'])
    stem_mat=nodes.new('GeometryNodeSetMaterial')
    stem_mat.inputs['Material'].default_value=materials[0]
    link(stem_mesh.outputs['Mesh'],stem_mat.inputs['Geometry'])
    stem=store(stem_mat.outputs['Geometry'],'lp_card_id','INT',-1,'FACE')

    spline_id=named('lp_spline_id','INT')
    total=sum(slot.weight for slot in slots)
    selection=random('FLOAT',0.,total,spline_id,'texture_seed')
    choice=None
    for slot_index in reversed(range(len(slots)-1)):
        threshold=sum(slot.weight for slot in slots[:slot_index+1])
        less=nodes.new('FunctionNodeCompare'); less.data_type='FLOAT'; less.operation='LESS_THAN'
        link(selection,less.inputs[0]); less.inputs[1].default_value=threshold
        switch=nodes.new('GeometryNodeSwitch'); switch.input_type='INT'
        link(less.outputs[0],switch.inputs['Switch'])
        switch.inputs['True'].default_value=slot_index
        if choice is None: switch.inputs['False'].default_value=len(slots)-1
        else: link(choice,switch.inputs['False'])
        choice=switch.outputs[0]
    if choice is None: choice=0
    path=store(path,'lp_template','INT',choice,'CURVE')

    ratio=nodes.new('ShaderNodeValue'); ratio.name='Preview Ratio'
    ratio.outputs[0].default_value=settings.preview_ratio if settings.preview_enabled else 1.
    preview_chance=random('FLOAT',0.,1.,spline_id,'seed',717)
    over=nodes.new('FunctionNodeCompare'); over.data_type='FLOAT'; over.operation='GREATER_THAN'
    link(preview_chance,over.inputs[0]); link(ratio.outputs[0],over.inputs[1])
    viewport=nodes.new('GeometryNodeIsViewport')
    viewport_only=nodes.new('FunctionNodeBooleanMath'); viewport_only.operation='AND'
    link(over.outputs[0],viewport_only.inputs[0]); link(viewport.outputs[0],viewport_only.inputs[1])
    thin=nodes.new('GeometryNodeDeleteGeometry'); thin.domain='CURVE'; thin.mode='ALL'
    link(path,thin.inputs['Geometry']); link(viewport_only.outputs[0],thin.inputs['Selection'])
    visible=thin.outputs['Geometry']

    base_hue,base_saturation,base_value=colorsys.rgb_to_hsv(*settings.color)
    hue=random('FLOAT',settings.hue_min,settings.hue_max,spline_id,'color_seed')
    saturation=random('FLOAT',settings.saturation_min,settings.saturation_max,spline_id,'color_seed',101)
    brightness=random('FLOAT',settings.value_min,settings.value_max,spline_id,'color_seed',202)
    tint=random('FLOAT_VECTOR',tuple(settings.tint_min),tuple(settings.tint_max),spline_id,'color_seed',303)
    hsv=nodes.new('FunctionNodeCombineColor'); hsv.mode='HSV'
    link(number('FLOORED_MODULO',number('ADD',base_hue,hue),1.),hsv.inputs[0])
    link(number('MINIMUM',1.,number('MULTIPLY',base_saturation,saturation)),hsv.inputs[1])
    link(number('MINIMUM',1.,number('MULTIPLY',base_value,brightness)),hsv.inputs[2])
    tint_multiply=nodes.new('ShaderNodeVectorMath'); tint_multiply.operation='MULTIPLY'
    link(hsv.outputs['Color'],tint_multiply.inputs[0]); link(tint,tint_multiply.inputs[1])
    opacity=random('FLOAT',settings.opacity_min,settings.opacity_max,spline_id,'color_seed',404)
    phase=random('FLOAT',0.,math.tau,spline_id,'seed',505)
    uniform=random('FLOAT',settings.size_min,settings.size_max,spline_id,'size_seed')
    axis=random('FLOAT_VECTOR',tuple(settings.axis_min),tuple(settings.axis_max),spline_id,'size_seed',101)
    axis_x=nodes.new('ShaderNodeSeparateXYZ'); link(axis,axis_x.inputs[0])
    size=number('MULTIPLY',uniform,axis_x.outputs['X'])

    joined=nodes.new('GeometryNodeJoinGeometry')
    link(stem,joined.inputs[0])
    for slot_index,slot in enumerate(slots):
        match=nodes.new('FunctionNodeCompare'); match.data_type='INT'; match.operation='EQUAL'
        link(named('lp_template','INT'),match.inputs[0]); match.inputs[1].default_value=slot_index
        separate=nodes.new('GeometryNodeSeparateGeometry'); separate.domain='CURVE'
        link(visible,separate.inputs['Geometry']); link(match.outputs[0],separate.inputs['Selection'])
        begin=number('MINIMUM',.95,number('MAXIMUM',0.,number('ADD',value('frond_petiole'),(slot.pivot-.5)*.15)))
        trim=nodes.new('GeometryNodeTrimCurve'); trim.mode='FACTOR'
        link(separate.outputs['Selection'],trim.inputs['Curve']); link(begin,trim.inputs[2])
        blade_resample=nodes.new('GeometryNodeResampleCurve')
        blade_resample.name=f'Banana Blade Segments {slot_index}'
        driver(blade_resample.inputs['Count'],'frond_segments',1)
        link(trim.outputs['Curve'],blade_resample.inputs['Curve'])
        blade_factor=nodes.new('GeometryNodeSplineParameter')
        blade_curve=store(blade_resample.outputs['Curve'],'lp_blade_v','FLOAT',blade_factor.outputs['Factor'])
        twist=value('twist')
        tilt=nodes.new('GeometryNodeSetCurveTilt')
        link(blade_curve,tilt.inputs['Curve'])
        link(number('ADD',slot.rotation,number('MULTIPLY',twist,blade_factor.outputs['Factor'])),tilt.inputs['Tilt'])
        blade_curve=tilt.outputs['Curve']
        blade_normal=nodes.new('GeometryNodeInputNormal')
        bend_scale=number('MULTIPLY',value('bend'),number('POWER',blade_factor.outputs['Factor'],2.))
        blade_offset=nodes.new('ShaderNodeVectorMath'); blade_offset.operation='SCALE'
        link(blade_normal.outputs['Normal'],blade_offset.inputs[0]); link(bend_scale,blade_offset.inputs['Scale'])
        blade_bend=nodes.new('GeometryNodeSetPosition')
        link(blade_curve,blade_bend.inputs['Geometry']); link(blade_offset.outputs[0],blade_bend.inputs['Offset'])
        blade_curve=blade_bend.outputs['Geometry']
        local_index=nodes.new('GeometryNodeInputIndex')
        blade_curve=store(blade_curve,'lp_local_spline_id','INT',local_index.outputs['Index'],'CURVE')

        line=nodes.new('GeometryNodeCurvePrimitiveLine')
        line.inputs['Start'].default_value=(-.5,0,0)
        line.inputs['End'].default_value=(.5,0,0)
        across=nodes.new('GeometryNodeResampleCurve')
        across.inputs['Count'].default_value=3
        link(line.outputs['Curve'],across.inputs['Curve'])
        across_factor=nodes.new('GeometryNodeSplineParameter')
        blade_profile=store(across.outputs['Curve'],'lp_profile_u','FLOAT',across_factor.outputs['Factor'])
        distance=number('MULTIPLY',number('ABSOLUTE',number('SUBTRACT',across_factor.outputs['Factor'],.5)),2.)
        edge=number('MULTIPLY',value('frond_leaf_droop'),distance)
        center=number('MULTIPLY',value('valley'),number('SUBTRACT',1.,distance))
        profile_y=number('ADD',edge,center)
        profile_vector=nodes.new('ShaderNodeCombineXYZ')
        link(profile_y,profile_vector.inputs['Y'])
        profile_shape=nodes.new('GeometryNodeSetPosition')
        link(blade_profile,profile_shape.inputs['Geometry']); link(profile_vector.outputs[0],profile_shape.inputs['Offset'])

        local_factor=named('lp_blade_v','FLOAT')
        rise=number('MINIMUM',1.,number('MULTIPLY',local_factor,5.))
        fall=number('MINIMUM',1.,number('MULTIPLY',number('SUBTRACT',1.,local_factor),6.))
        taper=number('SUBTRACT',1.,number('MULTIPLY',value('frond_taper'),number('MULTIPLY',local_factor,.35)))
        envelope=number('MAXIMUM',.025,number('MULTIPLY',rise,number('MULTIPLY',fall,taper)))
        width=number('MULTIPLY',value('frond_width'),number('MULTIPLY',slot.size*slot.aspect*settings.scale_axes[0],size))
        scale=number('MULTIPLY',envelope,number('MULTIPLY',width,curve_radius.outputs['Radius']))
        ribbon=nodes.new('GeometryNodeCurveToMesh')
        link(blade_curve,ribbon.inputs['Curve']); link(profile_shape.outputs['Geometry'],ribbon.inputs['Profile Curve'])
        link(scale,ribbon.inputs['Scale'])
        # Edge vertices retreat toward their own spline, leaving the midrib
        # untouched. Each side samples a separate deterministic tear chance.
        mesh_index=nodes.new('GeometryNodeInputIndex')
        chance=random('FLOAT',0.,1.,mesh_index.outputs['Index'],'blade_tear_seed')
        tear_event=nodes.new('FunctionNodeCompare'); tear_event.data_type='FLOAT'
        tear_event.operation='LESS_THAN'
        link(chance,tear_event.inputs[0]); link(value('blade_tear_chance'),tear_event.inputs[1])
        magnitude=random('FLOAT',.4,1.,mesh_index.outputs['Index'],'blade_tear_seed',101)
        edge_weight=number('MULTIPLY',2.,number('ABSOLUTE',number('SUBTRACT',named('lp_profile_u','FLOAT'),.5)))
        interior=number('SINE',number('MULTIPLY',math.pi,local_factor))
        strength=number('MULTIPLY',value('blade_edge_tear'),
                        number('MULTIPLY',tear_event.outputs[0],
                               number('MULTIPLY',magnitude,number('MULTIPLY',edge_weight,interior))))
        sample_center=nodes.new('GeometryNodeSampleCurve')
        link(blade_curve,sample_center.inputs['Curves'])
        link(local_factor,sample_center.inputs['Factor'])
        link(named('lp_local_spline_id','INT'),sample_center.inputs['Curve Index'])
        mesh_position=nodes.new('GeometryNodeInputPosition')
        toward_center=nodes.new('ShaderNodeVectorMath'); toward_center.operation='SUBTRACT'
        link(sample_center.outputs['Position'],toward_center.inputs[0])
        link(mesh_position.outputs['Position'],toward_center.inputs[1])
        tear_offset=nodes.new('ShaderNodeVectorMath'); tear_offset.operation='SCALE'
        link(toward_center.outputs[0],tear_offset.inputs[0]); link(strength,tear_offset.inputs['Scale'])
        tear_shape=nodes.new('GeometryNodeSetPosition')
        link(ribbon.outputs['Mesh'],tear_shape.inputs['Geometry'])
        link(tear_offset.outputs[0],tear_shape.inputs['Offset'])
        blade=store(tear_shape.outputs['Geometry'],'lp_card_id','INT',spline_id,'FACE')
        blade=store(blade,'lp_card_source_id','INT',spline_id)
        blade=store(blade,'lp_card','BOOLEAN',True,'FACE')
        blade=store(blade,'lp_card_u','FLOAT',named('lp_profile_u','FLOAT'))
        blade=store(blade,'lp_card_v','FLOAT',local_factor)
        u0,v0,u1,v1=slot.uv_region
        uv=nodes.new('ShaderNodeCombineXYZ')
        link(number('ADD',u0,number('MULTIPLY',named('lp_profile_u','FLOAT'),u1-u0)),uv.inputs['X'])
        link(number('ADD',v0,number('MULTIPLY',local_factor,v1-v0)),uv.inputs['Y'])
        blade=store(blade,'UVMap','FLOAT2',uv.outputs[0],'CORNER')
        blade=store(blade,'lp_color','FLOAT_COLOR',tint_multiply.outputs[0])
        blade=store(blade,'lp_opacity','FLOAT',opacity)
        blade=store(blade,'lp_card_phase','FLOAT',phase)
        # One frond moves together, while individual blades still flutter.
        blade=store(blade,'lp_cluster_phase','FLOAT',0.)
        blade=store(blade,'lp_wind','FLOAT',number('POWER',named('lp_path_factor','FLOAT'),2.))
        blade=store(blade,'lp_leaf_wind','FLOAT',number('POWER',local_factor,2.))
        anchor=nodes.new('GeometryNodeSampleCurve')
        link(path,anchor.inputs['Curves']); link(begin,anchor.inputs['Factor'])
        link(spline_id,anchor.inputs['Curve Index'])
        blade=store(blade,'lp_anchor','FLOAT_VECTOR',anchor.outputs['Position'])
        material=nodes.new('GeometryNodeSetMaterial')
        material.inputs['Material'].default_value=materials[slot_index+1]
        link(blade,material.inputs['Geometry'])
        link(material.outputs['Geometry'],joined.inputs[0])

    output=nodes.new('NodeGroupOutput')
    if settings.kind=='Tree':
        source_mesh=nodes.new('NodeGroupInput')
        combined=nodes.new('GeometryNodeJoinGeometry')
        link(source_mesh.outputs['Geometry'],combined.inputs[0])
        link(joined.outputs['Geometry'],combined.inputs[0])
        link(combined.outputs['Geometry'],output.inputs['Geometry'])
    else: link(joined.outputs['Geometry'],output.inputs['Geometry'])
    return graph


def snapshot(source,ratio):
    """Reduce banana blade lengthwise resolution and rachis sides for LOD."""
    modifier=instance_cards.modifier(source)
    if not modifier or source.landscapy.pattern!='Banana' or source.get('lp_live_mode') not in {'Path','Surface','Volume','TreePath','TreeSurface','TreeVolume'}:
        raise ValueError('Banana snapshot requires a live Banana source')
    original=modifier.node_group
    copy=original.copy()
    sides=max(3,round(source.landscapy.frond_stem_sides*ratio))
    segments=max(4,round(source.landscapy.frond_segments*ratio))
    try:
        profile=copy.nodes.get('Live Path Stem Profile')
        if not profile: raise ValueError('Banana graph has no stem profile')
        profile.inputs['Resolution'].driver_remove('default_value')
        profile.inputs['Resolution'].default_value=sides
        for node in copy.nodes:
            if node.name.startswith('Banana Blade Segments '):
                node.inputs['Count'].driver_remove('default_value')
                node.inputs['Count'].default_value=segments+1
        modifier.node_group=copy
        return instance_cards.full_mesh(source),sides,segments
    finally:
        modifier.node_group=original
        if copy.users==0: bpy.data.node_groups.remove(copy)
