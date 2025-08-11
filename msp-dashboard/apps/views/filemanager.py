from django.shortcuts import redirect, render, reverse
from django.http import HttpResponse, Http404
from django.db import connection
from apps.models import FileInfo
from apps.forms import *
from django.contrib import messages
from django.contrib import messages
import os
import uuid
import csv
from rbac.decorators import has_permission

#####
# Filemanager

# CONSTANTS
ACCUMULATED_SPACE_IN_GB = 64
KB_MULTIPLIER = 1024
MB_MULTIPLIER = KB_MULTIPLIER * 1024
GB_MULTIPLIER = MB_MULTIPLIER * 1024


def get_breadcrumbs(request):
    # Remove "/apps/filemanager" from the beginning of the path
    path = request.path.replace("/apps/filemanager", "", 1)
    path_components = [component for component in path.split("/") if component]

    # Start with the breadcrumb for Home
    breadcrumbs = [{"name": "Home", "url": "/apps/filemanager/"}]
    url = "/apps/filemanager/"

    # Include the tenant name in the URL but skip it in the breadcrumb names
    for i, component in enumerate(path_components):
        url += f"{component}/"
        if i == 0:  # Skip the tenant name (first component) in the breadcrumb names
            continue
        breadcrumbs.append({"name": component, "url": url})

    return breadcrumbs


def convert_csv_to_text(csv_file_path):
    with open(csv_file_path, "r") as file:
        reader = csv.reader(file)
        rows = list(reader)

    text = ""
    for row in rows:
        text += ",".join(row) + "\n"

    return text


def filter_files(file_list, extensions=[]):
    files = []

    for file_path in file_list:
        try:
            _, extension = os.path.splitext(file_path)
            if not extensions or extension.lower() in extensions:
                # Convert the file path to use forward slashes for URLs
                url_file_path = file_path.replace(os.sep, "/")
                file = {
                    "file": (
                        url_file_path.split("/media/")[1]  # Use "/" instead of os.sep
                        if "media" in url_file_path
                        else url_file_path
                    ),
                    "filename": os.path.basename(file_path),
                    "file_path": file_path,  # Keep the original file path as is
                }

                # If the file type is csv, convert csv file to txt and show on frontend
                if extension.lower() == ".csv":
                    csv_text = convert_csv_to_text(file_path)
                else:
                    csv_text = ""
                file["csv_text"] = csv_text
                # Append file in files
                files.append(file)

        except Exception as e:
            print(" > " + str(e))

    return files


def get_files_from_directory(directory_path, extensions=[]):
    files = []
    file_list = [
        os.path.join(directory_path, filename)
        for filename in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, filename))
    ]
    files = filter_files(file_list, extensions)
    return files


def get_files_from_directory_recursive(directory_path, extensions=[]):
    files = []
    file_list = []
    for root, dirs, filenames in os.walk(directory_path):
        for filename in filenames:
            file_list.append(os.path.join(root, filename))

    files = filter_files(file_list, extensions)
    return files


def generate_nested_directory(root_path, path):
    directories = []

    schema = connection.settings_dict["SCHEMA"]
    for name in os.listdir(path):
        inner_path = os.path.join(path, name)
        if os.path.isdir(inner_path):
            # Users can only view the filesystem of their own tenant
            if (schema not in path) and (name != schema):
                continue

            unique_id = str(uuid.uuid4())
            nested_path = os.path.join(path, name)
            nested_directories = generate_nested_directory(root_path, nested_path)

            # Folder Size
            folder_size: int = get_path_size(inner_path)
            if folder_size < KB_MULTIPLIER:
                folder_size = ""
            else:
                folder_size: str = format_size(folder_size)

            directories.append(
                {
                    "id": unique_id,
                    "name": name,
                    "path": os.path.relpath(nested_path, root_path),
                    "directories": nested_directories,
                    "space": folder_size,
                }
            )
    return directories


def apps_filemanager_overview(request):
    return render(request, "apps/filemanager/overview.html")


