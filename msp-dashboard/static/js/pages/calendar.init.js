import * as dateUtils from "./dateUtils.init.js";

// Global variables
var modalTitle, formEvent, formDeleteEvent, forms, selectedEvent, addEvent, Draggable, externalEventContainerEl, calendarEl, eventCategoryChoice = null;

// Utility functions
function getInitialView() {
    return window.innerWidth >= 768 && window.innerWidth < 1200 ? "timeGridWeek" : window.innerWidth <= 768 ? "listMonth" : "dayGridMonth";
}

// Flatpickr functions
window.flatPickrInit = function() {
    console.log("flatPickrInit called");
};

window.flatpicekrValueClear = function() {
    console.log("flatpicekrValueClear called");
};

// Event form functions
window.eventClicked = function() {
    console.log("eventClicked called");
};

window.eventTyped = function() {
    console.log("eventTyped called");
    const formEvent = document.getElementById("form-event");
    if (formEvent) {
        formEvent.classList.remove("view-event");
    }
    
    // Show form fields
    const titleField = document.getElementById("event-title");
    if (titleField) {
        titleField.classList.replace("d-none", "d-block");
    }
    
    const categoryField = document.getElementById("event-category");
    if (categoryField) {
        categoryField.classList.replace("d-none", "d-block");
    }
    
    const locationField = document.getElementById("event-location");
    if (locationField) {
        locationField.classList.replace("d-none", "d-block");
    }
    
    const descriptionField = document.getElementById("event-description");
    if (descriptionField) {
        descriptionField.classList.replace("d-none", "d-block");
    }
    
    // Hide read-only tags
    const startDateTag = document.getElementById("event-start-date-tag");
    if (startDateTag) {
        startDateTag.classList.replace("d-block", "d-none");
    }
    
    const locationTag = document.getElementById("event-location-tag");
    if (locationTag) {
        locationTag.classList.replace("d-block", "d-none");
    }
    
    const descriptionTag = document.getElementById("event-description-tag");
    if (descriptionTag) {
        descriptionTag.classList.replace("d-block", "d-none");
    }
    
    // Show save button
    const saveBtn = document.getElementById("btn-save-event");
    if (saveBtn) {
        saveBtn.removeAttribute("hidden");
    }
};

// Event details population
function populateEventDetails(event) {
    console.log("populateEventDetails called with:", event);
    
    // Populate basic fields
    const titleField = document.getElementById("event-title");
    if (titleField) {
        titleField.value = event.title || "";
    }
    
    const locationField = document.getElementById("event-location");
    if (locationField) {
        locationField.value = event.extendedProps?.location || "";
    }
    
    const descriptionField = document.getElementById("event-description");
    if (descriptionField) {
        descriptionField.value = event.extendedProps?.description || "";
    }
    
    const eventIdField = document.getElementById("eventid");
    if (eventIdField) {
        eventIdField.value = event.id || "";
    }
    
    // Populate date fields
    if (event.start) {
        const startDate = new Date(event.start);
        const startDateField = document.getElementById("start_date");
        if (startDateField) {
            startDateField.value = startDate.toISOString().split('T')[0]; // YYYY-MM-DD format
        }
    }
    
    if (event.end) {
        const endDate = new Date(event.end);
        const endDateField = document.getElementById("end_date");
        if (endDateField) {
            endDateField.value = endDate.toISOString().split('T')[0]; // YYYY-MM-DD format
        }
    }
    
    // Populate time fields
    if (event.start) {
        const startDate = new Date(event.start);
        const startTime = startDate.toTimeString().slice(0, 5); // HH:MM format
        const startTimeField = document.getElementById("timepicker1");
        if (startTimeField) {
            startTimeField.value = startTime;
        }
    }
    
    if (event.end) {
        const endDate = new Date(event.end);
        const endTime = endDate.toTimeString().slice(0, 5); // HH:MM format
        const endTimeField = document.getElementById("timepicker2");
        if (endTimeField) {
            endTimeField.value = endTime;
        }
    }
    
    // Update hidden datetime fields
    updateDateTimeFields();
    
    // Handle mandatory attendees
    const mandatoryAttendeesField = document.getElementById("mandatory-attendees-fresh");
    if (mandatoryAttendeesField && event.extendedProps?.mandatory_invites) {
        const attendeeIds = event.extendedProps.mandatory_invites.map(tech => tech.user_id || tech.id);
        for (let i = 0; i < mandatoryAttendeesField.options.length; i++) {
            mandatoryAttendeesField.options[i].selected = attendeeIds.includes(parseInt(mandatoryAttendeesField.options[i].value));
        }
    }
    
    // Handle optional attendees
    const optionalAttendeesField = document.getElementById("optional-attendees-fresh");
    if (optionalAttendeesField && event.extendedProps?.optional_invites) {
        const attendeeIds = event.extendedProps.optional_invites.map(tech => tech.user_id || tech.id);
        for (let i = 0; i < optionalAttendeesField.options.length; i++) {
            optionalAttendeesField.options[i].selected = attendeeIds.includes(parseInt(optionalAttendeesField.options[i].value));
        }
    }
    
    // Handle recurrence fields
    if (event.extendedProps?.repeating) {
        const isRepeatingCheckbox = document.getElementById("isRepeating");
        if (isRepeatingCheckbox) {
            isRepeatingCheckbox.checked = true;
            toggleRecurrenceFields();
        }
        
        const repeatFrequencyField = document.getElementById("repeat-frequency");
        if (repeatFrequencyField && event.extendedProps?.repeat_frequency) {
            repeatFrequencyField.value = event.extendedProps.repeat_frequency;
        }
        
        const repeatIntervalField = document.getElementById("repeat-interval");
        if (repeatIntervalField && event.extendedProps?.repeat_interval) {
            repeatIntervalField.value = event.extendedProps.repeat_interval;
        }
    }
}

