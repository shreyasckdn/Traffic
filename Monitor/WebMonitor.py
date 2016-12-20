"""
.. module:: WebMonitor

ConvoTest
*************

:Description: WebStatus



:Authors: bejar


:Version:

:Created on: 28/11/2016 11:10

"""

import socket

from flask import Flask, render_template, request
from pymongo import MongoClient

import StringIO

import bokeh.plotting as plt
import tempfile
import matplotlib
matplotlib.use('Agg')

import  matplotlib.pyplot as plt
import base64
import seaborn as sns

from Util.DBConfig import mongoconnection
#from Parameters.Private import WS_port

__author__ = 'bejar'

# Configuration stuff
hostname = socket.gethostname()
port = 8850

app = Flask(__name__)




@app.route('/Monitor')
def info():
    """
    Status de las ciudades
    """

    client = MongoClient(mongoconnection.server)
    db = client[mongoconnection.db]
    db.authenticate(mongoconnection.user, password=mongoconnection.passwd)
    col = db[mongoconnection.col]

    vals = col.find({'done': False}, {'_id':1,'acc':1, 'loss': 1, 'val_acc':1, 'val_loss':1, 'host':1, 'time_upd':1})

    res = {}
    for v in vals:
        if len(v['acc'])>0:
            res[v['_id']] = {}
            res[v['_id']]['epoch'] = len(v['acc'])
            res[v['_id']]['acc'] = v['acc'][-1]
            res[v['_id']]['val_acc'] = v['val_acc'][-1]
            res[v['_id']]['host'] = v['host']
            res[v['_id']]['upd'] = v['time_upd']


    vals = col.find({'done': True, 'final_val_acc': { '$gt': 0.7 }},
                    {'_id':1,'final_acc':1, 'final_val_acc':1, 'val_loss':1})

    old = {}

    for v in vals:
        res[v['_id']] = {}
        res[v['_id']]['final_acc'] = v['final_acc']
        res[v['_id']]['final_val_acc'] = v['final_val_acc']


    return render_template('Monitor.html', data=res, old=old)




@app.route('/Graph', methods=['GET','POST'])
def graphic():
    """
    Generates a page with the training trace

    :return:
    """

    lstyles = [':', '-', '--', '-.'] *3
    payload = request.form['graph']

    client = MongoClient(mongoconnection.server)
    db = client[mongoconnection.db]
    db.authenticate(mongoconnection.user, password=mongoconnection.passwd)
    col = db[mongoconnection.col]

    vals = col.find_one({'_id': int(payload)}, {'acc':1, 'loss': 1, 'val_acc':1, 'val_loss':1})
    if vals is not None:
        del vals['_id']

        img = StringIO.StringIO()



        fig = plt.figure(figsize=(5,4),dpi=100)
        axes = fig.add_subplot(1,1,1)

        for v,lstyle in zip(sorted(vals), lstyles):
            axes.plot(range(len(vals[v])),vals[v],lstyle, label=v)

        axes.set_xlabel('epoch')
        axes.set_ylabel('acc/loss')
        axes.set_title("Training/Test")

        plt.legend()
        plt.savefig(img, format='png')
        img.seek(0)

        plot_url = base64.b64encode(img.getvalue())
        plt.close()

        return render_template('graphview.html', plot_url=plot_url)
    else:
        return None

@app.route('/Model', methods=['GET','POST'])
def model():
    """
    Generates a page with the training trace

    :return:
    """
    payload = request.form['model']

    client = MongoClient(mongoconnection.server)
    db = client[mongoconnection.db]
    db.authenticate(mongoconnection.user, password=mongoconnection.passwd)
    col = db[mongoconnection.col]

    vals = col.find_one({'_id': int(payload)}, {'model':1})

    return vals['model']



if __name__ == '__main__':
    # Ponemos en marcha el servidor Flask
    app.run(host='0.0.0.0', port=port, debug=False)