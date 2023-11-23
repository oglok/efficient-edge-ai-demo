WARNING: This demo sets up a *privileged* namespace called efficient-edge-demo in order to access /dev/video0 (usually a webcam or MIPI camera) on the host. Please use privileged namespaces carefully and keep in mind this is not best practice.

This is designed to run on a 16GiB Orin NX unit, but may be able to fit on an 8GiB version as well.

-- INSTALL PROCESS --
To create the namespace, deployments, services, and route apply the demo.yaml file
```oc apply -f demo.yaml```

The route will be named: microshift-web-demo.local

MicroShift offers mDNS resolution for routes that end with the .local domain. If a machine, equipped with an mDNS daemon like Avahi or Bonjour, attempts to access the webserver from the same local network, it will automatically resolve the route's IP. This enables seamless access to the webserver.

If that's not the case, on your host system, add an entry to your hosts file (/etc/hosts for Mac/Linux or C:\Windows\System32\drivers\etc\hosts for Windows) to point the route name above to the IP of your Jetson.

Visit the web page in a browser to use the demo app.
