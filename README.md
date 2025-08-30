# Docker Container Port Viewer

A lightweight web interface to list running Docker containers and generate clickable links for each container’s exposed ports. Supports protocol, base URL, and override options per container.

---

## Features

- Displays container name, stack (if available), IP addresses, and exposed ports.
- Generates clickable links for each container port.
- Supports per-container protocol configuration (`http` / `https`).
- Optional base URL override for container links.
- Optional override to suppress dynamic port when using base URL (for reverse proxy setups).
- Stack links can optionally use a custom Portainer URL.

---

## How it works

- Container links: Built using HOST_IP by default. If viewer.baseurl is set, that is used instead. If viewer.override_dynamic_port=true, the container port is not appended.
- Stack links: Built using HOST_IP by default, optionally overridden with PORTAINER_URL.
- Protocols: viewer.protocol.<port> controls whether the link uses http or https.

---

## Environment Variables

| Variable       | Description                                                                                  |
|----------------|----------------------------------------------------------------------------------------------|
| `HOST_IP`      | Mandatory. The host IP used for generating container and stack links if no override is set. |
| `PORTAINER_URL`| Optional. Base URL for Portainer stack links. Overrides HOST_IP for stacks.                  |
| `PORTAINER_PORT`| Optional. Port for Portainer, default `9443` if not set.                                     |

---

## Supported Labels

These labels are applied to each container to control how links are generated:

| Label                                  | Description                                                                                 |
|---------------------------------------|---------------------------------------------------------------------------------------------|
| `viewer.protocol.<container_port>`     | Protocol for a given exposed port (`http` or `https`).                                      |
| `viewer.baseurl`                        | Optional. Overrides HOST_IP for container links. Can include hostname or full base URL.    |
| `viewer.override_dynamic_port`         | Optional. `true` → use base URL as-is, no port appended. `false` (default) → append port. |

**Example:**

```yaml
labels:
  # Set protocol for ports
  - viewer.protocol.8080=http
  - viewer.protocol.443=https

  # Override host IP with a base URL
  - viewer.baseurl=https://ldc01.sandpit.cba

  # If true, do not append the dynamic port to base URL
  - viewer.override_dynamic_port=true
