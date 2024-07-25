from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponseRedirect,HttpResponse,JsonResponse
from django.urls import reverse
from .models import puntoVenta,articulosModel,stockPuntoVenta,Sales,salesItems,Seller,sellerInventory,sellerSalesItems,sellerSales,costosEmpresaVendedoresModel,costosEmpresaPuntosVentaModel,pvInventory,salesItemsPV,RegistroInventarioVendedores,RegistroInventarioPuntoVenta, usersPermission
from .forms import InventarioForm,inventarioVendedorForm,InventoryFormPV,costosPuntosVentaForm,costosVendedoresForm,inventarioPuntoVentaForm,inventarioCargaVendedorForm,inventarioCargaPVForm,InventoryFormSeller,InventoryMatrix
import json,sys
from datetime import date, datetime
from django.contrib import messages
from django.db.models import Count,Sum,Q #Q es para consultas mas complejas que involucren condicionales

from django.views.decorators.csrf import csrf_exempt

import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import itertools

from django.views.decorators.csrf import csrf_exempt


from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


from django.db import transaction
from django.db.models import F, ExpressionWrapper, FloatField

from collections import defaultdict
from itertools import chain


# Create your views here.
def save_SellerExternalInventory(request):
    resp = {'status':'failed','msg':''}
    data = request.POST
    
    pref = datetime.now().year + datetime.now().year * 1000 
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = RegistroInventarioVendedores.objects.filter(code = str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        # #print(data)
        i = 0
        for prod in data.getlist('product_id[]'):
            product_id = prod 
            product = articulosModel.objects.all().filter(id=prod).first()
            
            precioVentaVendedor=product.precioVentaVendedorReparto
            qty = int(data.getlist('qty[]')[i] )
            precioVentaVendedorExterno=product.precioVentaVendedorExterno
            precioOriginal=product.costo
            nombreArticulo=product.nombreArticulo
            seller_id=request.user.id
            
            price = data.getlist('price[]')[i]
            # #print("Precio del producto de vendedor",price)
            obj, created = sellerInventory.objects.get_or_create(product_id_id=product_id,seller_id_id=seller_id)
            if not created:
                sellerInventory.objects.filter(product_id_id=product_id,seller_id_id=seller_id).update(qty=F('qty')+qty)

            else:
                obj.product_id_id=product_id
                obj.seller_id_id=seller_id
                obj.precioVentaVendedor=price
                obj.precioVentaVendedorExterno=precioVentaVendedorExterno
                obj.precioOriginal=precioOriginal
                obj.nombreArticulo=nombreArticulo
                obj.qty=qty
                # obj.code=code
                # obj.product_id=product_id
                obj.save()

            RegistroInventarioVendedores(nombre_producto=nombreArticulo,cantidad=qty,usuario_id=seller_id,code=code,product_id=product_id).save()#Registro de inventario
            
            i += int(1)

            product.cantidad=product.cantidad-qty #Restar de inventario de matriz
            product.save() #Restar de inventario de matriz

        sale_id=code
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        # articulosModel.success(request, "Venta guardada.")
    except Exception as e:
        #print(e)
        resp['msg'] = "Ocurrió un error"
        ##print("Unexpected errors:", e)###############################
    return HttpResponse(json.dumps(resp),content_type="application/json")





def receiptChargePV(request):
    if request.user.is_authenticated:
        # #print(request.GET)
        id = request.GET.get('id')
        transaction = {'date_added':timezone.now()}

        usuarioData=User.objects.all().filter(id=request.user.id).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        total_value = 0
        acumulador_total_productos=0
        ItemList = RegistroInventarioPuntoVenta.objects.filter(code = id).all()# LISTA TODOS LOS ELEMENTOS DEL REGISTRO
        for elemento in ItemList:
            # #print(elemento.product_id)
            articulo=articulosModel.objects.all().filter(id=elemento.product_id).get()# OBTEN LA INFORMACION DEL ARTICULO ORIGINAL
            # #print(articulo.precioVentaVendedorReparto)
            total_value=total_value+(elemento.cantidad*articulo.precioVentaPublico)
            elemento.nombreArticulo=articulo.nombreArticulo
            elemento.precioPV=articulo.precioVentaPublico
            elemento.precioVExterno=articulo.precioVentaVendedorExterno
            elemento.precioVendedor=articulo.precioVentaVendedorReparto
            acumulador_total_productos+elemento.cantidad
            
        
        context = {
            "total":total_value,
            # "total_discounts":total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList,
            'nombreUsuario':nombreUsuario,
            'total_productos':acumulador_total_productos,

        }

        return render(request, 'receiptCharge.html',context)
    else:
        return render(request,'forbiden.html')



def receiptChargeSellerExternal(request):
    if request.user.is_authenticated:
        # #print(request.GET)
        id = request.GET.get('id')
        transaction = {'date_added':timezone.now()}

        usuarioData=User.objects.all().filter(id=request.user.id).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        total_value = 0
        ItemList = RegistroInventarioVendedores.objects.filter(code = id).all()# LISTA TODOS LOS ELEMENTOS DEL REGISTRO
        acumulador_total_productos=0
        for elemento in ItemList:
            # #print(elemento.product_id)
            articulo=articulosModel.objects.all().filter(id=elemento.product_id).get()# OBTEN LA INFORMACION DEL ARTICULO ORIGINAL
            # #print(articulo.precioVentaVendedorReparto)
            total_value=total_value+(elemento.cantidad*articulo.precioVentaVendedorExterno)
            acumulador_total_productos+=elemento.cantidad
            elemento.nombreArticulo=articulo.nombreArticulo
            elemento.precioPV=articulo.precioVentaPublico
            elemento.precioPV=articulo.precioVentaVendedorExterno
            elemento.precioVendedor=articulo.precioVentaVendedorReparto
            
        
        context = {
            "total":total_value,
            # "total_discounts":total_discounts,
            'total_productos':acumulador_total_productos,
            "transaction" : transaction,
            "salesItems" : ItemList,
            'nombreUsuario':nombreUsuario,
        }

        return render(request, 'receiptCharge.html',context)
    else:
        return render(request,'forbiden.html')


def receiptChargeSellerToday(request):
    if request.user.is_authenticated:
        # #print(request.GET)
        id = request.GET.get('id')
        print(id)
        codigoTransaccion=RegistroInventarioVendedores.objects.all().filter(id = id).values('code')
        codigoTransaccion=codigoTransaccion[0]['code']
        
        
        user_id=RegistroInventarioVendedores.objects.all().filter(id = id).values('usuario_id')
        # print(user_id[0]['usuario_id'])
        userData=User.objects.all().filter(id=user_id[0]['usuario_id']).get()
        nombreUsuario="Nombre: "+userData.first_name+" "+userData.last_name+" "+". Usuario: "+userData.username
        transaction = {'date_added':timezone.now()}

        permisosEspeciales=usersPermission.objects.filter(user_id=user_id[0]['usuario_id']).get()



        # usuarioData=User.objects.all().filter(id=request.user.id).get()# NOMBRE DEL USUARIO AL TICKET
        # nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        total_value = 0
        acumulador_total_productos=0
        ItemList = RegistroInventarioVendedores.objects.filter(code = codigoTransaccion).all()# LISTA TODOS LOS ELEMENTOS DEL REGISTRO
        print(ItemList)
        for elemento in ItemList:
            #print("impresion: ",elemento)
            # #print(elemento.product_id)
            articulo=articulosModel.objects.all().filter(id=elemento.product_id).get()# OBTEN LA INFORMACION DEL ARTICULO ORIGINAL
            # #print(articulo.precioVentaVendedorReparto)
            

            elemento.nombreArticulo=articulo.nombreArticulo
            elemento.precioPV=articulo.precioVentaVendedorReparto
            if permisosEspeciales.is_externalSeller:
                elemento.precioPV=articulo.precioVentaVendedorExterno
            else:
                elemento.precioPV=articulo.precioVentaVendedorReparto

            total_value=total_value+(elemento.cantidad*elemento.precioPV)
            

            
            acumulador_total_productos+=elemento.cantidad
            ##print(acumulador_total_productos)
            elemento.precioVExterno=articulo.precioVentaVendedorExterno
            elemento.precioVendedor=articulo.precioVentaVendedorReparto

            
        
        context = {
            "total":total_value,
            # "total_discounts":total_discounts,
            "transaction" : transaction,
            'total_productos':acumulador_total_productos,

            "salesItems" : ItemList,
            'nombreUsuario':nombreUsuario,
        }

        return render(request, 'receiptCharge.html',context)
    else:
        return render(request,'forbiden.html')


def save_SellerInventory(request):
    resp = {'status':'failed','msg':''}
    data = request.POST
    
    pref = datetime.now().year + datetime.now().year * 1000 
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = RegistroInventarioVendedores.objects.filter(code = str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        # #print(data)
        i = 0
        for prod in data.getlist('product_id[]'):
            product_id = prod 
            product = articulosModel.objects.all().filter(id=prod).first()
            
            precioVentaVendedor=product.precioVentaVendedorReparto
            qty = int(data.getlist('qty[]')[i] )
            precioVentaVendedorExterno=product.precioVentaVendedorExterno
            precioOriginal=product.costo
            nombreArticulo=product.nombreArticulo
            seller_id=request.user.id
            
            price = data.getlist('price[]')[i]
            # #print("Precio del producto de vendedor",price)
            obj, created = sellerInventory.objects.get_or_create(product_id_id=product_id,seller_id_id=seller_id)
            if not created:
                sellerInventory.objects.filter(product_id_id=product_id,seller_id_id=seller_id).update(qty=F('qty')+qty)

            else:
                obj.product_id_id=product_id
                obj.seller_id_id=seller_id
                obj.precioVentaVendedor=price
                obj.precioVentaVendedorExterno=precioVentaVendedorExterno
                obj.precioOriginal=precioOriginal
                obj.nombreArticulo=nombreArticulo
                obj.qty=qty
                # obj.code=code
                # obj.product_id=product_id
                obj.save()

            RegistroInventarioVendedores(nombre_producto=nombreArticulo,cantidad=qty,usuario_id=seller_id,code=code,product_id=product_id).save()#Registro de inventario
            
            i += int(1)

            product.cantidad=product.cantidad-qty #Restar de inventario de matriz
            product.save() #Restar de inventario de matriz

        sale_id=code
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        # articulosModel.success(request, "Venta guardada.")
    except Exception as e:
        #print(e)
        resp['msg'] = "Ocurrió un error"
        ##print("Unexpected errors:", e)###############################
    return HttpResponse(json.dumps(resp),content_type="application/json")


def save_PVInventory(request):
    resp = {'status':'failed','msg':''}
    data = request.POST
    
    pref = datetime.now().year + datetime.now().year * 1000 
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = RegistroInventarioPuntoVenta.objects.filter(code = str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        # #print(data)
        i = 0
        for prod in data.getlist('product_id[]'):
            product_id = prod 
            product = articulosModel.objects.all().filter(id=prod).first()
            
            precioVentaVendedor=product.precioVentaVendedorReparto
            qty = int(data.getlist('qty[]')[i] )
            precioVentaVendedorExterno=product.precioVentaVendedorExterno
            precioOriginal=product.costo
            nombreArticulo=product.nombreArticulo
            precioVenta=product.precioVentaPublico
            seller_id=request.user.id
            
            # price = data.getlist('price[]')[i]
            obj, created = pvInventory.objects.get_or_create(product_id_id=product_id,seller_id_id=seller_id)
            if not created:
                pvInventory.objects.filter(product_id_id=product_id,seller_id_id=seller_id).update(qty=F('qty')+qty)

            else:
                obj.product_id_id=product_id
                obj.seller_id_id=seller_id
                obj.precioVentaVendedor=precioVentaVendedor
                obj.precioVentaVendedorExterno=precioVentaVendedorExterno
                obj.precioOriginal=precioOriginal#costo
                obj.nombreArticulo=nombreArticulo
                obj.precioVenta=precioVenta
                obj.qty=qty
                obj.code=code
                # obj.product_id=product_id
                obj.save()

            RegistroInventarioPuntoVenta(nombre_producto=nombreArticulo,cantidad=qty,usuario_id=seller_id,code=code,product_id=product_id).save()#Registro de inventario
            
            i += int(1)

            product.cantidad=product.cantidad-qty #Restar de inventario de matriz
            product.save() #Restar de inventario de matriz

        sale_id=code
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        # articulosModel.success(request, "Venta guardada.")
    except Exception as e:
        #print(e)
        resp['msg'] = "Ocurrió un error"
        ##print("Unexpected errors:", e)###############################
    return HttpResponse(json.dumps(resp),content_type="application/json")

# # # #





def addMatrixStock(request):
    if request.user.is_authenticated:
        lista = articulosModel.objects.all()
        for item in lista:
                item.costo_total = item.cantidad * item.costo
                item.precio_publico_total = item.cantidad * item.precioVentaPublico
                item.ganancia = item.precio_publico_total - item.costo_total
                item.gananciaUnitaria = item.precioVentaPublico - item.costo
                
                
        total_public_price = sum(item.precio_publico_total for item in lista)
        total_cost = sum(item.cantidad * item.costo for item in lista)
        gananciaTotal = total_public_price - total_cost

        if request.method == 'POST':
            form = InventoryMatrix(request.POST)
            if form.is_valid():
                # user = form.cleaned_data['user']
                product = form.cleaned_data['product']
                quantity = form.cleaned_data['quantity']
                inventory_item, created = articulosModel.objects.get_or_create(
                    id=product.id
                    )
                if not created:
                    inventory_item.cantidad += quantity
                else:
                    inventory_item.cantidad = quantity
                
                inventory_item.save()
                

                # Guardar el formulario si es válido
                # Redirigir a una página de éxito o a donde desees
                return redirect('addStockMatrix')

        else:
            form = InventoryMatrix()
            lista = articulosModel.objects.all()
        

        context = {
            'form': form,
            'lista':lista,
            'total_cost':total_cost,
            'gananciaTotal':gananciaTotal,
            'total_public_price':total_public_price,
            }
        return render(request, 'listaInventariosMatrix.html', context)
    else:
        return render(request, 'forbidden.html')

def listProducts(request):
    if request.user.is_authenticated:
        articulos=articulosModel.objects.all()

        return render(request,'listProducts.html',context={'articulos':articulos})
    else:
        return render(request,'forbiden.html')


def editProducts(request):
    if request.user.is_authenticated:
        try:
            articulos=articulosModel.objects.all()
            return render(request,'editProducts.html',context={'articulos':articulos})

        except Exception as e:
            ###print(e)
            pass
        return render(request,'editProducts.html')
    else:
        return render(request,'forbiden.html')


def editSingleProduct(request,id):
    if request.user.is_authenticated:
        try:
            currentInfoProduct=articulosModel.objects.get(id=id)
            if request.method=="POST":
                nombreArticulo=request.POST.get('nombreArticulo')
                unidad=request.POST.get('unidad')
                descripcionArticulo=request.POST.get('descripcionArticulo')
                costo=request.POST.get('costo')
                precioVentaPublico=request.POST.get('precioVentaPublico')
                precioVentaVendedorReparto=request.POST.get('precioVentaVendedorReparto')
                cantidadMinima=request.POST.get('cantidadMinima')
                cantidadMaxima=request.POST.get('cantidadMaxima')
                urlArticulo=request.POST.get('urlArticulo')
                precioVentaVendedorExterno=request.POST.get('precioVentaVendedorExterno')
                cantidadStockMaestro=request.POST.get('cantidadStockMaestro')
                currentInfoProduct.nombreArticulo=nombreArticulo
                currentInfoProduct.unidad=unidad
                currentInfoProduct.costo=costo
                currentInfoProduct.descripcionArticulo=descripcionArticulo
                currentInfoProduct.precioVentaPublico=precioVentaPublico
                currentInfoProduct.precioVentaVendedorReparto=precioVentaVendedorReparto
                currentInfoProduct.cantidad=cantidadStockMaestro
                currentInfoProduct.cantidadMinima=cantidadMinima
                currentInfoProduct.cantidadMaxima=cantidadMaxima
                currentInfoProduct.urlArticulo=urlArticulo
                currentInfoProduct.precioVentaVendedorExterno=precioVentaVendedorExterno

                currentInfoProduct.save()
                return redirect('editProducts')
            else:
                return render(request,'editSingleProduct.html',context={'currentInfoProduct':currentInfoProduct})
        except:
            return render(request,'editSingleProduct.html',context={'currentInfoProduct':currentInfoProduct})
    else:
        return render(request,'forbiden.html')


def deleteProduct(request,id):
    if request.user.is_authenticated:
        try:
            deleteProduct=articulosModel.objects.get(id=id)
            deleteProduct.delete()
            return redirect('editProducts')
        except:
            return render(request,'deletePV.html')
    else:
        return render(request,'forbiden.html')


def home(request):
    return render(request,'index.html')


def typeUser(request):
    if request.user.is_authenticated:
        objetoUsuario = User.objects.get(id=request.user.id)
        # objeto = usersPermission.objects.get(user_id=request.user.id)
        # objetoUsuario.is_externalSeller=objeto.is_externalSeller
        # objetoUsuario.is_matrixSeller=objeto.is_matrixSeller

        if objetoUsuario.is_staff and objetoUsuario.is_superuser and objetoUsuario.is_active:
            listaPermisos = User.objects.all()
            listaPermisosEspeciales=usersPermission.objects.all()

            if request.method == 'POST':
                # Process form submission
                
                for user in listaPermisos:
                    # Update user permissions based on form data
                    user.is_superuser = 'permissions_superuser_' + str(user.id) in request.POST                    
                    user.is_staff = 'permissions_staff_' + str(user.id) in request.POST
                    user.is_active = 'permissions_active_' + str(user.id) in request.POST                    
                    user.save()
                for user in listaPermisosEspeciales:
                    user.is_externalSeller='permissions_external_'+str(user.id) in request.POST
                    user.is_matrixSeller='permissions_matrix_'+str(user.id) in request.POST
                    user.save()

                return redirect('typeUser')  # Redirect to a success page
            else:
                listaCombinada=[]
                listaPermisos = User.objects.all()
                for user in listaPermisos:
                    user_permission = usersPermission.objects.filter(user_id=user.id).first()
                    if user_permission:
                        listaCombinada.append({
                            'user_id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'is_staff':user.is_staff,
                            'is_superuser':user.is_superuser,
                            'is_active':user.is_active,
                            'is_externalSeller': user_permission.is_externalSeller,
                            'is_matrixSeller': user_permission.is_matrixSeller,
                        })
                    else:
                        listaCombinada.append({
                            'user_id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'is_externalSeller': False,
                            'is_matrixSeller': False,
                        })
                return render(request, 'editTypeUser.html', context={'listaPermisos': listaCombinada})
        else:
            return HttpResponse("No eres administrador, tu no puedes hacer este cambio", content_type='text/plain')
    else:
        return render(request, 'forbiden.html')


def dashboard(request):
    if request.user.is_authenticated:
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_last_week = start_of_week - timedelta(days=7)


        userName=request.user
        user_id=request.user.id
        objetoUsuario=User.objects.get(id=user_id)
        objeto=usersPermission.objects.get(user_id=user_id)
        objetoUsuario.is_externalSeller=objeto.is_externalSeller
        objetoUsuario.is_matrixSeller=objeto.is_matrixSeller

        mensaje=""
        ###print(userName)
        if (objetoUsuario.is_staff and objetoUsuario.is_superuser and objetoUsuario.is_active):# dashboard de administrador
            return render(request,'dashboard.html',context={'mensaje':mensaje})
        elif (objetoUsuario.is_active and not objetoUsuario.is_staff and not objetoUsuario.is_superuser and not objetoUsuario.is_externalSeller and not objetoUsuario.is_matrixSeller):#dashboard de vendedores
            ##print("Vendedor Normal")
            try:
                ventasUsuarioSemanaActual=sellerSales.objects.filter(
                    origin=request.user.id,
                    date_added__date__gte=start_of_week,
                    date_added__date__lt=start_of_week + timedelta(days=7)
                ).aggregate(total_ventas=Sum('grand_total'))['total_ventas'] or 0
                
                ventasUsuarioSemanaPasada=sellerSales.objects.filter(
                    origin=request.user.id,
                    date_added__date__gte=start_of_last_week,
                    date_added__date__lt=start_of_last_week + timedelta(days=7)
                    ).aggregate(total_ventas=Sum('grand_total'))['total_ventas'] or 0

                ventasUsuario=sellerSales.objects.all().filter(origin=request.user.id,date_added__date=timezone.now().date()).aggregate(total_ventas=Sum('grand_total'))
            except Exception as e:
                ##print(e)
                ventasUsuario=0
                ventasUsuarioSemanaPasada=0
                ventasUsuarioSemanaActual=0
            return render(request,'dashVentasSeller.html',context={'mensaje':mensaje,'user_id':user_id,'totalVentasUsuario':ventasUsuario,'ventasUsuarioSemanaPasada':ventasUsuarioSemanaPasada,'ventasUsuarioSemanaActual':ventasUsuarioSemanaActual})
        elif (objetoUsuario.is_active and not objetoUsuario.is_staff and not objetoUsuario.is_superuser and objetoUsuario.is_externalSeller and not objetoUsuario.is_matrixSeller):#dashboard de vendedores externos
            #print("Vendedor Externo")
            try:
                ventasUsuarioSemanaActual=sellerSales.objects.filter(
                    origin=request.user.id,
                    date_added__date__gte=start_of_week,
                    date_added__date__lt=start_of_week + timedelta(days=7)
                ).aggregate(total_ventas=Sum('grand_total'))['total_ventas'] or 0
                
                ventasUsuarioSemanaPasada=sellerSales.objects.filter(
                    origin=request.user.id,
                    date_added__date__gte=start_of_last_week,
                    date_added__date__lt=start_of_last_week + timedelta(days=7)
                    ).aggregate(total_ventas=Sum('grand_total'))['total_ventas'] or 0

                ventasUsuario=sellerSales.objects.all().filter(origin=request.user.id,date_added__date=timezone.now().date()).aggregate(total_ventas=Sum('grand_total'))
            except Exception as e:
                ##print(e)
                ventasUsuario=0
                ventasUsuarioSemanaPasada=0
                ventasUsuarioSemanaActual=0
            return render(request,'dashVentasExternalSeller.html',context={'mensaje':mensaje,'user_id':user_id,'totalVentasUsuario':ventasUsuario,'ventasUsuarioSemanaPasada':ventasUsuarioSemanaPasada,'ventasUsuarioSemanaActual':ventasUsuarioSemanaActual})
        
        elif (objetoUsuario.is_active and objetoUsuario.is_staff and not objetoUsuario.is_superuser ):#dashboard de puntos de venta
            try:
                Ventas=Sales.objects.all().filter(origin=request.user.id,date_added__date=timezone.now().date()).aggregate(total_ventas=Sum('grand_total'))
            except Exception as e:
                ##print(e)
                Ventas=0
            return render(request,'dahsPuntosVenta.html',context={'Ventas':Ventas})
        
        elif (objetoUsuario.is_active and not objetoUsuario.is_staff and not objetoUsuario.is_superuser and not objetoUsuario.is_externalSeller and objetoUsuario.is_matrixSeller):#dashboard de vendedores matrix
            # #print("Vendedor Matriz")
            try:
                ventasUsuarioSemanaActual=Sales.objects.filter(
                    origin=request.user.id,
                    date_added__date__gte=start_of_week,
                    date_added__date__lt=start_of_week + timedelta(days=7)
                ).aggregate(total_ventas=Sum('grand_total'))['total_ventas'] or 0
                
                ventasUsuarioSemanaPasada=Sales.objects.filter(
                    origin=request.user.id,
                    date_added__date__gte=start_of_last_week,
                    date_added__date__lt=start_of_last_week + timedelta(days=7)
                    ).aggregate(total_ventas=Sum('grand_total'))['total_ventas'] or 0

                ventasUsuario=Sales.objects.all().filter(origin=request.user.id,date_added__date=timezone.now().date()).aggregate(total_ventas=Sum('grand_total'))
            except Exception as e:
                ##print(e)
                ventasUsuario=0
                ventasUsuarioSemanaPasada=0
                ventasUsuarioSemanaActual=0
            return render(request,'dashVentasMatrixSeller.html',context={'mensaje':mensaje,'user_id':user_id,'totalVentasUsuario':ventasUsuario,'ventasUsuarioSemanaPasada':ventasUsuarioSemanaPasada,'ventasUsuarioSemanaActual':ventasUsuarioSemanaActual})##############################################
        
        else:
            return HttpResponse("Contacta al administrador del sistema")
        
        #return render(request,'dashboard.html',context={'mensaje':mensaje})
        
    else:
        return render(request,'forbiden.html')


def products(request):
    if request.user.is_authenticated:
        return render(request,'products.html')
    else:
        return render(request,'forbiden.html')


def addPV(request):
    if request.user.is_authenticated:
        if request.method=="POST":
            try:
                nombrePV=request.POST.get('nombrePV')
                direccionPV=request.POST.get('direccionPV')
                telefonoPV=request.POST.get('telefonoPV')
                puntoVenta.objects.create(nombrePV=nombrePV,telefonoPV=telefonoPV,direccionPV=direccionPV)
                mensaje="Se ha registrado correctamente el Punto de Venta, vuelve al menú principal"
                #return render(request,"addPV.html",context={'mensaje':mensaje})
                return redirect('dashboard')
            except:
                mensaje="Ocurrió un error al registrar el Punto de Venta"
                return render(request,"addPV.html",context={'mensaje':mensaje})
                
        else:
            return render(request,'addPV.html')
    else:
        return render(request,'forbiden.html')
 

def PV(request):
    if request.user.is_authenticated:

        return render(request,'PV.html')
    else:
        return render(request,'forbiden.html')


def deletePV(request,id):
    if request.user.is_authenticated:
        try:
            deletePV=puntoVenta.objects.get(id=id)
            deletePV.delete()
            return redirect('dashboard')
        except:
            return render(request,'deletePV.html')
    else:
        return render(request,'forbiden.html')


def listPVs(request):
    if request.user.is_authenticated:
        try:
            puntosVenta=User.objects.all().filter(is_active=True,is_superuser=False,is_staff=True)
            
            return render(request,'listPVs.html',context={'puntosVenta':puntosVenta})
        except:
            ###print("Error")
            return render(request,'listPVs.html')
    else:
        return render(request,'forbiden.html')


def editPV(request,id):
    if request.user.is_authenticated:
        try:
            currentInfoPV=puntoVenta.objects.get(id=id)
            if request.method=="POST":
                nombrePV=request.POST.get('nombrePV')
                direccionPV=request.POST.get('direccionPV')
                telefonoPV=request.POST.get('telefonoPV')
                currentInfoPV.nombrePV=nombrePV
                currentInfoPV.direccionPV=direccionPV
                currentInfoPV.telefonoPV=telefonoPV

                currentInfoPV.save()
                return redirect('listPVs')
            else:
                return render(request,'editPV.html',context={'currentInfoPV':currentInfoPV})
        except:
            return render(request,'editPV.html',context={'currentInfoPV':currentInfoPV})
    else:
        return render(request,'forbiden.html')


def editPVs(request):
    if request.user.is_authenticated:
        try:
            puntosVenta=puntoVenta.objects.all()
            
            return render(request,'listPVs.html',context={'puntosVenta':puntosVenta})
        except:
            ###print("Error")
            return render(request,'listPVs.html')
    else:
        return render(request,'forbiden.html')


def addProducts(request):
    if request.user.is_authenticated:
        if request.method=="POST":
            try:
                nombreArticulo=request.POST.get('nombreArticulo')
                
                unidad=request.POST.get('unidad')
                descripcionArticulo=request.POST.get('descripcionArticulo')
                costo=request.POST.get('costo')
                precioVentaPublico=request.POST.get('precioVentaPublico')
                precioVentaVendedorReparto=request.POST.get('precioVentaVendedorReparto')
                precioVentaVendedorExterno=request.POST.get('precioVentaVendedorExterno')
                cantidadMinima=request.POST.get('cantidadMinima')
                cantidadMaxima=request.POST.get('cantidadMaxima')
                urlArticulo=request.POST.get('urlArticulo')
                cantidadStockMaestro=request.POST.get('cantidadStockMaestro')
                articulosModel.objects.create(nombreArticulo=nombreArticulo,unidad=unidad,descripcionArticulo=descripcionArticulo,costo=costo,precioVentaPublico=precioVentaPublico,precioVentaVendedorExterno=precioVentaVendedorExterno,precioVentaVendedorReparto=precioVentaVendedorReparto,cantidadMaxima=cantidadMaxima,cantidadMinima=cantidadMinima,cantidad=cantidadStockMaestro,urlArticulo=urlArticulo)
                mensaje="Se ha guardado el producto"
                return render(request,"addProduct.html",context={'mensaje':mensaje})
                #return redirect('addProduct')
            except Exception as e:
                ##print(e)
                mensaje="Ocurrió un error al registrar el producto"
                return render(request,"addProduct.html",context={'mensaje':mensaje})
        else:
            return render(request,"addProduct.html")
    else:
        return render(request,'forbiden.html')
    

def addStock(request,pk=None):

    inventario = get_object_or_404(stockPuntoVenta, pk=pk) if pk else None
    lista=stockPuntoVenta.objects.all()

    for item in lista:
        item.costo_total = item.stock * item.producto.costo
        item.precio_publico_total = item.stock * item.producto.precioVentaPublico
        item.ganancia = item.precio_publico_total - item.costo_total
        item.gananciaUnitaria=item.producto.precioVentaPublico - item.producto.costo

    total_public_price = sum(item.precio_publico_total for item in lista)
    total_cost = sum(item.stock * item.producto.costo for item in lista)
    gananciaTotal=total_public_price-total_cost

    if request.method == 'POST':
        form = InventarioForm(request.POST,instance=inventario)
        if form.is_valid():
            form.save()
            return redirect('addStock')
    else:
        form = InventarioForm(instance=inventario)
        
    return render(request, 'addStock.html', {'form': form,'gananciaTotal':gananciaTotal,'inventario':inventario,'lista':lista,'total_cost':total_cost,'total_public_price': total_public_price})


def updateStock(request, id):
    if request.user.is_authenticated:
        try:
            currentStock=stockPuntoVenta.objects.get(id=id)

            if request.method=="POST":

                stock=request.POST.get('stock')
                currentStock.stock=stock
                currentStock.save()

                return redirect('addStock')
            else:
                return render(request,'updateStock.html',context={'currentStock':currentStock})
        except:
            return render(request,'updateStock.html',context={'currentStock':currentStock})
    else:
        return render(request,'forbiden.html')


def updateStockSeller(request, id):
    if request.user.is_authenticated:
        try:
            # Obtener la petición del usuario
            userPetition = request.user.id
            
            # Obtener el stock actual
            currentStock = sellerInventory.objects.get(id=id)
            cantidadActual = currentStock.qty
            
            # Obtener el producto correspondiente al stock actual
            productMatrix = articulosModel.objects.get(id=currentStock.product_id_id)
            
            if request.method == "POST":
                stock = request.POST.get('stock')
                
                # Actualizar el stock
                currentStock.qty = stock
                diferencia = int(stock) - cantidadActual
                
                if diferencia > 0:
                    productMatrix.cantidad -= diferencia
                elif diferencia < 0:
                    productMatrix.cantidad -= diferencia
                # Guardar los cambios en los modelos
                currentStock.save()
                productMatrix.save()
                
                return redirect('sellers')
            else:
                # Mostrar la página de actualización con el stock actual
                return render(request, 'updateStockSeller.html', context={'currentStock': currentStock})
        except sellerInventory.DoesNotExist:
            # Manejar el caso cuando no se encuentra el stock
            return render(request, 'updateStockSeller.html', context={'currentStock': None})
        except articulosModel.DoesNotExist:
            # Manejar el caso cuando no se encuentra el producto
            return render(request, 'updateStockSeller.html', context={'currentStock': None})
        except Exception as e:
            # Manejar otras excepciones de manera genérica
            #print(e)
            return render(request, 'updateStockSeller.html', context={'currentStock': None})
    else:
        return render(request, 'forbiden.html')
   

def updateStockSellerFinance(request, id):
    if request.user.is_authenticated:
        try:
            # Obtener la petición del usuario
            userPetition = request.user.id
            
            # Obtener el stock actual
            currentStock = sellerInventory.objects.get(id=id)
            cantidadActual = currentStock.qty
            
            # Obtener el producto correspondiente al stock actual
            productMatrix = articulosModel.objects.get(id=currentStock.product_id_id)
            
            if request.method == "POST":
                stock = request.POST.get('stock')
                
                # Actualizar el stock
                currentStock.qty = stock
                diferencia = int(stock) - cantidadActual
                
                if diferencia > 0:
                    productMatrix.cantidad -= diferencia
                elif diferencia < 0:
                    productMatrix.cantidad -= diferencia
                # Guardar los cambios en los modelos
                currentStock.save()
                productMatrix.save()
                
                return redirect('financeDashboard')
            else:
                # Mostrar la página de actualización con el stock actual
                return render(request, 'updateStockSeller.html', context={'currentStock': currentStock})
        except sellerInventory.DoesNotExist:
            # Manejar el caso cuando no se encuentra el stock
            return render(request, 'updateStockSeller.html', context={'currentStock': None})
        except articulosModel.DoesNotExist:
            # Manejar el caso cuando no se encuentra el producto
            return render(request, 'updateStockSeller.html', context={'currentStock': None})
        except Exception as e:
            # Manejar otras excepciones de manera genérica
            #print(e)
            return render(request, 'updateStockSeller.html', context={'currentStock': None})
    else:
        return render(request, 'forbiden.html')
   

def stock(request):
    if request.user.is_authenticated:
        return render(request,'stock.html')
    else:
        return render(request,'forbiden.html')


def registrarVentaMatrixView(request):
    if request.user.is_authenticated:
        products = articulosModel.objects.all()######NECESARIO PARA FILTRAR SOLO EL INVENTARIO DE CADA VENDEDOR
        product_json = []
        ###print(products)
        for product in products:
            ###print(product.product_id_id)
            # #print('id',product.id, 'name',product.nombreArticulo, 'price',float(product.precioVentaPublico),'qty',float(product.cantidad),'general_id',product.id)            
            product_json.append({'id':product.id, 'name':product.nombreArticulo, 'price':float(product.precioVentaPublico),'qty':float(product.cantidad),'general_id':product.id})
        
        context = {
            'page_title' : "Punto de venta",
            'products' : products,
            'product_json' : json.dumps(product_json)
        }
        # return HttpResponse('')
        return render(request, 'registrarVentaVendedoresMatriz.html',context)
    else:
        return render(request,'forbiden.html')
 

def checkout_modal(request):
    if request.user.is_authenticated:
        sucursales = puntoVenta.objects.all()
        grand_total = 0
        if 'grand_total' in request.GET:
            grand_total = request.GET['grand_total']
        
        context = {
            'grand_total' : grand_total,
            'sucursales' : sucursales,
        }
        return render(request, 'checkout.html',context)
    else:
        return render(request, 'forbiden.html')


def checkout_modal_carga_vendedores(request):
    if request.user.is_authenticated:
        sucursales = puntoVenta.objects.all()
        grand_total = 0
        if 'grand_total' in request.GET:
            grand_total = request.GET['grand_total']
        
        context = {
            'grand_total' : grand_total,
            'sucursales' : sucursales,
        }
        return render(request, 'checkoutSellerCargaInventario.html',context)
    else:
        return render(request, 'forbiden.html')
    
def checkout_modal_carga_pv(request):
    if request.user.is_authenticated:
        sucursales = puntoVenta.objects.all()
        grand_total = 0
        if 'grand_total' in request.GET:
            grand_total = request.GET['grand_total']
        
        context = {
            'grand_total' : grand_total,
            'sucursales' : sucursales,
        }
        return render(request, 'checkoutSellerCargaInventario.html',context)
    else:
        return render(request, 'forbiden.html')


def save_pos(request):
    resp = {'status':'failed','msg':''}
    data = request.POST
    ###print(data)
    pref = datetime.now().year + datetime.now().year
    
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = Sales.objects.filter(code = str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        sales = Sales(code=code, sub_total = data['sub_total'], tax = data['tax'], tax_amount = data['tax_amount'], grand_total = data['grand_total'], tendered_amount = data['tendered_amount'], amount_change = data['amount_change'],origin=request.user.id)
        sales.save()
        
        

        sale_id = Sales.objects.last().pk
        i = 0
        for prod in data.getlist('product_id[]'):
            #product_id = prod 
            sale = Sales.objects.filter(id=sale_id).first()
            product = articulosModel.objects.filter(id=prod).first()
            qty = int(data.getlist('qty[]')[i] )
            
            price = data.getlist('price[]')[i]
            total = float(qty) * float(price)
            ###print({'sale_id' : sale, 'product_id' : product, 'qty' : qty, 'price' : price, 'total' : total})
            salesItems(sale_id = sale, product_id = product, qty = qty, price = price, total = total).save()
            try:
                productoDecremento=stockPuntoVenta.objects.get(producto_id=prod)
                if productoDecremento.stock>0 and productoDecremento.stock>=qty:
                    productoDecremento.stock-=qty
                    productoDecremento.save()
            except:
                pass
                
            i += int(1)

            
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        articulosModel.success(request, "Venta guardada.")
    except Exception as e:
        resp['msg'] = "Ocurrió un error"
        ###print("Unexpected error:", e)
    return HttpResponse(json.dumps(resp),content_type="application/json")


def receipt(request):
    if request.user.is_authenticated:
        


        id = request.GET.get('id')
        sales = Sales.objects.filter(id = id).first()
        transaction = {}
        for field in Sales._meta.get_fields():
            if field.related_model is None:
                transaction[field.name] = getattr(sales,field.name)
        
        ventaInformacion=Sales.objects.all().filter(code= transaction['code']).values('origin')
        usuarioData=User.objects.all().filter(id=ventaInformacion[0]['origin']).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        # print(ventaInformacion[0]['origin'])
        
        if 'tax_amount' in transaction:
            transaction['tax_amount'] = format(float(transaction['tax_amount']))

        ItemList = salesItems.objects.filter(sale_id = sales).all()
        
        total_discounts=0
        for elemento in ItemList:
            discount=(elemento.discount*elemento.price*elemento.qty)/100
            # ##print(discount)
            total_discounts+=discount

        
        total=transaction["grand_total"]+total_discounts
        
        context = {
            "total":total,
            "total_discounts":total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList,
            "nombreUsuario":nombreUsuario,
        }

        return render(request, 'receipt.html',context)
    else:
        return render(request,'forbiden.html')
    # return HttpResponse('')


def salesList(request):#########AGREGAR NOMBRE DE USUARIO QUE HIZO LA VENTA, NO COINCIDE EL TOTAL DE ARTICULOS CON LOS TICKETS
    ###VERIFICAR CONTADOR DE TICKETS, NOMBRE DE USUARIO EN TICKET
    if request.user.is_authenticated:

        sales = Sales.objects.all()
        salesVendedor=sellerSales.objects.all()
        sale_data = []
        sale_data_vendedor=[]
        for sale in sales:
            # print(sale) obtengo el codigo de la venta de puntos de venta
            # print(sale.id)obtengo el id de la venta que es realmente lo que esta asociado con los artículos que se venden
            articulosPuntosVenta=salesItems.objects.filter(sale_id = sale.id).all().aggregate(Sum('qty'))
            


            data = {}
            data['qty']=articulosPuntosVenta['qty__sum']
            for field in sale._meta.get_fields(include_parents=False):
                if field.related_model is None:
                    data[field.name] = getattr(sale,field.name)
            data['items'] = salesItems.objects.filter(sale_id = sale).all()
            data['item_count'] = len(data['items'])

            data['id_puntoVenta']=Sales.objects.all().filter(code=sale).values('origin')
            data['id_puntoVenta']=data['id_puntoVenta'][0]['origin']
            data['nombre_puntoVenta']=User.objects.all().filter(id=data['id_puntoVenta']).values('username')
            data['nombre_puntoVenta']=data['nombre_puntoVenta'][0]['username']
            # print(data['nombre_puntoVenta'])

            if 'tax_amount' in data:
                data['tax_amount'] = format(float(data['tax_amount']),'.2f')
            # ###print(data)
            sale_data.append(data)
        # ###print(sale_data)
        acumuladorSellers=0
        for sale in salesVendedor:
            articulosVendedor=sellerSalesItems.objects.filter(sale_id = sale.id).all().aggregate(Sum('qty'))

            data = {}
            data['qty']=articulosVendedor['qty__sum']
            data['id_vendedor']=sellerSales.objects.all().filter(code=sale).values('origin')
            data['id_vendedor']=data['id_vendedor'][0]['origin']
            data['nombre_vendedor']=User.objects.all().filter(id=data['id_vendedor']).values('username')
            data['nombre_vendedor']=data['nombre_vendedor'][0]['username']
            
            
            for field in sale._meta.get_fields(include_parents=False):
                if field.related_model is None:
                    data[field.name] = getattr(sale,field.name)
                    
            
            data['items'] = sellerSalesItems.objects.filter(sale_id = sale).all()
            

            
            data['item_count'] = len(data['items'])
            if 'tax_amount' in data:
                data['tax_amount'] = format(float(data['tax_amount']),'.2f')
            # ###print(data)
            sale_data_vendedor.append(data)
        # ###print(sale_data)  

        context = {
            'page_title':'Sales Transactions',
            'sale_data':sale_data,
            'sale_data_vendedor':sale_data_vendedor,
        }
        # return HttpResponse('')
        return render(request, 'sales.html',context)
    else:
        return render(request,'forbiden.html')


def delete_sale(request):
    if request.user.is_authenticated:

        resp = {'status':'failed', 'msg':''}
        id = request.POST.get('id')
        try:
            delete = Sales.objects.filter(id = id).delete()
            resp['status'] = 'success'
            messages.success(request, 'Registro de venta eliminado.')
        except:
            resp['msg'] = "Ha ocurrido un error."
            ###print("Unexpected error:", sys.exc_info()[0])
        return HttpResponse(json.dumps(resp), content_type='application/json')
    
    else:
        return render(request,'forbiden.html')


def delete_sale_sellers(request):
    if request.user.is_authenticated:

        resp = {'status':'failed', 'msg':''}
        id = request.POST.get('id')
        try:
            ventaOriginalCodigo=sellerSales.objects.filter(id=id).values('id')
            origenVendedor=sellerSales.objects.filter(id=id).values('origin')
            ventaOriginalCodigo=ventaOriginalCodigo[0]['id']
            origenVendedor=origenVendedor[0]['origin']


            antesEliminacion=sellerSalesItems.objects.filter(sale_id_id = ventaOriginalCodigo)

            for articulo in antesEliminacion:
                cantidadArticulosEliminar=articulo.qty
                productID=articulo.product_id_id
                sellerInventory.objects.filter(product_id_id = productID,seller_id_id = origenVendedor).update(qty = F('qty') + cantidadArticulosEliminar)


            delete = sellerSalesItems.objects.filter(sale_id_id = ventaOriginalCodigo).delete()
            
            delete = sellerSales.objects.filter(id = id).delete()
            resp['status'] = 'success'
            messages.success(request, 'Registro de venta eliminado.')
        except:
            resp['msg'] = "Ha ocurrido un error."
            ###print("Unexpected error:", sys.exc_info()[0])
        return HttpResponse(json.dumps(resp), content_type='application/json')
    
    else:
        return render(request,'forbiden.html')
    
def delete_charge_sellers(request):
    if request.user.is_authenticated:

        resp = {'status':'failed', 'msg':''}
        id = request.POST.get('id')
        print(id)
        code=RegistroInventarioVendedores.objects.all().filter(id=id).values('code')
        code=code[0]['code']
        try:
            delete = RegistroInventarioVendedores.objects.filter(code = code).delete()
            resp['status'] = 'success'
            messages.success(request, 'Registro de venta eliminado.')
        except:
            resp['msg'] = "Ha ocurrido un error."
            ###print("Unexpected error:", sys.exc_info()[0])
        return HttpResponse(json.dumps(resp), content_type='application/json')
    
    else:
        return render(request,'forbiden.html')


def dash_ventas(request):
    if request.user.is_authenticated:

        return render(request,'dashVentas.html')
    else:
        return render(request,'forbiden.html')

@login_required
def financeDashboard(request):
    today=timezone.now().date()
    
    lunesSemanaPasada=today-timedelta(days=today.weekday()+7)
    domingoSemanaPasada=lunesSemanaPasada+timedelta(days=6)
    
    diasDesdeLunes=today.weekday()
    lunesSemana = today - timedelta(days=diasDesdeLunes)
    # #print(lunesSemana)
    domingoSemana=lunesSemana+timedelta(days=7)
    # #print(domingoSemana)
    vendedorMasRepetido="Ninguno"
    productMasVendidoSellerSemanal="Ninguno"
    total_public_price=0
    total_cost=0
    gananciaTotal=0

    try:
        vendedorMasRepetido=sellerSales.objects.filter(date_added__range=[lunesSemana,domingoSemana]).values('origin').annotate(origin_count=Count('origin')).order_by('-origin_count').first()#OBTENER VENDEDOR SEMANAL QUE HIZO MAS VENTAS
        vendedorMasRepetido=User.objects.all().filter(id=vendedorMasRepetido['origin'])#EN VISTA REFINAR PARA QUE MUESTRE EL NOMBRE DEL VENDEDOR
    except:
        vendedorMasRepetido="Ninguno"

    

    puntoVentaMasRepetido=Sales.objects.filter(date_added__range=[lunesSemana,domingoSemana]).values('origin').annotate(origin_count=Count('origin')).order_by('-origin_count').first()#OBTENER PUNTO DE VENTA QUE HIZO MÁS VENTAS
    if puntoVentaMasRepetido is None:
        puntoVentaMasRepetido="No hay punto de venta con más ventas todavía"
    else:
        puntoVentaMasRepetido=User.objects.all().filter(id=puntoVentaMasRepetido['origin'])# EN VISTA REFINAR PARA QUE MUESTRE EL NOMBRE DEL PUNTO DE VENTA

    
    
    

    ventasSemanalesSellers=sellerSales.objects.filter(date_added__range=[lunesSemana,domingoSemana]).values_list('id',flat=True)#OBTENGO LAS VENTAS SEMANALES PARA VENDEDORES
    articulosSemanalesSellers=sellerSalesItems.objects.filter(sale_id_id__in=ventasSemanalesSellers)
    try:
        ventasAgrupadas = articulosSemanalesSellers.values('product_id_id').annotate(total_qty=Sum('qty')).order_by('-total_qty').first()
    except:
        ventasAgrupadas="Nada"
    if ventasAgrupadas is None:
        pass
    else:
        productMasVendidoSellerSemanal=articulosModel.objects.all().filter(id=ventasAgrupadas['product_id_id'])
    ventasSemanalesVendedores=sellerSales.objects.filter(date_added__range=[lunesSemana,domingoSemana])
    
    grouped_sales = defaultdict(list)#AGRUPAMIENTO PARA PODER SEPARARLOS POR TABLAS
    for sale in ventasSemanalesVendedores:
        userData=User.objects.all().filter(id=sale.origin).get()
        sale.origin="Usuario:"+userData.username+". Nombre: " + userData.first_name+" "+userData.last_name
        articulosVenta=sellerSalesItems.objects.all().filter(sale_id_id=sale.id)
        gananciaPorVenta=0
        acumuladorProductosPorVenta=0
        for elemento in articulosVenta:
            costoProducto=articulosModel.objects.all().filter(id=elemento.product_id_id).get()
            gananciaPorProducto=elemento.total-(costoProducto.costo*elemento.qty)
            acumuladorProductosPorVenta=acumuladorProductosPorVenta+elemento.qty
            gananciaPorVenta=gananciaPorVenta+gananciaPorProducto

        sale.gananciaPorVenta=gananciaPorVenta
        sale.acumuladorProductosPorVenta=acumuladorProductosPorVenta
        
        grouped_sales[sale.origin].append(sale)

    # #print(grouped_sales)
    
    

    ventasSemanalesPorVendedorOrigin=ventasSemanalesVendedores.values('origin').annotate(total_ventas=Sum('grand_total'))
    # #print(ventasSemanalesVendedores)
    for elemento in ventasSemanalesPorVendedorOrigin:#salarios
        ventas=elemento['total_ventas']
        identificadorUsuario=elemento['origin']
        datos=User.objects.all().filter(id=identificadorUsuario).get()
        elemento['origin']="Usuario: "+datos.username+". Nombre Completo: "+datos.first_name+" "+datos.last_name+"."
        if ventas >= 22000 and  ventas < 26000:
            elemento['salario'] = ventas*0.11
        elif ventas >= 26000 and ventas < 30000:
            elemento['salario'] = ventas*0.12
        elif ventas >= 30000 and ventas < 34000:
            elemento['salario'] = ventas*0.13
        elif ventas >= 34000 and ventas < 40000:
            elemento['salario'] = ventas*0.14
        elif ventas >= 40000:
            elemento['salario'] = ventas*0.15
        elif ventas < 22000:
            elemento['salario'] = 1750
        else:
            elemento['salario'] = 0
    
    ventasSemanalesPV=Sales.objects.filter(date_added__range=[lunesSemana,domingoSemana]).values_list('id',flat=True)
    ventasSemanalesPVNormal=Sales.objects.filter(date_added__range=[lunesSemana,domingoSemana])
    dineroSemanalPV=0
    cantidadVentasSemanalesPV=0
    for elemento in ventasSemanalesPVNormal:
        dineroSemanalPV=elemento.grand_total+dineroSemanalPV
        cantidadVentasSemanalesPV+=int(1)

    dineroSemanalSeller=0
    cantidadVentasSemanalesVendedores=0
    for elemento in ventasSemanalesVendedores:
        dineroSemanalSeller=elemento.grand_total+dineroSemanalSeller
        cantidadVentasSemanalesVendedores+=int(1)

    cantidadTotalVentasSemanales=cantidadVentasSemanalesVendedores+cantidadVentasSemanalesPV

    dineroSemanalTotal=dineroSemanalSeller+dineroSemanalPV

    articulosSemanalesPV=salesItems.objects.filter(sale_id_id__in=ventasSemanalesPV)
    
    ventasAgrupadasPV = articulosSemanalesPV.values('product_id_id').annotate(total_qty=Sum('qty')).order_by('-total_qty').first()
    try:
        productMasVendidoPVSemanal=articulosModel.objects.all().filter(id=ventasAgrupadasPV.product_id_id)
    except:
        productMasVendidoPVSemanal="Ninguno"


    
    articulosSemanalesGlobales = articulosSemanalesPV.union(articulosSemanalesSellers)
    
    qty_totals = defaultdict(int)
    for elemento in articulosSemanalesGlobales:
        qty_totals[elemento.product_id_id] += elemento.qty

    try:
        max_product_id = max(qty_totals, key=qty_totals.get)
        productoGlobalMasVendidoSemanal=articulosModel.objects.all().filter(id=max_product_id)
    except:
        max_product_id=0
        productoGlobalMasVendidoSemanal="No hay"
    
    todaySellerSales=sellerSales.objects.all().filter(date_added__date=today)
    todayPVSales=Sales.objects.all().filter(date_added__date=today)
    historicSellerSales=sellerSales.objects.all()
    historicPVSales=Sales.objects.all()
    
    addSalesSellerAcumulator=0#acumulador de ventas de vendedores hoy
    numerosVentasHoySellers=0#acumulador de numero de ventas de vendedores hoy
    for elemento in todaySellerSales:#para calculo de total de ventas en dinero y cantidad de ventas de vendedores
        addSalesSellerAcumulator=addSalesSellerAcumulator+elemento.grand_total
        numerosVentasHoySellers+=int(1)
    
    addPVSalesAcumulator=0
    numerosVentaPVHoy=0
    for elemento in todayPVSales:#para calculo total de ventas de puntos de venta y numero de ventas de puntos de venta
        addPVSalesAcumulator=addPVSalesAcumulator+elemento.grand_total
        numerosVentaPVHoy+=int(1)

    addHistoricPVSales=0
    numerosHistoricPVSales=0
    for elemento in historicPVSales:# para calculo historico de ventas PUNTOS DE VENTA dinero y numero
        addHistoricPVSales=addHistoricPVSales+elemento.grand_total
        numerosHistoricPVSales+=int(1)

    addHistoricSellerSales=0
    numerosHistoricSellerSales=0
    for elemento in historicSellerSales:
        addHistoricSellerSales=addHistoricSellerSales+elemento.grand_total
        numerosHistoricSellerSales+=int(1)

    totalVentasHoy=addPVSalesAcumulator+addSalesSellerAcumulator#total de ventas hoy dinero
    numeroTotalVentasHoy=numerosVentasHoySellers+numerosVentaPVHoy#total ventas hoy numero
    totalVentasHistorico=addHistoricSellerSales+addHistoricPVSales#total ventas historico dinero
    totalNumeroVentasHistorico=numerosHistoricPVSales+numerosHistoricSellerSales#total ventas historico numero

    lista = sellerInventory.objects.all()
    # listaAgrupada=sellerInventory.objects.values('seller_id_id')
    listaAgrupada=defaultdict(list)
    acumuladorValorStockVendedor=0
    for elemento in lista:
        userData=User.objects.all().filter(id=elemento.seller_id_id).get()
        elemento.seller_id_id="Usuario:"+userData.username+". Nombre: " + userData.first_name+" "+userData.last_name
        # #print(elemento.seller_id_id)
        elemento.costo_total = elemento.qty * elemento.product_id.costo
        elemento.precio_publico_total = elemento.qty * elemento.product_id.precioVentaVendedorReparto
        elemento.ganancia = elemento.precio_publico_total - elemento.costo_total
        elemento.gananciaUnitaria = elemento.product_id.precioVentaVendedorReparto - elemento.product_id.costo

        elemento.gananciaTotal=elemento.product_id.precioVentaVendedorReparto-elemento.product_id.costo
        
        listaAgrupada[elemento.seller_id_id].append(elemento)

    sumatorios={}

    #OBTENER EL VALOR DE SU STOCK DE VENDEDORES
    listaUsuarios = User.objects.all().values('id','username','first_name','last_name')
    usuarios_dict = {
        user['id']: {
            'last_name': user['last_name'],
            'username': user['username']
            }
            for user in listaUsuarios}
    
    resultados=[]
    for llave, valor in usuarios_dict.items():
        # print(llave)#identificador del usuario
        userData=User.objects.all().filter(id=llave).get()
        nombreUsuario="Usuario: "+userData.username+" Nombre completo: "+userData.first_name+" "+ userData.last_name
        permisosEspeciales=usersPermission.objects.filter(user_id=llave).get()
        # print(valor)
        inventarioVendedor=sellerInventory.objects.all().filter(seller_id_id=llave)#recuperamos su inventario
        valordeStock=0
        valorStockLimites=0
        acumuladorProductos=0
        for elemento in inventarioVendedor:
            datosProducto=articulosModel.objects.filter(id=elemento.product_id_id).get()
            if permisosEspeciales.is_externalSeller:
                elemento.precio=datosProducto.precioVentaVendedorExterno
            else:
                elemento.precio=datosProducto.precioVentaVendedorReparto
            elemento.costo=datosProducto.costo
            valordeStock+=(elemento.costo*elemento.qty)#costo para becaana *cantidad
            valorStockLimites+=(elemento.precio*elemento.qty)
            acumuladorProductos+=elemento.qty

        usuario_resultado = {
            "nombreUsuario": nombreUsuario,
            "valordeStock": valordeStock,
            "valorStockLimites":valorStockLimites,
            "acumuladorProductos": acumuladorProductos
            }
        resultados.append(usuario_resultado)



    


    for llave,valores in listaAgrupada.items():#OBTENER EL CALCULO DE GANANCIAS TOTAL
        

        sumatorios[llave] = {
            'gananciaProductoReparto': 0,
            'gananciaProductoRepartoExterno': 0
        }

        for elemento in valores:
            productID=elemento.product_id_id
            cantidad=elemento.qty
            datosProducto=articulosModel.objects.all().filter(id=productID).get()
            costoProductos=datosProducto.costo
            precioVentaReparto=datosProducto.precioVentaVendedorReparto
            precioVentaRepartoExterno=datosProducto.precioVentaVendedorExterno
            gananciaProductoReparto=(cantidad*precioVentaReparto)-(cantidad*costoProductos)
            gananciaProductoRepartoExterno=(cantidad*precioVentaRepartoExterno)-(cantidad*costoProductos)
            
            sumatorios[llave]['gananciaProductoReparto'] += gananciaProductoReparto
            sumatorios[llave]['gananciaProductoRepartoExterno'] += gananciaProductoRepartoExterno

    try:
        total_public_price = sum(item.precio_publico_total for item in lista)
        total_cost = sum(item.qty * item.product_id.costo for item in lista)        
        gananciaTotal = total_public_price - total_cost
    except:
        pass


    total_public_price = sum(item.precio_publico_total for item in lista)
    total_cost = sum(item.qty * item.product_id.costo for item in lista)
    gananciaTotal = total_public_price - total_cost

    ventasSemanalesPasadasSellers=sellerSales.objects.filter(date_added__range=[lunesSemanaPasada,domingoSemanaPasada])


    grouped_sales_pasadas = defaultdict(list)#AGRUPAMIENTO PARA PODER SEPARARLOS POR TABLAS
    for sale in ventasSemanalesPasadasSellers:
        userData=User.objects.all().filter(id=sale.origin).get()
        sale.origin="Usuario:"+userData.username+". Nombre: " + userData.first_name+" "+userData.last_name
        articulosVenta=sellerSalesItems.objects.all().filter(sale_id_id=sale.id)
        gananciaPorVenta=0
        acumuladorProductosPorVenta=0
        for elemento in articulosVenta:
            costoProducto=articulosModel.objects.all().filter(id=elemento.product_id_id).get()
            gananciaPorProducto=elemento.total-(costoProducto.costo*elemento.qty)
            acumuladorProductosPorVenta=acumuladorProductosPorVenta+elemento.qty
            gananciaPorVenta=gananciaPorVenta+gananciaPorProducto

        sale.gananciaPorVenta=gananciaPorVenta
        sale.acumuladorProductosPorVenta=acumuladorProductosPorVenta
        
        grouped_sales_pasadas[sale.origin].append(sale)

    ventasSemanalesPasadasPorVendedorOrigin=ventasSemanalesPasadasSellers.values('origin').annotate(total_ventas=Sum('grand_total'))
    # #print(ventasSemanalesVendedores)
    for elemento in ventasSemanalesPasadasPorVendedorOrigin:#salarios
        ventas=elemento['total_ventas']
        identificadorUsuario=elemento['origin']
        datos=User.objects.all().filter(id=identificadorUsuario).get()
        elemento['origin']="Usuario: "+datos.username+". Nombre Completo: "+datos.first_name+" "+datos.last_name+"."
        if ventas >= 22000 and  ventas < 26000:
            elemento['salario'] = ventas*0.11
        elif ventas >= 26000 and ventas < 30000:
            elemento['salario'] = ventas*0.12
        elif ventas >= 30000 and ventas < 34000:
            elemento['salario'] = ventas*0.13
        elif ventas >= 34000 and ventas < 40000:
            elemento['salario'] = ventas*0.14
        elif ventas >= 40000:
            elemento['salario'] = ventas*0.15
        elif ventas < 22000:
            elemento['salario'] = 1750
        else:
            elemento['salario'] = 0
    

    
    



    context = {
        'sumatorios':sumatorios,
        'gananciaTotal':gananciaTotal,
        'total_cost':total_cost,
        'total_public_price':total_public_price,
        'listaAgrupada': dict(listaAgrupada), 
        'total_public_price': total_public_price,
        'total_cost': total_cost, 
        'gananciaTotal': gananciaTotal,
        'totalVentasHoy':totalVentasHoy,#dinero hoy
        'ventas_hoy_vendedores':addSalesSellerAcumulator,#dinero hoy
        'ventas_hoy_puntos_venta':addPVSalesAcumulator,#dinero hoy
        'numerosVentaPVHoy':numerosVentaPVHoy,#cantidad hoy
        'numerosVentasHoySellers':numerosVentasHoySellers,#cantidad hoy 
        'numeroTotalVentasHoy':numeroTotalVentasHoy,#cantidad hoy
        'dineroSemanalTotal':dineroSemanalTotal,# dinero semanal global
        'dineroSemanalSeller':dineroSemanalSeller,# dinero semanal vendedores
        'dineroSemanalPV':dineroSemanalPV,# dinero semanal puntos de venta
        'cantidadTotalVentasSemanales':cantidadTotalVentasSemanales,# cantidad semanal global
        'cantidadVentasSemanalesVendedores':cantidadVentasSemanalesVendedores,# cantidad semanal vendedores
        'cantidadVentasSemanalesPV':cantidadVentasSemanalesPV,# cantidad semanal puntos de venta
        'ventas_historico_vendedores':addHistoricSellerSales, #dinero historico puntos de venta
        'ventas_historico_puntos_venta':addHistoricPVSales, # dinero historico puntos de venta
        'numero_ventas_historico_vendedores':numerosHistoricSellerSales, #cantidad vendedores historicos
        'numero_ventas_historico_puntos_venta':numerosHistoricPVSales, #cantidad vendedores puntos de venta
        'total_ventas_historico':totalVentasHistorico, #dinero total historico
        'total_ventas_historico_numero':totalNumeroVentasHistorico, #cantidad total historico
        'puntoVentaMasRepetido':puntoVentaMasRepetido,#mejor punto de venta semanal
        'vendedorMasRepetido':vendedorMasRepetido, #mejor vendedor semanal
        'productMasVendidoSellerSemanal':productMasVendidoSellerSemanal, # mejor producto semanal vendedor
        'productMasVendidoPVSemanal':productMasVendidoPVSemanal, #mejor producto semanal puntos de venta
        'productoGlobalMasVendidoSemanal':productoGlobalMasVendidoSemanal, #mejor producto semanal
        'ventasSemanalesPorVendedorOrigin':ventasSemanalesPorVendedorOrigin,#parámetro de salario
        'grouped_sales':dict(grouped_sales),#ventas agrupadas para vendedores
        'ventasSemanalesPasadasPorVendedorOrigin':ventasSemanalesPasadasPorVendedorOrigin,#parámetro de salario
        'grouped_sales_pasadas':dict(grouped_sales_pasadas),
        'resultados':resultados,
        }
    return render(request, 'finance.html',context)


def sellersDashboard(request):#DASHBOARD DE VENDEDORES DE REPARTO
    if request.user.is_authenticated:
        return render(request,'vendedoresDash.html')
    else:
        return render(request,'forbiden.html')


def settingsView(request):#POSIBLE AJUSTE DE COMBUSTIBLE
    if request.user.is_authenticated:
        return render(request,'settings.html')
    else:
        return render(request,'forbiden.html')


def sellersListView(request):#LISTADO DE VENDEDORES
    context = {
        "active_icon": "sellers",
        "customers": User.objects.all().filter(is_active=True, is_superuser=False, is_staff=False)
    }
    return render(request, "customers.html", context=context)


def sellersAddView(request):#REGISTRO DE VENDEDORES
    if request.method == 'POST':
        # Save the POST arguments
        data = request.POST

        attributes = {
            "first_name": data['first_name'],
            "last_name": data['last_name'],
            "address": data['address'],
            "email": data['email'],
            "phone": data['phone'],
        }

        # Check if a customer with the same attributes exists
        if Seller.objects.filter(**attributes).exists():
            messages.error(request, 'Customer already exists!',
                           extra_tags="warning")
            return redirect('sellersAdd')

        try:
            # Create the customer
            new_customer = Seller.objects.create(**attributes)

            # If it doesn't exist save it
            new_customer.save()

            messages.success(request, 'Customer: ' + attributes["first_name"] + " " +
                             attributes["last_name"] + ' created successfully!', extra_tags="success")
            return redirect('sellersList')
        except Exception as e:
            messages.success(
                request, 'There was an error during the creation!', extra_tags="danger")
            ###print(e)
            return redirect('sellersAdd')

    return render(request, "customers_add.html", )


def sellersUpdateView(request, seller_id):#ACTUALIZACIÓN DE INFORMACIÓN DE VENDEDORES
    """
    Args:
        request:
        seller_id : The customer's ID that will be updated
    """

    # Get the customer
    try:
        # Get the customer to update
        customer = Seller.objects.get(id=seller_id)
    except Exception as e:
        messages.success(
            request, 'Error al obtener información del cliente!', extra_tags="danger")
        ###print(e)
        return redirect('sellersList')

    context = {
        "active_icon": "customers",
        "customer": customer,
    }

    if request.method == 'POST':
        try:
            # Save the POST arguments
            data = request.POST
            ###print(data)

            attributes = {
                "first_name": data['first_name'],
                "last_name": data['last_name'],
                "address": data['address'],
                "email": data['email'],
                "phone": data['phone'],
            }

            # Check if a customer with the same attributes exists
            if Seller.objects.filter(**attributes).exists():
                messages.error(request, 'Vendedor ya existe!',
                               extra_tags="warning")
                return redirect('sellersAdd')
            

            customer = Seller.objects.get(id=seller_id)
            customer.first_name=data['first_name']
            customer.last_name=data['last_name']
            customer.address= data['address']
            customer.email= data['email']
            customer.phone= data['phone']


            customer.save()


            messages.success(request, 'Vendedor: ' + customer.get_full_name() +
                             ' actualizado satisfactoriamente!', extra_tags="success")
            return redirect('sellersList')
        except Exception as e:
            messages.success(
                request, 'Error en la actualización!', extra_tags="danger")
            ###print(e)
            return redirect('sellersList')

    return render(request, "customers_update.html", context=context)


def sellersDeleteView(request, seller_id):#ELIMINACIÓN DE VENDEDORES
    """
    Args:
        request:
        customer_id : The customer's ID that will be deleted
    """
    try:
        # Get the customer to delete
        seller = Seller.objects.get(id=seller_id)
        seller.delete()
        messages.success(request, 'Vendedor: ' + seller.get_full_name() +
                         ' eliminado!', extra_tags="success")
        return redirect('sellersList')
    except Exception as e:
        messages.success(
            request, 'Ocurrió un error durante la eliminación!', extra_tags="danger")
        ###print(e)
        return redirect('sellersList')


def inventariosVendedores(request, pk=None):  # INVENTARIOS DE VENDEDORES 
    if request.user.is_authenticated:
        
        lista = sellerInventory.objects.all()
        for item in lista:
            item.costo_total = item.qty * item.product_id.costo
            item.precio_publico_total = item.qty * item.product_id.precioVentaVendedorReparto
            item.ganancia = item.precio_publico_total - item.costo_total
            item.gananciaUnitaria = item.product_id.precioVentaVendedorReparto - item.product_id.costo

        total_public_price = sum(item.precio_publico_total for item in lista)
        total_cost = sum(item.qty * item.product_id.costo for item in lista)
        gananciaTotal = total_public_price - total_cost

        if request.method == 'POST':
            form=InventoryFormSeller(request.POST)
            if form.is_valid():
                user = form.cleaned_data['user']
                product = form.cleaned_data['product']
                quantity = form.cleaned_data['quantity']
                inventory_item, created = sellerInventory.objects.get_or_create(
                    seller_id=user,
                    product_id=product
                    )
                if not created:
                    inventory_item.qty += quantity
                else:
                    inventory_item.qty = quantity

                product.cantidad-=quantity
                product.save()
                
                RegistroInventarioVendedores.objects.create(
                        usuario=user,
                        nombre_producto=product,  # Ajusta esto según el nombre del campo en tu modelo articulosModel
                        cantidad=quantity
                        )

                inventory_item.save()

                return redirect('sellers')
        else:
            form = InventoryFormSeller()
        
        # Renderizar el formulario y otros datos
        return render(request, 'listaInventariosVendedores.html', {'form': form, 'lista': lista, 'total_public_price': total_public_price, 'total_cost': total_cost, 'gananciaTotal': gananciaTotal})

    else:
        return render(request, 'forbiden.html')


def sellersDashboardSellView(request):
    if request.user.is_authenticated:
        return render(request,'dashVentasSeller.html')
    else:
        return render(request,'forbiden.html')


def registrarVentaVendedorView(request):
    if request.user.is_authenticated:
        id_vendedor=request.user.id
        products = sellerInventory.objects.all().filter(seller_id=id_vendedor)######NECESARIO PARA FILTRAR SOLO EL INVENTARIO DE CADA VENDEDOR

        product_json = []
        ###print(products)
        
        for product in products:
            ###print(product.product_id_id)
            ###print(product)   
            modeloOriginal=articulosModel.objects.all().filter(id=product.product_id_id).get()
            precio=modeloOriginal.precioVentaVendedorReparto
            product_json.append({'id':product.id, 'name':product.nombreArticulo, 'price':float(precio),'qty':float(product.qty),'general_id':product.product_id_id})
            
            
        context = {
            'page_title' : "Punto de venta",
            'products' : products,
            
            'product_json' : json.dumps(product_json)
        }
        # return HttpResponse('')
        return render(request, 'registrarVentaVendedoresReparto.html',context)
    else:
        return render(request,'forbiden.html')
    

def registrarVentaVendedorExternoView(request):
    if request.user.is_authenticated:
        id_vendedor=request.user.id
        products = sellerInventory.objects.all().filter(seller_id=id_vendedor)######NECESARIO PARA FILTRAR SOLO EL INVENTARIO DE CADA VENDEDOR
        product_json = []
        ###print(products)
        for product in products:

            modeloOriginal=articulosModel.objects.all().filter(id=product.product_id_id).get()
            precio=modeloOriginal.precioVentaVendedorExterno
            ###print(product.product_id_id)
            ###print(product)            
            product_json.append({'id':product.id, 'name':product.nombreArticulo, 'price':float(precio),'qty':float(product.qty),'general_id':product.product_id_id})
        context = {
            'page_title' : "Punto de venta",
            'products' : products,
            'product_json' : json.dumps(product_json)
        }
        # return HttpResponse('')
        return render(request, 'registrarVentaVendedoresReparto.html',context)
    else:
        return render(request,'forbiden.html')
    

def posSeller(request):
    if request.user.is_authenticated:
        #products = articulosModel.objects.all()
        products = sellerInventory.objects.all().filter(seller_id=request.user.id)######NECESARIO PARA FILTRAR SOLO EL INVENTARIO DE CADA VENDEDOR

        sucursales = puntoVenta.objects.all()

        product_json = []
        for product in products:

            product_json.append({'id':product.product_id_id, 'name':product.nombreArticulo, 'price':float(product.precioVentaPublico)})
        context = {
            'page_title' : "Punto de venta",
            'products' : products,
            'product_json' : json.dumps(product_json),
            'sucursales':sucursales,
        }
        # return HttpResponse('')
        return render(request, 'registrarVenta.html',context)
    else:
        return render(request,'forbiden.html')


def save_posSeller(request):##EJEMPLO
    resp = {'status':'failed','msg':''}
    data = request.POST
    ###print(data)
    pref = datetime.now().year + datetime.now().year * 100000000
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = sellerSales.objects.filter(code = str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        sales = sellerSales(code=code, sub_total = data['sub_total'], tax = data['tax'], tax_amount = data['tax_amount'], grand_total = data['grand_total'], tendered_amount = data['tendered_amount'], amount_change = data['amount_change'],origin=request.user.id)
        sales.save()
        sale_id = sellerSales.objects.last().pk
        i = 0
        cantidadTotalProductos=0
        for prod in data.getlist('product_id[]'):
            #product_id = prod 
            sale = sellerSales.objects.filter(id=sale_id).first()
            product = articulosModel.objects.all().filter(id=prod).first()
            qty = int(data.getlist('qty[]')[i] )
            cantidadTotalProductos=cantidadTotalProductos+qty
            
            price = data.getlist('price[]')[i]
            total = float(qty) * float(price)
            discount = float(data.getlist('disc[]')[i])
            ###print({'sale_id' : sale, 'product_id' : product, 'qty' : qty, 'price' : price, 'total' : total})

            sellerSalesItems(sale_id = sale, product_id = product, qty = qty, price = price, total = total,discount = discount).save()

            productoDecremento=sellerInventory.objects.get(product_id=prod,seller_id_id=request.user.id)
            if productoDecremento.qty>0 and productoDecremento.qty>=qty:
                productoDecremento.qty-=qty
                productoDecremento.save()
            
            i += int(1)
            
            # sellerInventory.qty=sellerInventory.qty-qty
            # sellerInventory.save()

            
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
    except Exception as e:
        resp['msg'] = "Ocurrió un error"
        #print("Unexpected errors:", e)###############################
    return HttpResponse(json.dumps(resp),content_type="application/json")

def receiptChargeSeller(request):
    if request.user.is_authenticated:
        # #print(request.GET)
        id = request.GET.get('id')
        transaction = {'date_added':timezone.now()}

        usuarioData=User.objects.all().filter(id=request.user.id).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        total_value = 0
        acumulador_total_productos=0
        ItemList = RegistroInventarioVendedores.objects.filter(code = id).all()# LISTA TODOS LOS ELEMENTOS DEL REGISTRO
        for elemento in ItemList:
            #print("impresion: ",elemento)
            # #print(elemento.product_id)
            articulo=articulosModel.objects.all().filter(id=elemento.product_id).get()# OBTEN LA INFORMACION DEL ARTICULO ORIGINAL
            # #print(articulo.precioVentaVendedorReparto)
            total_value=total_value+(elemento.cantidad*articulo.precioVentaVendedorReparto)
            elemento.nombreArticulo=articulo.nombreArticulo
            elemento.precioPV=articulo.precioVentaVendedorReparto
            
            acumulador_total_productos+=elemento.cantidad
            ##print(acumulador_total_productos)
            elemento.precioVExterno=articulo.precioVentaVendedorExterno
            elemento.precioVendedor=articulo.precioVentaVendedorReparto
            
        
        context = {
            "total":total_value,
            # "total_discounts":total_discounts,
            "transaction" : transaction,
            'total_productos':acumulador_total_productos,

            "salesItems" : ItemList,
            'nombreUsuario':nombreUsuario,
        }

        return render(request, 'receiptCharge.html',context)
    else:
        return render(request,'forbiden.html')

    

def receiptSeller(request):
    if request.user.is_authenticated:

        id = request.GET.get('id')
        sales = sellerSales.objects.filter(id = id).first()
        transaction = {}
        for field in sellerSales._meta.get_fields():
            if field.related_model is None:
                transaction[field.name] = getattr(sales,field.name)
        if 'tax_amount' in transaction:
            transaction['tax_amount'] = format(float(transaction['tax_amount']))

        
        
        # transaction['code']=int(transaction['code'])+100000000
        # transaction['code']=str(transaction['code'])
        ItemList = sellerSalesItems.objects.filter(sale_id = sales).all()
        total_discounts=0
        acumulador_total_productos=0
        for elemento in ItemList:
            discount=(elemento.discount*elemento.price*elemento.qty)/100
            # ##print(discount)
            total_discounts+=discount
            acumulador_total_productos=acumulador_total_productos+elemento.qty

        total=transaction["grand_total"]+total_discounts
        ventaInformacion=sellerSales.objects.all().filter(code= transaction['code']).values('origin')
        usuarioData=User.objects.all().filter(id=ventaInformacion[0]['origin']).get()# NOMBRE DEL USUARIO AL TICKET
        
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        
        context = {
            "total":total,
            "total_discounts" : total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList,
            'total_productos':acumulador_total_productos,
            "nombreUsuario":nombreUsuario,
        }

        return render(request, 'receipt.html',context)
    else:
        return render(request,'forbiden.html')
    # return HttpResponse('')


def consultaPropioInventario(request,id_vendedor):
    if request.user.is_authenticated:
        ###print(id_vendedor)
        id=id_vendedor
        articulosVendedor=sellerInventory.objects.all().filter(seller_id=id_vendedor)
        permisosEspeciales=usersPermission.objects.filter(user_id=id).get()


        costoStock=0
        for elemento in articulosVendedor:
            datosProducto=articulosModel.objects.filter(id=elemento.product_id_id).get()
            if permisosEspeciales.is_externalSeller:
                elemento.precioVentaVendedor=datosProducto.precioVentaVendedorExterno
            else:
                elemento.precioVentaVendedor=datosProducto.precioVentaVendedorReparto
            costoStock=costoStock+elemento.qty*elemento.precioVentaVendedor
            
        context={
            'lista':articulosVendedor,
            'costoStock':costoStock,
        }
        return render(request,'vendedorConsultaPropioInventario.html',context)
    else:
        return render(request,'forbiden.html')


def consultaPropioInventarioExterno(request,id_vendedor):
    if request.user.is_authenticated:
        ###print(id_vendedor)
        id=id_vendedor
        permisosEspeciales=usersPermission.objects.filter(user_id=id).get()
        articulosVendedor=sellerInventory.objects.all().filter(seller_id=id_vendedor)

        costoStock=0
        for elemento in articulosVendedor:
            datosProducto=articulosModel.objects.filter(id=elemento.product_id_id).get()
            if permisosEspeciales.is_externalSeller:
                elemento.precioVentaVendedor=datosProducto.precioVentaVendedorExterno
            else:
                elemento.precioVentaVendedor=datosProducto.precioVentaVendedorReparto

            costoStock=costoStock+elemento.qty*elemento.precioVentaVendedor
            
        context={
            'lista':articulosVendedor,
            'costoStock':costoStock,

        }
        return render(request,'vendedorExternoConsultaPropioInventario.html',context)
    else:
        return render(request,'forbiden.html')
    
def consultaPropioInventarioMatriz(request,id_vendedor):
    if request.user.is_authenticated:
        ###print(id_vendedor)
        articulosVendedor=articulosModel.objects.all()
        context={
            'lista':articulosVendedor,
        }
        return render(request,'vendedorMatrizConsultaPropioInventario.html',context)
    else:
        return render(request,'forbiden.html')
    
def eliminarStockPuntoVenta(request,id):
    if request.user.is_authenticated:
        stock_eliminar=stockPuntoVenta.objects.all().filter(id=id)
        stock_eliminar.delete()
        return redirect('addStock')
    else:
        return render(request,'forbiden.html')
    
def costosVendedoresView(request):
    if request.user.is_authenticated:
        lista=costosEmpresaVendedoresModel.objects.all()
        if request.method=="POST":
            form = costosVendedoresForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('costosVendedores')

        else:
            form=costosVendedoresForm()
            return render(request,'costosVendedores.html',context={'form':form,'lista':lista})
    else:
        return render(request,'forbiden.html')
    
def costosPuntosVentaView(request):
    if request.user.is_authenticated:
        lista=costosEmpresaPuntosVentaModel.objects.all()            
        if request.method=="POST":
            form = costosPuntosVentaForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('costosPuntosVenta')

        else:
            form = costosPuntosVentaForm()
            return render(request,'costosPuntosVenta.html',context={'form':form,'lista':lista})
    else:
        return render(request,'forbiden.html')
    
def dashboardCostos(request):
    if request.user.is_authenticated:
        return render(request,'dashCostos.html')
    else:
        return render(request,'forbiden.html')
    
def updateCostSellerView(request, id):
    if request.user.is_authenticated:
        try:
            currentCostSeller=costosEmpresaVendedoresModel.objects.get(id=id)

            if request.method=="POST":
                form=costosVendedoresForm(request.POST,instance=currentCostSeller)
                if form.is_valid():
                    form.save()

                return redirect('costosVendedores')
            else:
                form=costosVendedoresForm(instance=currentCostSeller)
                return render(request,'updateCostSeller.html',context={'currentCostSeller':currentCostSeller,'form': form})
        except:
            return render(request,'updateCostSeller.html',context={'currentCostSeller':currentCostSeller})
    else:
        return render(request,'forbiden.html')
    
def deleteCostSellerView(request,id):
    if request.user.is_authenticated:
        try:
            deleteCostoSeller=costosEmpresaVendedoresModel.objects.get(id=id)
            deleteCostoSeller.delete()
            return redirect('costosVendedores')
        except:
            return redirect('costosVendedores')
    else:
        return render(request,'forbiden.html')

def deleteRegisterSellers(request,id):
    if request.user.is_authenticated:
        try:
            deleteRegister=RegistroInventarioVendedores.objects.get(id=id)
            articulo = articulosModel.objects.get(nombreArticulo=deleteRegister.nombre_producto)
            articulo.cantidad = F('cantidad') + deleteRegister.cantidad
            identificadorUsuario=deleteRegister.usuario_id

            stockSellerV=sellerInventory.objects.all().filter(seller_id=identificadorUsuario,product_id=articulo.pk).get()
            stockSellerV.qty=F('qty')-deleteRegister.cantidad
            stockSellerV.save()

            articulo.save()
            deleteRegister.delete()
            return redirect('reporteInventario')
        except:
            return redirect('reporteInventario')
    else:
        return render(request,'forbiden.html')
    
def deleteRegisterPV(request,id):
    if request.user.is_authenticated:
        try:
            deleteRegister=RegistroInventarioPuntoVenta.objects.get(id=id)
            articulo = articulosModel.objects.get(nombreArticulo=deleteRegister.nombre_producto)
            articulo.cantidad = F('cantidad') + deleteRegister.cantidad
            identificadorUsuario = deleteRegister.usuario_id
            
            
            stockPuntoVentaV=pvInventory.objects.all().filter(seller_id=identificadorUsuario,product_id=articulo.pk).get()
            stockPuntoVentaV.qty=stockPuntoVentaV.qty-deleteRegister.cantidad
            
            stockPuntoVentaV.save()
            articulo.save()
            deleteRegister.delete()
            return redirect('reporteInventario')
        except:
            return redirect('reporteInventario')
    else:
        return render(request,'forbiden.html')

def deleteCostPuntoVentaView(request,id):
    if request.user.is_authenticated:
        try:
            deleteCostoPuntoVenta=costosEmpresaPuntosVentaModel.objects.get(id=id)
            deleteCostoPuntoVenta.delete()
            return redirect('costosPuntosVenta')
        except:
            return redirect('costosPuntosVenta')
    else:
        return render(request,'forbiden.html')
    
def updateCostPuntoVentaView(request, id):
    if request.user.is_authenticated:
        try:
            currentCostPuntosVenta=costosEmpresaPuntosVentaModel.objects.get(id=id)

            if request.method=="POST":
                form=costosPuntosVentaForm(request.POST,instance=currentCostPuntosVenta)
                if form.is_valid():
                    form.save()

                return redirect('costosPuntosVenta')
            else:
                form=costosPuntosVentaForm(instance=currentCostPuntosVenta)
                return render(request,'updateCostPuntoVenta.html',context={'currentCostPuntosVenta':currentCostPuntosVenta,'form': form})
        except:
            return render(request,'updateCostPuntoVenta.html',context={'currentCostPuntosVenta':currentCostPuntosVenta})
    else:
        return render(request,'forbiden.html')

def alertsView(request):
    if request.user.is_authenticated:
        try:
            productos=articulosModel.objects.all()
            id_producto=[]
            producto_list=[]
            cantidad_maxima_list = []
            cantidad_minima_list = []
            for producto in productos:
                id_producto.append(producto.pk)
                producto_list.append(producto.nombreArticulo)
                cantidad_maxima_list.append(producto.cantidadMaxima)
                cantidad_minima_list.append(producto.cantidadMinima)

            productos=pd.DataFrame({'ID':id_producto,'Producto':producto_list,'Minimo':cantidad_minima_list,'Maximo':cantidad_maxima_list})
            # vendedoresI=Seller.objects.all()
            # id_vendedores=[]
            # for vendedor in vendedoresI:
            #     id_vendedores.append(vendedor.pk)
            listaAlertasPuntoVenta=[]
            for stock_item in stockPuntoVenta.objects.all():
                producto=stock_item.producto
                sucursal=stock_item.sucursal

                if stock_item.stock < producto.cantidadMinima:
                    listaAlertasPuntoVenta.append(f"Cantidad del producto {producto.nombreArticulo} (disponible: {stock_item.stock}) para el Punto de venta {sucursal} es inferior al mínimo configurado (minimo: {producto.cantidadMinima})")
                if stock_item.stock > producto.cantidadMaxima:
                    listaAlertasPuntoVenta.append(f"Cantidad del producto {producto.nombreArticulo} (disponible: {stock_item.stock}) para el Punto de venta {sucursal} es superior al máximo configurado ({producto.cantidadMaxima})")


            listaAlertasVendedores=[]
            for inventory_item in sellerInventory.objects.all():
                product = inventory_item.product_id
                seller = inventory_item.seller_id
                # Check if the available quantity is less than the minimum quantity
                if inventory_item.qty < product.cantidadMinima:
                    # Handle the case where the available quantity is less than the minimum quantity
                    listaAlertasVendedores.append(f"Cantidad disponible para el producto: {product.nombreArticulo} (disponible: {inventory_item.qty}) del vendedor: {seller} es menor al mínimo configurado ({product.cantidadMinima})")  
                if inventory_item.qty > product.cantidadMinima:
                    # Handle the case where the available quantity is less than the minimum quantity
                    listaAlertasVendedores.append(f"Cantidad disponible para el producto: {product.nombreArticulo} (disponible: {inventory_item.qty}) del vendedor: {seller} es superior al máximo configurado ({product.cantidadMaxima})")                
        except:
            listaAlertasPuntoVenta.append("Error")
        return render(request,'alerts.html',context={'listaAlertasPuntoVenta':listaAlertasPuntoVenta,'listaAlertasVendedores':listaAlertasVendedores})
    else:
        return render(request,'forbiden.html')

def salesListVendedores(request):
    if request.user.is_authenticated:

        salesVendedor=sellerSales.objects.all().filter(origin=request.user.id)
        sale_data_vendedor=[]
        
        for sale in salesVendedor:
            data = {}
            for field in sale._meta.get_fields(include_parents=False):
                if field.related_model is None:
                    data[field.name] = getattr(sale,field.name)
            data['items'] = sellerSalesItems.objects.filter(sale_id = sale).all()
            data['item_count'] = len(data['items'])
            if 'tax_amount' in data:
                data['tax_amount'] = format(float(data['tax_amount']),'.2f')
            # ###print(data)
            sale_data_vendedor.append(data)
        # ###print(sale_data)  

        context = {
            'page_title':'Sales Transactions',
            'sale_data':sale_data_vendedor,
        }
        # return HttpResponse('')
        return render(request, 'sellerSales.html',context)
    else:
        return render(request,'forbiden.html')

def salesListMatrix(request):
    if request.user.is_authenticated:

        salesVendedor=Sales.objects.all().filter(origin=request.user.id)
        sale_data_vendedor=[]
        
        for sale in salesVendedor:
            data = {}
            for field in sale._meta.get_fields(include_parents=False):
                if field.related_model is None:
                    data[field.name] = getattr(sale,field.name)
            data['items'] = salesItems.objects.filter(sale_id = sale).all()
            data['item_count'] = len(data['items'])
            if 'tax_amount' in data:
                data['tax_amount'] = format(float(data['tax_amount']),'.2f')
            # ###print(data)
            sale_data_vendedor.append(data)
        # ###print(sale_data)  

        context = {
            'page_title':'Sales Transactions',
            'sale_data':sale_data_vendedor,
        }
        # return HttpResponse('')
        return render(request, 'matrixSales.html',context)
    else:
        return render(request,'forbiden.html')


def inventariosPV(request, pk=None):
    if request.user.is_authenticated:
        
        lista = pvInventory.objects.all()

        for item in lista:
            item.costo_total = item.qty * item.product_id.costo
            item.precio_publico_total = item.qty * item.product_id.precioVentaPublico
            item.ganancia = item.precio_publico_total - item.costo_total
            item.gananciaUnitaria = item.product_id.precioVentaPublico - item.product_id.costo

        total_public_price = sum(item.precio_publico_total for item in lista)
        total_cost = sum(item.qty * item.product_id.costo for item in lista)
        gananciaTotal = total_public_price - total_cost

        if request.method == 'POST':
            form = InventoryFormPV(request.POST)
            if form.is_valid():
                user=form.cleaned_data['user']
                product=form.cleaned_data['product']
                quantity=form.cleaned_data['quantity']
                inventory_item, created = pvInventory.objects.get_or_create(
                    seller_id=user,
                    product_id=product
                    )
                if not created:
                    inventory_item.qty += quantity
                else:
                    inventory_item.qty = quantity
                product.cantidad-=quantity
                product.save()
                RegistroInventarioPuntoVenta.objects.create(
                        usuario=user,
                        nombre_producto=product,  # Ajusta esto según el nombre del campo en tu modelo articulosModel
                        cantidad=quantity
                        )
                inventory_item.save()
                return redirect('puntosVenta')

                
        else:
            form = InventoryFormPV()
            return render(request, 'listaInventariosPV.html', {'form': form, 'lista': lista, 'total_cost': total_cost, 'total_public_price': total_public_price, 'gananciaTotal': gananciaTotal})

    else:
        return render(request, 'forbiden.html')


def updateStockPV(request, id):
    if request.user.is_authenticated:
        try:
            userPetition = request.user.id
            
            # Initialize currentStock outside the try block
            currentStock = None
            currentStock = pvInventory.objects.all().filter(id=id).get()
            cantidadActual=currentStock.qty
            productMatrix=articulosModel.objects.get(id=currentStock.product_id_id)

            if request.method == "POST":
                stock = request.POST.get('stock')
                currentStock.qty = stock
                diferencia=int(stock)-cantidadActual
                if diferencia > 0:
                    productMatrix.cantidad -= diferencia
                elif diferencia <0:
                    productMatrix.cantidad -= diferencia
                currentStock.save()
                productMatrix.save()
                
                return redirect('puntosVenta')
            else:
                return render(request, 'updateStockSeller.html', context={'currentStock': currentStock})
        except pvInventory.DoesNotExist:
            
            return render(request, 'updateStockSeller.html', context={'currentStock': currentStock})
        except Exception as e:
            
            return render(request, 'updateStockSeller.html', context={'currentStock': currentStock})
    else:
        return render(request, 'forbidden.html')


def deleteStockPV(request, id):##################################
    if request.user.is_authenticated:
        deleteStockPV=pvInventory.objects.get(id=id)
        deleteStockPV.delete()
        return redirect('puntosVenta')
    else:
        return render(request, 'forbidden.html')


def deleteStockSellers(request, id):##################################
    if request.user.is_authenticated:
        deleteStockSeller=sellerInventory.objects.get(id=id)
        deleteStockSeller.delete()
        return redirect('sellers')
    else:
        return render(request, 'forbidden.html')

def deleteStockSellersFinance(request, id):##################################
    if request.user.is_authenticated:
        deleteStockSeller=sellerInventory.objects.get(id=id)
        deleteStockSeller.delete()
        return redirect('financeDashboard')
    else:
        return render(request, 'forbidden.html')


def registrarVentaPuntosVentaView(request):
    if request.user.is_authenticated:
        id_vendedor=request.user.id
        products = pvInventory.objects.all().filter(seller_id=id_vendedor)######NECESARIO PARA FILTRAR SOLO EL INVENTARIO DE CADA VENDEDOR
        product_json = []
        for product in products:
            articulo = articulosModel.objects.get(pk=product.product_id_id)
            precio_venta_publico = articulo.precioVentaPublico
            product_json.append({'id':product.id, 'name':product.nombreArticulo, 'price':float(precio_venta_publico),'qty':float(product.qty),'general_id':product.product_id_id})
        context = {
            'page_title' : "Punto de venta",
            'products' : products,
            'product_json' : json.dumps(product_json)
        }
        return render(request, 'registrarVentaPV.html',context)
    else:
        return render(request,'forbiden.html')


def posPV(request):
    if request.user.is_authenticated:
        products = pvInventory.objects.all().filter(seller_id=request.user.id)
        sucursales = puntoVenta.objects.all()
        product_json = []
        for product in products:
            product_json.append({'id':product.product_id_id, 'name':product.nombreArticulo, 'price':float(product.precioVentaPublico)})
        context = {
            'page_title' : "Punto de venta",
            'products' : products,
            'product_json' : json.dumps(product_json),
            'sucursales':sucursales,
        }
        # return HttpResponse('')
        return render(request, 'registrarVentaPV.html',context)
    else:
        return render(request,'forbiden.html')


def save_posPV(request):
    resp = {'status':'failed','msg':''}
    data = request.POST
    ###print(data)
    pref = datetime.now().year + datetime.now().year * 1000 
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = Sales.objects.filter(code = str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        sales = Sales(code=code, sub_total = data['sub_total'], tax = data['tax'], tax_amount = data['tax_amount'], grand_total = data['grand_total'], tendered_amount = data['tendered_amount'], amount_change = data['amount_change'],origin=request.user.id)
        sales.save()
        sale_id = Sales.objects.last().pk
        i = 0
        for prod in data.getlist('product_id[]'):
            #product_id = prod 
            sale = Sales.objects.filter(id=sale_id).first()
            product = articulosModel.objects.all().filter(id=prod).first()
            qty = int(data.getlist('qty[]')[i] )
            
            price = data.getlist('price[]')[i]
            discount = float(data.getlist('disc[]')[i])
            total = float(qty) * float(price)
            ###print({'sale_id' : sale, 'product_id' : product, 'qty' : qty, 'price' : price, 'total' : total})

            salesItems(sale_id = sale, product_id = product, qty = qty, price = price, total = total, discount = discount).save()

            productoDecremento=pvInventory.objects.get(product_id=prod,seller_id_id=request.user.id)
            if productoDecremento.qty>0 and productoDecremento.qty>=qty:
                productoDecremento.qty-=qty
                productoDecremento.save()
            
            i += int(1)
            
            # sellerInventory.qty=sellerInventory.qty-qty
            # sellerInventory.save()

            
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        articulosModel.success(request, "Venta guardada.")
    except Exception as e:
        resp['msg'] = "Ocurrió un error"
        ##print("Unexpected errors:", e)###############################
    return HttpResponse(json.dumps(resp),content_type="application/json")

def save_posMatrix(request):
    resp = {'status':'failed','msg':''}
    data = request.POST
    ###print(data)
    pref = datetime.now().year + datetime.now().year * 1000 
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = Sales.objects.filter(code = str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        sales = Sales(code=code, sub_total = data['sub_total'], tax = data['tax'], tax_amount = data['tax_amount'], grand_total = data['grand_total'], tendered_amount = data['tendered_amount'], amount_change = data['amount_change'],origin=request.user.id)
        sales.save()
        sale_id = Sales.objects.last().pk
        i = 0
        for prod in data.getlist('product_id[]'):
            #product_id = prod 
            sale = Sales.objects.filter(id=sale_id).first()
            product = articulosModel.objects.all().filter(id=prod).first()
            qty = int(data.getlist('qty[]')[i] )
            
            price = data.getlist('price[]')[i]
            discount = float(data.getlist('disc[]')[i])
            total = float(qty) * float(price)
            # #print({'sale_id' : sale, 'product_id' : product, 'qty' : qty, 'price' : price, 'total' : total})

            salesItems(sale_id = sale, product_id = product, qty = qty, price = price, total = total, discount = discount).save()

            productoDecremento=articulosModel.objects.get(id=prod)#,seller_id_id=request.user.id)
            if productoDecremento.cantidad>0 and productoDecremento.cantidad>=qty:
                productoDecremento.cantidad-=qty
                productoDecremento.save()
            
            i += int(1)
            
            # sellerInventory.qty=sellerInventory.qty-qty
            # sellerInventory.save()

            
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        articulosModel.success(request, "Venta guardada.")
    except Exception as e:
        #print(e)
        resp['msg'] = "Ocurrió un error"
        ##print("Unexpected errors:", e)###############################
    return HttpResponse(json.dumps(resp),content_type="application/json")


def receiptPV(request):
    if request.user.is_authenticated:
        ##print("Vista puntos venta")
        id = request.GET.get('id')
        sales = Sales.objects.filter(id = id).first()
        transaction = {}
        total_discounts=0
        for field in Sales._meta.get_fields():
            if field.related_model is None:
                transaction[field.name] = getattr(sales,field.name)
        if 'tax_amount' in transaction:
            transaction['tax_amount'] = format(float(transaction['tax_amount']))
        ItemList = salesItemsPV.objects.filter(sale_id = sales).all()

        for elemento in ItemList:
            discount=(elemento.discount*elemento.price*elemento.qty)/100
            ##print(discount)
            total_discounts+=discount
            acumulador_total_productos=acumulador_total_productos+elemento.qty
        total=transaction["grand_total"]+total_discounts
        ventaInformacion=Sales.objects.all().filter(code= transaction['code']).values('origin')
        usuarioData=User.objects.all().filter(id=ventaInformacion[0]['origin']).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        

        context = {
            "total":total,
            "total_discounts":total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList,
            'total_productos':acumulador_total_productos,
            "nombreUsuario":nombreUsuario,
        }

        return render(request, 'receipt.html',context)
    else:
        return render(request,'forbiden.html')
    # return HttpResponse('')

def receiptMatrix(request):
    if request.user.is_authenticated:
        ##print("Vista puntos venta")
        id = request.GET.get('id')
        sales = Sales.objects.filter(id = id).first()
        transaction = {}
        total_discounts=0
        for field in Sales._meta.get_fields():
            if field.related_model is None:
                transaction[field.name] = getattr(sales,field.name)
        if 'tax_amount' in transaction:
            transaction['tax_amount'] = format(float(transaction['tax_amount']))
        ItemList = salesItems.objects.filter(sale_id = sales).all()

        for elemento in ItemList:
            discount=(elemento.discount*elemento.price*elemento.qty)/100
            ##print(discount)
            total_discounts+=discount
        total=transaction["grand_total"]+total_discounts
        usuarioData=User.objects.all().filter(id=request.user.id).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        

        context = {
            "total":total,
            "total_discounts":total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList,
            "nombreUsuario":nombreUsuario,
        }

        return render(request, 'receipt.html',context)
    else:
        return render(request,'forbiden.html')
    # return HttpResponse('')


def pvConsultaInventario(request):
    if request.user.is_authenticated:
        lista=pvInventory.objects.all().filter(seller_id=request.user.id)
        total=0
        for item in lista:
            precio_producto = item.precioVentaVendedor * item.qty
            total += precio_producto
            item.costo = item.product_id.costo

        context={
            'lista':lista,
            'total':total,
        }
        return render(request,'pvConsultaInventario.html',context)
    else:
        return render(request,'forbiden.html')


def registrar_inventario_vendedores(request, pk=None):  # AUTOCARGA DE INVENTARIO VENDEDORES
    if request.user.is_authenticated:
        inventarioVendedor = get_object_or_404(Seller, pk=pk) if pk else None
        lista = sellerInventory.objects.all().filter(seller_id_id=request.user.id)
        fecha_actual = datetime.now().date()
        registro=RegistroInventarioVendedores.objects.all().filter(usuario_id=request.user.id,fecha=fecha_actual)
        products = articulosModel.objects.all()######NECESARIO PARA FILTRAR SOLO EL INVENTARIO DE CADA VENDEDOR
        product_json = []
        ###print(products)
        for product in products:
            ###print(product.product_id_id)
            ###print(product)            
            product_json.append({'id':product.pk, 'name':product.nombreArticulo, 'price':float(product.precioVentaVendedorReparto),'qty':float(product.cantidad),'descripcionArticulo':product.descripcionArticulo})

        for item in lista:
            item.costo_total = item.qty * item.product_id.costo
            item.precio_publico_total = item.qty * item.product_id.precioVentaVendedorReparto
            item.ganancia = item.precio_publico_total - item.costo_total
            item.gananciaUnitaria = item.product_id.precioVentaVendedorReparto - item.product_id.costo

        total_public_price = sum(item.precio_publico_total for item in lista)
        total_cost = sum(item.qty * item.product_id.costo for item in lista)
        gananciaTotal = total_public_price - total_cost

        if request.method == 'POST':
            form = inventarioCargaVendedorForm(request.POST, instance=inventarioVendedor)
            if form.is_valid():
                with transaction.atomic():
                    # Asigna la instancia de usuario actual al campo seller_id antes de guardar el formulario
                    form.instance.seller_id = request.user

                    try:
                        producto_inventario = sellerInventory.objects.get(
                            product_id=form.instance.product_id,
                            seller_id=request.user
                        )
                        # Si el producto ya existe, suma la cantidad proporcionada en el formulario a la cantidad existente
                        producto_inventario.qty += form.instance.qty
                        producto_inventario.save()
                    except sellerInventory.DoesNotExist:
                        # Si el producto no existe, crea un nuevo registro en el inventario
                        ##print("Producto Nuevo")
                        form.save()

                    # Restar la cantidad de inventario agregada del stock disponible en articulosModel
                    instance = form.instance
                    articulo = instance.product_id
                    articulo.cantidad -= instance.qty
                    articulo.save()

                    RegistroInventarioVendedores.objects.create(
                        usuario=request.user,
                        nombre_producto=instance.product_id.nombreArticulo,  # Ajusta esto según el nombre del campo en tu modelo articulosModel
                        cantidad=instance.qty
                        )

                    

                return redirect('cargarInventarioVendedores')
        else:
            form = inventarioCargaVendedorForm(instance=inventarioVendedor)
            return render(request, 'listaInventarioVendedor.html', {'form': form, 'inventario': inventarioVendedor, 'lista': lista, 'total_public_price': total_public_price, 'total_cost': total_cost, 'gananciaTotal': gananciaTotal,'registro':registro,          'product_json' : json.dumps(product_json),'products':products    })

    else:
        return render(request, 'forbiden.html')
    
def registrar_inventario_vendedores_external(request, pk=None):  # AUTOCARGA DE INVENTARIO VENDEDORES EXTERNOS
    if request.user.is_authenticated:
        inventarioVendedor = get_object_or_404(Seller, pk=pk) if pk else None
        lista = sellerInventory.objects.all().filter(seller_id_id=request.user.id)
        fecha_actual = datetime.now().date()
        registro=RegistroInventarioVendedores.objects.all().filter(usuario_id=request.user.id,fecha=fecha_actual)


        for item in lista:
            item.costo_total = item.qty * item.product_id.costo
            item.precio_publico_total = item.qty * item.product_id.precioVentaVendedorExterno
            item.ganancia = item.precio_publico_total - item.costo_total
            item.gananciaUnitaria = item.product_id.precioVentaVendedorExterno - item.product_id.costo

        products = articulosModel.objects.all()######NECESARIO PARA FILTRAR SOLO EL INVENTARIO DE CADA VENDEDOR
        product_json = []
        ###print(products)
        for product in products:
            ###print(product.product_id_id)
            ###print(product)            
            product_json.append({'id':product.pk, 'name':product.nombreArticulo, 'price':float(product.precioVentaVendedorExterno),'qty':float(product.cantidad),'descripcionArticulo':product.descripcionArticulo})

        total_public_price = sum(item.precio_publico_total for item in lista)
        total_cost = sum(item.qty * item.product_id.costo for item in lista)
        gananciaTotal = total_public_price - total_cost

        if request.method == 'POST':
            form = inventarioCargaVendedorForm(request.POST, instance=inventarioVendedor)
            if form.is_valid():
                with transaction.atomic():
                    # Asigna la instancia de usuario actual al campo seller_id antes de guardar el formulario
                    form.instance.seller_id = request.user

                    try:
                        producto_inventario = sellerInventory.objects.get(
                            product_id=form.instance.product_id,
                            seller_id=request.user
                        )
                        # Si el producto ya existe, suma la cantidad proporcionada en el formulario a la cantidad existente
                        producto_inventario.qty += form.instance.qty
                        producto_inventario.save()
                    except sellerInventory.DoesNotExist:
                        # Si el producto no existe, crea un nuevo registro en el inventario
                        ##print("Producto Nuevo")
                        form.save()

                    # Restar la cantidad de inventario agregada del stock disponible en articulosModel
                    instance = form.instance
                    articulo = instance.product_id
                    articulo.cantidad -= instance.qty
                    articulo.save()

                    RegistroInventarioVendedores.objects.create(
                        usuario=request.user,
                        nombre_producto=instance.product_id.nombreArticulo,  # Ajusta esto según el nombre del campo en tu modelo articulosModel
                        cantidad=instance.qty,
                        product_id=instance.product_id
                        )

                    

                return redirect('cargarInventarioVendedores')
        else:
            form = inventarioCargaVendedorForm(instance=inventarioVendedor)
            return render(request, 'listaInventarioVendedorExterno.html', {'form': form, 'inventario': inventarioVendedor, 'lista': lista, 'total_public_price': total_public_price, 'total_cost': total_cost, 'gananciaTotal': gananciaTotal,'registro':registro,          'product_json' : json.dumps(product_json),'products':products    })

    else:
        return render(request, 'forbiden.html')


def historialInventario(request):
    if request.user.is_authenticated:
        registro=RegistroInventarioVendedores.objects.all().filter(usuario_id=request.user.id)
        context={
            'registro':registro,
        }
        return render(request,'tabla_inventario.html',context)
    else:
        return render(request,'forbiden.html')
    

def registrar_inventario_puntos_venta(request, pk=None):  # AUTOCARGA DE INVENTARIO VENDEDORES
    if request.user.is_authenticated:
        inventarioPuntoVenta = get_object_or_404(Seller, pk=pk) if pk else None
        lista = pvInventory.objects.all().filter(seller_id_id=request.user.id)
        today=date.today()
        registro=RegistroInventarioPuntoVenta.objects.all().filter(usuario_id=request.user.id,fecha=today)
        products = articulosModel.objects.all()######NECESARIO PARA FILTRAR SOLO EL INVENTARIO DE CADA VENDEDOR
        product_json = []
        ###print(products)
        for product in products:
            ###print(product.product_id_id)
            ###print(product)            
            product_json.append({'id':product.pk, 'name':product.nombreArticulo, 'price':float(product.precioVentaPublico),'qty':float(product.cantidad),'descripcionArticulo':product.descripcionArticulo})
        

        for item in lista:
            item.costo_total = item.qty * item.product_id.costo
            item.precio_publico_total = item.qty * item.product_id.precioVentaVendedorReparto
            item.ganancia = item.precio_publico_total - item.costo_total
            item.gananciaUnitaria = item.product_id.precioVentaVendedorReparto - item.product_id.costo

        total_public_price = sum(item.precio_publico_total for item in lista)
        total_cost = sum(item.qty * item.product_id.costo for item in lista)
        gananciaTotal = total_public_price - total_cost


        if request.method == 'POST':
            form = inventarioCargaPVForm(request.POST, instance=inventarioPuntoVenta)
            if form.is_valid():
                with transaction.atomic():
                    # Asigna la instancia de usuario actual al campo seller_id antes de guardar el formulario
                    form.instance.seller_id = request.user

                    try:
                        producto_inventario = pvInventory.objects.get(
                            product_id=form.instance.product_id,
                            seller_id=request.user
                        )
                        # Si el producto ya existe, suma la cantidad proporcionada en el formulario a la cantidad existente
                        producto_inventario.qty += form.instance.qty
                        producto_inventario.save()
                    except pvInventory.DoesNotExist:
                        # Si el producto no existe, crea un nuevo registro en el inventario
                        ##print("Producto Nuevo")
                        form.save()

                    # Restar la cantidad de inventario agregada del stock disponible en articulosModel
                    instance = form.instance
                    articulo = instance.product_id
                    articulo.cantidad -= instance.qty
                    articulo.save()

                    RegistroInventarioPuntoVenta.objects.create(
                        usuario=request.user,
                        nombre_producto=instance.product_id.nombreArticulo,  # Ajusta esto según el nombre del campo en tu modelo articulosModel
                        cantidad=instance.qty
                        )

                return redirect('cargarInventarioPV')
        else:
            form = inventarioCargaPVForm(instance=inventarioPuntoVenta)

            return render(request, 'listaInventarioPV.html', {'form': form, 'inventario': inventarioPuntoVenta, 'lista': lista, 'total_public_price': total_public_price, 'total_cost': total_cost, 'gananciaTotal': gananciaTotal,'registro':registro,'product_json' : json.dumps(product_json),'products':products})

    else:
        return render(request, 'forbiden.html')
  

def salesListPV(request):
    if request.user.is_authenticated:

        salesVendedor=Sales.objects.all().filter(origin=request.user.id)
        sale_data_vendedor=[]
        
        for sale in salesVendedor:
            data = {}
            for field in sale._meta.get_fields(include_parents=False):
                if field.related_model is None:
                    data[field.name] = getattr(sale,field.name)
            data['items'] = salesItems.objects.filter(sale_id = sale).all()
            data['item_count'] = len(data['items'])
            if 'tax_amount' in data:
                data['tax_amount'] = format(float(data['tax_amount']),'.2f')
            # ###print(data)
            sale_data_vendedor.append(data)
        # ###print(sale_data)  

        context = {
            'page_title':'Sales Transactions',
            'sale_data':sale_data_vendedor,
        }
        # return HttpResponse('')
        return render(request, 'pvSales.html',context)
    else:
        return render(request,'forbiden.html')


def reporteInventario(request):
    if request.user.is_authenticated:
        inventarioStockMaestro=articulosModel.objects.all()
        todos_inventarios=list(sellerInventory.objects.all()) + list(pvInventory.objects.all())
        todos_cargas=list(RegistroInventarioPuntoVenta.objects.all()) + list(RegistroInventarioVendedores.objects.all())
        cargas_vendedores_list=list(RegistroInventarioVendedores.objects.all())
        today=date.today()
        cargas_vendedores_list_today=list(RegistroInventarioVendedores.objects.all().filter(fecha=today))
        cargas_pv_list_today=list(RegistroInventarioPuntoVenta.objects.all().filter(fecha=today))
        cargas_pv_list=list(RegistroInventarioPuntoVenta.objects.all())

        usuarios_vendedores = sellerInventory.objects.values('seller_id').distinct()
        inventario_por_usuario_vendedor = {}
        for usuario in usuarios_vendedores:
            inventario_por_usuario_vendedor[usuario['seller_id']] = sellerInventory.objects.filter(seller_id=usuario['seller_id'])

        usuarios_puntos_venta = pvInventory.objects.values('seller_id').distinct()
        inventario_por_usuario_punto_venta = {}
        for usuario in usuarios_puntos_venta:
            inventario_por_usuario_punto_venta[usuario['seller_id']] = pvInventory.objects.filter(seller_id=usuario['seller_id'])

        registro_cargas_vendedores = RegistroInventarioVendedores.objects.values('usuario_id').distinct()
        cargas_vendedores = {}
        for carga in registro_cargas_vendedores:
            usuario_id = carga['usuario_id']
            cargas_vendedores[usuario_id] = RegistroInventarioVendedores.objects.filter(usuario_id=usuario_id)


        registro_cargas_puntos_venta = RegistroInventarioPuntoVenta.objects.values('usuario_id').distinct()
        cargas_puntos_venta = {}
        for carga in registro_cargas_puntos_venta:
            usuario_id = carga['usuario_id']
            cargas_puntos_venta[usuario_id] = RegistroInventarioPuntoVenta.objects.filter(usuario_id=usuario_id)#values('usuario_id').distinct()


        # ##print(todos_cargas)
        context={
            'cargas_pv_list':cargas_pv_list,
            'cargas_vendedores_list':cargas_vendedores_list,
            'cargas_vendedores_list_today':cargas_vendedores_list_today,
            'cargas_pv_list_today':cargas_pv_list_today,
            'todos_cargas':todos_cargas,
            'todos_inventarios':todos_inventarios,
            'inventario_por_usuario_vendedor':inventario_por_usuario_vendedor,
            'inventario_por_usuario_punto_venta':inventario_por_usuario_punto_venta,
            'cargas_vendedores':cargas_vendedores,
            'cargas_puntos_venta':cargas_puntos_venta,
            'inventarioStockMaestro':inventarioStockMaestro,
        }
        return render(request,'reporteInventario.html',context)
    else:
        return render(request,'forbiden.html')
    
from collections import OrderedDict

@login_required
def reimpresionCargasDiarias(request):
    today = datetime.now().date()
    cargasHoyPuntosVenta = RegistroInventarioPuntoVenta.objects.all()
    cargasHoyVendedores = RegistroInventarioVendedores.objects.filter(fecha=today)

    # Crear un diccionario para almacenar las entradas únicas por `code`
    unique_cargas = OrderedDict()

    # Iterar sobre los registros y agregar solo los únicos por `code`
    for carga in cargasHoyVendedores:
        if carga.code not in unique_cargas:
            unique_cargas[carga.code] = carga

    # Convertir el diccionario a una lista de valores
    cargasHoyVendedores = list(unique_cargas.values())

    # Obtener los valores de los campos que necesitas
    cargasHoyVendedores = [carga.__dict__ for carga in cargasHoyVendedores]

    # Añadir los datos del usuario correspondiente
    for carga in cargasHoyVendedores:
        usuarioData = User.objects.filter(id=carga['usuario_id']).first()
        if usuarioData:
            carga['nombre_vendedor'] = f"{usuarioData.first_name} {usuarioData.last_name} Usuario: {usuarioData.username}"

    
    
    context = {
        'registros_por_usuario': cargasHoyVendedores,
    }

    return render(request, 'reimpresionCargasDiarias.html', context)

@login_required
def reimpresionCargasDiariasInd(request):
    # Obtengo todas las cargas del vendedor
    cargasVendedor = RegistroInventarioVendedores.objects.filter(usuario_id=request.user.id).values_list('code', flat=True).distinct()
    # #print(cargasVendedor)
    
    sale_data_vendedor = []
    
    for code in cargasVendedor:
        # Obtengo una carga de ejemplo para este código
        carga = RegistroInventarioVendedores.objects.filter(code=code, usuario_id=request.user.id).first()
        aditionalPermissions=usersPermission.objects.filter(user_id=request.user.id).get()
        
        data = {}
        for field in carga._meta.get_fields(include_parents=False):
            if field.related_model is None:
                data[field.name] = getattr(carga, field.name)
        
        # Obtengo todos los items con el mismo code y usuario_id
        items = RegistroInventarioVendedores.objects.filter(code=code, usuario_id=request.user.id).values()
        # #print(items)
        acumuladorValor=0
        for elemento in items:
            cantidad=elemento['cantidad']
            infoProducto=articulosModel.objects.all().filter(id=elemento['product_id']).get()
            if aditionalPermissions.is_externalSeller:
                precioProducto=infoProducto.precioVentaVendedorExterno*cantidad
            else:
                precioProducto=infoProducto.precioVentaVendedorReparto*cantidad
            acumuladorValor+=precioProducto
        data['acumuladorValor']=acumuladorValor
        data['items'] = list(items)
        data['item_count'] = sum(item['cantidad'] for item in items)
        
        sale_data_vendedor.append(data)
    
    context = {
        'sale_data': sale_data_vendedor,
    }
    return render(request, 'reimpresionCargasDiariasInd.html', context)


def receiptSellerCharge(request):
    if request.user.is_authenticated:
        id = request.GET.get('id')
        transaction = {}        
        transaction['code']=int(id)
        transaction['code']=str(transaction['code'])
        ItemList = RegistroInventarioVendedores.objects.filter(code = id).all()
        
        permisosEspeciales=usersPermission.objects.filter(user_id=request.user.id).get()
        total=0
        acumulador_total_productos=0
        for elemento in ItemList:
            datosProducto=articulosModel.objects.filter(id=elemento.product_id).get()
            
            if permisosEspeciales.is_externalSeller:
                elemento.precio=datosProducto.precioVentaVendedorExterno
            else:
                elemento.precio=datosProducto.precioVentaVendedorReparto

            total=total + (elemento.precio*elemento.cantidad)
            acumulador_total_productos+=elemento.cantidad
            

            
        datosTransaccin=RegistroInventarioVendedores.objects.filter(code = id).first()
        transaction['date_added']=datosTransaccin.fecha
        
        usuarioData=User.objects.all().filter(id=request.user.id).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        
        context = {
            "total":total,
            "transaction" : transaction,
            "salesItems" : ItemList,
            'total_productos':acumulador_total_productos,
            "nombreUsuario":nombreUsuario,
        }

        return render(request, 'receiptChargeC.html',context)
    else:
        return render(request,'forbiden.html')
    

def impresionInventariosI(request):
    if request.user.is_authenticated:
        # id = request.GET.get('id')
        id=request.user.id
        transaction = {}        
        transaction['code']=int(id)
        transaction['code']=str(transaction['code'])
        ItemList = sellerInventory.objects.filter(seller_id_id = id,qty__gt=0).all()
        
        permisosEspeciales=usersPermission.objects.filter(user_id=id).get()

        total=0
        acumulador_total_productos=0
        for elemento in ItemList:
            datosProducto=articulosModel.objects.filter(id=elemento.product_id_id).get()
            elemento.nombreArticulo=datosProducto.nombreArticulo

            if permisosEspeciales.is_externalSeller:
                elemento.precio=datosProducto.precioVentaVendedorExterno
            else:
                elemento.precio=datosProducto.precioVentaVendedorReparto

            total=total + (elemento.precio*elemento.qty)
            acumulador_total_productos+=elemento.qty
            
        transaction['date_added']=datetime.now().date()
        
        usuarioData=User.objects.all().filter(id=id).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        
        context = {
            "total":total,
            "transaction" : transaction,
            "salesItems" : ItemList,
            'total_productos':acumulador_total_productos,
            "nombreUsuario":nombreUsuario,
        }

        return render(request, 'receiptInventory.html',context)
    else:
        return render(request,'forbiden.html')


@login_required
def impresionInventarios(request):
    usuarios = User.objects.all().values('id','username','first_name','last_name')
    usuarios_list=list(usuarios)
    

    context={
        'usuarios':usuarios_list,        
    }

    return render(request,'impresionInventarios.html',context)


def receiptSellerInventory(request):
    if request.user.is_authenticated:
        id = request.GET.get('id')
        transaction = {}        
        transaction['code']=int(id)
        transaction['code']=str(transaction['code'])
        ItemList = sellerInventory.objects.filter(seller_id_id = id,qty__gt=0).all()
        
        permisosEspeciales=usersPermission.objects.filter(user_id=id).get()

        total=0
        acumulador_total_productos=0
        for elemento in ItemList:
            datosProducto=articulosModel.objects.filter(id=elemento.product_id_id).get()
            elemento.nombreArticulo=datosProducto.nombreArticulo

            if permisosEspeciales.is_externalSeller:
                elemento.precio=datosProducto.precioVentaVendedorExterno
            else:
                elemento.precio=datosProducto.precioVentaVendedorReparto

            total=total + (elemento.precio*elemento.qty)
            acumulador_total_productos+=elemento.qty
            
        transaction['date_added']=datetime.now().date()
        
        usuarioData=User.objects.all().filter(id=id).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        
        context = {
            "total":total,
            "transaction" : transaction,
            "salesItems" : ItemList,
            'total_productos':acumulador_total_productos,
            "nombreUsuario":nombreUsuario,
        }

        return render(request, 'receiptInventory.html',context)
    else:
        return render(request,'forbiden.html')
    

@csrf_exempt
def delete_multiple_records(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        # print(ids)
        sellerInventory.objects.filter(pk__in=ids).delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'fail'}, status=400)



@login_required
def salesHistory(request):
    today=timezone.now().date()
    
    lunesSemanaPasada=today-timedelta(days=today.weekday()+7)
    domingoSemanaPasada=lunesSemanaPasada+timedelta(days=6)
    
    diasDesdeLunes=today.weekday()
    lunesSemana = today - timedelta(days=diasDesdeLunes)
    # #print(lunesSemana)
    domingoSemana=lunesSemana+timedelta(days=7)
    # #print(domingoSemana)

    ventasSemanalesSellers=sellerSales.objects.filter(date_added__range=[lunesSemana,domingoSemana]).values_list('id',flat=True)#OBTENGO LAS VENTAS SEMANALES PARA VENDEDORES
    articulosSemanalesSellers=sellerSalesItems.objects.filter(sale_id_id__in=ventasSemanalesSellers)
    try:
        ventasAgrupadas = articulosSemanalesSellers.values('product_id_id').annotate(total_qty=Sum('qty')).order_by('-total_qty').first()
    except:
        ventasAgrupadas="Nada"
    if ventasAgrupadas is None:
        pass
    else:
        productMasVendidoSellerSemanal=articulosModel.objects.all().filter(id=ventasAgrupadas['product_id_id'])
    ventasSemanalesVendedores=sellerSales.objects.filter(date_added__range=[lunesSemana,domingoSemana])
    
    grouped_sales = defaultdict(list)#AGRUPAMIENTO PARA PODER SEPARARLOS POR TABLAS
    for sale in ventasSemanalesVendedores:
        userData=User.objects.all().filter(id=sale.origin).get()
        sale.origin="Usuario:"+userData.username+". Nombre: " + userData.first_name+" "+userData.last_name
        articulosVenta=sellerSalesItems.objects.all().filter(sale_id_id=sale.id)
        gananciaPorVenta=0
        acumuladorProductosPorVenta=0
        for elemento in articulosVenta:
            costoProducto=articulosModel.objects.all().filter(id=elemento.product_id_id).get()
            gananciaPorProducto=elemento.total-(costoProducto.costo*elemento.qty)
            acumuladorProductosPorVenta=acumuladorProductosPorVenta+elemento.qty
            gananciaPorVenta=gananciaPorVenta+gananciaPorProducto

        sale.gananciaPorVenta=gananciaPorVenta
        sale.acumuladorProductosPorVenta=acumuladorProductosPorVenta
        
        grouped_sales[sale.origin].append(sale)

    ventasHoySellers=sellerSales.objects.filter(date_added=today).values_list('id',flat=True)#OBTENGO LAS VENTAS SEMANALES PARA VENDEDORES
    articulosHoySellers=sellerSalesItems.objects.filter(sale_id_id__in=ventasHoySellers)
    try:
        ventasAgrupadasHoy = articulosHoySellers.values('product_id_id').annotate(total_qty=Sum('qty')).order_by('-total_qty').first()
    except:
        ventasAgrupadasHoy="Nada"
    if ventasAgrupadasHoy is None:
        pass
    else:
        productMasVendidoSellerHoy=articulosModel.objects.all().filter(id=ventasAgrupadasHoy['product_id_id'])
    ventasHoyVendedores=sellerSales.objects.filter(date_added__date=today)
    # print(ventasHoyVendedores)
    
    grouped_sales_hoy_vendedores = defaultdict(list)#AGRUPAMIENTO PARA PODER SEPARARLOS POR TABLAS
    for sale in ventasHoyVendedores:
        userData=User.objects.all().filter(id=sale.origin).get()
        sale.origin="Usuario:"+userData.username+". Nombre: " + userData.first_name+" "+userData.last_name
        articulosVenta=sellerSalesItems.objects.all().filter(sale_id_id=sale.id)
        gananciaPorVenta=0
        acumuladorProductosPorVenta=0
        for elemento in articulosVenta:
            costoProducto=articulosModel.objects.all().filter(id=elemento.product_id_id).get()
            gananciaPorProducto=elemento.total-(costoProducto.costo*elemento.qty)
            acumuladorProductosPorVenta=acumuladorProductosPorVenta+elemento.qty
            gananciaPorVenta=gananciaPorVenta+gananciaPorProducto

        sale.gananciaPorVenta=gananciaPorVenta
        sale.acumuladorProductosPorVenta=acumuladorProductosPorVenta
        
        grouped_sales_hoy_vendedores[sale.origin].append(sale)
    ventasHoyPV=Sales.objects.filter(date_added=today).values_list('id',flat=True)#OBTENGO LAS VENTAS SEMANALES PARA VENDEDORES
    articulosHoyPV=salesItemsPV.objects.filter(sale_id_id__in=ventasHoyPV)
    try:
        ventasAgrupadasHoyPV = articulosHoyPV.values('product_id_id').annotate(total_qty=Sum('qty')).order_by('-total_qty').first()
    except:
        ventasAgrupadasHoyPV="Nada"
    if ventasAgrupadasHoyPV is None:
        pass
    else:
        productMasVendidoSellerHoy=articulosModel.objects.all().filter(id=ventasAgrupadasHoyPV['product_id_id'])
    ventasHoyPV=Sales.objects.filter(date_added__date=today)
    # print(ventasHoyPV)
    
    grouped_sales_hoy_puntosVenta = defaultdict(list)#AGRUPAMIENTO PARA PODER SEPARARLOS POR TABLAS
    for sale in ventasHoyPV:
        userData=User.objects.all().filter(id=sale.origin).get()
        sale.origin="Usuario:"+userData.username+". Nombre: " + userData.first_name+" "+userData.last_name
        articulosVenta=salesItems.objects.all().filter(sale_id_id=sale.id)
        gananciaPorVenta=0
        acumuladorProductosPorVenta=0
        for elemento in articulosVenta:
            # print(elemento.qty)
            costoProducto=articulosModel.objects.all().filter(id=elemento.product_id_id).get()
            gananciaPorProducto=elemento.total-(costoProducto.costo*elemento.qty)
            acumuladorProductosPorVenta=acumuladorProductosPorVenta+elemento.qty
            gananciaPorVenta=gananciaPorVenta+gananciaPorProducto

        sale.gananciaPorVenta=gananciaPorVenta
        sale.acumuladorProductosPorVenta=acumuladorProductosPorVenta
        
        grouped_sales_hoy_puntosVenta[sale.origin].append(sale)
    ventasPV=Sales.objects.values_list('id',flat=True)#OBTENGO LAS VENTAS SEMANALES PARA VENDEDORES
    articulosPV=salesItemsPV.objects.filter(sale_id_id__in=ventasPV)
    try:
        ventasAgrupadasPV = articulosPV.values('product_id_id').annotate(total_qty=Sum('qty')).order_by('-total_qty').first()
    except:
        ventasAgrupadasPV="Nada"
    if ventasAgrupadasPV is None:
        pass
    else:
        productMasVendidoSeller=articulosModel.objects.all().filter(id=ventasAgrupadasPV['product_id_id'])
    ventasPV=Sales.objects.all()
    # print(ventasPV)
    
    grouped_sales_puntosVenta = defaultdict(list)#AGRUPAMIENTO PARA PODER SEPARARLOS POR TABLAS
    for sale in ventasPV:
        userData=User.objects.all().filter(id=sale.origin).get()
        sale.origin="Usuario:"+userData.username+". Nombre: " + userData.first_name+" "+userData.last_name
        articulosVenta=salesItems.objects.all().filter(sale_id_id=sale.id)
        gananciaPorVenta=0
        acumuladorProductosPorVenta=0
        for elemento in articulosVenta:
            # print(elemento.qty)
            costoProducto=articulosModel.objects.all().filter(id=elemento.product_id_id).get()
            gananciaPorProducto=elemento.total-(costoProducto.costo*elemento.qty)
            acumuladorProductosPorVenta=acumuladorProductosPorVenta+elemento.qty
            gananciaPorVenta=gananciaPorVenta+gananciaPorProducto

        sale.gananciaPorVenta=gananciaPorVenta
        sale.acumuladorProductosPorVenta=acumuladorProductosPorVenta
        
        grouped_sales_puntosVenta[sale.origin].append(sale)

    #####################################
    ventasVendedores=sellerSales.objects.filter(date_added__range=[lunesSemana,domingoSemana])
    
    grouped_sales_vendedores = defaultdict(list)#AGRUPAMIENTO PARA PODER SEPARARLOS POR TABLAS
    for sale in ventasVendedores:
        userData=User.objects.all().filter(id=sale.origin).get()
        sale.origin="Usuario:"+userData.username+". Nombre: " + userData.first_name+" "+userData.last_name
        articulosVenta=sellerSalesItems.objects.all().filter(sale_id_id=sale.id)
        gananciaPorVenta=0
        acumuladorProductosPorVenta=0
        for elemento in articulosVenta:
            costoProducto=articulosModel.objects.all().filter(id=elemento.product_id_id).get()
            gananciaPorProducto=elemento.total-(costoProducto.costo*elemento.qty)
            acumuladorProductosPorVenta=acumuladorProductosPorVenta+elemento.qty
            gananciaPorVenta=gananciaPorVenta+gananciaPorProducto

        sale.gananciaPorVenta=gananciaPorVenta
        sale.acumuladorProductosPorVenta=acumuladorProductosPorVenta
        
        grouped_sales_vendedores[sale.origin].append(sale)



    ventasHoySellers=sellerSales.objects.filter(date_added=today).values_list('id',flat=True)#OBTENGO LAS VENTAS SEMANALES PARA VENDEDORES
    articulosHoySellers=sellerSalesItems.objects.filter(sale_id_id__in=ventasHoySellers)
    try:
        ventasAgrupadasHoy = articulosHoySellers.values('product_id_id').annotate(total_qty=Sum('qty')).order_by('-total_qty').first()
    except:
        ventasAgrupadasHoy="Nada"
    if ventasAgrupadasHoy is None:
        pass
    else:
        productMasVendidoSellerHoy=articulosModel.objects.all().filter(id=ventasAgrupadasHoy['product_id_id'])
    

    ventasSemanalesPV=Sales.objects.filter(date_added__range=[lunesSemana,domingoSemana]).values_list('id',flat=True)#OBTENGO LAS VENTAS SEMANALES PARA VENDEDORES
    articulosSemanalesPV=salesItems.objects.filter(sale_id_id__in=ventasSemanalesPV)
    try:
        ventasAgrupadaspvsemanales = articulosSemanalesPV.values('product_id_id').annotate(total_qty=Sum('qty')).order_by('-total_qty').first()
    except:
        ventasAgrupadaspvsemanales="Nada"
    if ventasAgrupadaspvsemanales is None:
        pass
    else:
        productMasVendidoPVSemanal=articulosModel.objects.all().filter(id=ventasAgrupadaspvsemanales['product_id_id'])
    ventasSemanalesPV=Sales.objects.filter(date_added__range=[lunesSemana,domingoSemana])
    
    grouped_sales_SEMANALES_PV = defaultdict(list)#AGRUPAMIENTO PARA PODER SEPARARLOS POR TABLAS
    for sale in ventasSemanalesPV:
        userData=User.objects.all().filter(id=sale.origin).get()
        sale.origin="Usuario:"+userData.username+". Nombre: " + userData.first_name+" "+userData.last_name
        articulosVenta=salesItems.objects.all().filter(sale_id_id=sale.id)
        gananciaPorVenta=0
        acumuladorProductosPorVenta=0
        for elemento in articulosVenta:
            costoProducto=articulosModel.objects.all().filter(id=elemento.product_id_id).get()
            gananciaPorProducto=elemento.total-(costoProducto.costo*elemento.qty)
            acumuladorProductosPorVenta=acumuladorProductosPorVenta+elemento.qty
            gananciaPorVenta=gananciaPorVenta+gananciaPorProducto

        sale.gananciaPorVenta=gananciaPorVenta
        sale.acumuladorProductosPorVenta=acumuladorProductosPorVenta
        
        grouped_sales_SEMANALES_PV[sale.origin].append(sale)
    

    # print(grouped_sales_puntosVenta)
    context={
        'grouped_sales':dict(grouped_sales),
        'grouped_sales_hoy_vendedores':dict(grouped_sales_hoy_vendedores),
        'grouped_sales_hoy_puntosVenta':dict(grouped_sales_hoy_puntosVenta),
        'grouped_sales_puntosVenta':dict(grouped_sales_puntosVenta),
        'grouped_sales_vendedores':dict(grouped_sales_vendedores),
        'grouped_sales_SEMANALES_PV':dict(grouped_sales_SEMANALES_PV),
    }

    return render(request,'salesHistory.html',context)