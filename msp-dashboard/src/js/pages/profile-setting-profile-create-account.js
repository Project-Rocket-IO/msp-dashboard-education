var count = 1;

function createDeleteButtonDiv(newDiv) {    
    // Delete Button
    var deleteButtonDiv = document.createElement("div");
    deleteButtonDiv.classList.add("hstack", "gap-2", "justify-content-end");
    
    var deleteButton = document.createElement("a");
    deleteButton.addEventListener('click', () => deleteEl(newDiv.id));
    deleteButton.classList.add("btn", "btn-danger", "mb-4");
    deleteButton.textContent = "Remove";

    deleteButtonDiv.appendChild(deleteButton);

    return deleteButtonDiv;
}

function createStudentAssignmentDiv() {
    // Student Assignment Select (Dynamic)
    var studentAssignmentDiv = document.createElement("div");
    studentAssignmentDiv.classList.add("col-lg-3", "mb-3");
    studentAssignmentDiv.style.display = 'none'

    var studentAssignmentLabel = document.createElement("label");
    studentAssignmentLabel.setAttribute("for", "student-assignment");
    studentAssignmentLabel.classList.add("form-label");
    studentAssignmentLabel.textContent = "Assign to User";

    var studentAssignmentSelectDiv = document.createElement("div");
    studentAssignmentSelectDiv.classList.add("row");

    var studentAssignmentSelectDivInner = document.createElement("div");
    studentAssignmentSelectDivInner.classList.add("col-lg-12");

    var studentAssignmentSelect = document.createElement("select");
    studentAssignmentSelect.classList.add("form-control");
    studentAssignmentSelect.setAttribute("data-choices", "");
    studentAssignmentSelect.setAttribute("data-choices-search-true", "");
    studentAssignmentSelect.setAttribute("name", "assigned_user_id");

    // Options for Student Assignment Select - Get from Django context
    var availableUsers = window.availableUsers || [];
    if (availableUsers.length > 0) {
        availableUsers.forEach(function (client) {
            var option = document.createElement("option");
            option.setAttribute("value", client.user_id);
            option.textContent = client.name + " (" + client.contact_first + " " + client.contact_last + ")";
            studentAssignmentSelect.appendChild(option);
        });
    } else {
        // Fallback if no clients available
        var option = document.createElement("option");
        option.setAttribute("value", "");
        option.textContent = "No clients available";
        studentAssignmentSelect.appendChild(option);
    }

    studentAssignmentSelectDivInner.appendChild(studentAssignmentSelect)
    studentAssignmentSelectDiv.appendChild(studentAssignmentSelectDivInner);
    studentAssignmentDiv.appendChild(studentAssignmentLabel);
    studentAssignmentDiv.appendChild(studentAssignmentSelectDiv);
    
    return [studentAssignmentDiv, studentAssignmentSelect];
}

function createRolesDiv() {
    
    // Role Select
    var roleDiv = document.createElement("div");
    roleDiv.classList.add("col-lg-3", "mb-3");

    var roleLabel = document.createElement("label");
    roleLabel.setAttribute("for", "role");
        roleLabel.classList.add("form-label");
    roleLabel.textContent = "Role";

    var roleSelectDiv = document.createElement("div");
    roleSelectDiv.classList.add("row");

    
    var roleSelectDivInner = document.createElement("div");
    roleSelectDivInner.classList.add("col-lg-12");

    var roleSelect = document.createElement("select");
    roleSelect.classList.add("form-control");
    roleSelect.setAttribute("data-choices", "");
    roleSelect.setAttribute("data-choices-search-false", "");
    roleSelect.setAttribute("name", "role");
    roleSelect.setAttribute("id", `user-role-choice-${count}`);

    // Options for Role Select - Get from Django context
    var availableGroups = window.availableGroups || [];
    if (availableGroups.length > 0) {
        // Use Django groups if available
        availableGroups.forEach(function (group) {
            var option = document.createElement("option");
            option.setAttribute("value", group.id);
            option.textContent = group.name;
            roleSelect.appendChild(option);
        });
    } else {
        // Fallback to educational roles if Django groups not available
        var roles = ["Student", "Faculty/Staff", "Administrator", "IT Dept", "Super Admin"];
        roles.forEach(function (role, index) {
            var option = document.createElement("option");
            option.setAttribute("value", String(index + 1));
            option.textContent = role;
            roleSelect.appendChild(option);
        });
    }
    
    roleSelectDivInner.appendChild(roleSelect)
    roleSelectDiv.appendChild(roleSelectDivInner);
    roleDiv.appendChild(roleLabel);
    roleDiv.appendChild(roleSelectDiv);

    return [roleDiv, roleSelect];
}

