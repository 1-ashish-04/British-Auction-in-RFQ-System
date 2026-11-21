
from django.db import models
from django.db.models import F
 
 
class Supplier(models.Model):
    name = models.CharField(max_length=120, unique=True)
 
    def __str__(self):
        return self.name
 
 
class RFQ(models.Model):
    ANY_BID, RANK_CHANGE, L1_CHANGE = "ANY_BID", "ANY_RANK_CHANGE", "L1_CHANGE"
    TRIGGERS = [(ANY_BID, "Bid received in last X min"),
                (RANK_CHANGE, "Any supplier rank change in last X min"),
                (L1_CHANGE, "L1 change in last X min")]
 
    reference_id = models.CharField(max_length=60, unique=True)
    name = models.CharField(max_length=200)
    bid_start = models.DateTimeField()
    original_close = models.DateTimeField()
    bid_close = models.DateTimeField()          # current close (may extend)
    forced_close = models.DateTimeField()
    pickup_date = models.DateField()
    trigger_window_min = models.PositiveIntegerField()   # X
    extension_min = models.PositiveIntegerField()        # Y
    trigger_type = models.CharField(max_length=20, choices=TRIGGERS, default=ANY_BID)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        constraints = [models.CheckConstraint(
            condition=models.Q(forced_close__gt=F("original_close")), name="forced_gt_close")]
 
    def status(self, now):
        if now < self.bid_start:
            return "Upcoming"
        if now >= self.bid_close:
            return "Force Closed" if self.bid_close >= self.forced_close else "Closed"
        return "Active"
 
 
class Bid(models.Model):
    rfq = models.ForeignKey(RFQ, related_name="bids", on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    carrier_name = models.CharField(max_length=120)
    freight = models.DecimalField(max_digits=12, decimal_places=2)
    origin_charges = models.DecimalField(max_digits=12, decimal_places=2)
    destination_charges = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    transit_days = models.PositiveIntegerField()
    validity_days = models.PositiveIntegerField()
    created_at = models.DateTimeField()
 
    class Meta:
        indexes = [models.Index(fields=["rfq", "total"]), models.Index(fields=["rfq", "supplier"])]
 
 
class ActivityLog(models.Model):
    rfq = models.ForeignKey(RFQ, related_name="logs", on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20)   # BID / EXTENSION
    message = models.TextField()
    old_close = models.DateTimeField(null=True, blank=True)
    new_close = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()
 
    class Meta:
        ordering = ["created_at", "id"]
 