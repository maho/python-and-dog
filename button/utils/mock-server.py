#!/usr/bin/env python3
from flask import Flask, request, jsonify


app = Flask(__name__)


@app.route("/foo/", methods=['POST'])
def index():

    print("request=", request.json)

    return jsonify("ok"), 202


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5060)
