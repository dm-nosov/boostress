# Boostress - Distributed Orders Fulfillment System

## Description and Stack
Boostress allows users to fulfill, process and monitor distributed orders from different providers unified by a specific integration API.

Technical stack:
- Python 3.10
- Django 5.1.1
- Celery 5.4.0
- Django Celery Beat
- Celery Results
- Redis DB as a message broker
- PostgreSQL DB
- Docker
- Docker Swarm
- Docker secrets
- Github actions
- Github releases
- Github packages

## Deployment Instructions

1. Clone this repository

`git clone https://github.com/dm-nosov/boostress.git`

2. Set the permissions. You need this to get logs from different containers to a single directory on the host machine.

```
cd boostress
chmod -R 777 logs
chmod -R 777 conf
```

3. Initialize the swarm

`docker swarm init`

4. Set docker secrets for SECRET_KEY, PostgreSQL user password and Django admin password.

```
echo "ENTER YOUR KEY" | docker secret create django_secret_key -
echo "ENTER YOUR KEY" | docker secret create postgres_password -
echo "ENTER YOUR KEY" | docker secret create admin_password -
echo "ENTER YOUR KEY" | docker secret create redis_password -
```


5. Host‑level Nginx (or any reverse proxy) can be used for SSL termination in front of the internal Nginx container.

   By default, the included Docker Compose setup provides an `nginx` service listening on port 1080, serving static assets from the shared `static_files` volume and proxying application traffic to the Django app.

   Update `ALLOWED_HOSTS` and `TRUSTED_ORIGINS` in `docker-compose.yml` to your desired domain in the `web` service configuration.

Use the following host nginx config for the related virtual host:

   ```nginx
    location / {
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {                                                                                                                                              
        proxy_pass http://127.0.0.1:1080/static/;                                                                                                                    
        proxy_set_header Host              $host;                                                                                                                    
        proxy_set_header X-Real-IP         $remote_addr;                                                                                                             
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;                                                                                               
        proxy_set_header X-Forwarded-Proto $scheme;                                                                                                                  
    } 
   
   ```


7. Deploy the stack to your swarm
   
`docker stack deploy -c docker-compose.yml example`

8. Run the admin `http://your_virtual_host/admin` and provide the admin credentials which you previously provided to Docker secrets.

## Implementation Notes

- Using the shared volumes, nginx automatically receives the static files which the app provides during the build process.
- DB migrations happen during a node startup which guarantees that everything is ready to a migration.
- Secrets are updated on each startup, so that just restart the containers to apply the new ones. 
- The app image is publicly available, you can use it instead of building yours.
- The image does not contain any secret information neither in code nor in the environment variables, so that the deployment code is safe to share to public.
- Docker swarm is flexible enough in case you want to scale from a single physical machine.
- The code encapsulates the API implementation inside the `provider_api` package, thus you can be easily modify the API without touching the business logic code.
- The code uses model managers and model methods to clearly explain the business logic (object responsibilities) instead of using ORM methods directly.
- The app integrates the default admin UI instead of creating custom views.
- The scheduler and results are available directly from the admin UI.

## External API (Order Creation)

Boostress exposes a simple JSON API endpoint for external systems to submit new orders.

**Endpoint:** `POST /home/api/orders/`

**Authentication:** Include your API key in the `X-API-KEY` HTTP header.

**Request JSON Payload:**
```json
{
  "link": "https://example.com/item/123",
  "platform": "PlatformName"
}
```

You can also supply optional fields in the same JSON payload:
- `name`: human-readable order name
- `link_type`: e.g. `"https"` or `"http"`
- `budget`: numeric budget value
- `deadline`: ISO 8601 datetime string (e.g. `"2025-12-31T23:59:59Z"`)
- `time_sensible`: boolean
- `total_followers`: integer
- `natural_time_cycles`: boolean

**Success Response:**
- **201 Created** if a new order was inserted, or **200 OK** if an existing order already existed.
```json
{ "id": 123, "created": true }
```

**Error Responses:**
- **403 Forbidden** for missing or invalid API key
- **400 Bad Request** for malformed JSON or missing required fields (`link`, `platform`)

**Example `curl` Invocation:**
```bash
curl -X POST https://your-domain/home/api/orders/ \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: your_api_key_here" \
     -d '{"link":"https://example.com/item/123","platform":"PlatformName"}'
```
