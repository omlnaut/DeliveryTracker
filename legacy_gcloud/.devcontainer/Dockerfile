FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:489.0.0-stable

env ENVIRONMENT=development

# Install OpenSSH client
RUN apt-get update && apt-get install -y openssh-client && rm -rf /var/lib/apt/lists/*
