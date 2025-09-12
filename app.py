import os
import socket
from flask import Flask, render_template_string
import docker

app = Flask(__name__)
client = docker.from_env()

HOST_IP = os.environ.get("HOST_IP")
PORTAINER_PORT = os.environ.get("PORTAINER_PORT", "9443")
PORTAINER_URL = os.environ.get("PORTAINER_URL")

TEMPLATE = """
<!doctype html>
<html>
  <head>
    <title>Docker Container Port Viewer</title>
    <link rel="stylesheet" type="text/css" 
          href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css"/>
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <style>
      table.dataTable thead input {
        width: 100%;
        box-sizing: border-box;
      }
      th {
        vertical-align: bottom;
      }
      .description {
        font-size: 0.8em;
        font-weight: normal;
        color: #555;
      }
    </style>
  </head>
  <body>
    <h1>Docker Container Port Viewer</h1>
    {% if PORTAINER_URL %}
      <h2>Using Portainer URL: {{PORTAINER_URL}}:{{PORTAINER_PORT}}</h2>
    {% else %}
      <h2>Using HOST_IP: {{HOST_IP}}</h2>
    {% endif %}
    <table id="containers" class="display">
      <thead>
        <tr>
          <th>Name</th>
          <th>Image</th>
          <th>Stack</th>
          <th>
            Ports
            <div class="description">(container → host)</div>
          </th>
          <th>Links</th>
        </tr>
        <tr>
          <th><input type="text" placeholder="Search Name"></th>
          <th><input type="text" placeholder="Search Image"></th>
          <th><input type="text" placeholder="Search Stack"></th>
          <th><input type="text" placeholder="Search Ports"></th>
          <th><input type="text" placeholder="Search Links"></th>
        </tr>
      </thead>
      <tbody>
        {% for c in containers %}
        <tr>
          <td>{{c.name}}</td>
          <td>{{c.image}}</td>
          <td>
            {% if c.stack %}
              <a href="{{c.stack_url}}" target="_blank">{{c.stack}}</a>
            {% else %}
              -
            {% endif %}
          </td>
          <td>
            {% for p in c.ports %}
              {{p}}<br>
            {% endfor %}
          </td>
          <td>
            {% for l in c.links %}
              <a href="{{l}}" target="_blank">{{l}}</a><br>
            {% endfor %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <script>
      $(document).ready(function () {
        var table = $('#containers').DataTable({
          pageLength: 25,
          orderCellsTop: true,
          fixedHeader: true
        });

        // Apply the search
        $('#containers thead tr:eq(1) th input').on('keyup change', function () {
          table
            .column($(this).parent().index())
            .search(this.value)
            .draw();
        });
      });
    </script>
  </body>
</html>
"""

def build_link(base, proto, host, port, override_port):
    # If baseurl has http(s), respect it
    if base and (base.startswith("http://") or base.startswith("https://")):
        return base if override_port else f"{base}:{port}"
    # Otherwise prepend protocol if known
    url_host = base if base else host
    if proto:
        url_host = f"{proto}://{url_host}"
    if override_port:
        return url_host
    return f"{url_host}:{port}"

@app.route("/")
def index():
    containers = []
    for container in client.containers.list():
        name = container.name
        image = container.image.tags[0] if container.image.tags else container.image.short_id
        labels = container.labels
        stack = labels.get("com.docker.compose.project")

        stack_url = None
        if stack:
            base_host = PORTAINER_URL if PORTAINER_URL else HOST_IP
            stack_url = f"https://{base_host}:{PORTAINER_PORT}/#!/2/docker/stacks/{stack}"

        ports = []
        links = []
        if container.ports:
            for container_port, mappings in container.ports.items():
                if mappings:
                    for m in mappings:
                        host_port = m.get("HostPort")
                        proto = labels.get(f"viewer.protocol.{host_port}")
                        baseurl = labels.get("viewer.baseurl")
                        override = labels.get("viewer.override_dynamic_port", "false").lower() == "true"

                        ports.append(f"{container_port}->{host_port}")
                        link = build_link(baseurl, proto, HOST_IP, host_port, override)
                        links.append(link)

        containers.append({
            "name": name,
            "image": image,
            "stack": stack,
            "stack_url": stack_url,
            "ports": ports,
            "links": links
        })

    return render_template_string(
        TEMPLATE, containers=containers,
        HOST_IP=HOST_IP, PORTAINER_PORT=PORTAINER_PORT,
        PORTAINER_URL=PORTAINER_URL
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
