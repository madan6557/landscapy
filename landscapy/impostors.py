"""Eight azimuth GPU impostor atlas, camera/viewport selection, and metadata."""
import bpy, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from bpy.app.handlers import persistent
from .bake_edges import dilate_rgba

NAME='Landscapy Impostor View'
_updating=False
_rendering=False
_viewport_active=False
_force_viewport=True
_region_matrices={}

def atlas(scene,cam,center,extent,directory,uid,suffix,normal=False):
    tile=scene.render.resolution_x
    pixels=np.zeros((tile*2,tile*4,4),dtype=np.float32)
    for view in range(8):
        angle=view*math.tau/8
        direction=Vector((math.sin(angle),-math.cos(angle),0))
        cam.location=center+direction*extent*3
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        temporary=directory/(uid+'_'+suffix+'_view'+str(view)+'.png')
        scene.render.filepath=str(temporary)
        bpy.ops.render.render(write_still=True,scene=scene.name)
        image=bpy.data.images.load(str(temporary),check_existing=False)
        try:
            if normal: image.colorspace_settings.name='Non-Color'
            values=np.empty(len(image.pixels),dtype=np.float32)
            image.pixels.foreach_get(values)
            block=dilate_rgba(values.reshape(tile,tile,4),8)
            pixels[view//4*tile:(view//4+1)*tile,view%4*tile:(view%4+1)*tile]=block
        finally:
            bpy.data.images.remove(image)
            temporary.unlink(missing_ok=True)
    path=directory/(uid+'_impostor_'+suffix+'.png')
    result=bpy.data.images.new('LP '+uid+' '+suffix+' Atlas',width=tile*4,height=tile*2,alpha=True)
    if normal: result.colorspace_settings.name='Non-Color'
    result.pixels.foreach_set(pixels.reshape(-1))
    result.update(); result.filepath_raw=str(path); result.file_format='PNG'; result.save(); result.pack()
    return result,path

def metadata(source,extent,center,tile,color_path,normal_path):
    return {
        'schema':1,'source_uid':source.landscapy.uid,'mode':'azimuth_8',
        'atlas_color':color_path.name,'atlas_normal':normal_path.name if normal_path else None,
        'atlas_size':[tile*4,tile*2],'tile_size':[tile,tile],
        'billboard_extent':extent,'center_local':list(center),
        'angle_convention':'0 degrees views from local -Y; angles increase about local +Z toward +X',
        'normal_space':'tangent; each tile uses that view camera right/up/toward-camera axes' if normal_path else None,
        'views':[{'index':i,'azimuth_degrees':i*45,
                  'view_direction_local':[round(math.sin(i*math.tau/8),7),round(-math.cos(i*math.tau/8),7),0],
                  'uv_rect':[i%4/4,i//4/2,(i%4+1)/4,(i//4+1)/2]} for i in range(8)],
    }

def modifier(ob):
    group=bpy.data.node_groups.new('LP Impostor '+ob.name,'GeometryNodeTree')
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=group.nodes; links=group.links.new
    inp=nodes.new('NodeGroupInput'); output=nodes.new('NodeGroupOutput')
    attribute=nodes.new('GeometryNodeInputNamedAttribute'); attribute.data_type='INT'; attribute.inputs['Name'].default_value='lp_impostor_view'
    value=nodes.new('ShaderNodeValue'); value.name='Active View'
    compare=nodes.new('FunctionNodeCompare'); compare.data_type='INT'; compare.operation='NOT_EQUAL'
    links(attribute.outputs['Attribute'],compare.inputs[0]); links(value.outputs[0],compare.inputs[1])
    delete=nodes.new('GeometryNodeDeleteGeometry'); delete.domain='FACE'; delete.mode='ALL'
    links(inp.outputs[0],delete.inputs['Geometry']); links(compare.outputs[0],delete.inputs['Selection']); links(delete.outputs[0],output.inputs[0])
    mod=ob.modifiers.new(NAME,'NODES'); mod.node_group=group

def billboard(source,col,center,extent,image,normal_image,meta):
    from . import mesh_object,billboard_material
    half=extent*.5; vertices=[]; faces=[]
    for view in range(8):
        rotation=Matrix.Rotation(view*math.tau/8,3,'Z')
        vertices.extend(center+rotation@Vector((x,0,z)) for x,z in [(-half,-half),(half,-half),(half,half),(-half,half)])
        faces.append(tuple(view*4+j for j in range(4)))
    ob=mesh_object(source.name+' • Flat 8 Views',vertices,faces,col,billboard_material(image,lit=bool(normal_image)))
    uv=ob.data.uv_layers.new(name='UVMap')
    for view in range(8):
        x=view%4/4; y=view//4/2
        for j,(u,v) in enumerate([(0,0),(1,0),(1,1),(0,1)]):
            uv.data[view*4+j].uv=(x+u/4,y+v/2)
    a=ob.data.attributes.new('lp_impostor_view','INT','FACE')
    for i,d in enumerate(a.data): d.value=i
    a=ob.data.attributes.new('lp_color','FLOAT_COLOR','POINT')
    for d in a.data: d.color=(1,1,1,1)
    a=ob.data.attributes.new('lp_opacity','FLOAT','POINT')
    for d in a.data: d.value=1
    a=ob.data.attributes.new('lp_wind','FLOAT','POINT')
    for i,d in enumerate(a.data): d.value=0 if i%4<2 else 1
    if normal_image:
        tree=ob.data.materials[0].node_tree; tex=tree.nodes.new('ShaderNodeTexImage'); tex.image=normal_image
        normal=tree.nodes.new('ShaderNodeNormalMap'); tree.links.new(tex.outputs['Color'],normal.inputs['Color'])
        tree.links.new(normal.outputs[0],tree.nodes['Principled BSDF'].inputs['Normal'])
    ob.matrix_world=source.matrix_world.copy()
    ob['lp_impostor_mode']='MULTI8'; ob['lp_impostor_active']=0; ob['lp_impostor_center']=list(center)
    ob['lp_impostor_info']=json.dumps(meta,separators=(',',':'))
    modifier(ob)
    return ob

def _select(scene, point=None, direction=None):
    global _updating
    if _updating or not scene or (point is None and direction is None): return
    _updating=True
    try:
        for ob in scene.objects:
            if ob.get('lp_impostor_mode')!='MULTI8': continue
            center=ob.matrix_world@Vector(ob['lp_impostor_center'])
            local=ob.matrix_world.to_3x3().inverted()@(point-center if point is not None else direction)
            if local.xy.length<1e-6: continue
            angle=math.atan2(local.x,-local.y)
            index=round(angle/(math.tau/8))%8
            if ob.get('lp_impostor_active')!=index:
                ob['lp_impostor_active']=index
                mod=ob.modifiers.get(NAME)
                if mod and mod.node_group:
                    mod.node_group.nodes['Active View'].outputs[0].default_value=index
                    mod.node_group.update_tag()
                ob.update_tag(refresh={'OBJECT'})
    finally: _updating=False

def update(scene):
    """Select the view for the scene camera, including headless renders."""
    if scene and scene.camera: _select(scene,point=scene.camera.matrix_world.translation)

def update_viewport(scene,region):
    """Select from a 3D viewport's perspective or orthographic direction."""
    if region.view_perspective=='CAMERA':
        update(scene)
    elif region.view_perspective=='ORTHO':
        _select(scene,direction=region.view_matrix.inverted().to_3x3()@Vector((0,0,1)))
    else:
        _select(scene,point=region.view_matrix.inverted().translation)

def poll_viewports():
    global _viewport_active,_force_viewport,_region_matrices
    if _rendering: return .15
    current={}; chosen=None; first=None
    manager=bpy.context.window_manager
    if not manager: return .15
    for window in manager.windows:
        scene=window.scene
        for area in window.screen.areas:
            if area.type!='VIEW_3D': continue
            region=area.spaces.active.region_3d
            key=area.as_pointer()
            matrix=tuple(round(x,7) for row in region.view_matrix for x in row)
            current[key]=matrix
            if first is None: first=(scene,region)
            if _region_matrices.get(key)!=matrix: chosen=(scene,region)
    _viewport_active=first is not None
    if chosen is None and _force_viewport: chosen=first
    _region_matrices=current
    _force_viewport=False
    if chosen: update_viewport(*chosen)
    return .15

@persistent
def on_depsgraph(scene,depsgraph):
    if not _rendering and not _viewport_active: update(scene)

@persistent
def on_load(dummy):
    global _force_viewport
    _force_viewport=True
    for scene in bpy.data.scenes: update(scene)

@persistent
def on_render_pre(scene):
    global _rendering
    _rendering=True
    update(scene)

@persistent
def on_render_end(scene):
    global _rendering,_force_viewport
    _rendering=False
    _force_viewport=True

def register():
    if on_depsgraph not in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.append(on_depsgraph)
    if on_load not in bpy.app.handlers.load_post: bpy.app.handlers.load_post.append(on_load)
    if on_render_pre not in bpy.app.handlers.render_pre: bpy.app.handlers.render_pre.append(on_render_pre)
    for handler in (bpy.app.handlers.render_complete,bpy.app.handlers.render_cancel):
        if on_render_end not in handler: handler.append(on_render_end)
    if not bpy.app.timers.is_registered(poll_viewports): bpy.app.timers.register(poll_viewports,first_interval=.15,persistent=True)

def unregister():
    global _rendering,_viewport_active,_force_viewport
    if on_depsgraph in bpy.app.handlers.depsgraph_update_post: bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph)
    if on_load in bpy.app.handlers.load_post: bpy.app.handlers.load_post.remove(on_load)
    if on_render_pre in bpy.app.handlers.render_pre: bpy.app.handlers.render_pre.remove(on_render_pre)
    for handler in (bpy.app.handlers.render_complete,bpy.app.handlers.render_cancel):
        if on_render_end in handler: handler.remove(on_render_end)
    if bpy.app.timers.is_registered(poll_viewports): bpy.app.timers.unregister(poll_viewports)
    _rendering=False; _viewport_active=False; _force_viewport=True; _region_matrices.clear()
