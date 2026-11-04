"""LOD texture copies and coverage-aware foliage selection."""
import bpy
import bmesh
import math
from collections import defaultdict, deque
import numpy as np


def scaled_materials(obj,owner_uid,label,scale,cache):
    """Give an output independent packed images, including nested node groups."""
    if scale>=1: return []
    changed=[]
    materials=cache.setdefault('materials',{})
    images=cache.setdefault('images',{})
    groups=cache.setdefault('groups',{})

    def image_copy(source):
        if source in images: return images[source]
        width,height=source.size[:]
        if width<1 or height<1 or source.source in {'TILED','SEQUENCE','MOVIE','VIEWER'}:
            images[source]=source
            changed.append({'source':source.name_full,'source_size':[width,height],
                            'skipped':f'Image source {source.source} cannot be resized as a static packed LOD'})
            return source
        target_width=max(1,min(width,round(width*scale)))
        target_height=max(1,min(height,round(height*scale)))
        if (target_width,target_height)==(width,height):
            images[source]=source
            return source
        copy=source.copy()
        copy.name=f'{source.name} • {label} {target_width}x{target_height}'
        copy.scale(target_width,target_height)
        copy.pack()
        copy['lp_lod_owner']=owner_uid
        copy['lp_lod_variant']=label
        copy['lp_lod_source']=source.name_full
        images[source]=copy
        changed.append({'source':source.name_full,'source_size':[width,height],
                        'image':copy.name_full,'size':[target_width,target_height]})
        return copy

    def walk(tree):
        for node in tree.nodes:
            if node.type=='GROUP' and node.node_tree:
                old=node.node_tree
                if old not in groups:
                    copied=old.copy()
                    copied.name=f'{old.name} • {label}'
                    copied['lp_lod_owner']=owner_uid
                    copied['lp_lod_variant']=label
                    groups[old]=copied
                    walk(copied)
                node.node_tree=groups[old]
            elif node.type in {'TEX_IMAGE','TEX_ENVIRONMENT'} and node.image:
                node.image=image_copy(node.image)

    for index,source in enumerate(list(obj.data.materials)):
        if not source: continue
        if source not in materials:
            copy=source.copy()
            copy.name=f'{source.name} • {label} LOD'
            copy['lp_lod_owner']=owner_uid
            copy['lp_lod_variant']=label
            materials[source]=copy
            if copy.use_nodes: walk(copy.node_tree)
        obj.data.materials[index]=materials[source]
    return changed


def clean_owned(owner_uid):
    """Discard only unused LOD copies from an earlier successful build."""
    for _ in range(3):
        for collection in (bpy.data.materials,bpy.data.node_groups,bpy.data.images):
            for item in list(collection):
                if item.get('lp_lod_owner')==owner_uid and item.users==0:
                    collection.remove(item)


def _alpha_source(material,cache):
    if material in cache: return cache[material]
    image=None; extension='REPEAT'
    if material and material.use_nodes:
        nodes=material.node_tree.nodes
        node=nodes.get('image')
        if not node or node.type!='TEX_IMAGE' or not node.image or not node.outputs['Alpha'].is_linked:
            node=next((item for item in nodes if item.type=='TEX_IMAGE' and item.image and item.outputs['Alpha'].is_linked),None)
        if node: image=node.image; extension=node.extension
    result=None
    if image and min(image.size)>0 and image.channels>=4:
        width,height=image.size[:]
        pixels=np.empty(len(image.pixels),dtype=np.float32)
        image.pixels.foreach_get(pixels)
        result=(pixels.reshape(height,width,image.channels)[:,:,3],extension)
    cache[material]=result
    return result


def _fill_holes(mask,resolution):
    """Keep isolated cards that fill an enclosed gap in the dense crown."""
    dense=mask.reshape(resolution,resolution)
    exterior=np.zeros_like(dense)
    queue=deque()
    for x in range(resolution):
        for y in (0,resolution-1):
            if not dense[y,x] and not exterior[y,x]: exterior[y,x]=True; queue.append((x,y))
    for y in range(resolution):
        for x in (0,resolution-1):
            if not dense[y,x] and not exterior[y,x]: exterior[y,x]=True; queue.append((x,y))
    while queue:
        x,y=queue.popleft()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<resolution and 0<=ny<resolution and not dense[ny,nx] and not exterior[ny,nx]:
                exterior[ny,nx]=True; queue.append((nx,ny))
    return (dense|~exterior).ravel()


