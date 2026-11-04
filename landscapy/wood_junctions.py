"""Fuse tree wood before creating any of the image cards."""
import bpy


def fuse(builder):
    if not builder.f or len(set(builder.branch_ids)) < 2:
        return

    source = bpy.data.meshes.new('Landscapy junction input')
    staging = bpy.data.objects.new('Landscapy junction input', source)
    operand = bpy.data.collections.new('Landscapy empty union operand')
    evaluated = None
    try:
        source.from_pydata(builder.v, [], builder.f)
        source.update()
        uv = source.uv_layers.new(name='UVMap')
        uv.data.foreach_set('uv', [coordinate for pair in builder.uv for coordinate in pair])
        attributes = (
            ('lp_branch_id', 'INT', builder.branch_ids),
            ('lp_branch_level', 'INT', builder.branch_levels),
            ('lp_branch_t', 'FLOAT', builder.branch_t),
        )
        for name, data_type, values in attributes:
            source.attributes.new(name, data_type, 'POINT').data.foreach_set('value', values)
        bpy.context.scene.collection.objects.link(staging)
        modifier = staging.modifiers.new('Fuse wood surfaces', 'BOOLEAN')
        modifier.operation = 'UNION'
        modifier.solver = 'EXACT'
        modifier.operand_type = 'COLLECTION'
        modifier.collection = operand
        modifier.use_self = True
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = staging.evaluated_get(depsgraph)
        joined = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        if not joined or not joined.polygons:
            raise ValueError('Wood junction union produced no surface. Check the tree guides or turn off Join Wood Junctions.')

        vertices = [tuple(vertex.co) for vertex in joined.vertices]
        faces = [tuple(face.vertices) for face in joined.polygons]
        joined_uv = [tuple(loop.uv) for loop in joined.uv_layers['UVMap'].data]
        ids = [item.value for item in joined.attributes['lp_branch_id'].data]
        levels = {branch_id: level for branch_id, level in zip(builder.branch_ids, builder.branch_levels)}
        positions = [min(1., max(0., item.value)) for item in joined.attributes['lp_branch_t'].data]

        # Reuse the same builder for cards and wind. Face UVs on the wood
        # remain in their original local branch charts.
        detail, wind_scale = builder.detail_scale, builder.cluster_wind_scale
        builder.__init__(detail)
        builder.cluster_wind_scale = wind_scale
        builder.add(vertices, faces, uv=[(0., 0.)] * len(vertices))
        builder.uv = joined_uv
        builder.branch_ids = ids
        builder.branch_levels = [levels.get(branch_id, -1) for branch_id in ids]
        builder.branch_t = positions
    finally:
        if evaluated is not None:
            evaluated.to_mesh_clear()
        bpy.data.objects.remove(staging, do_unlink=True)
        bpy.data.collections.remove(operand)
        bpy.data.meshes.remove(source)
