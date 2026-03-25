import { useEffect, useState } from "react";

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
    </div>
  );
}

export default Admin;