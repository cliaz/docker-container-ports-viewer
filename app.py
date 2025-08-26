from flask import Flask, render_template_string
import docker
import os

app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

def get_host_ip():
    return os.environ.get('HOST_IP', 'Unknown')

def get_portainer_port():
    return os.environ.get('PORTAINER_PORT', '9443')  # default HTTPS port

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Docker Container Info</title>
    <meta http-equiv="refresh" content="30">
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { padding: 8px; text-align: left; vertical-align: top; }
        th { background-color: #f0f0f0; }
        a { text-decoration: none; color: #0066cc; }
        a:hover { text-decoration: underline; }
        thead input { width: 100%; box-sizing: border-box; }
    </style>
</head>
<body>
    <h2>Running Docker Containers</h2>
    <p><strong>Host IP:</strong> {{ host_ip }}</p>
    <table id="containers" class="display">
        <thead>
            <tr>
                <th>Name</th>
                <th>Stack</th>
                <th>Image</th>
                <th>IP Address</th>
                <th>Ports</th>
                <th>Links</th>
            </tr>
            <tr>
                <th><input type="text" placeholder="Search Name"></th>
                <th><input type="text" placeholder="Search Stack"></th>
                <th><input type="text" placeholder="Search Image"></th>
                <th><input type="text" placeholder="Search IP"></th>
                <th><input type="text" placeholder="Search Ports"></th>
                <th><input type="text" placeholder="Search Links"></th>
            </tr>
        </thead>
        <tbody>
        {% for container in containers %}
        <tr>
            <td>{{ container.name }}</td>
            <td>
                {% set stack_name = container.labels.get('com.docker.compose.project') %}
                {% if stack_name %}
                    <a href="https://{{ host_ip }}:{{ portainer_port }}/#!/2/docker/stacks/{{ stack_name }}" target="_blank">{{ stack_name }}</a>
                {% else %}
                    None
                {% endif %}
            </td>
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
                                    {% set port_num = port.split('/')[0] %}
                                    {% set protocol = container.labels.get('viewer.protocol.' ~ port_num, 'http') %}
                                    <a href="{{ protocol }}://{{ host_ip }}:{{ m.HostPort }}" target="_blank">{{ protocol }}://{{ host_ip }}:{{ m.HostPort }}</a><br>
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
        </tbody>
    </table>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready(function() {
            var savedLength = localStorage.getItem('pageLength') ? parseInt(localStorage.getItem('pageLength')) : 25;
            var savedSearch = localStorage.getItem('tableSearch') ? JSON.parse(localStorage.getItem('tableSearch')) : [];
            var savedOrder = localStorage.getItem('tableOrder') ? JSON.parse(localStorage.getItem('tableOrder')) : [[0, 'asc']];

            var table = $('#containers').DataTable({
                pageLength: savedLength,
                order: savedOrder,
                initComplete: function() {
                    var api = this.api();
                    api.columns().every(function(i) {
                        var input = $('#containers thead tr:eq(1) th').eq(i).find('input');
                        if (savedSearch[i]) {
                            input.val(savedSearch[i]);
                            this.search(savedSearch[i]);
                        }
                        input.on('keyup change', () => {
                            api.column(i).search(input.val()).draw();
                            var filters = [];
                            api.columns().every(function(j) {
                                filters[j] = api.column(j).search();
                            });
                            localStorage.setItem('tableSearch', JSON.stringify(filters));
                        });
                    });
                }
            });

            // Save page length
            table.on('length.dt', function(e, settings, len) {
                localStorage.setItem('pageLength', len);
            });

            // Save sort order
            table.on('order.dt', function() {
                localStorage.setItem('tableOrder', JSON.stringify(table.order()));
            });
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    containers = client.containers.list()
    host_ip = get_host_ip()
    portainer_port = get_portainer_port()
    return render_template_string(TEMPLATE, containers=containers, host_ip=host_ip, portainer_port=portainer_port)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
