from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import authenticate, login
from .forms import UserForm, UploadForm, AnalyseForm, DownloadForm
from .models import PictureModel
from django.http import HttpResponse
from django.utils.encoding import smart_str
import numpy as np
import pytesseract
import cv2, os, re
import mimetypes
from wand.image import Image
from wand.color import Color
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader
from zipfile import ZipFile
from PIL import Image as PImage, ImageFilter


class UserFormView(View):
    form_class = UserForm
    template_name = 'ocr/login.html'

    # display blank form / registration
    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name)

    # process form data
    def post(self, request):

        form = self.form_class(request.POST)

        # # cleaned (normalized) data
        # username = form.cleaned_data["username"]
        # password = form.cleaned_data["password"]

        username = request.POST['username']
        password = request.POST['password']

        # return User objects if credentials are correct
        # check the user is available
        user = authenticate(username=username, password=password)

        # if user is valid, login user account
        if user is not None:
            if user.is_active:
                # session expiry
                # request.session.set_expiry(30)
                login(request, user)
                # get the user name
                # request.user.username
                return redirect('ocr:index')

        # if existing the problems, return a error message
        return render(request, 'ocr/error.html', {"msg": "Information is not correct"})


class IndexView(View):
    username = ''
    form_class = UploadForm

    def get(self, request):
        if request.user.is_authenticated():
            self.username = request.user.username
            form = self.form_class(None)
            return render(request, 'ocr/index.html', {"username": self.username, "form": form})
        else:
            return render(request, 'ocr/login.html')

    def post(self, request):
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            pmodel = PictureModel()
            pmodel.picture = form.cleaned_data['picture']
            pmodel.save()
            # add analysis code
            purl = str(pmodel.picture.url)
            dnum, dname, rstr, rd = ImageOcr(purl)

            return render(request, 'ocr/analysis.html',
                          {"username": self.username, "pmodel": pmodel, "dname": dname, "dnum": dnum, "rstr": rstr, "rd": rd})


class AnalyseView(View):
    username = ''

    def get(self, request):
        if request.user.is_authenticated():
            self.username = request.user.username
            # form = self.form_class(None)
            return render(request, 'ocr/analysis.html', {"username": self.username})
        else:
            return render(request, 'ocr/login.html')

    def post(self, request):
        form = AnalyseForm(request.POST)
        if form.is_valid():
            dname = form.cleaned_data['dname']
            dnum = form.cleaned_data['dnum']
            form = DownloadForm
            # return render(request, 'ocr/download.html', {"username": self.username, "dname": dname, "dnum": dnum, 'form': form})
            return redirect("ocr:download", dname=dname, dnum=dnum)
        else:
            return render(request, 'ocr/error.html', {'msg': 'download fail'})


class DownloadView(View):
    username = ''

    def get(self, request, dname, dnum):
        if request.user.is_authenticated():
            self.username = request.user.username
            form = DownloadForm
            return render(request, 'ocr/download.html',
                          {'username': self.username, "dname": dname, "dnum": dnum, 'form': form})
        else:
            return render(request, 'ocr/login.html')

    def post(self, request, dname, dnum):

        form = DownloadForm(request.POST)
        if form.is_valid():
            file_format = form.cleaned_data['file_format']
            file_name = form.cleaned_data['file_name']
            CreatePDF(file_name, file_format, dname, dnum)
            if file_format == 'pdf':
                CompressFiles(file_format, file_name)
                fsock = open('media/files/%s.zip' % smart_str(file_name), 'rb')
                # wrapper = FileWrapper(fsock)
                content_type = mimetypes.guess_type('media/files/%s.zip' % smart_str(file_name))[0]
                response = HttpResponse(fsock, content_type=content_type)
                response['Content-Length'] = os.path.getsize('media/files/%s.zip' % smart_str(file_name))
                response['Content-Disposition'] = "attachment; filename=%s.zip" % smart_str(file_name)
                fsock.close()
                return response
            else:
                Pdf2Image(file_format, file_name)
                CompressFiles(file_format, file_name)
                fsock = open('media/files/%s.zip' % smart_str(file_name), 'rb')
                # wrapper = FileWrapper(fsock)
                content_type = mimetypes.guess_type('media/files/%s.zip' % smart_str(file_name))[0]
                response = HttpResponse(fsock, content_type=content_type)
                response['Content-Length'] = os.path.getsize('media/files/%s.zip' % smart_str(file_name))
                response['Content-Disposition'] = "attachment; filename=%s.zip" % smart_str(file_name)
                fsock.close()
                return response
        else:
            return render(request, 'ocr/error.html', {'msg': 'download fail'})


