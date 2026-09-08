#pragma once

#include "CoreMinimal.h"

class UCameraComponent;
class AActor;

/** Display exposure for the physically lit scene; does not change illumination. */
namespace DaylightExposure
{
    inline constexpr int32 Version = 2;
    inline constexpr float MinEV100 = -4.f;
    inline constexpr float MaxEV100 = 20.f;
    inline constexpr float HistogramMinEV100 = -8.f;
    inline constexpr float HistogramMaxEV100 = 20.f;

    void Configure(UCameraComponent& Camera, float Compensation);
    void ResetAfterJump(AActor* Viewer);
}
