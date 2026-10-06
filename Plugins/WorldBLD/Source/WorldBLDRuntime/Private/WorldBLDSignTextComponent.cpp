// Copyright WorldBLD LLC. All rights reserved.

#include "WorldBLDSignTextComponent.h"

#include "Engine/Font.h"

namespace
{
	static void SplitByNewlinePreserveEmpty(const FString& InText, TArray<FString>& OutLines)
	{
		OutLines.Reset();

		FString Current;
		for (TCHAR Ch : InText)
		{
			if (Ch == TCHAR('\r'))
			{
				continue;
			}

			if (Ch == TCHAR('\n'))
			{
				OutLines.Add(Current);
				Current.Reset();
				continue;
			}

			Current.AppendChar(Ch);
		}

		OutLines.Add(Current);
	}

	static void SplitWordsByWhitespace(const FString& InLine, TArray<FString>& OutWords)
	{
		OutWords.Reset();

		FString CurrentWord;
		for (TCHAR Ch : InLine)
		{
			if (FChar::IsWhitespace(Ch))
			{
				if (!CurrentWord.IsEmpty())
				{
					OutWords.Add(CurrentWord);
					CurrentWord.Reset();
				}
				continue;
			}

			CurrentWord.AppendChar(Ch);
		}

		if (!CurrentWord.IsEmpty())
		{
			OutWords.Add(CurrentWord);
		}
	}
}

UWorldBLDSignTextComponent::UWorldBLDSignTextComponent()
	: RawText(FText::GetEmpty())
	, BoundsSize(200.0f, 100.0f)
	, Kerning(0.0f)
	, bTruncateVerticalOverflow(true)
	, RenderedTextCache(FText::GetEmpty())
	, bWasTextTruncated(false)
{
}

void UWorldBLDSignTextComponent::OnRegister()
{
	Super::OnRegister();
	UpdateTextLayout();
}

void UWorldBLDSignTextComponent::UpdateTextLayout()
{
	HorizSpacingAdjust = Kerning;

	const FString SourceText = RawText.ToString();
	TArray<FString> WrappedLines;
	BuildWrappedLines(SourceText, WrappedLines);

	const float LineHeight = GetEstimatedLineHeight();
	const float MaxHeight = FMath::Max(0.0f, BoundsSize.Y);
	const int32 MaxLines = (LineHeight > KINDA_SMALL_NUMBER)
		? FMath::FloorToInt(MaxHeight / LineHeight)
		: MAX_int32;

	bWasTextTruncated = false;
	if (bTruncateVerticalOverflow && MaxLines >= 0 && WrappedLines.Num() > MaxLines)
	{
		bWasTextTruncated = true;
		WrappedLines.SetNum(FMath::Max(0, MaxLines));
	}

	const FString RenderedString = BuildRenderedStringFromLines(WrappedLines);
	RenderedTextCache = FText::FromString(RenderedString);
	SetText(RenderedTextCache);
}

FText UWorldBLDSignTextComponent::GetRenderedText() const
{
	return RenderedTextCache;
}

bool UWorldBLDSignTextComponent::WasTextTruncated() const
{
	return bWasTextTruncated;
}

FBoxSphereBounds UWorldBLDSignTextComponent::CalcBounds(const FTransform& LocalToWorld) const
{
	const float HalfWidth = FMath::Max(0.5f, BoundsSize.X * 0.5f);
	const float Height = FMath::Max(1.0f, BoundsSize.Y);

	const FBox LocalBox(
		FVector(0.0f, -HalfWidth, 0.0f),
		FVector(0.0f, HalfWidth, Height)
	);

	return FBoxSphereBounds(LocalBox).TransformBy(LocalToWorld);
}

float UWorldBLDSignTextComponent::MeasureTextWidth(const FString& TextToMeasure) const
{
	if (TextToMeasure.IsEmpty())
	{
		return 0.0f;
	}

	const UFont* FontObject = Font;
	const float WorldSizeValue = FMath::Max(1.0f, WorldSize);

	if (FontObject == nullptr)
	{
		// Fallback estimate when font data is missing.
		return TextToMeasure.Len() * (WorldSizeValue * 0.5f);
	}

	float AccumulatedWidth = 0.0f;
	float CharWidth = 0.0f;
	float CharHeight = 0.0f;

	for (TCHAR Character : TextToMeasure)
	{
		FontObject->GetCharSize(Character, CharWidth, CharHeight);
		AccumulatedWidth += CharWidth;
	}

	// Font advance is pixel-like units around default size; normalize to world size.
	// 16.0f keeps proportions close to TextRender defaults for practical wrapping.
	const float WidthScale = WorldSizeValue / 16.0f;
	const int32 GapCount = FMath::Max(0, TextToMeasure.Len() - 1);
	return (AccumulatedWidth * WidthScale) + (GapCount * Kerning);
}

float UWorldBLDSignTextComponent::GetEstimatedLineHeight() const
{
	const float BaseLineHeight = FMath::Max(1.0f, WorldSize);
	return BaseLineHeight + VertSpacingAdjust;
}

void UWorldBLDSignTextComponent::BuildWrappedLines(const FString& SourceText, TArray<FString>& OutLines) const
{
	OutLines.Reset();

	const float MaxWidth = FMath::Max(1.0f, BoundsSize.X);
	TArray<FString> SourceLines;
	SplitByNewlinePreserveEmpty(SourceText, SourceLines);

	for (const FString& SourceLine : SourceLines)
	{
		if (SourceLine.IsEmpty())
		{
			OutLines.Add(FString());
			continue;
		}

		TArray<FString> Words;
		SplitWordsByWhitespace(SourceLine, Words);

		if (Words.IsEmpty())
		{
			OutLines.Add(FString());
			continue;
		}

		FString CurrentLine;
		for (const FString& Word : Words)
		{
			const FString Candidate = CurrentLine.IsEmpty()
				? Word
				: FString::Printf(TEXT("%s %s"), *CurrentLine, *Word);

			if (!CurrentLine.IsEmpty() && MeasureTextWidth(Candidate) > MaxWidth)
			{
				OutLines.Add(CurrentLine);
				CurrentLine = Word;
				continue;
			}

			CurrentLine = Candidate;
		}

		OutLines.Add(CurrentLine);
	}
}

FString UWorldBLDSignTextComponent::BuildRenderedStringFromLines(const TArray<FString>& InLines) const
{
	if (InLines.IsEmpty())
	{
		return FString();
	}

	FString OutString;
	for (int32 LineIndex = 0; LineIndex < InLines.Num(); ++LineIndex)
	{
		if (LineIndex > 0)
		{
			OutString.AppendChar(TCHAR('\n'));
		}

		OutString.Append(InLines[LineIndex]);
	}

	return OutString;
}

#if WITH_EDITOR
void UWorldBLDSignTextComponent::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);

	const FName PropertyName = PropertyChangedEvent.Property != nullptr
		? PropertyChangedEvent.Property->GetFName()
		: NAME_None;

	if (PropertyName == GET_MEMBER_NAME_CHECKED(UTextRenderComponent, Text))
	{
		RawText = Text;
	}

	UpdateTextLayout();
}
#endif

