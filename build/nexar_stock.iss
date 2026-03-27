; ════════════════════════════════════════════════════════════
; build/nexar_stock.iss — Script de Inno Setup 6
;
; Genera un instalador profesional para Windows que:
;   - Instala en la carpeta del usuario (sin requerir admin)
;   - Crea acceso directo en el Escritorio (opcional)
;   - Crea entrada en el Menú Inicio
;   - Incluye desinstalador automático
;
; Para compilar manualmente:
;   ISCC.exe /DAppVersion=1.6.0 build\nexar_stock.iss
;
; GitHub Actions pasa la versión automáticamente.
; ════════════════════════════════════════════════════════════

; ── CONSTANTES ──────────────────────────────────────────────
; Si no se pasa /DAppVersion desde la línea de comando,
; usa "1.0.0" como valor por defecto
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

#define AppName      "Nexar Stock"
#define AppExeName   "NexarStock.exe"
#define AppPublisher "Nexar Sistemas"
#define AppURL       "https://wa.me/5492645858874"

; ── CONFIGURACIÓN GENERAL ───────────────────────────────────
[Setup]
; AppId es un GUID único para este producto.
; NO cambies este valor entre versiones o el desinstalador fallará.
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Instala en la carpeta de datos del usuario — no requiere permisos de admin
; {userappdata} = C:\Users\NombreUsuario\AppData\Roaming\
DefaultDirName={userappdata}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes

; Ruta y nombre del instalador resultante
; Relativo a este .iss: sube un nivel (..) y entra a dist/installer/
OutputDir=..\dist\installer
OutputBaseFilename=NexarStock_{#AppVersion}_Setup

; Ícono del instalador (relativo a este .iss)
SetupIconFile=..\static\icons\nexar_stock_ico.ico

; Compresión máxima para menor tamaño del instalador
Compression=lzma2/ultra64
SolidCompression=yes

; Estilo moderno con barra lateral y colores
WizardStyle=modern
WizardResizable=no

; No requiere derechos de administrador
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Instalar en modo 64 bits si el sistema lo soporta
ArchitecturesInstallIn64BitMode=x64compatible

; Requiere Windows 10 o superior
MinVersion=10.0

; ── IDIOMA ──────────────────────────────────────────────────
[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

; ── TAREAS OPCIONALES ───────────────────────────────────────
; Nota: NO usar Flags: checked — es inválido en Inno Setup 6
[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Opciones adicionales:"

; ── ARCHIVOS A INSTALAR ─────────────────────────────────────
[Files]
; El .exe de PyInstaller (relativo a este .iss)
Source: "..\dist\NexarStock.exe"; DestDir: "{app}"; Flags: ignoreversion

; ── ACCESOS DIRECTOS ────────────────────────────────────────
; Reglas importantes:
; - Cada entrada en una sola línea (no dividir con &)
; - Usar {userprograms} y {userdesktop}, NO {commonprograms} ni {commondesktop}
;   (los comunes requieren permisos de administrador y dan error de acceso)
[Icons]
Name: "{userprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Comment: "Sistema de gestión para almacenes"
Name: "{userprograms}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Comment: "Sistema de gestión para almacenes"; Tasks: desktopicon

; ── EJECUTAR AL TERMINAR LA INSTALACIÓN ─────────────────────
[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName} ahora"; Flags: nowait postinstall skipifsilent

; ── MENSAJES PERSONALIZADOS ─────────────────────────────────
[Messages]
WelcomeLabel1=Bienvenido al instalador de {#AppName} v{#AppVersion}
WelcomeLabel2=Este asistente instalará {#AppName} en tu computadora.%n%nNexar Stock es un sistema de gestión completo para almacenes y pequeños comercios.%n%nCerrá todas las demás aplicaciones antes de continuar.
FinishedHeadingLabel=Instalación completada
FinishedLabel={#AppName} v{#AppVersion} se instaló correctamente.%n%nHacé clic en Finalizar para cerrar el asistente.
```