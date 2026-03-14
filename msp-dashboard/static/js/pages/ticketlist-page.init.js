(function () {
    const MAX_CREATE_FILES = 10;
    const MAX_CREATE_FILE_SIZE_BYTES = 25 * 1024 * 1024;
    const MAX_UPLOAD_FILE_SIZE_BYTES = 250 * 1024 * 1024;
    const CREATE_ALLOWED_EXTENSIONS = [
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".csv",
        ".xls",
        ".xlsx",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
    ];

    let selectedCreateFiles = [];
    let createEditor = null;
    let activeTicketModalTab = "create";
    let isCreateSubmitting = false;
    let isLoadSubmitting = false;

    document.addEventListener("DOMContentLoaded", function () {
        setupBulkDelete();
        setupTicketSearch();
        setupTicketModalTabs();
        setupCreateTicketForm();
        setupLoadTicketForm();
    });

    function getCsrfToken() {
        const tokenInput = document.querySelector("[name=csrfmiddlewaretoken]");
        return tokenInput ? tokenInput.value : "";
    }

    function parseResponseBody(response) {
        return response.text().then(function (text) {
            if (!text) {
                return {};
            }

            try {
                return JSON.parse(text);
            } catch (error) {
                return { success: false, message: text };
            }
        });
    }

    function formatFileSize(bytes) {
        if (!bytes) {
            return "0 Bytes";
        }

        const sizes = ["Bytes", "KB", "MB", "GB"];
        const index = Math.min(
            Math.floor(Math.log(bytes) / Math.log(1024)),
            sizes.length - 1
        );
        const value = bytes / Math.pow(1024, index);
        return value.toFixed(value >= 10 || index === 0 ? 0 : 1) + " " + sizes[index];
    }

    function normalizeSearchText(value) {
        return String(value || "")
            .toLowerCase()
            .replace(/\s+/g, " ")
            .trim();
    }

    function parseTicketDateRange(value) {
        const text = String(value || "").trim();
        if (!text) {
            return null;
        }

        const parts = text.split(" to ");
        const start = new Date(parts[0]);
        const end = new Date(parts[parts.length - 1] || parts[0]);
        if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
            return null;
        }

        start.setHours(0, 0, 0, 0);
        end.setHours(23, 59, 59, 999);
        return { start: start, end: end };
    }

    function showTabForSelector(selector) {
        const trigger = document.querySelector('[href="' + selector + '"]');
        if (!trigger) {
            return;
        }

        if (window.bootstrap && window.bootstrap.Tab) {
            window.bootstrap.Tab.getOrCreateInstance(trigger).show();
            return;
        }

        trigger.click();
    }

    function setupBulkDelete() {
        const removeActionsButton = document.getElementById("remove-actions");
        if (!removeActionsButton) {
            return;
        }

        const checkAllInputs = Array.from(
            document.querySelectorAll("[data-check-all-tickets]")
        );
        const rowCheckboxes = Array.from(
            document.querySelectorAll(".ticket-row-checkbox")
        );

        function syncRowState(checkbox) {
            const row = checkbox.closest("tr");
            if (row) {
                row.classList.toggle("table-active", checkbox.checked);
            }
        }

        function syncCheckAllStates() {
            checkAllInputs.forEach(function (checkAllInput) {
                const container = checkAllInput.closest("[data-ticket-table]");
                if (!container) {
                    return;
                }

                const checkboxes = Array.from(
                    container.querySelectorAll(".ticket-row-checkbox:not(:disabled)")
                );
                const checkedCount = checkboxes.filter(function (checkbox) {
                    return checkbox.checked;
                }).length;

                checkAllInput.checked =
                    checkboxes.length > 0 && checkedCount === checkboxes.length;
                checkAllInput.indeterminate =
                    checkedCount > 0 && checkedCount < checkboxes.length;
            });
        }

        function updateBulkDeleteButton() {
            const selectedCount = rowCheckboxes.filter(function (checkbox) {
                return checkbox.checked;
            }).length;

            removeActionsButton.disabled = selectedCount === 0;
            removeActionsButton.classList.toggle("disabled", selectedCount === 0);
            removeActionsButton.style.display = "";
            removeActionsButton.setAttribute(
                "aria-disabled",
                selectedCount === 0 ? "true" : "false"
            );

            syncCheckAllStates();
        }

        checkAllInputs.forEach(function (checkAllInput) {
            checkAllInput.addEventListener("change", function () {
                const container = checkAllInput.closest("[data-ticket-table]");
                if (!container) {
                    return;
                }

                const checkboxes = container.querySelectorAll(
                    ".ticket-row-checkbox:not(:disabled)"
                );
                checkboxes.forEach(function (checkbox) {
                    checkbox.checked = checkAllInput.checked;
                    syncRowState(checkbox);
                });
                updateBulkDeleteButton();
            });
        });

        rowCheckboxes.forEach(function (checkbox) {
            checkbox.addEventListener("change", function () {
                syncRowState(checkbox);
                updateBulkDeleteButton();
            });
            syncRowState(checkbox);
        });

        updateBulkDeleteButton();

        window.deleteMultiple = function () {
            const selectedIds = rowCheckboxes
                .filter(function (checkbox) {
                    return checkbox.checked;
                })
                .map(function (checkbox) {
                    return checkbox.dataset.ticketId;
                })
                .filter(Boolean);

            if (!selectedIds.length) {
                Swal.fire({
                    title: "Select tickets",
                    text: "Choose at least one ticket before trying to delete.",
                    icon: "info",
                    confirmButtonClass: "btn btn-info",
                    buttonsStyling: false,
                });
                return;
            }

            Swal.fire({
                title: "Are you sure?",
                text: "These tickets will be permanently deleted.",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Yes, delete them!",
                confirmButtonClass: "btn btn-primary w-xs me-2 mt-2",
                cancelButtonClass: "btn btn-danger w-xs mt-2",
                buttonsStyling: false,
                showCloseButton: true,
            }).then(function (result) {
                if (!result.isConfirmed) {
                    return;
                }

                removeActionsButton.disabled = true;

                fetch(ticketBulkDeleteURL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({ ticket_ids: selectedIds }),
                })
                    .then(function (response) {
                        return parseResponseBody(response).then(function (body) {
                            return { ok: response.ok, body: body };
                        });
                    })
                    .then(function (resultBody) {
                        const body = resultBody.body || {};
                        if (!resultBody.ok || !body.success) {
                            throw new Error(
                                body.message ||
                                    "The selected tickets could not be deleted."
                            );
                        }

                        return Swal.fire({
                            title: "Deleted!",
                            text: body.message,
                            icon: "success",
                            confirmButtonClass: "btn btn-info w-xs mt-2",
                            buttonsStyling: false,
                        }).then(function () {
                            window.location.reload();
                        });
                    })
                    .catch(function (error) {
                        removeActionsButton.disabled = false;
                        Swal.fire({
                            title: "Delete failed",
                            text: error.message,
                            icon: "error",
                            confirmButtonClass: "btn btn-danger w-xs mt-2",
                            buttonsStyling: false,
                        });
                    });
            });
        };
    }

    function setupTicketSearch() {
        const searchInput = document.querySelector(
            "#ticketsList .search-box input"
        );
        const statusSelect = document.getElementById("idStatus");
        const dateRangeInput = document.getElementById("demo-datepicker");
        const noResult =
            document.querySelector("#ticketsList .noresult") ||
            document.querySelector(".noresult");
        const noResultTitle = document.getElementById("ticket-search-empty-title");
        const noResultMessage = document.getElementById(
            "ticket-search-empty-message"
        );
        const rows = Array.from(document.querySelectorAll("[data-ticket-row]"));
        const placeholderRows = Array.from(
            document.querySelectorAll(".no-tickets-placeholder")
        );
        const paginationSections = Array.from(
            document.querySelectorAll("#open-tickets-section, #closed-tickets-section")
        );

        if (!searchInput || !rows.length) {
            window.SearchData = function () {};
            return;
        }

        function getRowPaneKey(row) {
            const pane = row.closest("[data-ticket-table]");
            return pane ? pane.dataset.ticketTable : "";
        }

        function updateNoResult(query, hasFilters, totalMatches) {
            if (!noResult) {
                return;
            }

            if (!hasFilters || totalMatches > 0) {
                noResult.style.display = "none";
                return;
            }

            const rawQuery = String(query || "").trim();
            if (noResultTitle) {
                noResultTitle.textContent = (rawQuery || "Search") + " Not found";
            }
            if (noResultMessage) {
                noResultMessage.textContent =
                    "No tickets matched that search, technician, name, or description.";
            }
            noResult.style.display = "block";
        }

        function applyTicketSearch() {
            const query = normalizeSearchText(searchInput.value);
            const selectedStatus = normalizeSearchText(
                statusSelect ? statusSelect.value : ""
            );
            const selectedRange = parseTicketDateRange(
                dateRangeInput ? dateRangeInput.value : ""
            );
            const hasFilters = Boolean(
                query ||
                    (selectedStatus && selectedStatus !== "all") ||
                    (dateRangeInput && String(dateRangeInput.value || "").trim())
            );
            const matchCounts = { open: 0, closed: 0 };
            let totalMatches = 0;

            rows.forEach(function (row) {
                const searchText = normalizeSearchText(row.dataset.searchText);
                const rowStatus = normalizeSearchText(row.dataset.ticketStatus).replace(
                    /\s+/g,
                    ""
                );
                const selectedStatusKey = selectedStatus.replace(/\s+/g, "");
                const rowDate = row.dataset.createDate
                    ? new Date(row.dataset.createDate)
                    : null;

                let matches = !query || searchText.includes(query);

                if (matches && selectedStatusKey && selectedStatusKey !== "all") {
                    matches = rowStatus === selectedStatusKey;
                }

                if (matches && selectedRange && rowDate) {
                    matches =
                        rowDate >= selectedRange.start &&
                        rowDate <= selectedRange.end;
                }

                row.style.display = matches ? "" : "none";

                if (matches) {
                    totalMatches += 1;
                    const paneKey = getRowPaneKey(row);
                    if (paneKey && Object.prototype.hasOwnProperty.call(matchCounts, paneKey)) {
                        matchCounts[paneKey] += 1;
                    }
                }
            });

            placeholderRows.forEach(function (row) {
                row.style.display = hasFilters ? "none" : "";
            });

            paginationSections.forEach(function (section) {
                section.style.display = hasFilters ? "none" : "";
            });

            if (hasFilters && totalMatches > 0) {
                const activePane = document.querySelector(".tab-pane.show.active");
                const activeTable = activePane
                    ? activePane.querySelector("[data-ticket-table]")
                    : null;
                const activePaneKey = activeTable ? activeTable.dataset.ticketTable : "";
                if (activePaneKey && matchCounts[activePaneKey] === 0) {
                    if (matchCounts.open > 0) {
                        showTabForSelector("#open-tickets");
                    } else if (matchCounts.closed > 0) {
                        showTabForSelector("#closed-tickets");
                    }
                }
            }

            updateNoResult(searchInput.value, hasFilters, totalMatches);
        }

        searchInput.addEventListener("input", applyTicketSearch);

        if (statusSelect) {
            statusSelect.addEventListener("change", applyTicketSearch);
        }

        if (dateRangeInput) {
            dateRangeInput.addEventListener("change", applyTicketSearch);
            dateRangeInput.addEventListener("input", applyTicketSearch);
        }

        window.SearchData = applyTicketSearch;
    }

    function setupTicketModalTabs() {
        const modal = document.getElementById("showModal");
        if (!modal) {
            return;
        }

        const title = document.getElementById("exampleModalLabel");
        const tabTriggers = Array.from(
            document.querySelectorAll("[data-ticket-tab-trigger]")
        );
        const openButtons = Array.from(
            document.querySelectorAll("[data-ticket-modal-tab]")
        );

        function setModalTitle(tabName) {
            if (!title) {
                return;
            }

            if (tabName === "load") {
                title.textContent = "Load Tickets from Excel";
                return;
            }

            title.textContent = "Create Ticket";
        }

        function activateTab(tabName) {
            const trigger = document.querySelector(
                '[data-ticket-tab-trigger="' + tabName + '"]'
            );
            if (trigger) {
                bootstrap.Tab.getOrCreateInstance(trigger).show();
            }
            activeTicketModalTab = tabName;
            setModalTitle(tabName);
        }

        openButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                activeTicketModalTab = button.dataset.ticketModalTab || "create";
            });
        });

        modal.addEventListener("show.bs.modal", function (event) {
            const source = event.relatedTarget;
            activeTicketModalTab =
                (source && source.dataset.ticketModalTab) || "create";
        });

        modal.addEventListener("shown.bs.modal", function () {
            activateTab(activeTicketModalTab);
        });

        tabTriggers.forEach(function (trigger) {
            trigger.addEventListener("shown.bs.tab", function () {
                activeTicketModalTab = trigger.dataset.ticketTabTrigger || "create";
                setModalTitle(activeTicketModalTab);
            });
        });
    }

    function setupCreateTicketForm() {
        const form = document.getElementById("createTicketDropzone");
        if (!form) {
            return;
        }

        const fileInput = document.getElementById("ticket-files-input");
        const dropzone = document.getElementById("ticket-file-dropzone");
        const previewList = document.getElementById("ticket-file-preview-list");
        const previewEmpty = document.getElementById("ticket-file-preview-empty");
        const resultContainer = document.getElementById("createTicketResult");
        const submitButton = document.getElementById("add-btn");
        const modal = document.getElementById("showModal");
        const descriptionField = document.getElementById("ckeditor-classic");

        if (window.ClassicEditor && descriptionField) {
            ClassicEditor.create(descriptionField)
                .then(function (editor) {
                    createEditor = editor;
                    editor.ui.view.editable.element.style.height = "200px";
                })
                .catch(function (error) {
                    console.error(error);
                });
        }

        function showCreateResult(message, type) {
            if (!resultContainer) {
                return;
            }

            resultContainer.className = "alert alert-" + type + " mx-3 mb-0";
            resultContainer.innerHTML = message;
            resultContainer.classList.remove("d-none");
        }

        function hideCreateResult() {
            if (!resultContainer) {
                return;
            }

            resultContainer.classList.add("d-none");
            resultContainer.innerHTML = "";
        }

        function renderCreateFilePreview() {
            if (!previewList || !previewEmpty) {
                return;
            }

            previewList.innerHTML = "";
            previewEmpty.style.display = selectedCreateFiles.length ? "none" : "block";

            selectedCreateFiles.forEach(function (file, index) {
                const item = document.createElement("div");
                item.className = "border rounded-3 p-2";
                item.innerHTML =
                    '<div class="d-flex align-items-center">' +
                    '<div class="flex-shrink-0 me-3">' +
                    '<div class="avatar-sm bg-light rounded">' +
                    '<div class="avatar-title text-primary bg-soft-primary rounded">' +
                    '<i class="ri-file-fill"></i>' +
                    "</div>" +
                    "</div>" +
                    "</div>" +
                    '<div class="flex-grow-1 overflow-hidden">' +
                    '<h6 class="mb-1 text-truncate">' +
                    file.name +
                    "</h6>" +
                    '<p class="mb-0 text-muted small">' +
                    formatFileSize(file.size) +
                    "</p>" +
                    "</div>" +
                    '<div class="flex-shrink-0 ms-3">' +
                    '<button type="button" class="btn btn-sm btn-link text-danger p-0" data-create-file-remove="' +
                    index +
                    '">' +
                    '<i class="ri-close-line fs-5"></i>' +
                    "</button>" +
                    "</div>" +
                    "</div>";
                previewList.appendChild(item);
            });

            previewList
                .querySelectorAll("[data-create-file-remove]")
                .forEach(function (button) {
                    button.addEventListener("click", function () {
                        const index = Number(button.dataset.createFileRemove);
                        selectedCreateFiles.splice(index, 1);
                        renderCreateFilePreview();
                    });
                });
        }

        function validateCreateFile(file) {
            const extension = "." + file.name.split(".").pop().toLowerCase();
            if (!CREATE_ALLOWED_EXTENSIONS.includes(extension)) {
                return (
                    "'" +
                    file.name +
                    "' is not a supported file type for ticket attachments."
                );
            }

            if (file.size > MAX_CREATE_FILE_SIZE_BYTES) {
                return (
                    "'" +
                    file.name +
                    "' is larger than 25 MB. Please upload a smaller file."
                );
            }

            return "";
        }

        function addCreateFiles(fileList) {
            const incomingFiles = Array.from(fileList || []);
            if (!incomingFiles.length) {
                return;
            }

            const errors = [];
            incomingFiles.forEach(function (file) {
                const validationError = validateCreateFile(file);
                if (validationError) {
                    errors.push(validationError);
                    return;
                }

                const alreadyAdded = selectedCreateFiles.some(function (existingFile) {
                    return (
                        existingFile.name === file.name &&
                        existingFile.size === file.size &&
                        existingFile.lastModified === file.lastModified
                    );
                });

                if (!alreadyAdded) {
                    selectedCreateFiles.push(file);
                }
            });

            if (selectedCreateFiles.length > MAX_CREATE_FILES) {
                selectedCreateFiles = selectedCreateFiles.slice(0, MAX_CREATE_FILES);
                errors.push("Only the first 10 files were kept for this ticket.");
            }

            renderCreateFilePreview();

            if (errors.length) {
                showCreateResult(errors.join("<br>"), "warning");
            } else {
                hideCreateResult();
            }
        }

        function resetCreateForm() {
            form.reset();
            selectedCreateFiles = [];
            renderCreateFilePreview();
            hideCreateResult();
            form.classList.remove("was-validated");
            if (fileInput) {
                fileInput.value = "";
            }
            if (createEditor) {
                createEditor.setData("");
            }
        }

        if (dropzone && fileInput) {
            ["dragenter", "dragover", "dragleave", "drop"].forEach(function (eventName) {
                dropzone.addEventListener(eventName, function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                });
            });

            ["dragenter", "dragover"].forEach(function (eventName) {
                dropzone.addEventListener(eventName, function () {
                    dropzone.classList.add("border-primary");
                    dropzone.classList.add("bg-soft-primary");
                });
            });

            ["dragleave", "drop"].forEach(function (eventName) {
                dropzone.addEventListener(eventName, function () {
                    dropzone.classList.remove("border-primary");
                    dropzone.classList.remove("bg-soft-primary");
                });
            });

            dropzone.addEventListener("click", function () {
                fileInput.click();
            });

            dropzone.addEventListener("keydown", function (event) {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    fileInput.click();
                }
            });

            dropzone.addEventListener("drop", function (event) {
                addCreateFiles(event.dataTransfer.files);
            });

            fileInput.addEventListener("change", function (event) {
                addCreateFiles(event.target.files);
                fileInput.value = "";
            });
        }

        renderCreateFilePreview();

        form.addEventListener("submit", function (event) {
            event.preventDefault();
            hideCreateResult();
            form.classList.add("was-validated");

            if (!form.checkValidity()) {
                showCreateResult(
                    "Please complete the required ticket fields before submitting.",
                    "danger"
                );
                return;
            }

            if (isCreateSubmitting) {
                return;
            }

            isCreateSubmitting = true;
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML =
                    '<i class="ri-loader-4-line align-bottom me-1"></i> Saving...';
            }

            const formData = new FormData(form);
            formData.delete("files");

            if (createEditor) {
                formData.set("description", createEditor.getData());
            }

            selectedCreateFiles.forEach(function (file) {
                formData.append("files", file, file.name);
            });

            fetch(ticketCreateURL, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then(function (response) {
                    return parseResponseBody(response).then(function (body) {
                        return { ok: response.ok, body: body };
                    });
                })
                .then(function (result) {
                    const body = result.body || {};
                    if (!result.ok || !body.success) {
                        if (body.errors) {
                            const fieldErrors = Object.keys(body.errors)
                                .map(function (fieldName) {
                                    return (
                                        "<strong>" +
                                        fieldName +
                                        ":</strong> " +
                                        body.errors[fieldName].join(", ")
                                    );
                                })
                                .join("<br>");
                            throw new Error(fieldErrors || body.message);
                        }

                        throw new Error(
                            body.message || "The ticket could not be created."
                        );
                    }

                    showCreateResult(
                        body.message || "Ticket created successfully.",
                        "success"
                    );

                    setTimeout(function () {
                        window.location.href = body.redirect_url || ticketListURL;
                    }, 600);
                })
                .catch(function (error) {
                    showCreateResult(error.message, "danger");
                })
                .finally(function () {
                    isCreateSubmitting = false;
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.innerHTML = "Add Ticket";
                    }
                });
        });

        if (modal) {
            modal.addEventListener("hidden.bs.modal", function () {
                resetCreateForm();
            });
        }
    }

    function setupLoadTicketForm() {
        const modal = document.getElementById("showModal");
        const form = document.getElementById("loadTicketForm");
        if (!form) {
            return;
        }

        const fileInput = document.getElementById("excel_file");
        const dropZone = document.getElementById("drop-zone");
        const fileName = document.getElementById("file-name");
        const filePreview = document.getElementById("file-preview");
        const previewFileName = document.getElementById("preview-file-name");
        const previewFileSize = document.getElementById("preview-file-size");
        const uploadButton = document.getElementById("uploadBtn");
        const uploadProgress = document.getElementById("uploadProgress");
        const progressBar = uploadProgress
            ? uploadProgress.querySelector(".progress-bar")
            : null;
        const uploadResult = document.getElementById("uploadResult");

        function showUploadResult(message, type, errors) {
            if (!uploadResult) {
                return;
            }

            let detailsHtml = message;
            if (Array.isArray(errors) && errors.length) {
                detailsHtml +=
                    '<ul class="mb-0 mt-2 text-start">' +
                    errors
                        .slice(0, 10)
                        .map(function (error) {
                            return "<li>" + error + "</li>";
                        })
                        .join("") +
                    "</ul>";

                if (errors.length > 10) {
                    detailsHtml +=
                        '<div class="mt-2 small text-muted">Showing the first 10 row errors.</div>';
                }
            }

            uploadResult.className = "alert alert-" + type;
            uploadResult.innerHTML = detailsHtml;
            uploadResult.style.display = "block";
        }

        function hideUploadResult() {
            if (!uploadResult) {
                return;
            }

            uploadResult.style.display = "none";
            uploadResult.innerHTML = "";
        }

        function resetLoadFile() {
            if (fileInput) {
                fileInput.value = "";
            }
            if (fileName) {
                fileName.textContent = "No file chosen";
            }
            if (filePreview) {
                filePreview.style.display = "none";
            }
            hideUploadResult();
            if (progressBar) {
                progressBar.style.width = "0%";
                progressBar.classList.remove("progress-bar-animated");
            }
            if (uploadProgress) {
                uploadProgress.style.display = "none";
            }
        }

        window.removeFile = resetLoadFile;

        function handleLoadFile(file) {
            if (!file) {
                return;
            }

            if (!/\.(xlsx|xls)$/i.test(file.name)) {
                showUploadResult(
                    "Please select an Excel file in .xlsx or .xls format.",
                    "danger"
                );
                return;
            }

            if (file.size > MAX_UPLOAD_FILE_SIZE_BYTES) {
                showUploadResult(
                    "File size exceeds the 250 MB upload limit.",
                    "danger"
                );
                return;
            }

            if (fileName) {
                fileName.textContent = file.name;
            }
            if (previewFileName) {
                previewFileName.textContent = file.name;
            }
            if (previewFileSize) {
                previewFileSize.textContent = formatFileSize(file.size);
            }
            if (filePreview) {
                filePreview.style.display = "block";
            }

            hideUploadResult();
        }

        if (dropZone && fileInput) {
            ["dragenter", "dragover", "dragleave", "drop"].forEach(function (eventName) {
                dropZone.addEventListener(eventName, function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                });
            });

            ["dragenter", "dragover"].forEach(function (eventName) {
                dropZone.addEventListener(eventName, function () {
                    dropZone.classList.add("border-primary");
                    dropZone.style.backgroundColor = "#e3f2fd";
                });
            });

            ["dragleave", "drop"].forEach(function (eventName) {
                dropZone.addEventListener(eventName, function () {
                    dropZone.classList.remove("border-primary");
                    dropZone.style.backgroundColor = "#f8f9fa";
                });
            });

            dropZone.addEventListener("click", function () {
                fileInput.click();
            });

            dropZone.addEventListener("drop", function (event) {
                const droppedFile = event.dataTransfer.files[0];
                if (droppedFile) {
                    const transfer = new DataTransfer();
                    transfer.items.add(droppedFile);
                    fileInput.files = transfer.files;
                    handleLoadFile(droppedFile);
                }
            });

            fileInput.addEventListener("change", function () {
                handleLoadFile(fileInput.files[0]);
            });
        }

        form.addEventListener("submit", function (event) {
            event.preventDefault();

            if (isLoadSubmitting) {
                return;
            }

            if (!fileInput || !fileInput.files[0]) {
                showUploadResult("Please choose an Excel file before uploading.", "danger");
                return;
            }

            isLoadSubmitting = true;
            hideUploadResult();

            if (uploadButton) {
                uploadButton.disabled = true;
                uploadButton.innerHTML =
                    '<i class="ri-loader-4-line align-bottom me-1"></i> Uploading...';
            }
            if (uploadProgress) {
                uploadProgress.style.display = "block";
            }
            if (progressBar) {
                progressBar.style.width = "45%";
                progressBar.classList.add("progress-bar-animated");
            }

            fetch(ticketBulkUploadURL, {
                method: "POST",
                body: new FormData(form),
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then(function (response) {
                    return parseResponseBody(response).then(function (body) {
                        return { ok: response.ok, body: body };
                    });
                })
                .then(function (result) {
                    const body = result.body || {};
                    const rowErrors = body.errors || [];

                    if (!result.ok || !body.success) {
                        throw {
                            message:
                                body.message ||
                                "The spreadsheet could not be imported.",
                            errors: rowErrors,
                        };
                    }

                    if (progressBar) {
                        progressBar.style.width = "100%";
                    }

                    const alertType = rowErrors.length ? "warning" : "success";
                    showUploadResult(
                        body.message || "Tickets were created successfully.",
                        alertType,
                        rowErrors
                    );

                    setTimeout(function () {
                        const modalInstance = bootstrap.Modal.getInstance(modal);
                        if (modalInstance) {
                            modalInstance.hide();
                        }
                        window.location.reload();
                    }, rowErrors.length ? 2500 : 1500);
                })
                .catch(function (error) {
                    if (progressBar) {
                        progressBar.style.width = "0%";
                    }
                    showUploadResult(
                        error.message || "An unexpected upload error occurred.",
                        "danger",
                        error.errors || []
                    );
                })
                .finally(function () {
                    isLoadSubmitting = false;
                    if (uploadButton) {
                        uploadButton.disabled = false;
                        uploadButton.innerHTML =
                            '<i class="ri-upload-line align-bottom me-1"></i> Upload & Create Tickets';
                    }
                    if (progressBar) {
                        progressBar.classList.remove("progress-bar-animated");
                    }
                    if (uploadProgress) {
                        uploadProgress.style.display = "none";
                    }
                });
        });

        if (modal) {
            modal.addEventListener("hidden.bs.modal", function () {
                resetLoadFile();
            });
        }
    }
})();
