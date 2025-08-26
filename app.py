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
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; }
        th { background-color: #f0f0f0; }
        a { text-decoration: none; color: #0066cc; }
        a:hover { text-decoration: underline; }
        tfoot input { width: 100%; box-sizing: border-box; }
        .filter-bar { margin-bottom: 10px; }
        .filter-bar select, .filter-bar button { margin-left: 10px; }
    </style>
    <!-- DataTables CSS/JS -->
    <link rel="stylesheet" type="text/css"
          href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css"/>
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
</head>
<body>
    <h2>Running Docker Containers</h2>
    <p><strong>Host IP:</strong> {{ host_ip }}</p>

    <div class="filter-bar">
        <label for="stackFilter"><strong>Filter by Stack:</strong></label>
        <select id="stackFilter">
            <option value="">All</option>
            {% for stack in stacks %}
            <option value="{{ stack }}">{{ stack }}</option>
            {% endfor %}
        </select>
        <button id="clearFilters">Clear Filters</button>
    </div>

    <table id="containers">
        <thead>
            <tr>
                <th>Name</th>
                <th>Stack</th>
                <th>Image</th>
                <th>IP Address</th>
                <th>Ports</th>
                <th>Links</th>
            </tr>
        </thead>
        <tfoot>
            <tr>
                <th>Name</th>
                <th>Stack</th>
                <th>Image</th>
                <th>IP Address</th>
                <th>Ports</th>
                <th>Links</th>
            </tr>
        </tfoot>
        <tbody>
        {% for container in containers %}
        <tr>
            <td>{{ container.name }}</td>
            <td>{{ container.labels.get('com.docker.compose.project', 'N/A') }}</td>
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

    <script>
    $(document).ready(function() {
        // Add search inputs to footer
        $('#containers tfoot th').each(function() {
            var title = $(this).text();
            $(this).html('<input type="text" placeholder="Search '+title+'" />');
        });

        var table = $('#containers').DataTable();

        // Apply column-specific search
        table.columns().every(function() {
            var that = this;
            $('input', this.footer()).on('keyup change', function() {
                if (that.search() !== this.value) {
                    that.search(this.value).draw();
                }
            });
        });

        // Stack filter dropdown
        $('#stackFilter').on('change', function() {
            var val = $(this).val();
            table.column(1).search(val ? '^'+val+'$' : '', true, false).draw();
        });

        // Clear filters button
        $('#clearFilters').on('click', function() {
            // Clear dropdown
            $('#stackFilter').val('');
            // Clear global search
            table.search('').draw();
            // Clear each column search
            table.columns().search('').draw();
            // Clear footer inputs
            $('#containers tfoot input').val('');
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
    stacks = sorted(set(c.labels.get("com.docker.compose.project", "N/A") for c in containers))
    return render_template_string(TEMPLATE, containers=containers, host_ip=host_ip, stacks=stacks)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
