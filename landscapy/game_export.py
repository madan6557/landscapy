"""Export built Landscapy variants as self-contained GLB assets for game pipelines."""
import json
import re
from pathlib import Path

import bpy
from bpy.props import BoolProperty


LABELS=('High','Mid','Low','Flat')
ATTRIBUTES={
    'lp_wind':'_LP_WIND',
    'lp_leaf_wind':'_LP_LEAF_WIND',
    'lp_branch_wind_cos':'_LP_BRANCH_COS',
    'lp_branch_wind_sin':'_LP_BRANCH_SIN',
    'lp_cluster_phase':'_LP_CLUSTER_PHASE',
    'lp_card_phase':'_LP_CARD_PHASE',
    'lp_branch_t':'_LP_BRANCH_T',
    'lp_branch_id':'_LP_BRANCH_ID',
    'lp_branch_level':'_LP_BRANCH_LEVEL',
    'lp_opacity':'_LP_OPACITY',
}


def outputs(source):
    """Resolve only bodies owned by this generator, including hidden Build results."""
    found={}
    for ob in bpy.data.objects:
        label=ob.get('lp_variant')
        if ob.get('lp_source')==source.landscapy.uid and label in LABELS:
            if label in found: raise RuntimeError(f'Duplicate {label} output for {source.name}')
            found[label]=ob
    missing=[label for label in LABELS if label not in found]
    if missing: raise RuntimeError(f'{source.name}: Build Variants first; missing {", ".join(missing)}')
    return found


def _asset_name(source):
    readable=re.sub(r'[^A-Za-z0-9_-]+','_',source.name).strip('_')[:48] or 'Landscapy'
    return f'{readable}_{source.landscapy.uid[:8]}'


def _attributes(mesh):
    """Use glTF custom semantics and a standard vertex color with card opacity."""
    exported={}
    for source_name,target_name in ATTRIBUTES.items():
        source=mesh.attributes.get(source_name)
        if not source or source.domain!='POINT': continue
        target=mesh.attributes.new(target_name,'FLOAT','POINT')
        for out,value in zip(target.data,source.data): out.value=float(value.value)
        exported[target_name]=source_name
    colors=mesh.color_attributes.get('lp_color')
    opacity=mesh.attributes.get('lp_opacity')
    if colors and colors.domain=='POINT':
        target=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
        for index,out in enumerate(target.data):
            source=colors.data[index].color
            out.color=(source[0],source[1],source[2],
                       float(opacity.data[index].value) if opacity and opacity.domain=='POINT' else source[3])
        mesh.color_attributes.active_color=target
        exported['COLOR_0']='lp_color RGB × lp_opacity alpha'
    face_view=mesh.attributes.get('lp_impostor_view')
    if face_view and face_view.domain=='FACE':
        view=mesh.attributes.new('_LP_IMPOSTOR_VIEW','FLOAT','POINT')
        for face in mesh.polygons:
            for vertex in face.vertices: view.data[vertex].value=float(face_view.data[face.index].value)
        exported['_LP_IMPOSTOR_VIEW']='lp_impostor_view'
    return exported


def _snapshot(original,source,scene):
    """Freeze attachment deformation at the current frame, without procedural wind."""
    from . import impostors
    disabled=[]
    for modifier in original.modifiers:
        if modifier.name in {'Landscapy Wind',impostors.NAME}:
            disabled.append((modifier,modifier.show_viewport,modifier.show_render))
            modifier.show_viewport=False; modifier.show_render=False
    try:
        bpy.context.view_layer.update()
        depsgraph=bpy.context.evaluated_depsgraph_get(); depsgraph.update()
        mesh=bpy.data.meshes.new_from_object(original.evaluated_get(depsgraph),
                                             preserve_all_data_layers=True,depsgraph=depsgraph)
        clone=bpy.data.objects.new(original.name+' • Game Export',mesh)
        scene.collection.objects.link(clone)
        clone.matrix_world=source.matrix_world.inverted()@original.matrix_world
        clone.hide_render=False; clone.hide_set(False)
        return clone
    finally:
        for modifier,viewport,render in disabled:
            modifier.show_viewport=viewport; modifier.show_render=render


def _remove(objects):
    for ob in objects:
        mesh=ob.data
        bpy.data.objects.remove(ob,do_unlink=True)
        if mesh and mesh.users==0: bpy.data.meshes.remove(mesh)


