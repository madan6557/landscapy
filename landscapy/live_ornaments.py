"""Geometry Nodes ornament scattering on evaluated live foliage and Ivy."""
import math
import bpy


NAME='Landscapy Live Ornaments'


def _driver(socket,owner,property_name,offset=0):
    driver=socket.driver_add('default_value').driver
    driver.type='SCRIPTED' if offset else 'AVERAGE'
    variable=driver.variables.new(); variable.name='value'
    variable.targets[0].id=owner
    variable.targets[0].data_path='landscapy.'+property_name
    if offset: driver.expression=f'value+{offset}'


def _graph(owner,slots,prototypes,rest):
    s=owner.landscapy
    group=bpy.data.node_groups.new('LP Live Ornaments '+owner.name,'GeometryNodeTree')
    group.is_modifier=True
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=group.nodes; link=group.links.new
    output=nodes.new('NodeGroupOutput')

    def named(name,kind):
        node=nodes.new('GeometryNodeInputNamedAttribute')
        node.data_type=kind; node.inputs['Name'].default_value=name
        return node.outputs['Attribute']
    def prop(name,offset=0):
        node=nodes.new('ShaderNodeValue'); _driver(node.outputs[0],owner,name,offset)
        return node.outputs[0]
    def number(operation,a,b=None):
        node=nodes.new('ShaderNodeMath'); node.operation=operation
        for index,value in enumerate((a,b)):
            if value is None: continue
            if isinstance(value,(int,float)): node.inputs[index].default_value=value
            else: link(value,node.inputs[index])
        return node.outputs[0]
    def compare(operation,a,b):
        node=nodes.new('FunctionNodeCompare'); node.data_type='FLOAT'; node.operation=operation
        for socket,value in ((node.inputs[0],a),(node.inputs[1],b)):
            if isinstance(value,(int,float)): socket.default_value=value
            else: link(value,socket)
        return node.outputs[0]
    def vector(operation,a,b):
        node=nodes.new('ShaderNodeVectorMath'); node.operation=operation
        link(a,node.inputs[0])
        if isinstance(b,(tuple,list)): node.inputs[1].default_value=b
        else: link(b,node.inputs[1])
        return node.outputs[0]
    def store(geometry,name,kind,value):
        node=nodes.new('GeometryNodeStoreNamedAttribute')
        node.data_type=kind; node.domain='POINT'; node.inputs['Name'].default_value=name
        link(geometry,node.inputs['Geometry']); link(value,node.inputs['Value'])
        return node.outputs['Geometry']
    def random_float(minimum,maximum,seed_property,identity,offset=0):
        node=nodes.new('FunctionNodeRandomValue'); node.data_type='FLOAT'
        for name,value in (('Min',minimum),('Max',maximum)):
            if isinstance(value,(float,int)): node.inputs[name].default_value=value
            else: link(value,node.inputs[name])
        _driver(node.inputs['Seed'],owner,seed_property,offset)
        link(identity,node.inputs['ID'])
        return node.outputs['Value']

    target=nodes.new('GeometryNodeObjectInfo'); target.name='Live Ornament Target'
    target.inputs['Object'].default_value=rest; target.transform_space='RELATIVE'
    surfaces=target.outputs['Geometry']
    if s.ornament_zone!='ALL':
        card=named('lp_card','BOOLEAN')
        split=nodes.new('GeometryNodeSeparateGeometry'); split.domain='FACE'
        link(surfaces,split.inputs['Geometry']); link(card,split.inputs['Selection'])
        surfaces=split.outputs['Selection' if s.ornament_zone=='FOLIAGE' else 'Inverted']

    scatter=nodes.new('GeometryNodeDistributePointsOnFaces')
    scatter.distribute_method='POISSON'
    link(surfaces,scatter.inputs['Mesh'])
    _driver(scatter.inputs['Density Max'],owner,'ornament_density')
    _driver(scatter.inputs['Distance Min'],owner,'ornament_spacing')
    _driver(scatter.inputs['Seed'],owner,'ornament_seed')
    points=store(scatter.outputs['Points'],'lp_ornament_normal','FLOAT_VECTOR',scatter.outputs['Normal'])

    bounds=nodes.new('GeometryNodeBoundBox'); link(surfaces,bounds.inputs['Geometry'])
    lower=nodes.new('ShaderNodeSeparateXYZ'); link(bounds.outputs['Min'],lower.inputs[0])
    upper=nodes.new('ShaderNodeSeparateXYZ'); link(bounds.outputs['Max'],upper.inputs[0])
    position=nodes.new('GeometryNodeInputPosition')
    height=nodes.new('ShaderNodeSeparateXYZ'); link(position.outputs['Position'],height.inputs[0])
    normalized=number('DIVIDE',number('SUBTRACT',height.outputs['Z'],lower.outputs['Z']),
                      number('MAXIMUM',.001,number('SUBTRACT',upper.outputs['Z'],lower.outputs['Z'])))
    outside=nodes.new('FunctionNodeBooleanMath'); outside.operation='OR'
    link(compare('LESS_THAN',normalized,prop('ornament_height_min')),outside.inputs[0])
    link(compare('GREATER_THAN',normalized,prop('ornament_height_max')),outside.inputs[1])
    trimmed=nodes.new('GeometryNodeDeleteGeometry'); trimmed.domain='POINT'; trimmed.mode='ALL'
    link(points,trimmed.inputs['Geometry']); link(outside.outputs[0],trimmed.inputs['Selection'])

    # Sort by an independent random key before the hard cap; card order cannot
    # concentrate all accepted ornaments on the first mesh faces.
    index=nodes.new('GeometryNodeInputIndex')
    ordering=random_float(0.,1.,'ornament_seed',index.outputs[0],101)
    sort=nodes.new('GeometryNodeSortElements'); sort.domain='POINT'
    link(trimmed.outputs['Geometry'],sort.inputs['Geometry'])
    link(ordering,sort.inputs['Sort Weight'])
    limited=nodes.new('GeometryNodeDeleteGeometry'); limited.domain='POINT'; limited.mode='ALL'
    link(sort.outputs['Geometry'],limited.inputs['Geometry'])
    link(compare('GREATER_EQUAL',index.outputs[0],prop('ornament_limit')),limited.inputs['Selection'])
    points=store(limited.outputs['Geometry'],'lp_ornament_id','INT',index.outputs[0])
    identity=named('lp_ornament_id','INT')

    hue=random_float(prop('ornament_hue_min'),prop('ornament_hue_max'),'ornament_color_seed',identity)
    saturation=random_float(prop('ornament_sat_min'),prop('ornament_sat_max'),'ornament_color_seed',identity,101)
    brightness=random_float(prop('ornament_value_min'),prop('ornament_value_max'),'ornament_color_seed',identity,202)
    hsv=nodes.new('ShaderNodeCombineXYZ')
    link(number('ADD',.5,hue),hsv.inputs['X'])
    link(saturation,hsv.inputs['Y']); link(brightness,hsv.inputs['Z'])
    points=store(points,'lp_ornament_hsv','FLOAT_VECTOR',hsv.outputs[0])
    opacity=random_float(prop('ornament_opacity_min'),prop('ornament_opacity_max'),
                         'ornament_color_seed',identity,303)
    points=store(points,'lp_ornament_opacity','FLOAT',opacity)

    total=sum(slot.weight for slot in slots)
    choice=random_float(0.,total,'ornament_choice_seed',identity)
    joined=nodes.new('GeometryNodeJoinGeometry')
    low=0.
    for slot_index,(slot,prototype) in enumerate(zip(slots,prototypes)):
        high=low+slot.weight
        eligible=nodes.new('FunctionNodeBooleanMath'); eligible.operation='AND'
        link(compare('GREATER_EQUAL',choice,low),eligible.inputs[0])
        link(compare('LESS_THAN',choice,high),eligible.inputs[1])
        split=nodes.new('GeometryNodeSeparateGeometry'); split.domain='POINT'
        link(points,split.inputs['Geometry']); link(eligible.outputs[0],split.inputs['Selection'])
        selected=split.outputs['Selection']
        source_index=nodes.new('FunctionNodeInputInt'); source_index.integer=slot_index
        selected=store(selected,'lp_ornament_source_index','INT',source_index.outputs[0])

        normal=named('lp_ornament_normal','FLOAT_VECTOR')
        offset=nodes.new('ShaderNodeVectorMath'); offset.operation='SCALE'
        link(normal,offset.inputs[0])
        link(number('ADD',prop('ornament_offset'),slot.offset),offset.inputs['Scale'])
        shift=nodes.new('GeometryNodeSetPosition')
        link(selected,shift.inputs['Geometry']); link(offset.outputs[0],shift.inputs['Offset'])
        selected=store(shift.outputs['Geometry'],'lp_anchor_position','FLOAT_VECTOR',position.outputs['Position'])

        tint=nodes.new('ShaderNodeCombineXYZ')
        for axis,channel in zip(('X','Y','Z'),range(3)):
            link(number('MULTIPLY',prop(f'ornament_color[{channel}]'),slot.tint[channel]),tint.inputs[axis])
        selected=store(selected,'lp_ornament_color','FLOAT_COLOR',tint.outputs[0])

        base=nodes.new('FunctionNodeAlignRotationToVector'); base.axis='Z'
        link(normal,base.inputs['Vector'])
        euler=nodes.new('ShaderNodeCombineXYZ')
        for axis,setting,slot_axis,seed_offset in [('X','ornament_pitch',0,11),
                                                   ('Y','ornament_roll',1,17),
                                                   ('Z','ornament_yaw',2,23)]:
            angle=random_float(number('MULTIPLY',prop(setting),-1),prop(setting),
                               'ornament_transform_seed',identity,seed_offset)
            link(number('ADD',angle,slot.rotation[slot_axis]),euler.inputs[axis])
        turn=nodes.new('FunctionNodeEulerToRotation'); link(euler.outputs[0],turn.inputs['Euler'])
        rotation=nodes.new('FunctionNodeRotateRotation'); rotation.rotation_space='LOCAL'
        link(base.outputs['Rotation'],rotation.inputs['Rotation'])
        link(turn.outputs['Rotation'],rotation.inputs['Rotate By'])

        size=random_float(prop('ornament_size_min'),prop('ornament_size_max'),
                          'ornament_transform_seed',identity,31)
        axes=nodes.new('ShaderNodeCombineXYZ')
        for axis,channel in zip(('X','Y','Z'),range(3)):
            link(prop(f'ornament_axes[{channel}]'),axes.inputs[axis])
        scale=nodes.new('ShaderNodeVectorMath'); scale.operation='SCALE'
        link(axes.outputs[0],scale.inputs[0])
        link(number('MULTIPLY',size,slot.scale),scale.inputs['Scale'])

        prototype_info=nodes.new('GeometryNodeObjectInfo')
        prototype_info.inputs['Object'].default_value=prototype
        instance=nodes.new('GeometryNodeInstanceOnPoints')
        link(selected,instance.inputs['Points'])
        link(prototype_info.outputs['Geometry'],instance.inputs['Instance'])
        link(rotation.outputs['Rotation'],instance.inputs['Rotation'])
        link(scale.outputs[0],instance.inputs['Scale'])
        link(instance.outputs['Instances'],joined.inputs[0])
        low=high
    realize=nodes.new('GeometryNodeRealizeInstances')
    link(joined.outputs[0],realize.inputs['Geometry'])
    link(realize.outputs['Geometry'],output.inputs['Geometry'])
    return group


