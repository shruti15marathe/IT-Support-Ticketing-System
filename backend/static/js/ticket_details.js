const ticketNumber = location.pathname.split("/").pop();
const currentUser = JSON.parse(localStorage.getItem("user"));

const ticketNo = document.getElementById("ticketNo");
const ticketSubject = document.getElementById("ticketSubject");
const ticketStatus = document.getElementById("ticketStatus");
const ticketPriority = document.getElementById("ticketPriority");
const ticketTech = document.getElementById("ticketTech");
const responseDue = document.getElementById("responseDue");
const resolutionDue = document.getElementById("resolutionDue");
const ticketDescription = document.getElementById("ticketDescription");
const commentList = document.getElementById("commentList");
const newComment = document.getElementById("newComment");
const sendCommentBtn = document.getElementById("sendCommentBtn");

function formatDate(value){
    if(!value) return "-";

    const d = new Date(value);

    return d.toLocaleString("en-GB",{
        timeZone:"Asia/Kolkata",
        day:"2-digit",
        month:"short",
        year:"numeric",
        hour:"numeric",
        minute:"2-digit",
        hour12:true
    }).replace(",","");
}

async function loadTicket(){
    const res = await fetch(`/ticket/details/${ticketNumber}`);
    const t = await res.json();

    ticketNo.innerText = t.ticket_number;
    ticketSubject.innerText = t.subject;
    ticketStatus.innerText = t.status;
    ticketPriority.innerText = t.priority;
    ticketTech.innerText = t.technician_name || "Unassigned";
    responseDue.innerText = formatDate(t.response_due_at);
    resolutionDue.innerText = formatDate(t.resolution_due_at);
    ticketDescription.innerText = t.description;
}

async function loadComments(){
    try{
        const res = await fetch(`/ticket/comments/${ticketNumber}`);

        if(!res.ok) throw new Error("Unable to load comments");

        const data = await res.json();

        commentList.innerHTML = "";

        if(data.length === 0){
            commentList.innerHTML = "<p class='text-secondary'>No comments yet.</p>";
            return;
        }

        data.forEach(c => {
            const isTech = c.role === "technician";

            commentList.innerHTML += `
                <div class="d-flex justify-content-${isTech ? "end" : "start"} mb-3">
    <div class="${isTech ? "tech-msg" : "cust-msg"}">

        <div style="font-size:11px;font-weight:600;opacity:.9;margin-bottom:2px;">
            ${c.full_name}
        </div>

        <div>${c.comment}</div>

        <div style="font-size:11px;margin-top:4px;opacity:.75;"
             class="${isTech ? "text-white-50" : "text-muted"}">
            ${c.created_at}
        </div>

    </div>
</div>
            `;
        });

        commentList.scrollTop = commentList.scrollHeight;

    }catch(err){
        console.error(err);
        commentList.innerHTML = "<p class='text-danger'>Unable to load comments.</p>";
    }
}

sendCommentBtn.onclick = async () => {

    const comment = newComment.value.trim();
    if(!comment) return;

    const res = await fetch("/ticket/comments",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body: JSON.stringify({
            ticket_number: ticketNumber,
            user_id: currentUser.id,
            comment: comment
        })
    });

    if(res.ok){
        newComment.value = "";
        await loadComments();
    }else{
        alert("Comment could not be sent");
    }
};

loadTicket();
loadComments();