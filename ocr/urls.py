from django.conf.urls import url
from . import views


urlpatterns = [
     url(r'^$', views.UserFormView.as_view(), name='login'),
     url(r'^index/$', views.IndexView.as_view(), name='index'),
     url(r'^analysis/$', views.AnalyseView.as_view(), name='analysis'),
     url(r'^download/(?P<dname>\w+\s{1,1}\w+)/(?P<dnum>[A-Z]\d{4,4}-\d{5,5}-\d{5,5})/$', views.DownloadView.as_view(), name='download'),
     url(r'^test/$', views.PdfView.as_view(), name='pdf'),
]


