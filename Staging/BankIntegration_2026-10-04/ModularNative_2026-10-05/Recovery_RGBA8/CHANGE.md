# Preserve valid existing RGBA8 color textures

Native H0017 import stopped because a reused sRGB color texture uses Unreal TC_EDITOR_ICON, whose installed UE 5.8 TextureDefines.h labels it Uncompressed (RGBA8). The current adapter accepts only TC_DEFAULT for color.

This candidate changes only that assertion to also accept TC_EDITOR_ICON for color. Data masks and normal policies remain unchanged. It does not modify shared texture packages. All source geometry, material graphs, identities, holds and destination paths remain unchanged.

This candidate is not loaded or applied. Apply only after the current loaded importer is closed and the request and authority are resealed. H0910 and H0911 receipts retain their original request identity and saved packages. Do not rewrite their evidence or reimport them.
