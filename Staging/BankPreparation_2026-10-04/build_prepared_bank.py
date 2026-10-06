"""Reconcile retained preparation by canonical AssetId. Does not modify live catalog."""
import base64,collections,csv,hashlib,html,json,math,pathlib,re
from datetime import datetime,timezone
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=pathlib.Path(__file__).resolve().parent
SOURCES=pathlib.Path('C:/Users/USER/Documents/Pipeline Environment/ModelBank/Prepared_2026-10-04')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(name,v):(OUT/name).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def yes(v):return str(v).lower() in ('true','1')
def package(p):return ROOT/'Content'/(p.split('.')[0][6:]+'.uasset') if p.startswith('/Game/') else None
def parse_list(s):
    try:return json.loads(s)
    except (ValueError,TypeError):return None
catpath=ROOT/'Staging/ModelBank/PermanentIntegration_2026-10-02/catalog_v4_source.json';cat=read(catpath)
index={r['asset_id']:r for r in csv.DictReader((ROOT/'Staging/ModelBank/BANK_CANDIDATE_INDEX_2026-09-29.csv').open(encoding='utf-8-sig'))}
ledger={r['AssetId']:r for r in csv.DictReader((ROOT/'Staging/ModelBank/BANK_ASSETID_REVIEW_LEDGER_2026-10-01.csv').open(encoding='utf-8-sig'))}
prepared={r['asset_id']:r for r in (read(p) for p in SOURCES.glob('*/ASSET.json'))}
native=read(OUT/'NATIVE_MEASUREMENTS.json') if (OUT/'NATIVE_MEASUREMENTS.json').exists() else {}
repair=read(OUT/'MATERIAL_REPAIR.json') if (OUT/'MATERIAL_REPAIR.json').exists() else None
oldphotos=read(ROOT/'Staging/BankDepthAudit_2026-10-04/GALLERY_COVERAGE.json')['native_image_manifest']
baseline=read(OUT/'BASELINE.json');rows=[];patches=[];native_queue=[];external_imports=[]
applied=read(OUT/'CATALOG_METADATA_APPLIED.json') if (OUT/'CATALOG_METADATA_APPLIED.json').exists() else None
named=['H0013','H0907','H0051','H0958','H0094']
for c in cat['rows']:
    aid=c['asset_id'];i=index.get(aid,{});l=ledger.get(aid,{});rt=c['runtime'];b=prepared.get(aid)
    category=i.get('category',c.get('recorded_category',''));modular=category=='Buildings/Modules'
    path=rt['ObjectPath'];disk=package(path);enabled=yes(rt['RunEligible'])
    held=[n for n in named if re.search(r'(?:^|[_\.])'+n+r'(?:[_\.]|$)',aid)]
    palm=bool(re.search(r'palm|coconut',i.get('name',rt['VariantId']),re.I))
    record={'asset_id':aid,'catalog_row_name':c['catalog_row_name'],'name':i.get('name',rt['VariantId']),
        'category':category,'family_id':rt['FamilyId'],'source_package':c['source_package'],
        'source_path':i.get('source_path'),'record_kind':i.get('record_kind','material_identity'),
        'object_path':path,'native_class_recorded':c.get('recorded_native_class'),
        'runtime_enabled':enabled,'runtime_hold_preserved':yes(rt['ExplicitHold']),'hold_reasons_preserved':c['hold_reasons'],
        'named_holds_preserved':held,'palm_hold_not_released':palm,
        'rights_state_preserved':c['recorded_rights_state'],'canonical_qualified':c['canonical_qualified'],
        'request_role':rt['RequestRole'],'placement_rule':rt['PlacementRule'],'allowed_zones_current':rt['AllowedZones'],
        'style_source_recorded':c.get('environment_style_set'),'style_context_current':rt['StyleSet'],
        'normal_scope_current':rt['AllowedAreas'],'new_normal_scope_requested':['GazaRimal','GazaShujaiya'],
        'newly_imported':False,'newly_connected':False,'newly_enabled':False,'new_area_generation':False,
        'native_preview_sources':oldphotos.get(aid,[]),'prepared_source':None,'blockers':[]}
    if modular:
        record['phase_status']='modular_phase_deferred';rows.append(record);continue
    materials=c.get('live_measurement',{}).get('material_paths',[])
    if not materials:
        mats=parse_list(i.get('material_paths',''))
        if isinstance(mats,list):materials=mats
    materials=[p if isinstance(p,str) else p.get('refPath',p.get('path','')) for p in materials]
    normal=c.get('normal_use_configuration',c.get('normal_use',{}))
    overrides=normal.get('instance_material_slots',cat.get('instance_materials',{}).get(path,[]))
    record['material_slots_recorded']=[{'slot':n,'path':p,'package_exists':bool(package(p) and package(p).is_file())} for n,p in enumerate(materials)]
    record['instancing_material_slots_recorded']=overrides
    measured=native.get(aid)
    if measured and measured['status']=='measured':
        record['native_measurement']=measured
        record['native_load_verified_this_run']=True
        record['material_slots_recorded']=measured['material_slots']
        record['dimensions_native_m_recorded']=[x/100 for x in measured['dimensions_cm']]
    record['dependency_unresolved_count_recorded']=int(l['UnresolvedDependencyCount']) if l.get('UnresolvedDependencyCount','').isdigit() else None
    record['dependency_unresolved_paths_recorded']=l.get('UnresolvedDependencyPaths','')
    if path:
        record['package_exists']=bool(disk and disk.is_file());record['native_load_verified_this_run']=bool(measured and measured['status']=='measured')
        if disk and disk.is_file():
            digest=sha(disk);record['current_package_sha256']=digest
            record['package_revision_matches_runtime']=digest.lower()==rt['AssetRevision'].lower()
        if yes(rt['BoundsValid']):
            lo=[float(rt['BoundsMin'+a+'Cm']) for a in 'XYZ'];hi=[float(rt['BoundsMax'+a+'Cm']) for a in 'XYZ']
            record['bounds_native_cm_recorded']={'min':lo,'max':hi};record['dimensions_native_m_recorded']=[(b-a)/100 for a,b in zip(lo,hi)]
            record['placement_definition']={'up_axis':'native_Z','scale_min':[1,1,1],'scale_max':[1,1,1],
                'horizontal_anchor_cm':[(lo[0]+hi[0])/2,(lo[1]+hi[1])/2],
                'anchor_z_cm':float(rt['AnchorZCm']) if yes(rt['AnchorValid']) else lo[2],
                'anchor_basis':'retained_verified_runtime' if yes(rt['AnchorValid']) else 'recorded_AABB_bottom_candidate_not_contact_verification',
                'forward_axis':rt['ForwardAxis'] or None,'forward_axis_candidate':'+X' if hi[0]-lo[0]>=hi[1]-lo[1] else '+Y',
                'forward_axis_basis':'runtime' if yes(rt['OrientationValid']) else 'longest_horizontal_extent_is_geographic_alignment_only_not_facing',
                'min_spacing_cm_recorded':float(rt['MinSpacingCm'])}
        if c.get('recorded_native_class')=='StaticMesh':
            native_queue.append({'asset_id':aid,'path':path,'current_file_sha256':record.get('current_package_sha256'),
                'already_enabled':enabled,'named_hold':bool(held),'preserve_hold':record['runtime_hold_preserved'],
                'measure':['loaded_native_bounds','LOD0_vertex_minimum_contact_and_XY_anchor','material_slot_order','dependency_closure','UV_channels','normals','LOD_and_collision','role_facing'],
                'read_only':True,'editor_owner_required':True})
    name=(record['name']+' '+category).lower()
    if category=='Utility/RooftopProps':required='roof_or_wall_host_attachment'
    elif category=='Signs':required='sign_host_attachment_or_measured_standalone_pole'
    elif re.search(r'fence|guard.?rail|barrier|railing|hedge',name):required='linear_boundary_alignment'
    elif re.search(r'sidewalk|pavement|roaddrain|manhole|^road',name):required='road_or_surface_host'
    elif category=='Buildings/Whole':required='whole_building_footprint_height_terrain_fit'
    elif category=='Vegetation':required='vegetation_ground_fit'
    elif category in ('StreetProps','SmallProps'):required='ground_prop_contact_clearance'
    else:required='nonplacement_dependency_or_surface'
    record['required_consumer_context']=required
    record['context_classification_basis']='category_and_name_triage_requires_asset_review'
    if required in ('roof_or_wall_host_attachment','sign_host_attachment_or_measured_standalone_pole','linear_boundary_alignment','road_or_surface_host'):
        record['blockers'].append('explicit_host_or_linear_provider_required_no_ground_scatter_substitution')
    if held:record['blockers'].append('named_owner_hold')
    if palm:record['blockers'].append('palm_selection_hold_preserved')
    if b:
        fixed=repair if repair and repair['asset_id']==aid else None
        record['prepared_source']={'receipt':str(SOURCES/aid.replace('.','_')/'ASSET.json'),'blend':b.get('prepared_blend'),
            'source_fbx':b['source_fbx'],'source_fbx_sha256':b['source_fbx_sha256'],'dimensions_m':b.get('dimensions_m'),
            'bounds_m':b.get('bounds_m'),'bottom_center_m':b.get('bottom_center_m'),'preview':b.get('preview_path'),
            'preview_kind':b.get('preview_kind'),'triangles_LOD0':b.get('triangles'),
            'primary_render_object_count':b.get('primary_render_object_count'),'collision_object_count':b.get('collision_object_count'),
            'material_slots_by_object':[{k:o[k] for k in ['name','geometry_role','material_slots','uv_layers']} for o in b.get('objects',[])],
            'texture_references':b.get('texture_references'),'missing_texture_count':b.get('missing_texture_count'),
            'uv_missing_render_objects':b.get('uv_missing_objects'),'geometry_edited':False,
            'source_files_unchanged':b.get('source_unchanged') and b.get('source_blend_unchanged')}
        if b.get('missing_texture_count'):record['blockers'].append('missing_texture_files')
        if fixed:
            donor=prepared[fixed['donor_asset_id']]
            record['prepared_source']['original_missing_texture_count']=b.get('missing_texture_count')
            record['prepared_source']['missing_texture_count']=len(fixed['linked_render_material_missing_images'])
            record['prepared_source']['blend']=fixed['prepared_blend']
            record['prepared_source']['prepared_import_fbx']=fixed['prepared_fbx']
            record['prepared_source']['material_repair']=fixed
            record['prepared_source']['texture_references']=donor['texture_references']
            record['prepared_source']['preview']=fixed.get('material_preview',b.get('preview_path'))
            record['prepared_source']['preview_kind']='fresh_Blender_material_render_not_native_Unreal_appearance'
            record['blockers']=[x for x in record['blockers'] if x!='missing_texture_files']
        if b.get('uv_missing_objects'):record['blockers'].append('render_mesh_UV_inspection_required')
        if b['status']!='prepared_source':record['blockers'].append('blender_preparation_error')
        record['blockers'].extend(['native_import_readback_and_material_binding_pending','contact_facing_and_context_review_pending'])
        record['phase_status']='blender_source_prepared_native_integration_pending'
        external_imports.append({'asset_id':aid,'name':record['name'],'existing_catalog_row':record['catalog_row_name'],
            'source_fbx':fixed['prepared_fbx'] if fixed else b['source_fbx'],'sha256':sha(pathlib.Path(fixed['prepared_fbx'])) if fixed else b['source_fbx_sha256'],'prepared_blend':fixed['prepared_blend'] if fixed else b.get('prepared_blend'),
            'destination_package_proposed':'/Game/Project/Shared/ModelBank/Prepared/External/'+aid.replace('.','_')+'/SM_'+re.sub('[^A-Za-z0-9_]','_',record['name']),
            'destination_status':'reserved_plan_not_an_existing_native_reference',
            'geometry_policy':'reuse_existing_FBX_preserve_collision_and_LODs_no_remodel',
            'material_mapping_by_source_object':record['prepared_source']['material_slots_by_object'],
            'textures':record['prepared_source']['texture_references'],'material_repair':fixed,'combine_policy':'review_multi_object_assembly_before_single_static_mesh_import',
            'activate_automatically':False,'blockers':record['blockers']})
    elif enabled:record['phase_status']='retained_runtime_use_metadata_reconciled'
    elif i.get('record_kind')=='family_candidate':record['phase_status']='family_inventory_not_individual_mesh'
    elif measured and measured['status']=='measured':record['phase_status']='native_measured_configuration_pending'
    elif path:record['phase_status']='native_metadata_prepared_readback_pending'
    elif i.get('source_scope')=='current':record['phase_status']='native_dependency_not_selectable_mesh_preserved'
    else:
        record['phase_status']='external_native_or_speedtree_source_requires_native_importer'
        record['blockers'].append('source_format_not_Blender_FBX_use_native_dependency_preserving_import')
    if record.get('dependency_unresolved_count_recorded',0):record['blockers'].append('recorded_unresolved_dependencies')
    if measured and measured['status']=='measured':
        record['bounds_native_cm_measured']=measured['bounds_cm']
        record['dimensions_native_m_measured']=[x/100 for x in measured['dimensions_cm']]
        if measured['dependencies']['unresolved_registry_packages']:record['blockers'].append('native_original_material_dependency_references_unresolved_review_instance_overrides_separately')
        if any(not s['path'] for s in measured['material_slots']):record['blockers'].append('native_material_slot_empty_role_review_required')
        if 'placement_definition' in record:
            record['placement_definition']['measured_vertex_anchor_z_candidate']=measured.get('anchor_z_cm_candidate')
    # This payload updates descriptive preparation fields only; runtime eligibility stays unchanged.
    patches.append({'asset_id':aid,'catalog_row_name':c['catalog_row_name'],'bank_preparation':record})
    rows.append(record)

