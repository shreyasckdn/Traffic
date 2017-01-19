'''
.. module:: ConvoBatch

ConvoBatch
*************

  Trains a model according to a configuration file (--batch) or the harcoded config object
  Model is trained using the train_on_batch method from Keras model, so only a day is loaded in memory at a time

:Description: ConvoBatch

:Authors: bejar

:Version: 

:Created on: 23/12/2016 15:05 

'''

__author__ = 'bejar'

from keras import backend as K

from Models.SimpleModels import simple_model
from Util.ConvoTrain import transweights, train_model_batch
from Util.DataGenerators import list_days_generator
from Util.ConvoTrain import load_dataset
from Util.Constants import dataset_path

import json
import argparse

__author__ = 'bejar'


def load_config_file(nfile):
    '''
    Read the configuration from a json file

    :param nfile:
    :return:
    '''
    fp = open('./' + nfile + '.json', 'r')

    s = ''

    for l in fp:
        s += l

    return s


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', help='Ejecucion no interactiva', action='store_true', default=False)
    parser.add_argument('--config', default='config', help='Configuracion del experimento')
    args = parser.parse_args()

    if args.batch:
        sconfig = load_config_file(args.config)

        config = json.loads(sconfig)
        # config['decay'] = config['lrate'] / config['epochs']

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
        z_factor = 0.25
        camera = None  # 'Ronda' #Cameras[0]

        smodel = 3
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
                      }},
            "train":
                {"batchsize": 256,
                 "epochs": 200,
                 "classweight": transweights(classweight)},

            'imgord': 'th'
        }


        # config['optimizer']['params']['decay'] = config['lrate'] / config['epochs']

    K.set_image_dim_ordering(config['imgord'])

    _, test, test_labels, num_classes = load_dataset(config, only_test=True, imgord=config['imgord'])

    config['input_shape'] = test[0][0].shape
    config['num_classes'] = num_classes

    model = simple_model(config)

    train_model_batch(model, config, test, test_labels)
