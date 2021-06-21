from django.shortcuts import redirect, render
from django.contrib.sites.shortcuts import get_current_site
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.html import escape
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as django_login
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from .pcloud_api import login as pcloud_login
from .controllers import *
from .forms import *
from .models import *
import pytz, io

from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template

# Create your views here.
@login_required(login_url='/guru-login')
def index(request):
    user_id = request.user.id
    
    # login to pcloud
    pc = loginPcloudWithUserId(user_id)

    # get used space and total space in pcloud
    [used, total] = usedSpace(pc)

    used_percentage = (used / total) * 100
    if used_percentage > 80:
        messages.error(request, "PERHATIAN: Penyimpanan hampir habis, segera hapus materi yang tidak terpakai untuk mengosongkan penyimpanan")

    # context to pass variable to template view
    context = {"used_space": used, "total_space": total}

    return TemplateResponse(request, 'index.html', context)

@login_required(login_url='/guru-login')
def mapel(request):
    user_id = request.user.id
    
    # get mapel teached by user id
    mapels = getMapelTeached(user_id)

    # get mapel not teached by user_id
    mapels_not_teached = [(mapel.id, mapel.name) for mapel in getMapelNotTeached(user_id)]

    if (request.method == "POST"):
        form = TambahMapelForm(request.POST)
        form.fields['mapel'].choices = mapels_not_teached

        if form.is_valid():
            mapel_id = int(form.cleaned_data['mapel'])
            m = Mengajar(mapel_id = mapel_id, teacher_id = getTeacherFromUserId(user_id).id)
            m.save()

            messages.success(request, "Mata pelajaran " + m.mapel.name + " berhasil ditambahkan")

            return redirect("mapel")
    
    else:
        form = TambahMapelForm()
        form.fields['mapel'].choices = mapels_not_teached

    # context to pass variable to template view
    context = {'mapels': mapels, 'form': form}

    return TemplateResponse(request, 'mapel.html', context)

@login_required(login_url='/guru-login')
def hapusMapel(request, mapel_id = 0):
    user_id = request.user.id

    teacher = getTeacherFromUserId(user_id)

    mengajar = Mengajar.objects.filter(teacher_id = teacher.id).filter(mapel_id = mapel_id)
    mapel_name = mengajar[0].mapel.name
    mengajar.delete()

    messages.success(request, "Mata pelajaran " + mapel_name + " berhasil dihapus")
    
    return redirect("mapel")

@login_required(login_url='/guru-login')
def materi(request, mapel_id = 0):
    user_id = request.user.id
    
    # get materis
    materis = getMateris(user_id, mapel_id)

    # get mapel name by mapel id
    mapel_name = Mapel.objects.get(id = mapel_id)

    if (request.method == "POST"):
        tambah_form = MateriForm(request.POST)

        if tambah_form.is_valid():
            materi = tambah_form.cleaned_data['name']
            deadline = tambah_form.cleaned_data['deadline']
            if Materi.objects.filter(mapel_id = mapel_id, teacher_id = getTeacherFromUserId(user_id).id, name = materi).exists():
                messages.error(request, "Materi dengan nama " + materi + " sudah ada")
            else:
                m = Materi(mapel_id = mapel_id, teacher_id = getTeacherFromUserId(user_id).id, name = materi, deadline = deadline)
                m.save()
                messages.success(request, "Materi " + materi + " berhasil ditambahkan")

            return redirect("materi", mapel_id = mapel_id)
    
    else:
        tambah_form = MateriForm()

    # context to pass variable to template view
    context = {'materis': materis, 'tambah_form': tambah_form, 'mapel_name': mapel_name}

    return TemplateResponse(request, 'materi.html', context)

@login_required(login_url='/guru-login')
def editMateri(request, mapel_id = 0, slug = ''):
    user_id = request.user.id
    
    # get materi
    materi = Materi.objects.get(mapel_id = mapel_id, slug = slug, teacher_id = getTeacherFromUserId(user_id))

    materi_name = materi.name

    if (request.method == "POST"):
        form = MateriForm(request.POST, instance = materi)

        if form.is_valid():
            form.save()

            return redirect("materi", mapel_id = mapel_id)
    
    else:
        form = MateriForm(instance = materi)

    # context to pass variable to template view
    context = {'form': form, 'materi_name': materi_name}

    return TemplateResponse(request, 'edit_materi.html', context)

@login_required(login_url='/guru-login')
def hapusMateri(request, mapel_id = 0, slug = ''):
    user_id = request.user.id

    teacher = getTeacherFromUserId(user_id)

    materi = Materi.objects.filter(teacher_id = teacher.id, mapel_id = mapel_id, slug = slug)
    materi_name = materi[0].name
    materi.delete()

    messages.success(request, "Materi " + materi_name + " berhasil dihapus")
    
    return redirect("materi", mapel_id = mapel_id)

@login_required(login_url='/guru-login')
def materiFileSiswa(request, mapel_id = 0, slug = ''):
    # get materi
    materi = Materi.objects.get(mapel_id = mapel_id, slug = slug)

    materi_name = materi.name
    form_link = 'http://' + get_current_site(request).domain + '/form-pengumpulan/' + materi.form_hash
    token = materi.token
    deadline = materi.deadline

    # get file siswa
    file_siswa = FileSiswa.objects.filter(materi_id = materi.id)

    if (request.method == "POST"):
        ids = request.POST.getlist("nilai_id")
        nilais = request.POST.getlist("nilai_field")

        for id_, nilai in zip(ids, nilais):
            updated_filesiswa = FileSiswa.objects.get(id = id_)
            updated_filesiswa.nilai = nilai
            updated_filesiswa.save()

        messages.success(request, "Nilai siswa berhasil dirubah")

        return redirect("materi_filesiswa", mapel_id = mapel_id, slug = slug)

    # context to pass variable to template view
    context = {'file_siswa': file_siswa, 'materi_name': materi_name, 'form_link': form_link, 'token': token, 'deadline': deadline, 'mapel_id': mapel_id, 'slug': slug}

    return TemplateResponse(request, 'materi_filesiswa.html', context)

