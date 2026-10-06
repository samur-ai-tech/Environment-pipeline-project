// Copyright WorldBLD LLC. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

class SWindow;
class SWorldBLDAssetLibraryWindow;

class WORLDBLDEDITOR_API FWorldBLDAssetLibraryWindow
{
public:
	static void OpenAssetLibrary();
	static void OpenAssetLibraryWithCategory(const FString& CategoryPath);
	static void CloseAssetLibrary();

private:
	static TWeakPtr<SWindow> AssetLibraryWindow;
	static TWeakPtr<SWorldBLDAssetLibraryWindow> AssetLibraryWidget;
};
