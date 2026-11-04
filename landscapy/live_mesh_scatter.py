"""Mesh Surface/Volume point distribution shared by live foliage generators."""
import bpy


def points(nodes,link,driver,number,settings,mode,geometry,triangulated_mesh):
    """Return points and the orientation/spacing nodes needed by callers."""
    if mode=='Surface':
        scatter=nodes.new('GeometryNodeDistributePointsOnFaces')
        scatter.distribute_method='POISSON'
        link(triangulated_mesh,scatter.inputs['Mesh'])
        driver(scatter.inputs['Density Max'],'density')
        driver(scatter.inputs['Distance Min'],'spacing')
        driver(scatter.inputs['Seed'],'seed')
        if settings.mask:
            weight=nodes.new('GeometryNodeInputNamedAttribute'); weight.data_type='FLOAT'
            weight.inputs['Name'].default_value=settings.mask
            link(weight.outputs['Attribute'],scatter.inputs['Density Factor'])
        return scatter.outputs['Points'],scatter,None,None

    volume=nodes.new('GeometryNodeMeshToVolume')
    volume.inputs['Resolution Mode'].default_value='Amount'
    driver(volume.inputs['Voxel Amount'],'live_volume_grid_cells')
    link(geometry,volume.inputs['Mesh'])
    random_points=nodes.new('GeometryNodeDistributePointsInVolume')
    random_points.inputs['Mode'].default_value='Random'
    link(volume.outputs['Volume'],random_points.inputs['Volume'])
    driver(random_points.inputs['Density'],'density')
    driver(random_points.inputs['Seed'],'seed')
    grid=nodes.new('GeometryNodeDistributePointsInVolume')
    grid.inputs['Mode'].default_value='Grid'
    link(volume.outputs['Volume'],grid.inputs['Volume'])
    bounds=nodes.new('GeometryNodeBoundBox')
    link(geometry,bounds.inputs['Geometry'])
    extent=nodes.new('ShaderNodeVectorMath'); extent.operation='SUBTRACT'
    link(bounds.outputs['Max'],extent.inputs[0]); link(bounds.outputs['Min'],extent.inputs[1])
    diagonal=nodes.new('ShaderNodeVectorMath'); diagonal.operation='LENGTH'
    link(extent.outputs[0],diagonal.inputs[0])
    requested=nodes.new('ShaderNodeValue'); driver(requested.outputs[0],'spacing')
    grid_detail=nodes.new('ShaderNodeValue'); driver(grid_detail.outputs[0],'live_volume_grid_cells')
    effective=number('MAXIMUM',requested.outputs[0],number('MAXIMUM',.02,number('DIVIDE',diagonal.outputs['Value'],grid_detail.outputs[0])))
    grid_spacing=nodes.new('ShaderNodeCombineXYZ')
    for axis in ('X','Y','Z'): link(effective,grid_spacing.inputs[axis])
    link(grid_spacing.outputs[0],grid.inputs['Spacing'])
    density=nodes.new('ShaderNodeValue'); driver(density.outputs[0],'density')
    grid_rate=number('MINIMUM',1.,number('MULTIPLY',density.outputs[0],number('POWER',effective,3.)))
    volume_index=nodes.new('GeometryNodeInputIndex')
    mask=None
    if settings.mask:
        weight=nodes.new('GeometryNodeInputNamedAttribute'); weight.data_type='FLOAT'
        weight.inputs['Name'].default_value=settings.mask
        nearest=nodes.new('GeometryNodeSampleNearestSurface'); nearest.data_type='FLOAT'
        link(triangulated_mesh,nearest.inputs['Mesh'])
        link(weight.outputs['Attribute'],nearest.inputs['Value'])
        position=nodes.new('GeometryNodeInputPosition')
        link(position.outputs['Position'],nearest.inputs['Sample Position'])
        mask=nearest.outputs['Value']

    def thin_volume(geometry_points,rate,offset):
        chance=nodes.new('FunctionNodeRandomValue'); chance.data_type='FLOAT'
        chance.inputs['Min'].default_value=0; chance.inputs['Max'].default_value=1
        driver(chance.inputs['Seed'],'seed',offset)
        link(volume_index.outputs['Index'],chance.inputs['ID'])
        probability=number('MULTIPLY',rate,mask) if mask else rate
        excess=nodes.new('FunctionNodeCompare'); excess.data_type='FLOAT'; excess.operation='GREATER_THAN'
        link(chance.outputs['Value'],excess.inputs[0]); link(probability,excess.inputs[1])
        delete=nodes.new('GeometryNodeDeleteGeometry'); delete.domain='POINT'; delete.mode='ALL'
        link(geometry_points,delete.inputs['Geometry']); link(excess.outputs[0],delete.inputs['Selection'])
        return delete.outputs['Geometry']

    random_geometry=thin_volume(random_points.outputs['Points'],number('ADD',1.,0.),912) if mask else random_points.outputs['Points']
    grid_geometry=thin_volume(grid.outputs['Points'],grid_rate,913)
    choose_grid=nodes.new('FunctionNodeCompare'); choose_grid.data_type='FLOAT'; choose_grid.operation='GREATER_THAN'
    link(requested.outputs[0],choose_grid.inputs[0]); choose_grid.inputs[1].default_value=.000001
    switch=nodes.new('GeometryNodeSwitch'); switch.input_type='GEOMETRY'
    link(choose_grid.outputs[0],switch.inputs['Switch'])
    link(random_geometry,switch.inputs['False']); link(grid_geometry,switch.inputs['True'])
    return switch.outputs[0],None,choose_grid,effective


def volume_rotation(nodes,link,driver,number,random,settings,ids,triangulated_mesh,position):
    """Blend random frond directions toward the closest surface normal."""
    axis=random('FLOAT_VECTOR',(-3.141592653589793,)*3,(3.141592653589793,)*3,
                settings.rotation_seed+707,ids,'rotation_seed',707)
    random_axis=nodes.new('FunctionNodeEulerToRotation')
    link(axis,random_axis.inputs['Euler'])
    random_direction=nodes.new('FunctionNodeRotateVector')
    random_direction.inputs['Vector'].default_value=(0,0,1)
    link(random_axis.outputs['Rotation'],random_direction.inputs['Rotation'])
    nearest=nodes.new('GeometryNodeSampleNearestSurface'); nearest.data_type='FLOAT_VECTOR'
    link(triangulated_mesh,nearest.inputs['Mesh'])
    normal=nodes.new('GeometryNodeInputNormal')
    link(normal.outputs['Normal'],nearest.inputs['Value'])
    link(position,nearest.inputs['Sample Position'])
    alignment=nodes.new('ShaderNodeValue'); driver(alignment.outputs[0],'canopy_alignment')
    random_weight=nodes.new('ShaderNodeVectorMath'); random_weight.operation='SCALE'
    link(random_direction.outputs['Vector'],random_weight.inputs[0])
    link(number('SUBTRACT',1.,alignment.outputs[0]),random_weight.inputs['Scale'])
    outward_weight=nodes.new('ShaderNodeVectorMath'); outward_weight.operation='SCALE'
    link(nearest.outputs['Value'],outward_weight.inputs[0])
    link(alignment.outputs[0],outward_weight.inputs['Scale'])
    direction=nodes.new('ShaderNodeVectorMath'); direction.operation='ADD'
    link(random_weight.outputs[0],direction.inputs[0]); link(outward_weight.outputs[0],direction.inputs[1])
    base_axis=nodes.new('FunctionNodeAlignRotationToVector'); base_axis.axis='Z'
    link(direction.outputs[0],base_axis.inputs['Vector'])
    return base_axis.outputs['Rotation']
