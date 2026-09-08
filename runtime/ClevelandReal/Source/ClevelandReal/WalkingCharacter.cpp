#include "WalkingCharacter.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "OperableDoor.h"
#include "WalkthroughProbe.h"
#include "SceneControls.h"
#include "DaylightExposure.h"
#include "LandscapeProbe.h"

AWalkingCharacter::AWalkingCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
    CreateDefaultSubobject<UWalkthroughProbe>(TEXT("OptInRuntimeProbe"));
    CreateDefaultSubobject<ULandscapeProbe>(TEXT("OptInLandscapeProbe"));
    CreateDefaultSubobject<USceneControls>(TEXT("SceneControls"));
    GetCapsuleComponent()->InitCapsuleSize(23.f, 88.f);
    GetCharacterMovement()->MaxWalkSpeed = 140.f;
    GetCharacterMovement()->MaxStepHeight = 20.f;
    GetCharacterMovement()->MaxAcceleration = 500.f;
    GetCharacterMovement()->BrakingDecelerationWalking = 800.f;
    GetCharacterMovement()->SetWalkableFloorAngle(46.f);
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Eyes"));
    Camera->SetupAttachment(GetCapsuleComponent());
    Camera->SetRelativeLocation(FVector(0.f, 0.f, 77.f));
    Camera->FieldOfView = 80.f;
    Camera->bUsePawnControlRotation = true;
    bUseControllerRotationYaw = true;
}

void AWalkingCharacter::BeginPlay()
{
    Super::BeginPlay();
    SmoothedEyeZ = GetActorLocation().Z + 77.f;
}

void AWalkingCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    // The lowest intended walking floor is -272 cm. Recovery is a last resort;
    // continuous yard collision is authored separately, including the areaway.
    if (GetActorLocation().Z < -700.f) RecoverToSafeGround();
    if (GetCharacterMovement()->IsMovingOnGround() &&
        GetCharacterMovement()->CurrentFloor.IsWalkableFloor())
    {
        GroundedSeconds += DeltaSeconds;
        if (GroundedSeconds > 0.35f)
        {
            LastSafeLocation = GetActorLocation();
            LastSafeView = Controller ? Controller->GetControlRotation() : GetActorRotation();
            bHasSafeLocation = true;
        }
    }
    else GroundedSeconds = 0.f;
    const float TargetZ = GetActorLocation().Z + 77.f;
    if (!GetCharacterMovement()->IsMovingOnGround() || FMath::Abs(TargetZ - SmoothedEyeZ) > 100.f)
        SmoothedEyeZ = TargetZ;
    else
        SmoothedEyeZ = FMath::FInterpTo(SmoothedEyeZ, TargetZ, DeltaSeconds, 14.f);

    const float Walking = GetCharacterMovement()->IsMovingOnGround()
        ? FMath::Clamp(GetVelocity().Size2D() / 140.f, 0.f, 1.f) : 0.f;
    WalkPhase += DeltaSeconds * Walking * 9.f;
    const float Sway = bCameraSway ? Walking : 0.f;
    Camera->SetRelativeLocation(FVector(0.f, 0.3f * FMath::Sin(WalkPhase * .5f) * Sway,
        SmoothedEyeZ - GetActorLocation().Z + .5f * FMath::Sin(WalkPhase) * Sway));
}

bool AWalkingCharacter::RecoverToSafeGround()
{
    // PlayerStart is the fallback only before the pawn has stood on real ground.
    const FVector Destination = bHasSafeLocation ? LastSafeLocation + FVector(0, 0, 3)
        : FVector(300, -200, 100);
    if (!TeleportTo(Destination, GetActorRotation(), false, false)) return false;
    GetCharacterMovement()->StopMovementImmediately();
    GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    if (Controller && bHasSafeLocation) Controller->SetControlRotation(LastSafeView);
    SmoothedEyeZ = GetActorLocation().Z + 77.f;
    GroundedSeconds = 0.f;
    ++RecoveryCount;
    DaylightExposure::ResetAfterJump(this);
    UE_LOG(LogTemp, Display, TEXT("Cleveland recovered to safe ground: %s"), *Destination.ToString());
    return true;
}

void AWalkingCharacter::FellOutOfWorld(const UDamageType& DamageType)
{
    RecoverToSafeGround();
}

void AWalkingCharacter::SetupPlayerInputComponent(UInputComponent* Input)
{
    Super::SetupPlayerInputComponent(Input);
    Input->BindAxis("MoveForward", this, &AWalkingCharacter::MoveForward);
    Input->BindAxis("MoveRight", this, &AWalkingCharacter::MoveRight);
    Input->BindAxis("TurnMouse", this, &AWalkingCharacter::TurnMouse);
    Input->BindAxis("LookMouse", this, &AWalkingCharacter::LookMouse);
    Input->BindAxis("TurnStick", this, &AWalkingCharacter::TurnStick);
    Input->BindAxis("LookStick", this, &AWalkingCharacter::LookStick);
    Input->BindAction("Interact", IE_Pressed, this, &AWalkingCharacter::Interact);
    Input->BindAction("ToggleSway", IE_Pressed, this, &AWalkingCharacter::ToggleSway);
}

void AWalkingCharacter::MoveForward(float Value)
{
    if (Controller) AddMovementInput(FRotationMatrix(FRotator(0, Controller->GetControlRotation().Yaw, 0)).GetUnitAxis(EAxis::X), Value);
}

void AWalkingCharacter::MoveRight(float Value)
{
    if (Controller) AddMovementInput(FRotationMatrix(FRotator(0, Controller->GetControlRotation().Yaw, 0)).GetUnitAxis(EAxis::Y), Value);
}

void AWalkingCharacter::TurnMouse(float Value) { AddControllerYawInput(Value * MouseSensitivity); }
void AWalkingCharacter::LookMouse(float Value) { AddControllerPitchInput(Value * MouseSensitivity); }
void AWalkingCharacter::TurnStick(float Value) { AddControllerYawInput(Value * 90.f * GetWorld()->GetDeltaSeconds()); }
void AWalkingCharacter::LookStick(float Value) { AddControllerPitchInput(Value * 70.f * GetWorld()->GetDeltaSeconds()); }
void AWalkingCharacter::ToggleSway() { bCameraSway = !bCameraSway; }

void AWalkingCharacter::Interact()
{
    FHitResult Hit;
    const FVector Start = Camera->GetComponentLocation();
    FCollisionQueryParams Query(SCENE_QUERY_STAT(DoorInteraction), true, this);
    if (GetWorld()->LineTraceSingleByChannel(Hit, Start, Start + Camera->GetForwardVector() * 220.f, ECC_Visibility, Query))
    {
        for (USceneComponent* Component = Hit.GetComponent(); Component; Component = Component->GetAttachParent())
        {
            if (AOperableDoor* Door = Cast<AOperableDoor>(Component->GetOwner()))
            {
                Door->Toggle();
                return;
            }
        }
        for (AActor* Actor = Hit.GetActor(); Actor; Actor = Actor->GetAttachParentActor())
        {
            if (AOperableDoor* Door = Cast<AOperableDoor>(Actor))
            {
                Door->Toggle();
                return;
            }
        }
    }
}
