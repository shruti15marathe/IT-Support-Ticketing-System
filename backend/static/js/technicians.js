if (window.technicianLoaded) {
    console.log("technicians.js already loaded");
} else {
    window.technicianLoaded = true;

    const techUser = JSON.parse(localStorage.getItem("user"));

    if (!techUser || techUser.role !== "technician") {
        window.location.href = "/login";
    } else {
        document.getElementById("techName").innerText =
            `Welcome, ${techUser.full_name}`;

        const ticketModal = new bootstrap.Modal(
            document.getElementById("ticketModal")
        );

        async function loadTickets() {
            try {
                const response = await fetch(
                    `/technician/tickets/${techUser.id}`
                );

                if (!response.ok) {
                    throw new Error("Failed to load tickets");
                }

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

                    let statusClass = "assigned";

                    if (ticket.status === "In Progress")
                        statusClass = "progress";

                    if (ticket.status === "Resolved")
                        statusClass = "resolved";

                    const priorityClass =
                        (ticket.priority || "Medium").toLowerCase();

                    table.innerHTML += `
                        <tr>
                            <td><strong>${ticket.ticket_number}</strong></td>
                            <td>${ticket.subject}</td>
                            <td>
                                <span class="priority-badge ${priorityClass}">
                                    ${ticket.priority || "Medium"}
                                </span>
                            </td>
                            <td>
    <select class="form-select form-select-sm" onchange="quickStatus('${ticket.ticket_number}',this.value)">
        <option value="Assigned" ${ticket.status==="Assigned"?"selected":""}>Assigned</option>
        <option value="In Progress" ${ticket.status==="In Progress"?"selected":""}>In Progress</option>
        <option value="Resolved" ${ticket.status==="Resolved"?"selected":""}>Resolved</option>
    </select>
</td>
                            <td>
    <button
        class="btn-view"
        onclick="window.location.href='/ticket/view/${ticket.ticket_number}'">
        View
    </button>
</td>
                        </tr>
                    `;
                });

                document.getElementById("assignedCount").innerText = assigned;
                document.getElementById("progressCount").innerText = progress;
                document.getElementById("resolvedCount").innerText = resolved;

                if (!tickets.length) {
                    table.innerHTML = `
                        <tr>
                            <td colspan="5"
                                class="text-center text-secondary py-4">
                                No tickets assigned to you.
                            </td>
                        </tr>
                    `;
                }

            } catch (error) {
                console.error("Ticket loading error:", error);

                document.getElementById("ticketRows").innerHTML = `
                    <tr>
                        <td colspan="5"
                            class="text-center text-danger py-4">
                            Unable to load tickets.
                        </td>
                    </tr>
<tr>
    <td><strong>${ticket.ticket_number}</strong></td>
    <td>${ticket.subject}</td>
    <td>
        <span class="priority-badge ${priorityClass}">
            ${ticket.priority || "Medium"}
        </span>
    </td>
    <td>
        <span class="badge-status ${statusClass}">
            ${ticket.status}
        </span>
    </td>
    <td>
        <button
            class="btn-view"
            onclick="openTicket('${ticket.ticket_number}')">
            View
        </button>
    </td>
</tr>

                `;
            }
        }

function formatDate(value) {
    if (!value) return "Not set";

    const date = new Date(value);

    return date.toLocaleString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
        timeZone: "Asia/Kolkata"
    }).replace(",", "");
}
        async function openTicket(ticketNumber) {
            try {
                const response = await fetch(
                    `/ticket/${ticketNumber}`
                );

                if (!response.ok) {
                    throw new Error("Ticket not found");
                }

                const ticket = await response.json();

                document.getElementById("mTicket").value =
                    ticket.ticket_number;

                document.getElementById("mSubject").value =
                    ticket.subject;

                document.getElementById("mPriority").value =
                    ticket.priority;

                document.getElementById("mDescription").value =
                    ticket.description;

                document.getElementById("mStatus").value =
                    ticket.status;

                document.getElementById("mResolution").value =
                    ticket.resolution_notes || "";

                ticketModal.show();
                loadTechComments(ticket.ticket_number);

            } catch (error) {
                console.error(error);
                alert("Unable to load ticket.");
            }
        }

async function loadTechComments(ticketNumber){
    const res=await fetch(`/ticket/comments/${ticketNumber}`);
    const data=await res.json();

    const list=document.getElementById("techCommentList");
    list.innerHTML="";

    if(data.length===0){
        list.innerHTML="<p class='text-secondary mb-0'>No comments yet.</p>";
        return;
    }

    data.forEach(c=>{
       list.innerHTML += `
<div class="border rounded p-2 mb-2">
    <strong>${c.full_name}</strong>
    <small class="text-secondary">(${c.role})</small>
    <div>${c.comment}</div>
    <small class="text-secondary d-block mt-1">
        ${formatDate(c.created_at)}
    </small>
</div>`;
    });
}

        document.getElementById("saveStatusBtn").onclick = async () => {

            const ticketNumber =
                document.getElementById("mTicket").value;

            const status =
                document.getElementById("mStatus").value;

            const resolution_notes =
                document.getElementById("mResolution").value;

            try {
                const response = await fetch(
                    `/ticket/${ticketNumber}`,
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

                if (!response.ok || !result.success) {
                    throw new Error(
                        result.message || "Update failed"
                    );
                }

                ticketModal.hide();
                await loadTickets();

            } catch (error) {
                console.error(error);
                alert("Unable to update ticket.");
            }
        };

        window.openTicket = openTicket;

        loadTickets();
    }
}
async function quickStatus(ticketNumber,status){
    const res=await fetch("/technician/status",{
        method:"PUT",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({ticket_number:ticketNumber,status})
    });

    const result=await res.json();

    if(result.success){
        location.reload();
    }else{
        alert("Unable to update status");
    }
}

const techSendBtn = document.getElementById("techSendComment");

if (techSendBtn) {
    techSendBtn.onclick = async () => {
        const comment = document.getElementById("techNewComment").value.trim();
        if (!comment) return;

        const user = JSON.parse(localStorage.getItem("user"));
        const ticket = document.getElementById("mTicket").value;

        await fetch("/ticket/comments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                ticket_number: ticket,
                user_id: user.id,
                comment: comment
            })
        });

        document.getElementById("techNewComment").value = "";
        loadTechComments(ticket);
    };
}