"""
.. module:: BatchTrain

BatchTrain
*************

:Description: BatchTrain

    

:Authors: bejar
    

:Version: 

:Created on: 20/12/2016 14:33 

"""

__author__ = 'bejar'

from keras import backend as K
from pymongo import MongoClient

from Util.DBConfig import mongoconnection

K.set_image_dim_ordering('th')


from Models.SimpleModels import simple_model
from Util.ConvoTrain import train_model, load_dataset
import socket
from time import sleep

if __name__ == '__main__':
    while True:
        client = MongoClient(mongoconnection.server)
        db = client[mongoconnection.db]
        db.authenticate(mongoconnection.user, password=mongoconnection.passwd)
        col = db[mongoconnection.col]
        batch = col.find_one({'host':socket.gethostname().split('.')[0], 'pending': True})
        if batch is not None:
            config = batch['config']
            train, test, test_labels, num_classes = load_dataset(config['train'], config['test'], config['z_factor'])

            config['input_shape'] = train[0][0].shape
            config['nexamples'] = train[0].shape[0]
            config['num_classes'] = num_classes

            model = simple_model(config['model'], config)
            train_model(model, config, train, test, test_labels)
            col.update({'_id': batch['_id']}, {'$set':{'pending': False}})
        else:
            sleep(1500)