// Modal functions
function showAddNewEventModal(clickedDateInfo) {
    console.log("showAddNewEventModal called", clickedDateInfo);
    
    // Reset form for new event
    if (formEvent) {
        formEvent.reset();
    }
    
    // Update modal title for new event
    if (modalTitle) {
        modalTitle.innerText = "New Meeting";
    }
    
    // Hide edit-specific elements for new event
    const editBtn = document.getElementById("edit-event-btn");
    if (editBtn) {
        editBtn.setAttribute("hidden", "true");
    }
    
    const saveBtn = document.getElementById("btn-save-event");
    if (saveBtn) {
        saveBtn.removeAttribute("hidden");
        saveBtn.innerHTML = "Send";
    }
    
    const deleteBtn = document.getElementById("btn-delete-event");
    if (deleteBtn) {
        deleteBtn.setAttribute("hidden", "true");
    }
    
    // Clear the event ID field for new events
    const eventIdField = document.getElementById("eventid");
    if (eventIdField) {
        eventIdField.value = "";
    }
    
    // If a specific date was clicked, populate start and end dates
    if (clickedDateInfo && clickedDateInfo.date) {
        const clickedDate = new Date(clickedDateInfo.date);
        const dateString = clickedDate.toISOString().split('T')[0]; // YYYY-MM-DD format
        
        // Set start date
        const startDateField = document.getElementById("start_date");
        if (startDateField) {
            startDateField.value = dateString;
        }
        
        // Set end date
        const endDateField = document.getElementById("end_date");
        if (endDateField) {
            endDateField.value = dateString;
        }
        
        console.log("Set start and end dates to:", dateString);
    }
    
    // Show the modal
    if (addEvent) {
        addEvent.show();
    }
}

