import os
import docker
from flask import Flask, render_template_string

app = Flask(__name__)
client = docker.DockerClient(base_url="unix://var/run/docker.sock")

HOST_IP = os.environ.get("HOST_IP")
PORTAINER_PORT = os.environ.get("PORTAINER_PORT", "9443")
PORTAINER_URL = os.environ.get("PORTAINER_URL")  # optional override

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Docker Container Viewer</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h2>Docker Containers</h2>
    <table id="containerTable" class="display">
        <thead>
            <tr>
                <th>Name</th>
                <th>Stack</th>
                <th>IP</th>
                <th>Ports</th>
            </tr>
        </thead>
        <tbody>
            {% for container in containers %}
            <tr>
                <td>
                    {% if container.link %}
                        <a href="{{ container.link }}" target="_blank">{{ container.name }}</a>
                    {% else %}
                        {{ container.name }}
                    {% endif %}
                </td>
                <td>
                    {% if container.stack_link %}
                        <a href="{{ container.stack_link }}" target="_blank">{{ container.stack }}</a>
                    {% else %}
                        {{ container.stack }}
                    {% endif %}
                </td>
                <td>{{ container.ip }}</td>
                <td>{{ container.ports }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready(function() {
            $('#containerTable').DataTable({
                pageLength: 25,
                initComplete: function () {
                    this.api().columns().every(function () {
                        var column = this;
                        var input = $('<input type="text" placeholder="Search" />')
                            .appendTo($(column.header()))
                            .on('keyup change clear', function () {
                                if (column.search() !== this.value) {
                                    column.search(this.value).draw();
                                }
                            });
                    });
                }
            });
        });
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    containers = []
    for c in client.containers.list():
        info = c.attrs
        name = c.name
        ip = None
        stack = info["Config"]["Labels"].get("com.docker.compose.project", "")
        stack_link = None

        # Determine stack link (optional)
        if stack:
            base_url = PORTAINER_URL if PORTAINER_URL else f"https://{HOST_IP}:{PORTAINER_PORT}"
            stack_link = f"{base_url}/#!/2/docker/stacks/{stack}"

        # Get container IP
        if info["NetworkSettings"]["Networks"]:
            ip = list(info["NetworkSettings"]["Networks"].values())[0].get("IPAddress", "")

        # Determine exposed ports
        ports = []
        link = None
        for port, mappings in (info["NetworkSettings"]["Ports"] or {}).items():
            if mappings:
                for m in mappings:
                    container_port = port.split("/")[0]
                    protocol_label = info["Config"]["Labels"].get(f"viewer.protocol.{m['HostPort']}", "http")

                    # Handle baseurl logic
                    baseurl = info["Config"]["Labels"].get("viewer.baseurl")
                    override = info["Config"]["Labels"].get("viewer.override_dynamic_port", "false").lower() == "true"

                    if baseurl:
                        if override:
                            link = baseurl  # absolute override
                        else:
                            link = f"{baseurl}:{m['HostPort']}"
                    else:
                        link = f"{protocol_label}://{HOST_IP}:{m['HostPort']}"

                    ports.append(f"{m['HostPort']}->{container_port}/{port.split('/')[1]}")

        containers.append({
            "name": name,
            "stack": stack,
            "stack_link": stack_link,
            "ip": ip,
            "ports": ", ".join(ports),
            "link": link
        })

    return render_template_string(TEMPLATE, containers=containers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
