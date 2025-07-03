#!/bin/bash

echo "Creating AWS Lambda deployment package with dependencies"

# Create a temporary directory
TempDir="temp"
ZipFileName="lambda-deployment-package.zip"
mkdir -p $TempDir

# Copy all files to the temporary directory, excluding the following folders
rsync -av --progress . $TempDir --exclude ".git" --exclude ".github" --exclude ".vscode" --exclude "temp" --exclude "__pycache__" --exclude ".venv" --exclude "docs" --exclude "README.md" --exclude "swagger.yaml" --exclude "tests.py" --exclude "scripts" --exclude "$ZipFileName" --exclude "requirements.txt" --exclude "images"

# Copy the dependencies to the temporary directory
echo "Copying the dependencies to the $TempDir directory"
DependenciesPath=".venv/lib/python3.*/site-packages/*"
rsync -av --progress $DependenciesPath $TempDir --exclude "__pycache__"

# Install pydantic for x86_64 architecture
echo "Installing pydantic for x86_64 architecture"
pip install pydantic --platform manylinux2014_x86_64 --target=$TempDir --implementation cp --only-binary=:all: --upgrade --python-version 3.12

# Install psycopg2-binary for x86_64 architecture
echo "Installing psycopg2-binary for x86_64 architecture"
pip install psycopg2-binary --platform manylinux2014_x86_64 --target=$TempDir --implementation cp --only-binary=:all: --upgrade --python-version 3.12

# Zip the contents of the temporary directory (at root)
echo "Zipping the contents of the $TempDir directory"
# zip -r ./$ZipFileName ./$TempDir/*
cd $TempDir
zip -r ../$ZipFileName *
cd ..

# Delete the temporary directory
rm -rf $TempDir

echo "AWS Lambda deployment package created"