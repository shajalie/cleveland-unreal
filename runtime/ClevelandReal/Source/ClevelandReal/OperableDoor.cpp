#include "OperableDoor.h"
#include "Components/SceneComponent.h"

AOperableDoor::AOperableDoor()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Hinge"));
    RootComponent->SetMobility(EComponentMobility::Movable);
}

void AOperableDoor::BeginPlay()
{
    Super::BeginPlay();
    ClosedRotation = RootComponent->GetRelativeRotation();
}

void AOperableDoor::Toggle() { bOpen = !bOpen; }

void AOperableDoor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    CurrentAngle = FMath::FInterpConstantTo(CurrentAngle, bOpen ? OpenAngle : 0.f, DeltaSeconds, DegreesPerSecond);
    RootComponent->SetRelativeRotation(ClosedRotation + FRotator(0.f, CurrentAngle, 0.f));
}
