"""Reusable v015 context and spatial policies; no asset/site-specific runtime code."""
NONBUILDING_RULES.update({'whole_building':'building_footprint',
                         'road_surface':'generated_road_material',
                         'sidewalk_surface':'generated_sidewalk_material'})

SURFACE_ROLES = {'road_surface', 'sidewalk_surface'}
PLACEMENT_PRIORITY = {'whole_building':0, 'tree':1, 'street_pole':2,
                      'street_prop':3, 'shrub':4, 'small_prop':5, 'understory':6}

def _permanent_surface_rows(parent, rows):
    """Materials have use/scope/revision contracts, never mesh contact contracts."""
    if parent.evalParm('technical_preview_enabled'):
        return [r for r in rows if r['RequestRole'] in SURFACE_ROLES and
                int(r['TechnicalPreviewEligible']) and not int(r['ExplicitHold']) and not r['HoldReasons']]
    if not parent.evalParm('bank_release_enabled'):
        return []
    selected=[]
    for row in rows:
        if row['RequestRole'] not in SURFACE_ROLES or not int(row['RunEligible']):
            continue
        valid=(not int(row['ExplicitHold']) and not row['HoldReasons'] and
               row['Role']==row['RequestRole'] and NONBUILDING_RULES[row['Role']]==row['PlacementRule'] and
               row['ReleaseId']==parent.evalParm('catalog_release_id').strip() and
               row['DecisionId'] and row['FamilyId'] and row['VariantId'] and
               row['StyleSet']==parent.evalParm('bank_style_set').strip() and
               math.isfinite(float(row['SelectionWeight'])) and float(row['SelectionWeight'])>0 and
               row['PlacementScope']=='area_zone' and not row['AllowedPlacementIds'] and
               bank_v2_tokens(row['AllowedAreas'],'AllowedAreas') and
               bank_v2_tokens(row['AllowedZones'],'AllowedZones') and
               re.fullmatch(r'[a-fA-F0-9]{64}',row['AssetRevision']) and
               re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+',row['ObjectPath']))
        if not valid:
            _fail('Invalid enabled generated-surface material contract: '+row['AssetId'])
        selected.append(row)
    return selected

def _permanent_rectangle(row, request, margin=0.0):
    samples=_permanent_footprint(row,request)
    if not margin:
        return [samples[i] for i in (0,2,8,6)]
    p=request.position()
    theta=math.radians(float(request.attribValue('bank_yaw_degrees'))-
                      {'+X':0,'+Y':90,'-X':180,'-Y':-90}.get(row['ForwardAxis'],0))
    c,s=math.cos(theta),math.sin(theta)
    rx=(float(row['BoundsMaxXCm'])-float(row['BoundsMinXCm']))/200.0+margin
    rz=(float(row['BoundsMaxYCm'])-float(row['BoundsMinYCm']))/200.0+margin
    return [(p[0]+x*c-z*s,p[2]+x*s+z*c) for x,z in [(-rx,-rz),(rx,-rz),(rx,rz),(-rx,rz)]]

def _permanent_rectangles_overlap(a,b):
    # Separating axes use actual oriented footprints instead of circumcircles.
    for ring in (a,b):
        for start,end in zip(ring,ring[1:]+ring[:1]):
            axis=(start[1]-end[1],end[0]-start[0])
            pa=[p[0]*axis[0]+p[1]*axis[1] for p in a]
            pb=[p[0]*axis[0]+p[1]*axis[1] for p in b]
            if max(pa)<=min(pb)+1e-8 or max(pb)<=min(pa)+1e-8:
                return False
    return True

def _permanent_spacing_ok(row,request,placed):
    rectangle=_permanent_rectangle(row,request,0.5)
    position=request.position()
    for prior in placed.get('all',()):
        if _permanent_rectangles_overlap(rectangle,prior['clearance_rectangle']):
            return False
        if row['RequestRole']==prior['role'] and math.hypot(position[0]-prior['x'],position[2]-prior['z']) < max(float(row['MinSpacingCm'])/100.0,prior['spacing']):
            return False
    return True

def _permanent_polygon_covers_rectangle(ring,rectangle):
    # Clip the complete concave geographic polygon in rectangle-local space.
    # Its intersection area must equal the entire native footprint area.
    origin=rectangle[0]
    ex=np.asarray(rectangle[1])-origin;ez=np.asarray(rectangle[3])-origin
    width=float(np.linalg.norm(ex));depth=float(np.linalg.norm(ez))
    if width<=0 or depth<=0:
        return False
    ex/=width;ez/=depth
    local=[(float(np.dot(np.asarray(p)-origin,ex)),float(np.dot(np.asarray(p)-origin,ez))) for p in ring]
    clipped=_clip_polygon(local,(0,width,0,depth))
    covered=abs(_signed_area(clipped)) if len(clipped)>=3 else 0.0
    return abs(covered-width*depth)<=max(1e-6,width*depth*1e-8)

def _permanent_ground_samples(row,request):
    # Cover the entire native footprint at the terrain mask's metre resolution.
    rectangle=_permanent_rectangle(row,request,1.0)
    origin=np.asarray(rectangle[0]);ex=np.asarray(rectangle[1])-origin;ez=np.asarray(rectangle[3])-origin
    width=float(np.linalg.norm(ex));depth=float(np.linalg.norm(ez))
    return [tuple(origin+ex*u+ez*v) for u in np.linspace(0,1,max(2,int(math.ceil(width))+1))
            for v in np.linspace(0,1,max(2,int(math.ceil(depth))+1))]

def _permanent_context_matches(parent,row,area,zone):
    style=parent.evalParm('environment_style_set').strip()
    if not style or row['StyleSet'] != style:
        return False
    areas=bank_v2_tokens(row['AllowedAreas'],'AllowedAreas')
    if area not in areas and 'any_validated_area' not in areas:
        return False
    return zone in bank_v2_tokens(row['AllowedZones'],'AllowedZones')

_permanent_previous_requests=cook_nonbuilding_requests
def cook_nonbuilding_requests(node):
    _permanent_previous_requests(node)
    parent,geo=node.parent(),node.geometry()
    zone=geo.findPointAttrib('bank_zone') or geo.addAttrib(hou.attribType.Point,'bank_zone','')
    zones={'tree':'open_ground','shrub':'open_ground','understory':'open_ground',
           'small_prop':'open_ground','street_prop':'roadside','street_pole':'roadside',
           'sign':'building_wall','rooftop_utility':'building_roof'}
    for point in geo.points():
        point.setAttribValue(zone,zones.get(point.attribValue('bank_role'),''))
    if not parent.evalParm('nonbuilding_enabled') or parent.evalParm('bank_inspection_only'):
        return
    active=_nonbuilding_active_rows(parent,_nonbuilding_v3_rows(node.inputs()[3].geometry()))
    if not any(r['RequestRole']=='whole_building' for r in active):
        return
    attrs={name:geo.findPointAttrib(name) or geo.addAttrib(hou.attribType.Point,name,0.0 if name in ('bank_yaw_degrees','building_height_m') else '')
           for name in ('placement_id','bank_role','placement_rule','bank_yaw_degrees','source_area_id',
                        'source_osm_id','source_detail_id','request_origin','bank_zone','building_footprint_json','building_height_m')}
    for pad in node.inputs()[2].geometry().prims():
        if pad.type()!=hou.primType.Polygon or not pad.isClosed():
            continue
        ring=[(v.point().position()[0],v.point().position()[2]) for v in pad.vertices()]
        if len(ring)<3:
            continue
        x,z=_centroid(ring)
        if not _point_in_polygon((x,z),ring):
            continue
        _,a,b=max((math.hypot(b[0]-a[0],b[1]-a[1]),a,b) for a,b in zip(ring,ring[1:]+ring[:1]))
        osm=str(pad.attribValue('source_osm_id'));area=str(pad.attribValue('source_area_id'))
        detail='building_'+osm
        _nonbuilding_add_request(geo,attrs,(x,float(pad.attribValue('base_m')),z),{
            'placement_id':area+':'+detail,'bank_role':'whole_building','placement_rule':'building_footprint',
            'bank_yaw_degrees':math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])),
            'source_area_id':area,'source_osm_id':osm,'source_detail_id':detail,'request_origin':'geographic_building_footprint',
            'bank_zone':'building_'+str(pad.attribValue('building_class')),
            'building_footprint_json':json.dumps(ring),'building_height_m':float(pad.attribValue('height_m'))})

