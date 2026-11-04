"""Sample a mesh controller in Geometry Nodes and return card anchors.

The returned anchors still feed the existing card shape and texture pipeline.
Temporary Blender data is removed before the generator commits its mesh.
"""
import bpy
from mathutils import Vector


def points(settings,controller,owner,evaluated_mesh,group):
    """World-area Surface/Carpet sampling with optional Poisson spacing."""
    # Match the rendered triangle layout, including the split of warped quads.
    mesh=bpy.data.meshes.new('LP Temporary Surface Distribution Mesh')
    mesh.from_pydata([vertex.co.copy() for vertex in evaluated_mesh.vertices],[],
                     [tuple(triangle.vertices) for triangle in evaluated_mesh.loop_triangles])
    mesh.update()
    temporary=None
    nodes=None
    evaluated=None
    try:
        mesh.name='LP Temporary Surface Distribution Mesh'
        mesh.transform(controller.matrix_world)
        if group:
            mask=mesh.attributes.new('lp_distribution_mask','FLOAT','POINT')
            for index,item in enumerate(mask.data):
                try: item.value=max(0.,min(1.,group.weight(index)))
                except RuntimeError: item.value=0.
        temporary=bpy.data.objects.new('LP Temporary Surface Distribution',mesh)
        bpy.context.scene.collection.objects.link(temporary)
        nodes=bpy.data.node_groups.new('LP Temporary Surface Points','GeometryNodeTree')
        nodes.is_modifier=True
        nodes.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
        nodes.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
        n=nodes.nodes; link=nodes.links.new
        input_node=n.new('NodeGroupInput'); output=n.new('NodeGroupOutput')
        scatter=n.new('GeometryNodeDistributePointsOnFaces')
        scatter.distribute_method='POISSON' if settings.spacing>0 else 'RANDOM'
        scatter.inputs['Seed'].default_value=settings.seed
        if settings.spacing>0:
            scatter.inputs['Density Max'].default_value=settings.density
            scatter.inputs['Distance Min'].default_value=settings.spacing
        else:
            scatter.inputs['Density'].default_value=settings.density
        link(input_node.outputs['Geometry'],scatter.inputs['Mesh'])
        if group:
            weight=n.new('GeometryNodeInputNamedAttribute'); weight.data_type='FLOAT'
            weight.inputs['Name'].default_value='lp_distribution_mask'
            if settings.spacing>0:
                link(weight.outputs['Attribute'],scatter.inputs['Density Factor'])
            else:
                multiply=n.new('ShaderNodeMath'); multiply.operation='MULTIPLY'
                multiply.inputs[1].default_value=settings.density
                link(weight.outputs['Attribute'],multiply.inputs[0])
                link(multiply.outputs[0],scatter.inputs['Density'])
        store=n.new('GeometryNodeStoreNamedAttribute')
        store.data_type='FLOAT_VECTOR'; store.domain='POINT'
        store.inputs['Name'].default_value='lp_distribution_normal'
        link(scatter.outputs['Points'],store.inputs['Geometry'])
        surface_normal=n.new('GeometryNodeInputNormal')
        nearest=n.new('GeometryNodeSampleNearestSurface'); nearest.data_type='FLOAT_VECTOR'
        link(input_node.outputs['Geometry'],nearest.inputs['Mesh'])
        link(surface_normal.outputs['Normal'],nearest.inputs['Value'])
        position=n.new('GeometryNodeInputPosition')
        link(position.outputs['Position'],nearest.inputs['Sample Position'])
        link(nearest.outputs['Value'],store.inputs['Value'])
        limited=n.new('GeometryNodeDeleteGeometry'); limited.domain='POINT'; limited.mode='ALL'
        link(store.outputs['Geometry'],limited.inputs['Geometry'])
        index=n.new('GeometryNodeInputIndex')
        compare=n.new('FunctionNodeCompare'); compare.data_type='INT'; compare.operation='GREATER_EQUAL'
        compare.inputs[1].default_value=settings.limit
        link(index.outputs['Index'],compare.inputs[0])
        link(compare.outputs[0],limited.inputs['Selection'])
        convert=n.new('GeometryNodePointsToVertices')
        link(limited.outputs['Geometry'],convert.inputs['Points'])
        link(convert.outputs['Mesh'],output.inputs['Geometry'])
        modifier=temporary.modifiers.new('LP Surface Distribution','NODES')
        modifier.node_group=nodes
        bpy.context.view_layer.update()
        depsgraph=bpy.context.evaluated_depsgraph_get(); depsgraph.update()
        evaluated=temporary.evaluated_get(depsgraph)
        result=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=depsgraph)
        normals=result.attributes.get('lp_distribution_normal')
        if not normals and result.vertices:
            raise RuntimeError('Geometry Nodes surface distribution did not preserve normals')
        inverse=owner.matrix_world.inverted()
        # The card's local Z is a growth direction, so invert the owner
        # transform as a vector rather than transforming a shading normal.
        normal_matrix=owner.matrix_world.to_3x3().inverted()
        anchors=[]
        for index,vertex in enumerate(result.vertices):
            normal=Vector(normals.data[index].vector) if normals else Vector((0,0,1))
            anchors.append((inverse@vertex.co,(normal_matrix@normal).normalized()))
        return anchors
    finally:
        if evaluated: evaluated.to_mesh_clear()
        if temporary: bpy.data.objects.remove(temporary,do_unlink=True)
        if nodes and nodes.users==0: bpy.data.node_groups.remove(nodes)
        if mesh.users==0: bpy.data.meshes.remove(mesh)
