from flask import Flask,render_template
import boto3, botocore
import configparser
import os
from werkzeug.utils import secure_filename
from flask import Flask, redirect, url_for, request
import json
import numpy as np

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/application', methods=["POST","GET"])
def application():
   cls = ''
   prob = 0

   if request.method == 'POST':
      print('called')
      config = configparser.ConfigParser()
      config.read('config.ini')

      key = config['aws']['AWS_ACCESS_KEY']
      secret = config['aws']['AWS_SECRET_ACCESS_KEY']

      runtime = boto3.client(
         "sagemaker-runtime",
         aws_access_key_id=key,
         aws_secret_access_key=secret
      )

      endpoint = 'enter endpoint here'

      # Read image into memory
      payload = request.files['file']

      # Send image via InvokeEndpoint API
      response = runtime.invoke_endpoint(EndpointName=endpoint,
                                         ContentType='application/x-image',
                                         Body=payload)

      result = response["Body"].read()
      result = json.loads(result)
      index = np.argmax(result)

      object_categories = [
        #enter object categories here
      ]

      cls = object_categories[index]
      prob = str(round(result[index],2))

   return render_template('application.html',cls=cls,prob=prob)

def lyric_input(lyric):
    #todo
    return lyric

#run flask app
if __name__ == '__main__':
   app.run()
