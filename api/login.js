export default function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ message: 'Method Not Allowed' });
    return;
  }

  const { username, password } = req.body;

  if (
    username === process.env.ADMIN_USERNAME &&
    password === process.env.ADMIN_PASSWORD
  ) {
    // Successful login — set a simple session cookie (for demo only)
    res.setHeader(
      'Set-Cookie',
      'admin-auth=true; HttpOnly; Path=/; Max-Age=3600'
    );
    res.status(200).json({ message: 'Login successful' });
  } else {
    res.status(401).json({ message: 'Invalid credentials' });
  }
}
