import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import os
import tifffile
from glob import glob
from skimage.segmentation import relabel_sequential
from EmbedSeg.utils.glasbey import Glasbey
from EmbedSeg.train import invert_one_hot
from scipy.ndimage import zoom
import pandas as pd
import ast
import pycocotools.mask as rletools


def create_color_map(n_colors=10):
    gb = Glasbey(base_palette=[(255, 0, 0), (0, 255, 0), (0, 0, 255)],
                 lightness_range=(10, 100),
                 hue_range=(10, 100),
                 chroma_range=(10, 100),
                 no_black=True)
    p = gb.generate_palette(size=n_colors)
    p[0, :] = [0, 0, 0]  # make label 0 always black!
    p_ = np.hstack((p, np.ones((p.shape[0], 1))))
    p_ = np.where(p_ > 0, p_, 0)
    p_ = np.where(p_ <= 1, p_, 1)
    return p_


def visualize(image, prediction, ground_truth, embedding, new_cmp):
    font = {'family': 'serif',
            'color': 'white',
            'weight': 'bold',
            'size': 16,
            }
    plt.figure(figsize=(15, 15))
    img_show = image if image.ndim == 2 else image[0, ...]
    plt.subplot(221);
    plt.imshow(img_show, cmap='magma');
    plt.text(30, 30, "IM", fontdict=font)
    plt.xlabel('Image')
    plt.axis('off')
    if (ground_truth is not None):
        plt.subplot(222);
        plt.axis('off')
        plt.imshow(ground_truth, cmap=new_cmp, interpolation='None')
        plt.text(30, 30, "GT", fontdict=font)
        plt.xlabel('Ground Truth')
    plt.subplot(223);
    plt.axis('off')
    plt.imshow(embedding, interpolation='None')
    plt.subplot(224);
    plt.axis('off')
    plt.imshow(prediction, cmap=new_cmp, interpolation='None')
    plt.text(30, 30, "PRED", fontdict=font)
    plt.xlabel('Prediction')
    plt.tight_layout()
    plt.show()

# TODO --> code repetition in datasets directory!
def decode(filename, one_hot = False, center=False):
    df = pd.read_csv(filename, header=None)
    df_numpy = df.to_numpy()
    d = {}

    if one_hot:
        mask_decoded = []
        for row in df_numpy:
            d['counts'] = ast.literal_eval(row[1])
            d['size'] = ast.literal_eval(row[2])
            mask = rletools.decode(d)  # returns binary mask
            mask_decoded.append(mask)
    else:
        if center:
            mask_decoded = np.zeros(ast.literal_eval(df_numpy[0][2]),
                                    dtype=np.bool)  # obtain size by reading first row of csv file
        else:
            mask_decoded = np.zeros(ast.literal_eval(df_numpy[0][2]),
                                    dtype=np.uint16)  # obtain size by reading first row of csv file
        for row in df_numpy:
            d['counts'] = ast.literal_eval(row[1])
            d['size'] = ast.literal_eval(row[2])
            mask = rletools.decode(d)  # returns binary mask
            y, x = np.where(mask == 1)
            mask_decoded[y, x] = int(row[0])
    return np.asarray(mask_decoded)

def visualize_many_crops(data_dir, project_name, train_val_dir, center, n_images, new_cmp, one_hot=False):
    font = {'family': 'serif',
            'color':  'black',
            'weight': 'bold',
            'size': 16,
            }
    im_filenames = sorted(glob(os.path.join(data_dir, project_name, train_val_dir)+'/images/*.tif'))
    ma_filenames = sorted(glob(os.path.join(data_dir, project_name, train_val_dir)+ '/masks/*')) # `tifs` or `csvs`
    center_filenames = sorted(glob(os.path.join(data_dir, project_name, train_val_dir)+ '/center-'+center+'/*')) # `tifs` or `csvs`
    indices = np.random.randint(0, len(im_filenames), n_images)
    fig = plt.figure(constrained_layout=False, figsize=(16, 10))
    spec = gridspec.GridSpec(ncols=n_images, nrows=3, figure=fig)
    for i, index in enumerate(indices):
        ax0 = fig.add_subplot(spec[0, i])
        im = tifffile.imread(im_filenames[index])
        if im.ndim==2:
            ax0.imshow(im, cmap='magma', interpolation='None')
        else:
            ax0.imshow(im[0], cmap='magma', interpolation='None')
        ax0.axes.get_xaxis().set_visible(False)
        ax0.set_yticklabels([])
        ax0.set_yticks([])
        if i==0:
            ax0.set_ylabel('IM', fontdict=font)
        ax1 = fig.add_subplot(spec[1, i])
        if one_hot:
            if(ma_filenames[index][-3:]=='csv'):
                label = invert_one_hot(decode(ma_filenames[index], one_hot = True))
            else:
                label = invert_one_hot(tifffile.imread(ma_filenames[index]))
        else:
            label, _, _ = relabel_sequential(tifffile.imread(ma_filenames[index]))
        ax1.imshow(label, cmap=new_cmp, interpolation='None')
        ax1.axes.get_xaxis().set_visible(False)
        ax1.set_yticklabels([])
        ax1.set_yticks([])
        if i==0:
            ax1.set_ylabel('MASK', fontdict=font)
        ax2 = fig.add_subplot(spec[2, i])
        if center_filenames[index][-3:]=='csv':
            ax2.imshow(decode(center_filenames[index], center=True), cmap='gray', interpolation='None')
        else:
            ax2.imshow(tifffile.imread(center_filenames[index]), cmap='gray', interpolation='None')
        ax2.axes.get_xaxis().set_visible(False)
        ax2.set_yticklabels([])
        ax2.set_yticks([])
        if i==0:
            ax2.set_ylabel('CENTER', fontdict=font)
        plt.tight_layout(pad=0, h_pad=0)
    plt.show()




