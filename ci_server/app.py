from flask import Flask, request, json
import requests
import docker
import os
import socket

app = Flask(__name__)

@app.route("/")
def hello():
    html = "<h3>Hello!</h3>"
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
