"""Retained source preparation, measurement and geometry thumbnails. No source overwrite."""
import bpy, json, pathlib, sys, time, hashlib, traceback, math, re
import numpy as np
from mathutils import Vector
OUT=pathlib.Path(__file__).resolve().parent
jobs=json.loads((OUT/'BLENDER_QUEUE.json').read_text())
if '--' in sys.argv:
    ids=sys.argv[sys.argv.index('--')+1:]
    if ids: jobs=[j for j in jobs if j['asset_id'] in ids]
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save_json(p,v): p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
for n,job in enumerate(jobs):
    folder=pathlib.Path(job['output_dir']);folder.mkdir(parents=True,exist_ok=True)
    receipt=folder/'ASSET.json'
    if receipt.exists() and json.loads(receipt.read_text()).get('preparation_revision')=='v2_render_collision_lod_roles':
        continue
    started=time.time(); result=dict(job,status='working',blender_version=bpy.app.version_string)
    try:
        if job['source_blend']:
            bpy.ops.wm.open_mainfile(filepath=job['source_blend'],load_ui=False,use_scripts=False)
            result['geometry_source']='existing_archive_blend_preserved'
            result['source_blend_sha256']=sha(job['source_blend'])
        else:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.context.scene.unit_settings.system='METRIC'
            bpy.context.scene.unit_settings.scale_length=1.0
            bpy.ops.import_scene.fbx(filepath=job['source_fbx'],use_manual_orientation=False,global_scale=1.0,use_custom_normals=True,use_image_search=False,use_anim=False)
            result['geometry_source']='fbx_metadata_axis_and_unit_import'
        scene=bpy.context.scene
        scale=float(scene.unit_settings.scale_length)
        meshes=[o for o in scene.objects if o.type=='MESH']
        if not meshes: raise ValueError('no_mesh_objects')
        deps=bpy.context.evaluated_depsgraph_get(); records=[]; all_min=[]; all_max=[]
        for ob in meshes:
            evaluated=ob.evaluated_get(deps);me=evaluated.to_mesh()
            coords=np.empty(len(me.vertices)*3,dtype=np.float64);me.vertices.foreach_get('co',coords);coords=coords.reshape((-1,3))
            mat=np.array(evaluated.matrix_world);world=(coords@mat[:3,:3].T+mat[:3,3])*scale
            if len(world)==0: evaluated.to_mesh_clear();continue
            low=world.min(axis=0);high=world.max(axis=0)
            collision=bool(re.match(r'^(UCX|UBX|USP|UCP)_',ob.name,re.I))
            lodmatch=re.search(r'(?:_|\b)LOD[_-]?(\d+)(?:\b|_|\.)',ob.name,re.I)
            lod=int(lodmatch.group(1)) if lodmatch else 0
            visible_geometry=not collision and lod==0
            if visible_geometry: all_min.append(low);all_max.append(high)
            me.calc_loop_triangles()
            records.append({'name':ob.name,'geometry_role':'collision' if collision else ('render_lod'+str(lod)),'primary_render':visible_geometry,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'uv_layers':[uv.name for uv in me.uv_layers],
                'bounds_m':{'min':low.tolist(),'max':high.tolist()},'matrix_world':[list(v) for v in ob.matrix_world],
                'material_slots':[s.material.name if s.material else None for s in ob.material_slots],
                'negative_transform_determinant':ob.matrix_world.determinant()<0,'has_custom_normals':bool(me.has_custom_normals)})
            evaluated.to_mesh_clear()
            ob['bank_asset_id']=job['asset_id'];ob['bank_family_id']=job['family_id'];ob['bank_role_category']=job['category']
            ob['bank_original_source']=job['source_fbx'];ob['bank_runtime_enabled']=False
            ob.hide_render=not visible_geometry
        low=np.min(all_min,axis=0);high=np.max(all_max,axis=0);size=high-low
        report=json.loads(pathlib.Path(job['source_report']).read_text(encoding='utf-8-sig')) if job['source_report'] else {}
        texture_refs=[]
        for material,maps in report.get('material_maps',{}).items():
            for channel,value in maps.items():
                if not isinstance(value,dict) or not value.get('file'): continue
                p=pathlib.Path(job['source_root'])/value['file']
                texture_refs.append({'material':material,'channel':channel,'path':str(p),'exists':p.is_file(),'uv_scale':value.get('uv_scale'),'uv_offset':value.get('uv_offset')})
        image_records=[]
        for im in bpy.data.images:
            if im.source not in ('FILE','TILED'): continue
            p=pathlib.Path(bpy.path.abspath(im.filepath))
            if not p.is_file():
                candidates={x['path'] for x in texture_refs if pathlib.Path(x['path']).name==p.name and x['exists']}
                if len(candidates)==1: p=pathlib.Path(next(iter(candidates)))
            # Repoint only exact existing filenames; never guess a replacement texture.
            if p.is_file(): im.filepath=str(p)
            image_records.append({'name':im.name,'path':str(p),'exists':p.is_file(),'packed':bool(im.packed_file),'colorspace':im.colorspace_settings.name})
        primary=[x for x in records if x['primary_render']]
        result.update(objects=records,object_count=len(records),primary_render_object_count=len(primary),collision_object_count=sum(x['geometry_role']=='collision' for x in records),triangles=sum(x['triangles'] for x in primary),all_lods_and_collision_triangles=sum(x['triangles'] for x in records),
            bounds_m={'min':low.tolist(),'max':high.tolist()},dimensions_m=size.tolist(),scene_scale_length=scale,
            bottom_center_m=[float((low[0]+high[0])/2),float((low[1]+high[1])/2),float(low[2])],
            anchor_status='measured_AABB_bottom_not_verified_contact_surface',forward_status='requires_role_specific_facing_review',
            texture_references=texture_refs,images=image_records,missing_texture_count=sum(not (x['exists'] or x['packed']) for x in image_records),
            source_report_missing_images=report.get('missing_images',[]),uv_missing_objects=[x['name'] for x in primary if not x['uv_layers']],
            native_imported=False,connected=False,enabled=False,geometry_edited=False,canonical_qualification=False)
        # Native editable source keeps original vertex data, object transforms, slots, UVs and normals.
        asset_file=folder/'Prepared.blend'
        scene['bank_asset_id']=job['asset_id'];scene['bank_preparation']='metadata_and_existing_source_reuse_no_geometry_remodel'
        scene['bank_units_note']='Measurements are world coordinates times scene.unit_settings.scale_length, in metres.'
        scene['bank_native_status']='not_imported_or_enabled_by_this_preparation'
        bpy.ops.wm.save_as_mainfile(filepath=str(asset_file),check_existing=False)
        result['prepared_blend']=str(asset_file)
        # Camera exists only for the thumbnail session and is not part of the saved source.
        for ob in scene.objects:
            if ob.type!='MESH': ob.hide_render=True
        center=Vector(((low+high)/(2*scale)).tolist());extent=max(float(max(size))/scale,0.01)
        camdata=bpy.data.cameras.new('BankPreviewCamera');cam=bpy.data.objects.new('BankPreviewCamera',camdata);scene.collection.objects.link(cam)
        cam.location=center+Vector((1.4,-1.8,1.1))*extent;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        camdata.type='ORTHO';camdata.ortho_scale=extent*1.6;camdata.clip_start=max(extent/10000,0.00001);camdata.clip_end=max(extent*20,100)
        scene.camera=cam;scene.render.engine='BLENDER_WORKBENCH'
        scene.render.resolution_x=480;scene.render.resolution_y=480;scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
        shade=scene.display.shading;shade.light='STUDIO';shade.color_type='SINGLE';shade.single_color=(0.58,0.65,0.69);shade.show_shadows=True;shade.show_cavity=True;shade.cavity_type='BOTH';shade.background_type='WORLD'
        if scene.world is None: scene.world=bpy.data.worlds.new('BankPreviewWorld')
        scene.world.color=(0.045,0.055,0.07)
        scene.render.filepath=str(folder/'GeometryPreview.png')
        bpy.ops.render.render(write_still=True)
        result.update(status='prepared_source',preparation_revision='v2_render_collision_lod_roles',preview_path=scene.render.filepath,preview_kind='actual_LOD0_geometry_studio_render_not_textured_or_native_appearance',seconds=round(time.time()-started,3),source_unchanged=sha(job['source_fbx'])==job['source_fbx_sha256'])
        if job['source_blend']: result['source_blend_unchanged']=sha(job['source_blend'])==result['source_blend_sha256']
    except Exception:
        result.update(status='preparation_error',error=traceback.format_exc(),seconds=round(time.time()-started,3))
    save_json(receipt,result)
    with (OUT/'BLENDER_PROGRESS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'asset_id':job['asset_id'],'status':result['status'],'seconds':result['seconds'],'time':time.time()})+'\n')
    print('BANK_PROGRESS',n+1,len(jobs),job['asset_id'],result['status'],flush=True)
