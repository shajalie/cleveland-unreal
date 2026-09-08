#include "SceneEffects.h"
#include "LandscapeCluster.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
    FString OptionsPath() { return FPaths::ProjectSavedDir() / TEXT("ClevelandReview/scene-effects.json"); }
}

bool FSceneEffects::Read(const TSharedPtr<FJsonObject>& Input)
{
    if (!Input || Input->Values.Num() == 0 || Input->Values.Num() > 5) return false;
    // Validate the entire edit before applying any part; never accept console text.
    for (const auto& Pair : Input->Values)
    {
        if (Pair.Key != TEXT("grass") && Pair.Key != TEXT("plants") && Pair.Key != TEXT("breeze") &&
            Pair.Key != TEXT("rayShadows") && Pair.Key != TEXT("reflections")) return false;
        if (!Pair.Value || Pair.Value->Type != EJson::Boolean) return false;
    }
    Input->TryGetBoolField(TEXT("grass"), Grass);
    Input->TryGetBoolField(TEXT("plants"), Plants);
    Input->TryGetBoolField(TEXT("breeze"), Breeze);
    Input->TryGetBoolField(TEXT("rayShadows"), RayShadows);
    Input->TryGetBoolField(TEXT("reflections"), Reflections);
    return true;
}

void FSceneEffects::Initialize(UWorld* World)
{
    FString Json;
    TSharedPtr<FJsonObject> Saved;
    if (FFileHelper::LoadFileToString(Json, *OptionsPath()) && Json.Len() <= 1024 &&
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Saved)) Read(Saved);
    Apply(World);
}

bool FSceneEffects::Update(UWorld* World, const TSharedPtr<FJsonObject>& Input)
{
    if (!Read(Input)) return false;
    Apply(World);
    auto Saved = Snapshot();
    Saved->RemoveField(TEXT("grassClusters"));
    Saved->RemoveField(TEXT("plantClusters"));
    FString Json;
    FJsonSerializer::Serialize(Saved, TJsonWriterFactory<>::Create(&Json));
    IFileManager::Get().MakeDirectory(*FPaths::GetPath(OptionsPath()), true);
    FFileHelper::SaveStringToFile(Json, *OptionsPath());
    return true;
}

void FSceneEffects::Apply(UWorld* World)
{
    GrassClusters = PlantClusters = 0;
    for (TActorIterator<ALandscapeCluster> It(World); It; ++It)
    {
        if (It->ActorHasTag(TEXT("ClevelandGrass")))
        {
            It->Instances->SetVisibility(Grass); ++GrassClusters;
        }
        if (It->ActorHasTag(TEXT("ClevelandPlants")))
        {
            It->Instances->SetVisibility(Plants); ++PlantClusters;
        }
    }
    if (!MaterialsReady)
    {
        // Cache only materials that actually support wind, once per level.
        // The component retains each dynamic instance; weak references avoid owning actors.
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            TInlineComponentArray<UStaticMeshComponent*> Components(*It);
            for (auto* Component : Components)
            {
                const bool Garden = It->IsA<ALandscapeCluster>();
                for (int32 I = 0; I < Component->GetNumMaterials(); ++I)
                {
                    auto* Material = Component->GetMaterial(I);
                    if (!Material || (!Garden && !Material->GetName().StartsWith(TEXT("MI_Cutout_")))) continue;
                    float DefaultStrength = 0;
                    if (!Material->GetScalarParameterValue(FMaterialParameterInfo(TEXT("BreezeStrength")), DefaultStrength)) continue;
                    if (auto* Dynamic = Component->CreateDynamicMaterialInstance(I))
                        WindMaterials.Add({Dynamic, DefaultStrength});
                }
            }
        }
        MaterialsReady = true;
    }
    for (const auto& Wind : WindMaterials)
        if (auto* Material = Wind.Material.Get()) Material->SetScalarParameterValue(TEXT("BreezeStrength"), Breeze ? Wind.Strength : 0.f);
    if (auto* CVar = IConsoleManager::Get().FindConsoleVariable(TEXT("r.RayTracing.Shadows")))
        CVar->Set(RayShadows ? 1 : 0, ECVF_SetByConsole);
    if (auto* CVar = IConsoleManager::Get().FindConsoleVariable(TEXT("r.Lumen.Reflections.Allow")))
        CVar->Set(Reflections ? 1 : 0, ECVF_SetByConsole);
}

