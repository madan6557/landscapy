"""Compact card source: solid mesh plus one point per card, realized by Geometry Nodes."""
import math
import bpy
from mathutils import Vector

NAME='Landscapy Card Instances'


def modifier(source):
    return source.modifiers.get(NAME)


def ratio_node(source):
    mod=modifier(source)
    return mod.node_group.nodes.get('Preview Ratio') if mod and mod.node_group else None


def clear(source):
    mod=modifier(source)
    if not mod: return
    group=mod.node_group
    templates=[node.inputs['Object'].default_value for node in group.nodes
               if node.type=='OBJECT_INFO' and node.inputs['Object'].default_value] if group else []
    source.modifiers.remove(mod)
    if group and group.users==0: bpy.data.node_groups.remove(group)
    for template in templates:
        if template.users==0:
            mesh=template.data
            bpy.data.objects.remove(template,do_unlink=True)
            if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)


def _cards(builder):
    if not builder.f: return [],{}
    if len(builder.f)!=len(builder.card_flags): raise ValueError('Invalid card topology')
    templates={}; records=[]; groups={}
    uv_start=0
    for index,face in enumerate(builder.f):
        uv=builder.uv[uv_start:uv_start+len(face)]
        uv_start+=len(face)
        if not builder.card_flags[index]:
            continue
        card_id=builder.card_ids[index]
        if card_id<0: raise ValueError('Card face lacks a stable ID')
        group=groups.setdefault(card_id,{'faces':[],'uv':{},'material':builder.mi[index]})
        if group['material']!=builder.mi[index]: raise ValueError('A card must use one material slot')
        group['faces'].append(tuple(face))
        for vertex,value in zip(face,uv):
            value=tuple(value)
            if vertex in group['uv'] and group['uv'][vertex]!=value:
                raise ValueError('Instanced Cards requires a consistent UV per card vertex')
            group['uv'][vertex]=value
    for card_id,group in groups.items():
        indices=sorted(group['uv'])
        remap={vertex:index for index,vertex in enumerate(indices)}
        faces=tuple(tuple(remap[vertex] for vertex in face) for face in group['faces'])
        count=len(indices)
        if count==4 and len(faces)==1 and len(faces[0])==4:
            pass
        elif count==5 and len(faces)==4 and all(len(face)==3 for face in faces):
            pass
        else:
            segments=math.isqrt(count)-1
            if segments<2 or (segments+1)**2!=count or len(faces)!=segments**2 or any(len(face)!=4 for face in faces):
                raise ValueError('Instanced Cards needs a Quad, four-triangle Valley/Peak, or regular subdivided card grid')
        uv=tuple(group['uv'][vertex] for vertex in indices)
        wind=tuple(builder.leaf_wind[vertex] for vertex in indices)
        key=(group['material'],uv,faces,wind)
        if key not in templates: templates[key]=len(templates)
        corners=tuple(tuple(builder.v[vertex]) for vertex in indices)
        center=sum((Vector(point) for point in corners),Vector())/len(corners)
        records.append({'position':tuple(center),'template':templates[key],
                        'source_index':indices[0],'card_id':card_id,'corners':corners})
    return records,templates


