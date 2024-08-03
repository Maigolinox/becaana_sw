from django.urls import path,include
from . import views
from django.conf.urls.static import static
from django.contrib import admin


urlpatterns=[
    path('admin/', admin.site.urls),
    path('',views.home,name="index"),
    path('dashboard/',views.dashboard,name="dashboard"),
    path('products/',views.products,name="products"),
    path('addProduct/',views.addProducts,name="addProduct"),
    path('editProducts/',views.editProducts,name="editProducts"),
    path('editProduct/<int:id>',views.editSingleProduct,name="editSingleProduct"),
    path('listProducts/',views.listProducts,name="listProducts"),
    path('deleteProduct/<int:id>',views.deleteProduct,name="deleteProduct"),
    path('addPV/',views.addPV,name="addPV"),
    path('editPVs/',views.editPVs,name="editPVs"),
    path('editPV/<int:id>',views.editPV,name="editPV"),
    path('listPVs/',views.listPVs,name="listPVs"),
    path('PV/',views.PV,name="PV"),
    path('deletePV/<int:id>',views.deletePV,name="deletePV"),
    path('addStock/',views.addStock,name='addStock'),
    path('stock/',views.stock,name="stock"),
    path('updateStock/<int:id>',views.updateStock,name="updateStock"),
    path('updateStockSeller/<int:id>',views.updateStockSeller,name="updateStockSeller"),
    path('updateStockSellerFinance/<int:id>',views.updateStockSellerFinance,name="updateStockSellerFinance"),
    path('registrarVentaMatrix/',views.registrarVentaMatrixView,name="registrarVentaMatrix"),#pos
    path('checkout-modal', views.checkout_modal, name="checkout-modal"),
    path('checkout-modal-carga-vendedores', views.checkout_modal_carga_vendedores, name="checkout-modal-carga-vendedores"),
    path('checkout-modal-carga-pv', views.checkout_modal_carga_pv, name="checkout-modal-carga-pv"),
    path('save-pos/', views.save_pos, name="save-pos"),
    path('receipt/', views.receipt, name="receipt-modal"),
    path('sales/', views.salesList, name="sales-page"),
    path('delete_sale/', views.delete_sale, name="delete-sale"),
    path('delete_sale_sellers/', views.delete_sale_sellers, name="delete-sale-sellers"),
    path('delete_charge_sellers/', views.delete_charge_sellers, name="delete-charge-sellers"),
    path('dashVentas/', views.dash_ventas, name="dashVentas"),
    path('financeDashboard/', views.financeDashboard, name="financeDashboard"),
    path('sellersDashboard/', views.sellersDashboard, name="sellersDashboard"),
    path('settings/', views.settingsView, name="settings"),
    path('listVendedor/', views.sellersListView, name='sellersList'),# Lista vendedores
    path('addVendedor/', views.sellersAddView, name='sellersAdd'), # Agregar vendedor de reparto
    path('updateVendedor/<str:seller_id>',views.sellersUpdateView, name='sellersUpdate'),# Actualizar Vendedor
    path('deleteVendedor/<str:seller_id>',views.sellersDeleteView, name='sellersDelete'),# Eliminar Vendedor
    path('sellers/', views.inventariosVendedores, name="sellers"),
    path('dashboardSellerView/', views.sellersDashboardSellView, name="sellersDashboardVentas"),
    path('registrarVentaVendedor/', views.registrarVentaVendedorView, name="registrarVentaVendedorReparto"),
    path('registrarVentaVendedorExterno/', views.registrarVentaVendedorExternoView, name="registrarVentaVendedorExterno"),
    path('registrarVentaSeller/',views.posSeller,name="registrarVentaSeller"),
    path('save-posSeller/', views.save_posSeller, name="save-pos-seller"),
    path('receiptSeller/', views.receiptSeller, name="receipt-modal-seller"),
    path('receiptChargeSeller/', views.receiptChargeSeller, name="receipt-charge-seller"),
    path('receiptPVs/', views.receiptChargePV, name="receipt-modal-pvs"),
    path('vendedorConsultaInventario/<str:id_vendedor>', views.consultaPropioInventario, name="vendedorConsultaPropioInventario"),
    path('vendedorExternoConsultaInventario/<str:id_vendedor>', views.consultaPropioInventarioExterno, name="vendedorExternoConsultaPropioInventario"),
    path('vendedorMatrizConsultaInventario/<str:id_vendedor>', views.consultaPropioInventarioMatriz, name="vendedorMatrizConsultaPropioInventario"),
    path('eliminarStockPuntosVenta/<str:id>',views.eliminarStockPuntoVenta,name="eliminarStockPV"),
    path('costosVendedores/',views.costosVendedoresView,name="costosVendedores"),
    path('costosPuntosVenta/',views.costosPuntosVentaView,name="costosPuntosVenta"),
    path('dashCostos/',views.dashboardCostos,name="dashboardCostos"),
    path('updateCostSeller/<int:id>',views.updateCostSellerView,name="updateCostSeller"),
    path('deleteCostSeller/<int:id>',views.deleteCostSellerView,name="deleteCostSeller"),
    path('updateCostPuntoVenta/<int:id>',views.updateCostPuntoVentaView,name="updatePuntoVenta"),
    path('deleteCostPuntoVenta/<int:id>',views.deleteCostPuntoVentaView,name="deletePuntoVenta"),
    path('alerts/',views.alertsView,name="alerts"),
    path('editTypeUser/',views.typeUser,name="typeUser"),
    path('sellerSales/',views.salesListVendedores,name="sellerSales"),
    path('matrixSales/',views.salesListMatrix,name="matrixSales"),
    path('puntosVenta/', views.inventariosPV, name="puntosVenta"),
    path('updateStockPV/<int:id>',views.updateStockPV,name="updateStockPV"),
    path('registrarVentaPuntosVenta/', views.registrarVentaPuntosVentaView, name="registrarVentaPuntosVenta"),
    path('save-posSellerPV/', views.save_posPV, name="save-pos-pv"),
    path('save-posMatrixPV/', views.save_posMatrix, name="save-pos-matrix"),
    path('save-posSellerInventory/', views.save_SellerInventory, name="save-seller-inventory"),
    path('save-posExternalSellerInventory/', views.save_SellerExternalInventory, name="save-seller-external-inventory"),
    path('save-posPVInventory/', views.save_PVInventory, name="save-pv-inventory"),
    path('receiptPV/', views.receiptPV, name="receipt-modal-pv"),
    path('receiptMatrix/', views.receiptMatrix, name="receipt-modal-matrix"),
    path('receiptChargeSellerToday/', views.receiptChargeSellerToday, name="receipt-charge-seller-today"),
    path('receiptChargeSellerExternal/', views.receiptChargeSellerExternal, name="receipt-charge-seller-external"),
    path('pvConsultaInventario/', views.pvConsultaInventario, name="pvConsultaInventario"),
    path('deleteStockPV/<int:id>',views.deleteStockPV,name="deleteStockPV"),
    path('deleteStockSellers/<int:id>',views.deleteStockSellers,name="deleteStockSellers"),
    path('deleteStockSellersFinance/<int:id>',views.deleteStockSellersFinance,name="deleteStockSellersFinance"),
    path('cargarInventarioSellers/',views.registrar_inventario_vendedores,name="cargarInventarioVendedores"),#######EJEMPLO
    path('cargarInventarioExternalSellers/',views.registrar_inventario_vendedores_external,name="cargarInventarioVendedoresExternos"),#######EJEMPLO
    path('cargarInventarioPV/',views.registrar_inventario_puntos_venta,name="cargarInventarioPV"),#######
    path('historialInventario/',views.historialInventario,name="historialInventario"),
    path('salesPV/',views.salesListPV,name="salesListPV"),
    path('reporteInventario/',views.reporteInventario,name="reporteInventario"),
    path('deleteRegisterSellers/<int:id>',views.deleteRegisterSellers,name="deleteRegisterSellers"),
    path('deleteRegisterPV/<int:id>',views.deleteRegisterPV,name="deleteRegisterPV"),
    path('addStockMatrix/',views.addMatrixStock,name="addStockMatrix"),
    path('reimpresionCargasDiarias/',views.reimpresionCargasDiarias,name="reimpresionCargasDiarias"),
    path('receiptSellerCharge/', views.receiptSellerCharge, name="receipt-modal-charge"),
    path('reimpresionCargasDiariasI/',views.reimpresionCargasDiariasInd,name="reimpresionCargasDiariasInd"),
    path('impresionInventariosI/', views.impresionInventariosI, name="reimpresionInventariosI"),
    path('impresionInventarios/', views.impresionInventarios, name="reimpresionInventarios"),
    path('receiptSellerInventory/', views.receiptSellerInventory, name="receipt-modal-inventory"),

    path('delete-multiple-records/', views.delete_multiple_records, name='delete_multiple_records'),
    path('salesHistory/', views.salesHistory, name="salesHistory"),
    path('deleteSaleSeller/<int:id>',views.deleteSaleSeller,name="deleteSaleSeller"),




    # path('storeData/',views.storeData,name="storeData")









    


]