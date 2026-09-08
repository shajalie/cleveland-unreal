#include "WalkthroughProbe.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/Controller.h"
#include "HAL/FileManager.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

UWalkthroughProbe::UWalkthroughProbe()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UWalkthroughProbe::BeginPlay()
{
    Super::BeginPlay();
    SetComponentTickEnabled(FParse::Param(FCommandLine::Get(), TEXT("ClevelandVerify")));
    Started = FPlatformTime::Seconds();
}

void UWalkthroughProbe::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction)
{
    Super::TickComponent(DeltaTime, TickType, TickFunction);
    ACharacter* Character = Cast<ACharacter>(GetOwner());
    if (!Character) return;
    const double Now = FPlatformTime::Seconds();
    const double Elapsed = Now - Started;
    // Wall time alone can expire during startup shader/PSO stalls before any
    // usable frames exist. Require game ticks as well as elapsed time.
    ++WarmupFrames;
    if (Elapsed < 30.0 || WarmupFrames < 300) return;
    if (!bSampleStarted)
    {
        bSampleStarted = true;
        SampleStarted = Now;
        WalkStart = Character->GetActorLocation();
        if (Character->GetController())
            Character->GetController()->SetControlRotation(FRotator(0.f, -90.f, 0.f));
    }
    ++SampleFrames;
    const double SampleElapsed = Now - SampleStarted;
    if (SampleElapsed < 2.0) Character->AddMovementInput(Character->GetActorForwardVector(), 1.f);
    if (SampleElapsed < 10.0) return;
    const FVector End = Character->GetActorLocation();
    const float Distance = FVector::Dist2D(WalkStart, End);
    const bool Grounded = Character->GetCharacterMovement()->IsMovingOnGround();
    const FString Folder = FPaths::ProjectSavedDir() / TEXT("ClevelandReview");
    IFileManager::Get().MakeDirectory(*Folder, true);
    const FString Screenshot = Folder / (TEXT("walkthrough-") + FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%S")) + TEXT(".png"));
    FScreenshotRequest::RequestScreenshot(Screenshot, false, false);
    const FRotator View = Character->GetViewRotation();
    const FString Report = FString::Printf(TEXT("{\n  \"sampleFrames\": %d,\n  \"averageFps\": %.2f,\n  \"walkDistanceCm\": %.2f,\n  \"grounded\": %s,\n  \"actorZCm\": %.2f,\n  \"viewPitch\": %.2f,\n  \"viewYaw\": %.2f,\n  \"scope\": \"One local forward-walk sample after 300 warmup ticks; does not verify browser input or all circulation paths\"\n}\n"),
        SampleFrames, SampleFrames / FMath::Max(Now - SampleStarted, 0.001), Distance, Grounded ? TEXT("true") : TEXT("false"), End.Z, View.Pitch, View.Yaw);
    FFileHelper::SaveStringToFile(Report, *(Folder / TEXT("runtime-probe.json")));
    UE_LOG(LogTemp, Display, TEXT("Cleveland runtime probe: %s"), *Report);
    SetComponentTickEnabled(false);
}
