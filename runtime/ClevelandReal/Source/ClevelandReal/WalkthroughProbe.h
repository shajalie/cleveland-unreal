#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "WalkthroughProbe.generated.h"

// Opt-in runtime verification. It is inactive during normal user walkthroughs.
UCLASS()
class CLEVELANDREAL_API UWalkthroughProbe : public UActorComponent
{
    GENERATED_BODY()
public:
    UWalkthroughProbe();
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* TickFunction) override;
private:
    double Started = 0;
    double SampleStarted = 0;
    int32 SampleFrames = 0;
    int32 WarmupFrames = 0;
    FVector WalkStart = FVector::ZeroVector;
    bool bSampleStarted = false;
};