def rebuild(owner):
    """Replace only this owner's live ornament output after a successful graph build."""
    from . import ornaments
    s=owner.landscapy
    slots=[entry for entry in s.ornament_slots if entry.object and entry.weight>0]
    if not slots:
        ornaments.clear(owner,'ORNAMENT'); s.ornament_status='Add at least one weighted source object'; return None
    for slot in slots:
        source=slot.object
        if source==owner or source.get('lp_ornament_owner') or source.get('lp_variant'):
            raise ValueError('Ornament source cannot be this generator or a managed output')
        if source.type!='MESH': raise ValueError('Ornament source must be a mesh object')
    dg=bpy.context.evaluated_depsgraph_get(); dg.update()
    child=None; group=None; rest=None; prototypes=[]; wrapped={}
    try:
        for slot in slots:
            source=slot.object
            evaluated=source.evaluated_get(dg)
            mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=dg)
            if not mesh.polygons:
                bpy.data.meshes.remove(mesh)
                raise ValueError('Ornament source has no evaluated faces: '+source.name)
            mesh.transform(source.matrix_world.to_3x3().to_4x4())
            for index,material in enumerate(list(mesh.materials)):
                if material not in wrapped: wrapped[material]=ornaments.wrap_material(material)
                mesh.materials[index]=wrapped[material]
            if not mesh.materials:
                if None not in wrapped: wrapped[None]=ornaments.wrap_material(None)
                mesh.materials.append(wrapped[None])
            proto=bpy.data.objects.new(owner.name+' • Ornament Prototype',mesh)
            proto['lp_live_ornament_prototype']=s.uid
            prototypes.append(proto)
        rest=owner.copy()
        rest.name=owner.name+' • Ornament Rest Surface'
        owner.users_collection[0].objects.link(rest)
        rest.parent=owner; rest.matrix_parent_inverse.identity(); rest.matrix_basis.identity()
        rest.landscapy.uid=''
        rest['lp_live_ornament_rest_proxy']=s.uid
        wind=rest.modifiers.get('Landscapy Wind')
        if wind: rest.modifiers.remove(wind)
        rest.hide_render=True; rest.hide_select=True; rest.hide_set(True)
        group=_graph(owner,slots,prototypes,rest)
        mesh=bpy.data.meshes.new(owner.name+' • Live Ornament Source')
        child=bpy.data.objects.new(owner.name+' • Live Ornaments',mesh)
        owner.users_collection[0].objects.link(child)
        child.parent=owner; child.matrix_parent_inverse.identity(); child.matrix_basis.identity()
        modifier=child.modifiers.new(NAME,'NODES'); modifier.node_group=group
        child.landscapy.target=owner
        child['lp_live_ornaments']=True
        from . import wind_modifier
        wind_modifier(child)
        bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get(); dg.update()
        evaluated=child.evaluated_get(dg); result=evaluated.to_mesh()
        try:
            ids=result.attributes.get('lp_ornament_id')
            count=len({item.value for item in ids.data}) if ids else 0
            faces=len(result.polygons)
        finally: evaluated.to_mesh_clear()
        ornaments.clear(owner,'ORNAMENT')
        child['lp_ornament_owner']=s.uid
        child['lp_attachment_kind']='ORNAMENT'
        child['lp_ornament_count']=count
        child.landscapy.binding_valid=True
        child.landscapy.binding_message='Live ornaments • following evaluated generator'
        s.ornament_status='Live ornaments • count follows controller and density; edit slots or zone with Update Ornaments'
        return child
    except BaseException:
        if child:
            data=child.data; bpy.data.objects.remove(child,do_unlink=True)
            if data and data.users==0: bpy.data.meshes.remove(data)
        if group and group.users==0: bpy.data.node_groups.remove(group)
        if rest:
            from . import instance_cards
            instance_cards.clear(rest)
            data=rest.data
            bpy.data.objects.remove(rest,do_unlink=True)
            if data and data.users==0: bpy.data.meshes.remove(data)
        for proto in prototypes:
            mesh=proto.data
            if proto.users==0: bpy.data.objects.remove(proto,do_unlink=True)
            if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)
        for material in wrapped.values():
            if material.users==0: bpy.data.materials.remove(material)
        raise
