// Copyright WorldBLD LLC. All rights reserved. 

#pragma once

#include "GenericPlatform/ICursor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "HitProxies.h"
#include "SceneManagement.h"
#include "PrimitiveDrawWrapper.generated.h"

USTRUCT(BlueprintType)
struct FPrimitiveDrawWrapper
{
	GENERATED_BODY()

	FPrimitiveDrawInterface* PDI {nullptr};
};

USTRUCT(BlueprintType)
struct FPrimitiveDrawParams
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="DebugDraw")
	FLinearColor Color {FColor::Black};

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="DebugDraw")
	float Thickness {0.0f};

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="DebugDraw")
	bool bForegroundDepth {true};

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="DebugDraw")
	bool bScreenSpace {false};

	FPrimitiveDrawParams() = default;
	FPrimitiveDrawParams(const FLinearColor& InColor, float InThickness) :
			Color(InColor), Thickness(InThickness) {}
};

USTRUCT(BlueprintType)
struct FElementHitProxyContext
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="DebugDraw")
	FString String;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="DebugDraw")
	TObjectPtr<UObject> Object {nullptr};

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category="DebugDraw")
	int32 Id {-1};
};

UCLASS()
class WORLDBLDRUNTIME_API UPrimitiveDrawWrapperUtils : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	
	///////////////////////////////////////////////////////////////////////////////////////////////

	UFUNCTION(BlueprintCallable, Category="WorldBLD|Utils|Rendering")
	static void PDI_SetHitProxy(FPrimitiveDrawWrapper Renderer, const FElementHitProxyContext& Context);

	UFUNCTION(BlueprintCallable, Category="WorldBLD|Utils|Rendering")
	static void PDI_ClearHitProxy(FPrimitiveDrawWrapper Renderer);

	UFUNCTION(BlueprintCallable, Category="WorldBLD|Utils|Rendering")
	static void PDI_DrawPoint(FPrimitiveDrawWrapper Renderer, const FPrimitiveDrawParams& DrawParams, const FVector& Location);

	UFUNCTION(BlueprintCallable, Category="WorldBLD|Utils|Rendering")
	static void PDI_DrawLine(FPrimitiveDrawWrapper Renderer, const FPrimitiveDrawParams& DrawParams, const FVector& Start, const FVector& End);

	UFUNCTION(BlueprintCallable, Category="WorldBLD|Utils|Rendering")
	static void PDI_DrawText(FPrimitiveDrawWrapper Renderer, const FPrimitiveDrawParams& DrawParams, const FString& Message, const FVector& Location);

	UFUNCTION(BlueprintCallable, Category="WorldBLD|Utils|Rendering")
	static void PDI_DrawDirectionalArrow(FPrimitiveDrawWrapper Renderer, const FPrimitiveDrawParams& DrawParams, const FVector& Start, const FVector& End, float ArrowSize);

	UFUNCTION(BlueprintCallable, Category="WorldBLDEditor|Utils")
	static void DebugRenderTextToActiveViewportCanvas(const FPrimitiveDrawParams& DrawParams, const FString& Message, const FVector& Location);

	/**
	 * Draws a horizontal circle in the XY-plane at the given center using PDI line segments.
	 * @param Renderer - The PDI wrapper
	 * @param Center - World-space center of the circle
	 * @param Radius - Radius in cm
	 * @param Color - Draw color
	 * @param Thickness - Line thickness (default 8.0)
	 * @param NumSegments - Number of line segments approximating the circle (default 32)
	 */
	UFUNCTION(BlueprintCallable, Category="WorldBLD|Utils|Rendering")
	static void PDI_DrawCircle(FPrimitiveDrawWrapper Renderer, const FVector& Center,
		float Radius, const FLinearColor& Color, float Thickness = 8.0f, int32 NumSegments = 32);
};

///////////////////////////////////////////////////////////////////////////////////////////////////

struct HCityKitSelectableObjectHitProxy : public HHitProxy
{
	DECLARE_HIT_PROXY(WORLDBLDRUNTIME_API);

	FElementHitProxyContext Context;

    HCityKitSelectableObjectHitProxy() : HHitProxy(HPP_Foreground) {}
	HCityKitSelectableObjectHitProxy(FElementHitProxyContext InContext)
		: HHitProxy(HPP_Foreground)
		, Context(InContext)
	{
	}

	// HHitProxy interface
	virtual bool AlwaysAllowsTranslucentPrimitives() const override { return true; }
	virtual EMouseCursor::Type GetMouseCursor() override { return EMouseCursor::Type::Hand; }
	// End of HHitProxy interface
};

///////////////////////////////////////////////////////////////////////////////////////////////////
