#!/bin/bash

# Récupérer le répertoire racine du script
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

container_name="converter"
container_version="1.0"

# Naviguer vers le répertoire racine
cd "$ROOT_DIR"

# Liste des répertoires contenant les fichiers Dockerfile
APP_DIRS=$(find . -mindepth 1 -maxdepth 1 -type d)

# Construire les images Docker pour chaque répertoire
for dir in $APP_DIRS; do
    # Extraire le nom du répertoire (nom de l'application)
    app_name=$(basename "$dir")
    
    # Vérifier si un Dockerfile existe dans le répertoire
    if [ -f "$dir/Dockerfile" ]; then
        echo "Building image for $app_name..."
        # Construire l'image Docker
        docker build -t "$app_name"-"$container_name":"$container_version" "$dir"
        echo "Image for $app_name built successfully."
    else
        echo "No Dockerfile found in $dir."
    fi
done

echo "All Docker images built successfully."