# Fixed aggregate family budgets prevent one family winning just through variant count.
# They are prospective, and computed only for the same role/style/context partitions.
groups=collections.defaultdict(list)
for r in rows:
    if r.get('phase_status')=='modular_phase_deferred' or r['record_kind']!='asset_candidate':continue
    key=(r['request_role'] or r['category'],r['family_id'],r['style_context_current'],r['required_consumer_context'])
    groups[key].append(r)
budgets=[]
for (role,family,style,context),members in sorted(groups.items()):
    budgets.append({'role':role,'family_id':family,'style':style,'context':context,'aggregate_budget':1.0,
        'variant_count':len(members),'per_variant_weight_if_all_members_activated':1/len(members),
        'asset_ids':[r['asset_id'] for r in members],'applied':False,
        'activation_rule':'Recompute budget/N over actual eligible members within the same role/style/context and named area; do not use row count as extra family probability.'})
write('PREPARED_BANK.json',{'schema':'environmentpipeline.bank_preparation.v1','rows':rows})
write('CATALOG_METADATA_PATCH.json',{'target':str(catpath),'target_sha256':sha(catpath),'target_native_table':cat['native_data_table_package'],
    'application_status':'descriptive_annotations_applied_runtime_unchanged' if applied else 'not_applied','application_receipt':applied,'runtime_changes':[],
    'merge_key':'asset_id','patches':patches})
