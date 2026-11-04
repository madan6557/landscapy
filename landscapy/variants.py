"""Non-destructive variant output. GPU-only transparent billboard bake."""
import bpy
import math
import json
import os
from pathlib import Path
from mathutils import Vector
from bpy.props import BoolProperty

def gpu(scene):
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use=d.type=='OPTIX'
    if not any(d.use and d.type=='OPTIX' for d in prefs.devices): raise RuntimeError('OptiX GPU required. CPU fallback is disabled.')
    scene.render.engine='CYCLES'; scene.cycles.device='GPU'; scene.cycles.samples=32; scene.cycles.use_denoising=True; scene.cycles.transparent_max_bounces=32

def collection(scene,name):
    col=bpy.data.collections.get(name)
    if not col: col=bpy.data.collections.new(name); scene.collection.children.link(col)
    col['lp_output']=True
    return col

def bake_directory(settings):
    configured=settings.bake_directory.strip() or '//Landscapy_Bakes'
    if configured.startswith('//') and not bpy.data.filepath:
        test_directory=os.environ.get('LANDSCAPY_BAKE_DIR')
        if test_directory: return Path(test_directory).expanduser().resolve()
        raise RuntimeError('Save the .blend file or choose an absolute Flat Bake Directory before Build Variants')
    if not configured.startswith('//') and not Path(configured).is_absolute():
        raise ValueError('Flat Bake Directory must be absolute or begin with //')
    return Path(bpy.path.abspath(configured)).expanduser().resolve()

