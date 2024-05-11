from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


import datetime

class usersPermission(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_externalSeller = models.BooleanField(default=False)
    is_matrixSeller = models.BooleanField(default=False)
    def clean(self):
        if self.is_externalSeller and self.is_matrixSeller:
            raise ValidationError("Solo una de las variables booleanas puede ser verdadera.")
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()  # Realizar la validación antes de guardar
        super().save(*args, **kwargs)


class proveedoresModel(models.Model):
    nombreProveedor=models.CharField(max_length=40,verbose_name="Nombre del Proveeedor")
    apellidosProveedor=models.CharField(max_length=80,verbose_name="Apellidos del Proveedor")
    direccionProveedor=models.CharField(max_length=80,verbose_name="Dirección del Proveedor")
    telefonoProveedor=models.CharField(max_length=80,verbose_name="Dirección del Proveedor")
    correoElectronicoProveedor=models.CharField(max_length=40,verbose_name="Correo electrónico del Proveedor")
    def __str__(self):
        return f"{self.nombreProveedor} {self.apellidosProveedor}"
    
class specialPermissions(models.Model):
    is_externalSeller=models.BooleanField(default=False)
    is_matrixSeller=models.BooleanField(default=False)


class articulosModel(models.Model):#ARTICULOS O DULCES A VENDER DENTRO DE LA DULCERIA
    nombreArticulo=models.CharField(max_length=100,verbose_name="Nombre del artículo")
    unidad=models.CharField(max_length=200,verbose_name="Unidad",default="Caja")
    descripcionArticulo=models.TextField(max_length=400,verbose_name="Descripción del artículo")
    costo=models.FloatField(verbose_name="Costo")
    precioVentaPublico=models.FloatField(verbose_name="Precio de venta al público")
    precioVentaVendedorReparto=models.FloatField(verbose_name="Precio de venta al vendedor de reparto",default=99999)
    precioVentaVendedorExterno=models.FloatField(verbose_name="Precio de venta al vendedor externo",default=0)
    cantidadMinima=models.FloatField(verbose_name="Cantidad mínima de producto")
    cantidadMaxima=models.FloatField(verbose_name="Cantidad máxima de producto")
    #cantidadMayoreo=models.FloatField(verbose_name="Cantidad a partir de la cual se cuenta como mayoreo",default=2)
    urlArticulo=models.CharField(max_length=200,verbose_name="URL de la imagen del artículo", default="https://cdn.pixabay.com/photo/2022/12/29/17/14/candy-7685391_1280.png")
    cantidad=models.FloatField(verbose_name="Stock maestro")
    
    #sucursal=models.CharField(max_length=200,verbose_name="Nombre de la sucursal",default="")
    def __str__(self):
        return self.nombreArticulo


class Seller(models.Model):#REGISTRO DE VENDEDORES
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, blank=True, null=True)
    address = models.TextField(max_length=256, blank=True, null=True)
    email = models.EmailField(max_length=256, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    photo = models.ImageField(upload_to='seller_photos/', blank=True, null=True)

    class Meta:
        db_table = 'Sellers'

    def __str__(self) -> str:
        return self.first_name + " " + self.last_name

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def to_select2(self):
        item = {
            "label": self.get_full_name(),
            "value": self.id
        }
        return item


class puntoVenta(models.Model):#REGISTRO DE PUNTOS DE VENTA
    nombrePV=models.CharField(max_length=40,verbose_name="Nombre del Punto de Venta")
    direccionPV=models.CharField(max_length=40,verbose_name="Dirección del Punto de Venta")
    telefonoPV=models.IntegerField(verbose_name="Teléfono del Punto de Venta")
    def __str__(self):
        return self.nombrePV


class stockPuntoVenta(models.Model):#STOCK DE CADA PUNTO DE VENTA
    sucursal = models.ForeignKey(puntoVenta, on_delete=models.CASCADE)
    producto = models.ForeignKey(articulosModel, on_delete=models.CASCADE)
    stock = models.IntegerField(default=0)
    class Meta:
        unique_together = ('sucursal', 'producto')


class Sales(models.Model):#VENTAS DE PUNTOS DE VENTA
    code = models.CharField(max_length=100)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    tendered_amount = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)
    date_added = models.DateTimeField(default=timezone.now) 
    date_updated = models.DateTimeField(auto_now=True) 
    origin=models.IntegerField(blank=True,null=True)

    #puntoVenta=models.ForeignKey(puntoVenta,on_delete=models.CASCADE)
    

    def __str__(self):
        return self.code


class salesItems(models.Model):#ARTICULOS DE VENTAS
    sale_id = models.ForeignKey(Sales,on_delete=models.CASCADE)
    product_id = models.ForeignKey(articulosModel,on_delete=models.CASCADE)
    price = models.FloatField(default=0)
    qty = models.FloatField(default=0)
    total = models.FloatField(default=0)
    discount = models.FloatField(default=0)

from django.contrib.auth.models import User