write('NATIVE_READBACK_QUEUE.json',native_queue);write('EXTERNAL_IMPORT_MANIFEST.json',external_imports);write('FAMILY_WEIGHT_BUDGETS.json',budgets)
checks={p:{'before':digest,'after':sha(pathlib.Path(p)),'unchanged':sha(pathlib.Path(p))==digest} for p,digest in baseline['files'].items()}
summary={'recorded_utc':datetime.now(timezone.utc).isoformat(),'catalog_identities':len(rows),'metadata_payload_rows':len(patches),
    'modular_deferred':sum(r['phase_status']=='modular_phase_deferred' for r in rows),
    'blender_sources_prepared':sum(r['status']=='prepared_source' for r in prepared.values()),
    'fresh_geometry_previews':sum(bool(r.get('preview_path')) for r in prepared.values()),
    'native_readback_queue':len(native_queue),'runtime_enabled_unchanged':sum(r['runtime_enabled'] for r in rows),
    'native_models_measured':sum(x['status']=='measured' for x in native.values()),
    'native_exact_vertex_scans':sum(x.get('vertex_scan')=='complete_compact_ids' for x in native.values()),
    'native_original_closure_missing_assets':sum(bool(x.get('dependencies',{}).get('unresolved_registry_packages')) for x in native.values()),
    'phase_status_counts':dict(collections.Counter(r['phase_status'] for r in rows)),
    'source_missing_texture_assets':[r['asset_id'] for r in prepared.values() if r.get('missing_texture_count')],
    'material_repairs_completed':[repair['asset_id']] if repair else [],
    'active_prepared_sources_with_missing_textures':[r['asset_id'] for r in rows if (r.get('prepared_source') or {}).get('missing_texture_count')],
    'source_missing_UV_render_assets':[r['asset_id'] for r in prepared.values() if r.get('uv_missing_objects')],
    'all_prepared_sources_preserved':all(r.get('source_unchanged') and r.get('source_blend_unchanged') for r in prepared.values()),
    'canonical_descriptive_metadata_application':applied,
    'protected_files':checks,'native_imported_this_run':0,'newly_enabled':0,'areas_generated_or_saved_this_run':0}
