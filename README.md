### sd2018b-exam2

**Universidad Icesi**
**Curso:** Sistemas Distribuidos
**Profesor:** Daniel Barragán C.
**Tema:** Construcción de artefactos para entrega continua
**Email:** daniel.barragan at correo.icesi.edu.co
**Estudiante:** Julián David González Jiménez
**ódigo:** A00315288
**URL Git:** https://github.com/juliand7gj/sd2018b-exam2

### Objetivos
* Realizar de forma autómatica la generación de artefactos para entrega continua
* Emplear librerías de lenguajes de programación para la realización de tareas específicas
* Diagnosticar y ejecutar de forma autónoma las acciones necesarias para corregir fallos en
la infraestructura

### Tecnlogías sugeridas para el desarrollo del examen
* Docker
* Box del sistema operativo CentOS7
* Repositorio Github
* Python3
* Librerias Python3: Flask, Connexion, Docker
* Ngrok

### Descripción
Para la realización de la actividad tener en cuenta lo siguiente:

* Crear un Fork del repositorio sd2018b-exam2 y adicionar las fuentes de un microservicio
de su elección.
* Alojar en su fork un archivo Dockerfile para la construcción de un artefacto tipo Docker a
partir de las fuentes de su microservicio.

Deberá probar y desplegar los siguientes componentes:

* Despliegue de un **registry** local de Docker para el almacenamiento de imágenes de Docker. Usar la imagen de DockerHub: https://hub.docker.com/_/registry/ . Probar que es posible descarga la imagen generada desde un equipo perteneciente a la red.

* Realizar un método en Python3.6 o superior que reciba como entrada el nombre de un servicio,
la version y el tipo (Docker ó AMI) y en su lógica realice la construcción de una imagen de Docker cuyo nombre deberá ser **service_name:version** y deberá ser publicada en el **registry** local creado en el punto anterior.

* Realizar una integración con GitHub para que al momento de realizar un **merge** a la rama
**develop**, se inicie la construcción de un artefacto tipo Docker a partir del Dockerfile y las fuentes del repositorio. Idee una estrategia para el envío del **service_name** y la **versión** a través del **webhook** de GitHub. La imagen generada deberá ser publicada en el **registry** local creado.

* Si la construcción es exitosa/fallida debera actualizarse un **badge** que contenga la palabra build y la versión del artefacto creado mas recientemente (**opcional**).

* En lugar de una máquina virtual de CentOS7 para alojar el CI server,  emplear la imagen de Docker de Docker hub para el ejecución de la API (webhook listener) y la generación del artefacto: https://hub.Docker.com/_/Docker/ (**opcional**).

![][14]
**Figura 1**. Diagrama de Entrega Continua

### Actividades
1. Documento README.md en formato markdown:  
  * Formato markdown (5%)
  * Nombre y código del estudiante (5%)
  * Ortografía y redacción (5%)
2. Documentación del procedimiento para el montaje del registry (10%). Evidencias del funcionamiento (5%).
3. Documentación e implementación del método para la generación del artefacto. Incluya el código fuente en el informe. Incluya comentarios en el código donde explique cada paso realizado (20%). Evidencias del funcionamiento (5%).
4. Documentación e integración de un repositorio de GitHub junto con la generación del artefacto tipo Docker (20%). Evidencias del funcionamiento (5%).
5. El informe debe publicarse en un repositorio de github el cual debe ser un fork de https://github.com/ICESI-Training/sd2018b-exam2 y para la entrega deberá hacer un Pull Request (PR) al upstream (10%). Tenga en cuenta que el repositorio debe contener todos los archivos necesarios para el aprovisionamiento
7. Documente algunos de los problemas encontrados y las acciones efectuadas para su solución al aprovisionar la infraestructura y aplicaciones (10%)

### Introducción

La rama actual contiene dos elementos clave para implementar la infraestructura. El primero es el docker-compose.yml. Este archivo contiene el aprovisionamiento requerido para cada CT. La segunda es la carpeta ci_server que contiene el script Dockerfile y python para crear la imagen de CI Server Docker.

### Desarrollo

## docker-compose.yml

```
version: "3"
services:
  ci_server:
    build: ./ci_server
    ports:
      - 8000:8000
    volumes:
      - //var/run/docker.sock:/var/run/docker.sock
  ngrok:
    image: wernight/ngrok
    ports:
      - 0.0.0.0:4040:4040
    links:
      - ci_server
    environment:
      NGROK_PORT: ci_server:8000
  registry:
    restart: always
    image: registry:2
    ports:
      - 5000:5000
    environment:
      REGISTRY_HTTP_ADDR: 0.0.0.0:5000
      REGISTRY_HTTP_TLS_CERTIFICATE: ./certs/domain.crt
      REGISTRY_HTTP_TLS_KEY: ./certs/domain.key
    volumes:
      - ./certs:/certs
```

