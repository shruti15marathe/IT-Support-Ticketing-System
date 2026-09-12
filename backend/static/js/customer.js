if (window.customerLoaded) {
    console.log("customer.js already loaded");
} else {
    window.customerLoaded = true;

    const customerUser = JSON.parse(localStorage.getItem("user"));

    if (!customerUser || customerUser.role !== "customer") {
        window.location.href = "/login";
    } else {

        document.getElementById("customerName").innerText =
            `Welcome back, ${customerUser.full_name} 👋`;

        const ticketModal = new bootstrap.Modal(
            document.getElementById("ticketModal")
        );

        function formatDate(value) {
            if (!value) return "Not set";

            const date = new Date(value);

            const day = String(date.getUTCDate()).padStart(2, "0");
            const month = date.toLocaleString("en-IN", {
                month: "short",
                timeZone: "Asia/Kolkata"
            });

            let hours = date.getUTCHours();
            const minutes = String(date.getUTCMinutes()).padStart(2, "0");

            const period = hours >= 12 ? "PM" : "AM";
            hours = hours % 12 || 12;

            return `${month} ${day}, ${hours}:${minutes} ${period}`;
        }

        async function loadCustomerTickets() {
            try {
                const response = await fetch(
                    `/customer/tickets/${customerUser.id}`
                );

                if (!response.ok) {
                    throw new Error("Failed to load tickets");
                }

                const tickets = await response.json();

                document.getElementById("totalCount").innerText = tickets.length;

                document.getElementById("progressCount").innerText =
                    tickets.filter(t => t.status === "In Progress").length;

                document.getElementById("resolvedCount").innerText =
                    tickets.filter(
                        t => t.status === "Resolved" || t.status === "Closed"
                    ).length;

                const container = document.getElementById("ticketCards");
                container.innerHTML = "";

                if (tickets.length === 0) {
                    container.innerHTML = `
                        <div class="empty-tickets">
                            <h5>No tickets yet</h5>
                            <p>Raise your first support ticket.</p>
                        </div>`;
                    return;
                }

                tickets.forEach(ticket => {

                    let statusClass = "assigned";

                    if (ticket.status === "Open")
                        statusClass = "open";
                    else if (ticket.status === "In Progress")
                        statusClass = "progress";
                    else if (
                        ticket.status === "Resolved" ||
                        ticket.status === "Closed"
                    )
                        statusClass = "resolved";

                    let slaHTML = "";

                    if (ticket.response_due_at) {
                        slaHTML += `
                            <span>
                                Response due:
                                <strong>${formatDate(ticket.response_due_at)}</strong>
                            </span>`;
                    }

                    if (ticket.resolution_due_at) {
                        slaHTML += `
                            <span>
                                Resolution due:
                                <strong>${formatDate(ticket.resolution_due_at)}</strong>
                            </span>`;
                    }

                    let slaStatus = "";

                    if (ticket.resolution_due_at) {
                        const due = new Date(ticket.resolution_due_at);
                        slaStatus = due < new Date()
                            ? "🔴 Overdue"
                            : "🟢 On Track";
                    }

                    slaHTML += `<span><strong>${slaStatus}</strong></span>`;

                    container.innerHTML += `
                        <div class="customer-ticket-card">

                            <div class="ticket-main">

                                <div class="ticket-top">
                                    <span class="ticket-number">${ticket.ticket_number}</span>
                                    <span class="badge-status ${statusClass}">
                                        ${ticket.status}
                                    </span>
                                </div>

                                <h4 class="ticket-subject">${ticket.subject}</h4>

                                <div class="ticket-meta">
                                    Priority:
                                    <strong>${ticket.priority || "Medium"}</strong>
                                    &nbsp; | &nbsp;
                                    Technician:
                                    <strong>${ticket.technician || "Not Assigned"}</strong>
                                </div>

                                <div class="ticket-sla">
                                    ${slaHTML}
                                </div>

                            </div>

                            <button
                                class="btn btn-primary ticket-view-btn"
                                onclick="viewTicket('${ticket.ticket_number}')">
                                View Details →
                            </button>

                        </div>`;
                });

            } catch (error) {
                console.error(error);

                document.getElementById("ticketCards").innerHTML = `
                    <div class="empty-tickets">
                        <h5>Unable to load tickets</h5>
                        <p>Please refresh and try again.</p>
                    </div>`;
            }
        }

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

        async function raiseTicket() {

            const subject = document.getElementById("subject").value.trim();
            const description = document.getElementById("description").value.trim();
            const priority = document.getElementById("priority").value;

            if (!subject || !description) {
                alert("Please fill all fields");
                return;
            }

            try {

                const response = await fetch("/customer/create-ticket", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        customer_id: customerUser.id,
                        subject,
                        description,
                        priority
                    })
                });

                const result = await response.json();

                if (!response.ok || !result.success) {
                    throw new Error(result.message || "Ticket creation failed");
                }

                alert(`Ticket ${result.ticket_number} raised successfully`);

                document.getElementById("subject").value = "";
                document.getElementById("description").value = "";
                document.getElementById("priority").value = "Medium";

                await loadCustomerTickets();

            } catch (error) {
                console.error(error);
                alert("Unable to raise ticket: " + error.message);
            }
        }

        window.raiseTicket = raiseTicket;
        window.openTicket = openTicket;

        loadCustomerTickets();
    }
}

function viewTicket(ticketNumber) {
    window.location.href = `/ticket/view/${ticketNumber}`;
}