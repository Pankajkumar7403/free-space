install uv package manager in your system.
cd backend
create a virtual enviroment 
uv venv
activate it using -> .venv/scripts/activate
then uv install


$apps = @("users","posts","feed","comments","likes","notifications","media","common",)

foreach ($app in $apps) {
    $basePath = "backend/apps/$app"
    
    New-Item -ItemType File -Path "$basePath/serializers.py" -Force
    New-Item -ItemType File -Path "$basePath/views.py" -Force
    New-Item -ItemType File -Path "$basePath/urls.py" -Force
}

Write-Host "Files created successfully!"