def _texture_sizes(objects):
    found={}; visited=set()
    def walk(tree):
        if not tree or tree in visited: return
        visited.add(tree)
        for node in tree.nodes:
            if node.type in {'TEX_IMAGE','TEX_ENVIRONMENT'} and node.image:
                found[node.image.name_full]=list(node.image.size[:])
            elif node.type=='GROUP' and node.node_tree: walk(node.node_tree)
    for ob in objects:
        for material in ob.data.materials:
            if material and material.use_nodes: walk(material.node_tree)
    return [{'image':name,'size':found[name]} for name in sorted(found)]


def export_variant(source,label,body,directory,stem):
    """Write one GLB without modifying Built mesh data or the user's selection."""
    try: bpy.ops.export_scene.gltf.get_rna_type()
    except (AttributeError,RuntimeError):
        bpy.ops.preferences.addon_enable(module='io_scene_gltf2')
    scene=bpy.context.scene
    selected=list(bpy.context.selected_objects)
    active=bpy.context.view_layer.objects.active
    cloned=[]; attributes={}
    path=directory/f'{stem}_{label}.glb'
    try:
        originals=[body]+[ob for ob in bpy.data.objects
                          if ob.get('lp_source')==source.landscapy.uid
                          and ob.get('lp_variant')==label+' Ornaments']
        for original in originals:
            clone=_snapshot(original,source,scene)
            cloned.append(clone)
            attributes.update(_attributes(clone.data))
        bpy.ops.object.select_all(action='DESELECT')
        for clone in cloned: clone.select_set(True)
        bpy.context.view_layer.objects.active=cloned[0]
        result=bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',
                                          use_selection=True,export_attributes=True,
                                          export_vertex_color='NAME',export_vertex_color_name='Color',
                                          export_all_vertex_colors=False,export_animations=False,
                                          export_extras=False,export_apply=False,export_yup=True)
        if result!={'FINISHED'}: raise RuntimeError(f'glTF export did not finish: {result}')
        for clone in cloned: clone.data.calc_loop_triangles()
        return {'variant':label,'file':path.name,'meshes':len(cloned),
                'triangles':sum(len(ob.data.loop_triangles) for ob in cloned),
                'attributes':attributes,'textures':_texture_sizes(cloned)}
    finally:
        _remove(cloned)
        bpy.ops.object.select_all(action='DESELECT')
        for ob in selected:
            if ob.name in bpy.data.objects and not ob.hide_get(): ob.select_set(True)
        if active and active.name in bpy.data.objects: bpy.context.view_layer.objects.active=active


def export_asset(source,directory):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    built=outputs(source)
    stem=_asset_name(source)
    rows=[export_variant(source,label,built[label],directory,stem) for label in LABELS]
    flat=built['Flat']; impostor=json.loads(flat['lp_impostor_info']) if flat.get('lp_impostor_info') else None
    manifest={'schema':1,'source_name':source.name,'source_uid':source.landscapy.uid,
              'coordinate_space':'glTF Y-up; source and impostor metadata use Blender local Z-up',
              'wind_shader':'Not included; custom _LP_ attributes carry masks and phase coefficients',
              'variants':rows,'impostor':impostor}
    path=directory/f'{stem}_manifest.json'
    path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


class LPExportGame(bpy.types.Operator):
    bl_idname='landscapy.export_game'; bl_label='Export Game Variants (GLB)'; bl_options={'REGISTER'}
    bl_description='Export built High/Mid/Low/Flat GLBs, packed textures, wind attributes and a manifest'
    batch: BoolProperty(default=False)
    def execute(self,context):
        active=context.object
        if not active or not active.landscapy.uid:
            self.report({'ERROR'},'Select a Landscapy generator'); return {'CANCELLED'}
        collection=active.landscapy.build_collection if self.batch else None
        sources=list(collection.all_objects) if collection else [active]
        sources=sorted((ob for ob in sources if ob.type=='MESH' and ob.landscapy.uid
                        and not ob.get('lp_variant')),key=lambda ob:ob.name_full)
        try:
            for source in sources: outputs(source)
            directory=Path(bpy.path.abspath(active.landscapy.game_export_dir))
            context.window_manager.progress_begin(0,max(1,len(sources)*4))
            try:
                done=0
                for source in sources:
                    export_asset(source,directory)
                    done+=4; context.window_manager.progress_update(done)
            finally: context.window_manager.progress_end()
        except Exception as exc:
            self.report({'ERROR'},str(exc)); return {'CANCELLED'}
        self.report({'INFO'},f'Exported {len(sources)} Landscapy assets to {directory}')
        return {'FINISHED'}
