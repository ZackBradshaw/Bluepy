// Copyright Epic Games, Inc. All Rights Reserved.

#include "blupyModule.h"
#include "blupyEditorModeCommands.h"

#define LOCTEXT_NAMESPACE "blupyModule"

void FblupyModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module

	FblupyEditorModeCommands::Register();
}

void FblupyModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

	FblupyEditorModeCommands::Unregister();
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FblupyModule, blupyEditorMode)