write('RESULT.json',summary)

# The catalog remains one identity index. Gallery joins preparation by AssetId.
cards=[]
for r in rows:
    pictures=[];prepared_row=r.get('prepared_source')
    if prepared_row and prepared_row.get('preview'):
        p=pathlib.Path(prepared_row['preview']);pictures.append({'url':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode(),'label':'Fresh Blender material render; not native Unreal appearance' if prepared_row.get('material_repair') else 'Fresh Blender LOD0 geometry preview; materials not shown'})
    for fn in r['native_preview_sources']:
        p=pathlib.Path(fn)
        if p.is_file():pictures.append({'url':'data:image/'+('png' if p.suffix=='.png' else 'jpeg')+';base64,'+base64.b64encode(p.read_bytes()).decode(),'label':'Historical native Unreal image; current appearance not verified'})
    cards.append({k:r.get(k) for k in ['asset_id','name','family_id','category','phase_status','runtime_enabled','blockers','dimensions_native_m_recorded','object_path','prepared_source']}|{'photos':pictures})
template='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Environmentpipeline Prepared Bank</title><style>body{font:16px system-ui;background:#111923;color:#e3edf4;margin:0}header,main{padding:24px 4vw}header{background:#1c2a38}h1{margin:0 0 12px}p{line-height:1.6}input,select,button{padding:10px;background:#233549;color:white;border:1px solid #496681;border-radius:6px}input{width:35vw}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:16px}.card{background:#1b2936;border:1px solid #35485a;border-radius:8px;padding:14px}.card img{width:100%;height:250px;object-fit:contain;background:#111923}.card h3{overflow-wrap:anywhere;font-size:15px}.muted,small{color:#afbfcb}small{display:block;margin:7px 0;overflow-wrap:anywhere}a{color:#94d6fa}details{margin-top:12px}dialog{background:#14212c;color:white;max-width:92vw}dialog img{max-height:80vh;max-width:85vw}.badge{color:#8fe1bd}.empty{height:250px;display:grid;place-items:center;color:#a0aebe}</style>
<header><h1>Environmentpipeline — prepared bank</h1><p>One canonical catalog, joined by AssetId. Existing props and whole buildings first; modular building work deferred.<br>Fresh Blender images show measured LOD0 geometry. Historical Unreal images and current runtime activation are labeled separately. No new native import, activation or area save is claimed.</p><input id="q" placeholder="Search name, identity, family"><select id="filter"><option value="prepared">Fresh Blender preparation</option><option value="all">All 1,223 identities</option><option value="enabled">Existing runtime selection</option><option value="photos">All pictured records</option><option value="blocked">Prepared source with missing texture / UV flag</option></select><p id="count"></p></header><main><div id="grid"></div></main><dialog id="view"><button id="close">Close</button><p id="caption"></p><img id="large"></dialog>
<script>const rows=__DATA__;const $=id=>document.getElementById(id);const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function render(){const q=$('q').value.toLowerCase(),f=$('filter').value;const rr=rows.filter(r=>(!q||[r.name,r.asset_id,r.family_id,r.category].join(' ').toLowerCase().includes(q))&&(f==='all'||f==='prepared'&&r.prepared_source||f==='enabled'&&r.runtime_enabled||f==='photos'&&r.photos.length||f==='blocked'&&r.prepared_source&&(r.prepared_source.missing_texture_count||r.prepared_source.uv_missing_render_objects.length)));$('count').textContent=rr.length+' records shown';$('grid').innerHTML='';for(const r of rr){const e=document.createElement('article');e.className='card';const p=r.prepared_source,d=p?.dimensions_m||r.dimensions_native_m_recorded;e.innerHTML=(r.photos.length?'<img loading="lazy" src="'+r.photos[0].url+'">':'<div class="empty">No current image available</div>')+'<h3>'+esc(r.name)+'</h3><small>'+esc(r.asset_id)+'</small><span class="badge">'+(r.runtime_enabled?'Already enabled in retained runtime':'Not enabled by this preparation')+'</span><small>'+esc(r.photos[0]?.label||'')+'</small><p>'+esc(r.category)+'<br>'+(d?d.map(x=>x.toFixed(3)).join(' × ')+' m':'Dimensions pending')+'</p><small>'+esc(r.phase_status)+'</small><details><summary>Preparation and dependencies</summary><small>'+esc(r.family_id)+'<br>'+esc(r.object_path||'No native catalog object path yet')+'<br>'+esc(r.blockers?.join(' | ')||'No new source blocker recorded')+'</small>'+(p?'<p><a href="'+encodeURI('file:///'+p.blend.replaceAll('\\\\','/'))+'">Prepared Blender source</a></p><small>Render triangles: '+p.triangles_LOD0+'; collision objects: '+p.collision_object_count+'; missing textures: '+p.missing_texture_count+'</small>':'')+'</details>';if(r.photos.length)e.querySelector('img').onclick=()=>{$('large').src=r.photos[0].url;$('caption').textContent=r.name+' — '+r.photos[0].label;$('view').showModal()};$('grid').append(e)}}$('q').oninput=render;$('filter').onchange=render;$('close').onclick=()=>$('view').close();render();</script></html>'''
(OUT/'BANK_GALLERY.html').write_text(template.replace('__DATA__',json.dumps(cards,ensure_ascii=False).replace('</','<\\/')),encoding='utf-8')
write('GALLERY_COVERAGE.json',{'total':len(cards),'pictured':sum(bool(c['photos']) for c in cards),'fresh_blender':sum(bool(c['prepared_source']) for c in cards),'historical_native':len(oldphotos)})
print(json.dumps(summary,indent=2))
