#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"

class SChatInterface : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SChatInterface) {}
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs);

private:
    FReply OnSendMessage();
    void LoadOldChats();
    void SaveChat(FString Message);

    TSharedPtr<SEditableTextBox> InputTextBox;
    TSharedPtr<STextBlock> ChatHistory;
    TArray<FString> OldChats;
};