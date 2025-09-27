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
    
    const titleField = document.getElementById("event-title");
    if (titleField) {
        titleField.value = event.title || "";
    }
    
    const locationField = document.getElementById("event-location");
    if (locationField) {
        locationField.value = event.extendedProps?.location || "No Location";
    }
    
    const descriptionField = document.getElementById("event-description");
    if (descriptionField) {
        descriptionField.value = event.extendedProps?.description || "No Description";
    }
    
    const eventIdField = document.getElementById("eventid");
    if (eventIdField) {
        eventIdField.value = event.id || "";
    }
    
    if (eventCategoryChoice) {
        eventCategoryChoice.destroy();
    }
    
    if (event.extendedProps?.type) {
        eventCategoryChoice = new Choices("#event-category", { searchEnabled: false });
        eventCategoryChoice.setChoiceByValue(event.extendedProps.type);
    }
    
    // Handle guest list
    const guestSelect = document.getElementById("event-guests");
    if (guestSelect && event.extendedProps?.guest_list) {
        const guestIds = event.extendedProps.guest_list.map(guest => guest.user_id);
        for (let i = 0; i < guestSelect.options.length; i++) {
            guestSelect.options[i].selected = guestIds.includes(guestSelect.options[i].value);
        }
    }
}

// Modal functions
function showAddNewEventModal() {
    console.log("showAddNewEventModal called");
    if (addEvent) {
        addEvent.show();
    }
}

function showEventModal(event) {
    console.log("showEventModal called with:", event);
    selectedEvent = event;
    
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
    
    eventTyped();
    flatPickrInit();
    flatpicekrValueClear();
    
    if (addEvent) {
        addEvent.show();
    }
    
    if (formEvent) {
        formEvent.reset();
    }
    
    populateEventDetails(selectedEvent);
    
    if (modalTitle) {
        modalTitle.innerText = selectedEvent.title || "Event Details";
    }
    
    const deleteBtn = document.getElementById("btn-delete-event");
    if (deleteBtn) {
        deleteBtn.removeAttribute("hidden");
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
                showEventModal(originalEvent);
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
                showEventModal(fallbackEvent);
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

// Wrapper function for event details
window.showEventDetails = function(eventData) {
    console.log("showEventDetails called with:", eventData);
};
