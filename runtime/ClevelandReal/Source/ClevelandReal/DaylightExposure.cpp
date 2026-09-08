#include "DaylightExposure.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

void DaylightExposure::Configure(UCameraComponent& Camera, float Compensation)
{
    auto& Settings = Camera.PostProcessSettings;
    // DefaultEngine.ini opts into EV100 units. Explicit camera overrides avoid
    // inherited/imported post-process ranges clamping the outdoor histogram.
    Settings.bOverride_AutoExposureMethod = true;
    Settings.AutoExposureMethod = AEM_Histogram;
    Settings.bOverride_AutoExposureMinBrightness = true;
    Settings.AutoExposureMinBrightness = MinEV100;
    Settings.bOverride_AutoExposureMaxBrightness = true;
    Settings.AutoExposureMaxBrightness = MaxEV100;
    Settings.bOverride_HistogramLogMin = true;
    Settings.HistogramLogMin = HistogramMinEV100;
    Settings.bOverride_HistogramLogMax = true;
    Settings.HistogramLogMax = HistogramMaxEV100;
    Settings.bOverride_AutoExposureLowPercent = true;
    Settings.AutoExposureLowPercent = 10.f;
    Settings.bOverride_AutoExposureHighPercent = true;
    Settings.AutoExposureHighPercent = 90.f;
    Settings.bOverride_AutoExposureBias = true;
    Settings.AutoExposureBias = Compensation;
    // Stops per second: settle promptly outside; recover gently in a dark room.
    Settings.bOverride_AutoExposureSpeedUp = true;
    Settings.AutoExposureSpeedUp = 6.f;
    Settings.bOverride_AutoExposureSpeedDown = true;
    Settings.AutoExposureSpeedDown = 2.f;
    Camera.PostProcessBlendWeight = 1.f;
}

void DaylightExposure::ResetAfterJump(AActor* Viewer)
{
    const auto* Pawn = Cast<APawn>(Viewer);
    auto* Controller = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
    if (Controller && Controller->PlayerCameraManager)
        Controller->PlayerCameraManager->SetGameCameraCutThisFrame();
}
