export default function AdminPage() {
  return (
    <div style={{ maxWidth: 600, margin: '2rem auto', padding: 20, fontFamily: 'Segoe UI, sans-serif' }}>
      <h1>Admin Login</h1>
      <p>Please enter your credentials.</p>
      <form
        onSubmit={e => {
          e.preventDefault();
          const username = e.target.username.value;
          const password = e.target.password.value;
          fetch('http://192.168.178.74:3000/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
          })
            .then(res => res.json())
            .then(data => {
              if (data.success) alert('Logged in!');
              else alert('Incorrect login.');
            });
        }}
      >
        <div style={{ marginBottom: 12 }}>
          <label>
            Username<br />
            <input name="username" type="text" required style={{ width: '100%', padding: 8, fontSize: 16 }} />
          </label>
        </div>
        <div style={{ marginBottom: 12 }}>
          <label>
            Password<br />
            <input name="password" type="password" required style={{ width: '100%', padding: 8, fontSize: 16 }} />
          </label>
        </div>
        <button type="submit" style={{
          backgroundColor: '#22c55e',
          color: 'white',
          padding: '10px 20px',
          border: 'none',
          borderRadius: '20px',
          fontWeight: '600',
          fontSize: '1rem',
          cursor: 'pointer'
        }}>Login</button>
      </form>
    </div>
  )
}
