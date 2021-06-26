from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name = "index"),
    path("guru-login", views.guruLogin, name = "guru_login"),
    path("guru-logout", views.guruLogout, name = "guru_logout"),
    path("mapel", views.mapel, name = "mapel"),
    path("mapel/hapus/<int:mapel_id>", views.hapusMapel, name = "hapus_mapel"),
    path("mapel/<int:mapel_id>", views.materi, name = "materi"),
    path("mapel/<int:mapel_id>/edit/<slug:slug>", views.editMateri, name = "edit_materi"),
    path("mapel/<int:mapel_id>/hapus/<slug:slug>", views.hapusMateri, name = "hapus_materi"),
    path("mapel/<int:mapel_id>/<slug:slug>", views.materiFileSiswa, name = "materi_filesiswa"),
    path("mapel/<int:mapel_id>/<slug:slug>/export_nilai", views.exportNilaiSiswa, name = "export_nilaisiswa"),
    path("mapel/<int:mapel_id>/<slug:slug>/hapus/<int:filesiswa_id>", views.hapusFileSiswa, name = "hapus_filesiswa"),
    path("mapel/<int:mapel_id>/<slug:slug>/download/<int:filesiswa_id>", views.downloadFileSiswa, name = "download_filesiswa"),
    path("mapel/<int:mapel_id>/<slug:slug>/archive", views.archiveMateri, name = "archive_materi"),
    path("mapel/<int:mapel_id>/<slug:slug>/download_archive", views.downloadArchiveMateri, name = "download_archive"),
    path("mapel/<int:mapel_id>/<slug:slug>/hapus_archive", views.deleteArchiveMateri, name = "hapus_archive"),
    path("pengaturan", views.pengaturan, name = "pengaturan"),
    path("form-pengumpulan/<str:form_hash>", views.formPengumpulan, name = "form_pengumpulan"),
    path("form-success", views.terimaKasih, name = "form_terimakasih"),
    path("form-expired", views.expired, name = "form_expired"),
]