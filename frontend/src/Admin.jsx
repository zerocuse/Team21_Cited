import { useEffect, useState } from "react";
const token = localStorage.getItem('token');
const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
function CreateUserForm({ onUserCreated }) {
  const [form, setForm] = useState({
    username: "", email: "", first_name: "", last_name: "", membership_status: "Free"
  });
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = () => {
    if (!form.username || !form.email || !form.first_name || !form.last_name) {
      setError("All fields are required.");
      return;
    }
    fetch("/api/admin/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    })
      .then((res) => res.json())
      .then((data) => {
        onUserCreated(data.message);
        setForm({ username: "", email: "", first_name: "", last_name: "", membership_status: "Free" });
        setError("");
      });
  };

  return (
    <div className="create-user-form">
      <h3>Create New User</h3>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <input name="username" placeholder="Username" value={form.username} onChange={handleChange} />
      <input name="email" placeholder="Email" value={form.email} onChange={handleChange} />
      <input name="first_name" placeholder="First Name" value={form.first_name} onChange={handleChange} />
      <input name="last_name" placeholder="Last Name" value={form.last_name} onChange={handleChange} />
      <select name="membership_status" value={form.membership_status} onChange={handleChange}>
        <option value="Free">Free</option>
        <option value="Premium">Premium</option>
        <option value="Admin">Admin</option>
      </select>
      <button onClick={handleSubmit}>Create User</button>
    </div>
  );
}

function Admin() {
  const [users, setUsers] = useState([]);
  const [message, setMessage] = useState("");
  const [suspendDays, setSuspendDays] = useState(7);
  const [serviceRunning, setServiceRunning] = useState(null);
  const [analytics, setAnalytics] = useState(null);

useEffect(() => {
  fetch("/api/admin/service/status")
    .then((res) => res.json())
    .then((data) => setServiceRunning(data.running))
    .catch(() => setServiceRunning(false));
}, []);
useEffect(() => {
  fetch("/api/admin/analytics", { headers: authHeaders })
    .then((res) => res.json())
    .then((data) => setAnalytics(data))
    .catch(() => setAnalytics(null));
}, []);

const toggleService = () => {
  const endpoint = serviceRunning ? "/api/admin/service/stop" : "/api/admin/service/start";
  fetch(endpoint, { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      setMessage(data.message);
      setServiceRunning(!serviceRunning);
    });
};

  useEffect(() => {
    fetch("/api/admin/users")
      .then((res) => res.json())
      .then((data) => setUsers(Array.isArray(data) ? data : []))
      .catch(() => setMessage("Unauthorized or error loading users."));
  }, []);

  const banUser = (userId) => {
    fetch(`/api/admin/ban/${userId}`, { method: "POST" })
      .then((res) => res.json())
      .then((data) => setMessage(data.message));
  };

  const suspendUser = (userId) => {
    fetch(`/api/admin/suspend/${userId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ duration_days: suspendDays }),
    })
      .then((res) => res.json())
      .then((data) => setMessage(data.message));
  };

  const deleteUser = (userId) => {
    fetch(`/api/admin/delete/${userId}`, { method: "DELETE" })
      .then((res) => res.json())
      .then((data) => setMessage(data.message));
  };

  return (
    <div className="admin-page">
      <h2>Admin User Management</h2>
      <div className="service-control">
  <span>Service Status: <strong>{serviceRunning === null ? "Loading..." : serviceRunning ? "Running" : "Stopped"}</strong></span>
  <button onClick={toggleService}>
    {serviceRunning ? "Stop Service" : "Start Service"}
  </button>
</div>
      {message && <p>{message}</p>}
      {users.length === 0 ? (
        <p>No users found.</p>
      ) : (
        users.map((user) => (
          <div key={user.id} className="admin-user-row">
            <span>{user.username} - {user.email}</span>
            <button onClick={() => banUser(user.id)}>Ban</button>
            <input
              type="number"
              value={suspendDays}
              onChange={(e) => setSuspendDays(e.target.value)}
              min="1"
              style={{ width: "50px" }}
            />
            <button onClick={() => suspendUser(user.id)}>Suspend</button>
            <button onClick={() => deleteUser(user.id)}>Delete</button>
          </div>
        ))
      )}
      {analytics && (
  <div className="analytics-panel">
    <h3>Analytics Summary</h3>
    <p>Total Claims Submitted: {analytics.total_claims}</p>
    <p>Trending Claims:</p>
    {analytics.trending_claims.length === 0
      ? <p>No trending claims.</p>
      : <ul>{analytics.trending_claims.map((c, i) => <li key={i}>{c}</li>)}</ul>
    }
    <p>Flagged Users:</p>
    {analytics.flagged_users.length === 0
      ? <p>No flagged users.</p>
      : <ul>{analytics.flagged_users.map((u, i) => <li key={i}>{u}</li>)}</ul>
    }
  </div>
)}
      <CreateUserForm onUserCreated={(msg) => setMessage(msg)} />
    </div>
  );
}

export default Admin;