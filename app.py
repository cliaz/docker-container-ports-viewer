from flask import Flask, render_template_string
import docker
import os

app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

def get_host_ip():
    return os.environ.get('HOST_IP', 'Unknown')

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Docker Container Info</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; }
        th { background-color: #f0f0f0; }
        a { text-decoration: none; color: #0066cc; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h2>Running Docker Containers</h2>
    <p><strong>Host IP:</strong> {{ host_ip }}</p>
    <table>
        <tr>
            <th>Name</th>
            <th>Image</th>
            <th>IP Address</th>
            <th>Ports</th>
            <th>Links</th>
        </tr>
        {% for container in containers %}
        <tr>
            <td>{{ container.name }}</td>
            <td>{{ container.image.tags[0] if container.image.tags else container.image.short_id }}</td>
            <td>
                {% for net_name, net_info in container.attrs.NetworkSettings.Networks.items() %}
                    {{ net_name }}: {{ net_info.IPAddress }}<br>
                {% endfor %}
            </td>
            <td>
                {% if container.ports %}
                    {% for port, mappings in container.ports.items() %}
                        {{ port }}{% if mappings %} → {% for m in mappings %}{{ m['HostIp'] }}:{{ m['HostPort'] }} {% endfor %}{% endif %}<br>
                    {% endfor %}
                {% else %}
                    None
                {% endif %}
            </td>
            <td>
                {% if host_ip != 'Unknown' and container.ports %}
                    {% for port, mappings in container.ports.items() %}
                        {% if mappings %}
                            {% for m in mappings %}
                                {% if m.HostPort %}
                                    {% set label_key = 'viewer.protocol.' ~ m.HostPort %}
                                    {% set protocol = container.labels[label_key] if container.labels and label_key in container.labels else 'http' %}
                                    <a href="{{ protocol }}://{{ host_ip }}:{{ m.HostPort }}" target="_blank">
                                        {{ protocol }}://{{ host_ip }}:{{ m.HostPort }}
                                    </a><br>
                                {% endif %}
                            {% endfor %}
                        {% endif %}
                    {% endfor %}
                {% else %}
                    None
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def index():
    containers = client.containers.list()
    host_ip = get_host_ip()
    return render_template_string(TEMPLATE, containers=containers, host_ip=host_ip)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
