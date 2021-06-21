from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver
from django.utils.text import slugify
from django.contrib import messages
from .pcloud_api import login, createFolder, renameFolder, deleteFolder, deleteFilesFromFolder
from .controllers import *
from .models import *

@receiver(pre_save, sender=Mengajar)
def preSaveMengajar(sender, instance, **kwargs):
    if instance.id:
        # set old mapel nameyy
        instance.old_mapel_id = instance.mapel_id

@receiver(post_save, sender=Mengajar)
def createPcloudFolder(sender, instance, created, **kwargs):
    # login to pcloud
    pc = loginPcloudWithUserId(instance.teacher_id)

    if created:
        # create new pcloud folder
        print(createFolder(pc, str(instance.mapel_id)))

    else:
        # rename pcloud folder
        print(renameFolder(pc, str(instance.old_mapel_id), str(instance.mapel_id)))
    

@receiver(post_delete, sender=Mengajar)
def deletePcloudFolder(sender, instance, **kwargs):
    # delete materi
    materi = Materi.objects.filter(teacher_id = instance.teacher_id, mapel_id = instance.mapel_id)
    materi.delete()

    # login to pcloud
    pc = loginPcloudWithUserId(instance.teacher_id)

    # delete folder
    print(deleteFolder(pc, str(instance.mapel_id)))

@receiver(pre_save, sender=Materi)
def preSaveMateri(sender, instance, **kwargs):
    try:
        # set old materi slug
        old_instance = Materi.objects.get(id = instance.id)
        instance.old_slug = old_instance.slug
    except:
        pass

@receiver(post_save, sender=Materi)
def createMateriFolder(sender, instance, created, **kwargs):
    # login to pcloud
    pc = loginPcloudWithUserId(instance.teacher_id)

    folder_path = str(instance.mapel_id) + '/' + instance.slug

    if created:
        # create new pcloud folder
        print(createFolder(pc, folder_path))

    else:
        # rename pcloud folder
        print(renameFolder(pc, str(instance.mapel_id) + '/' + instance.old_slug, folder_path))
        pass

@receiver(post_delete, sender=Materi)
def deleteMateriFolder(sender, instance, **kwargs):
    # login to pcloud
    pc = loginPcloudWithUserId(instance.teacher_id)

    # delete folder
    print(deleteFolder(pc, str(instance.mapel_id) + '/' + instance.slug))

@receiver(post_delete, sender=FileSiswa)
def deleteFile(sender, instance, **kwargs):
    # get materi
    materi = Materi.objects.get(id = instance.materi_id)

    # login to pcloud
    pc = loginPcloudWithUserId(materi.teacher_id)

    # delete file
    files = [instance.filename]
    deleteFilesFromFolder(pc, files, str(materi.mapel_id) + '/' + materi.slug)