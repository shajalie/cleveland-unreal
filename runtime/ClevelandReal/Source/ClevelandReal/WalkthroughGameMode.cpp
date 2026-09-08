#include "WalkthroughGameMode.h"
#include "WalkingCharacter.h"

AWalkthroughGameMode::AWalkthroughGameMode()
{
    DefaultPawnClass = AWalkingCharacter::StaticClass();
}
