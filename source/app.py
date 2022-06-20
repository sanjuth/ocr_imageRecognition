from IPython.display import Image
from matplotlib import pyplot as plt
import app
import io
import os
import cv2
import warnings
import pandasql as ps
import pandas as pd
import numpy as np
import re
import cv2
import pytesseract
from pytesseract import Output
import aspose.words as aw
from flask import Flask, render_template, request
app = Flask(__name__)

# @app.route('/home')
# def index():
#     return render_template('/index.html')


def findHorizontalLines(img):
    # img = cv2.imread(img)

    # convert image to greyscale
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # set threshold to remove background noise
    thresh = cv2.threshold(
        img, 30, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # define rectangle structure (line) to look for: width 100, hight 1. This is a
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (200, 1))

    # Find horizontal lines
    lineLocations = cv2.morphologyEx(
        thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

    return lineLocations

def pageSegmentation1(img, w, df_SegmentLocations):
    # img = cv2.imread(img) 
    im2 = img.copy()
    segments = []

    for i in range(len(df_SegmentLocations)):
        y = df_SegmentLocations['SegmentStart'][i]
        h = df_SegmentLocations['Height'][i]

        cropped = im2[y:y + h, 0:w] 
        segments.append(cropped)
        plt.figure(figsize=(8,8))
        plt.imshow(cropped)
        plt.title(str(i+1))        

    return segments

def extractTextFromImg(segment):
    text = pytesseract.image_to_string(segment, lang='eng')         
    text = text.encode("gbk", 'ignore').decode("gbk", "ignore")
        
    return text




@app.route('/')
def login():
    return render_template('login.html')

login_cred={"abcd":"1234","xyz":"abc123"}
@app.route('/', methods=['POST'])
def check():
    uname=request.form['uname']
    password=request.form['password']
    if uname in login_cred and login_cred[uname]==password:
        return render_template('index.html')
    return render_template('login.html')


@app.route("/upload", methods=['GET', 'POST'])
def ocr():
    if request.method == 'POST':
        print("jojo")
        # img = request.files.get('img', '')
        img = request.files['img']
        img=np.array(img)
        print(img)
        # img=cv2.imread(img)
        gvar=img
        lineLocations = findHorizontalLines(img)

        plt.figure(figsize=(24,24))
        # plt.imshow(lineLocations, cmap='Greys')
        df_lineLocations = pd.DataFrame(lineLocations.sum(axis=1)).reset_index()
        df_lineLocations.columns = ['rowLoc', 'LineLength']
        df_lineLocations[df_lineLocations['LineLength'] > 0]
        df_lineLocations['line'] = 0
        df_lineLocations['line'][df_lineLocations['LineLength'] > 100] = 1

        df_lineLocations['cumSum'] = df_lineLocations['line'].cumsum()
        df_lineLocations.head()
        query = '''
        select row_number() over (order by cumSum) as SegmentOrder
        , min(rowLoc) as SegmentStart
        , max(rowLoc) - min(rowLoc) as Height
        from df_lineLocations
        where line = 0
        --and CumSum !=0
        group by cumSum
        '''
        df_SegmentLocations  = ps.sqldf(query, locals())
        w = lineLocations.shape[1]
        segments = pageSegmentation1(img, w, df_SegmentLocations)
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
        doc = aw.Document()
        builder = aw.DocumentBuilder(doc)
        for i in segments:
            text = extractTextFromImg(i)
            builder.write(text)

    
    return 'uploaded'

global gvar
# if __name__=='__main__':
app.run(debug=True)