def get_path_size(source, total_size=0):
    total_size_in = total_size
    for item in os.listdir(source):
        itempath = os.path.join(source, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += get_path_size(itempath, total_size)
    return total_size - total_size_in


def count_files_in_directory(path):
    file_count = 0
    for root, dirs, files in os.walk(path):
        file_count += len(files)
    return file_count


def get_specific_extension_files(all_files):
    # Define the extensions for each category
    image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"]
    video_extensions = [".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"]
    document_extensions = [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".csv"]
    # Define a set of known extensions to categorize "others" later
    known_extensions = set(image_extensions + video_extensions + document_extensions)

    # Initialize empty lists to hold files of each type
    images = []
    videos = []
    documents = []
    others = []

    # Loop through all_files and categorize them based on extensions
    for file in all_files:
        _, extension = os.path.splitext(file["filename"])

        if extension.lower() in image_extensions:
            images.append(file)
        elif extension.lower() in video_extensions:
            videos.append(file)
        elif extension.lower() in document_extensions:
            documents.append(file)
        else:
            # Any file that doesn't match known extensions goes into "others"
            others.append(file)

    return images, videos, documents, others


def get_file_size(path):
    total_size = 0

    # Check if the path is a file
    if os.path.isfile(path):
        total_size = os.path.getsize(path)

    return total_size


def get_files_size(files):
    total_space = 0
    for file in files:
        file_path = file.get("file_path")
        file_size = get_file_size(file_path)
        total_space += file_size

    return total_space


def format_size(size_in_bytes: int) -> str:

    if size_in_bytes >= GB_MULTIPLIER:
        size_in_gb = size_in_bytes / GB_MULTIPLIER
        return (
            f"{size_in_gb:.2f} GB"
            if size_in_gb >= 1
            else f"{size_in_bytes / MB_MULTIPLIER:.2f} MB"
        )
    elif size_in_bytes >= MB_MULTIPLIER:
        size_in_mb = size_in_bytes / MB_MULTIPLIER
        return (
            f"{size_in_mb:.2f} MB"
            if size_in_mb >= 1
            else f"{size_in_bytes / KB_MULTIPLIER:.2f} KB"
        )
    elif size_in_bytes >= KB_MULTIPLIER:
        size_in_kb = size_in_bytes / KB_MULTIPLIER
        return f"{size_in_kb:.2f} KB"
    else:
        return f"{size_in_bytes} Bytes"


@has_permission("apps.view_fileinfo")
def apps_filemanager(request, directory=""):
    media_path = os.path.join(settings.MEDIA_ROOT)
    if not directory:
        directory = connection.settings_dict["SCHEMA"]
    directory = os.path.join(media_path, directory)

    schema = connection.settings_dict["SCHEMA"]
    directories = generate_nested_directory(
        media_path, directory
    )  # current path from media_path to directory
    selected_directory = directory

    accumulated_space = ACCUMULATED_SPACE_IN_GB * GB_MULTIPLIER

    used_space = get_path_size(directory)
    space_left: int = accumulated_space - used_space
    percent_left = (space_left / accumulated_space) * 100

    all_files, files, subdir_files_count = [], [], []
    selected_directory_path = os.path.join(media_path, selected_directory)

    if os.path.isdir(selected_directory_path):
        files = get_files_from_directory(selected_directory_path)
        all_files = get_files_from_directory_recursive(selected_directory_path)

    for directory in directories:
        subdir = os.path.join(media_path, directory.get("path"))
        subdir_files_count.append(count_files_in_directory(subdir))

    images, videos, documents, others = get_specific_extension_files(all_files)

    images_space = format_size(get_files_size(images))
    videos_space = format_size(get_files_size(videos))
    documents_space = format_size(get_files_size(documents))
    others_space = format_size(get_files_size(others))

    breadcrumbs = get_breadcrumbs(request)
    last_directory = breadcrumbs[-1]

    context = {
        "directories": directories,
        "files": files,
        "all_files": all_files,
        "subdir_files_count": subdir_files_count,
        "selected_directory": selected_directory,
        "segment": "file_manager",
        "breadcrumbs": breadcrumbs,
        "last_directory": last_directory,
        "company_name": schema,
        "storage_overview": {
            "used_space": format_size(used_space),
            "space_left": format_size(space_left),
            "percent_left": round(percent_left),
            "images": {"count": len(images), "space": images_space},
            "videos": {"count": len(videos), "space": videos_space},
            "documents": {"count": len(documents), "space": documents_space},
            "others": {"count": len(others), "space": others_space},
        },
        "": "",
    }

    return render(request, "apps/filemanager/overview.html", context)


def apps_filemanager_create_usrdir(request, pk):

    try:
        os.mkdir(os.path.join(settings.MEDIA_ROOT, f"public/{request.user}_{pk}"))
    except FileExistsError:
        messages.error(request, "User Directory Already")

    return redirect(reverse("apps:filemanager.overview"))


def apps_filemanager_upload_file(request):
    media_path = os.path.join(settings.MEDIA_ROOT)
    selected_directory = request.POST.get("directory", "")
    selected_directory_path = os.path.join(media_path, selected_directory)
    if request.method == "POST":
        file = request.FILES.get("file")
        file_path = os.path.join(selected_directory_path, file.name)
        with open(file_path, "wb") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

    return redirect(request.META.get("HTTP_REFERER"))


def apps_filemanager_delete_file(request, file_path):
    path = file_path.replace("%slash%", "/")
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, path)
    os.remove(absolute_file_path)
    return redirect(request.META.get("HTTP_REFERER"))


def apps_filemanager_delete_directory(request, directory=""):
    media_path = os.path.join(settings.MEDIA_ROOT)
    directories = generate_nested_directory(media_path, media_path)
    selected_directory = directory
    # shutil.rmtree()
    for directory in directories:
        print("Directory deleted", selected_directory)

    print("Directory deleted", selected_directory)
    render(request, "apps/filemanager/overview.html")


def apps_filemanager_download_file(request, file_path):
    absolute_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if os.path.exists(absolute_file_path):
        with open(absolute_file_path, "rb") as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response["Content-Disposition"] = "inline; filename=" + os.path.basename(
                absolute_file_path
            )
            return response
    raise Http404


def apps_filemanager_save_info(request, file_path):
    path = file_path.replace("%slash%", "/")
    if request.method == "POST":
        FileInfo.objects.update_or_create(
            path=path, defaults={"info": request.POST.get("info")}
        )

    return redirect(request.META.get("HTTP_REFERER"))