// Event details modal (similar to ticket/project modals)
function showEventDetailsModal(event) {
    console.log("showEventDetailsModal called with:", event);
    
    const eventName = event.title || "Untitled Event";
    const startDate = event.start ? new Date(event.start).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "No start date";
    const endDate = event.end ? new Date(event.end).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "No end date";
    
    // Format start and end times
    let startTime = "All Day";
    let endTime = "All Day";
    
    if (event.start) {
        const startDateTime = new Date(event.start);
        const startHour = startDateTime.getHours();
        const startMinute = startDateTime.getMinutes();
        
        // Check if it's not midnight (all-day event)
        if (startHour !== 0 || startMinute !== 0) {
            const startPeriod = startHour >= 12 ? 'PM' : 'AM';
            const startDisplayHour = startHour === 0 ? 12 : (startHour > 12 ? startHour - 12 : startHour);
            const startDisplayMinute = startMinute.toString().padStart(2, '0');
            startTime = `${startDisplayHour}:${startDisplayMinute} ${startPeriod}`;
        }
    }
    
    if (event.end) {
        const endDateTime = new Date(event.end);
        const endHour = endDateTime.getHours();
        const endMinute = endDateTime.getMinutes();
        
        // Check if it's not midnight (all-day event)
        if (endHour !== 0 || endMinute !== 0) {
            const endPeriod = endHour >= 12 ? 'PM' : 'AM';
            const endDisplayHour = endHour === 0 ? 12 : (endHour > 12 ? endHour - 12 : endHour);
            const endDisplayMinute = endMinute.toString().padStart(2, '0');
            endTime = `${endDisplayHour}:${endDisplayMinute} ${endPeriod}`;
        }
    }
    
    const location = event.extendedProps?.location || "No location";
    const description = event.extendedProps?.description || "No description";
    const eventType = event.extendedProps?.type || "Event";
    
    const modalHtml = `
        <div class="modal fade" id="event-details-modal" tabindex="-1" aria-labelledby="event-details-modal-label" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="event-details-modal-label">${eventName}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Start Date:</strong> ${startDate}</p>
                                <p><strong>End Date:</strong> ${endDate}</p>
                                <p><strong>Start Time:</strong> ${startTime}</p>
                                <p><strong>End Time:</strong> ${endTime}</p>
                                <p><strong>Location:</strong> ${location}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Type:</strong> ${eventType}</p>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-12">
                                <p><strong>Description:</strong></p>
                                <p>${description}</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" onclick="editEvent('${event.id}')">Edit</button>
                        <button type="button" class="btn btn-danger" onclick="deleteEvent('${event.id}', '${eventName}')">Delete</button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML("beforeend", modalHtml);
    const modal = new bootstrap.Modal(document.getElementById("event-details-modal"));
    modal.show();
    
    document.getElementById("event-details-modal").addEventListener("hidden.bs.modal", function() {
        document.getElementById("event-details-modal").remove();
    });
}

function showEventModal(event) {
    console.log("showEventModal called with:", event);
    selectedEvent = event;
    
    // Reset form first
    if (formEvent) {
        formEvent.reset();
    }
    
    // Update modal title
    if (modalTitle) {
        modalTitle.innerText = selectedEvent.title || "Edit Event";
    }
    
    // Show edit-specific elements
    const editBtn = document.getElementById("edit-event-btn");
    if (editBtn) {
        editBtn.removeAttribute("hidden");
        editBtn.setAttribute("data-id", "edit-event");
        editBtn.innerHTML = "Edit";
    }
    
    const saveBtn = document.getElementById("btn-save-event");
    if (saveBtn) {
        saveBtn.removeAttribute("hidden");
        saveBtn.innerHTML = "Update Event";
    }
    
    const deleteBtn = document.getElementById("btn-delete-event");
    if (deleteBtn) {
        deleteBtn.removeAttribute("hidden");
    }
    
    // Enable form editing mode
    eventTyped();
    
    // Initialize date/time pickers
    flatPickrInit();
    flatpicekrValueClear();
    
    // Populate form with event data
    populateEventDetails(selectedEvent);
    
    // Show the modal
    if (addEvent) {
        addEvent.show();
    }
}

// Ticket modal
function showTicketModal(ticket) {
    console.log("showTicketModal called with:", ticket);
    const ticketName = ticket.title.replace("Ticket: ", "");
    const dueDate = ticket.start ? new Date(ticket.start).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "No due date";
    const createDate = ticket.extendedProps?.create_date ? new Date(ticket.extendedProps.create_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "No create date";
    const assignments = ticket.extendedProps?.mandatory_invites?.map(tech => tech.username).join(", ") || "No assignments";
    const project = ticket.extendedProps?.project || "No project";
    const status = ticket.extendedProps?.status || "No status";
    const priority = ticket.extendedProps?.priority || "No priority";
    const description = ticket.extendedProps?.description || "Nothing since there is none";
    
    const modalHtml = `
        <div class="modal fade" id="ticket-modal" tabindex="-1" aria-labelledby="ticket-modal-label" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="ticket-modal-label">${ticketName}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Due Date:</strong> ${dueDate}</p>
                                <p><strong>Create Date:</strong> ${createDate}</p>
                                <p><strong>Assignment:</strong> ${assignments}</p>
                                <p><strong>Project:</strong> ${project}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Status:</strong> ${status}</p>
                                <p><strong>Priority:</strong> ${priority}</p>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-12">
                                <p><strong>Description:</strong></p>
                                <p>${description}</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" onclick="editTicket(${ticket.extendedProps.model_id})">Edit</button>
                        <button type="button" class="btn btn-secondary" onclick="viewTicket(${ticket.extendedProps.model_id})">View</button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML("beforeend", modalHtml);
    const modal = new bootstrap.Modal(document.getElementById("ticket-modal"));
    modal.show();
    
    document.getElementById("ticket-modal").addEventListener("hidden.bs.modal", function() {
        document.getElementById("ticket-modal").remove();
    });
}

