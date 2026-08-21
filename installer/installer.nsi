; DNA Lab Installer Script
; Requires NSIS to compile

!include "MUI2.nsh"

Name "DNA Lab"
OutFile "..\DNA_Lab_Setup.exe"
InstallDir "$LOCALAPPDATA\DNA_Lab"
RequestExecutionLevel user

!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    File "..\dist\DNA_Lab.exe"
    
    CreateShortCut "$DESKTOP\DNA Lab.lnk" "$INSTDIR\DNA_Lab.exe"
    
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\DNA_Lab.exe"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$DESKTOP\DNA Lab.lnk"
    RMDir "$INSTDIR"
SectionEnd
