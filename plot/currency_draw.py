# -*- encoding=utf-8 -*-

import draw
import pandas as pd
import argparse

def draw_currency(curfile, savefile):
    curnp = pd.read_csv(curfile).values
    x = range(len(curnp))
    y = [float(curnp[i][5]) for i in range(len(curnp))]
    draw.draw_curve(x, y, 'time', 'prices', 'prices trend', savefile)

def main(args):
    curfile = args.curfile
    savefile = args.savefile
    draw_currency(curfile, savefile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="", description="help instruction")
    parser.add_argument("-curfile", default="AUC", help="the input data path.")
    parser.add_argument("-savefile", default="AUC", help="the input data path.")
    args = parser.parse_args()
    
    main(args)
