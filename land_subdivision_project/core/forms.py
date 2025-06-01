# core/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Proyecto, Perfil  # Asegúrate de que estos modelos existan

# Formulario de registro de usuario
class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cd['password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

# Formulario para subir archivos de terreno
class SubirArchivoTerrenoForm(forms.Form):
    nombre = forms.CharField(max_length=255, label='Nombre del Terreno',
                           widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Terreno Principal'}))
    archivo_puntos = forms.FileField(label='Archivo de Puntos (ej: CSV, TXT)',
                                    widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.none(),
        label="Asignar a Proyecto",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['proyecto'].queryset = Proyecto.objects.filter(usuario=self.user)

# Formulario para editar perfil básico (User model)
class PerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'email': forms.EmailInput(attrs={'required': True}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True})
        }

# Formulario para configuración extendida (Perfil model)
class ConfiguracionForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['avatar', 'notificaciones', 'tema_oscuro']
        widgets = {
            'tema_oscuro': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificaciones': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'})
        }