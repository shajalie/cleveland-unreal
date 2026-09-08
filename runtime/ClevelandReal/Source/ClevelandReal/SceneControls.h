#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "SceneEffects.h"
#include "SceneControls.generated.h"

class ADirectionalLight;

/** Small, validated command surface shared by desktop and phone viewers. */
UCLASS()
class CLEVELANDREAL_API USceneControls : public UActorComponent
{
    GENERATED_BODY()
public:
    USceneControls();
    TSharedRef<FJsonObject> VerifyEffects();
protected:
    virtual void BeginPlay() override;
private:
    UFUNCTION()
    void HandleCommand(const FString& Descriptor);
    bool GoToRoom(const FString& Id);
    void SetSun(int64 UtcSeconds);
    void Respond(const FString& Error = TEXT(""));

    UPROPERTY()
    TObjectPtr<UActorComponent> StreamInput;
    UPROPERTY()
    TObjectPtr<ADirectionalLight> Sun;
    FString Room = TEXT("living");
    int64 Time = 1788886800; // 2026-09-08 13:00 in Washington, DC.
    float Elevation = 0.f;
    float Azimuth = 0.f;
    float Exposure = -0.5f;
    double LastStatus = 0;
    FSceneEffects Effects;
};
