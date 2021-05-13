# -*- coding: utf-8 -*-
# @Time    : 2021-04-26 8:48 p.m.
# @Author  : young wang
# @FileName: omega_compare.py
# @Software: PyCharm


'''this script generates images for the figure 3.1 as seen in
the paper. Sparse reconstructions of the same OCT
middle ear image using the same learned dictionary for
various values of the weighting parameter omega'''

import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from sporco.admm import cbpdn
from skimage.morphology import disk
from skimage.morphology import dilation, erosion
from misc import processing,quality,annotation
from skimage import filters

from functools import partial

# Module level constants
eps = 1e-14

if __name__ == '__main__':

    plt.close('all')
    # Customize matplotlib params
    matplotlib.rcParams.update(
        {
            'font.size': 18,
            'text.usetex': False,
            'font.family': 'stixgeneral',
            'mathtext.fontset': 'stix',
        }
    )
    file_name = ['ear']
    # Load the example dataset
    s, D = processing.load_data(file_name[0], decimation_factor=20)

    rvmin = 65  # dB
    vmax = 115  # dB

    s_log = 20 * np.log10(abs(s))

    # l2 norm data and save the scaling factor
    _, snorm = processing.to_l2_normed(s)

    opt_par = cbpdn.ConvBPDN.Options({'FastSolve': True, 'Verbose': False, 'StatusHeader': False,
                                      'MaxMainIter': 20, 'RelStopTol': 5e-5, 'AuxVarObj': True,
                                      'RelaxParam': 1.515, 'AutoRho': {'Enabled': True}})

    # Weigth factor to apply to the fidelity (l2) term in the cost function
    # in regions segmented as containing speckle
    speckle_weight = np.linspace(0.1,1,5)
    lmbda = 0.1

    index = 400 # index A-line
    s_line = abs(snorm[:,index])

    x_line = np.zeros((snorm.shape[0], len(speckle_weight)))
    sparse = np.zeros((snorm.shape[0], snorm.shape[1], len(speckle_weight)))
    sparsity = np.zeros(len(speckle_weight))

    #update opt to include W

    for i in range(len(speckle_weight)):

        x, line = processing.make_sparse_representation(s, D, lmbda, speckle_weight[i],Line=True,index = index )
        x_log = 20 * np.log10(abs(x))
        sparse[:,:,i] = filters.median(x_log, disk(1))
        x_line[:, i] = line

    width, height = (100, 80)
    homogeneous = [[125, 120, width, height]]
    # artifact = [[75, 5, 10, 8]]
    # background = [[425, 250, width - 25, height - 20]]

    fig = plt.figure(constrained_layout=True, figsize=(16, 9))
    gs = fig.add_gridspec(ncols=len(speckle_weight) + 1, nrows=3)

    aspect = s_log.shape[1] / s_log.shape[0]
    ax = fig.add_subplot(gs[0, 0])
    ax.imshow(s_log, 'gray', aspect=aspect, vmax=vmax, vmin=rvmin, interpolation='none')
    ax.set_axis_off()
    ax.set_title('reference', fontname='Arial')
    ax.axvline(x=index, ymin=0.6, ymax=1, linewidth=1, color='orange', linestyle='--')
    ax.axvline(x=index, ymin=0, ymax=0.6, linewidth=1, color='orange')
    for k in range(len(homogeneous)):
        for j in annotation.get_homogeneous(*homogeneous[k]):
            ax.add_patch(j)

    ho_original = quality.ROI(*homogeneous[0], s_log)

    ax = fig.add_subplot(gs[1, 0])
    ax.imshow(ho_original, 'gray', aspect=ho_original.shape[1] / ho_original.shape[0], vmax=vmax, vmin=rvmin)
    ax.set_axis_off()
    ax.annotate('', xy=(72.5, 10), xycoords='data',
                xytext=(60, 5), textcoords='data',
                arrowprops=dict(facecolor='white', shrink=0.05),
                horizontalalignment='right', verticalalignment='top',
                )
    ax.annotate('', xy=(87.5, 55), xycoords='data',
                xytext=(92.5, 70), textcoords='data',
                arrowprops=dict(facecolor='red', shrink=0.05),
                horizontalalignment='right', verticalalignment='top',
                )
    # for k in range(len(artifact)):
    #     for j in annotation.get_artifact(*artifact[k]):
    #         ax.add_patch(j)

    ax = fig.add_subplot(gs[2, 0])
    ax.plot(s_line)
    ax.set_xlabel('axial depth [pixels]', fontname='Arial')
    ax.set_ylabel('normalized \nmagnitude [a.u.]', fontname='Arial', fontsize=20)
    ax.set_ylim(0, np.max(s_line)*1.1)

    temp = np.where(s_log <= rvmin,0,s_log)
    ba_s = quality.ROI(*homogeneous[0], temp)
    ar_s = quality.ROI(*homogeneous[0], temp)

    for i in range(len(speckle_weight)):

        aspect = sparse[:, :, i].shape[1]/sparse[:, :, i].shape[0]
        ax = fig.add_subplot(gs[0, i + 1])
        ax.imshow(sparse[:, :, i], 'gray', aspect=aspect, vmax=vmax, vmin=rvmin)
        ax.axvline(x=index, ymin=0.6, ymax=1, linewidth=1, color='orange', linestyle='--')
        ax.axvline(x=index, ymin=0, ymax=0.6, linewidth=1, color='orange')
        # for k in range(len(background)):
        #     for j in annotation.get_background(*background[k]):
        #         ax.add_patch(j)

        ax.set_title('𝜆 = %.2f \n $\omega$ = %.1f' % (lmbda, speckle_weight[i]))
        ax.set_axis_off()
        for k in range(len(homogeneous)):
            for j in annotation.get_homogeneous(*homogeneous[k]):
                ax.add_patch(j)

        ho_x = quality.ROI(*homogeneous[0], sparse[:, :, i])
        # temp = np.where(sparse[:, :, i] <= rvmin,0,sparse[:, :, i])
        # ba_x = quality.ROI(*background[0], temp)
        # ar_x = quality.ROI(*artifact[0], temp)

        aspect = width / height
        ax = fig.add_subplot(gs[1, i + 1])
        ax.imshow(ho_x, 'gray', aspect=aspect, vmax=vmax, vmin=rvmin)
        ax.annotate('', xy=(72.5, 10), xycoords='data',
                    xytext=(60, 5), textcoords='data',
                    arrowprops=dict(facecolor='white', shrink=0.05),
                    horizontalalignment='right', verticalalignment='top',
                    )
        ax.annotate('', xy=(87.5, 55), xycoords='data',
                    xytext=(92.5, 70), textcoords='data',
                    arrowprops=dict(facecolor='red', shrink=0.05),
                    horizontalalignment='right', verticalalignment='top',
                    )
        # for k in range(len(artifact)):
        #     for j in annotation.get_artifact(*artifact[k]):
        #         ax.add_patch(j)

        ax.set_axis_off()

        ax = fig.add_subplot(gs[2, i + 1])
        ax.plot(x_line[:, i])
        ax.set_yticks([])
        ax.set_ylim(0, np.max(s_line)*1.1)

        ax.set_xlabel('axial depth [pixels]', fontname='Arial')
    plt.show()

