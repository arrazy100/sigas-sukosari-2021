from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid, random, string

# Create your models here.
class Mapel(models.Model):
    name = models.CharField(max_length = 200)
    description = models.CharField(max_length = 200)

    def __str__(self):
        return self.name

class Teacher(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    pcloud_username = models.CharField(max_length = 200)
    pcloud_password = models.CharField(max_length = 200)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

class Mengajar(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete = models.CASCADE)
    mapel = models.ForeignKey(Mapel, on_delete = models.CASCADE)

    def __str__(self):
        full_name = self.teacher.user.first_name + ' ' + self.teacher.user.last_name
        return full_name + " mengajar " + self.mapel.name

class Materi(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete = models.CASCADE)
    mapel = models.ForeignKey(Mapel, on_delete = models.CASCADE)
    name = models.CharField(max_length = 200)
    slug = models.SlugField()
    form_hash = models.CharField(max_length = 200)
    token = models.CharField(max_length = 6)
    deadline = models.DateTimeField()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # slug
        self.slug = slugify(self.name)

        if not self.token:
            # random hash link
            unique_id = str(uuid.uuid4()).replace('-', '')
            self.form_hash = unique_id

            # random 6 digit token
            letters = string.ascii_lowercase
            rand = ''.join(random.choice(letters) for i in range(6))
            self.token = rand

        super(Materi, self).save(*args, **kwargs)

class FileSiswa(models.Model):
    materi = models.ForeignKey(Materi, on_delete = models.CASCADE)
    student_name = models.CharField(max_length = 200)
    keterangan = models.TextField()
    filename = models.CharField(max_length = 200)
    uploaded_at = models.DateTimeField(default = timezone.now())
    nilai = models.FloatField(default = 0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return self.student_name