class sellerInventory(models.Model):#INVENTARIO DE VENDEDORES
    seller_id = models.ForeignKey(User,on_delete=models.CASCADE,verbose_name="Vendedor")
    product_id = models.ForeignKey(articulosModel,on_delete=models.CASCADE,verbose_name="Producto")
    precioVentaVendedor=models.FloatField(default=0,verbose_name="Precio de venta para vendedor")
    precioVentaVendedorExterno=models.FloatField(default=0,verbose_name="Precio de venta para vendedor externo")
    qty = models.FloatField(default=0,verbose_name="Cantidad")
    #precioOriginal=models.FloatField(default=0,verbose_name="Costo para BECAANA")
    precioOriginal = models.FloatField(default=0, verbose_name="Costo para BECAANA")
    nombreArticulo=models.CharField(max_length=100,verbose_name="Nombre del artículo")


    fecha = models.DateTimeField(default=timezone.now,verbose_name="Fecha:") 
    class Meta:
        unique_together = ('product_id', 'seller_id')

    def save(self, *args, **kwargs):
        if not self.pk:  # Si es un nuevo objeto
            self.precioOriginal = self.product_id.costo
            self.nombreArticulo = self.product_id.nombreArticulo
            self.precioVentaVendedor = self.product_id.precioVentaVendedorReparto
            self.precioVentaVendedorExterno = self.product_id.precioVentaVendedorExterno
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombreArticulo


class sellerSales(models.Model):# VENTAS DE VENDEDOR
    code = models.CharField(max_length=100)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    tendered_amount = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)
    date_added = models.DateTimeField(default=timezone.now) 
    date_updated = models.DateTimeField(auto_now=True) 
    origin=models.IntegerField(blank=True,null=True)


    #seller_id = models.ForeignKey(Seller,on_delete=models.CASCADE,verbose_name="Vendedor",default="")


    def __str__(self):
        return self.code


class sellerSalesItems(models.Model):#ARTICULOS DE VENTAS DE VENDEDOR
    sale_id = models.ForeignKey(sellerSales,on_delete=models.CASCADE)
    product_id = models.ForeignKey(articulosModel,on_delete=models.CASCADE)
    price = models.FloatField(default=0)
    qty = models.FloatField(default=0)
    total = models.FloatField(default=0)
    discount = models.FloatField(default=0)



class costosEmpresaVendedoresModel(models.Model):
    fecha=models.DateField(default=datetime.date.today,verbose_name="Fecha de los costos")
    vendedor=models.ForeignKey(User,on_delete=models.CASCADE,verbose_name="Nombre del vendedor al que se le dá")
    salario=models.FloatField(default=213.39,verbose_name="Salario del vendedor:")
    gasolina=models.FloatField(default=0,verbose_name="Dinero otorgado para gasolinas:")
    otros=models.FloatField(default=0,verbose_name="Otros gastos")
    

class costosEmpresaPuntosVentaModel(models.Model):
    fecha=models.DateField(default=datetime.date.today,verbose_name="Fecha de los costos")
    puntoVenta=models.ForeignKey(User,on_delete=models.CASCADE,verbose_name="Nombre del punto de venta")
    salarios=models.FloatField(default=0,verbose_name="Salarios de los trabajadores")
    productos=models.FloatField(default=0, verbose_name="Gastado en Adquisición de mercancía")
    otros=models.FloatField(default=0,verbose_name="Otros gastos")
    

class tipoVendedor(models.Model):

    # Define choices as a tuple of tuples
    MY_CHOICES = [
        ('Vendedor', 'Vendedor'),
        ('Punto de Venta', 'Punto de Venta'),
    ]
    identificador=models.IntegerField(verbose_name="Identificador del usuario")
    tipo=models.CharField(max_length=30,choices=MY_CHOICES)



class pvInventory(models.Model):#INVENTARIO DE VENDEDORES
    seller_id = models.ForeignKey(User,on_delete=models.CASCADE,verbose_name="Punto de venta:")
    product_id = models.ForeignKey(articulosModel,on_delete=models.CASCADE,verbose_name="Producto")
    precioVentaVendedor=models.FloatField(default=0,verbose_name="Precio de venta para vendedor")
    qty = models.FloatField(default=0,verbose_name="Cantidad")
    #precioOriginal=models.FloatField(default=0,verbose_name="Costo para BECAANA")
    precioOriginal = models.FloatField(default=0, verbose_name="Costo para BECAANA")
    nombreArticulo=models.CharField(max_length=100,verbose_name="Nombre del artículo")


    fecha = models.DateTimeField(default=timezone.now,verbose_name="Fecha:") 
    class Meta:
        unique_together=('product_id','seller_id')

    def save(self,*args,**kwargs):
        self.precioOriginal=self.product_id.costo
        self.nombreArticulo=self.product_id.nombreArticulo
        self.precioVentaVendedor = self.product_id.precioVentaPublico
        super().save(*args,**kwargs)

    def __str__(self):
        return self.nombreArticulo
    

class salesItemsPV(models.Model):#ARTICULOS DE VENTAS
    sale_id = models.ForeignKey(Sales,on_delete=models.CASCADE)
    product_id = models.ForeignKey(articulosModel,on_delete=models.CASCADE)
    price = models.FloatField(default=0)
    qty = models.FloatField(default=0)
    total = models.FloatField(default=0)
    discount = models.FloatField(default=0)


class RegistroInventarioVendedores(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre_producto = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_producto} - {self.fecha}"
    
class RegistroInventarioPuntoVenta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre_producto = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_producto} - {self.fecha}"