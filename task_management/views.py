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
from urllib.parse import quote
from .pcloud_api import login as pcloud_login
from .pcloud_api import createArchive, getArchiveProgress, folderSize
from .controllers import *
from .forms import *
from .models import *
import pytz, io, uuid

from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template

# Create your views here.
@login_required(login_url='/guru-login')
def index(request):
    user_id = request.user.id

    # get teacher
    teacher = Teacher.objects.get(user_id = user_id)

    # get mapel teached by user id
    mapels = getMapelTeached(user_id)[:3]

    # get materi
    materi = [m.id for m in Materi.objects.filter(teacher_id = teacher.id)]

    # get recent uploads
    recent_uploads = FileSiswa.objects.filter(materi_id__in = materi).order_by('-uploaded_at')[:5]

    # login to pcloud
    pc = loginPcloudWithUserId(user_id)

    # get used space and total space in pcloud
    [used, total] = usedSpace(pc)

    used_percentage = (used / total) * 100
    if used_percentage > 80:
        messages.error(request, "PERHATIAN: Penyimpanan hampir habis, segera hapus materi yang tidak terpakai untuk mengosongkan penyimpanan")

    # context to pass variable to template view
    context = {'used_percentage': int(used_percentage), 'used': used, 'total': total, 'teacher': teacher, 'mapels': mapels, 'recent_uploads': recent_uploads}

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
    user_id = request.user.id

    # get teacher
    teacher = Teacher.objects.get(user_id = user_id)

    # get materi
    materi = Materi.objects.get(teacher_id = teacher.id, mapel_id = mapel_id, slug = slug)

    # get mapel name
    mapel_name = Mapel.objects.get(id = mapel_id).name

    # parameter
    materi_name = materi.name
    form_link = 'http://' + get_current_site(request).domain + '/form-pengumpulan/' + materi.form_hash
    token = materi.token
    share_link = '*Form Pengumpulan ' + materi_name + '*%0a%0a' + quote(form_link) + '%0a%0a' + 'token: ' + token
    deadline = materi.deadline

    # is archiving?
    is_archive = False
    archiving = True
    try:
        archive = ArchiveMateri.objects.get(materi_id = materi.id)

        # done archiving?
        h = archive.progresshash
        pc = loginPcloudWithUserId(user_id)
        status = getArchiveProgress(pc, h)

        if status["result"] == 0:
            if status["bytes"] / status["totalbytes"] == 1:
                archiving = False
            else:
                archiving = True

            is_archive = True
    except:
        pass

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
    context = {'file_siswa': file_siswa, 'materi_name': materi_name, 'form_link': form_link, 'token': token, 'deadline': deadline, 'mapel_id': mapel_id, 'slug': slug, 'share_link': share_link, 'mapel_name': mapel_name, 'is_archive': is_archive, 'archiving': archiving}

    return TemplateResponse(request, 'materi_filesiswa.html', context)

@login_required(login_url='/guru-login')
def hapusFileSiswa(request, mapel_id = 0, filesiswa_id = 0, slug = ''):
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
def archiveMateri(request, mapel_id = 0, slug = ''):
    user_id = request.user.id

    # login to pcloud
    pc = loginPcloudWithUserId(user_id)

    # archive parameter
    folder_path = '/' + str(mapel_id) + '/' + slug
    dest = '/' + str(mapel_id) + '/'
    file_name = slug + '.zip'
    h = str(uuid.uuid4()).replace('-', '')

    # get teacher
    teacher = Teacher.objects.get(user_id = user_id)

    # get materi
    materi = Materi.objects.get(teacher_id = teacher.id, mapel_id = mapel_id, slug = slug)

    # check quota
    pc = loginPcloudWithUserId(user_id)
    [used, total] = usedSpace(pc)
    folder_size = folderSize(pc, folder_path)
    print("folder size + used:", folder_size + used)
    print("used:", used)
    print("total:", total)
    if folder_size + used > total:
        messages.error(request, "Penyimpanan tidak cukup, gagal membuat archive")

        return redirect("materi_filesiswa", mapel_id = mapel_id, slug = slug)

    # save to database
    m = ArchiveMateri(materi = materi, progresshash = h)
    m.save()

    # create archive to pcloud
    createArchive(pc, folder_path, dest, file_name, h)

    return redirect("materi_filesiswa", mapel_id = mapel_id, slug = slug)

@login_required(login_url='/guru-login')
def deleteArchiveMateri(request, mapel_id = 0, slug = ''):
    user_id = request.user.id

    # get teacher
    teacher = Teacher.objects.get(user_id = user_id)

    # get materi
    materi = Materi.objects.get(teacher_id = teacher.id, mapel_id = mapel_id, slug = slug)

    archive_materi = ArchiveMateri.objects.get(materi_id = materi.id)
    archive_materi.delete()

    messages.success(request, "Archive berhasil dihapus")

    return redirect("materi_filesiswa", mapel_id = mapel_id, slug = slug)

@login_required(login_url='/guru-login')
def downloadArchiveMateri(request, mapel_id = 0, slug = ''):
    # get file
    [file_, filename] = unduhArchive(request.user.id, mapel_id, slug)

    response = HttpResponse(file_, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

    return response

@login_required(login_url='/guru-login')
def exportNilaiSiswa(request, mapel_id = 0, slug = ''):
    user_id = request.user.id

    # get teacher
    teacher = Teacher.objects.get(user_id = user_id)

    # get materi
    materi = Materi.objects.get(teacher_id = teacher.id, mapel_id = mapel_id, slug = slug)

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

    # form expired response
    expired_response = redirect("form_expired")

    # form pengumpulan response
    pengumpulan_response = redirect("form_pengumpulan", form_hash = form_hash)

    # redirect to form_expired if time > deadline
    if (timezone.now() > materi.deadline):
        return expired_response

    if (request.method == "POST"):
        form = SiswaForm(request.POST, request.FILES)

        if form.is_valid():
            # don't submit if time > deadline
            if (timezone.now() > materi.deadline):
                return expired_response

            token = form.cleaned_data['token']

            # if inputted token is correct
            if (token == materi.token):
                name = form.cleaned_data['student_name']
                keterangan = form.cleaned_data['keterangan']
                files = request.FILES.getlist('files')
                uploaded_at = timezone.now()

                total_size = 0

                # get total file size, if > 5 MB return error messages
                for file in files:
                    total_size += file.size

                    if total_size > 5242880:
                        messages.error(request, "Maksimal upload file 5 MB")

                        return pengumpulan_response

                if not canUpload(user_id, total_size):
                    messages.error(request, "Penyimpanan sistem penuh, tidak bisa upload")

                    return pengumpulan_response

                folder_name = str(materi.mapel_id) + '/' + materi.slug
                file_name = slugify(name) + '.zip'

                # check siswa with name exists in database
                try:
                    filesiswa_exists = FileSiswa.objects.get(filename = file_name, materi_id = materi.id)
                    messages.error(request, "Siswa atas nama " + name + " sudah mengumpulkan tugas")

                    return pengumpulan_response
                except:
                    pass

                uploadMateriFiles(user_id, folder_name, files, file_name)

                filesiswa = FileSiswa(materi = materi, student_name = name, keterangan = keterangan, filename = file_name, uploaded_at = uploaded_at)
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
        logout(request)

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