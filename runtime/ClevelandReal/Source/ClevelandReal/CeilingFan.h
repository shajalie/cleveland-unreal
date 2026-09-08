#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "CeilingFan.generated.h"

/** Slow continuous rotation; can be stopped for an accumulated still. */
UCLASS()
class CLEVELANDREAL_API ACeilingFan : public AActor
{
    GENERATED_BODY()
public:
    ACeilingFan();
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Motion")
    bool bRunning = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Motion", meta=(ClampMin="0", ClampMax="120"))
    float RevolutionsPerMinute = 24.f;
};
