#include "SceneControls.h"
#include "DaylightExposure.h"
#include "WalkingCharacter.h"
#include "LandscapeCluster.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "SunPosition.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"

namespace
{
    // Anchors in the model's metres (+Y rear). USD imports with Y reversed.
    struct FRoomAnchor { const TCHAR* Id; FVector Position; float Yaw; };
    const FRoomAnchor Rooms[] = {
        {TEXT("living"), {3.0, 2.0, 0.0}, -90},
        {TEXT("foyer"), {0.0, 1.7, 0.0}, -90},
        {TEXT("dining"), {-2.1, 1.1, 0.0}, -135},
        {TEXT("kitchen"), {-2.15, 5.1, 0.0}, -155},
        {TEXT("breakfast"), {-4.65, 8.0, 0.0}, -75},
        {TEXT("study"), {3.0, 8.15, 0.0}, -90},
        {TEXT("powder"), {-0.7, 6.5, 0.0}, -90},
        {TEXT("primary"), {-2.2, 2.1, 3.12}, -130},
        {TEXT("sunroom"), {-3.4, 8.25, 3.12}, -120},
        {TEXT("yellow"), {1.5, 3.7, 3.12}, 25},
        {TEXT("blue"), {1.6, 8.2, 3.12}, -40},
        {TEXT("primary-bath"), {-0.35, 1.6, 3.12}, 90},
        {TEXT("hall-bath"), {2.85, 6.17, 3.12}, 0},
        {TEXT("lower"), {-2.4, 5.7, -2.72}, 150},
        {TEXT("porch"), {0.0, -1.5, -0.12}, -90},
        {TEXT("garden"), {4.5, 13.0, -0.55}, -145},
        {TEXT("pool"), {-0.8, 17.0, -1.62}, -160},
        {TEXT("front-lawn"), {2.0, -10.0, -.6}, -107},
        {TEXT("driveway"), {6.2, -8.0, -.58}, -100},
        {TEXT("rear-lawn"), {7.5, 16.0, -.638}, -160}
    };
}

USceneControls::USceneControls() { PrimaryComponentTick.bCanEverTick = false; }

TSharedRef<FJsonObject> USceneControls::VerifyEffects() { return Effects.Verify(GetWorld()); }

void USceneControls::BeginPlay()
{
    Super::BeginPlay();
    // Pixel Streaming's input class is reflected but not DLL-exported in 5.8.
    // Bind its public Blueprint delegate without depending on private headers.
    UClass* InputClass = LoadClass<UActorComponent>(nullptr, TEXT("/Script/PixelStreaming2.PixelStreaming2Input"));
    if (InputClass)
    {
        StreamInput = NewObject<UActorComponent>(GetOwner(), InputClass, TEXT("BrowserSceneInput"));
        GetOwner()->AddInstanceComponent(StreamInput);
        if (const auto* Event = FindFProperty<FMulticastDelegateProperty>(InputClass, TEXT("OnInputEvent")))
        {
            FScriptDelegate Delegate;
            Delegate.BindUFunction(this, TEXT("HandleCommand"));
            Event->AddDelegate(Delegate, StreamInput);
        }
        StreamInput->RegisterComponent();
    }
    for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It) { Sun = *It; break; }
    if (Sun) Sun->GetLightComponent()->SetMobility(EComponentMobility::Movable);
    if (auto* Walker = Cast<AWalkingCharacter>(GetOwner()))
    {
        DaylightExposure::Configure(*Walker->Camera, Exposure);
    }
    SetSun(Time);
    Effects.Initialize(GetWorld());
    // Reapply after startup scalability commands have settled.
    FTimerHandle StartupEffects;
    GetWorld()->GetTimerManager().SetTimer(StartupEffects, FTimerDelegate::CreateWeakLambda(this, [this]() {
        Effects.Apply(GetWorld()); Respond();
    }), 2.f, false);
    Respond();
}

