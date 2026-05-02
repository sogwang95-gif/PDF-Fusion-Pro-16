; PDF Fusion 26 NSIS Installer Script
; Simple, clean installer for Windows
; Generated: 2026

Unicode true
ManifestDPIAware true

; -------------------------------
; BASIC SETTINGS
; -------------------------------
Name "PDF Fusion 26"
OutFile "PDF_Fusion_26_Setup.exe"
InstallDir "$PROGRAMFILES64\PDF Fusion 26"
InstallDirRegKey HKLM "Software\PDF Fusion 26" "Install_Dir"
RequestExecutionLevel admin

; -------------------------------
; MODERN UI
; -------------------------------
!include "MUI2.nsh"

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${NSISDIR}\Docs\Modern UI\License.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language
!insertmacro MUI_LANGUAGE "English"

; -------------------------------
; INSTALLER SECTIONS
; -------------------------------
Section "PDF Fusion 26 (required)" SecMain
  SectionIn RO
  
  ; Set output path to the installation directory
  SetOutPath $INSTDIR
  
  ; Add files
  File "fusion222.py"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  ; Write registry keys
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PDF_Fusion_26" \
                   "DisplayName" "PDF Fusion 26"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PDF_Fusion_26" \
                   "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PDF_Fusion_26" \
                   "DisplayVersion" "26.1.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PDF_Fusion_26" \
                   "Publisher" "Kay Xam"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PDF_Fusion_26" \
                   "DisplayIcon" "$INSTDIR\uninstall.exe"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PDF_Fusion_26" \
                     "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PDF_Fusion_26" \
                     "NoRepair" 1
  
  ; Create desktop shortcut (optional component)
  ; This will be handled by the Desktop Shortcut section
  
SectionEnd

Section "Desktop Shortcut" SecDesktopShortcut
  CreateShortCut "$DESKTOP\PDF Fusion 26.lnk" "python" '"$INSTDIR\fusion222.py"' "" "" "" "" "Open PDF Fusion 26"
SectionEnd

Section "Start Menu Shortcut" SecStartMenu
  CreateDirectory "$SMPROGRAMS\PDF Fusion 26"
  CreateShortCut "$SMPROGRAMS\PDF Fusion 26\PDF Fusion 26.lnk" "python" '"$INSTDIR\fusion222.py"' "" "" "" "" "Open PDF Fusion 26"
  CreateShortCut "$SMPROGRAMS\PDF Fusion 26\Uninstall.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Python Runtime Check" SecPythonCheck
  ; Create a simple batch file that checks for Python
  FileOpen $0 "$INSTDIR\run_pdf_fusion.bat" w
  FileWrite $0 '@echo off$\r$\n'
  FileWrite $0 'echo Checking for Python...$\r$\n'
  FileWrite $0 'python --version >nul 2>&1$\r$\n'
  FileWrite $0 'if errorlevel 1 ($\r$\n'
  FileWrite $0 '  echo ERROR: Python not found!$\r$\n'
  FileWrite $0 '  echo.$\r$\n'
  FileWrite $0 '  echo PDF Fusion 26 requires Python 3.10 or higher.$\r$\n'
  FileWrite $0 '  echo Please install Python from https://python.org$\r$\n'
  FileWrite $0 '  echo.$\r$\n'
  FileWrite $0 '  echo After installing Python, also install PyPDF2:$\r$\n'
  FileWrite $0 '  echo   pip install PyPDF2$\r$\n'
  FileWrite $0 '  pause$\r$\n'
  FileWrite $0 '  exit /b 1$\r$\n'
  FileWrite $0 ')$\r$\n'
  FileWrite $0 '$\r$\n'
  FileWrite $0 'echo Checking for PyPDF2...$\r$\n'
  FileWrite $0 'python -c "import PyPDF2" >nul 2>&1$\r$\n'
  FileWrite $0 'if errorlevel 1 ($\r$\n'
  FileWrite $0 '  echo WARNING: PyPDF2 not found!$\r$\n'
  FileWrite $0 '  echo.$\r$\n'
  FileWrite $0 '  echo Installing PyPDF2...$\r$\n'
  FileWrite $0 '  pip install PyPDF2$\r$\n'
  FileWrite $0 '  if errorlevel 1 ($\r$\n'
  FileWrite $0 '    echo ERROR: Failed to install PyPDF2$\r$\n'
  FileWrite $0 '    echo Please install manually: pip install PyPDF2$\r$\n'
  FileWrite $0 '    pause$\r$\n'
  FileWrite $0 '  )$\r$\n'
  FileWrite $0 ')$\r$\n'
  FileWrite $0 '$\r$\n'
  FileWrite $0 'echo Starting PDF Fusion 26...$\r$\n'
  FileWrite $0 'echo.$\r$\n'
  FileWrite $0 'python "$INSTDIR\fusion222.py"$\r$\n'
  FileWrite $0 'pause$\r$\n'
  FileClose $0
  
  ; Update shortcuts to use batch file
  ${If} ${SectionIsSelected} ${SecDesktopShortcut}
    Delete "$DESKTOP\PDF Fusion 26.lnk"
    CreateShortCut "$DESKTOP\PDF Fusion 26.lnk" "$INSTDIR\run_pdf_fusion.bat" "" "" "" "" "Open PDF Fusion 26"
  ${EndIf}
  
  ${If} ${SectionIsSelected} ${SecStartMenu}
    Delete "$SMPROGRAMS\PDF Fusion 26\PDF Fusion 26.lnk"
    CreateShortCut "$SMPROGRAMS\PDF Fusion 26\PDF Fusion 26.lnk" "$INSTDIR\run_pdf_fusion.bat" "" "" "" "" "Open PDF Fusion 26"
  ${EndIf}
