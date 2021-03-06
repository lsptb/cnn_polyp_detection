import caffe
import surgery, score
import numpy as np
import os
import sys 
import setproctitle
setproctitle.setproctitle(os.path.basename(os.getcwd()))

# Pre-trained weights path
weights = './fcn32s-heavy-pascal.caffemodel'

# set gpu mode
caffe.set_mode_gpu()
caffe.set_device(0);

# Initialize SGD solver using the pre-trained weights
solver = caffe.SGDSolver('solver.prototxt')
solver.net.copy_from(weights)

# Resize blobs corresponding to deconvolutions
interp_layers = [k for k in solver.net.params.keys() if 'up' in k]
surgery.interp(solver.net, interp_layers)

# Train
solver.solve()
