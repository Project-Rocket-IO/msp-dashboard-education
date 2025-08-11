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

function createClientDiv() {
    // Client Choice Select (Dynamic)
    var clientChoiceDiv = document.createElement("div");
    clientChoiceDiv.classList.add("col-lg-3", "mb-3");
    clientChoiceDiv.style.display = 'none'

    var clientChoiceLabel = document.createElement("label");
    clientChoiceLabel.setAttribute("for", "client-choice");
    clientChoiceLabel.classList.add("form-label");
    clientChoiceLabel.textContent = "Client Choice";

    var clientChoiceSelectDiv = document.createElement("div");
    clientChoiceSelectDiv.classList.add("row");

    var clientChoiceSelectDivInner = document.createElement("div");
    clientChoiceSelectDivInner.classList.add("col-lg-12");

    var clientChoiceSelect = document.createElement("select");
    clientChoiceSelect.classList.add("form-control");
    clientChoiceSelect.setAttribute("data-choices", "");
    clientChoiceSelect.setAttribute("data-choices-search-true", "");
    clientChoiceSelect.setAttribute("name", `choices`);

    // Options for Client Choice Select (Assuming clients is an array of objects with 'name' attribute)
    clients.forEach(function (client) {
    var option = document.createElement("option");
    option.setAttribute("value", client.id);
    option.textContent = client.name;
    clientChoiceSelect.appendChild(option);
    });

    clientChoiceSelectDivInner.appendChild(clientChoiceSelect)
    clientChoiceSelectDiv.appendChild(clientChoiceSelectDivInner);
    clientChoiceDiv.appendChild(clientChoiceLabel);
    clientChoiceDiv.appendChild(clientChoiceSelectDiv);
    
    return [clientChoiceDiv, clientChoiceSelect];
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

    // Options for Role Select
    var roles = ["Administrator", "Bookkeeper", "Lead Technician", "Technician", "Sub Contractor", "Sales", "Project Manager", "Scheduler"]
    roles.forEach(function (role, index) {
        var option = document.createElement("option");
        option.setAttribute("value", String(index + 1));
        option.textContent = role;
        roleSelect.appendChild(option);
    });
    // Client Role
    var option = document.createElement("option");
    option.setAttribute("value", "10");
    option.textContent = "Client";
    roleSelect.appendChild(option);
    
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
    var [clientChoiceDiv, clientChoiceSelect] = createClientDiv();
    var deleteButtonDiv = createDeleteButtonDiv(newDiv);
  
    // Append all elements to the newDiv
    divRow.appendChild(roleDiv);
    divRow.appendChild(clientChoiceDiv);
    divRow.appendChild(deleteButtonDiv);

    newDiv.append(divRow)

    // Append the newDiv to the parent container with id "newlink"
    document.getElementById("newlink").appendChild(newDiv);

    // Initialize Choices.js
    new Choices(roleSelect, {
        searchEnabled: false
    });
    new Choices(clientChoiceSelect);

    // Display Client Choice only if Client is selected
    roleSelect.addEventListener('change', (event) => {
    let selectedOption = event.target.value;
    if (selectedOption == '10') {
        clientChoiceDiv.style.display = 'block'
        } else {
        clientChoiceDiv.style.display = 'none'
        }
    })

}
  
