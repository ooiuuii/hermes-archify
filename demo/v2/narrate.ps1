param(
    [string] $OutputDirectory,
    [string] $Voice = 'Microsoft Huihui Desktop',
    [string[]] $SceneIds = @(),
    [string] $StoryboardPath = (Join-Path $PSScriptRoot 'storyboard.json')
)
$ErrorActionPreference = 'Stop'
if (-not $OutputDirectory) { throw 'An explicit output directory is required.' }
$story = Get-Content -LiteralPath $StoryboardPath -Raw -Encoding UTF8 | ConvertFrom-Json
$audioDirectory = Join-Path $OutputDirectory 'audio'
New-Item -ItemType Directory -Path $audioDirectory -Force | Out-Null
Add-Type -AssemblyName System.Speech
$speaker = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
    $speaker.SelectVoice($Voice)
    $speaker.Rate = 0
    foreach ($scene in $story.scenes) {
        if ($SceneIds.Count -and $scene.id -notin $SceneIds) { continue }
        $destination = Join-Path $audioDirectory ($scene.id + '.wav')
        if (Test-Path -LiteralPath $destination) {
            throw "Audio already exists; use a fresh output directory: $destination"
        }
        $speaker.SetOutputToWaveFile($destination)
        $speaker.Speak($scene.narration)
        $speaker.SetOutputToNull()
        Write-Output "Narrated $($scene.id) using local Windows speech."
    }
} finally {
    $speaker.Dispose()
}
