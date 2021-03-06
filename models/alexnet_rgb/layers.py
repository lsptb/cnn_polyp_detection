import caffe
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import random

class SBDDSegDataLayer(caffe.Layer):
    """
    Layer class to load input image and ground truth binary mask from the polyp dataset
    and perform data pre-processing:
    - cast to float
    - image resizing
    - mean subtraction
    - RGB -> BGR
    """

    def setup(self, bottom, top):
        """
        Setup data layer initialising parameters:
        - data_dir: path to dataset
        - split: name of file containing frame filenames
        - mean: tuple of mean values to subtract
        - randomize: load in random order (default: True)
        - seed: seed for randomization (default: None)
        """
        # initialize
        params = eval(self.param_str)
        self.data_dir = params['data_dir']
        self.split = params['split']
	self.split_label = params['split_label']
        self.mean = np.array(params['mean'])
        self.random = params.get('randomize', True)
        self.seed = params.get('seed', None)
	self.width=params.get('width', 500)
	self.height=params.get('height', 500)

        # two tops: data and label
        if len(top) != 2:
            raise Exception("Need to define two tops: data and label.")
        # data layers have no bottoms
        if len(bottom) != 0:
            raise Exception("Do not define a bottom.")

        # load indices for images and binary masks
        split_f  = '{}/{}.txt'.format(self.data_dir, self.split)
	split_f_label  = '{}/{}.txt'.format(self.data_dir, self.split_label)
        self.indices = open(split_f, 'r').read().splitlines()
	self.indices_label= open(split_f_label, 'r').read().splitlines()
        self.idx = 0

        # if the data belong to the training set, parse them randomly
        if 'train' not in self.split:
            self.random = False

        # initialize the data index randomly in case of train, or
        # to zero in case of testing
        if self.random:
            random.seed(self.seed)
            self.idx = random.randint(0, len(self.indices)-1)


    def reshape(self, bottom, top):
	'''
	Load input image and binary masks and reshape blobs.
	'''
        # load RGB image and binary mask
	image=self.load_image(self.indices[self.idx])
	label=self.load_label(self.indices_label[self.idx])
	# Flip the image and the mask both on the vertical and horizontal axis
        # to augment the dataset.
	if 'train' in self.split:
		if random.random()>0.5:
			image=image[:,::-1,:]
			label=label[:,::-1,:]
		if random.random()>0.5:
			image=image[:,:,::-1]
			label=label[:,:,::-1]
        self.data = image
        self.label = label
        # reshape tops to fit (leading 1 is for batch dimension)
        top[0].reshape(1, *self.data.shape)
        top[1].reshape(1, *self.label.shape)


    def forward(self, bottom, top):
        # assign the output of the Python Layer as the input of the
        # next layers
        top[0].data[...] = self.data
        top[1].data[...] = self.label

        # pick next input randomly, if in train, or sequentially if in testing
        if self.random:
            self.idx = random.randint(0, len(self.indices)-1)
        else:
            self.idx += 1
            if self.idx == len(self.indices):
                self.idx = 0


    def backward(self, top, propagate_down, bottom):
	# the data layer doesn't participate in backprop, so we just pass
        pass


    def load_image(self, idx):
        """
        Load input image and preprocess for Caffe:
	- resize image
        - cast to float
        - switch channels RGB -> BGR
        - subtract mean
        - transpose to channel x height x width order
        """
	idx=idx.split()[0]
	try:
        	im = Image.open('{}/{}'.format(self.data_dir, idx))
	except:
		from skimage import io	
		im = io.imread('{}/{}'.format(self.data_dir, idx))
		im = Image.fromarray(im)
	im=im.resize((self.width, self.height), Image.ANTIALIAS)	# resize image
        im = np.array(im, dtype=np.float32)				# cast to float
        im = im[:,:,::-1]						# RGB -> BGR
        im -= self.mean							# mean subtraction
	# bring colour to the innermost dimension
        im = im.transpose((2,0,1))
        return im


    def load_label(self, idx):
        """
        Load binary mask and preprocess:
	- resize
	- convert to greyscale
	- cast to integer
	- binarize
        """
	idx=idx.split()[0]
        im = Image.open('{}/{}'.format(self.data_dir, idx))
	im=im.resize((self.width, self.height), Image.NEAREST)
	im=im.convert('L') 						# convert to greyscale
	im=np.array(im, dtype=(np.int32))
	label=im
	label[label>0]=1						# make sure the image is binary
	label=np.array(label,np.uint8)
	# an extra dimension is required by the loss function
        label = label[np.newaxis, ...]   
	return label

