const user = JSON.parse(localStorage.getItem("user"));

if (!user || user.role !== "customer") {
    window.location.href = "/login";
}

document.getElementById("customerName").innerText = user.full_name;

const ticketModal = new bootstrap.Modal(
    document.getElementById("ticketModal")
);

// Load Customer Tickets
async function loadCustomerTickets() {

    const response = await fetch(`/customer/tickets/${user.id}`);
    const tickets = await response.json();

    document.getElementById("totalCount").innerText = tickets.length;
    document.getElementById("progressCount").innerText =
        tickets.filter(t => t.status === "In Progress").length;
    document.getElementById("resolvedCount").innerText =
        tickets.filter(t => t.status === "Resolved").length;

    const container = document.getElementById("ticketCards");
    container.innerHTML = "";

    tickets.forEach(ticket => {

        let badge = "assigned";
        if (ticket.status === "In Progress") badge = "progress";
        if (ticket.status === "Resolved") badge = "resolved";

        container.innerHTML += `
        <div class="border rounded-4 p-3 mb-3">

            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="fw-bold mb-0">${ticket.ticket_number}</h6>
                <span class="badge-status ${badge}">
                    ${ticket.status}
                </span>
            </div>

            <h5 class="mb-1">${ticket.subject}</h5>

            <p class="text-secondary small mb-3">
                Assigned to: ${ticket.technician || "Not Assigned"}
            </p>

            <div class="d-flex justify-content-end">
                <button class="btn btn-primary btn-sm"
                    onclick='openTicket(${JSON.stringify(ticket)})'>
                    View Details
                </button>
            </div>

        </div>`;
    });
}

// View Ticket Modal
function openTicket(ticket) {

    document.getElementById("vTicket").value = ticket.ticket_number;
    document.getElementById("vSubject").value = ticket.subject;
    document.getElementById("vStatus").value = ticket.status;
    document.getElementById("vTech").value =
        ticket.technician || "Not Assigned";
    document.getElementById("vNotes").value =
        ticket.resolution_notes || "No resolution yet";

    ticketModal.show();
}

// Raise New Ticket
async function raiseTicket() {

    const subject = document.getElementById("subject").value;
    const description = document.getElementById("description").value;
    const priority = document.getElementById("priority").value;

    if (!subject || !description) {
        alert("Please fill all fields");
        return;
    }

    const response = await fetch("/customer/create-ticket", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            customer_id: user.id,
            subject,
            description,
            priority
        })
    });

    const result = await response.json();

    if (result.success) {

        alert("Ticket Raised Successfully");

        document.getElementById("subject").value = "";
        document.getElementById("description").value = "";
        document.getElementById("priority").value = "Medium";

        loadCustomerTickets();
    }
}

loadCustomerTickets();