// Copyright Epic Games, Inc. All Rights Reserved.

#include "blupyEditorMode.h"
#include "blupyEditorModeToolkit.h"
#include "EdModeInteractiveToolsContext.h"
#include "InteractiveToolManager.h"
#include "blupyEditorModeCommands.h"


//////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////// 
// AddYourTool Step 1 - include the header file for your Tools here
//////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////// 
#include "Tools/blupySimpleTool.h"
#include "Tools/blupyInteractiveTool.h"

// step 2: register a ToolBuilder in FblupyEditorMode::Enter() below


#define LOCTEXT_NAMESPACE "blupyEditorMode"

const FEditorModeID UblupyEditorMode::EM_blupyEditorModeId = TEXT("EM_blupyEditorMode");

FString UblupyEditorMode::SimpleToolName = TEXT("blupy_ActorInfoTool");
FString UblupyEditorMode::InteractiveToolName = TEXT("blupy_MeasureDistanceTool");


UblupyEditorMode::UblupyEditorMode()
{
	FModuleManager::Get().LoadModule("EditorStyle");

	// appearance and icon in the editing mode ribbon can be customized here
	Info = FEditorModeInfo(UblupyEditorMode::EM_blupyEditorModeId,
		LOCTEXT("ModeName", "blupy"),
		FSlateIcon(),
		true);
}


UblupyEditorMode::~UblupyEditorMode()
{
}


void UblupyEditorMode::ActorSelectionChangeNotify()
{
}

void UblupyEditorMode::Enter()
{
	UEdMode::Enter();

	//////////////////////////////////////////////////////////////////////////
	//////////////////////////////////////////////////////////////////////////
	// AddYourTool Step 2 - register the ToolBuilders for your Tools here.
	// The string name you pass to the ToolManager is used to select/activate your ToolBuilder later.
	//////////////////////////////////////////////////////////////////////////
	////////////////////////////////////////////////////////////////////////// 
	const FblupyEditorModeCommands& SampleToolCommands = FblupyEditorModeCommands::Get();

	RegisterTool(SampleToolCommands.SimpleTool, SimpleToolName, NewObject<UblupySimpleToolBuilder>(this));
	RegisterTool(SampleToolCommands.InteractiveTool, InteractiveToolName, NewObject<UblupyInteractiveToolBuilder>(this));

	// active tool type is not relevant here, we just set to default
	GetToolManager()->SelectActiveToolType(EToolSide::Left, SimpleToolName);
}

void UblupyEditorMode::CreateToolkit()
{
	Toolkit = MakeShareable(new FblupyEditorModeToolkit);
}

TMap<FName, TArray<TSharedPtr<FUICommandInfo>>> UblupyEditorMode::GetModeCommands() const
{
	return FblupyEditorModeCommands::Get().GetCommands();
}

#undef LOCTEXT_NAMESPACE
