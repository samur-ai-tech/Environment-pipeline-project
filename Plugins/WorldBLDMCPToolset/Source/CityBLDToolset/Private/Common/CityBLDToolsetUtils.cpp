// Copyright WorldBLD LLC. All rights reserved.

#include "Common/CityBLDToolsetUtils.h"

#include "Authorization/CityBLDAuthGate.h"
#include "Authorization/CityBLDLicenseSubsystem.h"
#include "BLDToolsetUtils.h"
#include "CityBlock.h"
#include "CityBLDPrefab.h"
#include "CityBLDTypes.h"
#include "CityBLDUtils.h"
#include "Components/SplineComponent.h"
#include "Editor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "CoreGlobals.h"
#include "ModularBuildingActor.h"

namespace CityBLDToolsetUtils
{
	namespace
	{
		double Cross2D(const FVector& A, const FVector& B)
		{
			return A.X * B.Y - A.Y * B.X;
		}

		/** True when segments AB and CD cross each other by more than Tolerance cm on both sides. */
		bool DoSegmentsCross2D(const FVector& A, const FVector& B, const FVector& C, const FVector& D, double Tolerance)
		{
			const FVector AB = B - A;
			const FVector CD = D - C;
			const double ToleranceAB = Tolerance * FVector2D(AB.X, AB.Y).Size();
			const double ToleranceCD = Tolerance * FVector2D(CD.X, CD.Y).Size();

			const double D1 = Cross2D(AB, C - A);
			const double D2 = Cross2D(AB, D - A);
			const double D3 = Cross2D(CD, A - C);
			const double D4 = Cross2D(CD, B - C);

			const bool bStraddlesAB = (D1 > ToleranceAB && D2 < -ToleranceAB) || (D1 < -ToleranceAB && D2 > ToleranceAB);
			const bool bStraddlesCD = (D3 > ToleranceCD && D4 < -ToleranceCD) || (D3 < -ToleranceCD && D4 > ToleranceCD);
			return bStraddlesAB && bStraddlesCD;
		}

		/** True when Point is inside Polygon and further than Tolerance from its boundary. */
		bool IsPointStrictlyInside2D(const FVector& Point, const TArray<FVector>& Polygon, double Tolerance)
		{
			return UCityBLDUtils::IsPointInPolygon2D(Point, Polygon)
				&& !UCityBLDUtils::IsPointOnPolygonBoundary2D(Point, Polygon, Tolerance);
		}
	}

	UWorld* GetEditorWorldOrRaise(const TCHAR* ToolsetName)
	{
		UWorld* World = BLDToolset::GetEditorWorld();
		if (!IsValid(World))
		{
			BLDToolset::RaiseError(ToolsetName, TEXT("No editor world is loaded."));
			return nullptr;
		}
		return World;
	}

	TArray<ACityBlock*> GetBlocks(UWorld* World, const TOptional<FCityBLDBounds>& Bounds)
	{
		TArray<ACityBlock*> Blocks;
		if (!IsValid(World))
		{
			return Blocks;
		}

		for (TActorIterator<ACityBlock> It(World); It; ++It)
		{
			ACityBlock* Block = *It;
			if (IsValid(Block) && OverlapsBounds(GetBlockBounds(Block), Bounds))
			{
				Blocks.Add(Block);
			}
		}
		return Blocks;
	}

	TArray<AModularBuildingActor*> GetBuildings(UWorld* World, const TOptional<FCityBLDBounds>& Bounds)
	{
		TArray<AModularBuildingActor*> Buildings;
		if (!IsValid(World))
		{
			return Buildings;
		}

		for (TActorIterator<AModularBuildingActor> It(World); It; ++It)
		{
			AModularBuildingActor* Building = *It;
			if (!IsValid(Building))
			{
				continue;
			}

			FBox Box = GetPointsBounds(GetBuildingFootprintWorld(Building));
			if (!Box.IsValid)
			{
				Box = FBox(Building->GetActorLocation(), Building->GetActorLocation());
			}

			if (OverlapsBounds(Box, Bounds))
			{
				Buildings.Add(Building);
			}
		}
		return Buildings;
	}

