// Copyright WorldBLD LLC. All rights reserved.

#include "IncludedUtilities/SLinePlacementContextMenu.h"
#include "IncludedUtilities/LinePlacementController.h"

#include "LinePlacement/WorldBLDAssetPalette.h"

#include "ContextMenu/Widgets/SWorldBLDAssetPicker.h"
#include "ContextMenu/Widgets/SWorldBLDPropertySlider.h"
#include "ContextMenu/WorldBLDContextMenuFont.h"
#include "ContextMenu/WorldBLDContextMenuStyle.h"

#include "AssetRegistry/AssetData.h"
#include "Engine/Blueprint.h"
#include "Styling/AppStyle.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "SLinePlacementContextMenu"

// ================================================================================================
// Construction
// ================================================================================================

void SLinePlacementContextMenu::Construct(const FArguments& InArgs)
{
	Controller = InArgs._Controller;

	// Spline type options
	SplineTypeOptions.Add(MakeShared<FString>(TEXT("Linear")));
	SplineTypeOptions.Add(MakeShared<FString>(TEXT("Curve")));
	CurrentSplineType = SplineTypeOptions[0]; // Default: Linear

	InteractionModeOptions.Add(MakeShared<FString>(TEXT("Draw")));
	InteractionModeOptions.Add(MakeShared<FString>(TEXT("Edit")));
	CurrentInteractionMode = InteractionModeOptions[0];

	const FMargin RowPadding(0.0f, 4.0f, 0.0f, 0.0f);
	const FMargin LabelPadding(0.0f, 0.0f, 8.0f, 0.0f);

	// Build the content widget
	TSharedRef<SVerticalBox> ContentBox = SNew(SVerticalBox)

		// ---- Asset Palette Picker ----
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(RowPadding)
		[
			SNew(SWorldBLDAssetPicker)
			.Label(LOCTEXT("PaletteLabel", "Asset Palette"))
			.ToolTipText(LOCTEXT("PaletteTooltip",
				"Select a Blueprint subclass of UWorldBLDAssetPalette that defines which meshes to scatter along the line."))
			.AssetClass(UWorldBLDAssetPalette::StaticClass())
			.SelectedAsset(this, &SLinePlacementContextMenu::GetSelectedPaletteAsset)
			.OnAssetSelected(this, &SLinePlacementContextMenu::OnPaletteAssetSelected)
			.bAllowClear(true)
		]

		// ---- Draw / Edit ----
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(RowPadding)
		[
			SNew(SHorizontalBox)

			+ SHorizontalBox::Slot()
			.FillWidth(1.0f)
			.VAlign(VAlign_Center)
			.Padding(LabelPadding)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("InteractionModeLabel", "Mode"))
				.Font(WorldBLDContextMenuFont::Get())
				.ColorAndOpacity(FLinearColor::White)
			]

			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			[
				SAssignNew(InteractionModeCombo, SComboBox<TSharedPtr<FString>>)
				.OptionsSource(&InteractionModeOptions)
				.InitiallySelectedItem(CurrentInteractionMode)
				.OnGenerateWidget(this, &SLinePlacementContextMenu::GenerateInteractionModeOptionWidget)
				.OnSelectionChanged(this, &SLinePlacementContextMenu::OnInteractionModeSelectionChanged)
				[
					SNew(STextBlock)
					.Text(this, &SLinePlacementContextMenu::GetInteractionModeLabel)
					.Font(WorldBLDContextMenuFont::Get())
				]
			]
		]

		// ---- Spline Type ----
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(RowPadding)
		[
			SNew(SHorizontalBox)

			+ SHorizontalBox::Slot()
			.FillWidth(1.0f)
			.VAlign(VAlign_Center)
			.Padding(LabelPadding)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("SplineTypeLabel", "Spline Type"))
				.Font(WorldBLDContextMenuFont::Get())
				.ColorAndOpacity(FLinearColor::White)
			]

			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			[
				SAssignNew(SplineTypeCombo, SComboBox<TSharedPtr<FString>>)
				.OptionsSource(&SplineTypeOptions)
				.InitiallySelectedItem(CurrentSplineType)
				.OnGenerateWidget(this, &SLinePlacementContextMenu::GenerateSplineTypeOptionWidget)
				.OnSelectionChanged(this, &SLinePlacementContextMenu::OnSplineTypeSelectionChanged)
				[
					SNew(STextBlock)
					.Text(this, &SLinePlacementContextMenu::GetSplineTypeLabel)
					.Font(WorldBLDContextMenuFont::Get())
				]
			]
		]

		// ---- Instance Meshes ----
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(RowPadding)
		[
			SNew(SHorizontalBox)

			+ SHorizontalBox::Slot()
			.FillWidth(1.0f)
			.VAlign(VAlign_Center)
			.Padding(LabelPadding)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("InstanceMeshesLabel", "Instance Meshes"))
				.ToolTipText(LOCTEXT("InstanceMeshesTooltip",
					"When enabled, all assets are placed as instances in a single InstancedStaticMeshComponent actor. "
					"When disabled, each asset becomes a separate AStaticMeshActor."))
				.Font(WorldBLDContextMenuFont::Get())
				.ColorAndOpacity(FLinearColor::White)
			]

			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			[
				SNew(SCheckBox)
				.IsChecked(this, &SLinePlacementContextMenu::GetInstanceMeshesCheckState)
				.OnCheckStateChanged(this, &SLinePlacementContextMenu::OnInstanceMeshesCheckStateChanged)
			]
		]

		// ---- Offset Variation ----
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(RowPadding)
		[
			SNew(SWorldBLDPropertySlider)
			.Label(LOCTEXT("OffsetVariationLabel", "Offset Variation"))
			.ToolTipText(LOCTEXT("OffsetVariationTooltip",
				"Random lateral scatter: each asset is displaced left or right by up to this many cm "
				"along the spline's right vector at its placement distance."))
			.UnitLabel(LOCTEXT("OffsetVariationUnit", "cm"))
			.Value(this, &SLinePlacementContextMenu::GetOffsetVariationValue)
			.MinValue(0.0f)
			.MinSliderValue(0.0f)
			.MaxSliderValue(500.0f)
			.DecimalPlaces(0)
			.OnValueChanged(this, &SLinePlacementContextMenu::OnOffsetVariationValueChanged)
		]

		// ---- Separator ----
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(0.0f, 8.0f, 0.0f, 4.0f)
		[
			SNew(SBorder)
			.BorderImage(FAppStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(WorldBLDContextMenuStyle::GetNeutralOutlineColor())
			.Padding(0.0f)
			[
				SNew(SBox).HeightOverride(1.0f)
			]
		]

		// ---- Reset Button ----
		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(RowPadding)
		[
			SNew(SButton)
			.ButtonStyle(&WorldBLDContextMenuStyle::GetNeutralButtonStyle())
			.HAlign(HAlign_Center)
			.OnClicked(this, &SLinePlacementContextMenu::OnSnapMeshesToGroundClicked)
			.ToolTipText(LOCTEXT("SnapMeshesToGroundTooltip",
				"Line trace downward from each placed mesh and move it to the first hit location."))
			[
				SNew(STextBlock)
				.Text(LOCTEXT("SnapMeshesToGroundLabel", "Snap Meshes To Ground"))
				.Font(WorldBLDContextMenuFont::Get())
				.ColorAndOpacity(FLinearColor::White)
			]
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(RowPadding)
		[
			SNew(SButton)
			.ButtonStyle(&WorldBLDContextMenuStyle::GetNeutralButtonStyle())
			.HAlign(HAlign_Center)
			.OnClicked(this, &SLinePlacementContextMenu::OnResetClicked)
			.ToolTipText(LOCTEXT("ResetTooltip", "Clear all placed points and assets to start fresh."))
			[
				SNew(STextBlock)
				.Text(LOCTEXT("ResetLabel", "Reset"))
				.Font(WorldBLDContextMenuFont::Get())
				.ColorAndOpacity(FLinearColor::White)
			]
		]

		+ SVerticalBox::Slot()
		.AutoHeight()
		.Padding(RowPadding)
		[
			SNew(STextBlock)
			.Text(LOCTEXT("ControlsHint", "Shortcuts: Enter=Finish draw  Esc=Draw/Edit/Save Prompt"))
			.Font(WorldBLDContextMenuFont::Get())
			.ColorAndOpacity(FLinearColor(0.7f, 0.7f, 0.7f))
		];

	ChildSlot
	[
		SNew(SBorder)
		.BorderImage(FAppStyle::Get().GetBrush("NoBorder"))
		.Padding(FMargin(8.0f))
		[
			ContentBox
		]
	];
}

// ================================================================================================
// Spline type combo
// ================================================================================================

TSharedRef<SWidget> SLinePlacementContextMenu::GenerateSplineTypeOptionWidget(TSharedPtr<FString> Item) const
{
	return SNew(STextBlock)
		.Text(Item.IsValid() ? FText::FromString(*Item) : FText::GetEmpty())
		.Font(WorldBLDContextMenuFont::Get());
}

void SLinePlacementContextMenu::OnSplineTypeSelectionChanged(TSharedPtr<FString> NewSelection, ESelectInfo::Type SelectionType)
{
	CurrentSplineType = NewSelection;

	if (ULinePlacementController* C = Controller.Get())
	{
		const bool bLinear = NewSelection.IsValid() && (*NewSelection == TEXT("Linear"));
		C->OnSplineTypeChanged(bLinear);
	}
}

FText SLinePlacementContextMenu::GetSplineTypeLabel() const
{
	return CurrentSplineType.IsValid() ? FText::FromString(*CurrentSplineType) : LOCTEXT("SplineTypeNone", "Linear");
}

TSharedRef<SWidget> SLinePlacementContextMenu::GenerateInteractionModeOptionWidget(TSharedPtr<FString> Item) const
{
	return SNew(STextBlock)
		.Text(Item.IsValid() ? FText::FromString(*Item) : FText::GetEmpty())
		.Font(WorldBLDContextMenuFont::Get());
}

void SLinePlacementContextMenu::OnInteractionModeSelectionChanged(TSharedPtr<FString> NewSelection, ESelectInfo::Type SelectionType)
{
	CurrentInteractionMode = NewSelection;
	if (ULinePlacementController* C = Controller.Get())
	{
		const bool bEditMode = NewSelection.IsValid() && (*NewSelection == TEXT("Edit"));
		C->SetInteractionMode(bEditMode ? EWorldBLDViewportSplineMode::Edit : EWorldBLDViewportSplineMode::Draw);
	}
}

FText SLinePlacementContextMenu::GetInteractionModeLabel() const
{
	if (const ULinePlacementController* C = Controller.Get())
	{
		return C->GetInteractionMode() == EWorldBLDViewportSplineMode::Edit
			? LOCTEXT("Mode_Edit", "Edit")
			: LOCTEXT("Mode_Draw", "Draw");
	}
	return CurrentInteractionMode.IsValid() ? FText::FromString(*CurrentInteractionMode) : LOCTEXT("Mode_DrawDefault", "Draw");
}

// ================================================================================================
// Instance meshes checkbox
// ================================================================================================

ECheckBoxState SLinePlacementContextMenu::GetInstanceMeshesCheckState() const
{
	if (const ULinePlacementController* C = Controller.Get())
	{
		return C->bInstanceMeshes ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
	}
	return ECheckBoxState::Unchecked;
}

void SLinePlacementContextMenu::OnInstanceMeshesCheckStateChanged(ECheckBoxState NewState)
{
	if (ULinePlacementController* C = Controller.Get())
	{
		C->OnInstanceMeshesChanged(NewState == ECheckBoxState::Checked);
	}
}

// ================================================================================================
// Asset palette picker
// ================================================================================================

TOptional<FAssetData> SLinePlacementContextMenu::GetSelectedPaletteAsset() const
{
	const ULinePlacementController* C = Controller.Get();
	// This panel is single-controller only, so "unset optional" should not be used here.
	// SWorldBLDAssetPicker interprets unset as "Mixed" (multi-selection state).
	const FAssetData EmptyAssetData;
	if (!IsValid(C))
	{
		return TOptional<FAssetData>(EmptyAssetData);
	}

	if (IsValid(C->PaletteAsset))
	{
		return TOptional<FAssetData>(FAssetData(C->PaletteAsset));
	}

	if (C->PaletteClass)
	{
		// Fallback to class defaults for class-based palettes.
		if (const UWorldBLDAssetPalette* CDO = C->PaletteClass.GetDefaultObject())
		{
			return TOptional<FAssetData>(FAssetData(CDO->GetClass()));
		}
	}

	return TOptional<FAssetData>(EmptyAssetData);
}

void SLinePlacementContextMenu::OnPaletteAssetSelected(const FAssetData& AssetData)
{
	if (ULinePlacementController* C = Controller.Get())
	{
		if (UWorldBLDAssetPalette* PaletteAsset = Cast<UWorldBLDAssetPalette>(AssetData.GetAsset()))
		{
			C->OnPaletteAssetChanged(PaletteAsset);
			return;
		}

		// The picker returns a Blueprint asset — get its generated class
		UClass* SelectedClass = nullptr;

		if (UBlueprint* BP = Cast<UBlueprint>(AssetData.GetAsset()))
		{
			SelectedClass = BP->GeneratedClass;
		}
		else if (UClass* DirectClass = Cast<UClass>(AssetData.GetAsset()))
		{
			SelectedClass = DirectClass;
		}

		if (SelectedClass && SelectedClass->IsChildOf(UWorldBLDAssetPalette::StaticClass()))
		{
			C->OnPaletteClassChanged(SelectedClass);
		}
		else
		{
			C->OnPaletteAssetChanged(nullptr);
		}
	}
}

// ================================================================================================
// Offset variation slider
// ================================================================================================

TOptional<float> SLinePlacementContextMenu::GetOffsetVariationValue() const
{
	if (const ULinePlacementController* C = Controller.Get())
	{
		return TOptional<float>(C->OffsetVariation);
	}
	return TOptional<float>();
}

void SLinePlacementContextMenu::OnOffsetVariationValueChanged(float NewValue)
{
	if (ULinePlacementController* C = Controller.Get())
	{
		C->OnOffsetVariationChanged(NewValue);
	}
}

// ================================================================================================
// Reset button
// ================================================================================================

FReply SLinePlacementContextMenu::OnSnapMeshesToGroundClicked()
{
	if (ULinePlacementController* C = Controller.Get())
	{
		C->SnapPlacedMeshesToGround();
	}
	return FReply::Handled();
}

FReply SLinePlacementContextMenu::OnResetClicked()
{
	if (ULinePlacementController* C = Controller.Get())
	{
		C->ResetPlacement();
	}
	return FReply::Handled();
}

#undef LOCTEXT_NAMESPACE
