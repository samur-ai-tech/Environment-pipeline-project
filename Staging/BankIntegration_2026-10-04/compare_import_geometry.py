"""Check nonzero surface triangles, not merely permissive triangle-count ranges."""
import collections,itertools,json,math
import bank_contracts as C
source=C.read(C.HERE/'SOURCE_TRIANGLE_GEOMETRY.json')
native=C.read(C.HERE/'NATIVE_TRIANGLE_GEOMETRY.json')
out=C.read(C.HERE/'IMPORT_GEOMETRY_EQUIVALENCE.json') if (C.HERE/'IMPORT_GEOMETRY_EQUIVALENCE.json').exists() else {}
def area2(points):
    a,b,c=points
    u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
    w=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
    return sum(x*x for x in w)
for aid,rows in source.items():
    if aid not in native:continue
    result=[]
    for row in rows:
        targets=native[aid] if len(rows)==1 else [r for r in native[aid] if r['path'].split('.')[-1].endswith(row['name'])]
        assert len(targets)==1
        target=targets[0]
        points=[[p[0],-p[1],p[2]] for p in row['vertices_cm']]
        # Grid lookup maps each native point to its closest source position.
        tolerance=0.01
        cells=collections.defaultdict(list)
        def cell(p):return tuple(math.floor(v/tolerance) for v in p)
        def key(p):return tuple(round(v,3) for v in p)
        for p in points:cells[cell(p)].append(p)
        mapped=[];matched_points=[];max_error=0;unmapped=0
        for p in target['vertices_cm']:
            k=cell(p)
            nearby=[q for delta in itertools.product((-1,0,1),repeat=3) for q in cells.get(tuple(k[i]+delta[i] for i in range(3)),[])]
            if not nearby:unmapped+=1;mapped.append(None);matched_points.append(None);continue
            q=min(nearby,key=lambda q:sum((p[i]-q[i])**2 for i in range(3)))
            error=math.sqrt(sum((p[i]-q[i])**2 for i in range(3)))
            if error>tolerance:unmapped+=1;mapped.append(None);matched_points.append(None);continue
            max_error=max(max_error,error);mapped.append(key(q));matched_points.append(q)
        source_counts=collections.Counter();native_counts=collections.Counter();source_zero=0;native_zero=0
        for tri in row['triangles']:
            ps=[points[i] for i in tri]
            if area2(ps)<=1e-14:source_zero+=1;continue
            source_counts[tuple(sorted(key(p) for p in ps))]+=1
        for tri in target['triangles']:
            if any(mapped[i] is None for i in tri):continue
            ps=[matched_points[i] for i in tri]
            if area2(ps)<=1e-14:native_zero+=1;continue
            if any(mapped[i] is None for i in tri):continue
            native_counts[tuple(sorted(mapped[i] for i in tri))]+=1
        missing=sum((source_counts-native_counts).values());added=sum((native_counts-source_counts).values())
        result.append({'source_object':row['name'],'native_path':target['path'],'source_triangles':len(row['triangles']),
            'native_triangles':len(target['triangles']),'source_zero_area_triangles':source_zero,'native_zero_area_triangles':native_zero,
            'nonzero_missing':missing,'nonzero_added':added,'unmapped_vertices':unmapped,'maximum_vertex_error_cm':max_error,
            'tolerance_cm':tolerance,'frame':'source world cm X,-Y,Z','passed':not(missing or added or unmapped)})
    out[aid]={'passed':all(r['passed'] for r in result),'objects':result}
C.write(C.HERE/'IMPORT_GEOMETRY_EQUIVALENCE.json',out)
print(json.dumps(out,indent=2))
