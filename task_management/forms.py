from django import forms
from .models import Materi, FileSiswa

class TambahMapelForm(forms.Form):
    mapel = forms.ChoiceField(choices = (("0", "Pilih Mapel")))

class MateriForm(forms.ModelForm):
    deadline = forms.DateTimeField(input_formats=['%d/%m/%Y %H:%M'])

    class Meta:
        model = Materi
        fields = ['name', 'deadline']

class SiswaForm(forms.Form):
    token = forms.CharField()
    student_name = forms.CharField(max_length=200)
    keterangan = forms.CharField(widget=forms.Textarea(), required=False)
    files = forms.FileField(widget = forms.ClearableFileInput(attrs={'multiple': True}))

class GuruLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

class PcloudForm(forms.Form):
    pcloud_username = forms.CharField()
    pcloud_password = forms.CharField()