@login_required(login_url='/guru-login')
def hapusFileSiswa(request, filesiswa_id = 0, mapel_id = 0, slug = ''):
    user_id = request.user.id

    teacher = getTeacherFromUserId(user_id)

    file_siswa = FileSiswa.objects.get(id = filesiswa_id)
    student_name = file_siswa.student_name
    file_siswa.delete()

    messages.success(request, "File siswa dengan nama " + student_name + " berhasil dihapus")
    
    return redirect("materi_filesiswa", mapel_id = mapel_id, slug = slug)

@login_required(login_url='/guru-login')
def downloadFileSiswa(request, filesiswa_id = 0, mapel_id = 0, slug = ''):
    # get file
    [file_, filename] = unduhFile(filesiswa_id)
    
    response = HttpResponse(file_, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
    
    return response

@login_required(login_url='/guru-login')
def exportNilaiSiswa(request, mapel_id = 0, slug = ''):
    # get materi
    materi = Materi.objects.get(mapel_id = mapel_id, slug = slug)

    # get file siswa
    file_siswa = FileSiswa.objects.filter(materi_id = materi.id)

    # pdf
    context = {'file_siswa': file_siswa, 'materi_name': materi.name}
    template = get_template("template_nilai.html")
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)

    # filename
    file_name = slug + '.pdf'

    # response
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    # response['Content-Disposition'] = 'attachment; filename=" ' + file_name + '"'

    return response

@login_required(login_url='/guru-login')
def pengaturan(request):
    user_id = request.user.id

    # get teacher
    teacher = Teacher.objects.get(user_id = user_id)

    if (request.method == "POST"):
        form = PcloudForm(request.POST, initial={'pcloud_username': teacher.pcloud_username, 'pcloud_password': teacher.pcloud_password})

        if form.is_valid():
            pcloud_username = form.cleaned_data['pcloud_username']
            pcloud_password = form.cleaned_data['pcloud_password']

            # login attempt to pcloud
            try:
                pc = pcloud_login(pcloud_username, pcloud_password)
                messages.success(request, "Akun pcloud berhasil diubah")
            except:
                messages.error(request, "Akun yang dirubah tidak bisa disambungkan ke pcloud")

                return redirect("pengaturan")

            teacher.pcloud_username = pcloud_username
            teacher.pcloud_password = pcloud_password
            teacher.save()

            return redirect("pengaturan")
    
    else:
        form = PcloudForm(initial={'pcloud_username': teacher.pcloud_username, 'pcloud_password': teacher.pcloud_password})

    # context to pass variable to template view
    context = {'form': form}

    return TemplateResponse(request, 'pengaturan.html', context)


def formPengumpulan(request, form_hash = ''):
    # get materi
    materi = Materi.objects.get(form_hash = form_hash)

    # user id
    teacher = Teacher.objects.get(id = materi.teacher_id)
    user_id = User.objects.get(id = teacher.user_id)

    # link expired
    if (timezone.now() > materi.deadline):
        return redirect("form_expired")

    if (request.method == "POST"):
        form = SiswaForm(request.POST, request.FILES)

        if form.is_valid():
            token = form.cleaned_data['token']
            if (token == materi.token):
                name = form.cleaned_data['student_name']
                keterangan = form.cleaned_data['keterangan']
                files = request.FILES.getlist('files')

                total_size = 0
                for file in files:
                    total_size += file.size
                    if total_size > 5242880:
                        messages.error(request, "Maksimal upload file 5 MB")
                        
                        return redirect('form_pengumpulan', form_hash = form_hash)

                folder_name = str(materi.mapel_id) + '/' + materi.slug
                file_name = slugify(name) + '.zip'

                try:
                    filesiswa_exists = FileSiswa.objects.get(filename = file_name, materi_id = materi.id)
                    messages.error(request, "Siswa atas nama " + name + " sudah mengumpulkan tugas")

                    return redirect("form_pengumpulan", form_hash = form_hash)
                except:
                    pass

                uploadMateriFiles(user_id, folder_name, files, file_name)
                
                filesiswa = FileSiswa(materi = materi, student_name = name, keterangan = keterangan, filename = file_name)
                filesiswa.save()

                return redirect("form_terimakasih")

            return redirect("form_pengumpulan", form_hash = form_hash)
    
    else:
        form = SiswaForm()

    # context to pass variable to template view
    context = {'form': form, 'materi_name': materi.name}

    return TemplateResponse(request, 'form_pengumpulan.html', context)

def terimaKasih(request):
    # context to pass variable to template view
    context = {}

    return render(request, 'form_terimakasih.html', context)

def expired(request):
    # context to pass variable to template view
    context = {}

    return render(request, 'form_expired.html', context)

def guruLogin(request):
    if request.user.is_authenticated:
        return redirect("index")

    if (request.method == "POST"):
        form = GuruLoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            next_url = request.POST.get('next')

            user = authenticate(username=username, password=password)

            if user is not None:
                django_login(request, user)

                if next_url:
                    return redirect(next_url)
                
                return redirect('index')
            else:
                messages.error(request, "Username/ password salah")

                return redirect('guru_login')
    
    else:
        form = GuruLoginForm()

    # context to pass variable to template view
    context = {'form': form}

    return TemplateResponse(request, 'guru_login.html', context)

@login_required(login_url='/guru-login')
def guruLogout(request):
    logout(request)

    return redirect('guru_login')