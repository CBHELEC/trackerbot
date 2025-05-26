async function loadStats() {
  const res = await fetch('/stats.json');
  const stats = await res.json();
  const form = document.getElementById('form');

  for (const key in stats) {
    const group = document.createElement('div');
    group.className = 'form-group';
    group.innerHTML = `
      <label>${key}</label>
      <input type="number" id="${key}" value="${stats[key]}">
    `;
    form.appendChild(group);
  }
}

async function saveStats() {
  const inputs = document.querySelectorAll('input');
  const updatedStats = {};
  inputs.forEach(input => {
    updatedStats[input.id] = parseInt(input.value);
  });

  const res = await fetch('/api/save-stats', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updatedStats)
  });

  const data = await res.json();
  if (data.success) {
    alert('Stats updated!');
  } else {
    alert('Failed to save.');
  }
}

loadStats();