	TMap<const AActor*, FParcelOwner> BuildParcelOwnerMap(UWorld* World)
	{
		TMap<const AActor*, FParcelOwner> Owners;
		for (ACityBlock* Block : GetBlocks(World))
		{
			for (int32 ParcelIndex = 0; ParcelIndex < Block->Parcels.Num(); ++ParcelIndex)
			{
				const UCityParcel* Parcel = Block->Parcels[ParcelIndex];
				if (!IsValid(Parcel))
				{
					continue;
				}

				for (const FParcelActorEntry& Entry : Parcel->ChildActors)
				{
					if (const AActor* Child = Entry.TryGetActor(World))
					{
						Owners.Add(Child, { Block, ParcelIndex });
					}
				}
			}
		}
		return Owners;
	}

	bool ValidateBounds(const TOptional<FCityBLDBounds>& Bounds, FString& OutError)
	{
		if (!Bounds.IsSet())
		{
			return true;
		}

		const FCityBLDBounds& Value = Bounds.GetValue();
		if (Value.Max.X <= Value.Min.X || Value.Max.Y <= Value.Min.Y)
		{
			OutError = TEXT("Bounds.Max must be greater than Bounds.Min in X and Y.");
			return false;
		}
		return true;
	}

	bool OverlapsBounds(const FBox& Box, const TOptional<FCityBLDBounds>& Bounds)
	{
		if (!Bounds.IsSet())
		{
			return true;
		}

		if (!Box.IsValid)
		{
			return false;
		}

		const FCityBLDBounds& Value = Bounds.GetValue();
		return Box.Min.X <= Value.Max.X && Box.Max.X >= Value.Min.X
			&& Box.Min.Y <= Value.Max.Y && Box.Max.Y >= Value.Min.Y;
	}

	FCityBLDBounds MakeBounds(const FBox& Box)
	{
		FCityBLDBounds Bounds;
		if (Box.IsValid)
		{
			Bounds.Min = Box.Min;
			Bounds.Max = Box.Max;
		}
		return Bounds;
	}

	TArray<FVector> GetSplineWorldPoints(const USplineComponent* Spline)
	{
		TArray<FVector> Points;
		if (!IsValid(Spline))
		{
			return Points;
		}

		const int32 NumPoints = Spline->GetNumberOfSplinePoints();
		Points.Reserve(NumPoints);
		for (int32 Index = 0; Index < NumPoints; ++Index)
		{
			Points.Add(Spline->GetLocationAtSplinePoint(Index, ESplineCoordinateSpace::World));
		}
		return Points;
	}

	TArray<FVector> GetBlockOutline(const ACityBlock* Block)
	{
		return IsValid(Block) ? GetSplineWorldPoints(Block->OuterLoop) : TArray<FVector>();
	}

	FBox GetBlockBounds(const ACityBlock* Block)
	{
		if (!IsValid(Block))
		{
			return FBox(ForceInit);
		}

		FBox Box = GetPointsBounds(GetBlockOutline(Block));
		if (!Box.IsValid)
		{
			Box = FBox(Block->GetActorLocation(), Block->GetActorLocation());
		}
		return Box;
	}

	TArray<FVector> GetBuildingFootprintWorld(const AModularBuildingActor* Building)
	{
		TArray<FVector> Points;
		if (!IsValid(Building))
		{
			return Points;
		}

		const FTransform ActorTransform = Building->GetActorTransform();
		Points.Reserve(Building->ShapePoints.Num());
		for (const FVector& LocalPoint : Building->ShapePoints)
		{
			Points.Add(ActorTransform.TransformPosition(LocalPoint));
		}
		return Points;
	}

	FBox GetPointsBounds(const TArray<FVector>& Points)
	{
		FBox Box(ForceInit);
		for (const FVector& Point : Points)
		{
			Box += Point;
		}
		return Box;
	}

	double PolygonArea2D(const TArray<FVector>& Points)
	{
		if (Points.Num() < 3)
		{
			return 0.0;
		}

		double TwiceArea = 0.0;
		for (int32 Index = 0; Index < Points.Num(); ++Index)
		{
			TwiceArea += Cross2D(Points[Index], Points[(Index + 1) % Points.Num()]);
		}
		return FMath::Abs(TwiceArea) * 0.5;
	}

