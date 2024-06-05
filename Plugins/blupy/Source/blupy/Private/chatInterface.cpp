#include "ChatInterface.h"
#include "SlateOptMacros.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

BEGIN_SLATE_FUNCTION_BUILD_OPTIMIZATION
void SChatInterface::Construct(const FArguments& InArgs)
{
    LoadOldChats();

    ChildSlot
    [
        SNew(SVerticalBox)
        + SVerticalBox::Slot()
        .AutoHeight()
        [
            SNew(SHorizontalBox)
            + SHorizontalBox::Slot()
            .FillWidth(1.0f)
            [
                SAssignNew(InputTextBox, SEditableTextBox)
            ]
            + SHorizontalBox::Slot()
            .AutoWidth()
            [
                SNew(SButton)
                .Text(FText::FromString("Send"))
                .OnClicked(this, &SChatInterface::OnSendMessage)
            ]
        ]
        + SVerticalBox::Slot()
        .FillHeight(1.0f)
        [
            SAssignNew(ChatHistory, STextBlock)
            .AutoWrapText(true)
        ]
    ];
    
    // Display old chats
    FString AllChats;
    for (const FString& Chat : OldChats)
    {
        AllChats += Chat + "\n";
    }
    ChatHistory->SetText(FText::FromString(AllChats));
}

FReply SChatInterface::OnSendMessage()
{
    if (InputTextBox.IsValid())
    {
        FString Message = InputTextBox->GetText().ToString();
        // Append message to chat history
        ChatHistory->SetText(FText::FromString(ChatHistory->GetText().ToString() + "\n" + Message));
        InputTextBox->SetText(FText::GetEmpty());

        // Save chat message
        SaveChat(Message);

        // Send message to OpenAI API
        // Implement API call here
    }
    return FReply::Handled();
}

void SChatInterface::LoadOldChats()
{
    FString ChatFilePath = FPaths::ProjectSavedDir() / TEXT("ChatHistory.txt");
    FFileHelper::LoadFileToStringArray(OldChats, *ChatFilePath);
}

void SChatInterface::SaveChat(FString Message)
{
    FString ChatFilePath = FPaths::ProjectSavedDir() / TEXT("ChatHistory.txt");
    OldChats.Add(Message);
    FFileHelper::SaveStringArrayToFile(OldChats, *ChatFilePath);
}
END_SLATE_FUNCTION_BUILD_OPTIMIZATION