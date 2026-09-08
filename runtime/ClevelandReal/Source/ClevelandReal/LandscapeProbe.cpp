#include "LandscapeProbe.h"
#include "WalkingCharacter.h"
#include "SceneControls.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "HAL/FileManager.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
    FVector ModelPosition(const TArray<TSharedPtr<FJsonValue>>& P)
    { return FVector(P[0]->AsNumber()*100,-P[1]->AsNumber()*100,P[2]->AsNumber()*100); }
}

ULandscapeProbe::ULandscapeProbe() { PrimaryComponentTick.bCanEverTick = true; }

void ULandscapeProbe::BeginPlay()
{
    Super::BeginPlay();
    SetComponentTickEnabled(FParse::Param(FCommandLine::Get(),TEXT("ClevelandLandscapeVerify")));
    Started = FPlatformTime::Seconds();
}

void ULandscapeProbe::TickComponent(float DeltaTime,ELevelTick TickType,FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(DeltaTime,TickType,TickFunction);
    auto* Walker=Cast<AWalkingCharacter>(GetOwner());
    if (!Walker) return;
    const double Now=FPlatformTime::Seconds();
    if (Now-Started<5 || ++Frames<90) return;
    FCollisionQueryParams Query(SCENE_QUERY_STAT(LandscapeRegression),true,Walker);
    if (!Report)
    {
        FString Path,Json;
        if (!FParse::Value(FCommandLine::Get(),TEXT("ClevelandLandscapeProbe="),Path) ||
            !FFileHelper::LoadFileToString(Json,*Path) ||
            !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json),Report))
        { UE_LOG(LogTemp,Error,TEXT("Landscape probe requires its generated JSON input"));SetComponentTickEnabled(false);return; }
        Routes=Report->GetArrayField(TEXT("routes"));
        TArray<TSharedPtr<FJsonValue>> Missing;
        const auto& Samples=Report->GetArrayField(TEXT("floorSamples"));
        for (const auto& Sample:Samples)
        {
            const FVector P=ModelPosition(Sample->AsArray());
            FHitResult Hit;
            if (!GetWorld()->LineTraceSingleByChannel(Hit,P+FVector(0,0,45),P-FVector(0,0,70),ECC_Visibility,Query) ||
                Hit.ImpactNormal.Z<.69 || FMath::Abs(Hit.ImpactPoint.Z-P.Z)>35)
                Missing.Add(Sample);
        }
        Report->SetNumberField(TEXT("floorSampleCount"),Samples.Num());
        Report->SetArrayField(TEXT("missingFloorSamples"),Missing);
        Report->RemoveField(TEXT("floorSamples"));
        RecoveryBefore=Walker->GetRecoveryCount();
    }
    if (bFallTest)
    {
        if (Now-RouteStarted<2) return;
        Report->SetBoolField(TEXT("fallRecoveryPassed"),Walker->GetRecoveryCount()==RecoveryBefore+1 &&
            Walker->GetCharacterMovement()->IsMovingOnGround() && Walker->GetActorLocation().Z>-600);
        Finish();return;
    }
    if (RouteStarted==0)
    {
        ++RouteIndex;
        if (RouteIndex>=Routes.Num())
        {
            Report->SetBoolField(TEXT("noAccidentalRecovery"),Walker->GetRecoveryCount()==RecoveryBefore);
            RecoveryBefore=Walker->GetRecoveryCount();
            Walker->SetActorLocation(FVector(0,0,-750),false,nullptr,ETeleportType::TeleportPhysics);
            Walker->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
            bFallTest=true;RouteStarted=Now;return;
        }
        const auto Route=Routes[RouteIndex]->AsObject();
        Start=ModelPosition(Route->GetArrayField(TEXT("start")))+FVector(0,0,91);
        End=ModelPosition(Route->GetArrayField(TEXT("end")))+FVector(0,0,91);
        const bool Placed=Walker->TeleportTo(Start,(End-Start).Rotation(),false,false);
        Walker->GetCharacterMovement()->StopMovementImmediately();
        Walker->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
        if (Walker->GetController())Walker->GetController()->SetControlRotation((End-Start).Rotation());
        auto Result=MakeShared<FJsonObject>();
        Result->SetStringField(TEXT("id"),Route->GetStringField(TEXT("id")));
        Result->SetBoolField(TEXT("placed"),Placed);
        Results.Add(MakeShared<FJsonValueObject>(Result));
        RouteStarted=Now;return;
    }
    const double Distance=FVector::Dist2D(Start,End);
    const double Elapsed=Now-RouteStarted;
    if (Elapsed<.75) return;
    const double Remaining=FVector::Dist2D(Walker->GetActorLocation(),End);
    if (Remaining>12 && Elapsed<Distance/140.+3.)
    { Walker->AddMovementInput((End-Start).GetSafeNormal2D(),1);return; }
    Walker->GetCharacterMovement()->StopMovementImmediately();
    auto Result=Results.Last()->AsObject();
    Result->SetNumberField(TEXT("remainingCm"),Remaining);
    Result->SetBoolField(TEXT("grounded"),Walker->GetCharacterMovement()->IsMovingOnGround());
    Result->SetBoolField(TEXT("passed"),Remaining<25 && Walker->GetCharacterMovement()->IsMovingOnGround());
    RouteStarted=0;
}

void ULandscapeProbe::Finish()
{
    Report->SetArrayField(TEXT("walkResults"),Results);
    bool Passed=Report->GetArrayField(TEXT("missingFloorSamples")).IsEmpty() &&
        Report->GetBoolField(TEXT("fallRecoveryPassed")) && Report->GetBoolField(TEXT("noAccidentalRecovery"));
    for (const auto& Result:Results) Passed &= Result->AsObject()->GetBoolField(TEXT("passed"));
    if (auto* Controls = GetOwner()->FindComponentByClass<USceneControls>())
    {
        auto Effects = Controls->VerifyEffects();
        Report->SetObjectField(TEXT("visualSettings"), Effects);
        Passed &= Effects->GetBoolField(TEXT("passed"));
    }
    else Passed = false;
    Report->SetBoolField(TEXT("passed"),Passed);
    Report->SetStringField(TEXT("scope"),TEXT("Packaged game physics: outdoor floor grid, six capsule walks, forced fall recovery. Not an exhaustive indoor collision audit."));
    FString Json;FJsonSerializer::Serialize(Report.ToSharedRef(),TJsonWriterFactory<>::Create(&Json));
    const FString Folder=FPaths::ProjectSavedDir()/TEXT("ClevelandReview");
    IFileManager::Get().MakeDirectory(*Folder,true);
    FFileHelper::SaveStringToFile(Json,*(Folder/TEXT("landscape-probe.json")));
    UE_LOG(LogTemp,Display,TEXT("CLEVELAND_LANDSCAPE_PROBE %s"),*Json);
    SetComponentTickEnabled(false);
}
