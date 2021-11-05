# HTTP Plugin for Podder Task Foundation

With this plugin, you can make your process as an HTTP API only with one command !

### How to install to your project

```bash
% podder plugin install podder-task-foundation-commands-http
```

### How to run 

```bash
% poetry run python manage.py http
```

### Available APIs

#### Get all available process names

GET http://localhost:5000/api/processes

#### Execute process

POST http://localhost:5000/api/processes/{your process name}

You can pass your input files as `multipart/form-data` body data.

