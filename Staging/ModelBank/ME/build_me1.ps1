$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$MeRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $MeRoot '..\..\..')).Path
$OldProjectRoot = 'C:\Users\USER\Documents\Unreal Projects\GIS_WorldBLD'
$LibraryRoot = Join-Path $OldProjectRoot 'SourceData\ModelBanks_Archive\Unreal_Model_Library_2026-09-24'
$HergelSourceRoot = Join-Path $LibraryRoot 'Sources\Hergel'
$IndexPath = Join-Path $ProjectRoot 'Staging\ModelBank\FULL_INDEX.csv'
$SourcesRoot = Join-Path $MeRoot 'Sources'

$Specs = @(
    [pscustomobject]@{ Id = '0013'; Group = 'Whole building'; Role = 'CityBLD static Prefab - Neoclassical' },
    [pscustomobject]@{ Id = '0014'; Group = 'Whole building'; Role = 'CityBLD static Prefab - Neoclassical' },
    [pscustomobject]@{ Id = '0015'; Group = 'Whole building'; Role = 'CityBLD static Prefab - Neoclassical' },
    [pscustomobject]@{ Id = '0016'; Group = 'Whole building'; Role = 'CityBLD static Prefab - Neoclassical' },
    [pscustomobject]@{ Id = '0905'; Group = 'Whole building'; Role = 'CityBLD static Prefab - Arab low-rise' },
    [pscustomobject]@{ Id = '0906'; Group = 'Whole building'; Role = 'CityBLD static Prefab - Arab low-rise' },
    [pscustomobject]@{ Id = '0907'; Group = 'Whole building'; Role = 'CityBLD static Prefab - Arab low-rise' },
    [pscustomobject]@{ Id = '0902'; Group = 'Whole building'; Role = 'CityBLD static Prefab - slum' },
    [pscustomobject]@{ Id = '0903'; Group = 'Whole building'; Role = 'CityBLD static Prefab - slum' },
    [pscustomobject]@{ Id = '0904'; Group = 'Whole building'; Role = 'CityBLD static Prefab - slum' },
    [pscustomobject]@{ Id = '0896'; Group = 'Whole building'; Role = 'CityBLD static Prefab - Middle East block review' },
    [pscustomobject]@{ Id = '0079'; Group = 'Street furniture'; Role = 'RoadBLD PropSpawner' },
    [pscustomobject]@{ Id = '0082'; Group = 'Street furniture'; Role = 'RoadBLD PropSpawner' },
    [pscustomobject]@{ Id = '0083'; Group = 'Street furniture'; Role = 'RoadBLD PropSpawner' },
    [pscustomobject]@{ Id = '0025'; Group = 'Street furniture'; Role = 'RoadBLD PropSpawner or RoadModule review' },
    [pscustomobject]@{ Id = '0060'; Group = 'Street furniture'; Role = 'RoadBLD PropSpawner or RoadModule review' },
    [pscustomobject]@{ Id = '0051'; Group = 'Street furniture'; Role = 'RoadBLD PropSpawner' },
    [pscustomobject]@{ Id = '0081'; Group = 'Street furniture'; Role = 'RoadBLD PropSpawner' },
    [pscustomobject]@{ Id = '0094'; Group = 'Street furniture'; Role = 'RoadBLD PropSpawner' },
    [pscustomobject]@{ Id = '0090'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0091'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0042'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0043'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0034'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0046'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0058'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0059'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0089'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0077'; Group = 'Prop'; Role = 'PCG or controlled prop placement' },
    [pscustomobject]@{ Id = '0650'; Group = 'Prop'; Role = 'Controlled facade or roof prop placement' },
    [pscustomobject]@{ Id = '0039'; Group = 'Vehicle'; Role = 'Manual vehicle placement - not generated' },
    [pscustomobject]@{ Id = '0636'; Group = 'Vegetation'; Role = 'PCG vegetation scatter' },
    [pscustomobject]@{ Id = '0647'; Group = 'Vegetation'; Role = 'PCG vegetation scatter' },
    [pscustomobject]@{ Id = '0958'; Group = 'Vegetation'; Role = 'PCG vegetation scatter' }
)

function Get-TextureRelativePaths {
    param([Parameter(Mandatory)]$SourceReport)
    $paths = @()
    if ($null -ne $SourceReport.material_maps) {
        foreach ($material in $SourceReport.material_maps.PSObject.Properties.Value) {
            foreach ($map in $material.PSObject.Properties.Value) {
                if ($null -ne $map -and $null -ne $map.file -and -not [string]::IsNullOrWhiteSpace([string]$map.file)) {
                    $paths += ([string]$map.file -replace '/', '\')
                }
            }
        }
    }
    return @($paths | Sort-Object -Unique)
}

function Get-SourceFolderLabel {
    param([Parameter(Mandatory)][string]$OriginalSource)
    $normalized = $OriginalSource -replace '\\', '/'
    $folder = $normalized.Substring(0, $normalized.LastIndexOf('/'))
    if ($folder -match '(?i)Need-to-fix') {
        return "$folder [contains Need-to-fix]"
    }
    return $folder
}

function Get-SafeFolderName {
    param([Parameter(Mandatory)][string]$Value)
    $safe = $Value -replace '[<>:"/\\|?*]', '_'
    $safe = $safe -replace '\s+', '_'
    return $safe.TrimEnd('.', ' ')
}

function Get-HashLower {
    param([Parameter(Mandatory)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Copy-VerifiedFile {
    param(
        [Parameter(Mandatory)][string]$Origin,
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][string]$SourceType
    )

    if (-not (Test-Path -LiteralPath $Origin -PathType Leaf)) {
        return [pscustomobject]@{
            origin_path = $Origin
            destination_path = 'missing'
            bytes = 'unknown'
            sha256 = 'unknown'
            source_type = "missing_$SourceType"
        }
    }

    $destinationParent = Split-Path -Parent $Destination
    [void](New-Item -ItemType Directory -Path $destinationParent -Force)
    $originHash = Get-HashLower -Path $Origin
    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $existingHash = Get-HashLower -Path $Destination
        if ($existingHash -ne $originHash) {
            throw "Refusing to overwrite a different existing staged file: $Destination"
        }
    }
    else {
        Copy-Item -LiteralPath $Origin -Destination $Destination
    }

    $destinationHash = Get-HashLower -Path $Destination
    if ($destinationHash -ne $originHash) {
        throw "SHA-256 mismatch after copy: $Destination"
    }

    $destinationItem = Get-Item -LiteralPath $Destination
    return [pscustomobject]@{
        origin_path = $Origin
        destination_path = $Destination
        bytes = $destinationItem.Length
        sha256 = $destinationHash
        source_type = $SourceType
    }
}

function Get-DimensionAssessment {
    param([Parameter(Mandatory)][string]$Id)
    switch ($Id) {
        '0013' { return 'Review: Z exceeds the 6-20 m house example; a taller building may be intended [judgment].' }
        '0014' { return 'Review: Z exceeds the 6-20 m house example [judgment].' }
        '0015' { return 'Review: Z exceeds the 6-20 m house example [judgment].' }
        '0016' { return 'Review: Z exceeds the 6-20 m house example [judgment].' }
        '0905' { return 'Plausible whole-building scale [judgment].' }
        '0906' { return 'Plausible whole-building scale [judgment].' }
        '0907' { return 'Plausible whole-building scale [judgment].' }
        '0902' { return 'Plausible small-shack scale; judged as a shack, not a 6-20 m house [judgment].' }
        '0903' { return 'Plausible shack scale [judgment].' }
        '0904' { return 'Plausible small-shack scale; judged as a shack, not a 6-20 m house [judgment].' }
        '0896' { return 'Not individual-building scale; the 137 x 111 m footprint indicates a block/compound [judgment from measured bounds].' }
        '0079' { return 'Outside the supplied 6-12 m streetlight example: Z is 3.693 m [judgment from measured bounds].' }
        '0082' { return 'Plausible small sign mesh; installed height and face direction are unknown [judgment/U].' }
        '0083' { return 'Plausible small sign mesh; installed height and face direction are unknown [judgment/U].' }
        '0025' { return 'Plausible barrier scale [judgment].' }
        '0060' { return 'Plausible barrier scale [judgment].' }
        '0051' { return 'Plausible bin scale [judgment].' }
        '0081' { return 'Plausible utility-box scale [judgment].' }
        '0094' { return 'Review: Z is 3.380 m, short for a utility pole; intended pole role is unknown [judgment/U].' }
        '0090' { return 'Plausible tank scale [judgment].' }
        '0091' { return 'Plausible narrow tank scale [judgment].' }
        '0042' { return 'Plausible food-cart scale [judgment].' }
        '0043' { return 'Plausible food-cart scale [judgment].' }
        '0034' { return 'Plausible hand-cart scale [judgment].' }
        '0046' { return 'Plausible crate scale [judgment].' }
        '0058' { return 'Plausible gas-cylinder scale; exact semantic role is inferred from the requested role [judgment].' }
        '0059' { return 'Plausible compact-grill scale [judgment].' }
        '0089' { return 'Plausible tire-stack scale [judgment].' }
        '0077' { return 'Plausible stone-stack scale [judgment].' }
        '0650' { return 'Plausible exterior air-conditioner scale [judgment].' }
        '0039' { return 'Outside the supplied 3.5-5.5 m car example: longest extent is 3.171 m [judgment from measured bounds].' }
        '0636' { return 'Plausible small acacia scale [judgment].' }
        '0647' { return 'Plausible low nopal/cactus scale [judgment].' }
        '0958' { return 'Plausible coconut-palm scale [judgment].' }
        default { return 'Unknown [U].' }
    }
}

function Get-DefectAndVerdict {
    param(
        [Parameter(Mandatory)][string]$Id,
        [Parameter(Mandatory)][int64]$Triangles
    )

    $triangleFlag = if ($Triangles -gt 150000) { "LOD0 exceeds 150k ($Triangles) [M]. " } else { '' }
    switch ($Id) {
        '0013' { return [pscustomobject]@{ Defects = 'Height is outside the supplied house example [M]; intended building class is unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0014' { return [pscustomobject]@{ Defects = $triangleFlag + 'Height is outside the supplied house example [M].'; Verdict = 'REVIEW - files only' } }
        '0015' { return [pscustomobject]@{ Defects = $triangleFlag + 'Height is outside the supplied house example [M].'; Verdict = 'REVIEW - files only' } }
        '0016' { return [pscustomobject]@{ Defects = $triangleFlag + 'Height is outside the supplied house example [M].'; Verdict = 'REVIEW - files only' } }
        '0896' { return [pscustomobject]@{ Defects = $triangleFlag + 'Source path contains Need-to-fix and bounds indicate a combined block, not one building [M].'; Verdict = 'REVIEW - files only' } }
        '0902' { return [pscustomobject]@{ Defects = 'Source path contains Need-to-fix [M]; visual defect state is unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0903' { return [pscustomobject]@{ Defects = 'Source path contains Need-to-fix [M]; visual defect state is unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0904' { return [pscustomobject]@{ Defects = 'Source path contains Need-to-fix [M]; visual defect state is unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0905' { return [pscustomobject]@{ Defects = 'Source path contains Need-to-fix [M]; visual defect state is unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0906' { return [pscustomobject]@{ Defects = 'Source path contains Need-to-fix [M]; visual defect state is unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0907' { return [pscustomobject]@{ Defects = 'Source path contains Need-to-fix [M]; visual defect state is unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0079' { return [pscustomobject]@{ Defects = 'Measured height is below the supplied streetlight range [M].'; Verdict = 'REVIEW - files only' } }
        '0082' { return [pscustomobject]@{ Defects = 'Regional sign face/text and placement height are unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0083' { return [pscustomobject]@{ Defects = 'Regional sign face/text and placement height are unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0094' { return [pscustomobject]@{ Defects = 'Measured height is short for an assumed utility-pole role [M/judgment].'; Verdict = 'REVIEW - files only' } }
        '0042' { return [pscustomobject]@{ Defects = $triangleFlag + 'No other defect is reported [M]; appearance is unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0077' { return [pscustomobject]@{ Defects = 'Source report records persisted precision and triangulation repair [M]; rendered result is unknown [U].'; Verdict = 'REVIEW - files only' } }
        '0650' { return [pscustomobject]@{ Defects = 'Source report records one collision mesh, but old Unreal report records zero simple collisions [M].'; Verdict = 'REVIEW - files only' } }
        '0039' { return [pscustomobject]@{ Defects = 'Longest measured extent is below the supplied car range [M].'; Verdict = 'REVIEW - files only' } }
        '0958' { return [pscustomobject]@{ Defects = 'Source notes list unresolved texture GUIDs despite missing_images=[] and PASS [M].'; Verdict = 'REVIEW - files only' } }
        default { return [pscustomobject]@{ Defects = 'No defect is reported in the inspected files [M]; visual/material correctness is unknown [U].'; Verdict = 'PROVISIONAL PASS - files only' } }
    }
}

[void](New-Item -ItemType Directory -Path $SourcesRoot -Force)
$Index = Import-Csv -LiteralPath $IndexPath
$CandidateRows = @()
$ManifestRows = @()
$QualificationRows = @()

foreach ($spec in $Specs) {
    $indexMatches = @($Index | Where-Object { $_.source_bank -eq 'Hergel' -and $_.id -eq $spec.Id })
    if ($indexMatches.Count -ne 1) {
        throw "Expected exactly one Hergel index row for $($spec.Id); found $($indexMatches.Count)."
    }
    $indexRow = $indexMatches[0]

    $unrealReportPath = Join-Path $LibraryRoot "Reports\Hergel\UnrealResults\$($spec.Id).json"
    $sourceReportPath = Join-Path $HergelSourceRoot "Reports\$($spec.Id).json"
    if (-not (Test-Path -LiteralPath $unrealReportPath -PathType Leaf)) {
        throw "Missing required Unreal report: $unrealReportPath"
    }
    if (-not (Test-Path -LiteralPath $sourceReportPath -PathType Leaf)) {
        throw "Missing required source report: $sourceReportPath"
    }

    $unrealReport = Get-Content -LiteralPath $unrealReportPath -Raw | ConvertFrom-Json
    $sourceReport = Get-Content -LiteralPath $sourceReportPath -Raw | ConvertFrom-Json
    $bounds = @($unrealReport.bounds_cm)
    if ($bounds.Count -ne 6) {
        throw "Unexpected bounds format in $unrealReportPath"
    }
    $xMetres = [math]::Round(([double]$bounds[3] - [double]$bounds[0]) / 100.0, 6)
    $yMetres = [math]::Round(([double]$bounds[4] - [double]$bounds[1]) / 100.0, 6)
    $zMetres = [math]::Round(([double]$bounds[5] - [double]$bounds[2]) / 100.0, 6)

    $lods = @($unrealReport.native_reload_audit.lods)
    if ($lods.Count -lt 1) {
        throw "No native reload LOD data in $unrealReportPath"
    }
    $triangles = [int64]$lods[0].triangles
    $materialCount = @($unrealReport.materials).Count
    $textureRelativePaths = @(Get-TextureRelativePaths -SourceReport $sourceReport)
    $textureAbsolutePaths = @()
    foreach ($relativeTexture in $textureRelativePaths) {
        $absoluteTexture = Join-Path $HergelSourceRoot $relativeTexture
        if (Test-Path -LiteralPath $absoluteTexture -PathType Leaf) {
            $textureAbsolutePaths += (Get-Item -LiteralPath $absoluteTexture).FullName
        }
    }
    $textureAbsolutePaths = @($textureAbsolutePaths | Sort-Object -Unique)

    $sourceFolderName = Get-SourceFolderLabel -OriginalSource ([string]$sourceReport.source)
    $flagged = if ($indexRow.import_check_result -eq 'flagged') { 'yes' } elseif ($indexRow.import_check_result -eq 'passed') { 'no' } else { 'unknown' }
    $sourceFbxExists = Test-Path -LiteralPath $indexRow.source_fbx_path -PathType Leaf
    $sourceFbxState = if ($sourceFbxExists) { 'present' } else { 'missing' }

    $CandidateRows += [pscustomobject]@{
        id = "H$($spec.Id)"
        name = $indexRow.name
        category = $indexRow.category
        old_project_uasset_path = $indexRow.old_project_file_path
        source_fbx_path = $indexRow.source_fbx_path
        source_fbx_state = $sourceFbxState
        textures_found_count = $textureAbsolutePaths.Count
        textures_found_paths = ($textureAbsolutePaths -join '; ')
        material_count = $materialCount
        triangle_count_lod0 = $triangles
        bounds_m_x = $xMetres
        bounds_m_y = $yMetres
        bounds_m_z = $zMetres
        bounds_source_report = $unrealReportPath
        pivot_note = 'unknown (not stated in the inspected per-model reports)'
        flagged_in_index = $flagged
        source_folder_name = $sourceFolderName
    }

    $assetFolderName = Get-SafeFolderName -Value ("H$($spec.Id)_$($indexRow.name)")
    $assetDestinationRoot = Join-Path $SourcesRoot $assetFolderName
    [void](New-Item -ItemType Directory -Path $assetDestinationRoot -Force)

    $fbxDestination = if ($sourceFbxExists) {
        Join-Path $assetDestinationRoot ([System.IO.Path]::GetFileName([string]$indexRow.source_fbx_path))
    }
    else {
        Join-Path $assetDestinationRoot ("H$($spec.Id)_missing_source.fbx")
    }
    $ManifestRows += Copy-VerifiedFile -Origin ([string]$indexRow.source_fbx_path) -Destination $fbxDestination -SourceType 'fbx'

    foreach ($relativeTexture in $textureRelativePaths) {
        $textureOrigin = Join-Path $HergelSourceRoot $relativeTexture
        $textureDestination = Join-Path $assetDestinationRoot $relativeTexture
        $ManifestRows += Copy-VerifiedFile -Origin $textureOrigin -Destination $textureDestination -SourceType 'texture'
    }

    $dimensionAssessment = Get-DimensionAssessment -Id $spec.Id
    $defectVerdict = Get-DefectAndVerdict -Id $spec.Id -Triangles $triangles
    $triangleAssessment = if ($triangles -gt 150000) { 'FLAG >150k [M]' } else { 'within supplied 150k flag threshold [M]' }
    $textureAssessment = if ($textureAbsolutePaths.Count -gt 0) { "$($textureAbsolutePaths.Count) present [M]" } else { '0 present [M]' }
    $QualificationRows += [pscustomobject]@{
        id = "H$($spec.Id)"
        name = $indexRow.name
        role = $spec.Role
        bounds = ('{0:N6} x {1:N6} x {2:N6} [M-derived]' -f $xMetres, $yMetres, $zMetres)
        dimension_fit = $dimensionAssessment
        triangles = ('{0:N0} LOD0 [M]' -f $triangles)
        triangle_check = $triangleAssessment
        materials = "$materialCount [M]"
        textures = $textureAssessment
        pivot = 'unknown [U]'
        index_flag = "$flagged [M]"
        defects = $defectVerdict.Defects
        verdict = $defectVerdict.Verdict
    }
}

$CandidatePath = Join-Path $MeRoot 'CANDIDATES_ME.csv'
$ManifestPath = Join-Path $MeRoot 'MANIFEST_ME.csv'
$QualificationPath = Join-Path $MeRoot 'QUALIFICATION_ME.md'
$CandidateRows | Export-Csv -LiteralPath $CandidatePath -NoTypeInformation -Encoding UTF8
$ManifestRows | Export-Csv -LiteralPath $ManifestPath -NoTypeInformation -Encoding UTF8

$qualificationLines = [System.Collections.Generic.List[string]]::new()
$qualificationLines.Add('# Middle Eastern representative set - file-only pre-qualification')
$qualificationLines.Add('')
$qualificationLines.Add('**This is NOT Unreal qualification.** Nothing here is generator-connected, generated, visually verified, or accepted in Environmentpipeline. All 34 assets remain only available in the old bank and staged as source copies. Licensing/provenance for every asset is unknown, so none may be treated as qualified for reuse.')
$qualificationLines.Add('')
$qualificationLines.Add('Evidence labels: **[M]** = measured directly from an inspected file/report; **[M-derived]** = calculated from measured report values; **[U]** = unknown; **[judgment]** = a file-only plausibility judgment, not a measurement. Bounds are `(max-min)/100` from the old Unreal report `bounds_cm`. Triangle counts are old Unreal native-reload LOD0 triangles. The 150k threshold is the manager-supplied flag threshold, not a vendor limit.')
$qualificationLines.Add('')
$qualificationLines.Add('Common measured/unknown state: all 34 indexed `.uasset` and source FBX paths exist [M]; all selected old imports report `PASS`, no selected index row is flagged, and all texture paths counted below exist [M]. No inspected report states a pivot [U]. All old Unreal reports record zero simple collisions [M], so collision suitability is unknown [U]. Every selected old report says procedural module adaptation is not established [M]. Material appearance, scale in the new project, generator compatibility, and rendered quality remain unknown [U].')
$qualificationLines.Add('')
$qualificationLines.Add('| ID | Asset | Proposed role | Bounds m X x Y x Z | Dimension fit | Triangles | Budget check | Materials | Textures | Pivot | Index flagged | File evidence / obvious defect | File-only verdict |')
$qualificationLines.Add('| --- | --- | --- | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- |')
foreach ($row in $QualificationRows) {
    $cells = @($row.id, $row.name, $row.role, $row.bounds, $row.dimension_fit, $row.triangles, $row.triangle_check, $row.materials, $row.textures, $row.pivot, $row.index_flag, $row.defects, $row.verdict)
    $escaped = @($cells | ForEach-Object { ([string]$_) -replace '\|', '\|' })
    $qualificationLines.Add('| ' + ($escaped -join ' | ') + ' |')
}
$qualificationLines.Add('')
$qualificationLines.Add('## Measured exceptions requiring review')
$qualificationLines.Add('')
$qualificationLines.Add('- LOD0 above 150k: H0014 (2,476,576), H0015 (201,055), H0016 (822,754), H0896 (208,623), and H0042 (155,520).')
$qualificationLines.Add('- Need-to-fix provenance path: H0896 and H0902-H0907.')
$qualificationLines.Add('- H0077 records persisted precision/triangulation repair in its source report. H0650 records one source collision mesh while the old Unreal report records zero simple collisions. H0958 records unresolved source texture GUIDs although its six linked texture files exist and the reports say PASS.')
$qualificationLines.Add('- The supplied example bands flag H0079 as short for a 6-12 m streetlight and H0039 as short for a 3.5-5.5 m car. H0013-H0016 exceed the supplied 6-20 m house-height example; they may represent taller buildings, which must be decided by visual inspection.')

Set-Content -LiteralPath $QualificationPath -Value $qualificationLines -Encoding UTF8

$sourceFiles = @(Get-ChildItem -LiteralPath $SourcesRoot -File -Recurse)
$manifestMissing = @($ManifestRows | Where-Object { $_.destination_path -eq 'missing' })
[pscustomobject]@{
    candidates = $CandidateRows.Count
    manifest_rows = $ManifestRows.Count
    staged_files = $sourceFiles.Count
    staged_bytes = ($sourceFiles | Measure-Object -Property Length -Sum).Sum
    missing_manifest_rows = $manifestMissing.Count
    output_candidates = $CandidatePath
    output_manifest = $ManifestPath
    output_qualification = $QualificationPath
} | Format-List