def _permanent_footprint(row,request):
    # Native Unreal centimetres -> Houdini metres. The request anchors the bbox center.
    rx=(float(row['BoundsMaxXCm'])-float(row['BoundsMinXCm']))/200.0
    rz=(float(row['BoundsMaxYCm'])-float(row['BoundsMinYCm']))/200.0
    correction={'+X':0,'+Y':90,'-X':180,'-Y':-90}.get(row['ForwardAxis'],0)
    theta=math.radians(float(request.attribValue('bank_yaw_degrees'))-correction)
    c,s=math.cos(theta),math.sin(theta);p=request.position()
    return [(p[0]+x*c-z*s,p[2]+x*s+z*c) for x,z in
            [(-rx,-rz),(0,-rz),(rx,-rz),(-rx,0),(0,0),(rx,0),(-rx,rz),(0,rz),(rx,rz)]]

def _permanent_fit_setup(node):
    terrain=node.inputs()[3].geometry()
    return {'box':_local_box(_package_for_sop(node.parent())),
            'roads':_exclusion_mask(terrain,'RoadBed',1),
            'pads':_exclusion_mask(terrain,'BuildingPad',1),
            'steep':_grid_array(_volume(terrain,'Steep')),
            'height':_grid_array(_volume(terrain,'height'))}

