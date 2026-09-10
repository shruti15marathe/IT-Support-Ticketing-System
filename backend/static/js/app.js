// =========================
// Logout
// =========================

function logout(){
    localStorage.removeItem("user");
    window.location.href="/logout";
}

// =========================
// Logged-in User
// =========================

const user = JSON.parse(localStorage.getItem("user"));

if (!user) {
    window.location.href = "/login";
}

const name = document.getElementById("userName");
if (name) {
    name.innerText = user.full_name;
}

// =========================
// Sidebar Navigation
// =========================

const nav = document.getElementById("nav");

if (nav) {

    let links = "";

    if (user.role === "admin") {
    links = `
        <a href="/admin" class="nav-link-item">
            📊 Dashboard
        </a>
        <a href="/admin/users" class="nav-link-item">
            👥 Users
        </a>
        <a href="/admin/reports-page" class="nav-link-item">
            📈 Reports
        </a>
    `;
}

    else if (user.role === "technician") {

        links = `
            <a href="/technicians" class="nav-link-item">
                🛠 My Tickets
            </a>
        `;

    }

    else if (user.role === "customer") {

        links = `
            <a href="/customer" class="nav-link-item">
                🎫 My Tickets
            </a>
        `;

    }

    nav.innerHTML = links;

}
const fullName=document.getElementById("fullName");
const email=document.getElementById("email");
const password=document.getElementById("password");
const role=document.getElementById("role");
const status=document.getElementById("status");

if(fullName) fullName.value="";
if(email) email.value="";
if(password) password.value="";
if(role) role.value="customer";
if(status) status.value="active";

