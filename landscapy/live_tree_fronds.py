"""Branch-linked Tree fronds built from compact editable guide edges."""
import bpy
from mathutils import Vector
from . import instance_cards, live_surface


def enabled(settings):
    return (settings.kind=='Tree' and settings.live_surface and settings.instance_cards
            and settings.pattern in live_surface.ARRANGED_PATH_PATTERNS | {'Banana'}
            and settings.preset!='Dead Tree')


def branch_bough(settings):
    return (enabled(settings) and settings.pattern=='Conifer'
            and not (settings.controller and settings.controller.type=='MESH'))


def remove_guides(source):
    """Discard auxiliary branch guides after a frozen variant is realized."""
    for guide in [child for child in source.children if child.get('lp_tree_frond_guide')]:
        mesh=guide.data
        bpy.data.objects.remove(guide,do_unlink=True)
        if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)


def attach_mesh_anchors(nodes,link,points):
    """Grow mesh-canopy fronds from nearby wood toward sampled canopy points.

    The canopy point remains the tip target; branch wind metadata is sampled
    from the same wood surface as the new root. Both operations stay live.
    """
    source=nodes.new('NodeGroupInput')
    position=nodes.new('GeometryNodeInputPosition')
    nearest=nodes.new('GeometryNodeSampleNearestSurface'); nearest.data_type='FLOAT_VECTOR'
    link(source.outputs['Geometry'],nearest.inputs['Mesh'])
    link(position.outputs['Position'],nearest.inputs['Value'])
    link(position.outputs['Position'],nearest.inputs['Sample Position'])

    target=nodes.new('GeometryNodeStoreNamedAttribute')
    target.data_type='FLOAT_VECTOR'; target.domain='POINT'
    target.inputs['Name'].default_value='lp_canopy_target'
    link(points,target.inputs['Geometry'])
    link(position.outputs['Position'],target.inputs['Value'])
    points=target.outputs['Geometry']

    for name,kind in [('lp_branch_id','INT'),('lp_branch_level','INT'),('lp_branch_t','FLOAT'),
                      ('lp_branch_wind_cos','FLOAT'),('lp_branch_wind_sin','FLOAT')]:
        attribute=nodes.new('GeometryNodeInputNamedAttribute'); attribute.data_type=kind
        attribute.inputs['Name'].default_value=name
        sample=nodes.new('GeometryNodeSampleNearestSurface'); sample.data_type=kind
        link(source.outputs['Geometry'],sample.inputs['Mesh'])
        link(attribute.outputs['Attribute'],sample.inputs['Value'])
        link(position.outputs['Position'],sample.inputs['Sample Position'])
        store=nodes.new('GeometryNodeStoreNamedAttribute'); store.data_type=kind; store.domain='POINT'
        store.inputs['Name'].default_value=name
        link(points,store.inputs['Geometry']); link(sample.outputs['Value'],store.inputs['Value'])
        points=store.outputs['Geometry']

    relocate=nodes.new('GeometryNodeSetPosition')
    link(points,relocate.inputs['Geometry'])
    link(nearest.outputs['Value'],relocate.inputs['Position'])
    points=relocate.outputs['Geometry']
    target_attribute=nodes.new('GeometryNodeInputNamedAttribute')
    target_attribute.data_type='FLOAT_VECTOR'
    target_attribute.inputs['Name'].default_value='lp_canopy_target'
    direction=nodes.new('ShaderNodeVectorMath'); direction.operation='SUBTRACT'
    link(target_attribute.outputs['Attribute'],direction.inputs[0])
    link(position.outputs['Position'],direction.inputs[1])
    distance=nodes.new('ShaderNodeVectorMath'); distance.operation='LENGTH'
    link(direction.outputs[0],distance.inputs[0])
    rotation=nodes.new('FunctionNodeAlignRotationToVector'); rotation.axis='Z'
    link(direction.outputs[0],rotation.inputs['Vector'])
    return points,rotation.outputs['Rotation'],distance.outputs['Value']