def _permanent_rejection(diag,reason,placement_id=None):
    counts=diag['rejection_reasons'];counts[reason]=counts.get(reason,0)+1
    if placement_id:
        diag['rejected_requests'].append({'placement_id':placement_id,'reason':reason})

def _permanent_candidate_rejection(node,row,request,fit):
    style=node.parent().evalParm('environment_style_set').strip()
    if not style or row['StyleSet'] != style:
        return 'environment_style'
    areas=bank_v2_tokens(row['AllowedAreas'],'AllowedAreas')
    if request.attribValue('source_area_id') not in areas and 'any_validated_area' not in areas:
        return 'environment_area'
    if request.attribValue('bank_zone') not in bank_v2_tokens(row['AllowedZones'],'AllowedZones'):
        return 'environment_zone'
    samples=_permanent_footprint(row,request)
    if row['RequestRole']=='whole_building':
        ring=json.loads(request.attribValue('building_footprint_json'))
        height=(float(row['BoundsMaxZCm'])-float(row['BoundsMinZCm']))/100.0
        desired=float(request.attribValue('building_height_m'))
        area=(float(row['BoundsMaxXCm'])-float(row['BoundsMinXCm']))*(float(row['BoundsMaxYCm'])-float(row['BoundsMinYCm']))/10000.0
        if not 0.5*desired<=height<=1.5*desired:
            return 'building_height'
        if area<0.45*abs(_signed_area(ring)):
            return 'building_coverage'
        if not _permanent_polygon_covers_rectangle(ring,_permanent_rectangle(row,request)):
            return 'building_footprint'
        return None
    if row['PlacementRule'] in ('mount_sign','roof_anchor'):
        return 'unsupported_attachment_contract'
    samples=_permanent_ground_samples(row,request)
    if not all(_nonbuilding_ground_ok(x,z,fit['roads'],fit['pads'],fit['steep'],fit['box']) for x,z in samples):
        return 'ground_mask_or_slope'
    heights=_sample_grid(fit['height'],[x for x,z in samples],[z for x,z in samples])
    if float(np.max(heights)-np.min(heights)) > 0.5:
        return 'terrain_height_spread'
    return None

def _permanent_candidate_fits(node,row,request,fit):
    return _permanent_candidate_rejection(node,row,request,fit) is None


def cook_permanent_surface_material(node):
    parent,geo=node.parent(),node.geometry()
    geo.clear();geo.merge(node.inputs()[0].geometry())
    lane='road_surface' if node.name()=='catalog_road_material' else 'sidewalk_surface'
    zone='road' if lane=='road_surface' else 'sidewalk'
    info=_package_for_sop(parent)
    rows=_permanent_surface_rows(parent,_nonbuilding_v3_rows(node.inputs()[1].geometry()))
    candidates=[r for r in rows if r['RequestRole']==lane and _permanent_context_matches(parent,r,info['area_id'],zone)]
    preview=bool(parent.evalParm('technical_preview_enabled'))
    chosen=_nonbuilding_choose(candidates,int(parent.evalParm('seed')),info['area_id']+':'+lane,preview)
    if chosen is None:
        if not preview:
            _fail('Required normal surface lane has no scoped material: '+lane)
        _set_detail(geo,'surface_material_selection_json',json.dumps({'lane':lane,'selected':None,'reason':'no_context_eligible_catalog_material'}))
        return
    # Long planar road/sidewalk faces sampled only at their perimeter can cut
    # through a non-planar Landscape. Brick the actual geographic surface on
    # the same metre grid, then sample every resulting point on that terrain.
    terrain_node=node.inputs()[0]
    if terrain_node is None or len(terrain_node.inputs())<3:
        _fail('Missing permanent surface terrain source: '+lane)
    height=_grid_array(_volume(terrain_node.inputs()[2].geometry(),'height'))
    original=[(_xy(prim),{a.name():prim.attribValue(a) for a in geo.primAttribs()}) for prim in geo.prims()]
    geo.deletePrims(list(geo.prims()),keep_points=False)
    attrs={a.name():a for a in geo.primAttribs()}
    lift=0.08 if lane=='road_surface' else 0.16
    for ring,values in original:
        xmin,xmax=min(p[0] for p in ring),max(p[0] for p in ring)
        zmin,zmax=min(p[1] for p in ring),max(p[1] for p in ring)
        for iz in range(math.floor(zmin),math.ceil(zmax)):
            for ix in range(math.floor(xmin),math.ceil(xmax)):
                cell=_condition_surface_polygon(_clip_polygon(ring,(ix,ix+1,iz,iz+1)))
                if not cell:
                    continue
                heights=_sample_grid(height,[x for x,z in cell],[z for x,z in cell])
                _add_polygon(geo,[(x,float(y)+lift,z) for (x,z),y in zip(cell,heights)],values,attrs)
    if original and not geo.prims():
        _fail('Terrain-conforming surface unexpectedly empty: '+lane)
    material=_attr(geo,hou.attribType.Prim,'unreal_material','')
    uv=geo.findVertexAttrib('uv') or geo.addAttrib(hou.attribType.Vertex,'uv',(0.0,0.0,0.0))
    # Native selected masters multiply UV0 by .25 for base/normal/roughness:
    # one coordinate unit per metre therefore gives their intended four-metre repeat.
    for prim in geo.prims():
        prim.setAttribValue(material,chosen['ObjectPath'])
        for vertex in prim.vertices():
            p=vertex.point().position();vertex.setAttribValue(uv,(p[0],p[2],0.0))
    _set_detail(geo,'surface_material_selection_json',json.dumps({'lane':lane,'asset_id':chosen['AssetId'],
                'path':chosen['ObjectPath'],'style':chosen['StyleSet'],'uv_coordinate_repeat_m':1.0,
                'native_main_texture_repeat_m':4.0,'native_macro_noise_repeat_m':20.0,'technical_preview':preview}))

