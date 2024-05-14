from django import forms
from django.forms import ModelForm
from becaanaPVm1APP1.models import stockPuntoVenta,articulosModel,sellerInventory,costosEmpresaPuntosVentaModel,costosEmpresaVendedoresModel, pvInventory, usersPermission

from django.contrib.auth.models import User


class InventarioForm(forms.ModelForm):
    class Meta:
        model = stockPuntoVenta
        fields = ['sucursal', 'producto', 'stock']

    def __init__(self, *args, **kwargs):
        super(InventarioForm, self).__init__(*args, **kwargs)
        # Limita las opciones de productos a aquellos que ya tienen inventario en la sucursal
        self.fields['producto'].queryset = articulosModel.objects.all()  # Elimina el filtro inicial





class inventarioVendedorForm(forms.ModelForm):
    class Meta:
        model=sellerInventory
        fields=['seller_id','product_id','qty']
        
    
    def __init__(self, *args, **kwargs):
        super(inventarioVendedorForm, self).__init__(*args, **kwargs)
        # Limita las opciones de productos a aquellos que ya tienen inventario en la sucursal
        self.fields['product_id'].queryset = articulosModel.objects.all()  # Elimina el filtro inicial
        self.fields['seller_id'].queryset = User.objects.filter(is_active=True,is_superuser=False,is_staff=False)

class InventoryFormSeller(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all().filter(is_active=True,is_superuser=False,is_staff=False), label="Usuario")
    product = forms.ModelChoiceField(queryset=articulosModel.objects.all(), label="Producto")
    quantity = forms.FloatField(label="Cantidad a agregar")

    def __init__(self, *args, **kwargs):
        super(InventoryFormSeller, self).__init__(*args, **kwargs)
        
        # Obtener los IDs de los usuarios que cumplen las condiciones de usersPermission
        users_permission_ids = usersPermission.objects.filter(is_matrixSeller=True).values_list('user_id', flat=True)
        
        # Filtrar el queryset de User para incluir solo los usuarios cuyos IDs no están en users_permission_ids
        filtered_users = User.objects.filter(is_active=True, is_superuser=False, is_staff=False).exclude(id__in=users_permission_ids)
        
        # Actualizar el queryset del campo user
        self.fields['user'].queryset = filtered_users

class InventoryFormPV(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all().filter(is_active=True,is_superuser=False,is_staff=True), label="Usuario de Punto de Venta:")
    product = forms.ModelChoiceField(queryset=articulosModel.objects.all(), label="Producto")
    quantity = forms.FloatField(label="Cantidad a agregar:")


class inventarioPuntoVentaForm(forms.ModelForm):
    class Meta:
        model=pvInventory
        fields=['seller_id','product_id','qty']
    
    def __init__(self, *args, **kwargs):
        super(inventarioPuntoVentaForm, self).__init__(*args, **kwargs)
        # Limita las opciones de productos a aquellos que ya tienen inventario en la sucursal
        self.fields['product_id'].queryset = articulosModel.objects.all()  # Elimina el filtro inicial
        self.fields['seller_id'].queryset = User.objects.filter(is_active=True,is_superuser=False,is_staff=True)

class costosVendedoresForm(forms.ModelForm):
    class Meta:
        model=costosEmpresaVendedoresModel
        fields=['fecha','vendedor','salario','gasolina','otros']

    def __init__(self, *args, **kwargs):
        super(costosVendedoresForm, self).__init__(*args, **kwargs)
        # Limita las opciones de productos a aquellos que ya tienen inventario en la sucursal
        self.fields['vendedor'].queryset = User.objects.filter(is_active=True, is_superuser=False, is_staff=False)


class costosPuntosVentaForm(forms.ModelForm):
    class Meta:
        model=costosEmpresaPuntosVentaModel
        fields=['fecha','puntoVenta','salarios','productos','otros']

    def __init__(self, *args, **kwargs):
        super(costosPuntosVentaForm, self).__init__(*args, **kwargs)
        
        # Filtrar los puntos de venta por los usuarios que cumplen con los criterios
        self.fields['puntoVenta'].queryset = User.objects.filter(is_active=True, is_superuser=False, is_staff=True)

class RegistroInventarioFormSellers(forms.ModelForm):
    class Meta:
        model = sellerInventory
        fields = ['product_id', 'qty']  # Puedes ajustar los campos según tus necesidades



class inventarioCargaVendedorForm(forms.ModelForm):
    class Meta:
        model=sellerInventory
        fields=['product_id','qty']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Obtiene el usuario de los argumentos si está presente
        super(inventarioCargaVendedorForm, self).__init__(*args, **kwargs)  # Corregir el nombre de la clase aquí
        # Limita las opciones de productos a aquellos que ya tienen inventario en la sucursal
        self.fields['product_id'].queryset = articulosModel.objects.all()  # Elimina el filtro inicial
        
        if user is not None:
            self.fields['seller_id'].initial = user.id  # Asigna el id del usuario al campo seller_id
            self.fields['seller_id'].widget = forms.HiddenInput()  # Oculta el campo seller_id en el formulario





class inventarioCargaPVForm(forms.ModelForm):
    class Meta:
        model=pvInventory
        fields=['product_id','qty']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Obtiene el usuario de los argumentos si está presente
        super(inventarioCargaPVForm, self).__init__(*args, **kwargs)  # Corregir el nombre de la clase aquí
        # Limita las opciones de productos a aquellos que ya tienen inventario en la sucursal
        self.fields['product_id'].queryset = articulosModel.objects.all()  # Elimina el filtro inicial
        if user is not None:
            self.fields['seller_id'].initial = user.id  # Asigna el id del usuario al campo seller_id
            self.fields['seller_id'].widget = forms.HiddenInput()  # Oculta el campo seller_id en el formulario


class InventoryMatrix(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all().filter(is_active=True,is_superuser=False,is_staff=False), label="Usuario")
    product = forms.ModelChoiceField(queryset=articulosModel.objects.all(), label="Producto")
    quantity = forms.FloatField(label="Cantidad a agregar")

    def __init__(self, *args, **kwargs):
        super(InventoryMatrix, self).__init__(*args, **kwargs)
        
        # Obtener los IDs de los usuarios que cumplen las condiciones de usersPermission
        users_permission_ids = usersPermission.objects.filter(is_matrixSeller=False).values_list('user_id', flat=True)
        
        # Filtrar el queryset de User para incluir solo los usuarios cuyos IDs no están en users_permission_ids
        filtered_users = User.objects.filter(is_active=True, is_superuser=False, is_staff=False).exclude(id__in=users_permission_ids)
        
        # Actualizar el queryset del campo user
        self.fields['user'].queryset = filtered_users