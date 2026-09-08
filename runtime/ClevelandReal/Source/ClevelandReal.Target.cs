using UnrealBuildTool;

public class ClevelandRealTarget : TargetRules
{
    public ClevelandRealTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("ClevelandReal");
    }
}