def _close_narrow_gaps(mask,resolution,radius=2):
    """Join nearby supported foliage without expanding its outer boundary."""
    grid=mask.reshape(resolution,resolution)
    expanded=grid.copy()
    for _ in range(radius):
        step=expanded.copy()
        step[1:] |= expanded[:-1]
        step[:-1] |= expanded[1:]
        step[:,1:] |= expanded[:,:-1]
        step[:,:-1] |= expanded[:,1:]
        expanded=step
    for _ in range(radius):
        step=expanded.copy()
        step[0]=False; step[-1]=False; step[:,0]=False; step[:,-1]=False
        step[1:] &= expanded[:-1]
        step[:-1] &= expanded[1:]
        step[:,1:] &= expanded[:,:-1]
        step[:,:-1] &= expanded[:,1:]
        expanded=step
    return expanded.ravel()


def _raster_triangle(projected,uv,alpha,opacity,resolution):
    p0,p1,p2=projected
    left=max(0,math.floor(min(p0[0],p1[0],p2[0])))
    right=min(resolution-1,math.ceil(max(p0[0],p1[0],p2[0])))
    bottom=max(0,math.floor(min(p0[1],p1[1],p2[1])))
    top=min(resolution-1,math.ceil(max(p0[1],p1[1],p2[1])))
    if left>right or bottom>top: return np.empty(0,dtype=np.int32)
    denom=(p1[1]-p2[1])*(p0[0]-p2[0])+(p2[0]-p1[0])*(p0[1]-p2[1])
    if abs(denom)<1e-6: return np.empty(0,dtype=np.int32)
    xs,ys=np.meshgrid(np.arange(left,right+1,dtype=np.float32)+.5,
                      np.arange(bottom,top+1,dtype=np.float32)+.5)
    a=((p1[1]-p2[1])*(xs-p2[0])+(p2[0]-p1[0])*(ys-p2[1]))/denom
    b=((p2[1]-p0[1])*(xs-p2[0])+(p0[0]-p2[0])*(ys-p2[1]))/denom
    c=1-a-b
    inside=(a>=-1e-5)&(b>=-1e-5)&(c>=-1e-5)
    if not inside.any(): return np.empty(0,dtype=np.int32)
    if alpha is not None:
        image,extension=alpha
        u=a*uv[0,0]+b*uv[1,0]+c*uv[2,0]
        v=a*uv[0,1]+b*uv[1,1]+c*uv[2,1]
        if extension=='REPEAT': u%=1; v%=1
        elif extension=='CLIP': inside&=(u>=0)&(u<=1)&(v>=0)&(v<=1)
        height,width=image.shape
        ix=np.minimum(width-1,np.maximum(0,(u*width).astype(np.int32)))
        iy=np.minimum(height-1,np.maximum(0,(v*height).astype(np.int32)))
        inside&=(image[iy,ix]*opacity>.35)
    return ((ys[inside]-.5).astype(np.int32)*resolution+(xs[inside]-.5).astype(np.int32))