void USceneControls::HandleCommand(const FString& Descriptor)
{
    if (Descriptor.Len() > 1024) return;
    TSharedPtr<FJsonObject> Input;
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Descriptor), Input) || !Input) return;
    FString Protocol, Action;
    if (!Input->TryGetStringField(TEXT("protocol"), Protocol) || Protocol != TEXT("cleveland.scene.v1") ||
        !Input->TryGetStringField(TEXT("action"), Action)) return;
    const double Now = FPlatformTime::Seconds();
    // Status polling must not discard a slider change arriving in the same
    // frame. Apply every bounded scene edit in order; throttle only polls.
    if (Action == TEXT("status"))
    {
        if (Now - LastStatus < 0.25) return;
        LastStatus = Now;
    }
    FString Error;
    if (Action == TEXT("room"))
    {
        FString Id;
        if (!Input->TryGetStringField(TEXT("room"), Id) || !GoToRoom(Id))
            Error = TEXT("This viewpoint has no clear standing spot. Try another room.");
    }
    else if (Action == TEXT("recover"))
    {
        auto* Walker = Cast<AWalkingCharacter>(GetOwner());
        if (!Walker || !Walker->RecoverToSafeGround()) Error = TEXT("Choose a room to return to a clear standing spot.");
    }
    else if (Action == TEXT("effects"))
    {
        const TSharedPtr<FJsonObject>* Options = nullptr;
        if (!Input->TryGetObjectField(TEXT("effects"), Options) || !Effects.Update(GetWorld(), *Options))
            Error = TEXT("Choose one of the available visual switches.");
    }
    else if (Action == TEXT("time"))
    {
        double Value;
        // Fixed study range; client cannot execute console commands or supply transforms.
        if (Input->TryGetNumberField(TEXT("utc"), Value) && FMath::IsFinite(Value) &&
            Value >= 1577836800.0 && Value <= 1924991999.0 && FMath::FloorToDouble(Value) == Value)
            SetSun(static_cast<int64>(Value));
        else Error = TEXT("Choose a date from 2020 through 2030.");
    }
    else if (Action == TEXT("exposure"))
    {
        double Value;
        if (Input->TryGetNumberField(TEXT("value"), Value) && FMath::IsFinite(Value) && Value >= -3 && Value <= 3)
        {
            Exposure = Value;
            if (auto* Walker = Cast<AWalkingCharacter>(GetOwner()))
                Walker->Camera->PostProcessSettings.AutoExposureBias = Exposure;
        }
        else Error = TEXT("Exposure must be between -3 and +3 stops.");
    }
    else if (Action != TEXT("status")) return;
    Respond(Error);
}

bool USceneControls::GoToRoom(const FString& Id)
{
    auto* Walker = Cast<AWalkingCharacter>(GetOwner());
    if (!Walker || !Walker->GetController()) return false;
    for (const auto& Anchor : Rooms)
    {
        if (Id != Anchor.Id) continue;
        FVector Position = Anchor.Position;
        float Yaw = Anchor.Yaw;
        // Local configuration allows viewpoint corrections without re-cooking
        // the house. Browser commands still only accept known room IDs.
        FString ViewPath, ViewJson;
        TSharedPtr<FJsonObject> Views;
        if (FParse::Value(FCommandLine::Get(), TEXT("ClevelandViews="), ViewPath) &&
            FFileHelper::LoadFileToString(ViewJson, *ViewPath) && ViewJson.Len() < 16000 &&
            FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(ViewJson), Views))
        {
            const TArray<TSharedPtr<FJsonValue>>* Values;
            if (Views->TryGetArrayField(Id, Values) && Values->Num() == 4)
            {
                double V[4]; bool Valid = true;
                for (int I = 0; I < 4; ++I)
                    Valid &= (*Values)[I]->TryGetNumber(V[I]) && FMath::IsFinite(V[I]) && FMath::Abs(V[I]) <= (I == 3 ? 180 : 100);
                if (Valid) { Position = FVector(V[0], V[1], V[2]); Yaw = V[3]; }
            }
        }
        const FVector Centre(Position.X * 100, -Position.Y * 100, Position.Z * 100);
        FCollisionQueryParams Query(SCENE_QUERY_STAT(RoomJump), true, Walker);
        // Reject furniture tops and obstructed capsules. Search only within 45 cm
        // of the authored anchor, and never silently jump through a room wall.
        const FVector Offsets[] = {{0,0,0},{35,0,0},{-35,0,0},{0,35,0},{0,-35,0}};
        for (const FVector& Offset : Offsets)
        {
            const FVector Floor = Centre + Offset;
            FHitResult Hit;
            if (!GetWorld()->LineTraceSingleByChannel(Hit, Floor + FVector(0,0,55), Floor - FVector(0,0,65), ECC_Visibility, Query) ||
                FMath::Abs(Hit.ImpactPoint.Z - Floor.Z) > 50 || Hit.ImpactNormal.Z < 0.7) continue;
            const FVector Destination(Hit.ImpactPoint.X, Hit.ImpactPoint.Y, Hit.ImpactPoint.Z + 91);
            if (GetWorld()->OverlapBlockingTestByChannel(Destination, FQuat::Identity, ECC_Pawn,
                FCollisionShape::MakeCapsule(23,88), Query)) continue;
            const FRotator View(0, Yaw, 0);
            if (!Walker->TeleportTo(Destination, View, false, false)) continue;
            Walker->GetCharacterMovement()->StopMovementImmediately();
            Walker->GetController()->SetControlRotation(View);
            Room = Id;
            DaylightExposure::ResetAfterJump(Walker);
            return true;
        }
        return false;
    }
    return false;
}