def _point_mesh(source,builder,records,materials):
    mesh=bpy.data.meshes.new(source.name+' • Card Points')
    wood_faces=[index for index,flag in enumerate(builder.card_flags) if not flag]
    wood_indices=sorted({vertex for index in wood_faces for vertex in builder.f[index]})
    remap={vertex:index for index,vertex in enumerate(wood_indices)}
    positions=[builder.v[index] for index in wood_indices]+[record['position'] for record in records]
    mesh.from_pydata(positions,[],[tuple(remap[vertex] for vertex in builder.f[index]) for index in wood_faces])
    mesh.update()
    for material in materials: mesh.materials.append(material)
    uv=mesh.uv_layers.new(name='UVMap')
    offsets=[]; cursor=0
    for face in builder.f:
        offsets.append(cursor); cursor+=len(face)
    for polygon,index in zip(mesh.polygons,wood_faces):
        polygon.material_index=builder.mi[index]
        polygon.use_smooth=builder.detail_scale>=1.5
        for loop,item in zip(polygon.loop_indices,builder.uv[offsets[index]:offsets[index]+len(builder.f[index])]):
            uv.data[loop].uv=item
    flags=mesh.attributes.new('lp_card','BOOLEAN','FACE')
    ids=mesh.attributes.new('lp_card_id','INT','FACE')
    for item in ids.data: item.value=-1
    def attr(name,kind,values,field):
        data=mesh.attributes.new(name,kind,'POINT')
        for item,value in zip(data.data,values): setattr(item,field,value)
    source_indices=wood_indices+[row['source_index'] for row in records]
    nwood=len(wood_indices)
    attr('lp_instance','BOOLEAN',[False]*nwood+[True]*len(records),'value')
    bough_density=getattr(builder,'bough_density',None)
    if bough_density is not None:
        attr('lp_bough_density','FLOAT',[0.]*nwood+bough_density,'value')
    attr('lp_template','INT',[-1]*nwood+[row['template'] for row in records],'value')
    attr('lp_card_source_id','INT',[-1]*nwood+[row['card_id'] for row in records],'value')
    detail_offsets=[]; buffer_starts=[]
    for row in records:
        if len(row['corners'])>5:
            buffer_starts.append(len(detail_offsets))
            detail_offsets.extend(tuple(Vector(point)-Vector(row['position'])) for point in row['corners'])
        else: buffer_starts.append(-1)
    attr('lp_buffer_start','INT',[-1]*nwood+buffer_starts,'value')
    for corner in range(5):
        attr('lp_corner'+str(corner),'FLOAT_VECTOR',[(0,0,0)]*nwood+
             [tuple(Vector(row['corners'][min(corner,len(row['corners'])-1)])-Vector(row['position']))
              for row in records],'vector')
    attr('lp_color','FLOAT_COLOR',[builder.col[i] for i in source_indices],'color')
    attr('lp_opacity','FLOAT',[builder.opacity[i] for i in source_indices],'value')
    height=max([point[2] for point in builder.v]+[.01])
    attr('lp_wind','FLOAT',[max(0,position[2]/height)**2 for position in positions],'value')
    attr('lp_cluster_phase','FLOAT',[builder.cluster_phase[i] for i in source_indices],'value')
    attr('lp_card_phase','FLOAT',[builder.card_phase[i] for i in source_indices],'value')
    branch_ids=[builder.branch_ids[i] for i in source_indices]
    branch_levels=[builder.branch_levels[i] for i in source_indices]
    branch_ts=[builder.branch_t[i] for i in source_indices]
    attr('lp_branch_id','INT',branch_ids,'value')
    attr('lp_branch_level','INT',branch_levels,'value')
    attr('lp_branch_t','FLOAT',branch_ts,'value')
    from . import branch_wind_fields
    cos,sin=branch_wind_fields(source,branch_ids,branch_ts)
    attr('lp_branch_wind_cos','FLOAT',cos,'value')
    attr('lp_branch_wind_sin','FLOAT',sin,'value')
    return mesh,detail_offsets


