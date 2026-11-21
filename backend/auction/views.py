
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import RFQ
from .serializers import RFQCreateSerializer, BidInputSerializer, rfq_summary, rfq_detail
from .services import place_bid
 
 
@api_view(["GET", "POST"])
def rfq_list(request):
    if request.method == "POST":
        s = RFQCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data, status=201)
    return Response([rfq_summary(r) for r in RFQ.objects.order_by("-created_at")])
 
 
@api_view(["GET"])
def rfq_detail_view(request, pk):
    return Response(rfq_detail(get_object_or_404(RFQ, pk=pk)))
 
 
@api_view(["POST"])
def submit_bid(request, pk):
    get_object_or_404(RFQ, pk=pk)
    s = BidInputSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    d = dict(s.validated_data)
    place_bid(pk, d.pop("supplier"), d)
    return Response(rfq_detail(RFQ.objects.get(pk=pk)), status=201)
 