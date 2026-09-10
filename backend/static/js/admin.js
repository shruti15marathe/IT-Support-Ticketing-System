let chart = null;

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

function getSlaStatus(value) {
  if (!value) return "";

  return new Date(value) < new Date() ? "🔴 Overdue" : "🟢 On Track";
}

async function loadDashboard() {
  try {
    const users = await (await fetch("/users")).json();
    const tickets = await (await fetch("/admin/tickets")).json();

    const techs = users.filter((u) => u.role === "technician");

    const open = tickets.filter(
      (t) => t.status === "Assigned" || t.status === "In Progress",
    ).length;

    const high = tickets.filter(
      (t) => t.priority === "High" || t.priority === "Critical",
    ).length;

    const assigned = tickets.filter((t) => t.status === "Assigned").length;

    const progress = tickets.filter((t) => t.status === "In Progress").length;

    const resolved = tickets.filter((t) => t.status === "Resolved").length;

    document.getElementById("techCount").innerText = techs.length;

    document.getElementById("openCount").innerText = open;

    document.getElementById("highCount").innerText = high;

    document.getElementById("assignedSummary").innerText = assigned;

    document.getElementById("progressSummary").innerText = progress;

    document.getElementById("resolvedSummary").innerText = resolved;
  
    document.getElementById("chartArea").innerHTML =
      '<canvas id="statusChart"></canvas>';

    if (chart) chart.destroy();

    chart = new Chart(document.getElementById("statusChart"), {
      type: "bar",

      data: {
        labels: ["Assigned", "In Progress", "Resolved"],

        datasets: [
          {
            data: [assigned, progress, resolved],

            backgroundColor: ["#2563EB", "#F59E0B", "#10B981"],

            borderRadius: 8,
          },
        ],
      },

      options: {
        responsive: true,
        plugins: {
          legend: {
            display: false,
          },
        },

        scales: {
          y: {
            beginAtZero: true,

            ticks: {
              stepSize: 1,
            },
          },
        },
      },
    }); 
    const table = document.getElementById("adminTicketRows");

    table.innerHTML = "";

    tickets.forEach((ticket) => {
      const options = techs
        .map(
          (u) => `
                <option value="${u.id}"
                    ${ticket.technician === u.full_name ? "selected" : ""}>
                    ${u.full_name}
                </option>
            `,
        )
        .join("");

      let statusClass = "assigned";

      if (ticket.status === "In Progress") statusClass = "progress";

      if (ticket.status === "Resolved") statusClass = "resolved";

      const slaStatus = getSlaStatus(ticket.resolution_due_at);

      table.innerHTML += `

                <tr>

                    <td>
                        <strong>
                            ${ticket.ticket_number}
                        </strong>
                    </td>

                    <td>

                        <strong>
                            ${ticket.subject}
                        </strong>

                        ${
                          ticket.response_due_at || ticket.resolution_due_at
                            ? `
                            <div class="admin-sla">

                                ${
                                  ticket.response_due_at
                                    ? `
                                    <small>
                                        Response:
                                        ${formatDate(ticket.response_due_at)}
                                    </small>
                                    `
                                    : ""
                                }

                                ${
                                  ticket.resolution_due_at
                                    ? `
                                    <small>
                                        Resolution:
                                        ${formatDate(ticket.resolution_due_at)}
                                    </small>
                                    `
                                    : ""
                                }

                                ${
                                  slaStatus
                                    ? `
                                    <small>
                                        ${slaStatus}
                                    </small>
                                    `
                                    : ""
                                }
                            </div>
                            `
                            : ""
                        }
                    </td>

                    <td>
                        <span class="priority-badge ${(
                          ticket.priority || "Medium"
                        ).toLowerCase()}">
                            ${ticket.priority || "Medium"}
                        </span>
                    </td>

                    <td>
                        <span class="badge-status ${statusClass}">
                            ${ticket.status}
                        </span>
                    </td>

                    <td>
                        <select
                            class="form-select form-select-sm"
                            id="tech-${ticket.ticket_number}">
                            <option value="">
                                Unassigned
                            </option>
                            ${options}
                        </select>
                    </td>

                    <td>
                        <button
                            class="btn btn-primary btn-sm"
                            onclick="assignTech('${ticket.ticket_number}')">
                            Assign
                        </button>
                    </td>

                </tr>
            `;
    });
  } catch (error) {
    console.error("Dashboard error:", error);
  }
}

async function assignTech(ticketNumber) {
  const technician_id = document.getElementById(`tech-${ticketNumber}`).value;

  try {
    const response = await fetch("/admin/assign", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ticket_number: ticketNumber,
        technician_id: technician_id || null,
      }),
    });

    const text = await response.text();

    console.log("STATUS:", response.status);
    console.log("SERVER RESPONSE:", text);

    if (!response.ok) {
      alert("Assignment failed. Check the browser console.");
      return;
    }

    const result = JSON.parse(text);

    if (result.success) {
      alert(
        technician_id
          ? "Technician assigned successfully"
          : "Ticket unassigned successfully",
      );

      await loadDashboard();
    } else {
      alert(result.message || "Assignment failed");
    }
  } catch (error) {
    console.error("Assignment error:", error);
    alert("Unable to update technician assignment.");
  }
}

loadDashboard();
