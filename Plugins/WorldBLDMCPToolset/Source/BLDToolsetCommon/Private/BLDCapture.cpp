// Copyright WorldBLD LLC. All rights reserved.

#include "BLDCapture.h"

#include "Containers/Ticker.h"
#include "Editor.h"
#include "ImageUtils.h"
#include "LevelEditorViewport.h"
#include "RenderingThread.h"
#include "UnrealClient.h"
#include "UObject/StrongObjectPtr.h"

namespace BLDCapturePrivate
{
	/** Frames drawn after moving the camera so streaming and virtual textures can catch up. */
	constexpr int32 SettleFrames = 4;

	struct FPendingCapture
	{
		TStrongObjectPtr<UBLDCaptureAsyncResult> Result;
		BLDCapture::FRequest Request;
	};

	FLevelEditorViewportClient* FindPerspectiveViewport()
	{
		if (GCurrentLevelEditingViewportClient
			&& GCurrentLevelEditingViewportClient->IsPerspective()
			&& GCurrentLevelEditingViewportClient->Viewport)
		{
			return GCurrentLevelEditingViewportClient;
		}

		if (GEditor)
		{
			for (FLevelEditorViewportClient* Client : GEditor->GetLevelViewportClients())
			{
				if (Client && Client->IsPerspective() && Client->Viewport)
				{
					return Client;
				}
			}
		}

		return nullptr;
	}

	bool IsViewportClientAlive(const FLevelEditorViewportClient* Client)
	{
		return GEditor && Client && GEditor->GetLevelViewportClients().Contains(Client) && Client->Viewport;
	}

	void FrameBounds(FLevelEditorViewportClient* Client, const FBox& Bounds, const EBLDCaptureView View, const double Padding)
	{
		const FVector Center = Bounds.GetCenter();
		const FVector Extent = Bounds.GetExtent();
		const FIntPoint ViewportSize = Client->Viewport->GetSizeXY();
		const double Aspect = ViewportSize.Y > 0 ? static_cast<double>(ViewportSize.X) / ViewportSize.Y : 16.0 / 9.0;
		const double HalfHorizontalFov = FMath::DegreesToRadians(FMath::Clamp<double>(Client->ViewFOV, 10.0, 170.0)) * 0.5;
		const double HalfVerticalFov = FMath::Atan(FMath::Tan(HalfHorizontalFov) / Aspect);
		const double SafePadding = FMath::Max(1.0, Padding);

		FRotator Rotation;
		double Distance = 0.0;
		if (View == EBLDCaptureView::TopDown)
		{
			// Looking straight down with yaw 0, screen-right is world +Y and screen-up is world +X.
			Rotation = FRotator(-89.9, 0.0, 0.0);
			Distance = FMath::Max(Extent.Y / FMath::Tan(HalfHorizontalFov), Extent.X / FMath::Tan(HalfVerticalFov)) * SafePadding + Extent.Z;
		}
		else
		{
			Rotation = FRotator(-50.0, 45.0, 0.0);
			const double Radius = FMath::Max(Extent.Size(), 500.0);
			Distance = Radius / FMath::Sin(FMath::Min(HalfHorizontalFov, HalfVerticalFov)) * SafePadding;
		}

		Client->SetViewLocation(Center - Rotation.Vector() * FMath::Max(Distance, 1000.0));
		Client->SetViewRotation(Rotation);
		Client->Invalidate();
	}

	TArray<FColor> ResizeToFit(const TArray<FColor>& Source, const FIntPoint SourceSize, const int32 MaxWidth, const int32 MaxHeight, FIntPoint& OutSize)
	{
		const double Scale = FMath::Min3(
			static_cast<double>(FMath::Max(MaxWidth, 16)) / SourceSize.X,
			static_cast<double>(FMath::Max(MaxHeight, 16)) / SourceSize.Y,
			1.0);
		OutSize = FIntPoint(
			FMath::Max(1, FMath::RoundToInt32(SourceSize.X * Scale)),
			FMath::Max(1, FMath::RoundToInt32(SourceSize.Y * Scale)));
		if (OutSize == SourceSize)
		{
			return Source;
		}

		TArray64<FLinearColor> SourceLinear;
		SourceLinear.SetNum(Source.Num());
		for (int32 Index = 0; Index < Source.Num(); ++Index)
		{
			SourceLinear[Index] = FLinearColor::FromSRGBColor(Source[Index]);
		}

		TArray64<FLinearColor> TargetLinear;
		TargetLinear.SetNum(static_cast<int64>(OutSize.X) * OutSize.Y);
		FImageUtils::ImageResize(SourceSize.X, SourceSize.Y, SourceLinear, OutSize.X, OutSize.Y, TargetLinear);

		TArray<FColor> Target;
		Target.SetNum(OutSize.X * OutSize.Y);
		for (int32 Index = 0; Index < Target.Num(); ++Index)
		{
			Target[Index] = TargetLinear[Index].ToFColorSRGB();
		}
		return Target;
	}

	void SetError(const FPendingCapture& Pending, const FString& Message)
	{
		Pending.Result->SetError(FString::Printf(TEXT("%s: %s"), *Pending.Request.ToolsetName, *Message));
	}
}

