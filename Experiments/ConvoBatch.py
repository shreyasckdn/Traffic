"""
.. module:: ConvoBatch

ConvoBatch
*************

  Trains a model according to a configuration file (--batch) or the harcoded config object

  It uses the files for each individual day
  Model is trained using the train_on_batch method from Keras model, so only a day is loaded in memory at a time

:Description: ConvoBatch

:Authors: bejar

:Version:

:Created on: 23/12/2016 15:05

"""

import argparse

import keras.models
from Traffic.Models.SimpleModels import simple_model
from Traffic.Private.DBConfig import mongoconnection
from Traffic.Util.ConvoTrain import load_dataset
from Traffic.Util.ConvoTrain import transweights, train_model_batch
from Traffic.Util.DataGenerators import list_days_generator
from keras import backend as K
from pymongo import MongoClient
from Traffic.Util.Misc import load_config_file, transweights

__author__ = 'bejar'

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', help='Non interactive run', action='store_true', default=False)
    parser.add_argument('--config', default='config', help='Experiment configuration')
    parser.add_argument('--resume', default=None, help='Resume existing experiment training')
    parser.add_argument('--retrain', default=None, help='Continue existing experiment training')
    args = parser.parse_args()

    if args.batch:
        config = load_config_file(args.config)

        ldaysTr = []

        for y, m, di, df in config['traindata']:
            ldaysTr.extend(list_days_generator(y, m, di, df))
        config['traindata'] = ldaysTr

        ldaysTs = []

        for y, m, di, df in config['testdata']:
            ldaysTs.extend(list_days_generator(y, m, di, df))
        config['testdata'] = ldaysTs
    else:
        ldaysTr = list_days_generator(2016, 11, 1, 30)
        ldaysTs = list_days_generator(2016, 12, 1, 2)

        classweight = {0: 1.0, 1: 1.0, 2: 2.0, 3: 3.0, 4: 4.0}

        config = {
            'datapath': '/home/bejar/storage/Data/Traffic/Datasets/',
            'savepath': '/home/bejar/storage/Data/Traffic/Models/',
            'traindata': ldaysTr,
            'testdata': ldaysTs,
            'rebalanced': False,
            'zfactor': 0.25,
            'model': 4,
            'convolayers':
                {'sizes': [128, 64, 32],
                 'convofields': [3, 3],
                 'dpconvo': 0.2,
                 'pool': ['max', 2, 2]},
            'fulllayers':
                {'sizes': [64, 32],
                 'regfull': ['l1', 0.2]},
            'optimizer':
                {'method': 'sdg',
                 'params':
                     {'lrate': 0.005,
                      'momentum': 0.9,
                      'nesterov': False,
                      'decay': 0
                      }},
            "train":
                {"batchsize": 256,
                 "epochs": 200,
                 "classweight": transweights(classweight)},

            'imgord': 'th'
        }

        # config['optimizer']['params']['decay'] = config['lrate'] / config['epochs']

    K.set_image_dim_ordering(config['imgord'])

    # Only the test set in memory, the training is loaded in batches
    _, test, test_labels, num_classes = load_dataset(config, only_test=True, imgord=config['imgord'])

    config['input_shape'] = test[0][0].shape
    config['num_classes'] = num_classes

    resume = None
    if args.retrain is not None:  # Retwork already trained
        client = MongoClient(mongoconnection.server)
        db = client[mongoconnection.db]
        db.authenticate(mongoconnection.user, password=mongoconnection.passwd)
        col = db[mongoconnection.col]

        vals = col.find_one({'_id': int(args.retrain)}, {'config': 1})
        if vals is None:
            raise ValueError('This experiment does not exist ' + args.retrain)
        else:
            if config['zfactor'] != vals['config']['zfactor']:
                raise ValueError('Incompatible Data')
            weights = config['train']['classweight']
            for w in weights:
                if weights[w] != vals['config']['train']['classweight'][w]:
                    raise ValueError('Incompatible class weights')
            config['model'] = vals['config']['model']
            config['convolayers'] = vals['config']['convolayers']
            config['fulllayers'] = vals['config']['fulllayers']
            config['cont'] = args.retrain
            model = keras.models.load_model(config['savepath'] + args.retrain + '.h5')
    elif args.resume is not None:  # Network interrupted
        client = MongoClient(mongoconnection.server)
        db = client[mongoconnection.db]
        db.authenticate(mongoconnection.user, password=mongoconnection.passwd)
        col = db[mongoconnection.col]

        vals = col.find_one({'_id': int(args.retrain)}, {'config': 1, 'acc': 1})
        if vals is None:
            raise ValueError('This experiment does not exist ' + args.resume)
        else:
            config = vals['config']
            config['train']['epochs_trained'] = len(config['acc'])
            model = keras.models.load_model(config['savepath'] + args.resume + '.h5')
            resume = vals

    else:  # New model
        model = simple_model(config)

    train_model_batch(model, config, test, test_labels, resume=resume)
