import { useEffect, useState } from "react";
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
      <CreateUserForm onUserCreated={(msg) => setMessage(msg)} />
    </div>
  );
}

export default Admin;