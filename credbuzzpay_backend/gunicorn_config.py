# Gunicorn Configuration File for CredBuzz Backend Production
# Server IP: 80.225.194.105

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'credbuzz_backend'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if you're terminating SSL at gunicorn level - usually done at nginx)
# keyfile = '/path/to/ssl/key.pem'
# certfile = '/path/to/ssl/cert.pem'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Reload workers when code changes (disable in production)
reload = os.getenv('GUNICORN_RELOAD', 'False').lower() in ('true', '1', 'yes')

# Forwarded allow ips (for nginx proxy)
forwarded_allow_ips = '*'
