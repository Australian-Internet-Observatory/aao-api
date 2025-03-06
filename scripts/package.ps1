echo "Creating AWS Lambda deployment package with dependencies"

# Create a temporary directory
$TempDir = "temp"
$ZipFileName = "lambda-deployment-package.zip"
New-Item -ItemType Directory -Path $TempDir -Force

# Copy all files to the temporary directory, excluding the following
# folders: .git, .vscode, temp, __pycache__, .venv
$ExcludedDirs = @(".git", ".github", ".vscode", "temp", "__pycache__", ".venv", "docs", "package.ps1", "README.md", "swagger.yaml", "tests.py", "scripts", $ZipFileName)
Copy-Item .\* -Destination $TempDir -Recurse -Exclude $ExcludedDirs -Force

# Copy the dependencies to the temporary directory
echo "Copying the dependencies to the $TempDir directory"
$ExcludedDepDirs = @("__pycache__")
$DependenciesPath = @(".venv\Lib\site-packages\*")
Copy-Item $DependenciesPath -Destination $TempDir -Recurse -Exclude $ExcludedDepDirs -Force

# Zip the contents of the temporary directory (at root)
echo "Zipping the contents of the $TempDir directory"
Compress-Archive -Path $TempDir\* -DestinationPath $ZipFileName -Force

# Delete the temporary directory
Remove-Item -Recurse -Force $TempDir

echo "AWS Lambda deployment package created"