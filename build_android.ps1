# build_android.ps1
# Compiles Vite production bundle and syncs static assets into android_dist folder

$DistFolder = "android_dist"

Write-Host "Building production web bundle using Vite..."
npm run build

# Remove old android_dist folder if exists
if (Test-Path $DistFolder) {
    Remove-Item -Recurse -Force $DistFolder
}

# Create new android_dist folder
New-Item -ItemType Directory -Force -Path $DistFolder

# Copy compiled dist bundle to android_dist
if (Test-Path "dist") {
    Copy-Item -Recurse -Path "dist\*" -Destination $DistFolder
}

Write-Host "Frontend build completed successfully in '$DistFolder' directory!"