	FVector PolygonCentroid(const TArray<FVector>& Points)
	{
		if (Points.IsEmpty())
		{
			return FVector::ZeroVector;
		}

		FVector Average = FVector::ZeroVector;
		for (const FVector& Point : Points)
		{
			Average += Point;
		}
		Average /= Points.Num();

		double TwiceArea = 0.0;
		double CentroidX = 0.0;
		double CentroidY = 0.0;
		for (int32 Index = 0; Index < Points.Num(); ++Index)
		{
			const FVector& Current = Points[Index];
			const FVector& Next = Points[(Index + 1) % Points.Num()];
			const double Cross = Cross2D(Current, Next);
			TwiceArea += Cross;
			CentroidX += (Current.X + Next.X) * Cross;
			CentroidY += (Current.Y + Next.Y) * Cross;
		}

		if (FMath::Abs(TwiceArea) < UE_KINDA_SMALL_NUMBER)
		{
			return Average;
		}

		return FVector(CentroidX / (3.0 * TwiceArea), CentroidY / (3.0 * TwiceArea), Average.Z);
	}

	bool IsPolygonSelfIntersecting2D(const TArray<FVector>& Points)
	{
		const int32 NumPoints = Points.Num();
		if (NumPoints < 4)
		{
			return false;
		}

		for (int32 First = 0; First < NumPoints; ++First)
		{
			for (int32 Second = First + 1; Second < NumPoints; ++Second)
			{
				// Adjacent edges share a vertex, including the closing edge.
				if (Second == First + 1 || (First == 0 && Second == NumPoints - 1))
				{
					continue;
				}

				if (DoSegmentsCross2D(Points[First], Points[(First + 1) % NumPoints], Points[Second], Points[(Second + 1) % NumPoints], 0.1))
				{
					return true;
				}
			}
		}
		return false;
	}

	bool DoPolygonsOverlap2D(const TArray<FVector>& A, const TArray<FVector>& B, double Tolerance)
	{
		if (A.Num() < 3 || B.Num() < 3)
		{
			return false;
		}

		const FBox BoxA = GetPointsBounds(A);
		const FBox BoxB = GetPointsBounds(B);
		if (BoxA.Min.X >= BoxB.Max.X - Tolerance || BoxA.Max.X <= BoxB.Min.X + Tolerance
			|| BoxA.Min.Y >= BoxB.Max.Y - Tolerance || BoxA.Max.Y <= BoxB.Min.Y + Tolerance)
		{
			return false;
		}

		for (int32 IndexA = 0; IndexA < A.Num(); ++IndexA)
		{
			for (int32 IndexB = 0; IndexB < B.Num(); ++IndexB)
			{
				if (DoSegmentsCross2D(A[IndexA], A[(IndexA + 1) % A.Num()], B[IndexB], B[(IndexB + 1) % B.Num()], Tolerance))
				{
					return true;
				}
			}
		}

		for (const FVector& Point : A)
		{
			if (IsPointStrictlyInside2D(Point, B, Tolerance))
			{
				return true;
			}
		}

		for (const FVector& Point : B)
		{
			if (IsPointStrictlyInside2D(Point, A, Tolerance))
			{
				return true;
			}
		}

		// Identical or nested outlines whose vertices all lie on the other's boundary.
		const FVector CentroidA = PolygonCentroid(A);
		return IsPointStrictlyInside2D(CentroidA, A, Tolerance) && IsPointStrictlyInside2D(CentroidA, B, Tolerance);
	}

	FString GetClassPath(const UClass* Class)
	{
		return Class ? Class->GetPathName() : FString();
	}

	FString GetAssetPath(const UClass* Class)
	{
		if (!Class)
		{
			return FString();
		}

		if (Class->IsNative())
		{
			return Class->GetPathName();
		}

		FString AssetName = Class->GetName();
		AssetName.RemoveFromEnd(TEXT("_C"));
		return Class->GetPackage()->GetName() + TEXT(".") + AssetName;
	}

	FString GetClassDisplayName(const UClass* Class)
	{
		if (!Class)
		{
			return FString();
		}

		FString Name;
		if (Class->IsChildOf(UDistrict::StaticClass()))
		{
			Name = Class->GetDefaultObject<UDistrict>()->DistrictName;
		}
		else if (Class->IsChildOf(ULandUse::StaticClass()))
		{
			Name = Class->GetDefaultObject<ULandUse>()->LandUseName;
		}
		else if (Class->IsChildOf(UBuildingStyle::StaticClass()))
		{
			Name = Class->GetDefaultObject<UBuildingStyle>()->StyleName;
		}
		else if (Class->IsChildOf(UGroundFloorType::StaticClass()))
		{
			Name = Class->GetDefaultObject<UGroundFloorType>()->TypeName;
		}

		if (Name.TrimStartAndEnd().IsEmpty())
		{
			Name = Class->GetName();
			Name.RemoveFromEnd(TEXT("_C"));
		}
		return Name;
	}

