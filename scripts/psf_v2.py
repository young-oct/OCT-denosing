# -*- coding: utf-8 -*-
# @Time    : 2023-08-26 03:52
# @Author  : young wang
# @FileName: psf_v2.py
# @Software: PyCharm

import numpy as np
from scipy.signal import find_peaks
import matplotlib
from matplotlib import pyplot as plt
import pickle
import os
import time
from numpy import linalg as LA
from numpy.fft import fft, ifft
from scipy.signal import hilbert, firwin, filtfilt

def find_variable_name(variable):
    for name, value in globals().items():
        if value is variable:
            return name


def locatepeaks(D, mask_size=10, include_range=15, dB=True):
    name = find_variable_name(D)

    D = np.ravel(D)
    print(name)
    D_log = 20 * np.log10(abs(D))
    D_log = D_log - np.min(D_log)

    # use find_peaks to get the indices of the peaks

    indices, _ = find_peaks(D_log, height=np.median(D_log))

    # use find_peaks to get the indices of the peaks
    # get the highest peak index and value
    highest_peak_index = indices[np.argmax(D_log[indices])]
    highest_peak_value = D_log[highest_peak_index]
    print("Highest peak is at index", highest_peak_index, \
          "with value", highest_peak_value)

    # create a mask for peaks within x samples of the highest peak
    mask = (indices >= highest_peak_index - mask_size) & (indices <= highest_peak_index + mask_size)
    # get the peaks within 20 samples of the highest peak
    nearby_peaks_indices = indices[mask]
    nearby_peaks_values = D_log[nearby_peaks_indices]

    # sort the nearby peaks by value, in descending order
    nearby_sorted_indices = nearby_peaks_indices[np.argsort(-nearby_peaks_values)]

    # find the second highest peak that is different from the highest peak
    for index in nearby_sorted_indices:
        if D_log[index] < highest_peak_value:
            second_highest_peak_index = index
            second_highest_peak_value = D_log[index]
            break
    print("Second highest peak within {} samples is at index "
          "{} with value {}".format(mask_size,
                                    second_highest_peak_index,
                                    second_highest_peak_value))

    # create a mask that excludes the range around the peak
    mask = np.ones(D_log.shape, dtype=bool)

    if dB:
        # (1) average on dB scale
        mask[
        max(0, highest_peak_index - include_range): min(len(D_log), highest_peak_index + include_range + 1)] = False

        # (1) create a new array excluding the range around the main peak
        arr_excluding_range = D_log[mask]

        # calculate the average of the new array
        avg_excluding_range = np.mean(arr_excluding_range)
    else:
        mask[
        max(0, highest_peak_index - include_range): min(len(D_log), highest_peak_index + include_range + 1)] = False

        # (1) create a new array excluding the range around the main peak
        arr_excluding_range = D[mask]

        # calculate the average of the new array
        avg_excluding_range = 20 * np.log10(abs(np.mean(arr_excluding_range)))

    #
    print(f"The average value excluding the main peak is {avg_excluding_range}")
    print(f"The dynamic range: PSF-background {highest_peak_value - avg_excluding_range}")

    return D_log, highest_peak_index, \
           highest_peak_value, second_highest_peak_index, \
           second_highest_peak_value, avg_excluding_range

