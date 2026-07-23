# build_android.ps1
# This script copies only the frontend files into the android_dist folder
# so that the APK does not include the heavy python backend and .git files.

$DistFolder = "android_dist"

# Remove old dist folder if exists
if (Test-Path $DistFolder) {
    Remove-Item -Recurse -Force $DistFolder
}

# Create new dist folder
New-Item -ItemType Directory -Force -Path $DistFolder

# Folders to copy
$Folders = @("css", "js", "assets")
foreach ($folder in $Folders) {
    if (Test-Path $folder) {
        Copy-Item -Recurse -Path $folder -Destination "$DistFolder\$folder"
    }
}

# Copy HTML files
Copy-Item -Path "*.html" -Destination $DistFolder

# Copy manifest/icons if they exist
if (Test-Path "manifest.json") { Copy-Item "manifest.json" -Destination $DistFolder }
if (Test-Path "favicon.ico") { Copy-Item "favicon.ico" -Destination $DistFolder }
if (Test-Path "apple-touch-icon.png") { Copy-Item "apple-touch-icon.png" -Destination $DistFolder }

Write-Host "Frontend build completed successfully in '$DistFolder' directory!"
