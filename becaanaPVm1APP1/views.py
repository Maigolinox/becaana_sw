from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponseRedirect,HttpResponse,JsonResponse
from django.urls import reverse
from .models import puntoVenta,articulosModel,stockPuntoVenta,Sales,salesItems,Seller,sellerInventory,sellerSalesItems,sellerSales,costosEmpresaVendedoresModel,costosEmpresaPuntosVentaModel,pvInventory,salesItemsPV,RegistroInventarioVendedores,RegistroInventarioPuntoVenta, usersPermission
from .forms import InventarioForm,inventarioVendedorForm,InventoryFormPV,costosPuntosVentaForm,costosVendedoresForm,inventarioPuntoVentaForm,inventarioCargaVendedorForm,inventarioCargaPVForm,InventoryFormSeller,InventoryMatrix
import json,sys
from datetime import date, datetime
from django.contrib import messages
from django.db.models import Count,Sum,Q #Q es para consultas mas complejas que involucren condicionales

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

def receiptChargeSellerExternal(request):
    if request.user.is_authenticated:
        # print(request.GET)
        id = request.GET.get('id')
        transaction = {'date_added':timezone.now()}

        usuarioData=User.objects.all().filter(id=request.user.id).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        total_value = 0
        ItemList = RegistroInventarioVendedores.objects.filter(code = id).all()# LISTA TODOS LOS ELEMENTOS DEL REGISTRO
        for elemento in ItemList:
            # print(elemento.product_id)
            articulo=articulosModel.objects.all().filter(id=elemento.product_id).get()# OBTEN LA INFORMACION DEL ARTICULO ORIGINAL
            # print(articulo.precioVentaVendedorReparto)
            total_value=total_value+(elemento.cantidad*articulo.precioVentaVendedorExterno)
            elemento.nombreArticulo=articulo.nombreArticulo
            
        
        context = {
            "total":total_value,
            # "total_discounts":total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList,
            'nombreUsuario':nombreUsuario,
        }

        return render(request, 'receiptCharge.html',context)
    else:
        return render(request,'forbiden.html')


