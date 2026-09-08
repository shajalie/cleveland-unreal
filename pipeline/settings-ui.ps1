param([string]$PreviewPath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[Windows.Forms.Application]::EnableVisualStyles()
$form = New-Object Windows.Forms.Form
$form.Text = 'Cleveland walkthrough - GPU settings'
$form.ClientSize = New-Object Drawing.Size(520,490)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.AutoScaleMode = 'Dpi'
$form.Font = New-Object Drawing.Font('Segoe UI',10)

function Add-Label([string]$Text, [int]$Top) {
    $label = New-Object Windows.Forms.Label
    $label.Text = $Text
    $label.Location = New-Object Drawing.Point(20,$Top)
    $label.Size = New-Object Drawing.Size(260,28)
    $form.Controls.Add($label)
}
Add-Label 'Rendering PC' 23
$profiles = New-Object Windows.Forms.ComboBox
$profiles.DropDownStyle = 'DropDownList'
$profiles.Location = New-Object Drawing.Point(285,20)
$profiles.Size = New-Object Drawing.Size(210,28)
[void]$profiles.Items.Add('RTX 2060 / 6 GB')
[void]$profiles.Items.Add('RTX 5090 / 32 GB')
$form.Controls.Add($profiles)
$fields = [ordered]@{
    TexturePoolMB = @('Texture memory pool (MB)',256,24576,256)
    NanitePoolMB = @('Geometry streaming pool (MB)',64,4096,64)
    Width = @('Video width',640,3840,160)
    Height = @('Video height',360,2160,90)
    ScreenPercentage = @('Internal resolution (%)',25,100,5)
    MaxFPS = @('Frame-rate limit',15,120,5)
    MaxBitrateMbps = @('Video bitrate limit (Mbps)',2,80,2)
}
$controls = @{}
$row = 60
foreach ($key in $fields.Keys) {
    $field = $fields[$key]
    Add-Label $field[0] ($row + 3)
    $numberControl = New-Object Windows.Forms.NumericUpDown
    $numberControl.Minimum = $field[1]; $numberControl.Maximum = $field[2]; $numberControl.Increment = $field[3]
    $numberControl.Location = New-Object Drawing.Point(285,$row)
    $numberControl.Size = New-Object Drawing.Size(210,28)
    $form.Controls.Add($numberControl)
    $controls[$key] = $numberControl
    $row += 37
}
$notice = New-Object Windows.Forms.Label
$notice.Text = "Pool budgets do not cap total GPU memory. Ray tracing and other apps use additional VRAM. Both presets keep the full source assets and hardware ray tracing. The 5090 preset has not been tested on a 5090."
$notice.Location = New-Object Drawing.Point(20,325)
$notice.Size = New-Object Drawing.Size(480,85)
$form.Controls.Add($notice)

function Show-Settings($Settings) {
    foreach ($key in $controls.Keys) { $controls[$key].Value = $Settings.$key }
}
function Save-Settings {
    $values = @{ Profile = @('Laptop','RTX5090')[$profiles.SelectedIndex]; Save = $true }
    foreach ($key in $controls.Keys) { $values[$key] = [int]$controls[$key].Value }
    & (Join-Path $PSScriptRoot 'gpu-settings.ps1') @values | Out-Null
}
$saved = & (Join-Path $PSScriptRoot 'gpu-settings.ps1')
$profiles.SelectedIndex = if ($saved.profile -eq 'RTX5090') { 1 } else { 0 }
Show-Settings $saved
$profiles.add_SelectedIndexChanged({
    $selected = @('Laptop','RTX5090')[$profiles.SelectedIndex]
    Show-Settings (& (Join-Path $PSScriptRoot 'gpu-settings.ps1') -Profile $selected)
})
$save = New-Object Windows.Forms.Button
$save.Text = 'Save settings'
$save.Location = New-Object Drawing.Point(20,425)
$save.Size = New-Object Drawing.Size(155,38)
$save.add_Click({
    try { Save-Settings; $notice.Text = 'Saved for this PC. Restart the walkthrough to apply changes.' }
    catch { $notice.Text = $_.Exception.Message }
})
$form.Controls.Add($save)
$launch = New-Object Windows.Forms.Button
$launch.Text = 'Save and start stream'
$launch.Location = New-Object Drawing.Point(265,425)
$launch.Size = New-Object Drawing.Size(230,38)
$launch.add_Click({
    try {
        Save-Settings
        $launch.Enabled = $false
        & (Join-Path $PSScriptRoot 'stream.ps1') | Out-Null
        $chrome = @(
            (Join-Path $env:ProgramFiles 'Google/Chrome/Application/chrome.exe'),
            (Join-Path ${env:ProgramFiles(x86)} 'Google/Chrome/Application/chrome.exe'),
            (Join-Path $env:LOCALAPPDATA 'Google/Chrome/Application/chrome.exe')
        ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if ($chrome) {
            Start-Process -FilePath $chrome -ArgumentList 'http://127.0.0.1:5190/?AutoConnect=true&AutoPlayVideo=true&WaitForStreamer=true&MaxReconnectAttempts=100'
        }
        $notice.Text = 'Starting Unreal. Local Chrome preview: http://127.0.0.1:5190/ . Remote phone access is still being integrated.'
    } catch { $notice.Text = $_.Exception.Message; $launch.Enabled = $true }
})
$form.Controls.Add($launch)
if ($PreviewPath) {
    # Render this app's own controls for layout review; never capture other apps.
    $form.Show()
    [Windows.Forms.Application]::DoEvents()
    $bitmap = New-Object Drawing.Bitmap($form.Width,$form.Height)
    $form.DrawToBitmap($bitmap, (New-Object Drawing.Rectangle(0,0,$form.Width,$form.Height)))
    $bitmap.Save([IO.Path]::GetFullPath($PreviewPath), [Drawing.Imaging.ImageFormat]::Png)
    $bitmap.Dispose()
    $form.Dispose()
} else { [void]$form.ShowDialog() }