// Project modal
function showProjectModal(project) {
    console.log("showProjectModal called with:", project);
    const projectName = project.title.replace("Project: ", "");
    const dueDate = project.start ? new Date(project.start).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "No due date";
    const createDate = project.extendedProps?.create_date ? new Date(project.extendedProps.create_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "No create date";
    const assignments = project.extendedProps?.mandatory_invites?.map(tech => tech.username).join(", ") || "No assignments";
    const status = project.extendedProps?.status || "No status";
    const priority = project.extendedProps?.priority || "No priority";
    const description = project.extendedProps?.description || "Nothing since there is none";
    
    const modalHtml = `
        <div class="modal fade" id="project-modal" tabindex="-1" aria-labelledby="project-modal-label" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="project-modal-label">${projectName}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Due Date:</strong> ${dueDate}</p>
                                <p><strong>Create Date:</strong> ${createDate}</p>
                                <p><strong>Assignments:</strong> ${assignments}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Status:</strong> ${status}</p>
                                <p><strong>Priority:</strong> ${priority}</p>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-12">
                                <p><strong>Description:</strong></p>
                                <p>${description}</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" onclick="editProject(${project.extendedProps.model_id})">Edit</button>
                        <button type="button" class="btn btn-secondary" onclick="viewProject(${project.extendedProps.model_id})">View</button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML("beforeend", modalHtml);
    const modal = new bootstrap.Modal(document.getElementById("project-modal"));
    modal.show();
    
    document.getElementById("project-modal").addEventListener("hidden.bs.modal", function() {
        document.getElementById("project-modal").remove();
    });
}

// Upcoming events function
function upcomingEvent(events) {
    console.log('upcomingEvent called with:', events);
    
    const now = new Date();
    const validEvents = events.filter(event => {
        const hasValidStart = event.start && event.start !== "Invalid Date";
        if (!hasValidStart) return false;
        
        try {
            const eventDate = new Date(event.start);
            const isFuture = eventDate >= now;
            return isFuture;
        } catch (e) {
            console.warn('Invalid date for event:', event.title, event.start);
            return false;
        }
    });
    
    validEvents.sort(function(event1, event2) {
        return new Date(event1.start) - new Date(event2.start);
    });
    
    const upcomingList = document.getElementById("upcoming-event-list");
    if (upcomingList) {
        upcomingList.innerHTML = "";
        
        validEvents.forEach(function(element) {
            const title = element.title;
            const eventType = element.event_type || 'event';
            const description = element.description ? element.description.substring(0, 50) + (element.description.length > 50 ? '...' : '') : "";
            
            let startDate = null;
            if (element.start) {
                try {
                    const date = new Date(element.start);
                    if (!isNaN(date.getTime())) {
                        startDate = date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
                    }
                } catch (e) {
                    console.warn('Invalid start date:', element.start);
                }
            }
            
            let colorClass = 'primary';
            if (eventType === 'ticket') colorClass = 'info';
            else if (eventType === 'project') colorClass = 'warning';
            
            let displayTitle = title;
            if (eventType === 'ticket' && !title.startsWith('Ticket:')) {
                displayTitle = 'Ticket: ' + title;
            } else if (eventType === 'project' && !title.startsWith('Project:')) {
                displayTitle = 'Project: ' + title;
            } else if (eventType === 'event' && !title.startsWith('Event:')) {
                displayTitle = 'Event: ' + title;
            }
            
            const eventHtml = `
                <div class='card mb-3'>
                    <div class='card-body'>
                        <div class='d-flex mb-3'>
                            <div class='flex-grow-1'>
                                <i class='mdi mdi-checkbox-blank-circle me-2 text-${colorClass}'></i>
                                <span class='fw-medium'>${startDate || 'No date'}</span>
                            </div>
                        </div>
                        <h6 class='card-title fs-16'>${displayTitle}</h6>
                        <p class='text-muted text-truncate-two-lines mb-0'>${description}</p>
                    </div>
                </div>
            `;
            
            upcomingList.innerHTML += eventHtml;
        });
    }
}

// Event functions
window.editEvent = function(eventId) {
    console.log("editEvent called with ID:", eventId);
    
    // Close the details modal first
    const detailsModal = document.getElementById("event-details-modal");
    if (detailsModal) {
        const modal = bootstrap.Modal.getInstance(detailsModal);
        if (modal) {
            modal.hide();
        }
        // Remove the modal from DOM after a short delay to ensure it's closed
        setTimeout(() => {
            if (detailsModal && detailsModal.parentNode) {
                detailsModal.remove();
            }
        }, 300);
    }
    
    // Find the event in window.events
    const event = window.events.find(e => e.id === eventId);
    if (event) {
        // Add a small delay to ensure the details modal is fully closed
        setTimeout(() => {
            showEventModal(event);
        }, 350);
    } else {
        console.error("Event not found with ID:", eventId);
    }
};

window.deleteEvent = function(eventId, eventName) {
    console.log("deleteEvent called with ID:", eventId, "Name:", eventName);
    
    const confirmationModalHtml = `
        <div class="modal fade" id="delete-confirmation-modal" tabindex="-1" aria-labelledby="delete-confirmation-modal-label" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="delete-confirmation-modal-label">Confirm Delete</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>Are you sure you want to delete event <strong>"${eventName}"</strong>?</p>
                        <p class="text-muted">This action cannot be undone.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger" onclick="confirmDeleteEvent('${eventId}')">Yes, Delete</button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML("beforeend", confirmationModalHtml);
    const modal = new bootstrap.Modal(document.getElementById("delete-confirmation-modal"));
    modal.show();
    
    document.getElementById("delete-confirmation-modal").addEventListener("hidden.bs.modal", function() {
        document.getElementById("delete-confirmation-modal").remove();
    });
};

window.confirmDeleteEvent = function(eventId) {
    console.log("confirmDeleteEvent called with ID:", eventId);
    
    // Remove from window.events array
    const eventIndex = window.events.findIndex(e => e.id === eventId);
    if (eventIndex !== -1) {
        window.events.splice(eventIndex, 1);
        console.log("Event removed from window.events");
    }
    
    // Here you would typically make an AJAX call to delete from the server
    // For now, we'll just refresh the calendar
    if (window.calendar) {
        window.calendar.refetchEvents();
    }
    
    // Close the confirmation modal
    const confirmationModal = document.getElementById("delete-confirmation-modal");
    if (confirmationModal) {
        const modal = bootstrap.Modal.getInstance(confirmationModal);
        if (modal) {
            modal.hide();
        }
    }
    
    // Close the details modal
    const detailsModal = document.getElementById("event-details-modal");
    if (detailsModal) {
        const modal = bootstrap.Modal.getInstance(detailsModal);
        if (modal) {
            modal.hide();
        }
    }
    
    console.log("Event deleted successfully");
};

// Navigation functions
window.editTicket = function(ticketId) {
    window.location.href = "/apps/support-tickets/edit/" + ticketId;
};

window.viewTicket = function(ticketId) {
    window.location.href = "/apps/support-tickets/details/" + ticketId;
};

window.editProject = function(projectId) {
    window.location.href = "/apps/projects/edit/" + projectId;
};

window.viewProject = function(projectId) {
    window.location.href = "/apps/projects/overview/" + projectId;
};

// Main initialization
document.addEventListener("DOMContentLoaded", async function() {
    console.log("Calendar initialization starting...");
    
    // Initialize modal
    addEvent = new bootstrap.Modal(document.getElementById("event-modal"), { keyboard: false });
    modalTitle = document.getElementById("modal-title");
    formEvent = document.getElementById("form-event");
    formDeleteEvent = document.getElementById("form-delete-event");
    forms = document.getElementsByClassName("needs-validation");
    selectedEvent = null;
    
    console.log("Modal initialized");
    
    // Initialize Draggable
    Draggable = FullCalendar.Draggable;
    externalEventContainerEl = document.getElementById("external-events");
    calendarEl = document.getElementById("calendar");
    
    new Draggable(externalEventContainerEl, {
        itemSelector: ".external-event",
        eventData: function(element) {
            return {
                id: Math.floor(Math.random() * 11000),
                title: element.innerText,
                allDay: true,
                start: new Date(),
                className: element.getAttribute("data-class")
            };
        }
    });
    
    console.log("Draggable initialized");
    
    // Initialize event category choice
    eventCategoryChoice = new Choices("#event-category", { searchEnabled: false });
    console.log("Event category choice initialized");
    
    // Initialize FullCalendar
    console.log("Initializing FullCalendar with events:", window.events);
    const calendar = new FullCalendar.Calendar(calendarEl, {
        timeZone: "local",
        editable: true,
        droppable: true,
        selectable: true,
        navLinks: true,
        initialView: getInitialView(),
        themeSystem: "bootstrap",
        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay,listMonth"
        },
        windowResize: function() {
            const view = getInitialView();
            calendar.changeView(view);
        },
        eventClick: function(info) {
            console.log("FullCalendar eventClick triggered");
            console.log("Event data from FullCalendar:", info.event);
            console.log("Event ID from FullCalendar:", info.event.id);
            console.log("Event title from FullCalendar:", info.event.title);
            
            const originalEvent = window.events.find(function(event) {
                return event.id === info.event.id;
            });
            
            console.log("Looking for original event with ID:", info.event.id);
            console.log("Available event IDs:", window.events.map(function(event) {
                return event.id;
            }));
            console.log("Original event found:", originalEvent);
            
            if (originalEvent) {
                console.log("Using original event data for modal");
                const extendedProps = originalEvent.extendedProps;
                if (extendedProps && extendedProps.model) {
                    if (extendedProps.model === "ticket") {
                        showTicketModal(originalEvent);
                        return;
                    }
                    if (extendedProps.model === "project") {
                        showProjectModal(originalEvent);
                        return;
                    }
                }
                showEventDetailsModal(originalEvent);
            } else {
                console.log("Original event not found, using FullCalendar data");
                const fallbackEvent = {
                    id: info.event.id,
                    title: info.event.title,
                    start: info.event.start,
                    end: info.event.end,
                    event_type: info.event.extendedProps?.event_type || "event",
                    extendedProps: info.event.extendedProps
                };
                showEventDetailsModal(fallbackEvent);
            }
            
            info.jsEvent.preventDefault();
            return false;
        },
        dateClick: function(info) {
            showAddNewEventModal(info);
        },
        events: window.events
    });
    
    calendar.render();
    console.log("FullCalendar rendered");
    
    // Store calendar instance globally for access by other functions
    window.calendar = calendar;
    
    // Load and display upcoming events
    upcomingEvent(window.events);
    console.log("Upcoming events populated");
    
    // Event listeners
    document.getElementById("btn-new-event").addEventListener("click", function(e) {
        console.log("Create New Event button clicked");
        showAddNewEventModal();
    });
    
    console.log("Calendar initialization complete!");
});