def CreatePDF(fname, fformat, dname, dnum):
    c = canvas.Canvas("media/files/cover.pdf")
    c.setFont('Helvetica-Bold', 14)
    c.drawString(150, 644, dname)
    c.drawString(180, 627, dnum)
    c.showPage()
    c.save()

    c1 = canvas.Canvas("media/files/cover1.pdf")
    c1.setFont('Helvetica-Bold', 14)
    c1.drawString(163, 628, dname)
    c1.drawString(192, 611, dnum)
    c1.showPage()
    c1.save()

    # merge pdf
    output1 = PdfFileWriter()
    output2 = PdfFileWriter()
    output3 = PdfFileWriter()
    output4 = PdfFileWriter()

    ipdf1 = PdfFileReader(open('media/files/ip1.pdf', 'rb'))
    ipdf2 = PdfFileReader(open('media/files/ip2.pdf', 'rb'))
    ipdf3 = PdfFileReader(open('media/files/ip3.pdf', 'rb'))
    ipdf4 = PdfFileReader(open('media/files/ip4.pdf', 'rb'))

    wpdf = PdfFileReader(open('media/files/cover.pdf', 'rb'))
    wpdf1 = PdfFileReader(open('media/files/cover1.pdf', 'rb'))
    watermark1 = wpdf1.getPage(0)
    watermark = wpdf.getPage(0)

    # ip1
    for i in range(ipdf1.getNumPages()):
        page = ipdf1.getPage(i)
        page.mergePage(watermark1)
        output1.addPage(page)

    with open('media/files/%s-1.pdf' % smart_str(fname), 'wb') as f:
        output1.write(f)

    # ip2
    for i in range(ipdf2.getNumPages()):
        page = ipdf2.getPage(i)
        page.mergePage(watermark)
        output2.addPage(page)

    with open('media/files/%s-2.pdf' % smart_str(fname), 'wb') as f:
        output2.write(f)

    # ip3
    for i in range(ipdf3.getNumPages()):
        page = ipdf3.getPage(i)
        page.mergePage(watermark)
        output3.addPage(page)

    with open('media/files/%s-3.pdf' % smart_str(fname), 'wb') as f:
        output3.write(f)

    # ip4
    for i in range(ipdf4.getNumPages()):
        page = ipdf4.getPage(i)
        page.mergePage(watermark)
        output4.addPage(page)

    with open('media/files/%s-4.pdf' % smart_str(fname), 'wb') as f:
        output4.write(f)


def CompressFiles(fformat, fname):
    with ZipFile('media/files/%s.zip' % smart_str(fname), 'w') as myzip:
        myzip.write('media/files/%s-1.%s' % (smart_str(fname), smart_str(fformat)))
        myzip.write('media/files/%s-2.%s' % (smart_str(fname), smart_str(fformat)))
        myzip.write('media/files/%s-3.%s' % (smart_str(fname), smart_str(fformat)))
        myzip.write('media/files/%s-4.%s' % (smart_str(fname), smart_str(fformat)))
        myzip.close()


