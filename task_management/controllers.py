from django.contrib import messages
from .models import *
from .pcloud_api import login, usedSpace, uploadFiles, downloadFile

def getTeacherFromUserId(user_id):
    try:
        teacher = Teacher.objects.get(user_id = user_id)

        return teacher
    except Teacher.DoesNotExist:
        pass

def loginPcloudWithUserId(user_id):
    # get teacher with user id
    teacher = getTeacherFromUserId(user_id)

    # login to pcloud
    if teacher is not None:
        pc = login(teacher.pcloud_username, teacher.pcloud_password)

        return pc

def canUpload(user_id, upload_size):
    # login to pcloud
    pc = loginPcloudWithUserId(user_id)

    # check space
    [used, total] = usedSpace(pc)
    byte_to_mb = 1 / 1048576
    upload_size = round(upload_size * byte_to_mb, 1)

    if (upload_size + used) > total:
        return False
    else:
        return True

def getMapelNotTeached(user_id):
    # get teacher with user id
    teacher = getTeacherFromUserId(user_id)

    # get mapel not teached by teacher with logged in user id
    mengajar = Mengajar.objects.values_list("mapel_id").filter(teacher_id = teacher.id)
    mapels = Mapel.objects.all()

    for m in mengajar:
        mapels = mapels.exclude(id = m[0])

    return mapels

def getMapelTeached(user_id):
    # get teacher with user id
    teacher = getTeacherFromUserId(user_id)

    # get mapel teached by teacher with logged in user id
    mengajar = Mengajar.objects.filter(teacher_id = teacher.id)
    mapels = []
    for obj in mengajar:
        mapels.append(Mapel.objects.get(id = obj.mapel_id))

    return mapels

def getMateris(user_id, mapel_id):
    # get teacher with user id
    teacher = getTeacherFromUserId(user_id)

    # get mapel object
    mengajar = Mengajar.objects.get(teacher_id = teacher.id, mapel_id = mapel_id)

    # get materi from mapel id
    materis = Materi.objects.filter(teacher_id = teacher.id, mapel_id = mengajar.mapel_id)

    return materis

def uploadMateriFiles(user_id, folder_name, files, file_name):
    # login data
    pc = loginPcloudWithUserId(user_id)

    # upload files
    result_name = uploadFiles(pc, files, folder_name, file_name)

    return result_name

def unduhFile(filesiswa_id):
    # get file siswa
    file_siswa = FileSiswa.objects.get(id = filesiswa_id)
    filename = file_siswa.filename

    # get mapel id and slug
    materi = Materi.objects.get(id = file_siswa.materi_id)
    mapel_id = materi.mapel_id
    slug = materi.slug

    # get teacher
    teacher = Teacher.objects.get(id = materi.teacher_id)

    # login
    pc = loginPcloudWithUserId(teacher.user_id)

    # open file
    file_ = downloadFile(pc, str(mapel_id) + '/' + slug, filename)

    return [file_, filename]

def unduhArchive(user_id, mapel_id, slug):
    # login
    pc = loginPcloudWithUserId(user_id)

    filename = slug + '.zip'

    # open file
    file_ = downloadFile(pc, str(mapel_id), filename)

    return [file_, filename]