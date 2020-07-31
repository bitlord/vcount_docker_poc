# vcount_docker_poc
# This is a python + flask docker PoC, it's full of known and unknown issues (poor design decisions and bugs)

# Install Fresh Ubuntu 18.04 server VM

# Install Docker ( https://docs.docker.com/engine/install/ubuntu/ )

# Install nginx on a VM (this will be used as simple HTTP connection load balancer)
apt install nginx

# Create new bridged network (it allows connecting between hosts using names unlike default bridge network)
docker network create --subnet 10.0.0.0/24 --driver bridge webappnet

# New bridge network is now configured
root@ubuntu:~# docker network ls
NETWORK ID          NAME                DRIVER              SCOPE
87dc6b0f6f0f        bridge              bridge              local
46ee65667e56        host                host                local
c3f91647acd6        none                null                local
47ce504c2eb8        webappnet           bridge              local


# Get redis docker image 
docker pull redis

# Now we have a local copy of the image
root@ubuntu:~# docker image ls
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
redis               latest              50541622f4f1        7 days ago          104MB


# Make permanent storage on docker host 
mkdir -p /docker/data/redis

# Run redis container (bind volume /docker/data/redis to /data inside "redisdb" container)
docker run -v /docker/data/redis:/data --name redisdb --network webappnet -d redis redis-server --appendonly yes

# Check currently running containers, or redis instance is now running
root@ubuntu:~# docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
247e9b489daf        redis               "docker-entrypoint.s…"   18 seconds ago      Up 15 seconds       6379/tcp            redisdb


# Build application docker image "vcount" (in the app directory where app.py, Dockerfile and requirements.txt is)
root@ubuntu:/home/ubuntu/vcount# docker build -t vcount .

# Now our docker image is ready
root@ubuntu:~/vcount# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
vcount              latest              966c771ef0d8        6 seconds ago       394MB
ubuntu              latest              1e4467b07108        5 days ago          73.9MB
redis               latest              50541622f4f1        7 days ago          104MB


# Run instance detached instance web0 and map port 5000 inside container to port 8080 on the docker host, use "webappnet" docker network, instance will be run using "vcount" image we prepared earlier
docker run --name web0 -p 8080:5000 --network webappnet -d vcount

# To run multiple instances (for example 4 you can automate this by)
for i in $(seq 0 3); do docker run --name web"${i}" -p 808"${i}":5000 --network webappnet -d vcount; done

# We can see all your containers running
root@ubuntu:~/vcount# docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
ee846ca90153        vcount              "/bin/sh -c /opt/vco…"   3 minutes ago       Up 3 minutes        0.0.0.0:8083->5000/tcp   web3
b73d6aa8d400        vcount              "/bin/sh -c /opt/vco…"   3 minutes ago       Up 3 minutes        0.0.0.0:8082->5000/tcp   web2
62b484420c74        vcount              "/bin/sh -c /opt/vco…"   3 minutes ago       Up 3 minutes        0.0.0.0:8081->5000/tcp   web1
c1d81cc35699        vcount              "/bin/sh -c /opt/vco…"   3 minutes ago       Up 3 minutes        0.0.0.0:8080->5000/tcp   web0
f20215b5eae2        redis               "docker-entrypoint.s…"   3 minutes ago       Up 3 minutes        6379/tcp                 redisdb


# also exposed port on the docker host
root@ubuntu:~/vcount# ss -tnpl | grep 808
LISTEN   0         128                       *:8080                   *:*        users:(("docker-proxy",pid=14521,fd=4))                                        
LISTEN   0         128                       *:8081                   *:*        users:(("docker-proxy",pid=14648,fd=4))                                        
LISTEN   0         128                       *:8082                   *:*        users:(("docker-proxy",pid=14770,fd=4))                                        
LISTEN   0         128                       *:8083                   *:*        users:(("docker-proxy",pid=14889,fd=4)) 

# Nginx configuration
# Remove default nginx website
rm /etc/nginx/sites-enabled/default

# Adjust nginx config by adding multiple backends for http load balacing /etc/nginx.conf (if not selected default policy is round-robin)
--- /etc/nginx/nginx.conf_orig	2020-07-29 18:54:43.838640032 +0000
+++ /etc/nginx/nginx.conf	2020-07-29 18:57:47.406424226 +0000
@@ -9,7 +9,20 @@
 }
 
 http {
+	upstream vcount {
+		server 127.0.0.1:8080;
+		server 127.0.0.1:8081;
+		server 127.0.0.1:8082;
+		server 127.0.0.1:8083;
+	}
 
+	server {
+		listen 80;
+
+	location / {
+		proxy_pass http://vcount;
+		}
+	}
 	##
 	# Basic Settings
 	##


# Reload nginx config
systemctl reload nginx

# Test your connection
root@ubuntu:~/vcount# for i in $(seq 15); do curl  http://localhost:80; done 
Hello visitor 1, this is instance ee846ca90153
Hello visitor b'1', this is instance c1d81cc35699
Hello visitor b'2', this is instance 62b484420c74
Hello visitor b'3', this is instance b73d6aa8d400
Hello visitor b'4', this is instance ee846ca90153
Hello visitor b'5', this is instance c1d81cc35699
Hello visitor b'6', this is instance 62b484420c74
Hello visitor b'7', this is instance b73d6aa8d400
Hello visitor b'8', this is instance ee846ca90153
Hello visitor b'9', this is instance c1d81cc35699
Hello visitor b'10', this is instance 62b484420c74
Hello visitor b'11', this is instance b73d6aa8d400
Hello visitor b'12', this is instance ee846ca90153
Hello visitor b'13', this is instance c1d81cc35699
Hello visitor b'14', this is instance 62b484420c74

# You can check statistics on your responses for example:
for i in $(seq 145); do curl  http://localhost:80; done | awk '{ print $7 }' | sort | uniq -c
...
     36 62b484420c74
     37 b73d6aa8d400
     36 c1d81cc35699
     36 ee846ca90153

# You can also see requests on each indivudual instance of the application:
root@ubuntu:~/vcount# docker logs web0 
 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
10.0.0.1 - - [29/Jul/2020 19:07:09] "GET / HTTP/1.0" 200 -
10.0.0.1 - - [29/Jul/2020 19:07:09] "GET / HTTP/1.0" 200 -
10.0.0.1 - - [29/Jul/2020 19:07:09] "GET / HTTP/1.0" 200 -
10.0.0.1 - - [29/Jul/2020 19:07:10] "GET / HTTP/1.0" 200 -
10.0.0.1 - - [29/Jul/2020 19:08:39] "GET / HTTP/1.0" 200 -
10.0.0.1 - - [29/Jul/2020 19:08:39] "GET / HTTP/1.0" 200 -
10.0.0.1 - - [29/Jul/2020 19:08:39] "GET / HTTP/1.0" 200 -
...


