// Copyright Epic Games, Inc. All Rights Reserved.

#include "BluePy.h"
#include "LevelEditor.h"
#include "SlateBasics.h"
#include "SlateExtras.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/PlatformFilemanager.h"
#include "IImageWrapperModule.h"
#include "IImageWrapper.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Json.h"

#define LOCTEXT_NAMESPACE "FBluePyModule"

void FBluePyModule::StartupModule()
{
    RegisterMenus();
    UE_LOG(LogTemp, Log, TEXT("BluePy Module Started"));
}

void FBluePyModule::ShutdownModule()
{
    UE_LOG(LogTemp, Log, TEXT("BluePy Module Shutdown"));
}

void FBluePyModule::RegisterMenus()
{
    FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");

    TSharedPtr<FExtender> MenuExtender = MakeShareable(new FExtender());
    MenuExtender->AddMenuExtension("FileProject", EExtensionHook::After, nullptr, FMenuExtensionDelegate::CreateRaw(this, &FBluePyModule::OnCropBlueprint));

    LevelEditorModule.GetMenuExtensibilityManager()->AddExtender(MenuExtender);
    UE_LOG(LogTemp, Log, TEXT("Menu Registered in Level Editor"));
}

void FBluePyModule::OnCropBlueprint()
{
    FString CroppedText = "Cropped Blueprint Code";
    CopyToClipboard(CroppedText);
    UE_LOG(LogTemp, Log, TEXT("Blueprint code copied to clipboard"));

    FString ScreenshotPath = FPaths::ProjectSavedDir() / TEXT("Screenshots/BlueprintCrop.png");
    TakeScreenshot(ScreenshotPath);
    UE_LOG(LogTemp, Log, TEXT("Screenshot taken at: %s"), *ScreenshotPath);

    // Send to OpenAI Vision API
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request = FHttpModule::Get().CreateRequest();
    Request->OnProcessRequestComplete().BindRaw(this, &FBluePyModule::OnResponseReceived);
    Request->SetURL("https://api.openai.com/v1/images");
    Request->SetVerb("POST");
    Request->SetHeader("Content-Type", "application/json");
    Request->SetHeader("Authorization", "Bearer YOUR_API_KEY");

    FString Payload = FString::Printf(TEXT("{\"image\": \"%s\"}"), *ScreenshotPath);
    Request->SetContentAsString(Payload);
    Request->ProcessRequest();
    UE_LOG(LogTemp, Log, TEXT("OpenAI Vision API request sent"));
}

void FBluePyModule::OnResponseReceived(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (bWasSuccessful && Response->GetResponseCode() == 200)
    {
        FString ResponseString = Response->GetContentAsString();
        UE_LOG(LogTemp, Log, TEXT("Successful response received: %s"), *ResponseString);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to receive a successful response"));
    }
}

void FBluePyModule::TakeScreenshot(FString FilePath)
{
    FScreenshotRequest::RequestScreenshot(FilePath, false, false);
    UE_LOG(LogTemp, Log, TEXT("Screenshot requested for path: %s"), *FilePath);
}

void FBluePyModule::CopyToClipboard(FString Text)
{
    FPlatformApplicationMisc::ClipboardCopy(*Text);
    UE_LOG(LogTemp, Log, TEXT("Text copied to clipboard: %s"), *Text);
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FBluePyModule, BluePy)
