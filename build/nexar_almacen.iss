; ════════════════════════════════════════════════════════════
; build/nexar_almacen.iss — Script de Inno Setup 6
;
; Genera un instalador profesional para Windows que:
;   - Instala en la carpeta del usuario (sin requerir admin)
;   - Crea acceso directo en el Escritorio (opcional)
;   - Crea entrada en el Menú Inicio
;   - Incluye desinstalador automático
;
; Para compilar manualmente:
;   ISCC.exe /DAppVersion=1.7.0 build\nexar_almacen.iss
;
; GitHub Actions pasa la versión automáticamente.
; ════════════════════════════════════════════════════════════

; ── CONSTANTES ──────────────────────────────────────────────
; Si no se pasa /DAppVersion desde la línea de comando,
; usa "1.0.0" como valor por defecto
; ════════════════════════════════════════════════════════════
; build/nexar_almacen.iss — Script de Inno Setup 6
; ════════════════════════════════════════════════════════════

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

#define AppName      "Nexar Almacen"
#define AppExeName   "NexarAlmacen.exe"
#define AppPublisher "Nexar Sistemas"
#define AppURL       "https://wa.me/5492645858874"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

DefaultDirName={userappdata}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes

OutputDir=..\dist\installer
OutputBaseFilename=NexarAlmacen_{#AppVersion}_Setup

SetupIconFile=..\static\icons\nexar_almacen_ico.ico

; ─── CAMBIO: el usuario debe aceptar la licencia antes de instalar ────────
; Inno Setup muestra esta pantalla automáticamente antes de cualquier otro paso
LicenseFile=..\LICENSE.txt
; ──────────────────────────────────────────────────────────────────────────

Compression=lzma2/ultra64
SolidCompression=yes

WizardStyle=modern
WizardResizable=no

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

ArchitecturesInstallIn64BitMode=x64compatible

MinVersion=10.0

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Opciones adicionales:"

[Files]
Source: "..\dist\NexarAlmacen.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Comment: "Sistema de gestión para almacenes"
Name: "{userprograms}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Comment: "Sistema de gestión para almacenes"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName} ahora"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel1=Bienvenido al instalador de {#AppName} v{#AppVersion}
WelcomeLabel2=Este asistente instalará {#AppName} en tu computadora.%n%nNexar Almacen es un sistema de gestión completo para almacenes y pequeños comercios.%n%nCerrá todas las demás aplicaciones antes de continuar.
FinishedHeadingLabel=Instalación completada
FinishedLabel={#AppName} v{#AppVersion} se instaló correctamente.%n%nHacé clic en Finalizar para cerrar el asistente.

; ─── CAMBIO: verificar que WebView2 Runtime esté instalado ────────────────
; WebView2 es el motor que usa pywebview para mostrar la ventana nativa.
; En Windows 10/11 actualizado ya viene instalado (con Edge).
; Este código verifica si está presente y avisa al usuario si falta.
[Code]
function IsWebView2Installed(): Boolean;
var
  Version: String;
begin
  Result := RegQueryStringValue(
    HKLM,
    'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
    'pv',
    Version
  );
  if not Result then
    Result := RegQueryStringValue(
      HKCU,
      'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
      'pv',
      Version
    );
end;

procedure InitializeWizard();
begin
  if not IsWebView2Installed() then
    MsgBox(
      'Atención: Microsoft WebView2 Runtime no está instalado.' + #13#10 + #13#10 +
      'Nexar Almacen puede funcionar sin él, pero la aplicación se abrirá ' +
      'en el navegador predeterminado en lugar de una ventana propia.' + #13#10 + #13#10 +
      'Para instalar WebView2 visitá: aka.ms/getwebview2' + #13#10 +
      '(suele estar incluido en Windows 10/11 actualizado)',
      mbInformation, MB_OK
    );
end;