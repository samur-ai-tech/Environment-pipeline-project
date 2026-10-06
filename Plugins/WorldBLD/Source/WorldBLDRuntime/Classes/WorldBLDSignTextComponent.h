// Copyright WorldBLD LLC. All rights reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/TextRenderComponent.h"
#include "WorldBLDSignTextComponent.generated.h"

/**
 * Text render component with a physical bounds box for constrained sign text.
 * Supports auto-wrap and optional vertical truncation.
 */
UCLASS(BlueprintType, Blueprintable, ClassGroup = (WorldBLD), meta = (BlueprintSpawnableComponent))
class WORLDBLDRUNTIME_API UWorldBLDSignTextComponent : public UTextRenderComponent
{
	GENERATED_BODY()

public:
	UWorldBLDSignTextComponent();

	// Source text entered by the user. Rendering is generated from this value.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="SignText")
	FText RawText;

	// Physical text area in world units. X = width, Y = height.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="SignText|Layout", meta=(ClampMin="1.0"))
	FVector2D BoundsSize;

	// Additional horizontal spacing between glyphs.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="SignText|Layout")
	float Kerning;

	// Prevents showing lines that exceed the bounds height.
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="SignText|Layout")
	bool bTruncateVerticalOverflow;

	// Recomputes wrapped/truncated text using current bounds and style settings.
	UFUNCTION(BlueprintCallable, CallInEditor, Category="SignText")
	void UpdateTextLayout();

	// Returns the text currently rendered by this component after layout.
	UFUNCTION(BlueprintPure, Category="SignText")
	FText GetRenderedText() const;

	// Returns true when the last layout pass truncated content vertically.
	UFUNCTION(BlueprintPure, Category="SignText")
	bool WasTextTruncated() const;

	// >> UActorComponent
	virtual void OnRegister() override;
	// << UActorComponent

	// >> USceneComponent
	virtual FBoxSphereBounds CalcBounds(const FTransform& LocalToWorld) const override;
	// << USceneComponent

#if WITH_EDITOR
	// >> UObject
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
	// << UObject
#endif

protected:
	float MeasureTextWidth(const FString& TextToMeasure) const;
	float GetEstimatedLineHeight() const;
	void BuildWrappedLines(const FString& SourceText, TArray<FString>& OutLines) const;
	FString BuildRenderedStringFromLines(const TArray<FString>& InLines) const;

private:
	UPROPERTY(Transient)
	FText RenderedTextCache;

	UPROPERTY(Transient)
	bool bWasTextTruncated;
};