def flat(source,col,directory):
    from . import mesh_object, billboard_material, wind_modifier, ornaments
    from . import instance_cards
    from .bake_edges import save_dilated
    from . import impostors
    original_scene=bpy.context.window.scene
    ratio_node=instance_cards.ratio_node(source)
    old_ratio=ratio_node.outputs[0].default_value if ratio_node else None
    if ratio_node: ratio_node.outputs[0].default_value=1
    scene=bpy.data.scenes.new('_Landscapy GPU Bake'); created=[]; temporary_materials=[]
    try:
        gpu(scene); scene.render.resolution_x=scene.render.resolution_y=int(source.landscapy.resolution); scene.render.resolution_percentage=100
        scene.render.film_transparent=True; scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
        scene.world=bpy.data.worlds.new('_LP Bake World'); scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
        subjects=[]
        wind_visibility=[(modifier,modifier.show_viewport,modifier.show_render)
                         for subject in [source,*ornaments.owned(source)]
                         for modifier in [subject.modifiers.get('Landscapy Wind')] if modifier]
        try:
            for modifier,_,_ in wind_visibility: modifier.show_viewport=False; modifier.show_render=False
            bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get(); dg.update()
            for subject in [source,*ornaments.owned(source)]:
                snapshot=bpy.data.meshes.new_from_object(subject.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
                ob=bpy.data.objects.new('_LP Bake '+subject.name,snapshot); scene.collection.objects.link(ob); created.append(ob); subjects.append(ob)
                ob.matrix_world=source.matrix_world.inverted()@subject.matrix_world
        finally:
            for modifier,viewport,render in wind_visibility:
                modifier.show_viewport=viewport; modifier.show_render=render
        corners=[ob.matrix_world@Vector(c) for ob in subjects for c in ob.bound_box]; low=Vector([min(c[i] for c in corners) for i in range(3)]); high=Vector([max(c[i] for c in corners) for i in range(3)]); center=(low+high)*.5
        extent=max(high-low)*1.15
        cam=bpy.data.objects.new('_LP Bake Camera',bpy.data.cameras.new('_LP Bake Camera')); scene.collection.objects.link(cam); created.append(cam)
        cam.location=center+Vector((0,-extent*3,0)); cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=extent; scene.camera=cam
        lamp=bpy.data.objects.new('_LP Bake Light',bpy.data.lights.new('_LP Bake Light','AREA')); scene.collection.objects.link(lamp); created.append(lamp); lamp.location=center+Vector((-extent,-extent,extent)); lamp.rotation_euler=(center-lamp.location).to_track_quat('-Z','Y').to_euler(); lamp.data.energy=extent*extent*60; lamp.data.size=extent*2
        directory.mkdir(parents=True,exist_ok=True); path=directory/(source.landscapy.uid+'_flat.png')
        multi=source.landscapy.flat_mode=='MULTI8'; tile=scene.render.resolution_x
        if multi: image,color_path=impostors.atlas(scene,cam,center,extent,directory,source.landscapy.uid,'color')
        else:
            scene.render.filepath=str(path); bpy.ops.render.render(write_still=True,scene=scene.name)
            image=bpy.data.images.load(str(path),check_existing=True); save_dilated(image,path)
        normal_image=None
        normal_path=None
        if source.landscapy.with_normals:
            for ob,index,original in [(obj,i,m) for obj in subjects for i,m in enumerate(list(obj.data.materials)) if m]:
                m=original.copy(); temporary_materials.append(m); m.use_nodes=True; nt=m.node_tree; n=nt.nodes; L=nt.links.new
                output=next((x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output),None) or n.new('ShaderNodeOutputMaterial')
                principled=next((x for x in n if x.type=='BSDF_PRINCIPLED'),None)
                emission=n.new('ShaderNodeEmission'); geom=n.new('ShaderNodeNewGeometry'); transform=n.new('ShaderNodeVectorTransform'); transform.vector_type='NORMAL'; transform.convert_from='WORLD'; transform.convert_to='CAMERA'
                L(geom.outputs['Normal'],transform.inputs[0]); scale=n.new('ShaderNodeVectorMath'); scale.operation='MULTIPLY_ADD'; scale.inputs[1].default_value=(.5,.5,.5); scale.inputs[2].default_value=(.5,.5,.5); L(transform.outputs[0],scale.inputs[0]); L(scale.outputs[0],emission.inputs['Color'])
                if principled:
                    transparent=n.new('ShaderNodeBsdfTransparent'); mix=n.new('ShaderNodeMixShader')
                    alpha_socket=principled.inputs['Alpha']
                    if alpha_socket.is_linked: L(alpha_socket.links[0].from_socket,mix.inputs[0])
                    else: mix.inputs[0].default_value=alpha_socket.default_value
                    L(transparent.outputs[0],mix.inputs[1]); L(emission.outputs[0],mix.inputs[2]); L(mix.outputs[0],output.inputs[0])
                else: L(emission.outputs[0],output.inputs[0])
                ob.data.materials[index]=m
            scene.view_settings.view_transform='Raw'; normal_path=directory/(source.landscapy.uid+'_normal.png')
            if multi: normal_image,normal_path=impostors.atlas(scene,cam,center,extent,directory,source.landscapy.uid,'normal',normal=True)
            else:
                scene.render.filepath=str(normal_path); bpy.ops.render.render(write_still=True,scene=scene.name)
                normal_image=bpy.data.images.load(str(normal_path),check_existing=True); normal_image.colorspace_settings.name='Non-Color'; save_dilated(normal_image,normal_path)
        if multi:
            meta=impostors.metadata(source,extent,center,tile,color_path,normal_path)
            (directory/(source.landscapy.uid+'_impostor.json')).write_text(json.dumps(meta,indent=2))
            return impostors.billboard(source,col,center,extent,image,normal_image,meta)
        half=extent*.5; x,z=center.x,center.z
        out=mesh_object(source.name+' • Flat',[(x-half,center.y,z-half),(x+half,center.y,z-half),(x+half,center.y,z+half),(x-half,center.y,z+half)],[(0,1,2,3)],col,billboard_material(image,lit=bool(normal_image)))
        uv=out.data.uv_layers.new(name='UVMap')
        for d,c in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]): d.uv=c
        a=out.data.attributes.new('lp_color','FLOAT_COLOR','POINT')
        for d in a.data: d.color=(1,1,1,1)
        a=out.data.attributes.new('lp_opacity','FLOAT','POINT')
        for d in a.data: d.value=1
        a=out.data.attributes.new('lp_wind','FLOAT','POINT')
        for i,d in enumerate(a.data): d.value=0 if i<2 else 1
        if normal_image:
            mat=out.data.materials[0]; nt=mat.node_tree; tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=normal_image; nm=nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tex.outputs['Color'],nm.inputs['Color']); nt.links.new(nm.outputs[0],nt.nodes['Principled BSDF'].inputs['Normal'])
        out.matrix_world=source.matrix_world.copy(); return out
    finally:
        if ratio_node: ratio_node.outputs[0].default_value=old_ratio
        bpy.context.window.scene=original_scene
        for ob in created:
            data=ob.data; bpy.data.objects.remove(ob,do_unlink=True)
            if data and data.users==0:
                if isinstance(data,bpy.types.Mesh): bpy.data.meshes.remove(data)
                elif isinstance(data,bpy.types.Camera): bpy.data.cameras.remove(data)
                elif isinstance(data,bpy.types.Light): bpy.data.lights.remove(data)
        world=scene.world; bpy.data.scenes.remove(scene)
        if world and world.users==0: bpy.data.worlds.remove(world)
        for mat in temporary_materials:
            if mat.users==0: bpy.data.materials.remove(mat)

