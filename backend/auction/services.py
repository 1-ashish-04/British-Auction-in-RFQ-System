
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import RFQ, Bid, ActivityLog, Supplier
 
 
def ranking(rfq):
    """[(supplier_id, best_total)] sorted L1..Ln. Ties: earlier bid wins."""
    best = {}
    for b in rfq.bids.order_by("created_at", "id"):
        cur = best.get(b.supplier_id)
        if cur is None or b.total < cur:
            best[b.supplier_id] = b.total
    return sorted(best.items(), key=lambda kv: kv[1])  # stable: earlier supplier first on ties
 
 
def _ids(r):
    return [s for s, _ in r]
 
 
@transaction.atomic
def place_bid(rfq_id, supplier_name, data):
    rfq = RFQ.objects.select_for_update().get(pk=rfq_id)   # serialises concurrent bids
    now = timezone.now()                                    # server time only
 
    if now < rfq.bid_start:
        raise ValidationError("Auction has not started.")
    if now >= rfq.bid_close:
        raise ValidationError("Auction is closed.")
 
    supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
    total = data["freight"] + data["origin_charges"] + data["destination_charges"]
 
    prev = dict(ranking(rfq)).get(supplier.id)
    if prev is not None and total >= prev:
        raise ValidationError("New bid must be lower than your previous best bid.")
 
    before = ranking(rfq)
    bid = Bid.objects.create(rfq=rfq, supplier=supplier, total=total, created_at=now, **data)
    after = ranking(rfq)
 
    ActivityLog.objects.create(rfq=rfq, event_type="BID", created_at=now,
                               message=f"{supplier.name} bid {total}")
 
    window_start = rfq.bid_close - timedelta(minutes=rfq.trigger_window_min)
    in_window = window_start <= now < rfq.bid_close
 
    reason = None
    if in_window:
        if rfq.trigger_type == RFQ.ANY_BID:
            reason = f"Bid received in last {rfq.trigger_window_min} min"
        elif rfq.trigger_type == RFQ.RANK_CHANGE and before and _ids(before) != _ids(after):
            reason = f"Supplier rank changed in last {rfq.trigger_window_min} min"
        elif rfq.trigger_type == RFQ.L1_CHANGE and _ids(before)[:1] != _ids(after)[:1]:
            reason = f"L1 changed in last {rfq.trigger_window_min} min"
 
    if reason:
        new_close = min(rfq.bid_close + timedelta(minutes=rfq.extension_min), rfq.forced_close)
        if new_close > rfq.bid_close:
            capped = " (capped at forced close)" if new_close == rfq.forced_close else ""
            ActivityLog.objects.create(rfq=rfq, event_type="EXTENSION", created_at=now,
                                       old_close=rfq.bid_close, new_close=new_close,
                                       message=f"Extended: {reason}{capped}")
            rfq.bid_close = new_close
            rfq.save(update_fields=["bid_close"])
    return bid
 