	FCityBLDClassRef MakeClassRef(const UClass* Class)
	{
		FCityBLDClassRef Ref;
		if (Class)
		{
			Ref.ClassPath = GetClassPath(Class);
			Ref.DisplayName = GetClassDisplayName(Class);
		}
		return Ref;
	}

	UClass* GetPresetBaseClass(ECityBLDPresetKind Kind)
	{
		switch (Kind)
		{
		case ECityBLDPresetKind::District:
			return UDistrict::StaticClass();
		case ECityBLDPresetKind::LandUse:
			return ULandUse::StaticClass();
		case ECityBLDPresetKind::BuildingStyle:
			return UBuildingStyle::StaticClass();
		case ECityBLDPresetKind::RoofStyle:
			return URoofStyle::StaticClass();
		case ECityBLDPresetKind::SidewalkPreset:
			return USidewalkPreset::StaticClass();
		case ECityBLDPresetKind::GroundFloorType:
			return UGroundFloorType::StaticClass();
		case ECityBLDPresetKind::Prefab:
			return ACityBLDPrefab::StaticClass();
		default:
			return nullptr;
		}
	}

	TArray<UClass*> DiscoverPresetClasses(ECityBLDPresetKind Kind)
	{
		TArray<UClass*> Classes = BLDToolset::DiscoverClasses(GetPresetBaseClass(Kind));
		Classes.Sort([](const UClass& A, const UClass& B)
		{
			return A.GetPathName() < B.GetPathName();
		});
		return Classes;
	}

	FString GetLicenseStateName()
	{
		const CityBLDAuthGate::FCityBLDAccessEvaluation Access = CityBLDAuthGate::EvaluateAccess();
		if (Access.AllowsEdits())
		{
			return Access.Tier == CityBLDAuthGate::ECityBLDAccessTier::Trial ? TEXT("Trial") : TEXT("Licensed");
		}

		if (Access.State == CityBLDAuthGate::ECityBLDAccessState::Unknown)
		{
			return TEXT("Checking");
		}

		if (!GEditor)
		{
			return TEXT("Unavailable");
		}

		const UCityBLDLicenseSubsystem* LicenseSubsystem = GEditor->GetEditorSubsystem<UCityBLDLicenseSubsystem>();
		if (!IsValid(LicenseSubsystem))
		{
			return TEXT("Unavailable");
		}

		if (!LicenseSubsystem->HasSessionToken())
		{
			return TEXT("NotLoggedIn");
		}

		switch (LicenseSubsystem->GetLicenseState())
		{
		case ECityBLDLicenseState::Error:
			return TEXT("Error");
		case ECityBLDLicenseState::Checking:
		case ECityBLDLicenseState::Unknown:
			return TEXT("Checking");
		case ECityBLDLicenseState::Unlicensed:
		default:
			return TEXT("Unlicensed");
		}
	}

#if WITH_DEV_AUTOMATION_TESTS
	namespace
	{
		int32 TestAuthorizationDepth = 0;
	}

	FScopedTestAuthorization::FScopedTestAuthorization()
	{
		check(IsInGameThread());
		++TestAuthorizationDepth;
	}

	FScopedTestAuthorization::~FScopedTestAuthorization()
	{
		check(IsInGameThread());
		--TestAuthorizationDepth;
	}
#endif

	bool EnsureAuthorized(FString& OutError)
	{
		BLDToolset::MarkCurrentCallUnattended();

#if WITH_DEV_AUTOMATION_TESTS
		// Only the toolset's own specs may bypass the gate; a test run started by anyone else does not.
		if (GIsAutomationTesting && TestAuthorizationDepth > 0 && IsInGameThread())
		{
			OutError.Reset();
			return true;
		}
#endif

		FText AccessError;
		if (CityBLDAuthGate::AllowEdits(AccessError))
		{
			OutError.Reset();
			return true;
		}

		OutError = AccessError.ToString();
		return false;
	}

	bool EnsureAuthorizedOrRaise(const TCHAR* ToolsetName)
	{
		FString Error;
		if (EnsureAuthorized(Error))
		{
			return true;
		}

		BLDToolset::RaiseError(ToolsetName, Error);
		return false;
	}
}
