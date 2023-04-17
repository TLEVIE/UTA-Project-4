from flask import Flask,render_template, request
import boto3, botocore
import configparser
import json
import numpy as np

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/application')
def application():
   return render_template('application.html')

@app.route('/application', methods=["POST"])
def application_post():
      
      result = ''

      runtime = boto3.client("sagemaker-runtime", region_name='us-west-2')
      endpoint = 'enter endpoint here'

      # Read image into memory
      payload = request.form['text_input']

      # Send image via InvokeEndpoint API
      response = runtime.invoke_endpoint(EndpointName=endpoint,
                                         ContentType='text/csv',
                                         Body=payload)

      result = response["Body"].read()
      result = json.loads(result)

      return render_template('application.html', result=result)

#run flask app
if __name__ == '__main__':
   app.run()
