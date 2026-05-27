# Nextcloud Stack

Provides private cloud storage, file synchronization, and collaborative tools running inside LXC container **CT102** (`192.168.0.132`).

## Services

* **Nextcloud Hub:** Core web interface, application suite, and file synchronization engine.
* **MariaDB:** Relational database backend optimized for Nextcloud data structures and user indexing.

## Notes

* Used as a secure, self-hosted alternative to OneDrive, Google Drive, and Dropbox.
* User data directories are mapped back to persistent directories on the host's 1TB storage drive.
* Full support for mobile applications, desktop sync clients, and WebDAV access layers.
* Managed entirely via Portainer.
