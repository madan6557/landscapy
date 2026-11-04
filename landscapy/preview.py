"""Viewport-only card thinning on a separate proxy; source topology stays intact."""
import bpy

NAME = 'Landscapy Preview Density'


def owned(source):
    return [ob for ob in bpy.data.objects if ob.parent == source and ob.get('lp_preview_owner')]


def _remove(source):
    for ob in owned(source):
        groups = [mod.node_group for mod in ob.modifiers if mod.type == 'NODES' and mod.node_group]
        bpy.data.objects.remove(ob, do_unlink=True)
        for group in groups:
            if group.users == 0: bpy.data.node_groups.remove(group)
    if 'lp_preview_display_type' in source:
        source.display_type = source['lp_preview_display_type']
        del source['lp_preview_display_type']


def _modifier(proxy, ratio):
    group = bpy.data.node_groups.new('LP Preview ' + proxy.name, 'GeometryNodeTree')
    group.is_modifier = True
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes = group.nodes
    link = group.links.new
    input_node = nodes.new('NodeGroupInput')
    output_node = nodes.new('NodeGroupOutput')
    ids = nodes.new('GeometryNodeInputNamedAttribute')
    ids.data_type = 'INT'
    ids.inputs['Name'].default_value = 'lp_card_id'
    card = nodes.new('GeometryNodeInputNamedAttribute')
    card.data_type = 'BOOLEAN'
    card.inputs['Name'].default_value = 'lp_card'
    random = nodes.new('FunctionNodeRandomValue')
    random.data_type = 'FLOAT'
    random.inputs['Min'].default_value = 0
    random.inputs['Max'].default_value = 1
    link(ids.outputs['Attribute'], random.inputs['ID'])
    amount = nodes.new('ShaderNodeValue')
    amount.name = 'Preview Ratio'
    amount.outputs[0].default_value = ratio
    excess = nodes.new('FunctionNodeCompare')
    excess.data_type = 'FLOAT'
    excess.operation = 'GREATER_THAN'
    link(random.outputs['Value'], excess.inputs[0])
    link(amount.outputs[0], excess.inputs[1])
    select = nodes.new('FunctionNodeBooleanMath')
    select.operation = 'AND'
    link(card.outputs['Attribute'], select.inputs[0])
    link(excess.outputs[0], select.inputs[1])
    delete = nodes.new('GeometryNodeDeleteGeometry')
    delete.domain = 'FACE'
    delete.mode = 'ALL'
    link(input_node.outputs[0], delete.inputs['Geometry'])
    link(select.outputs[0], delete.inputs['Selection'])
    link(delete.outputs[0], output_node.inputs[0])
    mod = proxy.modifiers.new(NAME, 'NODES')
    mod.node_group = group
    mod.show_render = False


def _instance_ornament_proxy(source,settings,force):
    """Show thin cards while the real target keeps full topology for binding."""
    from . import instance_cards
    proxies=owned(source)
    if not settings.preview_enabled or settings.preview_ratio>=1:
        _remove(source)
        return
    if not force and len(proxies)==1 and proxies[0].data==source.data:
        ratio=instance_cards.ratio_node(proxies[0])
        if ratio:
            ratio.outputs[0].default_value=settings.preview_ratio
            ratio.id_data.update_tag()
            proxies[0].update_tag(refresh={'OBJECT'})
            return
    _remove(source)
    source['lp_preview_display_type']=source.display_type
    source.display_type='BOUNDS'
    proxy=source.copy()
    proxy.data=source.data
    proxy.name=source.name+' • Preview'
    source.users_collection[0].objects.link(proxy)
    proxy.parent=source
    proxy.matrix_parent_inverse=source.matrix_world.inverted()
    proxy.landscapy.uid=''
    if 'lp_binding_signature' in proxy: del proxy['lp_binding_signature']
    proxy['lp_preview_owner']=settings.uid
    proxy.hide_render=True
    proxy.hide_select=True
    proxy.display_type='TEXTURED'
    mod=instance_cards.modifier(proxy)
    mod.node_group=mod.node_group.copy()
    ratio=instance_cards.ratio_node(proxy)
    ratio.outputs[0].default_value=settings.preview_ratio
    ratio.id_data.update_tag()


def sync(source, force=False):
    """Refresh a proxy after regeneration or change only its ratio node."""
    if not source or source.type != 'MESH' or not source.landscapy.uid:
        return
    settings = source.landscapy

    from . import instance_cards
    if settings.live_surface:
        from . import live_surface
        live_surface.localize(source)
    ratio=instance_cards.ratio_node(source)
    if ratio:
        mod=instance_cards.modifier(source)
        if mod.node_group.users>1:
            mod.node_group=mod.node_group.copy()
            ratio=instance_cards.ratio_node(source)
        bound_ornaments=any(ob.get('lp_ornament_owner')==settings.uid and not ob.get('lp_variant')
                            for ob in bpy.data.objects)
        if settings.ornaments_enabled or bound_ornaments:
            ratio.outputs[0].default_value=1.
            ratio.id_data.update_tag()
            source.update_tag(refresh={'OBJECT'})
            _instance_ornament_proxy(source,settings,force)
            return
        _remove(source)
        ratio.outputs[0].default_value=settings.preview_ratio if settings.preview_enabled else 1.
        ratio.id_data.update_tag()
        source.update_tag(refresh={'OBJECT'})
        return
    active = settings.kind in {'Tree', 'Foliage', 'Ivy'} and settings.preview_enabled and settings.preview_ratio < 1
    proxies = owned(source)
    if not active or not source.data or not source.data.polygons:
        _remove(source)
        return
    if not force and len(proxies) == 1 and proxies[0].data == source.data:
        mod = proxies[0].modifiers.get(NAME)
        if mod and mod.node_group:
            mod.node_group.nodes['Preview Ratio'].outputs[0].default_value = settings.preview_ratio
            mod.node_group.update_tag()
            proxies[0].update_tag(refresh={'OBJECT'})
            return
    _remove(source)
    source['lp_preview_display_type'] = source.display_type
    source.display_type = 'BOUNDS'
    proxy = source.copy()
    proxy.data = source.data
    proxy.name = source.name + ' • Preview'
    source.users_collection[0].objects.link(proxy)
    proxy.parent = source
    proxy.matrix_parent_inverse = source.matrix_world.inverted()
    proxy.landscapy.uid = ''
    if 'lp_binding_signature' in proxy:
        del proxy['lp_binding_signature']
    proxy['lp_preview_owner'] = settings.uid
    proxy.hide_render = True
    proxy.hide_select = True
    proxy.display_type = 'TEXTURED'
    _modifier(proxy, settings.preview_ratio)