void USceneControls::SetSun(int64 UtcSeconds)
{
    Time = UtcSeconds;
    const FDateTime Date = FDateTime::FromUnixTimestamp(Time);
    FSunPositionData Position;
    // UTC avoids browser timezone and daylight-saving ambiguity. Epic's result
    // includes a 180-degree elevation offset for its Blueprint convention.
    USunPositionFunctionLibrary::GetSunPosition(38.92485352f, -77.06033745f, 0, false,
        Date.GetYear(), Date.GetMonth(), Date.GetDay(), Date.GetHour(), Date.GetMinute(), 0, Position);
    Elevation = Position.Elevation - 180;
    Azimuth = Position.Azimuth;
    const double Alt = FMath::DegreesToRadians(Elevation);
    const double Az = FMath::DegreesToRadians(Azimuth);
    const double East = FMath::Cos(Alt) * FMath::Sin(Az);
    const double North = FMath::Cos(Alt) * FMath::Cos(Az);
    // Survey-plan basis, shared with design/spatial-model.json and the old study.
    const FVector ToSun(East * -0.7073902823 + North * 0.7068231663,
        -(East * -0.7068231663 + North * -0.7073902823), FMath::Sin(Alt));
    if (Sun)
    {
        Sun->SetActorRotation((-ToSun).Rotation());
        auto* Light = Cast<UDirectionalLightComponent>(Sun->GetLightComponent());
        // Clear-sky preview. This intensity is an estimate, not measured illuminance.
        const float AirMass = 1.f / FMath::Max(0.08f, FMath::Sin(static_cast<float>(Alt)));
        Light->SetIntensity(Elevation > 0 ? 110000.f * FMath::Exp(-0.14f * AirMass) : 0.f);
    }
    DaylightExposure::ResetAfterJump(GetOwner());
}

void USceneControls::Respond(const FString& Error)
{
    auto State = MakeShared<FJsonObject>();
    State->SetStringField(TEXT("protocol"), TEXT("cleveland.scene.v1"));
    State->SetStringField(TEXT("room"), Room);
    State->SetNumberField(TEXT("utc"), Time);
    State->SetNumberField(TEXT("elevation"), Elevation);
    State->SetNumberField(TEXT("azimuth"), Azimuth);
    State->SetNumberField(TEXT("exposure"), Exposure);
    State->SetNumberField(TEXT("lightingVersion"), DaylightExposure::Version);
    State->SetNumberField(TEXT("landscapeVersion"), TActorIterator<ALandscapeCluster>(GetWorld()) ? 3 : 0);
    State->SetObjectField(TEXT("effects"), Effects.Snapshot());
    if (const auto* Walker = Cast<AWalkingCharacter>(GetOwner()))
        State->SetNumberField(TEXT("recoveryCount"), Walker->GetRecoveryCount());
    const auto* Extended = IConsoleManager::Get().FindConsoleVariable(TEXT("r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange"));
    State->SetBoolField(TEXT("extendedExposureRange"), Extended && Extended->GetInt() == 1);
    State->SetNumberField(TEXT("minEV100"), DaylightExposure::MinEV100);
    State->SetNumberField(TEXT("maxEV100"), DaylightExposure::MaxEV100);
    if (Sun) State->SetNumberField(TEXT("sunIlluminanceLux"), Sun->GetLightComponent()->Intensity);
    State->SetStringField(TEXT("error"), Error);
    const FVector Location = GetOwner()->GetActorLocation();
    State->SetNumberField(TEXT("x"), Location.X);
    State->SetNumberField(TEXT("y"), Location.Y);
    State->SetNumberField(TEXT("z"), Location.Z);
    State->SetNumberField(TEXT("yaw"), GetOwner()->GetActorRotation().Yaw);
    FString Json;
    FJsonSerializer::Serialize(State, TJsonWriterFactory<>::Create(&Json));
    const FString Folder = FPaths::ProjectSavedDir() / TEXT("ClevelandReview");
    IFileManager::Get().MakeDirectory(*Folder, true);
    FFileHelper::SaveStringToFile(Json, *(Folder / TEXT("scene-state.json")));
    if (StreamInput)
    {
        if (UFunction* Send = StreamInput->FindFunction(TEXT("SendPixelStreaming2Response")))
        {
            struct FResponse { FString Descriptor; } Parameters{Json};
            StreamInput->ProcessEvent(Send, &Parameters);
        }
    }
}
