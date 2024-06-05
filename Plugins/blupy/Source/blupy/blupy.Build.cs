// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class blupy : ModuleRules
{
    public blupy(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
        
        PublicIncludePaths.AddRange(
            new string[] {
                // ... add public include paths required here ...
            }
        );
                
        PrivateIncludePaths.AddRange(
            new string[] {
                // ... add other private include paths required here ...
            }
        );
            
        PublicDependencyModuleNames.AddRange(
            new string[]
            {
                "Core",
                "CoreUObject",
                "Engine",
                "InputCore",
                "HTTP",
                "Json",
                "JsonUtilities",
                "ImageWrapper"
				"UnrealBuildTool"
            }
        );
        
        PrivateDependencyModuleNames.AddRange(
            new string[]
            {
                "EditorFramework",
                "EditorStyle",
                "UnrealEd",
                "LevelEditor",
                "InteractiveToolsFramework",
                "EditorInteractiveToolsFramework",
                "Slate",
                "SlateCore"
                // ... add other private dependencies here ...
            }
        );
        
        DynamicallyLoadedModuleNames.AddRange(
            new string[]
            {
                // ... add any modules that your module loads dynamically here ...
            }
        );
    }
}

