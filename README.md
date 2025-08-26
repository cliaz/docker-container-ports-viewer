
## Docker Container Ports Viewer

### Description
- Visualizes running Docker container ports and mappings.
- Simple web interface to view exposed ports.

### Features
- Lists all active containers and their port mappings.
- Shows clickable HTTP/HTTPS links if container labels are set.

### How to Use
- Run with `docker-compose up` or build and run the container.
- Access the web UI at [http://localhost:80](http://localhost:80).
- No configuration needed; works out of the box.

#### Show HTTP/HTTPS Links
Add labels to your container in `docker-compose.yml`:

```yaml
labels:
    - "viewer.protocol=http"
	- "viewer.port=8080"
```

Supported protocols: `http`, `https`.
The dashboard will display clickable links for labeled ports.
