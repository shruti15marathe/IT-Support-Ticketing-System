
async function loadDashboard() {}
let chart = null;

async function loadDashboard() {

    // Load Users
    const usersRes = await fetch("/users");
    const users = await usersRes.json();

    // Load Tickets
    const ticketsRes = await fetch("/admin/tickets");
    const tickets = await ticketsRes.json();

    // ===== KPI =====
    const technicians = users.filter(u => u.role === "technician").length;
   const open = tickets.filter(
    t => t.status === "Assigned" || t.status === "In Progress"
).length;
    const high = tickets.filter(
        t => t.priority === "High" || t.priority === "Critical"
    ).length;

    document.getElementById("techCount").innerText = technicians;
    document.getElementById("openCount").innerText = open;
    document.getElementById("highCount").innerText = high;

    // ===== Analytics =====
    const assigned = tickets.filter(t => t.status === "Assigned").length;
    const progress = tickets.filter(t => t.status === "In Progress").length;
    const resolved = tickets.filter(t => t.status === "Resolved").length;

document.getElementById("assignedSummary").innerText = assigned;
document.getElementById("progressSummary").innerText = progress;
document.getElementById("resolvedSummary").innerText = resolved;

    document.getElementById("chartArea").innerHTML =
        '<canvas id="statusChart"></canvas>';

    const ctx = document.getElementById("statusChart");

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Assigned", "In Progress", "Resolved"],
            datasets: [{
                data: [assigned, progress, resolved],
                backgroundColor: [
                    "#2563EB",
                    "#F59E0B",
                    "#10B981"
                ],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });

    // ===== Ticket Table =====
    const table = document.getElementById("adminTicketRows");
    table.innerHTML = "";

    tickets.forEach(ticket => {

        const options = users
            .filter(u => u.role === "technician")
            .map(u => `
                <option value="${u.id}"
                    ${ticket.technician === u.full_name ? "selected" : ""}>
                    ${u.full_name}
                </option>
            `).join("");

        const priorityClass = ticket.priority.toLowerCase();

        let statusClass = "assigned";
        if (ticket.status === "In Progress") statusClass = "progress";
        if (ticket.status === "Resolved") statusClass = "resolved";

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
                <span class="badge-status ${statusClass}">
                    ${ticket.status}
                </span>
            </td>

            <td>
                <select class="form-select form-select-sm"
                        id="tech-${ticket.ticket_number}">
                    <option value="">Unassigned</option>
                    ${options}
                </select>
            </td>

            <td>
                <button class="btn btn-primary btn-sm"
                    onclick="assignTech('${ticket.ticket_number}')">
                    Assign
                </button>
            </td>
        </tr>`;
    });

}

// ===== Assign Technician =====
async function assignTech(ticketNumber) {

    const technician_id =
        document.getElementById(`tech-${ticketNumber}`).value;

    if (!technician_id) {
        alert("Please select a technician");
        return;
    }

    const response = await fetch("/admin/assign", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            ticket_number: ticketNumber,
            technician_id: technician_id
        })
    });

    const result = await response.json();

    if (result.success) {
        alert("Technician Assigned Successfully");
        loadDashboard();
    } else {
        alert("Assignment Failed");
    }
}

// Initial Load
loadDashboard();