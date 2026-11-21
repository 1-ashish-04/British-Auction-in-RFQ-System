
from django.contrib import admin
from .models import RFQ, Bid, Supplier, ActivityLog
 
for m in (RFQ, Bid, Supplier, ActivityLog):
    admin.site.register(m)
 