def receiptChargeSeller(request):
    if request.user.is_authenticated:
        # print(request.GET)
        id = request.GET.get('id')
        transaction = {'date_added':timezone.now()}

        usuarioData=User.objects.all().filter(id=request.user.id).get()# NOMBRE DEL USUARIO AL TICKET
        nombreUsuario=usuarioData.username+" . Nombre: "+usuarioData.first_name+" "+usuarioData.last_name# NOMBRE DEL USUARIO AL TICKET
        
        total_value = 0
        ItemList = RegistroInventarioVendedores.objects.filter(code = id).all()# LISTA TODOS LOS ELEMENTOS DEL REGISTRO
        for elemento in ItemList:
            # print(elemento.product_id)
            articulo=articulosModel.objects.all().filter(id=elemento.product_id).get()# OBTEN LA INFORMACION DEL ARTICULO ORIGINAL
            # print(articulo.precioVentaVendedorReparto)
            total_value=total_value+(elemento.cantidad*articulo.precioVentaVendedorReparto)
            elemento.nombreArticulo=articulo.nombreArticulo
            
        
        context = {
            "total":total_value,
            # "total_discounts":total_discounts,
            "transaction" : transaction,
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
        # print(data)
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
            
            # price = data.getlist('price[]')[i]
            obj, created = sellerInventory.objects.get_or_create(product_id_id=product_id,seller_id_id=seller_id)
            if not created:
                sellerInventory.objects.filter(product_id_id=product_id,seller_id_id=seller_id).update(qty=F('qty')+qty)

            else:
                obj.product_id_id=product_id
                obj.seller_id_id=seller_id
                obj.precioVentaVendedor=precioVentaVendedor
                obj.precioVentaVendedorExterno=precioVentaVendedorExterno
                obj.precioOriginal=precioOriginal
                obj.nombreArticulo=nombreArticulo
                obj.qty=qty
                obj.code=code
                # obj.product_id=product_id
                obj.save()

            RegistroInventarioVendedores(nombre_producto=nombreArticulo,cantidad=qty,usuario_id=seller_id,code=code,product_id=product_id).save()#Registro de inventario
            
            i += int(1)

            product.cantidad=product.cantidad-qty #Restar de inventario de matriz
            product.save() #Restar de inventario de matriz

        sale_id=code
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        articulosModel.success(request, "Venta guardada.")
    except Exception as e:
        print(e)
        resp['msg'] = "Ocurrió un error"
        #print("Unexpected errors:", e)###############################
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
            ##print(e)
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
        ##print(userName)
        if (objetoUsuario.is_staff and objetoUsuario.is_superuser and objetoUsuario.is_active):# dashboard de administrador
            return render(request,'dashboard.html',context={'mensaje':mensaje})
        elif (objetoUsuario.is_active and not objetoUsuario.is_staff and not objetoUsuario.is_superuser and not objetoUsuario.is_externalSeller and not objetoUsuario.is_matrixSeller):#dashboard de vendedores
            #print("Vendedor Normal")
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
                #print(e)
                ventasUsuario=0
                ventasUsuarioSemanaPasada=0
                ventasUsuarioSemanaActual=0
            return render(request,'dashVentasSeller.html',context={'mensaje':mensaje,'user_id':user_id,'totalVentasUsuario':ventasUsuario,'ventasUsuarioSemanaPasada':ventasUsuarioSemanaPasada,'ventasUsuarioSemanaActual':ventasUsuarioSemanaActual})
        elif (objetoUsuario.is_active and not objetoUsuario.is_staff and not objetoUsuario.is_superuser and objetoUsuario.is_externalSeller and not objetoUsuario.is_matrixSeller):#dashboard de vendedores externos
            print("Vendedor Externo")
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
                #print(e)
                ventasUsuario=0
                ventasUsuarioSemanaPasada=0
                ventasUsuarioSemanaActual=0
            return render(request,'dashVentasExternalSeller.html',context={'mensaje':mensaje,'user_id':user_id,'totalVentasUsuario':ventasUsuario,'ventasUsuarioSemanaPasada':ventasUsuarioSemanaPasada,'ventasUsuarioSemanaActual':ventasUsuarioSemanaActual})
        
        elif (objetoUsuario.is_active and objetoUsuario.is_staff and not objetoUsuario.is_superuser ):#dashboard de puntos de venta
            try:
                Ventas=Sales.objects.all().filter(origin=request.user.id,date_added__date=timezone.now().date()).aggregate(total_ventas=Sum('grand_total'))
            except Exception as e:
                #print(e)
                Ventas=0
            return render(request,'dahsPuntosVenta.html',context={'Ventas':Ventas})
        
        elif (objetoUsuario.is_active and not objetoUsuario.is_staff and not objetoUsuario.is_superuser and not objetoUsuario.is_externalSeller and objetoUsuario.is_matrixSeller):#dashboard de vendedores matrix
            # print("Vendedor Matriz")
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
                #print(e)
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
            ##print("Error")
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
            ##print("Error")
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
                #print(e)
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
            print(e)
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
        ##print(products)
        for product in products:
            ##print(product.product_id_id)
            # print('id',product.id, 'name',product.nombreArticulo, 'price',float(product.precioVentaPublico),'qty',float(product.cantidad),'general_id',product.id)            
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


def save_pos(request):
    resp = {'status':'failed','msg':''}
    data = request.POST
    ##print(data)
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
            ##print({'sale_id' : sale, 'product_id' : product, 'qty' : qty, 'price' : price, 'total' : total})
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
        ##print("Unexpected error:", e)
    return HttpResponse(json.dumps(resp),content_type="application/json")


def receipt(request):
    if request.user.is_authenticated:

        id = request.GET.get('id')
        sales = Sales.objects.filter(id = id).first()
        transaction = {}
        for field in Sales._meta.get_fields():
            if field.related_model is None:
                transaction[field.name] = getattr(sales,field.name)
        if 'tax_amount' in transaction:
            transaction['tax_amount'] = format(float(transaction['tax_amount']))

        ItemList = salesItems.objects.filter(sale_id = sales).all()
        total_discounts=0
        for elemento in ItemList:
            discount=(elemento.discount*elemento.price*elemento.qty)/100
            # #print(discount)
            total_discounts+=discount

        
        total=transaction["grand_total"]+total_discounts
        
        context = {
            "total":total,
            "total_discounts":total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList
        }

        return render(request, 'receipt.html',context)
    else:
        return render(request,'forbiden.html')
    # return HttpResponse('')


def salesList(request):
    if request.user.is_authenticated:

        sales = Sales.objects.all()
        salesVendedor=sellerSales.objects.all()
        sale_data = []
        sale_data_vendedor=[]
        for sale in sales:
            data = {}
            for field in sale._meta.get_fields(include_parents=False):
                if field.related_model is None:
                    data[field.name] = getattr(sale,field.name)
            data['items'] = salesItems.objects.filter(sale_id = sale).all()
            data['item_count'] = len(data['items'])
            if 'tax_amount' in data:
                data['tax_amount'] = format(float(data['tax_amount']),'.2f')
            # ##print(data)
            sale_data.append(data)
        # ##print(sale_data)
        for sale in salesVendedor:
            data = {}
            for field in sale._meta.get_fields(include_parents=False):
                if field.related_model is None:
                    data[field.name] = getattr(sale,field.name)
            data['items'] = sellerSalesItems.objects.filter(sale_id = sale).all()
            data['item_count'] = len(data['items'])
            if 'tax_amount' in data:
                data['tax_amount'] = format(float(data['tax_amount']),'.2f')
            # ##print(data)
            sale_data_vendedor.append(data)
        # ##print(sale_data)  

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
            ##print("Unexpected error:", sys.exc_info()[0])
        return HttpResponse(json.dumps(resp), content_type='application/json')
    
    else:
        return render(request,'forbiden.html')


def delete_sale_sellers(request):
    if request.user.is_authenticated:

        resp = {'status':'failed', 'msg':''}
        id = request.POST.get('id')
        try:
            delete = sellerSales.objects.filter(id = id).delete()
            resp['status'] = 'success'
            messages.success(request, 'Registro de venta eliminado.')
        except:
            resp['msg'] = "Ha ocurrido un error."
            ##print("Unexpected error:", sys.exc_info()[0])
        return HttpResponse(json.dumps(resp), content_type='application/json')
    
    else:
        return render(request,'forbiden.html')


def dash_ventas(request):
    if request.user.is_authenticated:

        return render(request,'dashVentas.html')
    else:
        return render(request,'forbiden.html')


def financeDashboard(request):#MENU DE FINANZAS
    if request.user.is_authenticated:

        today = timezone.now().date()
        start_of_two_weeks_ago = today - timedelta(days=14)
        start_of_week = today - timedelta(days=today.weekday())
        #############BLOQUES PARA VENDEDORES
        try:
            ventas_ultimas_dos_semanas = sellerSales.objects.filter(date_added__date__gte=start_of_two_weeks_ago).values('id','origin','date_added','grand_total','code')

            user_ids = ventas_ultimas_dos_semanas.values_list('origin', flat=True).distinct()
            usuarios = User.objects.filter(id__in=user_ids)
            user_info_dict = {user.id: {'username': user.username, 'first_name': user.first_name, 'last_name': user.last_name} for user in usuarios}
            ventas_con_info_usuario = []
            for venta in ventas_ultimas_dos_semanas:
                items_venta = sellerSalesItems.objects.filter(sale_id=venta['id'])
                
                costo_total_venta = items_venta.aggregate(costo_total=Sum('product_id__costo'))['costo_total'] or 0
                ganancia_venta = venta['grand_total'] - costo_total_venta

                user_id = venta['origin']
                usuario_info = user_info_dict.get(user_id, {})
                venta_con_info_usuario = {
                    'origin': user_id,
                    'username': usuario_info.get('username', 'Usuario Desconocido'),
                    'first_name': usuario_info.get('first_name', 'Sin Nombre'),
                    'last_name': usuario_info.get('last_name', 'Sin Apellido'),
                    'date_added': venta['date_added'],
                    'grand_total': venta['grand_total'],
                    'code': venta['code'],
                    'ganancia':ganancia_venta,
                }
                ventas_con_info_usuario.append(venta_con_info_usuario)

            ventas_ultimas_dos_semanas=ventas_con_info_usuario

            ventas_ultima_semana = sellerSales.objects.filter(date_added__date__gte=start_of_week,date_added__date__lt=start_of_week + timedelta(days=7)).values('origin').annotate(total_ventas=Sum('grand_total'), count_origin=Count('origin'))
            ##############################
            lista_ventas_u_s=sellerSales.objects.filter(date_added__date__gte=start_of_week,date_added__date__lt=start_of_week + timedelta(days=7)).values('origin','id','grand_total')
            ventas_informacion=[]

            for venta in lista_ventas_u_s:
                items_venta=sellerSalesItems.objects.filter(sale_id=venta['id'])
                
                costo_total_venta=items_venta.aggregate(costo_total=Sum('product_id__costo'))['costo_total'] or 0
                ganancia_venta = venta['grand_total'] - costo_total_venta
                
                informacion={
                    'ganancia':ganancia_venta,
                    'origin':venta['origin'],
                    'cantidadArticulos':len(items_venta)
                } 
                ventas_informacion.append(informacion)

            # #print(ventas_informacion) #ya tiene cantidad de articulos por venta 'cantidadArticulos'

            cantidadArticulosOrigin={}
            for cantidad in ventas_informacion:
                origin=cantidad['origin']
                cantidadArticulos = cantidad['cantidadArticulos']
                if origin in cantidadArticulosOrigin:
                    cantidadArticulosOrigin[origin] += cantidadArticulos
                else:
                    cantidadArticulosOrigin[origin] = cantidadArticulos
            
            # #print(cantidadArticulosOrigin)
            
            sumas_por_origin = {}
            for dato in ventas_informacion:
                ##print(dato)
                origin = dato['origin']
                ganancia = dato['ganancia']
                cantidadArticulos = dato['cantidadArticulos']
                
                if origin in sumas_por_origin:
                    sumas_por_origin[origin] += ganancia
                    # sumas_por_origin['cantidadArticulos']+= cantidadArticulos
                else:
                    sumas_por_origin[origin] = ganancia
            resultado = [{'origin': origin, 'ganancia': ganancia} for origin, ganancia in sumas_por_origin.items()]
            
            
            ##########################
            user_ids_ultima_semana = ventas_ultima_semana.values_list('origin', flat=True).distinct()
            usuarios_ultima_semana = User.objects.filter(id__in=user_ids_ultima_semana)

            ventas_ultima_semana_con_nombres_de_usuario = []
            
            resultado_combinado = []
            
            for venta in ventas_ultima_semana:
                # #print(venta)
                conteo=venta['count_origin']
                origin = venta['origin']
                total_ventas = venta['total_ventas']
                ganancia = sumas_por_origin.get(origin, 0)  # Obtenemos la ganancia correspondiente al origin, si no existe, es 0
                cantidadArticulos=cantidadArticulosOrigin.get(origin,0)#Obtenemos la cantidad de articulos vendidos, sino existe, es 0
                
                
                resultado_combinado.append({'origin': origin, 'total_ventas': total_ventas, 'ganancia': ganancia,'conteo':conteo,'cantidadArticulos':cantidadArticulos})

            # #print(resultado_combinado)

            for venta in resultado_combinado:#ventas_ultima_semana:
                usuario = usuarios_ultima_semana.get(id=venta['origin'])
                salario=0
                conteo=venta['conteo']
                if venta['total_ventas'] >= 22000 and venta['total'] < 26000:#################TABULADOR DE SALARIOS
                    salario=venta['total_ventas']*1.11
                elif venta['total_ventas']>= 26000 and venta['total'] < 30000:
                    salario=venta['total_ventas']*1.12
                elif venta['total_ventas']>= 30000 and venta['total'] < 34000:
                    salario=venta['total_ventas']*1.13
                elif venta['total_ventas']>= 34000 and venta['total'] < 40000:
                    salario=venta['total_ventas']*1.14
                elif venta['total_ventas']>= 40000:
                    salario=venta['total_ventas']*1.15
                elif venta['total_ventas'] < 22000:
                    salario=1750
                else:
                    salario=0
                    
                venta_con_nombre_usuario = {
                    'username':usuario.username,
                    'first_name':usuario.first_name,
                    'last_name':usuario.last_name,
                    'total_ventas': venta['total_ventas'],
                    'salario':salario,
                    'ganancia':venta['ganancia'],
                    'conteo':conteo,
                    'cantidadArticulos':venta['cantidadArticulos'],
                }
                ventas_ultima_semana_con_nombres_de_usuario.append(venta_con_nombre_usuario)
            ventas_ultima_semana=ventas_ultima_semana_con_nombres_de_usuario

            ganancia_vendedores=0
            for elemento in ventas_ultima_semana:
                ganancia_vendedores+=elemento['ganancia']

        except Exception as e:
            # #print(e)
            pass
        
        

        now = datetime.now()
        current_year = now.strftime("%Y")
        current_month = now.strftime("%m")
        current_day = now.strftime("%d")
        transaction = len(Sales.objects.filter(
            date_added__year=current_year,
            date_added__month = current_month,
            date_added__day = current_day
        ))
        today_sales = Sales.objects.filter(
            date_added__year=current_year,
            date_added__month = current_month,
            date_added__day = current_day
        ).all()
        today_sales_seller = sellerSales.objects.filter(
            date_added__year=current_year,
            date_added__month = current_month,
            date_added__day = current_day
        ).all()
        transaction_seller = len(sellerSales.objects.filter(
            date_added__year=current_year,
            date_added__month = current_month,
            date_added__day = current_day
        ))
        historic_number_pv = len(Sales.objects.all())
        historic_number_sellers = len(sellerSales.objects.all())
        historic_total_sales_money_sellers=sum(sellerSales.objects.all().values_list('grand_total',flat=True))
        historic_total_sales_money_pv=sum(Sales.objects.all().values_list('grand_total',flat=True))
        total_historic_transactions=historic_number_pv+historic_number_sellers
        total_historic_money=historic_total_sales_money_pv+historic_total_sales_money_sellers

        total_sales = sum(today_sales.values_list('grand_total',flat=True))
        total_sales_seller =sum(today_sales_seller.values_list('grand_total',flat=True))
        total_sales_combined=total_sales+total_sales_seller
        total_number_sales=transaction_seller+transaction
        


    # CARACTERÍSTICAS PARA SER CONSIDERADO UN PRODUCTO MAS VENDIDO:
    #  DEBE SER EL PRODUCTO CON MAYOR CANTIDAD DE VENTAS
    #     * DISPONIBLE EN EL MODELO DE SALES ITEMS PARA PUNTOS DE VENTA
    #     * DISPONIBLE EN EL MODELO DE SELLER SALES ITEMS


        #PRODUCTO MAS VENDIDO PV
        producto_mas_vendido_pv= salesItems.objects.values('product_id__nombreArticulo').annotate(repetido=Count('product_id')).order_by('-repetido').first()
        
        ###print(producto_mas_vendido_pv)
        #PRODUCTO MAS VENDIDO VENDEDOR
        producto_mas_vendido_seller = sellerSalesItems.objects.values('product_id__nombreArticulo').annotate(repetido=Count('product_id')).order_by('-repetido').first()
        try:
            url_producto_mas_vendido_sellers=salesItems.objects.values('product_id__urlArticulo').annotate(repetido=Count('product_id')).order_by('-repetido').first()
            url_producto_mas_vendido_sellers=url_producto_mas_vendido_sellers['product_id__urlArticulo']
        except:
            url_producto_mas_vendido_sellers="https://static.vecteezy.com/system/resources/thumbnails/007/126/739/small/question-mark-icon-free-vector.jpg"
        try:
            url_producto_mas_vendido_pv=salesItems.objects.values('product_id__urlArticulo').annotate(repetido=Count('product_id')).order_by('-repetido').first()
            url_producto_mas_vendido_pv=url_producto_mas_vendido_pv['product_id__urlArticulo']
        except:
            url_producto_mas_vendido_pv="https://static.vecteezy.com/system/resources/thumbnails/007/126/739/small/question-mark-icon-free-vector.jpg"
        #PUNTO VENTA CON MAS VENTAS
        
        try:

            punto_venta_mas_ventas=Sales.objects.values('origin').annotate(repetido=Count('origin')).order_by('-repetido').first()
            punto_venta_mas_ventas=User.objects.all().filter(id=punto_venta_mas_ventas['origin']).values('first_name','last_name','username').get()
        except Exception as e:
            #print(e)
            pass
        #VENDEDOR CON MAS VENTAS
        try:
            vendedor_mas_ventas=sellerSales.objects.values('origin').annotate(repetido=Count('origin')).order_by('-repetido').first()
            vendedor_mas_ventas=User.objects.all().filter(id=vendedor_mas_ventas['origin']).values('first_name','last_name','username').get()
        except Exception as e:
            
            vendedor_mas_ventas="No hay"
        
        #COSTOS DE PUNTOS DE VENTA
        try:
            costosPuntoVenta = pd.DataFrame(costosEmpresaPuntosVentaModel.objects.values('fecha').annotate(
                total_salarios=Sum('salarios'),
                total_productos=Sum('productos'),
                total_otros=Sum('otros'),
                total=Sum('salarios')+Sum('productos')+Sum('otros')
                ))
        except:
            costosPuntoVenta=0
        #COSTOS DE VENDEDORES
        try:
            costosVendedores = pd.DataFrame(costosEmpresaVendedoresModel.objects.values('fecha').annotate(
                total_salario=Sum('salario'),
                total_gasolina=Sum('gasolina'),
                total_otros=Sum('otros'),
                total=Sum('salario')+Sum('gasolina')+Sum('otros')
                ))
        except:
            costosVendedores=0

        ##print(costosVendedores)
        try:
            costosVendedores['fecha']=pd.to_datetime(costosVendedores['fecha'])
        except:
            pass
        try:
            resultados_agrupados = costosVendedores.groupby('fecha').sum().reset_index()
        except:
            pass
        # ##print(resultados_agrupados.columns)
        try:
            costosPuntoVenta['fecha']=pd.to_datetime(costosPuntoVenta['fecha'])
        except:
            pass
        try:
            resultados_agrupados_puntoVenta = costosPuntoVenta.groupby('fecha').sum().reset_index()
        except:
            pass
        ##print(resultados_agrupados_puntoVenta.columns)

        
        df_ventas_puntos_venta=pd.DataFrame(Sales.objects.values('date_added').annotate(total_sales=Sum('grand_total')))
        try:
            df_ventas_puntos_venta['date_added']=pd.to_datetime(df_ventas_puntos_venta['date_added'])#.dt.strftime('%Y-%m-%d')
            df_ventas_puntos_venta = df_ventas_puntos_venta.groupby(df_ventas_puntos_venta['date_added'].dt.date)['total_sales'].sum().reset_index()
            df_ventas_puntos_venta=df_ventas_puntos_venta.set_index('date_added').sort_index()
        except:
            pass
        # df_ventas_puntos_venta['date_added']=df_ventas_puntos_venta['date_added'].strftime('%Y-%m-%d')
        df_ventas_vendedores=pd.DataFrame(sellerSales.objects.values('date_added').annotate(total_sales=Sum('grand_total')))
        try:
            df_ventas_vendedores['date_added']=pd.to_datetime(df_ventas_vendedores['date_added'])#.dt.strftime('%Y-%m-%d')
            df_ventas_vendedores = df_ventas_vendedores.groupby(df_ventas_vendedores['date_added'].dt.date)['total_sales'].sum().reset_index()
            df_ventas_vendedores=df_ventas_vendedores.set_index('date_added').sort_index()

        except:
            pass

        try:
            lista_fechas_costos_vendedores=list(date.strftime('%Y-%m-%d') for date in costosVendedores['fecha'])
        except:
            lista_fechas_costos_vendedores=[0]
        try:
            lista_total_salarios_vendedores=list(costosVendedores['total_salario'])
        except:
            lista_total_salarios_vendedores=[0]
        
        try:
            lista_total_gasolina_vendedores=list(costosVendedores['total_gasolina'])
        except:
            lista_total_gasolina_vendedores=[0]
        try:
            lista_total_otros_vendedores=list(costosVendedores['total_otros'])
        except:
            lista_total_otros_vendedores=[0]
        try:
            lista_total_vendedores=list(costosVendedores['total'])
        except:
            lista_total_vendedores=[0]
        lista_concatenada_vendedores_valores=list(itertools.chain(lista_total_salarios_vendedores,lista_total_gasolina_vendedores,lista_total_otros_vendedores,lista_total_vendedores))
        

        try:
            lista_fechas_puntos_venta=list(date.strftime('%Y-%m-%d') for date in costosPuntoVenta['fecha'])
        except:
            lista_fechas_puntos_venta=[0]
        try:
            lista_total_salarios_puntos_venta=list(costosPuntoVenta['total_salarios'])
        except:
            lista_total_salarios_puntos_venta=[0]
        try:
            lista_productos_puntos_venta=list(costosPuntoVenta['total_productos'])
        except:
            lista_productos_puntos_venta=[0]
        try:
            lista_otros_puntos_venta=list(costosPuntoVenta['total_otros'])
        except:
            lista_otros_puntos_venta=[0]
        try:
            lista_total_puntos_venta=list(costosPuntoVenta['total'])
        except:
            lista_total_puntos_venta=[0]
        lista_concatenada_puntos_venta_valores=list(itertools.chain(lista_total_salarios_puntos_venta,lista_productos_puntos_venta,lista_otros_puntos_venta,lista_total_puntos_venta))

        
        try:
            lista_fechas_vendedores=list(date.strftime('%Y-%m-%d') for date in df_ventas_vendedores.index)
        except:
            lista_fechas_vendedores=[0]
        try:
            lista_datos_ventas_vendedores=list(df_ventas_vendedores['total_sales'])
        except:
            lista_datos_ventas_vendedores=[0]

        try:
            lista_fechas_ventas_puntos_venta=list(date.strftime('%Y-%m-%d') for date in df_ventas_puntos_venta.index)
        except:
            lista_fechas_ventas_puntos_venta=[0]
        try:
            lista_datos_ventas_puntos_venta=list(df_ventas_puntos_venta['total_sales'])
        except:
            lista_datos_ventas_puntos_venta=[0]
        
        df_combinado = pd.concat([df_ventas_puntos_venta, df_ventas_vendedores], ignore_index=False)
        try:
                
            df_combinado_sumado = df_combinado.groupby('date_added').sum()
            df_combinado_sumado = df_combinado_sumado.reset_index()
            df_combinado_sumado['date_added'] = pd.to_datetime(df_combinado_sumado['date_added'])
        except:
            df_combinado_sumado=[]
        try:
            lista_fechas=list(df_combinado_sumado['date_added'].dt.strftime('%Y-%m-%d'))
            lista_datos=list(df_combinado_sumado['total_sales'])
        except:
            lista_fechas=[]
            lista_datos=[]


        try:
            fecha_actual=timezone.now()
            fecha_inicio=fecha_actual-timedelta(14)
            ventas_ultimas_dos_semanas_puntosVenta = Sales.objects.filter(date_added__gte=fecha_inicio, date_added__lte=fecha_actual).values('id','origin','date_added','grand_total','code')
            #################################DE LOS ULTIMOS 14 DIAS PUNTOS DE VENTA
            user_ids = ventas_ultimas_dos_semanas_puntosVenta.values_list('origin', flat=True).distinct()
            usuarios = User.objects.filter(id__in=user_ids)
            user_info_dict = {user.id: {'username': user.username, 'first_name': user.first_name, 'last_name': user.last_name} for user in usuarios}
            ventas_con_info_usuario = []
            for venta in ventas_ultimas_dos_semanas_puntosVenta:
                items_venta = salesItems.objects.filter(sale_id=venta['id'])
                
                costo_total_venta = items_venta.aggregate(costo_total=Sum('product_id__costo'))['costo_total'] or 0
                ganancia_venta = venta['grand_total'] - costo_total_venta

                user_id = venta['origin']
                usuario_info = user_info_dict.get(user_id, {})
                venta_con_info_usuario = {
                    'origin': user_id,
                    'username': usuario_info.get('username', 'Usuario Desconocido'),
                    'first_name': usuario_info.get('first_name', 'Sin Nombre'),
                    'last_name': usuario_info.get('last_name', 'Sin Apellido'),
                    'date_added': venta['date_added'],
                    'grand_total': venta['grand_total'],
                    'code': venta['code'],
                    'ganancia':ganancia_venta,
                }
                ventas_con_info_usuario.append(venta_con_info_usuario)
            ventas_ultimas_dos_semanas_puntosVenta=ventas_con_info_usuario
            #########################################################################
            ###########################################DE LA ULTIMA SEMANA INICIANDO CADA LUNES
            fecha_actual = timezone.now()
            dia_semana = fecha_actual.weekday()
            fecha_inicio_semana = fecha_actual - timedelta(days=dia_semana)
            ventas_semana_actual_puntosVenta = Sales.objects.filter(date_added__date__gte=fecha_inicio_semana,date_added__date__lt=fecha_actual).values('origin').annotate(total_ventas=Sum('grand_total'), count_origin=Count('origin'))
            
            lista_ventas_u_s_puntosVenta=Sales.objects.filter(date_added__date__gte=fecha_inicio_semana,date_added__date__lt=fecha_actual).values('origin','id','grand_total')
            ventas_informacion_puntosVenta=[]

            for venta in lista_ventas_u_s_puntosVenta:
                items_venta=salesItems.objects.filter(sale_id=venta['id'])
                
                costo_total_venta=items_venta.aggregate(costo_total=Sum('product_id__costo'))['costo_total'] or 0
                # #print(costo_total_venta)
                ganancia_venta = venta['grand_total'] - costo_total_venta
                # #print(ganancia_venta)
                informacion={
                    'ganancia':ganancia_venta,
                    'origin':venta['origin'],
                    'cantidadArticulos':len(items_venta)
                } 
                ventas_informacion_puntosVenta.append(informacion)

            # #print(ventas_informacion_puntosVenta) #ya tiene cantidad de articulos por venta 'cantidadArticulos'

            cantidadArticulosOrigin={}
            for cantidad in ventas_informacion_puntosVenta:
                origin=cantidad['origin']
                cantidadArticulos = cantidad['cantidadArticulos']
                if origin in cantidadArticulosOrigin:
                    cantidadArticulosOrigin[origin] += cantidadArticulos
                else:
                    cantidadArticulosOrigin[origin] = cantidadArticulos
            
            # #print(cantidadArticulosOrigin)
            
            sumas_por_origin_puntosVenta = {}
            for dato in ventas_informacion_puntosVenta:
                # #print(dato)
                origin = dato['origin']
                ganancia = dato['ganancia']
                cantidadArticulos = dato['cantidadArticulos']
                
                if origin in sumas_por_origin_puntosVenta:
                    sumas_por_origin_puntosVenta[origin] += ganancia
                    # sumas_por_origin['cantidadArticulos']+= cantidadArticulos
                else:
                    sumas_por_origin_puntosVenta[origin] = ganancia
            resultado = [{'origin': origin, 'ganancia': ganancia} for origin, ganancia in sumas_por_origin_puntosVenta.items()]
            # #print(resultado)
            
            
            ##########################
            user_ids_ultima_semana = ventas_semana_actual_puntosVenta.values_list('origin', flat=True).distinct()
            usuarios_ultima_semana = User.objects.filter(id__in=user_ids_ultima_semana)

            ventas_semana_actual_puntosVenta_con_nombres_de_usuario = []
            
            resultado_combinado_puntosVenta = []
            
            for venta in ventas_semana_actual_puntosVenta:
                # #print(venta)
                conteo=venta['count_origin']
                origin = venta['origin']
                total_ventas = venta['total_ventas']
                ganancia = sumas_por_origin_puntosVenta.get(origin, 0)  # Obtenemos la ganancia correspondiente al origin, si no existe, es 0
                cantidadArticulos=cantidadArticulosOrigin.get(origin,0)#Obtenemos la cantidad de articulos vendidos, sino existe, es 0
                
                
                resultado_combinado_puntosVenta.append({'origin': origin, 'total_ventas': total_ventas, 'ganancia': ganancia,'conteo':conteo,'cantidadArticulos':cantidadArticulos})

            # #print(resultado_combinado)

            for venta in resultado_combinado_puntosVenta:#ventas_ultima_semana:
                usuario = usuarios_ultima_semana.get(id=venta['origin'])
                salario=0
                conteo=venta['conteo']
                if venta['total_ventas'] >= 22000 and venta['total'] < 26000:#################TABULADOR DE SALARIOS
                    salario=venta['total_ventas']*1.11
                elif venta['total_ventas']>= 26000 and venta['total'] < 30000:
                    salario=venta['total_ventas']*1.12
                elif venta['total_ventas']>= 30000 and venta['total'] < 34000:
                    salario=venta['total_ventas']*1.13
                elif venta['total_ventas']>= 34000 and venta['total'] < 40000:
                    salario=venta['total_ventas']*1.14
                elif venta['total_ventas']>= 40000:
                    salario=venta['total_ventas']*1.15
                elif venta['total_ventas'] < 22000:
                    salario=1750
                else:
                    salario=0
                    
                venta_con_nombre_usuario = {
                    'username':usuario.username,
                    'first_name':usuario.first_name,
                    'last_name':usuario.last_name,
                    'total_ventas': venta['total_ventas'],
                    'salario':salario,
                    'ganancia':venta['ganancia'],
                    'conteo':conteo,
                    'cantidadArticulos':venta['cantidadArticulos'],
                }
                ventas_semana_actual_puntosVenta_con_nombres_de_usuario.append(venta_con_nombre_usuario)
            ventas_ultima_semana_puntosVenta=ventas_semana_actual_puntosVenta_con_nombres_de_usuario
            ganancias_puntos_venta=0
            for elemento in ventas_ultima_semana_puntosVenta:
                ganancias_puntos_venta += elemento['ganancia']

            ganancia_global_semanal=0
            ganancia_global_semanal=ganancia_vendedores+ganancias_puntos_venta

        except Exception as e:
            pass
        
        try:
            totalVendedoresSemanal=Sales.objects.filter(date_added__gte=fecha_inicio_semana, date_added__lte=fecha_actual).aggregate(totalVentasVendedoresSemanal=Sum('grand_total'))
            totalPuntosVentaSemanal=sellerSales.objects.filter(date_added__gte=fecha_inicio_semana, date_added__lte=fecha_actual).aggregate(totalVentasPuntosVentaSemanal=Sum('grand_total'))
            totalGlobalSemanal=totalVendedoresSemanal['totalVentasVendedoresSemanal']+totalPuntosVentaSemanal['totalVentasPuntosVentaSemanal']
        except Exception as e:
            totalGlobalSemanal=0

        context = {
            ########################       DATOS DEL GRÁFICO       ########################
            # 'graphic': graphic,
            'ganancia_global_semanal':ganancia_global_semanal,
            'ganancia_vendedores':ganancia_vendedores,
            'ganancias_puntos_venta':ganancias_puntos_venta,
            'totalVendedoresSemanal':totalVendedoresSemanal,
            'totalPuntosVentaSemanal':totalPuntosVentaSemanal,
            'totalGlobalSemanal':totalGlobalSemanal,
            'today':today,
            'ventas_ultima_semana':ventas_ultima_semana,#VENDEDORES
            'ventas_ultimas_dos_semanas':ventas_ultimas_dos_semanas,#VENDEDORES
            'ventas_ultimas_dos_semanas_puntosVenta':ventas_ultimas_dos_semanas_puntosVenta,#PUNTOSVENTA
            'ventas_ultima_semana_puntosVenta':ventas_ultima_semana_puntosVenta,
            'ventas_semana_actual_puntosVenta':ventas_semana_actual_puntosVenta,
            'start_of_week':start_of_week,
            'start_of_two_weeks_ago':start_of_two_weeks_ago,
            ###############################################################################
            'lista_concatenada_puntos_venta_valores':lista_concatenada_puntos_venta_valores,
            'lista_concatenada_vendedores_valores':lista_concatenada_vendedores_valores,
            'lista_fechas_costos_vendedores':lista_fechas_costos_vendedores,
            'lista_total_salarios_vendedores':lista_total_salarios_vendedores,
            'lista_total_gasolina_vendedores':lista_total_gasolina_vendedores,
            'lista_total_otros_vendedores':lista_total_otros_vendedores,
            'lista_total_vendedores':lista_total_vendedores,
            'lista_fechas_puntos_venta':lista_fechas_puntos_venta,
            'lista_total_salarios_puntos_venta':lista_total_salarios_puntos_venta,
            'lista_productos_puntos_venta':lista_productos_puntos_venta,
            'lista_otros_puntos_venta':lista_otros_puntos_venta,
            'lista_total_puntos_venta':lista_total_puntos_venta,
            'costosPuntoVenta':costosPuntoVenta,
            'costosVendedores':costosVendedores,
            'url_producto_mas_vendido_sellers':url_producto_mas_vendido_sellers,
            'url_producto_mas_vendido_pv':url_producto_mas_vendido_pv,
            'lista_fechas':lista_fechas,
            'lista_datos':lista_datos,
            'lista_fechas_vendedores':lista_fechas_vendedores,
            'lista_datos_ventas_vendedores':lista_datos_ventas_vendedores,
            'lista_datos_ventas_puntos_venta':lista_datos_ventas_puntos_venta,
            'lista_fechas_ventas_puntos_venta':lista_fechas_ventas_puntos_venta,
            ###################################### DEL DIA #########################################################
            'transaction' : transaction,#NUMERO DE VENTAS TODOS LOS PUNTOS DE VENTA
            'transaction_seller' : transaction_seller,#NUMERO DE VENTAS TODOS LOS VENDEDORES
            'total_sales' : total_sales,#TOTAL EN DINERO DE LAS VENTAS POR PUNTOS DE VENTA
            'total_sales_seller' : total_sales_seller,#TOTAL EN DINERO DE LAS VENTAS POR VENDEDORES
            'total_sales_combined':total_sales_combined,#TOTAL EN DINERO DE TODOS LOS VENDEDORES Y PUNTOS DE VENTA
            'total_number_sales':total_number_sales,#TOTAL DE VENTAS DEL DIA DE HOY
            ###################################### DE TODO EL TIEMPO #########################################################
            'historic_number_sellers':historic_number_sellers,
            'historic_number_pv':historic_number_pv,
            'historic_total_sales_money_sellers':historic_total_sales_money_sellers,
            'historic_total_sales_money_pv':historic_total_sales_money_pv,
            'total_historic_transactions':total_historic_transactions,
            'total_historic_money':total_historic_money,
            #################################### PRODUCTO GANADOR #############################################
            'producto_mas_vendido_pv':producto_mas_vendido_pv,#PUNTO DE VENTA
            'producto_mas_vendido_seller':producto_mas_vendido_seller,#VENDEDOR
            #################################### MEJOR PUNTO VENTA ###############################################
            'punto_venta_mas_ventas':punto_venta_mas_ventas,
            #################################### MEJOR VENDEDOR ###############################################
            'vendedor_mas_ventas':vendedor_mas_ventas,
        }
        return render(request, 'finance.html',context)
    else:
        return render(request,'forbiden.html')


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
            ##print(e)
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
        ##print(e)
        return redirect('sellersList')

    context = {
        "active_icon": "customers",
        "customer": customer,
    }

    if request.method == 'POST':
        try:
            # Save the POST arguments
            data = request.POST
            ##print(data)

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
            ##print(e)
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
        ##print(e)
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
        ##print(products)
        for product in products:
            ##print(product.product_id_id)
            ##print(product)            
            product_json.append({'id':product.id, 'name':product.nombreArticulo, 'price':float(product.precioVentaVendedor),'qty':float(product.qty),'general_id':product.product_id_id})
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
        ##print(products)
        for product in products:
            ##print(product.product_id_id)
            ##print(product)            
            product_json.append({'id':product.id, 'name':product.nombreArticulo, 'price':float(product.precioVentaVendedorExterno),'qty':float(product.qty),'general_id':product.product_id_id})
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
    ##print(data)
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
        for prod in data.getlist('product_id[]'):
            #product_id = prod 
            sale = sellerSales.objects.filter(id=sale_id).first()
            product = articulosModel.objects.all().filter(id=prod).first()
            qty = int(data.getlist('qty[]')[i] )
            
            price = data.getlist('price[]')[i]
            total = float(qty) * float(price)
            discount = float(data.getlist('disc[]')[i])
            ##print({'sale_id' : sale, 'product_id' : product, 'qty' : qty, 'price' : price, 'total' : total})

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
        articulosModel.success(request, "Venta guardada.")
    except Exception as e:
        resp['msg'] = "Ocurrió un error"
        ##print("Unexpected errors:", e)###############################
    return HttpResponse(json.dumps(resp),content_type="application/json")


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
        for elemento in ItemList:
            discount=(elemento.discount*elemento.price*elemento.qty)/100
            # #print(discount)
            total_discounts+=discount
        total=transaction["grand_total"]+total_discounts
        
        
        context = {
            "total":total,
            "total_discounts" : total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList
        }

        return render(request, 'receipt.html',context)
    else:
        return render(request,'forbiden.html')
    # return HttpResponse('')


def consultaPropioInventario(request,id_vendedor):
    if request.user.is_authenticated:
        ##print(id_vendedor)
        articulosVendedor=sellerInventory.objects.all().filter(seller_id=id_vendedor)
        costoStock=0
        for elemento in articulosVendedor:
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
        ##print(id_vendedor)
        articulosVendedor=sellerInventory.objects.all().filter(seller_id=id_vendedor)
        costoStock=0
        for elemento in articulosVendedor:
            costoStock=costoStock+elemento.qty*elemento.precioVentaVendedorExterno
        context={
            'lista':articulosVendedor,
            'costoStock':costoStock,

        }
        return render(request,'vendedorExternoConsultaPropioInventario.html',context)
    else:
        return render(request,'forbiden.html')
    
def consultaPropioInventarioMatriz(request,id_vendedor):
    if request.user.is_authenticated:
        ##print(id_vendedor)
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
            # ##print(data)
            sale_data_vendedor.append(data)
        # ##print(sale_data)  

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
            # ##print(data)
            sale_data_vendedor.append(data)
        # ##print(sale_data)  

        context = {
            'page_title':'Sales Transactions',
            'sale_data':sale_data_vendedor,
        }
        # return HttpResponse('')
        return render(request, 'matrixSales.html',context)
    else:
        return render(request,'forbiden.html')

# def inventariosPV(request,pk=None):#INVENTARIOS DE VENDEDORES
#     if request.user.is_authenticated:

#         inventarioPV = get_object_or_404(Seller, pk=pk) if pk else None
#         lista=pvInventory.objects.all()

#         for item in lista:
#             item.costo_total = item.qty * item.product_id.costo
#             item.precio_publico_total = item.qty * item.product_id.precioVentaPublico
#             item.ganancia = item.precio_publico_total - item.costo_total
#             item.gananciaUnitaria=item.product_id.precioVentaPublico - item.product_id.costo

#         total_public_price = sum(item.precio_publico_total for item in lista)
#         total_cost = sum(item.qty * item.product_id.costo for item in lista)
#         gananciaTotal=total_public_price-total_cost
        
#         if request.method == 'POST':
#             form = inventarioPuntoVentaForm(request.POST,instance=inventarioPV)
#             if form.is_valid():
#                 form.save()
#             return redirect('puntosVenta')
#         else:
#             form = inventarioPuntoVentaForm(instance=inventarioPV)
#             return render(request, 'listaInventariosPV.html', {'form': form,'inventario':inventarioPV,'lista':lista,'total_cost':total_cost,'total_public_price': total_public_price,'gananciaTotal':gananciaTotal})
        
#     else:
#         return render(request,'forbiden.html')

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
    ##print(data)
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
            ##print({'sale_id' : sale, 'product_id' : product, 'qty' : qty, 'price' : price, 'total' : total})

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
        #print("Unexpected errors:", e)###############################
    return HttpResponse(json.dumps(resp),content_type="application/json")

def save_posMatrix(request):
    resp = {'status':'failed','msg':''}
    data = request.POST
    ##print(data)
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
            # print({'sale_id' : sale, 'product_id' : product, 'qty' : qty, 'price' : price, 'total' : total})

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
        print(e)
        resp['msg'] = "Ocurrió un error"
        #print("Unexpected errors:", e)###############################
    return HttpResponse(json.dumps(resp),content_type="application/json")


def receiptPV(request):
    if request.user.is_authenticated:
        #print("Vista puntos venta")
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
            #print(discount)
            total_discounts+=discount
        total=transaction["grand_total"]+total_discounts
        

        context = {
            "total":total,
            "total_discounts":total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList
        }

        return render(request, 'receipt.html',context)
    else:
        return render(request,'forbiden.html')
    # return HttpResponse('')

def receiptMatrix(request):
    if request.user.is_authenticated:
        #print("Vista puntos venta")
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
            #print(discount)
            total_discounts+=discount
        total=transaction["grand_total"]+total_discounts
        

        context = {
            "total":total,
            "total_discounts":total_discounts,
            "transaction" : transaction,
            "salesItems" : ItemList
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


        for item in lista:
            item.costo_total = item.qty * item.product_id.costo
            item.precio_publico_total = item.qty * item.product_id.precioVentaVendedorReparto
            item.ganancia = item.precio_publico_total - item.costo_total
            item.gananciaUnitaria = item.product_id.precioVentaVendedorReparto - item.product_id.costo

        products = articulosModel.objects.all()######NECESARIO PARA FILTRAR SOLO EL INVENTARIO DE CADA VENDEDOR
        product_json = []
        ##print(products)
        for product in products:
            ##print(product.product_id_id)
            ##print(product)            
            product_json.append({'id':product.pk, 'name':product.nombreArticulo, 'price':float(product.precioVentaVendedorReparto),'qty':float(product.cantidad),'descripcionArticulo':product.descripcionArticulo})

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
                        #print("Producto Nuevo")
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
        ##print(products)
        for product in products:
            ##print(product.product_id_id)
            ##print(product)            
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
                        #print("Producto Nuevo")
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
                        #print("Producto Nuevo")
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
                    # RegistroInventarioVendedores.objects.create(
                    #     usuario=request.user,
                    #     nombre_producto=instance.product_id.nombreArticulo,  # Ajusta esto según el nombre del campo en tu modelo articulosModel
                    #     cantidad=instance.qty
                    #     )

                return redirect('cargarInventarioPV')
        else:
            form = inventarioCargaPVForm(instance=inventarioPuntoVenta)

            return render(request, 'listaInventarioPV.html', {'form': form, 'inventario': inventarioPuntoVenta, 'lista': lista, 'total_public_price': total_public_price, 'total_cost': total_cost, 'gananciaTotal': gananciaTotal,'registro':registro})

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
            # ##print(data)
            sale_data_vendedor.append(data)
        # ##print(sale_data)  

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


        # #print(todos_cargas)
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