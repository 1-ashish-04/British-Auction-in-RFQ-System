
from rest_framework import serializers
from django.utils import timezone
from .models import RFQ, Bid
from .services import ranking
 
 
class RFQCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFQ
        fields = ["id", "reference_id", "name", "bid_start", "original_close", "forced_close",
                  "pickup_date", "trigger_window_min", "extension_min", "trigger_type"]
        read_only_fields = ["id"]
 
    def validate(self, d):
        if d["forced_close"] <= d["original_close"]:
            raise serializers.ValidationError("Forced close must be later than bid close.")
        if d["original_close"] <= d["bid_start"]:
            raise serializers.ValidationError("Bid close must be after bid start.")
        if d["extension_min"] <= 0 or d["trigger_window_min"] <= 0:
            raise serializers.ValidationError("X and Y must be positive.")
        return d
 
    def create(self, d):
        return RFQ.objects.create(bid_close=d["original_close"], **d)
 
 
class BidSerializer(serializers.ModelSerializer):
    supplier = serializers.CharField(source="supplier.name", read_only=True)
 
    class Meta:
        model = Bid
        fields = ["id", "supplier", "carrier_name", "freight", "origin_charges",
                  "destination_charges", "total", "transit_days", "validity_days", "created_at"]
 
 
class BidInputSerializer(serializers.Serializer):
    supplier = serializers.CharField()
    carrier_name = serializers.CharField()
    freight = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    origin_charges = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    destination_charges = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    transit_days = serializers.IntegerField(min_value=1)
    validity_days = serializers.IntegerField(min_value=1)
 
 
def rfq_summary(rfq):
    r = ranking(rfq)
    return {"id": rfq.id, "reference_id": rfq.reference_id, "name": rfq.name,
            "current_lowest_bid": r[0][1] if r else None,
            "bid_close": rfq.bid_close, "forced_close": rfq.forced_close,
            "status": rfq.status(timezone.now())}
 
 
def rfq_detail(rfq):
    d = rfq_summary(rfq)
    ranks = {sid: i + 1 for i, (sid, _) in enumerate(ranking(rfq))}
    bids = rfq.bids.select_related("supplier").order_by("total", "created_at")
    d.update({
        "bid_start": rfq.bid_start, "original_close": rfq.original_close,
        "pickup_date": rfq.pickup_date,
        "config": {"trigger_window_min": rfq.trigger_window_min,
                   "extension_min": rfq.extension_min, "trigger_type": rfq.trigger_type},
        "bids": [{**BidSerializer(b).data, "rank": f"L{ranks[b.supplier_id]}"} for b in bids],
        "logs": [{"event_type": l.event_type, "message": l.message, "old_close": l.old_close,
                  "new_close": l.new_close, "created_at": l.created_at} for l in rfq.logs.all()],
    })
    return d
 