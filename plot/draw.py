# -*- coding=utf-8 -*-
import numpy as np
import matplotlib

import matplotlib.pyplot as plt

def draw_curve(x, y, xlabel, ylabel, title, filename):
    '''画出价格走势曲线'''
    plt.title(title)# give plot a title
    plt.xlabel(xlabel)# make axis labels
    plt.ylabel(ylabel)
    plt.plot(x, y, color='r')
    plt.legend(loc='upper left')
    plt.savefig(filename, format='png')

