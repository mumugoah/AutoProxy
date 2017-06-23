from flask import request, Request, Flask, Response
import config
from functools import wraps
from enum import Enum
import pymongo
import json

class ClientType(Enum):
    Client = 'proxy'
    Spider = 'spider'

app = Flask(__name__)


def check_auth(token, client:ClientType):
        if client == ClientType.Client:
            return token == config.CLIENT_AUTH_TOKEN
        elif client == ClientType.Spider:
            return token == config.SPIDER_AUTH_TOKEN
        else:
            return False

def authenticate(request:Request):
    auth_token = request.headers.get('Authorization')
    client = request.args.get('client')
    if client and auth_token:
        try:
            client = ClientType(client)
            res = check_auth(auth_token, client)
            if res:
                return True
        except:
            print('wrong keytype')
            return False


def get_collection()->pymongo:

    client = pymongo.MongoClient('127.0.0.1', 27017)
    db = client.proxy
    collection = db.proxy_clients

    return collection

def jsonres(data = None, message= '', status= 200):
    if data:
        return Response(json.dumps({
            'status':status,
            'data': data
        }),content_type='application/json')
    else:
        return Response(json.dumps({
            'status': status,
            'message': message
        }),content_type='application/json')

@app.route('/proxy', methods=['POST'])
def update():
    ip = request.remote_addr
    port = request.form.get('port')
    client_id = request.form.get('client_id')
    username = request.form.get('username')
    password = request.form.get('password')
    if not client_id or not username or not password or not port:
        return jsonres(message='参数不全', status=400)

    if not authenticate(request):
        return jsonres(message='认证失败', status=400)

    collection = get_collection()

    # 存入数据库
    if collection.find_one({'client_id':client_id}):
        collection.update({"client_id":client_id},{"$set":{"ip":ip, "port":port, "username":username, "password":password}})
    else:
        collection.insert({"client_id":client_id, "ip":ip, "port":port, "username":username, "password":password})

    return jsonres(data={'client_id':client_id}, status=200)


@app.route('/proxy', methods=['GET'])
def proxy():
    if not authenticate(request):
        return jsonres(message='认证失败', status=400)

    collection = get_collection()

    cur = collection.find({},{'_id':False})
    if cur:
        proxylist = []
        for proxy in cur:
            proxylist.append(proxy)

        if not proxylist:
            return jsonres(status=200, data=[])
        else:
            return jsonres(status=200, data=proxylist)
    else:
        return jsonres(status=200, data=[])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT)
