const API_BASE = '/api';
const SLOTS = Array.from({ length: 10 }, (_, i) => 10 + i);

const $firstName = document.getElementById('first_name');
const $date = document.getElementById('reservation_date');
const $slot = document.getElementById('reservation_slot');
const $form = document.getElementById('booking-form');
const $error = document.getElementById('error');
const $submit = document.getElementById('submit-btn');
const $resList = document.getElementById('reservations-list');
const $noBookings = document.getElementById('no-bookings');
const $resDate = document.getElementById('res-date');

function todayISO() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

function renderSlots(booked = []) {
  $slot.innerHTML = '';
  let anyAvailable = false;
  for (const s of SLOTS) {
    if (booked.includes(s)) continue;
    anyAvailable = true;
    const opt = document.createElement('option');
    opt.value = s;
    opt.textContent = `Slot ${s}:00`;
    $slot.appendChild(opt);
  }
  $submit.disabled = !anyAvailable;
  if (!anyAvailable) {
    const opt = document.createElement('option');
    opt.textContent = 'No slots available';
    $slot.appendChild(opt);
  }
}

async function refreshSlots() {
  const date = $date.value;
  if (!date) return;
  try {
    const res = await fetch(`${API_BASE}/slots?date=${date}`);
    const data = await res.json();
    renderSlots(data.booked || []);
  } catch (e) {
    $error.textContent = 'Failed to load slots: ' + e.message;
  }
}

async function refreshReservations() {
  const date = $date.value;
  $resDate.textContent = date || '';
  if (!date) return;
  try {
    const res = await fetch(`${API_BASE}/bookings?date=${date}`);
    const data = await res.json();
    $resList.innerHTML = '';
    if (!data.length) {
      $noBookings.style.display = 'block';
    } else {
      $noBookings.style.display = 'none';
      for (const b of data) {
        const li = document.createElement('li');
        li.textContent = `${b.first_name} - slot ${b.reservation_slot}:00`;
        $resList.appendChild(li);
      }
    }
  } catch (e) {
    $error.textContent = 'Failed to load bookings: ' + e.message;
  }
}

async function refreshAll() {
  await Promise.all([refreshSlots(), refreshReservations()]);
}

$date.addEventListener('change', refreshAll);

$form.addEventListener('submit', async (e) => {
  e.preventDefault();
  $error.textContent = '';
  const payload = {
    first_name: $firstName.value.trim(),
    reservation_date: $date.value,
    reservation_slot: parseInt($slot.value, 10),
  };
  if (!payload.first_name || !payload.reservation_date || !payload.reservation_slot) {
    $error.textContent = 'All fields are required.';
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/book`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (res.status === 201) {
      await refreshAll();
      $firstName.value = '';
    } else if (res.status === 409) {
      const body = await res.json();
      $error.textContent = body.detail || 'Slot already booked.';
      await refreshAll();
    } else {
      const body = await res.json();
      $error.textContent = body.detail || `Error ${res.status}`;
    }
  } catch (err) {
    $error.textContent = 'Network error: ' + err.message;
  }
});

$date.value = todayISO();
$date.min = todayISO();
renderSlots();
refreshAll();
