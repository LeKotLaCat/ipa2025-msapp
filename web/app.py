import os
from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient, DESCENDING
from bson import ObjectId, json_util

app = Flask(__name__)

mongo_uri = os.environ.get("MONGO_URI")
db_name = os.environ.get("DB_NAME")
client = MongoClient(mongo_uri)
db = client[db_name]

routers_collection = db["routers"]
interface_status_collection = db["interfaces"]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", routers=list(routers_collection.find()))


@app.route("/router/<router_ip>")
def router_detail(router_ip):
    status_history = (
        interface_status_collection.find({"router_ip": router_ip})
        .sort("timestamp", DESCENDING)
        .limit(3)
    )

    status_list = list(status_history)

    # Debug print
    print("--- DEBUG: Data being sent to template ---")
    print(json_util.dumps(status_list, indent=2))
    print("------------------------------------------")

    return render_template(
        "router_detail.html", router_ip=router_ip, history=status_list
    )


@app.route("/add", methods=["POST"])
def add_router():
    ip = request.form.get("ip")
    username = request.form.get("username")
    password = request.form.get("password")

    if ip and username and password:
        routers_collection.insert_one(
            {"ip": ip, "username": username, "password": password}
        )
    return redirect(url_for("index"))


@app.route("/delete/<id>", methods=["POST"])
def delete_router(id):
    routers_collection.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
