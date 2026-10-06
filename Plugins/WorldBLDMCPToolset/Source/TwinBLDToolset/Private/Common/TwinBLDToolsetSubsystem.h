// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "EditorSubsystem.h"

#include "TwinBLDToolsetSubsystem.generated.h"

class UTwinBLDImportSession;
class UWorld;

/**
 * Owns the TwinBLD import session used by every TwinBLD toolset, so loaded OSM data, tile selection and running
 * generation survive between tool calls. The session follows the editor world: when the level changes, the geo
 * origin is re-read from the new level.
 */
UCLASS()
class UTwinBLDToolsetSubsystem : public UEditorSubsystem
{
	GENERATED_BODY()

public:
	virtual void Deinitialize() override;

	/** The shared import session, or null when the editor is unavailable. Marks the calling tool as unattended. */
	static UTwinBLDImportSession* GetSession();

	/** Dialog-free TwinBLD access check. Raises a TwinBLDToolset error and returns false when edits are blocked. */
	static bool EnsureAuthorizedOrRaise();

private:
	UTwinBLDImportSession* GetOrCreateSession();

	UPROPERTY(Transient)
	TObjectPtr<UTwinBLDImportSession> Session;

	TWeakObjectPtr<UWorld> SessionWorld;
};
