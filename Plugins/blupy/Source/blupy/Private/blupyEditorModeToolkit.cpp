// Copyright Epic Games, Inc. All Rights Reserved.

#include "blupyEditorModeToolkit.h"
#include "blupyEditorMode.h"
#include "Engine/Selection.h"

#include "Modules/ModuleManager.h"
#include "PropertyEditorModule.h"
#include "IDetailsView.h"
#include "EditorModeManager.h"

#define LOCTEXT_NAMESPACE "blupyEditorModeToolkit"

FblupyEditorModeToolkit::FblupyEditorModeToolkit()
{
}

void FblupyEditorModeToolkit::Init(const TSharedPtr<IToolkitHost>& InitToolkitHost, TWeakObjectPtr<UEdMode> InOwningMode)
{
	FModeToolkit::Init(InitToolkitHost, InOwningMode);
}

void FblupyEditorModeToolkit::GetToolPaletteNames(TArray<FName>& PaletteNames) const
{
	PaletteNames.Add(NAME_Default);
}


FName FblupyEditorModeToolkit::GetToolkitFName() const
{
	return FName("blupyEditorMode");
}

FText FblupyEditorModeToolkit::GetBaseToolkitName() const
{
	return LOCTEXT("DisplayName", "blupyEditorMode Toolkit");
}

#undef LOCTEXT_NAMESPACE
