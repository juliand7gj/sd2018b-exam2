import os
import logging
import requests
import json
import docker
from flask import Flask, request, json

def hello():
    result = {'command_return': 'Hello'}
    return result

def repository_merged():
    retorno = ""
    post_json_data = request.get_data()
    string = str(post_json_data, 'utf-8')
    jsonFile = json.loads(string)
    itWasMerged = jsonFile["pull_request"]["merged"]
    domain = 'swan-registry.icesi.edu.co:443'
    if itWasMerged:
        pull_id = jsonFile["pull_request"]["head"]["sha"]
        json_image_url = 'https://raw.githubusercontent.com/juanswan13/sd2018b-exam2/' + pull_id + '/images.json'
        json_image_response = requests.get(json_image_url)
        images_json = json.loads(json_image_response.content)
        for service in images_json["images"]:
            service_name = service["service_name"]
            image_type = service["type"]
            image_version = service["version"]
            if image_type == 'Docker':
                image_url = 'https://raw.githubusercontent.com/juanswan13/sd2018b-exam2/' + pull_id + '/' + service_name + '/Dockerfile'
                file_response=requests.get(image_url)
                file = open("Dockerfile","w")
                file.write(str(file_response.content, 'utf-8'))
                file.close()
                image_tag = domain + '/' + service_name + ':' + image_version
                client = docker.from_env()
                client.images.build(path="./", tag=image_tag)
                client.images.push(image_tag)
                client.images.remove(image=image_tag, force=True)
                retorno = image_tag + " - " + retorno
            elif image_type == 'AMI':
                image_url = 'https://raw.githubusercontent.com/juanswan13/sd2018b-exam2/' + pull_id + '/' + service_name + '/AMI'
                file_response=requests.get(image_url)
                file = open("AMI","w")
                file.write(str(file_response.content, 'utf-8'))
                file.close()
                image_tag = domain + '/' + service_name + ':' + image_version

                retorno = image_tag + " - " + retorno
            else:
                result = {'command_return': 'ERROR: JSON does not have a correct format.'}
        result = {'command_return': retorno}
    else:
        result = {'command_return': 'Pull request was not merged'}
    return result