TSharedRef<FJsonObject> FSceneEffects::Snapshot() const
{
    auto State = MakeShared<FJsonObject>();
    State->SetBoolField(TEXT("grass"), Grass);
    State->SetBoolField(TEXT("plants"), Plants);
    State->SetBoolField(TEXT("breeze"), Breeze);
    State->SetBoolField(TEXT("rayShadows"), RayShadows);
    State->SetBoolField(TEXT("reflections"), Reflections);
    State->SetNumberField(TEXT("grassClusters"), GrassClusters);
    State->SetNumberField(TEXT("plantClusters"), PlantClusters);
    return State;
}

TSharedRef<FJsonObject> FSceneEffects::Verify(UWorld* World)
{
    // Opt-in packaged regression: exercise actual component visibility, wind
    // parameters, console switches, rejection and disk persistence, then restore.
    auto Original = Snapshot();
    Original->RemoveField(TEXT("grassClusters")); Original->RemoveField(TEXT("plantClusters"));
    auto Off = MakeShared<FJsonObject>();
    for (const auto& Pair : Original->Values) Off->SetBoolField(Pair.Key, false);
    bool Passed = Update(World, Off) && GrassClusters > 0 && PlantClusters > 0 && WindMaterials.Num() > 0;
    for (TActorIterator<ALandscapeCluster> It(World); It; ++It)
        if (It->ActorHasTag(TEXT("ClevelandGrass")) || It->ActorHasTag(TEXT("ClevelandPlants")))
            Passed &= !It->Instances->IsVisible() && It->Instances->GetCollisionEnabled() == ECollisionEnabled::NoCollision;
    for (const auto& Wind : WindMaterials)
    {
        float Strength = -1;
        Passed &= Wind.Material.IsValid() && Wind.Material->GetScalarParameterValue(FMaterialParameterInfo(TEXT("BreezeStrength")), Strength) && Strength == 0;
    }
    const auto* Ray = IConsoleManager::Get().FindConsoleVariable(TEXT("r.RayTracing.Shadows"));
    const auto* Reflection = IConsoleManager::Get().FindConsoleVariable(TEXT("r.Lumen.Reflections.Allow"));
    Passed &= Ray && Ray->GetInt() == 0 && Reflection && Reflection->GetInt() == 0;
    FString SavedJson; TSharedPtr<FJsonObject> Saved;
    bool SavedOff = FFileHelper::LoadFileToString(SavedJson, *OptionsPath()) &&
        FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(SavedJson), Saved) && Saved && Saved->Values.Num() == 5;
    if (SavedOff) for (const auto& Pair : Saved->Values) SavedOff &= Pair.Value->Type == EJson::Boolean && !Pair.Value->AsBool();
    auto Invalid = MakeShared<FJsonObject>(); Invalid->SetStringField(TEXT("grass"), TEXT("false"));
    const bool RejectType = !Update(World, Invalid);
    Invalid = MakeShared<FJsonObject>();
    Invalid->SetBoolField(TEXT("unknownConsoleCommand"), true);
    const bool RejectUnknown = !Update(World, Invalid);
    const bool Restored = Update(World, Original);
    auto Result = MakeShared<FJsonObject>();
    Result->SetBoolField(TEXT("visibilityWindAndLighting"), Passed);
    Result->SetBoolField(TEXT("savedOnPc"), SavedOff);
    Result->SetBoolField(TEXT("rejectsInvalidSettings"), RejectType && RejectUnknown);
    Result->SetBoolField(TEXT("restored"), Restored);
    Result->SetNumberField(TEXT("windMaterials"), WindMaterials.Num());
    Result->SetNumberField(TEXT("grassClusters"), GrassClusters);
    Result->SetNumberField(TEXT("plantClusters"), PlantClusters);
    Result->SetBoolField(TEXT("passed"), Passed && SavedOff && RejectType && RejectUnknown && Restored);
    return Result;
}