SectionEnd

; -------------------------------
; SECTION DESCRIPTIONS
; -------------------------------
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "Main application files (required)."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktopShortcut} "Create a shortcut on your desktop."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Create Start Menu shortcuts."
  !insertmacro MUI_DESCRIPTION_TEXT ${SecPythonCheck} "Add Python dependency checker. Recommended for first-time users."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; -------------------------------
; UNINSTALLER
; -------------------------------
Section "Uninstall"
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PDF_Fusion_26"
  DeleteRegKey HKLM "Software\PDF Fusion 26"
  
  ; Remove files and uninstaller
  Delete "$INSTDIR\fusion222.py"
  Delete "$INSTDIR\run_pdf_fusion.bat"
  Delete "$INSTDIR\uninstall.exe"
  
  ; Remove shortcuts, if any
  Delete "$DESKTOP\PDF Fusion 26.lnk"
  Delete "$SMPROGRAMS\PDF Fusion 26\PDF Fusion 26.lnk"
  Delete "$SMPROGRAMS\PDF Fusion 26\Uninstall.lnk"
  RMDir "$SMPROGRAMS\PDF Fusion 26"
  
  ; Remove directories
  RMDir "$INSTDIR"
  
SectionEnd

; -------------------------------
; INIT FUNCTIONS
; -------------------------------
Function .onInit
  ; Check for admin rights
  UserInfo::GetAccountType
  pop $0
  ${If} $0 != "admin"
    MessageBox MB_OK|MB_ICONEXCLAMATION "This installer requires administrator privileges."
    SetErrorLevel 740 ; ERROR_ELEVATION_REQUIRED
    Quit
  ${EndIf}
  
  ; Auto-select Python check by default
  SectionSetFlags ${SecPythonCheck} ${SF_SELECTED}
FunctionEnd

Function .onInstSuccess
  ; Optional: Show message about Python requirement
  ${If} ${SectionIsSelected} ${SecPythonCheck}
    MessageBox MB_OK|MB_ICONINFORMATION "PDF Fusion 26 has been installed.$\r$\n$\r$\nNote: This application requires Python 3.10+ and PyPDF2.$\r$\nThe installer has created a launcher that will check for these dependencies."
  ${Else}
    MessageBox MB_OK|MB_ICONINFORMATION "PDF Fusion 26 has been installed.$\r$\n$\r$\nNote: This application requires Python 3.10+ and PyPDF2.$\r$\nMake sure these are installed before running the application."
  ${EndIf}
FunctionEnd