namespace BLDCapture
{
	bool EncodeImage(const TArray<FColor>& Pixels, const FIntPoint Size, const int32 MaxWidth, const int32 MaxHeight, FToolsetImage& OutImage)
	{
		if (Size.X <= 0 || Size.Y <= 0 || Pixels.Num() != Size.X * Size.Y)
		{
			return false;
		}

		TArray<FColor> Opaque = Pixels;
		for (FColor& Pixel : Opaque)
		{
			Pixel.A = 255;
		}

		FIntPoint ImageSize;
		const TArray<FColor> Scaled = BLDCapturePrivate::ResizeToFit(Opaque, Size, MaxWidth, MaxHeight, ImageSize);
		return OutImage.SetFromBitmap(Scaled, ImageSize);
	}

	void Capture(UBLDCaptureAsyncResult* Result, FRequest Request)
	{
		using namespace BLDCapturePrivate;

		if (!Result)
		{
			return;
		}

		const TSharedRef<FPendingCapture> Pending = MakeShared<FPendingCapture>();
		Pending->Result.Reset(Result);
		Pending->Request = MoveTemp(Request);
		Pending->Request.Width = FMath::Clamp(Pending->Request.Width, 16, 4096);
		Pending->Request.Height = FMath::Clamp(Pending->Request.Height, 16, 4096);

		FLevelEditorViewportClient* Client = FindPerspectiveViewport();
		if (!Client)
		{
			SetError(*Pending, TEXT("No perspective level viewport is available. Captures require the editor UI."));
			return;
		}

		const EBLDCaptureView View = Pending->Request.View;
		if ((View == EBLDCaptureView::Oblique || View == EBLDCaptureView::TopDown) && !Pending->Request.Bounds.IsValid)
		{
			SetError(*Pending, TEXT("Nothing to frame. Pass an area or a target with bounds."));
			return;
		}

		const FVector SavedLocation = Client->GetViewLocation();
		const FRotator SavedRotation = Client->GetViewRotation();
		const bool bSavedSelection = Client->EngineShowFlags.Selection != 0;
		const bool bSavedSelectionOutline = Client->EngineShowFlags.SelectionOutline != 0;
		const bool bSavedModeWidgets = Client->EngineShowFlags.ModeWidgets != 0;

		if (View == EBLDCaptureView::Pose)
		{
			Client->SetViewLocation(Pending->Request.PoseLocation);
			Client->SetViewRotation(Pending->Request.PoseRotation);
		}
		else if (View != EBLDCaptureView::Current)
		{
			FrameBounds(Client, Pending->Request.Bounds, View, Pending->Request.Padding);
		}

		Client->EngineShowFlags.SetSelection(false);
		Client->EngineShowFlags.SetSelectionOutline(false);
		Client->EngineShowFlags.SetModeWidgets(false);
		Client->Invalidate();

		const TSharedRef<int32> FramesRemaining = MakeShared<int32>(SettleFrames);
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda(
			[Pending, Client, FramesRemaining, SavedLocation, SavedRotation, bSavedSelection, bSavedSelectionOutline, bSavedModeWidgets](float)
			{
				if (!IsViewportClientAlive(Client))
				{
					SetError(*Pending, TEXT("The level viewport closed during capture."));
					return false;
				}

				if (--(*FramesRemaining) > 0)
				{
					Client->Invalidate();
					return true;
				}

				Client->Viewport->Draw();
				FlushRenderingCommands();

				TArray<FColor> Bitmap;
				const FIntPoint SourceSize = Client->Viewport->GetSizeXY();
				const bool bCaptured = GetViewportScreenShot(Client->Viewport, Bitmap)
					&& Bitmap.Num() == SourceSize.X * SourceSize.Y;

				FBLDCaptureResult Capture;
				Capture.CameraLocation = Client->GetViewLocation();
				Capture.CameraRotation = Client->GetViewRotation();
				if (Pending->Request.Bounds.IsValid)
				{
					Capture.BoundsMin = Pending->Request.Bounds.Min;
					Capture.BoundsMax = Pending->Request.Bounds.Max;
				}
				Capture.Warnings = Pending->Request.Warnings;

				Client->EngineShowFlags.SetSelection(bSavedSelection);
				Client->EngineShowFlags.SetSelectionOutline(bSavedSelectionOutline);
				Client->EngineShowFlags.SetModeWidgets(bSavedModeWidgets);
				if (Pending->Request.bRestoreCamera)
				{
					Client->SetViewLocation(SavedLocation);
					Client->SetViewRotation(SavedRotation);
				}
				Client->Invalidate();

				if (!bCaptured)
				{
					SetError(*Pending, TEXT("Failed to read the viewport framebuffer."));
					return false;
				}

				if (!EncodeImage(Bitmap, SourceSize, Pending->Request.Width, Pending->Request.Height, Capture.Image))
				{
					SetError(*Pending, TEXT("Failed to encode the capture."));
					return false;
				}

				Pending->Result->SetValue(Capture);
				return false;
			}));
	}
}