if __name__ == '__main__':
    rvmin, vmax = 5, 55  # dB

    t = time.process_time()

    plt.close('all')
    # Customize matplotlib params
    matplotlib.rcParams.update(
        {
            'font.size': 16,
            'text.usetex': False,
            'font.family': 'stixgeneral',
            'mathtext.fontset': 'stix',
        }
    )

    with open('../data/mirror_clean.npy', 'rb') as f:
        clean = np.load(f)

    sg = np.mean(np.mean(clean[:, :, :], axis=0), axis=0)
    b = firwin(401, 0.05, pass_zero='highpass')
    sg = filtfilt(b, 1, sg)

    temp_aline = ifft(sg) / LA.norm(ifft(sg))
    peak_aline = np.argmax(np.abs(temp_aline))
    A_line = temp_aline[int(peak_aline-165):int(peak_aline+165)]
    D0 = A_line[:,np.newaxis]

    file_name = ['nail']
    D_PATH = '../Data/PSF/' + file_name[0]
    #
    with open(D_PATH, 'rb') as af:
        D1 = pickle.load(af)
        af.close()

    fig, ax = plt.subplots(2, 3, figsize=(16, 9))

    ax[0, 0].plot(abs(D0))
    ax[0, 0].set_title('measured PSF')
    ax[0, 0].set_ylabel('magnitude [a.u.]')

    ax[0, 1].plot(abs(D1))
    ax[0, 1].set_title('learned PSF')

    include_range, exclude_range = 20, 100

    D0_log, D0_highest_peak_index, D0_highest_peak_value, \
    D0_second_highest_peak_index, D0_second_highest_peak_value, \
    D0_avg_excluding_range = locatepeaks(D0, include_range, exclude_range, dB=True)

    ax[1, 0].plot(D0_log)
    ax[1, 0].set_ylabel('20 log(magnitude) [db]')
    ax[1, 0].set_xlabel('axial depth [pixels]')

    x_indice, offset = D0_second_highest_peak_index, 10
    x_left = x_indice - offset
    x_right = x_indice + offset
    #
    ax[1, 0].hlines(y=D0_highest_peak_value, xmin=x_left, xmax=x_right, colors='r', linestyle='dotted', linewidth=1)
    ax[1, 0].hlines(y=D0_second_highest_peak_value, xmin=x_left, xmax=x_right, colors='r', linestyle='dotted',
                    linewidth=1)

    ax[1, 0].annotate("",
                      xy=(x_indice - offset / 2, D0_second_highest_peak_value), xycoords='data',
                      xytext=(x_indice - offset / 2, D0_highest_peak_value), textcoords='data',
                      arrowprops=dict(arrowstyle="<->",
                                      connectionstyle="arc3", color='r', lw=1),
                      )
    ax[1, 0].text(x_left - offset *1.5 ,
                  D0_avg_excluding_range + (D0_highest_peak_value - D0_second_highest_peak_value) *0.8,
                  'PSF - ''sidelobe: %.2f dB' % (D0_highest_peak_value - D0_second_highest_peak_value),
                  fontsize=8.5, fontweight='bold', rotation='vertical')

    ax[1, 0].hlines(y=D0_highest_peak_value, xmin=x_left + offset * 10, xmax=x_right + offset * 12, colors='r',
                    linestyle='dotted',
                    linewidth=1)
    ax[1, 0].hlines(y=D0_avg_excluding_range, xmin=x_left + offset * 10, xmax=x_right + offset * 12, colors='r',
                    linestyle='dotted',
                    linewidth=1)

    ax[1, 0].annotate("",
                      xy=(x_right + offset * 10, D0_avg_excluding_range), xycoords='data',
                      xytext=(x_right + offset * 10, D0_highest_peak_value), textcoords='data',
                      arrowprops=dict(arrowstyle="<->",
                                      connectionstyle="arc3", color='r', lw=1),
                      )
    ax[1, 0].text(x_right + offset * 8.5, D0_avg_excluding_range + offset,
                  'PSF - ''background: %.2f dB' % (D0_highest_peak_value - D0_avg_excluding_range),
                  fontsize=8.5, fontweight='bold', rotation='vertical')

    D1_log, D1_highest_peak_index, D1_highest_peak_value, \
    D1_second_highest_peak_index, D1_second_highest_peak_value, \
    D1_avg_excluding_range = locatepeaks(D1, include_range, exclude_range, dB=True)

    ax[1, 1].plot(D1_log)
    ax[1, 1].set_xlabel('axial depth [pixels]')

    x_indice, offset = D1_second_highest_peak_index, 10
    x_left = x_indice - offset
    x_right = x_indice + offset
    #
    ax[1, 1].hlines(y=D1_highest_peak_value, xmin=x_left, xmax=x_right, colors='r', linestyle='dotted', linewidth=1)
    ax[1, 1].hlines(y=D1_second_highest_peak_value, xmin=x_left, xmax=x_right, colors='r', linestyle='dotted',
                    linewidth=1)

    ax[1, 1].annotate("",
                      xy=(x_indice, D1_second_highest_peak_value), xycoords='data',
                      xytext=(x_indice, D1_highest_peak_value), textcoords='data',
                      arrowprops=dict(arrowstyle="<->",
                                      connectionstyle="arc3", color='r', lw=1),
                      )
    ax[1, 1].text(x_left - 2 * offset,
                  D1_avg_excluding_range + offset * 2.5,
                  'PSF - ''sidelobe: %.2f dB' % (D1_highest_peak_value - D1_second_highest_peak_value),
                  fontsize=8.5, fontweight='bold', rotation='vertical')

    ax[1, 1].hlines(y=D1_highest_peak_value, xmin=x_left + offset * 10, xmax=x_right + offset * 12, colors='r',
                    linestyle='dotted',
                    linewidth=1)
    ax[1, 1].hlines(y=D1_avg_excluding_range, xmin=x_left + offset * 10, xmax=x_right + offset * 12, colors='r',
                    linestyle='dotted',
                    linewidth=1)

    ax[1, 1].annotate("",
                      xy=(x_right + offset * 10, D1_avg_excluding_range), xycoords='data',
                      xytext=(x_right + offset * 10, D1_highest_peak_value), textcoords='data',
                      arrowprops=dict(arrowstyle="<->",
                                      connectionstyle="arc3", color='r', lw=1),
                      )
    ax[1, 1].text(x_right + offset * 8.5, D1_avg_excluding_range + offset,
                  'PSF - ''background: %.2f dB' % (D1_highest_peak_value - D1_avg_excluding_range),
                  fontsize=8.5, fontweight='bold', rotation='vertical')

    ax[0, 2].plot(abs(D0), label='measured PSF')
    ax[0, 2].plot(abs(D1), label='learned PSF')
    ax[0, 2].legend(fontsize=14)

    ax[0, 2].set_title('measured & learned PSF')

    ax[1, 2].plot(D0_log, linestyle='--', label='measured PSF')
    ax[1, 2].plot(D1_log, label='learned PSF')
    ax[1, 2].legend(fontsize=14)
    ax[1, 2].set_xlabel('axial depth [pixels]')

    plt.tight_layout()

    desktop_path = os.path.join(os.getenv('HOME'), 'Desktop')
    folder_path = os.path.join(desktop_path, 'Master/Thesis/Figure/Chapter 2/2.15 PSF comparison')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, 'PSF comparison.pdf')

    plt.savefig(file_path, dpi=600,
                format='pdf',
                bbox_inches='tight', pad_inches=0,
                facecolor='auto', edgecolor='auto')

    plt.show()

    ## only the measured

    fig, ax = plt.subplots(1, 1, figsize=(16, 9))
    x_indice, offset = D0_second_highest_peak_index, 10
    x_left = x_indice - offset
    x_right = x_indice + offset

    ax.plot(D0_log)

    ax.hlines(y=D0_highest_peak_value, xmin=x_left, xmax=x_right, colors='r', linestyle='dotted', linewidth=1)
    ax.hlines(y=D0_second_highest_peak_value, xmin=x_left, xmax=x_right, colors='r', linestyle='dotted',
                    linewidth=1)

    ax.annotate("",
                      xy=(x_indice - offset / 2, D0_second_highest_peak_value), xycoords='data',
                      xytext=(x_indice - offset / 2, D0_highest_peak_value), textcoords='data',
                      arrowprops=dict(arrowstyle="<->",
                                      connectionstyle="arc3", color='r', lw=1),
                      )
    ax.text(x_left - offset / 2,
                  D0_avg_excluding_range + (D0_highest_peak_value - D0_second_highest_peak_value) / 2,
                  'PSF - ''sidelobe: %.2f dB' % (D0_highest_peak_value - D0_second_highest_peak_value),
                  fontsize=8.5, fontweight='bold', rotation='vertical')

    ax.hlines(y=D0_highest_peak_value, xmin=x_left + offset * 10, xmax=x_right + offset * 12, colors='r',
                    linestyle='dotted',
                    linewidth=1)
    ax.hlines(y=D0_avg_excluding_range, xmin=x_left + offset * 10, xmax=x_right + offset * 12, colors='r',
                    linestyle='dotted',
                    linewidth=1)

    ax.annotate("",
                      xy=(x_right + offset * 10, D0_avg_excluding_range), xycoords='data',
                      xytext=(x_right + offset * 10, D0_highest_peak_value), textcoords='data',
                      arrowprops=dict(arrowstyle="<->",
                                      connectionstyle="arc3", color='r', lw=1),
                      )
    ax.text(x_right + offset * 8.5, D0_avg_excluding_range + offset,
                  'PSF - ''background: %.2f dB' % (D0_highest_peak_value - D0_avg_excluding_range),
                  fontsize=8.5, fontweight='bold', rotation='vertical')

    ax.set_ylabel('20 log(magnitude) [dB]', fontweight='bold')
    ax.set_xlabel('depth [pixels]', fontweight='bold')
    ax.set_title('averaged axial point spread function (PSF)', fontweight='bold')
    ax.minorticks_on()
    ax.tick_params(which='minor', width=2)  # Set the width of the minor ticks to 1 (you can adjust this value)

    plt.tight_layout()

    folder_path = os.path.join(desktop_path, 'Master/Thesis/Figure/Chapter 2/2.16 PSF setup')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, 'measured PSF.pdf')
    plt.savefig(file_path, dpi=600,
                format='pdf',
                bbox_inches='tight', pad_inches=0,
                facecolor='auto', edgecolor='auto')

    plt.show()
    plt.close(fig)


