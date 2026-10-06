// Copyright WorldBLD LLC. All rights reserved.

#include "Common/TwinBLDToolsetSubsystem.h"

#include "Authorization/TwinBLDAuthGate.h"
#include "BLDToolsetUtils.h"
#include "Editor.h"
#include "Engine/World.h"
#include "CoreGlobals.h"
#include "TwinBLDImportSession.h"

#include UE_INLINE_GENERATED_CPP_BY_NAME(TwinBLDToolsetSubsystem)

void UTwinBLDToolsetSubsystem::Deinitialize()
{
	if (Session)
	{
		Session->CancelAllAsyncWork();
		Session = nullptr;
	}
	Super::Deinitialize();
}

UTwinBLDImportSession* UTwinBLDToolsetSubsystem::GetSession()
{
	BLDToolset::MarkCurrentCallUnattended();
	UTwinBLDToolsetSubsystem* Subsystem = GEditor ? GEditor->GetEditorSubsystem<UTwinBLDToolsetSubsystem>() : nullptr;
	return Subsystem ? Subsystem->GetOrCreateSession() : nullptr;
}

bool UTwinBLDToolsetSubsystem::EnsureAuthorizedOrRaise()
{
	BLDToolset::MarkCurrentCallUnattended();
	if (GIsAutomationTesting)
	{
		return true;
	}

	FText AccessError;
	if (TwinBLDAuthGate::AllowEdits(AccessError))
	{
		return true;
	}

	BLDToolset::RaiseError(TEXT("TwinBLDToolset"), AccessError.ToString());
	return false;
}

UTwinBLDImportSession* UTwinBLDToolsetSubsystem::GetOrCreateSession()
{
	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		return nullptr;
	}

	if (!Session)
	{
		// The constructor restores the geo origin stored in the current level.
		Session = NewObject<UTwinBLDImportSession>(this, NAME_None, RF_Transient);
		SessionWorld = World;
	}
	else if (SessionWorld.Get() != World)
	{
		// A different level is open. Tile selection and origin belong to the old level.
		if (!Session->bGenerationInProgress && !Session->IsSatelliteImportInProgress())
		{
			Session->ClearTileSelection();
		}
		Session->RestorePersistedGeoOriginFromLevel();
		SessionWorld = World;
	}

	return Session;
}
