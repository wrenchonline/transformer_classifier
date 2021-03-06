from flask import Flask, request, jsonify
import logging
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.abspath("/src/"))

logging.basicConfig(
    filename="/src/app/api.log",
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s - %(message)s",
)
log = logging.getLogger()

import tensorflow_datasets as tfds
import tensorflow as tf
import utensor.dataset as dt
from utensor.optimizer import CustomSchedule, loss_function
from utensor.model import Transformer
import time
from utensor.masking import create_masks
from utensor.predict import restore, evaluate, translate
import pickle
import matplotlib.pyplot as plt
import json


app = Flask(__name__)
CORS(app)

checkpoint_path = "/src/data/"
params = json.load(open(checkpoint_path + "/params.json"))

params["checkpoint_path"] = checkpoint_path
d_model = params["d_model"]
MAX_LENGTH = params["MAX_LENGTH"]
BUFFER_SIZE = params["BUFFER_SIZE"]
BATCH_SIZE = params["BATCH_SIZE"]
num_heads = params["num_heads"]
num_layers = params["num_layers"]
dff = params["dff"]
dropout_rate = params["dropout_rate"]


log.info("loading model ...")
transformer, tokenizer_source, tokenizer_target = restore(params)
log.info("model loaded")


@app.route("/", methods=["GET"])
def home():
    return """ 
        <h1>UmayuxLabs transformer</h1>
        <p>This is the implementation of the transformes (attention is all you need from google)
        made by UmayuxLabs.</p>
        <p>This API has an endpoint where you can retrieve a response to a text input</p>
        <p>Depending on the model you will receive a different output. This is a generic API</p>
        <h3>USAGE</h3>
        <p>
            POST: /predict/ <br>
                QUERY: {sentence: "..."} <br>
            RETURN: {response: "...", status: 1} <br><br>
        
        <strong>EXAMPLE</strong> <br>
        curl -X POST http://localhost:65431/predict/ -d'{"sentence": "hola, buenos dias", "max_predictions": 5, "attention": false, "layer": 4, "block": 1}' -H "Content-Type: application/json"
        <br><br>
        curl -X POST http://localhost:65431/predict/ -d'{"sentence": "hola, buenos dias", "max_predictions": 5, "attention": false, "layer": 4, "block": 1}' -H "Content-Type: application/json"
        </p>
    """


@app.route("/predict/", methods=["POST"])
def predict():
    data = request.get_json()
    log.debug(data)
    params["max_predictions"] = data["max_predictions"]
    params["attention"] = data["attention"]
    params["layer"] = data["layer"]
    params["block"] = data["block"]

    response, attention = translate(
        data["sentence"], params, tokenizer_source, tokenizer_target, transformer
    )

    if params["attention"]:
        return jsonify(
            {
                "response": response,
                "attention": attention[
                    "decoder_layer{}_block{}".format(params["layer"], params["block"])
                ]
                .numpy()
                .tolist(),
            }
        )
    else:
        return jsonify({"response": response, "attention": []})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