def _template(source,number,key,materials):
    material_index,uv,faces,wind=key
    mesh=bpy.data.meshes.new(source.name+f' • Card {number}')
    vertices=[(-.5,0,-.5),(.5,0,-.5),(.5,0,.5),(-.5,0,.5)]
    if len(uv)==5: vertices.append((0,0,0))
    elif len(uv)>5:
        segments=math.isqrt(len(uv))-1
        vertices=[(index%(segments+1)/segments-.5,0,
                   index//(segments+1)/segments-.5) for index in range(len(uv))]
    mesh.from_pydata(vertices,[],faces)
    mesh.update(); mesh.materials.append(materials[material_index])
    layer=mesh.uv_layers.new(name='UVMap')
    for polygon in mesh.polygons:
        for loop,vertex in zip(polygon.loop_indices,polygon.vertices): layer.data[loop].uv=uv[vertex]
    weights=mesh.attributes.new('lp_leaf_wind','FLOAT','POINT')
    for item,value in zip(weights.data,wind): item.value=value
    corners=mesh.attributes.new('lp_corner_index','INT','POINT')
    for index,item in enumerate(corners.data): item.value=index
    flags=mesh.attributes.new('lp_card','BOOLEAN','FACE')
    for item in flags.data: item.value=True
    obj=bpy.data.objects.new(source.name+f' • Card {number}',mesh)
    return obj


def _detail_buffer(source,offsets):
    mesh=bpy.data.meshes.new(source.name+' • Card Detail Buffer')
    mesh.from_pydata(offsets,[],[])
    mesh.update()
    return bpy.data.objects.new(source.name+' • Card Detail Buffer',mesh)


def _group(source,templates,ratio,detail_offsets,live_bough=False):
    group=bpy.data.node_groups.new('LP Card Instances '+source.name,'GeometryNodeTree')
    group.is_modifier=True
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=group.nodes; L=group.links.new
    inp=nodes.new('NodeGroupInput'); out=nodes.new('NodeGroupOutput')
    def named(name,kind):
        node=nodes.new('GeometryNodeInputNamedAttribute'); node.data_type=kind
        node.inputs['Name'].default_value=name
        return node.outputs['Attribute']
    ids=named('lp_card_source_id','INT')
    is_card=named('lp_instance','BOOLEAN')
    split=nodes.new('GeometryNodeSeparateGeometry'); split.domain='POINT'
    L(inp.outputs[0],split.inputs['Geometry']); L(is_card,split.inputs['Selection'])
    active=split.outputs['Selection']
    if live_bough:
        def trim(geometry, field, property_name, data_type, operation):
            compare=nodes.new('FunctionNodeCompare')
            compare.data_type=data_type; compare.operation=operation
            a,b=compare.inputs['A'],compare.inputs['B']
            L(field,a)
            driver=b.driver_add('default_value').driver
            driver.type='AVERAGE'
            target=driver.variables.new().targets[0]
            target.id=source
            target.data_path='landscapy.'+property_name
            delete=nodes.new('GeometryNodeDeleteGeometry'); delete.domain='POINT'
            L(geometry,delete.inputs['Geometry']); L(compare.outputs[0],delete.inputs['Selection'])
            return delete.outputs['Geometry']
        active=trim(active,named('lp_bough_density','FLOAT'),'density','FLOAT','GREATER_THAN')
        active=trim(active,nodes.new('GeometryNodeInputIndex').outputs['Index'],'limit','INT','GREATER_EQUAL')
    random=nodes.new('FunctionNodeRandomValue'); random.data_type='FLOAT'
    random.inputs['Min'].default_value=0; random.inputs['Max'].default_value=1
    L(ids,random.inputs['ID'])
    amount=nodes.new('ShaderNodeValue'); amount.name='Preview Ratio'; amount.outputs[0].default_value=ratio
    compare=nodes.new('FunctionNodeCompare'); compare.data_type='FLOAT'; compare.operation='GREATER_THAN'
    L(random.outputs['Value'],compare.inputs[0]); L(amount.outputs[0],compare.inputs[1])
    viewport=nodes.new('GeometryNodeIsViewport')
    thin=nodes.new('FunctionNodeBooleanMath'); thin.operation='AND'
    L(compare.outputs[0],thin.inputs[0]); L(viewport.outputs[0],thin.inputs[1])
    delete=nodes.new('GeometryNodeDeleteGeometry'); delete.domain='POINT'; delete.mode='ALL'
    L(active,delete.inputs['Geometry']); L(thin.outputs[0],delete.inputs['Selection'])
    anchor=nodes.new('GeometryNodeStoreNamedAttribute'); anchor.data_type='FLOAT_VECTOR'; anchor.domain='POINT'
    anchor.inputs['Name'].default_value='lp_instance_anchor'
    L(delete.outputs[0],anchor.inputs['Geometry'])
    current_position=nodes.new('GeometryNodeInputPosition')
    L(current_position.outputs[0],anchor.inputs['Value'])
    template_id=named('lp_template','INT')
    join=nodes.new('GeometryNodeJoinGeometry')
    for key,number in templates.items():
        obj=_template(source,number,key,list(source.data.materials))
        match=nodes.new('FunctionNodeCompare'); match.data_type='INT'; match.operation='EQUAL'
        match.inputs[1].default_value=number
        L(template_id,match.inputs[0])
        separate=nodes.new('GeometryNodeSeparateGeometry'); separate.domain='POINT'
        L(anchor.outputs['Geometry'],separate.inputs['Geometry']); L(match.outputs[0],separate.inputs['Selection'])
        info=nodes.new('GeometryNodeObjectInfo'); info.inputs['Object'].default_value=obj
        instance=nodes.new('GeometryNodeInstanceOnPoints')
        L(separate.outputs['Selection'],instance.inputs['Points'])
        L(info.outputs['Geometry'],instance.inputs['Instance'])
        L(instance.outputs['Instances'],join.inputs[0])
    realize=nodes.new('GeometryNodeRealizeInstances'); L(join.outputs[0],realize.inputs['Geometry'])
    corner_index=named('lp_corner_index','INT')
    position=named('lp_corner0','FLOAT_VECTOR')
    for corner in range(1,5):
        match=nodes.new('FunctionNodeCompare'); match.data_type='INT'; match.operation='EQUAL'
        match.inputs[1].default_value=corner
        L(corner_index,match.inputs[0])
        choose=nodes.new('GeometryNodeSwitch'); choose.input_type='VECTOR'
        L(match.outputs[0],choose.inputs['Switch'])
        L(position,choose.inputs['False'])
        L(named('lp_corner'+str(corner),'FLOAT_VECTOR'),choose.inputs['True'])
        position=choose.outputs[0]
    if detail_offsets:
        buffer=_detail_buffer(source,detail_offsets)
        info=nodes.new('GeometryNodeObjectInfo'); info.inputs['Object'].default_value=buffer
        sample=nodes.new('GeometryNodeSampleIndex'); sample.data_type='FLOAT_VECTOR'; sample.domain='POINT'
        L(info.outputs['Geometry'],sample.inputs['Geometry'])
        buffer_position=nodes.new('GeometryNodeInputPosition')
        L(buffer_position.outputs['Position'],sample.inputs['Value'])
        index=nodes.new('ShaderNodeMath'); index.operation='ADD'
        start=named('lp_buffer_start','INT')
        L(start,index.inputs[0]); L(corner_index,index.inputs[1])
        L(index.outputs[0],sample.inputs['Index'])
        has_detail=nodes.new('FunctionNodeCompare'); has_detail.data_type='INT'; has_detail.operation='GREATER_THAN'
        has_detail.inputs[1].default_value=-1
        L(start,has_detail.inputs[0])
        choose=nodes.new('GeometryNodeSwitch'); choose.input_type='VECTOR'
        L(has_detail.outputs[0],choose.inputs['Switch'])
        L(position,choose.inputs['False']); L(sample.outputs['Value'],choose.inputs['True'])
        position=choose.outputs[0]
    reshape=nodes.new('GeometryNodeSetPosition')
    L(realize.outputs['Geometry'],reshape.inputs['Geometry'])
    translate=nodes.new('ShaderNodeVectorMath'); translate.operation='ADD'
    L(named('lp_instance_anchor','FLOAT_VECTOR'),translate.inputs[0])
    L(position,translate.inputs[1])
    L(translate.outputs[0],reshape.inputs['Position'])
    face_id=nodes.new('GeometryNodeStoreNamedAttribute'); face_id.data_type='INT'; face_id.domain='FACE'
    face_id.inputs['Name'].default_value='lp_card_id'
    L(reshape.outputs['Geometry'],face_id.inputs['Geometry']); L(ids,face_id.inputs['Value'])
    combined=nodes.new('GeometryNodeJoinGeometry')
    L(split.outputs['Inverted'],combined.inputs[0])
    L(face_id.outputs['Geometry'],combined.inputs[0])
    L(combined.outputs[0],out.inputs[0])
    return group


def commit(source,builder,materials,settings):
    if settings.kind not in {'Foliage','Tree','Ivy'}:
        raise ValueError('Instanced Cards requires a Foliage, Tree or Ivy generator')
    records,templates=_cards(builder)
    mesh,detail_offsets=_point_mesh(source,builder,records,materials)
    # The node group reads the new material slots while being assembled.
    old_mesh=source.data
    groups_before=set(bpy.data.node_groups)
    objects_before=set(bpy.data.objects)
    source.data=mesh
    try:
        # Automatic ornaments bind against the full evaluated mesh. Their
        # viewport preview uses a separate copy so target indices stay fixed.
        ratio=1. if settings.ornaments_enabled else settings.preview_ratio if settings.preview_enabled else 1.
        group=_group(source,templates,ratio,detail_offsets,live_bough=getattr(builder,'bough_density',None) is not None)
    except BaseException:
        source.data=old_mesh
        for created in set(bpy.data.node_groups)-groups_before:
            if created.users==0: bpy.data.node_groups.remove(created)
        for created in set(bpy.data.objects)-objects_before:
            if created.users==0:
                data=created.data
                bpy.data.objects.remove(created,do_unlink=True)
                if data and data.users==0: bpy.data.meshes.remove(data)
        bpy.data.meshes.remove(mesh)
        raise
    clear(source)
    old_wind=source.modifiers.get('Landscapy Wind')
    if old_wind:
        wind_group=old_wind.node_group
        source.modifiers.remove(old_wind)
        if wind_group and wind_group.users==0: bpy.data.node_groups.remove(wind_group)
    mod=source.modifiers.new(NAME,'NODES'); mod.node_group=group
    if old_mesh and old_mesh.users==0: bpy.data.meshes.remove(old_mesh)


def full_mesh(source):
    """Snapshot all cards in a neutral pose for Build Variants."""
    node=ratio_node(source)
    if not node: return None
    old_ratio=node.outputs[0].default_value
    wind=source.modifiers.get('Landscapy Wind')
    old_wind=(wind.show_viewport,wind.show_render) if wind else None
    try:
        node.outputs[0].default_value=1
        if wind: wind.show_viewport=False; wind.show_render=False
        bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get(); dg.update()
        return bpy.data.meshes.new_from_object(source.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
    finally:
        node.outputs[0].default_value=old_ratio
        if wind: wind.show_viewport,wind.show_render=old_wind
        bpy.context.view_layer.update()
