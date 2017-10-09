# gunicorn server configuration file
# extends and replaces api default configuration

port = 3000
bind = "127.0.0.1:" + port
workers = 3
