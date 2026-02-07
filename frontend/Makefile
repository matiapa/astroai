# Makefile for AstroIA Frontend

.PHONY: build deploy prod clean

# Build for production using the production environment file
build:
	flutter build web --dart-define-from-file=.env.prod

# Deploy to Firebase Hosting
deploy:
	firebase deploy --only hosting

# Build and deploy in one step
prod: build deploy

# Clean the project
clean:
	flutter clean
