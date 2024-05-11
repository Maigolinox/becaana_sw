from django.contrib import admin

# Register your models here.
from .models import RegistroInventarioVendedores,salesItems,salesItemsPV,Sales,pvInventory,tipoVendedor,costosEmpresaPuntosVentaModel,costosEmpresaVendedoresModel,sellerInventory,sellerSales,sellerSalesItems,stockPuntoVenta,articulosModel,puntoVenta,RegistroInventarioPuntoVenta


admin.site.register(RegistroInventarioVendedores)
admin.site.register(salesItems)
admin.site.register(salesItemsPV)
admin.site.register(Sales)
admin.site.register(pvInventory)
admin.site.register(tipoVendedor)
admin.site.register(costosEmpresaPuntosVentaModel)
admin.site.register(costosEmpresaVendedoresModel)
admin.site.register(sellerInventory)
admin.site.register(sellerSales)
admin.site.register(sellerSalesItems)
admin.site.register(stockPuntoVenta)
admin.site.register(articulosModel)
admin.site.register(puntoVenta)
admin.site.register(RegistroInventarioPuntoVenta)
