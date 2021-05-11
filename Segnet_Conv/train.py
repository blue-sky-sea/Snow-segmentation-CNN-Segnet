import keras
import numpy as np
from keras import backend as K
from keras.callbacks import (EarlyStopping, ModelCheckpoint, ReduceLROnPlateau,
                             TensorBoard)
from keras.optimizers import Adam
from keras.utils.data_utils import get_file
from PIL import Image

from nets.segnet import convnet_segnet

#-------------------------------------------------------------#
#   定义了一个生成器，用于读取datasets2文件夹里面的图片与标签
#-------------------------------------------------------------#
def generate_arrays_from_file(lines,batch_size):
    n = len(lines)
    i = 0
    while 1:
        X_train = []
        Y_train = []
        for _ in range(batch_size):
            if i==0:
                np.random.shuffle(lines)
            #-------------------------------------#
            #   读取输入图片并进行归一化和resize
            #-------------------------------------#
            name = lines[i].split(';')[0]
            img = Image.open("./dataset2/jpg/" + name)
            img = img.resize((WIDTH,HEIGHT), Image.BICUBIC)
            img = np.array(img)/255
            X_train.append(img)

            #-------------------------------------#
            #   读取标签图片并进行归一化和resize
            #-------------------------------------#
            name = lines[i].split(';')[1].split()[0]
            label = Image.open("./dataset2/png/" + name)
            label = label.resize((int(WIDTH/2),int(HEIGHT/2)), Image.NEAREST)
            if len(np.shape(label)) == 3:
                label = np.array(label)[:,:,0]
            label = np.reshape(np.array(label), [-1])
            one_hot_label = np.eye(NCLASSES)[np.array(label, np.int32)]
            Y_train.append(one_hot_label)

            i = (i+1) % n
        yield (np.array(X_train), np.array(Y_train))

if __name__ == "__main__":
    #---------------------------------------------#
    #   定义输入图片的高和宽，以及种类数量
    #---------------------------------------------#
    HEIGHT = 416
    WIDTH = 416
    #---------------------------------------------#
    #   背景 + 斑马线 = 2
    #---------------------------------------------#
    NCLASSES = 5

    log_dir = "logs/"
    model = convnet_segnet(n_classes=NCLASSES, input_height=HEIGHT, input_width=WIDTH)
    #---------------------------------------------------------------------#
    #   这一步是获得主干特征提取网络的权重、使用的是迁移学习的思想
    #   如果下载过慢，可以复制连接到迅雷进行下载。
    #   之后将权值复制到目录下，根据路径进行载入。
    #   如：
    #   weights_path = "xxxxx.h5"
    #   model.load_weights(weights_path,by_name=True,skip_mismatch=True)
    #---------------------------------------------------------------------#
    #WEIGHTS_PATH_NO_TOP = 'https://github.com/fchollet/deep-learning-models/releases/download/v0.1/vgg16_weights_tf_dim_ordering_tf_kernels_notop.h5'
    #weights_path = get_file('vgg16_weights_tf_dim_ordering_tf_kernels_notop.h5', WEIGHTS_PATH_NO_TOP, cache_subdir='models')
    weights_path = "logs/ep079-loss0.153-val_loss0.368.h5"
    model.load_weights(weights_path,by_name=True)

    # 打开数据集的txt
    with open("./dataset/train.txt","r") as f:
        lines = f.readlines()

    #---------------------------------------------#
    #   打乱的数据更有利于训练
    #   90%用于训练，10%用于估计。
    #---------------------------------------------#
    np.random.seed(10101)
    np.random.shuffle(lines)
    np.random.seed(None)
    num_val = int(len(lines)*0.1)
    num_train = len(lines) - num_val

    #-------------------------------------------------------------------------------#
    #   训练参数的设置
    #   checkpoint用于设置权值保存的细节，period用于修改多少epoch保存一次
    #   reduce_lr用于设置学习率下降的方式
    #   early_stopping用于设定早停，val_loss多次不下降自动结束训练，表示模型基本收敛
    #-------------------------------------------------------------------------------#
    checkpoint = ModelCheckpoint(log_dir + 'ep{epoch:03d}-loss{loss:.3f}-val_loss{val_loss:.3f}.h5',
                                    monitor='val_loss', save_weights_only=True, save_best_only=False, period=2)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1)
    early_stopping = EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=1)

    #-------------------------------------------------------------------------------#
    #   这里使用的是迁移学习的思想，主干部分提取出来的特征是通用的
    #   所以我们可以不训练主干部分先，因此训练部分分为两步，分别是冻结训练和解冻训练
    #   冻结训练是不训练主干的，解冻训练是训练主干的。
    #   由于训练的特征层变多，解冻后所需显存变大
    #-------------------------------------------------------------------------------#
    trainable_layer = 15
    for i in range(trainable_layer):
        model.layers[i].trainable = False
    print('freeze the first {} layers of total {} layers.'.format(trainable_layer, len(model.layers)))

    if True:
        lr = 1e-3
        batch_size = 4
        model.compile(loss = 'categorical_crossentropy',
                optimizer = Adam(lr=lr),
                metrics = ['accuracy'])

        print('Train on {} samples, val on {} samples, with batch size {}.'.format(num_train, num_val, batch_size))
        model.fit_generator(generate_arrays_from_file(lines[:num_train], batch_size),
                steps_per_epoch=max(1, num_train//batch_size),
                validation_data=generate_arrays_from_file(lines[num_train:], batch_size),
                validation_steps=max(1, num_val//batch_size),
                epochs=50,
                initial_epoch=0,
                callbacks=[checkpoint, reduce_lr,early_stopping])


    for i in range(len(model.layers)):
        model.layers[i].trainable = True

    if True:
        lr = 1e-4
        batch_size = 4
        model.compile(loss = 'categorical_crossentropy',
                optimizer = Adam(lr=lr),
                metrics = ['accuracy'])

        print('Train on {} samples, val on {} samples, with batch size {}.'.format(num_train, num_val, batch_size))
        model.fit_generator(generate_arrays_from_file(lines[:num_train], batch_size),
                steps_per_epoch=max(1, num_train//batch_size),
                validation_data=generate_arrays_from_file(lines[num_train:], batch_size),
                validation_steps=max(1, num_val//batch_size),
                epochs=100,
                initial_epoch=50,
                callbacks=[checkpoint, reduce_lr,early_stopping])
