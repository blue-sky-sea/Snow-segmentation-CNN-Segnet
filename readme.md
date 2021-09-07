========================================================================

# A snow segmentation using CNN-Segnet

========================================================================
![image](https://user-images.githubusercontent.com/26008298/132282618-0440b99c-af47-4e75-9c45-2253ba94f59d.png)

## environment
keras
tensorflow
PIL
numpy
...


## to make dataset
at /make_dataset
use lableme to label the snow area
save jpg and (labeled)json at /before
#### step1:python json_to_dataset.py
#### step2:python get_jpg_and_png
#### step3:python get_train_txt.py

## to train the data
python train.py 


## to predict the data
python predict.py 

## the predict result using ep079-loss0.153-val_loss0.368.h5 model
![02879](https://user-images.githubusercontent.com/26008298/117781328-7cd53080-b27b-11eb-8733-bc8825a4dac7.jpg)
![02865](https://user-images.githubusercontent.com/26008298/117781385-8f4f6a00-b27b-11eb-8f5c-64b8aada6c6e.jpg)

