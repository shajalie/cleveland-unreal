#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "OperableDoor.generated.h"

UCLASS()
class CLEVELANDREAL_API AOperableDoor : public AActor
{
    GENERATED_BODY()

public:
    AOperableDoor();
    virtual void Tick(float DeltaSeconds) override;
    UFUNCTION(BlueprintCallable, Category="Door") void Toggle();
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Door") float OpenAngle = 85.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Door") float DegreesPerSecond = 70.f;

protected:
    virtual void BeginPlay() override;

private:
    bool bOpen = false;
    FRotator ClosedRotation;
    float CurrentAngle = 0.f;
};
