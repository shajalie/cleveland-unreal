#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "LandscapeProbe.generated.h"

/** Opt-in packaged-game regression check: real physics, walking and fall recovery. */
UCLASS()
class CLEVELANDREAL_API ULandscapeProbe : public UActorComponent
{
    GENERATED_BODY()
public:
    ULandscapeProbe();
protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;
private:
    void Finish();
    double Started = 0;
    double RouteStarted = 0;
    int32 RouteIndex = -1;
    int32 Frames = 0;
    int32 RecoveryBefore = 0;
    bool bFallTest = false;
    FVector Start;
    FVector End;
    TSharedPtr<class FJsonObject> Report;
    TArray<TSharedPtr<class FJsonValue>> Routes;
    TArray<TSharedPtr<class FJsonValue>> Results;
};
