let allUsers = [];

async function loadUsers() {
    try {
        const response = await fetch("/users");
        allUsers = await response.json();

        document.getElementById("totalUsers").innerText = allUsers.length;

        renderUsers(allUsers);

    } catch (err) {
        console.error("User load error:", err);
    }
}

function renderUsers(users) {

    const tbody = document.getElementById("userTableBody");
    tbody.innerHTML = "";

    users.forEach(user => {

        const statusClass =
            user.account_status === "inactive"
                ? "bg-danger"
                : "bg-success";

        const roleColor =
            user.role === "admin"
                ? "bg-dark"
                : user.role === "technician"
                ? "bg-primary"
                : "bg-secondary";

        tbody.innerHTML += `
            <tr>

                <td>
                    <strong>${user.full_name}</strong>
                </td>

                <td>${user.email}</td>

                <td>
                    <span class="badge ${roleColor} text-capitalize">
                        ${user.role}
                    </span>
                </td>

                <td>
                    <span class="badge ${statusClass}">
                        ${user.account_status}
                    </span>
                </td>

        <td>
 <button class="btn btn-outline-primary btn-sm" onclick="openEdit(${user.id})">Edit</button>
 <button class="btn btn-outline-${user.account_status==="active"?"danger":"success"} btn-sm mt-1" onclick="toggleStatus(${user.id},'${user.account_status}')">
  ${user.account_status==="active"?"Deactivate":"Activate"}
 </button>
</td>
            </tr>
        `;
    });
}

function filterUsers() {

    const search =
        document.getElementById("searchUser")
        .value
        .toLowerCase();

    const role =
        document.getElementById("roleFilter")
        .value;

    const filtered = allUsers.filter(user => {

        const matchesSearch =
            user.full_name.toLowerCase().includes(search) ||
            user.email.toLowerCase().includes(search);

        const matchesRole =
            role === "all" || user.role === role;

        return matchesSearch && matchesRole;

    });

    document.getElementById("totalUsers").innerText = filtered.length;

    renderUsers(filtered);

}

document
.getElementById("searchUser")
.addEventListener("input", filterUsers);

document
.getElementById("roleFilter")
.addEventListener("change", filterUsers);

loadUsers();

// =========================
// Add + Edit User
// =========================

function resetModal(){
 editUserId.value="";
 fullName.value="";
 email.value="";
 password.value="";
 role.value="customer";
 status.value="active";
 document.querySelector(".modal-title").innerText="Create New User";
 saveUserBtn.innerText="Save User";
}

document.querySelector('[data-bs-target="#addUserModal"]').onclick=resetModal;

function openEdit(id){
 const u=allUsers.find(x=>x.id===id);
 editUserId.value=u.id;
 fullName.value=u.full_name;
 email.value=u.email;
 password.value="";
 role.value=u.role;
 status.value=u.account_status;
 document.querySelector(".modal-title").innerText="Edit User";
 saveUserBtn.innerText="Save Changes";
 new bootstrap.Modal(addUserModal).show();
}

saveUserBtn.onclick=saveUser;

async function saveUser(){
 const id=editUserId.value;
 const payload={
  full_name:fullName.value.trim(),
  email:email.value.trim(),
  password:password.value.trim(),
  role:role.value,
  account_status:status.value
 };

 if(!payload.full_name||!payload.email){
  alert("Fill all required fields");
  return;
 }

 const res=await fetch(
  id?`/users/update/${id}`:"/users/add",
  {
   method:id?"PUT":"POST",
   headers:{"Content-Type":"application/json"},
   body:JSON.stringify(payload)
  }
 );

 const result=await res.json();
 if(!result.success){
  alert(result.message);
  return;
 }

 bootstrap.Modal.getInstance(addUserModal).hide();
 resetModal();
 loadUsers();
}

async function toggleStatus(id,currentStatus){
 const next=currentStatus==="active"?"inactive":"active";

 const res=await fetch(`/users/status/${id}`,{
  method:"PUT",
  headers:{"Content-Type":"application/json"},
  body:JSON.stringify({account_status:next})
 });

 const result=await res.json();

 if(result.success){
  loadUsers();
 }else{
  alert("Unable to update status");
 }
}