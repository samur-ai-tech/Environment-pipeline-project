param([switch]$ReferenceOnly)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$packetRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$photoPath = Join-Path $packetRoot 'References/ref_agrofresas_huelva_planting.jpg'
$modelPath = Join-Path $packetRoot 'Previews/Distance/reference_angle_LOD0.png'
$previewDir = Join-Path $packetRoot 'Previews'
$background = [System.Drawing.Color]::FromArgb(31,36,32)
$foreground = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(235,239,230))
$secondary = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(188,201,177))
$fontTitle = [System.Drawing.Font]::new('Segoe UI',25,[System.Drawing.FontStyle]::Bold)
$fontText = [System.Drawing.Font]::new('Segoe UI',17)
$fontSmall = [System.Drawing.Font]::new('Segoe UI',14)

function Save-ReferenceComparison {
    $photo = [System.Drawing.Image]::FromFile($photoPath)
    $model = [System.Drawing.Image]::FromFile($modelPath)
    try {
        $sheet = [System.Drawing.Bitmap]::new(1640,1420)
        $canvas = [System.Drawing.Graphics]::FromImage($sheet)
        try {
            $canvas.Clear($background)
            $canvas.DrawString('Planting-stage reference and v005 model',$fontTitle,$foreground,20,15)
            $canvas.DrawString('Huelva, Spain | Agrofresas photograph',$fontText,$secondary,20,64)
            $canvas.DrawString('Offline Blender | young leafy transplants',$fontText,$secondary,840,64)
            # One source pixel per output pixel; original photographs remain unchanged.
            # Explicit pixel source/destination rectangles ignore differing photo/PNG DPI metadata.
            $canvas.DrawImage($photo,[System.Drawing.Rectangle]::new(20,108,800,1200),0,0,$photo.Width,$photo.Height,[System.Drawing.GraphicsUnit]::Pixel)
            $canvas.DrawImage($model,[System.Drawing.Rectangle]::new(840,108,800,1200),0,0,$model.Width,$model.Height,[System.Drawing.GraphicsUnit]::Pixel)
            $canvas.DrawString('Photo guides film, shoulders, buried edges and planting stage.',$fontSmall,$foreground,20,1323)
            $canvas.DrawString('Small leafy plugs follow the separate UC ANR photographs.',$fontSmall,$foreground,20,1351)
            $canvas.DrawString('Comparable view along the furrows; people and tunnel frames are not model content.',$fontSmall,$secondary,20,1380)
            $destination = Join-Path $previewDir 'REFERENCE_COMPARISON.png'
            $sheet.Save($destination,[System.Drawing.Imaging.ImageFormat]::Png)
        } finally { $canvas.Dispose(); $sheet.Dispose() }
    } finally { $photo.Dispose(); $model.Dispose() }
    $receipt = [ordered]@{
        file = 'Previews/REFERENCE_COMPARISON.png'
        method = 'Unscaled side-by-side photographic reference and 800x1200 Blender render, with attribution labels; no photo retouching.'
        photo = 'References/ref_agrofresas_huelva_planting.jpg'
        photo_sha256 = (Get-FileHash -LiteralPath $photoPath -Algorithm SHA256).Hash.ToLower()
        render = 'Previews/Distance/reference_angle_LOD0.png'
        render_sha256 = (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLower()
        source_page = 'https://www.agrofresas.com/epoca-de-plantacion-de-fresas/'
        image_original = 'https://www.agrofresas.com/wp-content/uploads/2025/10/Diseno-sin-titulo-2.jpg'
        rights = 'Photograph copyright remains with its owner; retained for visual review, not used in model textures.'
    }
    $receipt.output_sha256 = (Get-FileHash -LiteralPath (Join-Path $previewDir 'REFERENCE_COMPARISON.png') -Algorithm SHA256).Hash.ToLower()
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $packetRoot 'Reports/reference_comparison.json') -Encoding UTF8
}

function Save-DistanceContactSheet {
    $sheet = [System.Drawing.Bitmap]::new(1640,2160)
    $canvas = [System.Drawing.Graphics]::FromImage($sheet)
    try {
        $canvas.Clear($background)
        $canvas.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $canvas.DrawString('Young strawberry beds | 10 rows on a 3% slope',$fontTitle,$foreground,20,16)
        $canvas.DrawString('Detailed geometry',$fontText,$secondary,20,66)
        $canvas.DrawString('Authored lowest LOD',$fontText,$secondary,840,66)
        $rowIndex = 0
        foreach ($distance in @(15,60,150,500)) {
            $top = 112 + $rowIndex * 505
            $canvas.DrawString("$distance m | 1.7 m row centres | fixed 110 degree horizontal field of view",$fontSmall,$foreground,20,$top)
            $col = 0
            foreach ($lod in @('LOD0','LOD3')) {
                $path = Join-Path $packetRoot "Previews/Distance/field_3pct_${distance}m_$lod.png"
                $img = [System.Drawing.Image]::FromFile($path)
                try { $canvas.DrawImage($img,[System.Drawing.Rectangle]::new((20+$col*820),($top+33),800,450)) }
                finally { $img.Dispose() }
                $col++
            }
            $rowIndex++
        }
        $canvas.DrawString('Contact sheet is reduced for browsing. Full 1920x1080 source frames and exact cameras are retained.',$fontSmall,$secondary,20,2140)
        $sheet.Save((Join-Path $previewDir 'SLOPE_DISTANCE_CONTACT_SHEET.png'),[System.Drawing.Imaging.ImageFormat]::Png)
    } finally { $canvas.Dispose(); $sheet.Dispose() }
}

try {
    Save-ReferenceComparison
    if (-not $ReferenceOnly) { Save-DistanceContactSheet }
} finally {
    $foreground.Dispose(); $secondary.Dispose(); $fontTitle.Dispose(); $fontText.Dispose(); $fontSmall.Dispose()
}