def _coverage(mesh,resolution=128):
    card_attr=mesh.attributes.get('lp_card_id')
    if not card_attr: return {},[],[],{}
    mesh.calc_loop_triangles()
    faces={face.index:card_attr.data[face.index].value for face in mesh.polygons
           if card_attr.data[face.index].value>=0}
    if not faces: return {},[],[],{}
    verts=np.array([tuple(vertex.co) for vertex in mesh.vertices],dtype=np.float32)
    card_vertices=np.array(sorted({vertex for face in mesh.polygons if face.index in faces
                                   for vertex in face.vertices}),dtype=np.int32)
    views=[]
    for index in range(8):
        angle=index*math.tau/8
        views.append(np.stack((verts[:,0]*math.cos(angle)+verts[:,1]*math.sin(angle),verts[:,2]),axis=1))
    views.append(verts[:,:2].copy())
    projections=[]
    for xy in views:
        low=xy[card_vertices].min(axis=0); high=xy[card_vertices].max(axis=0)
        extent=max(float(max(high-low)),.001)
        projections.append((xy-(low+high)*.5)*(resolution-8)/(extent*1.10)+(resolution-1)*.5)
    # Geometry Nodes snapshots can retain UVMap without marking any layer active.
    # Sampling (0, 0) in that case makes textured cards look fully transparent
    # to the coverage test even though they render with their UVs intact.
    uv_layer=mesh.uv_layers.active or mesh.uv_layers.get('UVMap')
    if not uv_layer and mesh.uv_layers: uv_layer=mesh.uv_layers[0]
    opacity_attr=mesh.attributes.get('lp_opacity')
    alpha_cache={}
    fragments=defaultdict(lambda:[[] for _ in views])
    triangles=defaultdict(int)
    for tri in mesh.loop_triangles:
        card_id=faces.get(tri.polygon_index)
        if card_id is None: continue
        triangles[card_id]+=1
        face=mesh.polygons[tri.polygon_index]
        material=mesh.materials[face.material_index] if face.material_index<len(mesh.materials) else None
        alpha=_alpha_source(material,alpha_cache)
        uv=np.array([uv_layer.data[i].uv[:] for i in tri.loops],dtype=np.float32) if uv_layer else np.zeros((3,2),dtype=np.float32)
        opacity=sum(opacity_attr.data[i].value for i in tri.vertices)/3 if opacity_attr else 1.
        for index,projected in enumerate(projections):
            pixels=_raster_triangle(projected[list(tri.vertices)],uv,alpha,opacity,resolution)
            if pixels.size: fragments[card_id][index].append(pixels)
    pixels={card_id:[np.unique(np.concatenate(parts)) if parts else np.empty(0,dtype=np.int32)
                     for parts in per_view] for card_id,per_view in fragments.items()}
    for card_id in triangles:
        pixels.setdefault(card_id,[np.empty(0,dtype=np.int32) for _ in views])
    counts=[np.zeros(resolution*resolution,dtype=np.uint32) for _ in views]
    for per_view in pixels.values():
        for count,indices in zip(counts,per_view): count[indices]+=1
    cores=[]
    for count in counts:
        occupied=count>0; supported=count>1
        cores.append(occupied & (_fill_holes(_close_narrow_gaps(supported,resolution),resolution)
                                 if supported.sum()>=8 else occupied))
    return pixels,counts,cores,triangles


