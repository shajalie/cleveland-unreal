using UnrealBuildTool;

public class ClevelandRealEditorTarget : TargetRules
{
    public ClevelandRealEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("ClevelandReal");
    }
}
