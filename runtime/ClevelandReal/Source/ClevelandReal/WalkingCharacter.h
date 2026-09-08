#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "WalkingCharacter.generated.h"

class UCameraComponent;

/** Human-scale navigation. No flying, sprinting, weapons or automatic head shake. */
UCLASS()
class CLEVELANDREAL_API AWalkingCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    AWalkingCharacter();
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* Input) override;
    virtual void FellOutOfWorld(const UDamageType& DamageType) override;

    /** Restores a verified grounded position without destroying the streamed pawn. */
    bool RecoverToSafeGround();
    int32 GetRecoveryCount() const { return RecoveryCount; }

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="View")
    TObjectPtr<UCameraComponent> Camera;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Comfort")
    bool bCameraSway = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Comfort")
    float MouseSensitivity = 0.65f;

protected:
    virtual void BeginPlay() override;

private:
    void MoveForward(float Value);
    void MoveRight(float Value);
    void TurnMouse(float Value);
    void LookMouse(float Value);
    void TurnStick(float Value);
    void LookStick(float Value);
    void Interact();
    void ToggleSway();
    float SmoothedEyeZ = 0.f;
    float WalkPhase = 0.f;
    FVector LastSafeLocation = FVector::ZeroVector;
    FRotator LastSafeView = FRotator::ZeroRotator;
    float GroundedSeconds = 0.f;
    bool bHasSafeLocation = false;
    int32 RecoveryCount = 0;
};