def visualize_crop_3d(data_dir, project_name, train_val_dir, center, new_cmp, anisotropy):
    font = {'family': 'serif',
            'color':  'black',
            'weight': 'bold',
            'size': 16,
            }
    im_filenames = sorted(glob(os.path.join(data_dir, project_name, train_val_dir)+'/images/*.tif'))
    ma_filenames = sorted(glob(os.path.join(data_dir, project_name, train_val_dir)+ '/masks/*.tif'))
    center_filenames = sorted(glob(os.path.join(data_dir, project_name, train_val_dir) + '/center-' + center + '/*.tif'))
    index = np.random.randint(0, len(im_filenames), 1)[0]
    fig = plt.figure(constrained_layout=False, figsize=(12, 10))
    spec = gridspec.GridSpec(ncols=3, nrows=3, figure=fig)

    im = tifffile.imread(im_filenames[index])
    label, _, _ = relabel_sequential(tifffile.imread(ma_filenames[index]))
    center_im = tifffile.imread(center_filenames[index])


    im = zoom(im, (anisotropy, 1, 1), order=0)
    # print(np.unique(label))
    label = zoom(label, (anisotropy, 1, 1), order=0)
    # print(np.unique(label))
    center_im = zoom(center_im, (anisotropy, 1, 1), order=0)

    z_mid = im.shape[0]//2
    y_mid = im.shape[1]//2
    x_mid = im.shape[2]//2

    ax0 = fig.add_subplot(spec[0, 0])
    ax0.imshow(im[z_mid, ...], cmap='magma', interpolation='None')
    ax0.set_yticklabels([])
    ax0.set_yticks([])
    ax0.set_xticklabels([])
    ax0.set_xticks([])
    ax0.set_ylabel('IM', fontdict=font)
    ax0.set_xlabel('xy', fontdict=font)
    ax0.xaxis.set_label_position('top')

    ax1 = fig.add_subplot(spec[1, 0])
    ax1.imshow(label[z_mid, ...], cmap=new_cmp, interpolation='None')
    ax1.axes.get_xaxis().set_visible(False)
    ax1.set_yticklabels([])
    ax1.set_yticks([])
    ax1.set_ylabel('MASK', fontdict=font)
    ax2 = fig.add_subplot(spec[2, 0])
    ax2.imshow(center_im[z_mid, ...], cmap='gray', interpolation='None')
    ax2.axes.get_xaxis().set_visible(False)
    ax2.set_yticklabels([])
    ax2.set_yticks([])
    ax2.set_ylabel('CENTER', fontdict=font)

    # use interpolation
    ax6 = fig.add_subplot(spec[0, 1])
    ax6.imshow(im[..., x_mid], cmap='magma', interpolation='None')
    ax6.set_yticklabels([])
    ax6.set_yticks([])
    ax6.set_xticklabels([])
    ax6.set_xticks([])
    ax6.set_xlabel('yz', fontdict=font)
    ax6.xaxis.set_label_position('top')

    ax7 = fig.add_subplot(spec[1, 1])
    ax7.imshow(label[..., x_mid], cmap=new_cmp, interpolation='None')
    ax7.axes.get_xaxis().set_visible(False)
    ax7.set_yticklabels([])
    ax7.set_yticks([])

    ax8 = fig.add_subplot(spec[2, 1])
    ax8.imshow(center_im[..., x_mid], cmap='gray', interpolation='None')
    ax8.axes.get_xaxis().set_visible(False)
    ax8.set_yticklabels([])
    ax8.set_yticks([])



    ax3 = fig.add_subplot(spec[0, 2])
    ax3.imshow(np.transpose(im[:, y_mid, ...]), cmap='magma', interpolation='None')
    ax3.set_yticklabels([])
    ax3.set_yticks([])
    ax3.set_xticklabels([])
    ax3.set_xticks([])
    ax3.set_xlabel('zx', fontdict=font)
    ax3.xaxis.set_label_position('top')

    ax4 = fig.add_subplot(spec[1, 2])
    ax4.imshow(np.transpose(label[:, y_mid, ...]), cmap=new_cmp, interpolation='None')
    ax4.axes.get_xaxis().set_visible(False)
    ax4.set_yticklabels([])
    ax4.set_yticks([])
    ax5 = fig.add_subplot(spec[2, 2])
    ax5.imshow(np.transpose(center_im[:, y_mid, ...]), cmap='gray', interpolation='None')
    ax5.axes.get_xaxis().set_visible(False)
    ax5.set_yticklabels([])
    ax5.set_yticks([])

    plt.tight_layout(pad=0, h_pad=0)


plt.show()