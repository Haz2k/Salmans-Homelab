# Salman’s HomeLab

This repository documents my self-hosted home server running on Ubuntu Server with Docker Compose and Portainer.

## System Overview
- OS: Ubuntu Server
- Container Management: Docker Compose + Portainer
- UID/GID: 1000:1000
- Storage: Separate data drive for media, cloud, and photos
- Design Goals:
  - Stability
  - Easy updates
  - Clear separation of services

## Stacks
- Media Stack
- Nextcloud Stack
- Immich Stack
- Security & Maintenance Stack

Each stack has its own folder containing Docker Compose configuration and documentation.