def cook_permanent_building_replacement(node):
    geo=node.geometry();geo.clear();geo.merge(node.inputs()[0].geometry())
    instances=node.inputs()[1].geometry()
    ids={p.attribValue('source_osm_id') for p in instances.points() if p.attribValue('bank_role')=='whole_building'}
    attr=geo.findPrimAttrib('source_osm_id')
    if ids and attr:
        geo.deletePrims([p for p in geo.prims() if p.attribValue(attr) in ids],keep_points=False)
    _set_detail(geo,'native_building_replaced_osm_ids_json',json.dumps(sorted(ids)))

_permanent_selector_without_material_overrides=cook_nonbuilding_selector
def cook_nonbuilding_selector(node):
    """Emit native slot overrides from saved catalog metadata, preserving source assets."""
    _permanent_selector_without_material_overrides(node)
    geo=node.geometry();parent=node.parent()
    overrides=json.loads(parent.evalParm('bank_instance_materials') or '{}')
    if not isinstance(overrides,dict):_fail('Instance material metadata must map mesh paths to slot paths')
    for mesh,slots in overrides.items():
        if not re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+',mesh) or not isinstance(slots,list) or not 1<=len(slots)<=64:
            _fail('Invalid native mesh material metadata')
        if any(not re.fullmatch(r'/Game/[A-Za-z0-9_/]+\.[A-Za-z0-9_]+',p) for p in slots):
            _fail('Invalid native material slot path')
    affected=0
    if geo.findPointAttrib('unreal_instance'):
        for point in geo.points():
            slots=overrides.get(point.attribValue('unreal_instance'))
            if slots:
                affected+=1
                for index,path in enumerate(slots):
                    attribute=geo.findPointAttrib('unreal_material'+str(index)) or geo.addAttrib(hou.attribType.Point,'unreal_material'+str(index),'')
                    point.setAttribValue(attribute,path)
    digest=hashlib.sha256(json.dumps(overrides,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    _set_detail(geo,'instance_material_metadata_sha256',digest)
    if geo.findGlobalAttrib('bank_catalog_readback_json'):
        receipt=json.loads(geo.attribValue('bank_catalog_readback_json'))
        receipt.update(instance_material_metadata_sha256=digest,instance_material_overridden_placements=affected)
        _set_detail(geo,'bank_catalog_readback_json',json.dumps(receipt,sort_keys=True))
        report=parent.evalParm('bank_receipt_file').strip()
        if report:Path(report).write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding='utf-8')


def cook_stage(node,function_name):
    """Retain exact stage errors from the actual Engine cook, then fail normally."""
    try:
        globals()[function_name](node)
    except Exception:
        import traceback
        parent=node.parent()
        report=parent.evalParm('bank_receipt_file').strip()
        if report:
            error_path=Path(report+'.errors.json')
            errors=json.loads(error_path.read_text()) if error_path.exists() else {}
            errors[node.name()]={'function':function_name,'traceback':traceback.format_exc()}
            error_path.write_text(json.dumps(errors,indent=2),encoding='utf-8')
        raise
