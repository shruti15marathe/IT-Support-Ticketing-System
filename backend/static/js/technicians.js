const user = JSON.parse(localStorage.getItem("user"));

if (!user || user.role !== "technician") {
    window.location.href = "/login";
}

document.getElementById("techName").innerText =
    `Welcome, ${user.full_name}`;

const ticketModal = new bootstrap.Modal(
    document.getElementById("ticketModal")
);

// Load Technician Tickets
async function loadTickets() {

    const response = await fetch(
        `http://127.0.0.1:5050/technician/tickets/${user.id}`
    );

    const tickets = await response.json();

    const table = document.getElementById("ticketRows");
    table.innerHTML = "";

    let assigned = 0;
    let progress = 0;
    let resolved = 0;

    tickets.forEach(ticket => {

        if (ticket.status === "Assigned") assigned++;
        if (ticket.status === "In Progress") progress++;
        if (ticket.status === "Resolved") resolved++;

        // Status Badge
        let badge = "assigned";
        if (ticket.status === "In Progress") badge = "progress";
        if (ticket.status === "Resolved") badge = "resolved";

        // Priority Badge
        let priorityClass = "medium";
        if (ticket.priority === "Low") priorityClass = "low";
        if (ticket.priority === "High") priorityClass = "high";
        if (ticket.priority === "Critical") priorityClass = "critical";

        table.innerHTML += `
        <tr>
            <td><strong>${ticket.ticket_number}</strong></td>

            <td>${ticket.subject}</td>

            <td>
                <span class="priority-badge ${priorityClass}">
                    ${ticket.priority}
                </span>
            </td>

            <td>
                <span class="badge-status ${badge}">
                    ${ticket.status}
                </span>
            </td>

            <td>
                <button class="btn-view"
                    onclick="openTicket('${ticket.ticket_number}')">
                    View
                </button>
            </td>
        </tr>`;
    });

    document.getElementById("assignedCount").innerText = assigned;
    document.getElementById("progressCount").innerText = progress;
    document.getElementById("resolvedCount").innerText = resolved;
}

loadTickets();

// Open Ticket Modal
async function openTicket(ticketNumber) {

    const response = await fetch(
        `http://127.0.0.1:5050/ticket/${ticketNumber}`
    );

    const ticket = await response.json();

    document.getElementById("mTicket").value = ticket.ticket_number;
    document.getElementById("mSubject").value = ticket.subject;
    document.getElementById("mPriority").value = ticket.priority;
    document.getElementById("mDescription").value = ticket.description;
    document.getElementById("mStatus").value = ticket.status;

    ticketModal.show();
}

// Save Status
document.getElementById("saveStatusBtn").onclick = async () => {

    const ticketNumber = document.getElementById("mTicket").value;
    const status = document.getElementById("mStatus").value;
    const resolution_notes =
        document.getElementById("mResolution").value;

    const response = await fetch(
        `http://127.0.0.1:5050/ticket/${ticketNumber}`,
        {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                status,
                resolution_notes
            })
        }
    );

    const result = await response.json();

    if (result.success) {
        ticketModal.hide();
        loadTickets();
    }
};