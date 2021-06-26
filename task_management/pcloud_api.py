from pcloud import PyCloud
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import math, os

def login(username, password):
    pc = PyCloud(username, password)

    return pc

def usedSpace(login_data):
    user_info = login_data.userinfo()
    byte_to_mb = 1 / 1048576

    used_space = round(user_info["usedquota"] * byte_to_mb, 1)
    total_space = math.ceil(user_info["quota"] * byte_to_mb)

    return [used_space, total_space]

def createFolder(login_data, folder_name):
    new_folder = login_data.createfolder(path = '/' + folder_name)

    if (new_folder["result"] == 0):
        return "Folder " + folder_name + " berhasil dibuat"
    else:
        return new_folder["error"]

def renameFolder(login_data, old_name, new_name):
    rename_folder = login_data.renamefolder(path = '/' + old_name, topath = '/' + new_name)

    if (rename_folder["result"] == 0):
        return "Folder " + old_name + " berhasil diubah menjadi " + new_name
    else:
        return rename_folder["error"]

def deleteFolder(login_data, folder_name):
    # delete all files in folder
    [files, status] = listFileFromFolder(login_data, folder_name)
    deleteFilesFromFolder(login_data, files, folder_name)

    list_folder = login_data.listfolder(path = '/' + folder_name)
    if list_folder["result"] == 0:
        for folder in list_folder["metadata"]["contents"]:
            if (folder["isfolder"] == True):
                [f, s] = listFileFromFolder(login_data, folder["path"])
                deleteFilesFromFolder(login_data, f, folder["path"])
                login_data.deletefolder(path = folder["path"])

    # delete folder
    delete_folder = login_data.deletefolder(path = '/' + folder_name)

    if (delete_folder["result"] == 0):
        return "Folder " + folder_name + " berhasil dihapus"
    else:
        return delete_folder["error"]

def listFolder(login_data):
    pc_folders = login_data.listfolder(folderid = 0)
    folders = []

    for folder in pc_folders["metadata"]["contents"]:
        folders.append(folder["name"])

    return folders

def folderSize(login_data, path):
    listfolder = login_data.listfolder(path=path)
    total_size = 0
    byte_to_mb = 1 / 1048576

    if listfolder["result"] == 0:
        for file in listfolder["metadata"]["contents"]:
            total_size += round(file["size"] * byte_to_mb, 1)

    return total_size

def listFileFromFolder(login_data, folder_name):
    folder = login_data.listfolder(path = '/' + folder_name)
    files = []

    if folder["result"] == 0:
        for file in folder["metadata"]["contents"]:
            files.append(file["name"])

        return [files, True]
    else:
        return [files, False]

def downloadFile(login_data, folder_name, file_name):
    file_size = login_data.stat(path = '/' + folder_name + '/' + file_name)["metadata"]["size"]

    login_data.file_open(path = '/' + folder_name + '/' + file_name, flags = int("0x0040", 16))
    binary = login_data.file_read(fd = 1, count = file_size)
    login_data.file_close(fd = 1)

    return binary

def uploadFile(login_data, files, folder_name):
    upload_status = login_data.uploadfile(files = files, path = '/' + folder_name)

    return upload_status

def deleteFilesFromFolder(login_data, files, folder_name):
    for file in files:
        delete_status = login_data.deletefile(path = "/" + folder_name + "/" + file)

        if delete_status["result"] == 0:
            print("File " + file + " berhasil dihapus")

def downloadFolder(login_data, folder_name):
    [list_file, status] = listFileFromFolder(login_data, folder_name)

    # batalkan fungsi jika ada error
    if (not status):
        print(list_file["error"])
        return

    i = 1
    for file in list_file:
        file_name = file["name"]
        file_size = file["size"]
        path = "/" + folder_name + "/" + file_name
        new_file = os.path.join(folder_name, file_name)

        login_data.file_open(path = path, flags = int("0x0040", 16))
        binary = login_data.file_read(fd = i, count = file_size)

        try:
            os.makedirs(folder_name)
        except:
            pass

        with open(new_file, "wb") as f:
            f.write(binary)
            f.close()

        login_data.file_close(fd = i)

        i += 1

def uploadFiles(login_data, files, folder_name, zip_name):
    in_memory = BytesIO()
    zf = ZipFile(in_memory, mode="w", compression=ZIP_DEFLATED)

    i = 1
    for file in files:
        file_name = file.name
        file_size = file.size

        binary = file.read()

        zf.writestr(file_name, binary)

        i += 1

    path = "/" + folder_name + "/" + zip_name

    zf.close()
    in_memory.seek(0)
    data = in_memory.read()

    login_data.file_open(path = path, flags = int("0x0040", 16))
    status = login_data.file_write(fd = 1, data = data)
    login_data.file_close(fd = 1)

    if (status["result"] == 0):
        print(zip_name + " berhasil diupload ke " + folder_name)

def createArchive(login_data, path, topath, filename, progresshash):
    stat = login_data.stat(path=path)
    folderid = stat['metadata']['folderid']
    status = login_data.savezip(folderid=folderid, topath=topath + filename, progresshash=progresshash)

    return status

def getArchiveProgress(login_data, progresshash):
    status = login_data.savezipprogress(progresshash=progresshash)

    return status

# pc = login('devgame1100@gmail.com', 'Devsukosari0308')
# print(deleteFolder(pc, "1"))