// Helper function to update hidden datetime fields
function updateDateTimeFields() {
    const startDate = document.getElementById('start_date');
    const endDate = document.getElementById('end_date');
    const startTime = document.getElementById('timepicker1');
    const endTime = document.getElementById('timepicker2');
    
    if (startDate && startTime && startDate.value && startTime.value) {
        // Create a proper datetime string with timezone
        const startDateTime = new Date(startDate.value + 'T' + startTime.value + ':00');
        const startField = document.getElementById('start');
        if (startField) {
            startField.value = startDateTime.toISOString();
        }
    }
    
    if (endDate && endTime && endDate.value && endTime.value) {
        // Create a proper datetime string with timezone
        const endDateTime = new Date(endDate.value + 'T' + endTime.value + ':00');
        const endField = document.getElementById('end');
        if (endField) {
            endField.value = endDateTime.toISOString();
        }
    }
}

// Helper function to toggle recurrence fields
window.toggleRecurrenceFields = function() {
    const isRepeating = document.getElementById('isRepeating');
    const recurrenceFields = document.getElementById('recurrenceFields');
    
    if (isRepeating && recurrenceFields) {
        if (isRepeating.checked) {
            recurrenceFields.style.display = 'block';
        } else {
            recurrenceFields.style.display = 'none';
        }
    }
}

// Helper function to toggle custom recurrence options
window.toggleCustomRecurrence = function() {
    const repeatFrequency = document.getElementById('repeat-frequency');
    const weeklyRecurrenceOptions = document.getElementById('weeklyRecurrenceOptions');
    
    if (repeatFrequency && weeklyRecurrenceOptions) {
        if (repeatFrequency.value === 'WEEKLY') {
            weeklyRecurrenceOptions.style.display = 'block';
        } else {
            weeklyRecurrenceOptions.style.display = 'none';
        }
    }
}

// Wrapper function for event details
window.showEventDetails = function(eventData) {
    console.log("showEventDetails called with:", eventData);
};