function create_new_link() {
    // Increment the counter to generate unique IDs
    count++;

    // Create a new div element to hold the form fields
    var newDiv = document.createElement("div");
    newDiv.id = count;

    var divRow = document.createElement("div")
    divRow.classList.add("row"); 


    var fields = [
        { label: "First Name", type: "text", placeholder: "Enter your firstname", name: "first_name", required: true, classes: ["col-lg-3", "mb-3"] },
        { label: "Last Name", type: "text", placeholder: "Enter your lastname", name: "last_name", required: true, classes: ["col-lg-3", "mb-3"] },
        { label: "Email Address", type: "text", placeholder: "Input Email", name: "email", required: true, classes: ["col-lg-3", "mb-3"] },
        { label: "Phone Number", type: "text", placeholder: "Enter your phone number", name: "phone", classes: ["col-lg-3", "mb-3"] },
        { label: "Title", type: "text", placeholder: "Enter your title", name: "title", classes: ["col-lg-3", "mb-3"] },
        { label: "Password", type: "text", placeholder: "Enter password", name: "password", classes: ["col-lg-3", "mb-3"] }
    ];

    fields.forEach((field, index) => {
        var fieldDiv = document.createElement("div");
        fieldDiv.classList.add(...field.classes);

        var fieldLabel = document.createElement("label");
        fieldLabel.setAttribute("for", field.label.toLowerCase().replace(" ", ""));
        fieldLabel.classList.add("form-label");
        fieldLabel.textContent = field.label;

        var fieldInput = document.createElement("input");
        fieldInput.setAttribute("type", field.type);
        fieldInput.setAttribute("id", `${field.label.toLowerCase().replace(" ", "")}${count}`);
        fieldInput.setAttribute("placeholder", field.placeholder);
        fieldInput.setAttribute("name", field.name);
        fieldInput.classList.add("form-control");
        if (field.required) fieldInput.required = true;

        fieldDiv.appendChild(fieldLabel);
        fieldDiv.appendChild(fieldInput);

        divRow.appendChild(fieldDiv);
    });

    // Adding inner divs to the main div
    var [roleDiv, roleSelect] = createRolesDiv();
    var [studentAssignmentDiv, studentAssignmentSelect] = createStudentAssignmentDiv();
    var deleteButtonDiv = createDeleteButtonDiv(newDiv);
  
    // Append all elements to the newDiv
    divRow.appendChild(roleDiv);
    divRow.appendChild(studentAssignmentDiv);
    divRow.appendChild(deleteButtonDiv);

    newDiv.append(divRow)

    // Append the newDiv to the parent container with id "newlink"
    document.getElementById("newlink").appendChild(newDiv);

    // Initialize Choices.js
    new Choices(roleSelect, {
        searchEnabled: false
    });
    new Choices(studentAssignmentSelect);

    // Display Student Assignment dropdown only if Student role is selected
    roleSelect.addEventListener('change', (event) => {
        let selectedText = event.target.options[event.target.selectedIndex].text;
        if (selectedText === 'Student') {
            studentAssignmentDiv.style.display = 'block';
        } else {
            studentAssignmentDiv.style.display = 'none';
        }
    });

}
  
