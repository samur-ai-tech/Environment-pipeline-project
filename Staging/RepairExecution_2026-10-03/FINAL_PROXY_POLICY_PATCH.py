"""Append after retained assembly/terrain patches; nothing runs on import.

Generated decoration requests which failed normal native placement are explicitly
omitted from final proxy output. This is not native substitution. Surveyed trees,
external requests, unreleased areas, and disabled assembly remain unchanged.
"""


_final_proxy_policy_previous_filter = cook_bank_proxy_filter


def _final_proxy_generated_identity(role, detail_id, primitives, request, rejection):
    """Return (omission record, preservation reason), conservatively."""
    origins = {'tree': 'geographic_tree', 'street_pole': 'geographic_street_pole'}
    kinds = {'tree': 'procedural_tree_blockout', 'street_pole': 'procedural_street_pole'}
    rules = {'tree': 'terrain_tree', 'street_pole': 'roadside_pole'}
    if request.get('bank_role') != role or request.get('request_origin') != origins[role]:
        return None, 'surveyed_external_or_unconfirmed_request_origin'
    if request.get('placement_rule') != rules[role]:
        return None, 'unconfirmed_request_rule'
    if rejection.get('reason') != 'no_available_candidate':
        return None, 'no_explicit_failed_native_fit'
    if not primitives:
        return None, 'missing_generated_proxy_primitives'
    areas = {str(p.attribValue('source_area_id')) for p in primitives}
    osms = {str(p.attribValue('source_osm_id')).strip() for p in primitives}
    detail_kinds = {str(p.attribValue('detail_kind')) for p in primitives}
    if len(areas) != 1 or next(iter(areas)) not in ('GazaRimal', 'GazaShujaiya'):
        return None, 'area_identity_unconfirmed'
    area_id = next(iter(areas))
    if detail_kinds != {kinds[role]} or request.get('placement_id') != area_id + ':' + detail_id:
        return None, 'generated_primitive_identity_mismatch'
    if role == 'tree':
        if not re.fullmatch(r'tree_-?\d+_-?\d+', detail_id) or osms != {''}:
            return None, 'surveyed_or_nonseeded_tree_preserved'
        if rejection.get('anchor_search_policy') != 'generated_tree_same_seed_cell_max_2m':
            return None, 'bounded_generated_tree_fit_unconfirmed'
    else:
        match = re.fullmatch(r'pole_(\d+)_(\d+)_(\d+)', detail_id)
        if not match or osms != {match.group(1)}:
            return None, 'nonprocedural_or_unconfirmed_road_pole_preserved'
    anchor = rejection.get('source_anchor_m', request.get('P'))
    if not isinstance(anchor, (list, tuple)) or len(anchor) != 3:
        return None, 'original_anchor_missing'
    try:
        anchor = [float(v) for v in anchor]
    except (TypeError, ValueError):
        return None, 'original_anchor_invalid'
    if not all(math.isfinite(v) for v in anchor):
        return None, 'original_anchor_invalid'
    return {'detail_id': detail_id, 'placement_id': request['placement_id'],
            'source_area_id': area_id, 'source_osm_id': next(iter(osms)),
            'request_origin': request['request_origin'], 'original_anchor_m': anchor,
            'reason': 'generated_decoration_request_failed_safe_native_fit',
            'native_fit_failure': dict(rejection),
            'native_substitution': False}, None