def _guide(source,settings,anchors):
    from . import branch_wind_fields
    vertices=[]; edges=[]; ids=[]; levels=[]; branch_t=[]
    for origin,direction,multiplier,branch_id,level in anchors:
        direction=Vector(direction).normalized()
        start=Vector(origin)
        finish=start+direction*settings.length*multiplier
        if (finish-start).length<1e-5: continue
        index=len(vertices)
        vertices.extend((start,finish)); edges.append((index,index+1))
        ids.extend((branch_id,branch_id)); levels.extend((level,level))
        initial=0. if settings.preset in {'Palm','Banana'} else .25 if level>1 else .2
        branch_t.extend((initial,1.))
    mesh=bpy.data.meshes.new(source.name+' • Frond Guide Edges')
    mesh.from_pydata(vertices,edges,[]); mesh.update()
    cos,sin=branch_wind_fields(source,ids,branch_t)
    for name,kind,values in [('lp_branch_id','INT',ids),('lp_branch_level','INT',levels),
                             ('lp_branch_t','FLOAT',branch_t),
                             ('lp_branch_wind_cos','FLOAT',cos),('lp_branch_wind_sin','FLOAT',sin)]:
        attr=mesh.attributes.new(name,kind,'POINT')
        for item,value in zip(attr.data,values): item.value=value
    guide=bpy.data.objects.new(source.name+' • LIVE FROND GUIDES',mesh)
    (source.users_collection[0] if source.users_collection else bpy.context.scene.collection).objects.link(guide)
    guide.parent=source
    guide['lp_tree_frond_guide']=True
    guide.display_type='WIRE'
    guide.hide_set(True)
    return guide


def commit(source,builder,settings,slots,materials,anchors):
    """Replace the source with wood plus live fronds after staging succeeds."""
    if not enabled(settings): raise ValueError('Live Tree fronds require an arranged Leaf Type or Broad Lamina')
    mesh_controller=bool(settings.controller and settings.controller.type=='MESH')
    mode=live_surface.supported(settings) if mesh_controller else 'Path'
    old_guides=[child for child in source.children if child.get('lp_tree_frond_guide')]
    objects_before=set(bpy.data.objects)
    groups_before=set(bpy.data.node_groups)
    guide=None; staged=None; committed=False
    try:
        if not mesh_controller: guide=_guide(source,settings,anchors)
        staged=bpy.data.objects.new(source.name+' • Staged Wood',bpy.data.meshes.new('Staged Wood'))
        staged['lp_branch_graph']=source.get('lp_branch_graph','')
        builder.finish(staged,materials)
        if settings.pattern=='Banana':
            from . import live_banana
            group=live_banana.group(source,settings,slots,materials,mode,tree_guide=guide)
        else:
            prototypes=[live_surface._prototype(source,index,slot,materials[index+1],settings)
                        for index,slot in enumerate(slots)]
            group=live_surface._group(source,settings,slots,prototypes,materials,mode,tree_guide=guide)
        old_mesh=source.data
        instance_cards.clear(source)
        old_wind=source.modifiers.get('Landscapy Wind')
        if old_wind:
            wind_group=old_wind.node_group
            source.modifiers.remove(old_wind)
            if wind_group and wind_group.users==0: bpy.data.node_groups.remove(wind_group)
        source.data=staged.data
        source.data.name=source.name+' • Live Tree Wood'
        modifier=source.modifiers.new(instance_cards.NAME,'NODES')
        modifier.node_group=group
        source['lp_live_mode']='Tree'+mode
        committed=True
        bpy.data.objects.remove(staged,do_unlink=True); staged=None
        if old_mesh and old_mesh.users==0: bpy.data.meshes.remove(old_mesh)
        for old in old_guides:
            mesh=old.data
            bpy.data.objects.remove(old,do_unlink=True)
            if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)
    finally:
        if not committed:
            if staged:
                mesh=staged.data
                bpy.data.objects.remove(staged,do_unlink=True)
                if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)
            if guide:
                mesh=guide.data
                bpy.data.objects.remove(guide,do_unlink=True)
                if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)
            for created in set(bpy.data.node_groups)-groups_before:
                if created.users==0: bpy.data.node_groups.remove(created)
            for created in set(bpy.data.objects)-objects_before:
                if created.users==0:
                    mesh=created.data
                    bpy.data.objects.remove(created,do_unlink=True)
                    if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)
