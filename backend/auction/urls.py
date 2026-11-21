
from django.urls import path
from . import views
 
urlpatterns = [
    path("rfqs/", views.rfq_list),
    path("rfqs/<int:pk>/", views.rfq_detail_view),
    path("rfqs/<int:pk>/bids/", views.submit_bid),
]
 