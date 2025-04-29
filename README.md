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


5. Add nginx to the host machine (for example, for the SSL support) and add this directive to proxy the traffic to the internal nginx container.

```
location / {
    proxy_pass http://localhost:1080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```
**NOTE**: Instead of using the frontier nginx, you can modify the [docker-compose.yml](https://github.com/dm-nosov/boostress/blob/master/docker-compose.yml), nginx description, changing `"1080:80"` port binding to `"0.0.0.0:1080:80"` so you can run http://localhost:1080 on your host machine. In this case please keep the localhost hostname.

6. Replace 'localhost' with your desired external virtual host in docker-compose.yml
![image](https://github.com/user-attachments/assets/29e9d33a-aac1-4dd0-ac14-5ca14992ff3e)


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
  