def reduce_cards(obj,ratio,budget,seed):
    """Prune exterior detail without thinning the alpha-visible crown core."""
    mesh=obj.data
    pixels,counts,cores,triangles=_coverage(mesh)
    if not pixels: return {'cards_before':0,'cards_after':0,'coverage_views':9,
                           'proxy_core_preserved':True,'core_depth_preserved':True}
    protected_pixels=[int(np.count_nonzero(core & (count>0))) for count,core in zip(counts,cores)]
    # Never remove the last alpha-visible layer of a core pixel. A small,
    # bounded amount of second-layer thinning is allowed so genuine exterior
    # detail can be simplified without making the whole LOD ineligible.
    second_layer_pixels=[int(np.count_nonzero(core & (count>=2))) for count,core in zip(counts,cores)]
    max_second_layer_loss=[max(1,round(value*.02)) for value in second_layer_pixels]
    second_layer_loss=[0]*len(counts)
    occupied_pixels=[int(np.count_nonzero(count)) for count in counts]
    # One-layer foliage can still define a branch lobe or the outer contour.
    # Permit only tiny fringe changes, per card and in total, in every view.
    silhouette_card_limit=[max(1,round(value*.01)) for value in occupied_pixels]
    silhouette_total_limit=[max(1,round(value*.02)) for value in occupied_pixels]
    silhouette_loss=[0]*len(counts)
    target=max(1,round(len(pixels)*ratio))
    wood=sum(len(face.vertices)-2 for face in mesh.polygons if mesh.attributes['lp_card_id'].data[face.index].value<0)
    remaining=sum(triangles.values())+wood
    def importance(card_id):
        unique=sum(int(np.count_nonzero((count[indices]==1)&core[indices]))
                   for indices,count,core in zip(pixels[card_id],counts,cores))
        interior=sum(int(np.count_nonzero(core[indices])) for indices,core in zip(pixels[card_id],cores))
        total=sum(len(indices) for indices in pixels[card_id])
        outside=total-interior
        silhouette_unique=sum(int(np.count_nonzero((count[indices]==1)&~core[indices]))
                              for indices,count,core in zip(pixels[card_id],counts,cores))
        stable=(card_id*1103515245+seed*2654435761)&0xffffffff
        return unique,int(total>0),silhouette_unique,-outside/max(1,total),interior,stable
    # Only clear or visibly protruding extras qualify. Recheck all nine views
    # after each removal so repeated pruning cannot hollow the supported core.
    scores={card_id:importance(card_id) for card_id in pixels}
    order=sorted((card_id for card_id,score in scores.items()
                  if score[0]==0 and (score[1]==0 or -score[3]>=.10)),key=scores.get)
    dropped=set()
    for card_id in order:
        if len(pixels)-len(dropped)<=target and (not budget or remaining<=budget): break
        if len(pixels)-len(dropped)<=1: break
        if any(np.any((count[indices]==1)&core[indices])
               for indices,count,core in zip(pixels[card_id],counts,cores)):
            continue
        outline=[int(np.count_nonzero((count[indices]==1)&~core[indices]))
                 for indices,count,core in zip(pixels[card_id],counts,cores)]
        if any(new>per_card or old+new>total for new,per_card,old,total in
               zip(outline,silhouette_card_limit,silhouette_loss,silhouette_total_limit)):
            continue
        thinning=[int(np.count_nonzero((count[indices]==2)&core[indices]))
                  for indices,count,core in zip(pixels[card_id],counts,cores)]
        if any(loss+new>allowed for loss,new,allowed in
               zip(second_layer_loss,thinning,max_second_layer_loss)):
            continue
        for indices,count in zip(pixels[card_id],counts): count[indices]-=1
        second_layer_loss=[old+new for old,new in zip(second_layer_loss,thinning)]
        silhouette_loss=[old+new for old,new in zip(silhouette_loss,outline)]
        dropped.add(card_id)
        remaining-=triangles[card_id]
    final_protected=[int(np.count_nonzero(core & (count>0))) for count,core in zip(counts,cores)]
    final_occupied=[int(np.count_nonzero(count)) for count in counts]
    core_preserved=protected_pixels==final_protected
    depth_preserved=all(loss<=allowed for loss,allowed in zip(second_layer_loss,max_second_layer_loss))
    silhouette_preserved=all(loss<=allowed for loss,allowed in zip(silhouette_loss,silhouette_total_limit))
    if not core_preserved or not depth_preserved or not silhouette_preserved:
        raise RuntimeError('Foliage LOD would thin primary crown coverage')
    if dropped:
        ids=mesh.attributes['lp_card_id']
        vertices={index for face in mesh.polygons if ids.data[face.index].value in dropped
                  for index in face.vertices}
        bm=bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table(); bm.verts.index_update()
        bmesh.ops.delete(bm,geom=[bm.verts[index] for index in vertices],context='VERTS')
        bm.to_mesh(mesh); bm.free(); mesh.update()
    return {'cards_before':len(pixels),'cards_after':len(pixels)-len(dropped),
            'coverage_views':len(counts),'proxy_core_preserved':core_preserved,
            'core_depth_preserved':depth_preserved,
            'silhouette_budget_preserved':silhouette_preserved,
            'silhouette_loss_pixels_per_view':silhouette_loss,
            'silhouette_card_limit_pixels_per_view':silhouette_card_limit,
            'silhouette_total_limit_pixels_per_view':silhouette_total_limit,
            'primary_pixels_per_view':protected_pixels,
            'second_layer_pixels_per_view':second_layer_pixels,
            'second_layer_loss_pixels_per_view':second_layer_loss,
            'second_layer_loss_limit_fraction':.02,
            'visible_pixels_per_view_before':occupied_pixels,
            'visible_pixels_per_view_after':final_occupied,
            'protruding_cards_removed':len(dropped),
            'card_ratio_met':len(pixels)-len(dropped)<=target,
            'triangle_limit_met':not budget or remaining<=budget}
