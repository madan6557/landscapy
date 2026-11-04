"""Evaluated curve centerlines, preserving separate splines and cyclic paths."""
import bpy


def curve_paths(ob):
    dg=bpy.context.evaluated_depsgraph_get()
    data=ob.evaluated_get(dg).data.copy()
    data.bevel_depth=0; data.extrude=0; data.bevel_object=None
    data.dimensions='3D'
    temp=bpy.data.objects.new('_LP centerline',data)
    bpy.context.scene.collection.objects.link(temp)
    mesh=None
    try:
        bpy.context.view_layer.update()
        ev=temp.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=ev.to_mesh()
        vertices=[ob.matrix_world@v.co for v in mesh.vertices]
        adjacency={i:[] for i in range(len(vertices))}
        for edge in mesh.edges:
            a,b=edge.vertices; adjacency[a].append(b); adjacency[b].append(a)
        if any(len(v)>2 for v in adjacency.values()):
            raise ValueError('Curve centerline contains branching topology; use separate splines')
        unseen=set(adjacency); paths=[]
        while unseen:
            # Prefer an endpoint of this connected component, not another spline.
            component=set(); stack=[min(unseen)]
            while stack:
                i=stack.pop()
                if i in component: continue
                component.add(i); stack.extend(j for j in adjacency[i] if j not in component)
            endpoints=[i for i in component if len(adjacency[i])<2]
            start=min(endpoints or component); path=[]; previous=None; current=start
            while current in unseen:
                unseen.remove(current); path.append(vertices[current])
                following=[i for i in adjacency[current] if i!=previous]
                if not following: break
                previous,current=current,following[0]
                if current==start:
                    path.append(vertices[start]); break
            if len(path)>1: paths.append(path)
        return paths
    finally:
        if mesh is not None: ev.to_mesh_clear()
        bpy.data.objects.remove(temp,do_unlink=True)
        if data.users==0: bpy.data.curves.remove(data)


def resample(path, spacing):
    """Fixed arc-length stations; retain endpoints without zero-length segments."""
    if len(path)<2: return list(path)
    out=[path[0].copy()]; remaining=max(.001,spacing)
    for a,b in zip(path,path[1:]):
        cursor=a.copy(); distance=(b-cursor).length
        while distance>=remaining and distance>1e-9:
            if len(out)>=20000: raise ValueError('Path exceeds 20,000 stations; increase step size')
            cursor=cursor.lerp(b,remaining/distance); out.append(cursor.copy())
            distance=(b-cursor).length; remaining=max(.001,spacing)
        remaining-=distance
    if (out[-1]-path[-1]).length>1e-5: out.append(path[-1].copy())
    return out


def stations(path,density,limit):
    """Density per world meter, independent of spline tessellation resolution."""
    if density<=0 or limit<=0: return []
    lengths=[(b-a).length for a,b in zip(path,path[1:])]
    total=sum(lengths); count=min(limit,int(total*density)); out=[]
    if not count: return out
    segment=0; walked=0.
    for i in range(count):
        distance=total*(i+.5)/count
        while segment<len(lengths)-1 and walked+lengths[segment]<distance:
            walked+=lengths[segment]; segment+=1
        if lengths[segment]<1e-9: continue
        a,b=path[segment:segment+2]
        out.append((a.lerp(b,(distance-walked)/lengths[segment]),(b-a).normalized()))
    return out
