"""
.. module:: ConvoTest

ConvoTest
*************

:Description: ConvoTest

    

:Authors: bejar
    

:Version: 

:Created on: 28/11/2016 11:10 

"""

import numpy
from keras.datasets import cifar10
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import Flatten
from keras.constraints import maxnorm
from keras.optimizers import SGD
from keras.layers.convolutional import Convolution2D
from keras.layers.convolutional import MaxPooling2D
from keras.utils import np_utils
from keras import backend as K
K.set_image_dim_ordering('th')
from Util.Generate_Dataset import generate_dataset
from Util.Logger import config_logger
import time
from Util.Cameras import Cameras
from sklearn.metrics import confusion_matrix, classification_report


__author__ = 'bejar'




if __name__ == '__main__':
    seed = 7
    numpy.random.seed(seed)
    log = config_logger(file='convolutional-' + time.strftime('%Y%m%d%H%M%S', time.localtime(int(time.time()))))
    ldaysTr = ['20161111', '20161112', '20161113', '20161114', '20161115']
    ldaysTs = ['20161116']
    z_factor = 0.25
    camera = 'Ronda' #Cameras[0]

    log.info('Train= %s  Test= %s z_factor= %0.2f camera= %s', ldaysTr, ldaysTs, z_factor, camera)

    X_train, y_train, X_test, y_test = generate_dataset(ldaysTr, ldaysTs, z_factor, PCA=False, method='two', reshape=False, cpatt=camera)
    X_train = X_train.transpose((0,3,1,2))
    X_test = X_test.transpose((0,3,1,2))

    print(X_train[0].shape)

    y_train = np_utils.to_categorical(y_train)
    y_test = np_utils.to_categorical(y_test)
    num_classes = y_test.shape[1]
    print(num_classes)

    # Model 1
    model = Sequential()
    model.add(Convolution2D(32, 3, 3, input_shape=(3, 58, 78), border_mode='same', activation='relu', W_constraint=maxnorm(3)))
    model.add(Dropout(0.2))
    model.add(Convolution2D(32, 3, 3, activation='relu', border_mode='same', W_constraint=maxnorm(3)))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Flatten())
    model.add(Dense(128, activation='relu', W_constraint=maxnorm(3))) #512
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation='softmax'))

    # Model 2
    # model = Sequential()
    # model.add(Convolution2D(32, 3, 3, input_shape=(3, 58, 78), activation='relu', border_mode='same'))
    # model.add(Dropout(0.2))
    # model.add(Convolution2D(32, 3, 3, activation='relu', border_mode='same'))
    # model.add(MaxPooling2D(pool_size=(2, 2)))
    # model.add(Convolution2D(64, 3, 3, activation='relu', border_mode='same'))
    # model.add(Dropout(0.2))
    # model.add(Convolution2D(64, 3, 3, activation='relu', border_mode='same'))
    # model.add(MaxPooling2D(pool_size=(2, 2)))
    # model.add(Convolution2D(128, 3, 3, activation='relu', border_mode='same'))
    # model.add(Dropout(0.2))
    # model.add(Convolution2D(128, 3, 3, activation='relu', border_mode='same'))
    # model.add(MaxPooling2D(pool_size=(2, 2)))
    # model.add(Flatten())
    # model.add(Dropout(0.2))
    # model.add(Dense(1024, activation='relu', W_constraint=maxnorm(3)))
    # model.add(Dropout(0.2))
    # model.add(Dense(512, activation='relu', W_constraint=maxnorm(3)))
    # model.add(Dropout(0.2))
    # model.add(Dense(num_classes, activation='softmax'))


    # Compile model
    epochs = 50
    lrate = 0.05  #0.01
    decay = lrate/epochs
    sgd = SGD(lr=lrate, momentum=0.9, decay=decay, nesterov=False)
    model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
    print(model.summary())

    model.fit(X_train, y_train, validation_data=(X_test, y_test), nb_epoch=epochs, batch_size=32)
    # Final evaluation of the model
    scores = model.evaluate(X_test, y_test, verbose=0)
    print("Accuracy: %.2f%%" % (scores[1]*100))
    labels = model.predict(X_test)

    print(confusion_matrix(y_test, labels))
    print(classification_report(y_test, labels))