* ci_server: aquí se deben desplegar el Dockerfile que es para construir la imagen y el archivo python. Cuando ya se despliega todo, al hacer un PR, el repositorio verifica que se haga bien el merge y las imagenes se agregaran o no al la rama develop. A continuación el Dockerfile que ejecutara el el archivo python:

```
# Use an official Python runtime as a parent image
FROM python:3.6-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV NAME World

# Run app.py when the container launches
CMD ["python", "app.py"]
```

A continuació se muestra el archivo app.py. En el se hace uso de librerías docker, flask, entre otras.

```
from flask import Flask, request, json
import requests
import docker
import os
import socket

app = Flask(__name__)

@app.route("/")
def inicio():
    html = "<h3>Funciona</h3>"
    return html

@app.route("/jgonzalez/exam2/api/v1/images", methods=['POST'])
def build_image():
    content=request.get_data()
    contentString=str(content, 'utf-8')
    jsonFile=json.loads(contentString)
    merged=jsonFile["pull_request"]["merged"]
    if merged:
        sha=jsonFile["pull_request"]["head"]["sha"]
        imageUrl="https://raw.githubusercontent.com/juliand7gj/sd2018b-exam2/"+sha+"/image.json"
        imageResponse=requests.get(imageUrl)
        image=json.loads(imageResponse.content)

        dockerfileUrl="https://raw.githubusercontent.com/juliand7gj/sd2018b-exam2/"+sha+"/Dockerfile"
        dockerfileResponse=requests.get(dockerfileUrl)
        file = open("Dockerfile","w")
        file.write(str(dockerfileResponse.content, 'utf-8'))
        file.close()
        tag="registry:5000/"+image["service_name"]+":"+image["version"]

        client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        client.images.build(path="./", tag=tag)
        client.images.push(tag)
        client.images.remove(image=tag, force=True)
        return tag
    else:
        return "Pull request is not merged"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
```

* registry: este servicio hace referencia al registro local privado. Hace uso de la imagen del registry de docker y se le proporciona al al puerto 5000. Se necesitan los certificados SSL para la seguridad del servidor. Los certificados se guardan en ./certs.

Primero se crea un directorio donde se van a almacenar los certificados. Para generar los certificados se usa:

```
 openssl req -newkey rsa:4096 -nodes -sha256 -keyout `pwd`/certs/domain.key -x509 -days 365 -out `pwd`/certs/domain.crt
```

* ngrok: este servicio utiliza la imagen de Docker wernight/ngrok. Esta en el puerto 4040 y trabaja con ci_server en su puerto 8000.

### Pruebas

Primero se corre el siguiente comando en el archivo del repositorio, que sirve para iniciar la compilación de los servicios:

```
docker-compose up --build
```

![][1]
**Figura 2**. Creación de los contenedores Docker

![][2]
**Figura 3**. Creación de los contenedores Docker

Con el siguiente comando se pueden apreciar los servicios corriendo:

```
docker ps
```

![][12]
**Figura 4**. Servicios corriendo

Se abre Ngrok en el navegador en la dirección 0.0.0.0:4040

![][3]
**Figura 5**. NGROK

![][6]
**Figura 6**. Estado del NGROK

![][4]
**Figura 7**. ci_server

Ya estando todo activo, debemos ir al repositorio y añadir un webhook. En el se debe poner la URL que esta en Ngrok.

![][7]
**Figura 8**. Webhook

![][8]
**Figura 9**. webhook

Ahora ya se puede probar haciendo PR de la rama jgonzalez/develop a la rama develop:

![][9]
**Figura 10**. Pull Request

![][10]
**Figura 11**. Webhook trabajando

Al final se debe hacer merge sin ningun problema.

![][11]
**Figura 12**. Merge

### Dificultades

La mayor dificultad que tuve en la realización de este parcial fue que al activar los servicios, habia un problema de puertos, servía el Ngrok pero no servía el CI_Server. Lo logré corregir gracias a una ardua investigación sobre la causa del problema. Otra dificultad fue la falta de conocimiento sobre algunas tecnologias necesarias para la realización de este, pero lo solucione de la misma forma que el problema anterior. 

### Referencias
* https://hub.docker.com/_/registry/
* https://hub.docker.com/_/docker/
* https://docker-py.readthedocs.io/en/stable/index.html
* https://developer.github.com/v3/guides/building-a-ci-server/
* http://flask.pocoo.org/
* https://connexion.readthedocs.io/en/latest/

[14]: images/14.png
[1]: images/1.png
[2]: images/2.png
[3]: images/3.png
[4]: images/4.png
[5]: images/5.png
[6]: images/6.png
[7]: images/7.png
[8]: images/8.png
[9]: images/9.png
[10]: images/10.png
[11]: images/11.png
[12]: images/12.png
[13]: images/13.png