def Pdf2Image(fformat, fname):
    with Image(filename="media/files/%s-1.pdf[0]" % smart_str(fname)) as img:
        img.background_color = Color("white")
        img.alpha_channel = 'remove'
        img.format = fformat
        img.save(filename="media/files/%s-1.%s" % (smart_str(fname), smart_str(fformat)))

    with Image(filename="media/files/%s-2.pdf[0]" % smart_str(fname)) as img:
        img.background_color = Color("white")
        img.alpha_channel = 'remove'
        img.format = fformat
        img.save(filename="media/files/%s-2.%s" % (smart_str(fname), smart_str(fformat)))

    with Image(filename="media/files/%s-3.pdf[0]" % smart_str(fname)) as img:
        img.background_color = Color("white")
        img.alpha_channel = 'remove'
        img.format = fformat
        img.save(filename="media/files/%s-3.%s" % (smart_str(fname), smart_str(fformat)))

    with Image(filename="media/files/%s-4.pdf[0]" % smart_str(fname)) as img:
        img.background_color = Color("white")
        img.alpha_channel = 'remove'
        img.format = fformat
        img.save(filename="media/files/%s-4.%s" % (smart_str(fname), smart_str(fformat)))


class PdfView(View):
    def get(self, request):
        return render(request, 'ocr/test.html')


def ImageOcr(purl):
    a = 0.318
    b = 0.185
    c = 0.630
    d = 0.907

    purl = purl[1:]
    im = ''

    if purl[-4:] == ".pdf" or purl[-4:] == ".PDF":
        with Image(filename="%s[0]" % smart_str(str(purl))) as img:
            img.background_color = Color("white")
            img.alpha_channel = 'remove'
            img.format = 'jpg'
            img.save(filename="media/media/pimg.jpg")
            im = cv2.imread('media/media/pimg.jpg')

    else:
        im = cv2.imread(purl)

    print(purl)
    # crop image
    size = im.shape
    hei = size[0]
    wid = size[1]

    crop_im = im[int(b * hei):int(c * hei), int(a * wid):int(d * wid)]
    crop_im = crop_im + 20

    # # Histogram Equalization
    # he_img = cv2.equalizeHist(crop_im)
    # he_res = np.hstack((crop_im, he_img))
    # cv2.imwrite('he_image.jpg', he_res)




    hsv = cv2.cvtColor(crop_im, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    print(v[2][4])
    value = 130 - v[0][0]
    if value > 0:
        hsv[:, :, 2] += value
        crop_im = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    # cv2.imwrite("image_processed.jpg", crop_im)



    crop_im = cv2.GaussianBlur(crop_im, (5, 5), 0)

    gray_im = cv2.cvtColor(crop_im, cv2.COLOR_BGR2GRAY)


    # gray_im = cv2.adaptiveThreshold(gray_im, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 115, 1)
    ret, gray_im = cv2.threshold(gray_im, 115, 255, cv2.THRESH_BINARY)



    # dilation and erosion
    kernel = np.ones((2, 2), np.uint8)

    gray_im = cv2.erode(gray_im, kernel, iterations=1)
    gray_im = cv2.dilate(gray_im, kernel, iterations=1)

    cv2.imwrite('media/media/g_img.jpg', gray_im)


    # im = Image.open("g_img.jpg")
    # im.save("g_img1.jpg", dpi=(400,400))


    ims = PImage.open('media/media/g_img.jpg')
    ims = ims.filter(ImageFilter.SHARPEN)
    text = pytesseract.image_to_string(ims)
    patern = 'QWERTYUIOPASDFGHJKLZXCVBNM,1234567890'
    text = list(text)
    for c in range(len(text)):
        if text[c] not in patern:
            text[c] = ' '

    text = ''.join(str(e) for e in text)

    m = re.findall(r'\s{1,1}[A-Z]{1,1}\d{4,4}\s{1,1}', text)
    n = re.findall(r'\s{1,1}\d{5,5}\s{1,1}', text)
    rstr = re.findall(r'\s{1,1}[A-Z]+\s{1,1}', text)

    p = re.findall(r'[M]\s+\w+\s?[,]?\s?\w+\s+', text)
    p = str(p)
    p = p.replace("M", " ")

    p = re.findall(r'\w+', p)
    if len(m) >= 1 and len(n) >= 2:
        dnum = "%s-%s-%s" % (str(m[0]).strip(), str(n[0]).strip(), str(n[1]).strip())


    else:
        dnum = ''

    if len(p) >= 2:
        dname = "%s %s" % (p[1], p[0])

    else:
        dname = ''

    rd = m + n
    print(m)
    print(n)
    print(text)
    return dnum, dname, rstr, rd