def cook_bank_proxy_filter(node, role, detail_kind):
    _final_proxy_policy_previous_filter(node, role, detail_kind)
    if role not in ('tree', 'street_pole'):
        return
    parent, result = node.parent(), node.geometry()
    state = json.loads(result.attribValue('proxy_substitution_json'))
    # Never recategorize previous native substitution as an omission.
    state['native_removed_count'] = state['removed_count']
    state['omitted_generated_ids'] = []
    state['omitted_generated_count'] = 0
    state['omitted_generated_requests'] = []
    state['omission_preserved_diagnostics'] = []
    state['omission_policy'] = 'explicit_failed_generated_decoration_only_v1'
    report = parent.evalParm('bank_receipt_file').strip()
    receipt = json.loads(Path(report).read_text(encoding='utf-8')) if report else {}
    scope_failure = None
    if not parent.evalParm('bank_release_enabled') or parent.evalParm('technical_preview_enabled'):
        scope_failure = 'normal_released_generation_required'
    elif (receipt.get('release_enabled') is not True or receipt.get('technical_preview_enabled') is not False
          or receipt.get('nonbuilding_mode') != 'release'
          or receipt.get('request_scope') != 'complete_augmented_selector_input'):
        scope_failure = 'current_normal_selector_receipt_required'
    elif not receipt.get('active_candidate_roles', {}).get(role, 0):
        scope_failure = 'supported_native_role_required'
    elif any(result.findPrimAttrib(key) is None for key in
             ('detail_id', 'detail_kind', 'source_area_id', 'source_osm_id')):
        scope_failure = 'proxy_source_provenance_missing'
    groups = {}
    if scope_failure is None:
        for primitive in result.prims():
            if primitive.attribValue('detail_kind') == detail_kind:
                groups.setdefault(str(primitive.attribValue('detail_id')), []).append(primitive)
        areas = {str(p.attribValue('source_area_id')) for ps in groups.values() for p in ps}
        try:
            if len(areas) != 1 or next(iter(areas)) not in ('GazaRimal', 'GazaShujaiya'):
                scope_failure = 'named_normal_area_required' if groups else 'no_remaining_generated_proxies'
            elif _assembly_contract(parent, next(iter(areas))) is None:
                scope_failure = 'enabled_scoped_assembly_contract_required'
        except (TypeError, ValueError, KeyError) as exc:
            scope_failure = 'assembly_contract_validation_failed:' + str(exc)
    if scope_failure:
        state['omission_preserved_diagnostics'].append({'reason': scope_failure})
    else:
        requests, rejected = {}, {}
        for record in receipt.get('requests', []):
            requests.setdefault(record.get('placement_id'), []).append(record)
        for record in receipt.get('placement_diagnostics', {}).get(role, {}).get('rejected_requests', []):
            rejected.setdefault(record.get('placement_id'), []).append(record)
        delete = []
        for detail_id in state['remaining_ids']:
            primitives = groups.get(detail_id, [])
            area_id = str(primitives[0].attribValue('source_area_id')) if primitives else ''
            placement_id = area_id + ':' + detail_id
            if len(requests.get(placement_id, [])) != 1 or len(rejected.get(placement_id, [])) != 1:
                record, reason = None, 'unique_current_request_and_failure_required'
            else:
                record, reason = _final_proxy_generated_identity(
                    role, detail_id, primitives, requests[placement_id][0], rejected[placement_id][0])
            if record:
                state['omitted_generated_requests'].append(record)
                delete.extend(primitives)
            else:
                state['omission_preserved_diagnostics'].append({'detail_id': detail_id, 'reason': reason})
        result.deletePrims(delete, keep_points=False)
        omitted = {r['detail_id'] for r in state['omitted_generated_requests']}
        state['omitted_generated_ids'] = sorted(omitted)
        state['omitted_generated_count'] = len(omitted)
        state['remaining_ids'] = [i for i in state['remaining_ids'] if i not in omitted]
        state['remaining_count'] = len(state['remaining_ids'])
        if result.findGlobalAttrib('detail_ids_json') is not None:
            ids = json.loads(result.attribValue('detail_ids_json'))
            _set_detail(result, 'detail_ids_json', json.dumps([i for i in ids if i not in omitted]))
    state['remaining_primitives'] = len(result.prims())
    if state['source_count'] != state['removed_count'] + state['omitted_generated_count'] + state['remaining_count']:
        raise ValueError('proxy_native_omitted_remaining_accounting_mismatch')
    _set_detail(result, 'proxy_substitution_json', json.dumps(state, sort_keys=True))
    if report:
        receipt.setdefault('proxy_outputs', {})[role] = state
        Path(report).write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding='utf-8')
