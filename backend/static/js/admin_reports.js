async function loadReports(){
const res=await fetch("/admin/reports");
const data=await res.json();

document.getElementById("totalCount").innerText=data.total;
document.getElementById("openCount").innerText=data.open;
document.getElementById("progressCount").innerText=data.progress;
document.getElementById("resolvedCount").innerText=data.resolved;

const priority=document.getElementById("priorityChart");
priority.innerHTML="";

data.priority.forEach(p=>{
priority.innerHTML+=`
<div class="d-flex justify-content-between mb-2">
<span>${p.priority}</span>
<strong>${p.count}</strong>
</div>`;
});

const tech=document.getElementById("techChart");
tech.innerHTML="";

data.technicians.forEach(t=>{
tech.innerHTML+=`
<div class="d-flex justify-content-between mb-2">
<span>${t.full_name}</span>
<strong>${t.tickets}</strong>
</div>`;
});
}

loadReports();