def build_steps(source,scene):
    """Stage each variant; closing before Flat rolls back this asset's new outputs."""
    from . import wind_modifier, attachments, ornaments, generate, lod, instance_cards, live_surface, live_banana, live_tree_fronds
    s=source.landscapy
    if source.get('lp_binding_signature') and not s.binding_valid: raise RuntimeError('Source attachment is invalid. Rebind before Build Variants.')
    attached=ornaments.owned(source)
    if attached:
        dg=bpy.context.evaluated_depsgraph_get(); dg.update()
        evaluated=source.evaluated_get(dg); target_mesh=evaluated.to_mesh()
        try: current_topology=attachments.signature(target_mesh)
        finally: evaluated.to_mesh_clear()
        if any(not child.get('lp_live_ornaments') and child.get('lp_binding_signature')!=current_topology for child in attached):
            raise RuntimeError('Fruit / ornament anchors are outdated. Use Generate on the plant before Build Variants.')
    directory=bake_directory(s)
    report=[]
    # Build new results first. Existing managed versions are replaced only after success.
    new=[]
    try:
        for label,ratio in [('High',1),('Mid',s.mid_ratio),('Low',s.low_ratio),('Flat',0)]:
            col=collection(scene,'Landscapy • '+label)
            budget=s.mid_triangle_limit if label=='Mid' else s.low_triangle_limit if label=='Low' else 0
            texture_scale=s.mid_texture_scale if label=='Mid' else s.low_texture_scale if label=='Low' else 1
            texture_cache={}; texture_changes=[]; card_info={}
            tree_live=live_tree_fronds.enabled(s) and source.get('lp_live_mode') in {'TreePath','TreeSurface','TreeVolume'}
            arranged=s.kind in {'Foliage','Tree'} and s.pattern in live_surface.ARRANGED_PATH_PATTERNS
            banana=s.pattern=='Banana' and s.kind in {'Tree','Foliage'} and s.live_surface and source.get('lp_live_mode') in {'Path','Surface','Volume','TreePath','TreeSurface','TreeVolume'}
            stem_sides=(s.ivy_vine_sides if s.kind=='Ivy' else s.frond_stem_sides if arranged or banana else None) if s.live_surface and label!='Flat' else None
            blade_segments=s.frond_segments if banana and label!='Flat' else None
            if label=='Flat':
                before=set(col.objects)
                try: ob=flat(source,col,directory)
                except BaseException:
                    for added in set(col.objects)-before:
                        data=added.data; bpy.data.objects.remove(added,do_unlink=True)
                        if isinstance(data,bpy.types.Mesh) and data.users==0: bpy.data.meshes.remove(data)
                    raise
                new.append(ob)
            else:
                ob=source.copy(); ob.data=source.data.copy(); col.objects.link(ob); new.append(ob)
                ob.name=source.name+' • '+label
                if tree_live and label!='High' and ratio<1:
                    ob.landscapy.mesh_detail=max(.35,s.mesh_detail*ratio)
                    ob.landscapy.ornaments_enabled=False; ob.landscapy.fruit_enabled=False
                    ob.landscapy.preview_enabled=False
                    generate(ob)
                    old=ob.data
                    if banana: ob.data,stem_sides,blade_segments=live_banana.snapshot(ob,ratio)
                    else: ob.data,stem_sides=live_surface.path_stem_snapshot(ob,ratio)
                    instance_cards.clear(ob)
                    if old.users==0: bpy.data.meshes.remove(old)
                    live_tree_fronds.remove_guides(ob)
                elif label!='High' and ratio<1 and not (s.kind in {'Foliage','Ivy'} and s.live_surface and instance_cards.modifier(source)):
                    instance_cards.clear(ob)
                    ob.landscapy.instance_cards=False
                    ob.landscapy.mesh_detail=max(.35,s.mesh_detail*ratio)
                    ob.landscapy.ornaments_enabled=False; ob.landscapy.fruit_enabled=False
                    ob.landscapy.preview_enabled=False
                    generate(ob)
                elif instance_cards.modifier(source):
                    old=ob.data
                    if banana and label!='High' and ratio<1:
                        ob.data,stem_sides,blade_segments=live_banana.snapshot(ob,ratio)
                    elif s.live_surface and (s.kind=='Ivy' or arranged) and label!='High' and ratio<1:
                        ob.data,stem_sides=live_surface.path_stem_snapshot(ob,ratio)
                    else:
                        ob.data=instance_cards.full_mesh(source)
                    instance_cards.clear(ob)
                    if old.users==0: bpy.data.meshes.remove(old)
                for mod in list(ob.modifiers):
                    if mod.name==attachments.NAME: ob.modifiers.remove(mod)
                    elif mod.name!='Landscapy Wind' or not s.keep_wind: ob.modifiers.remove(mod)
                if label!='High' and (ratio<1 or budget): card_info=lod.reduce_cards(ob,ratio,budget,s.seed)
                texture_changes.extend(lod.scaled_materials(ob,s.uid,label,texture_scale,texture_cache))
            ob['lp_source']=s.uid; ob['lp_variant']=label; ob.landscapy.uid=''
            if label=='Flat' and s.keep_wind:
                ob.landscapy.wind_controller=s.wind_controller or source; wind_modifier(ob)
            if label=='Flat' and s.flat_mode=='MULTI8':
                from . import impostors
                impostors.update(scene)
            if source.get('lp_binding_signature'):
                ob.landscapy.attachment_local_wind=s.attachment_local_wind; attachments.bind(ob,s.target)
            ornament_faces=0; attachment_triangles_used=0
            if label!='Flat':
                for ornament in ornaments.owned(source):
                    category=ornament.get('lp_attachment_kind','ORNAMENT')
                    category_label='Fruit' if category=='FRUIT' else 'Ornaments'
                    child=ornament.copy()
                    if ornament.get('lp_live_ornaments'):
                        dg=bpy.context.evaluated_depsgraph_get(); dg.update()
                        child.data=bpy.data.meshes.new_from_object(ornament.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
                        child['lp_live_ornaments']=False
                    else: child.data=ornament.data.copy()
                    child.modifiers.clear(); col.objects.link(child); new.append(child)
                    child.name=source.name+' • '+label+' '+category_label; child.parent=ob; child.matrix_parent_inverse.identity(); child.matrix_basis.identity()
                    if ratio<1 or budget:
                        import bmesh,random
                        ids=child.data.attributes['lp_ornament_id']; seed=s.fruit_seed if category=='FRUIT' else s.ornament_seed
                        all_ids=sorted({x.value for x in ids.data},key=lambda value:random.Random(seed+value*1009).random())
                        card_cap=max(1,round(len(all_ids)*ratio)) if all_ids else 0
                        body_triangles=sum(len(face.vertices)-2 for face in ob.data.polygons)
                        allowed=max(0,budget-body_triangles-attachment_triangles_used) if budget else None
                        counts={value:0 for value in all_ids}
                        for face in child.data.polygons: counts[ids.data[face.vertices[0]].value]+=len(face.vertices)-2
                        retained=set(); total=0
                        for value in all_ids[:card_cap]:
                            if allowed is not None and total+counts[value]>allowed: continue
                            retained.add(value); total+=counts[value]
                        attachment_triangles_used+=total
                        drop=set(all_ids)-retained
                        bm=bmesh.new(); bm.from_mesh(child.data); bm.verts.ensure_lookup_table(); bm.verts.index_update()
                        bmesh.ops.delete(bm,geom=[v for v in bm.verts if ids.data[v.index].value in drop],context='VERTS'); bm.to_mesh(child.data); bm.free()
                    texture_changes.extend(lod.scaled_materials(child,s.uid,label,texture_scale,texture_cache))
                    child['lp_source']=s.uid; child['lp_variant']=label+' '+category_label; child.landscapy.uid=''
                    child['lp_ornament_count']=len({x.value for x in child.data.attributes['lp_ornament_id'].data})
                    if child.data.vertices: attachments.bind(child,ob)
                    else:
                        if 'lp_binding_signature' in child: del child['lp_binding_signature']
                    child.hide_set(True); child.hide_render=True; ornament_faces+=len(child.data.polygons)
            ob.hide_set(True); ob.hide_render=True
            ob.data.calc_loop_triangles(); body_triangles=len(ob.data.loop_triangles)
            flags=ob.data.attributes.get('lp_card')
            wood_triangles=sum(len(face.vertices)-2 for face in ob.data.polygons
                               if not flags or not flags.data[face.index].value)
            ornament_triangles=sum(len(face.vertices)-2 for child in new if child.get('lp_variant') in {label+' Ornaments',label+' Fruit'} for face in child.data.polygons)
            report.append({'variant':label,'triangles':body_triangles,'wood_triangles':wood_triangles,
                           'ornament_triangles':ornament_triangles,'total_triangles':body_triangles+ornament_triangles,
                           'triangle_limit':budget,'limit_met':not budget or body_triangles+ornament_triangles<=budget,
                           'ornament_faces':ornament_faces,'mesh_detail':ob.landscapy.mesh_detail if label!='Flat' else 0,
                           'ivy_vine_profile_sides':stem_sides if s.kind=='Ivy' else None,
                           'frond_stem_profile_sides':stem_sides if arranged or banana else None,
                           'banana_blade_segments':blade_segments,
                           'texture_scale':texture_scale,'textures':texture_changes,'coverage':card_info})
            if label!='Flat': yield label
        for old in list(bpy.data.objects):
            if old.get('lp_source')==s.uid and old not in new:
                data=old.data
                bpy.data.objects.remove(old,do_unlink=True)
                if isinstance(data,bpy.types.Mesh) and data.users==0: bpy.data.meshes.remove(data)
        lod.clean_owned(s.uid)
        summary=' / '.join(f"{row['variant']} {row['total_triangles']:,}" for row in report)
        protected=any(row['coverage'].get('card_ratio_met') is False for row in report)
        limits=any(row['limit_met'] is False for row in report)
        s.status='Built variants (triangles): '+summary
        if protected: s.status+=' • card ratio limited by coverage'
        if limits: s.status+=' • triangle limit unmet'
        directory.mkdir(parents=True,exist_ok=True); (directory/(s.uid+'_report.json')).write_text(json.dumps(report,indent=2))
    except BaseException:
        for ob in new:
            data=ob.data
            bpy.data.objects.remove(ob,do_unlink=True)
            if isinstance(data,bpy.types.Mesh) and data.users==0: bpy.data.meshes.remove(data)
        lod.clean_owned(s.uid)
        raise
    yield 'Flat'


def build(source,scene):
    """Synchronous API used by scripts and background Blender sessions."""
    for _ in build_steps(source,scene): pass


def batch_steps(objects,scene):
    """Close the active asset generator when a modal Build is cancelled."""
    for ob in objects:
        active=build_steps(ob,scene)
        try:
            for label in active: yield ob.name_full,label
        finally: active.close()

class LPBuild(bpy.types.Operator):
    bl_idname='landscapy.build'; bl_label='Build Variants'; bl_options={'REGISTER','UNDO'}
    batch: BoolProperty(default=False)
    def _sources(self,context):
        source=context.object
        if not source or not source.landscapy.uid: raise RuntimeError('Select a Landscapy generator')
        objects=list(source.landscapy.build_collection.all_objects) if self.batch and source.landscapy.build_collection else [source]
        return sorted((o for o in objects if o.type=='MESH' and o.landscapy.uid and not o.get('lp_variant')),
                      key=lambda ob:ob.name_full)
    def execute(self,context):
        try:
            objects=self._sources(context)
            if not objects: raise RuntimeError('No Landscapy generators in the selected collection')
            wm=context.window_manager; wm.progress_begin(0,len(objects)*4)
            try:
                done=0
                for ob in objects:
                    for _ in build_steps(ob,context.scene):
                        done+=1; wm.progress_update(done)
            finally: wm.progress_end()
        except Exception as exc: self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self,context,event):
        if bpy.app.background or not context.window: return self.execute(context)
        try:
            objects=self._sources(context)
            if not objects: raise RuntimeError('No Landscapy generators in the selected collection')
        except Exception as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        bpy.ops.ed.undo_push(message='Before Landscapy Build')
        self._steps=batch_steps(objects,context.scene)
        self._completed=0; self._total=len(objects)*4
        wm=context.window_manager; wm.progress_begin(0,self._total)
        self._timer=wm.event_timer_add(.05,window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _stop(self,context):
        context.window_manager.event_timer_remove(self._timer)
        context.window_manager.progress_end()

    def modal(self,context,event):
        if event.type=='ESC':
            self._steps.close(); self._stop(context)
            self.report({'INFO'},f'Build cancelled after {self._completed}/{self._total} variants')
            return {'CANCELLED'}
        if event.type!='TIMER': return {'PASS_THROUGH'}
        try:
            source,label=next(self._steps)
        except StopIteration:
            self._stop(context)
            self.report({'INFO'},f'Built {self._total} variants')
            return {'FINISHED'}
        except Exception as exc:
            self._steps.close(); self._stop(context)
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        self._completed+=1
        context.window_manager.progress_update(self._completed)
        if self._completed>=self._total:
            self._steps.close(); self._stop(context)
            self.report({'INFO'},f'Built {self._total} variants')
            return {'FINISHED'}
        self.report({'INFO'},f'{source}: {label} ({self._completed}/{self._total})')
        return {'RUNNING_MODAL'}
