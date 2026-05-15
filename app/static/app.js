const state = {
  users: [],
  services: [],
  bookings: [],
  lastRefund: 0,
};

const els = {
  apiStatus: document.querySelector("#api-status"),
  userSelect: document.querySelector("#user-select"),
  serviceSelect: document.querySelector("#service-select"),
  bookingForm: document.querySelector("#booking-form"),
  bookingDate: document.querySelector("#booking-date"),
  bookingTime: document.querySelector("#booking-time"),
  filterForm: document.querySelector("#filter-form"),
  fromDate: document.querySelector("#from-date"),
  toDate: document.querySelector("#to-date"),
  table: document.querySelector("#bookings-table"),
  result: document.querySelector("#result-box"),
  visibleMetric: document.querySelector("#metric-visible"),
  activeMetric: document.querySelector("#metric-active"),
  cancelledMetric: document.querySelector("#metric-cancelled"),
  refundMetric: document.querySelector("#metric-refund"),
};

function money(cents = 0) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function toBogotaIso(date, time, endOfDay = false) {
  const resolvedTime = endOfDay ? "23:59:59" : `${time}:00`;
  return `${date}T${resolvedTime}-05:00`;
}

function setResult(payload, type = "muted") {
  els.result.className = `result-box is-${type}`;
  els.result.textContent =
    typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw payload;
  }
  return payload;
}

function optionLabelForUser(user) {
  return `${user.name} · ${user.plan}`;
}

function optionLabelForService(service) {
  const marker = service.non_refundable ? " · no reembolsable" : "";
  return `${service.name} · ${service.duration_minutes} min · ${money(service.price_cents)}${marker}`;
}

function renderCatalog() {
  els.userSelect.innerHTML = state.users
    .map((user) => `<option value="${user.id}">${optionLabelForUser(user)}</option>`)
    .join("");

  els.serviceSelect.innerHTML = state.services
    .map((service) => `<option value="${service.id}">${optionLabelForService(service)}</option>`)
    .join("");
}

function userName(userId) {
  return state.users.find((user) => user.id === userId)?.name ?? userId;
}

function serviceName(serviceId) {
  return state.services.find((service) => service.id === serviceId)?.name ?? serviceId;
}

function renderBookings() {
  els.visibleMetric.textContent = state.bookings.length;
  els.activeMetric.textContent = state.bookings.filter((booking) => booking.status === "active").length;
  els.cancelledMetric.textContent = state.bookings.filter((booking) => booking.status === "cancelled").length;
  els.refundMetric.textContent = money(state.lastRefund);

  if (state.bookings.length === 0) {
    els.table.innerHTML = '<tr><td class="empty-row" colspan="7">No hay reservas en este rango.</td></tr>';
    return;
  }

  els.table.innerHTML = state.bookings
    .map((booking) => {
      const refund =
        booking.refund_amount_cents === null ? "-" : money(booking.refund_amount_cents);
      const disabled = booking.status !== "active" ? "disabled" : "";
      return `
        <tr>
          <td>${booking.id}</td>
          <td>${userName(booking.user_id)}</td>
          <td>${serviceName(booking.service_id)}</td>
          <td>${formatDateTime(booking.start_at)}</td>
          <td><span class="status ${booking.status}">${booking.status}</span></td>
          <td>${refund}</td>
          <td><button class="cancel-button" data-booking-id="${booking.id}" ${disabled}>Cancelar</button></td>
        </tr>
      `;
    })
    .join("");
}

async function loadBookings() {
  const userId = els.userSelect.value;
  const from = toBogotaIso(els.fromDate.value, "00:00");
  const to = toBogotaIso(els.toDate.value, "23:59", true);
  state.bookings = await api(
    `/api/v1/users/${encodeURIComponent(userId)}/bookings?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
  );
  renderBookings();
}

async function bootstrap() {
  try {
    const [health, users, services] = await Promise.all([
      api("/api/v1/health"),
      api("/api/v1/users"),
      api("/api/v1/services"),
    ]);
    state.users = users;
    state.services = services;
    renderCatalog();
    els.apiStatus.textContent = health.status === "ok" ? "API conectada" : "API disponible";
    els.apiStatus.classList.add("is-ok");
    await loadBookings();
  } catch (error) {
    els.apiStatus.textContent = "API no disponible";
    setResult(error, "error");
  }
}

els.bookingForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    user_id: els.userSelect.value,
    service_id: els.serviceSelect.value,
    start_at: toBogotaIso(els.bookingDate.value, els.bookingTime.value),
  };

  try {
    const booking = await api("/api/v1/bookings", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setResult(booking, "success");
    await loadBookings();
  } catch (error) {
    setResult(error, "error");
  }
});

els.filterForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await loadBookings();
    setResult("Listado actualizado.", "muted");
  } catch (error) {
    setResult(error, "error");
  }
});

els.userSelect.addEventListener("change", () => {
  loadBookings().catch((error) => setResult(error, "error"));
});

els.table.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-booking-id]");
  if (!button) {
    return;
  }

  try {
    const cancellation = await api(`/api/v1/bookings/${button.dataset.bookingId}`, {
      method: "DELETE",
    });
    state.lastRefund = cancellation.refund_amount_cents;
    setResult(cancellation, "success");
    await loadBookings();
  } catch (error) {
    setResult(error, "error");
  }
});

document.querySelectorAll("[data-scenario]").forEach((button) => {
  button.addEventListener("click", () => {
    const scenario = button.dataset.scenario;
    const scenarios = {
      holiday: ["2026-05-18", "10:00", "s-003"],
      late: ["2026-05-15", "09:00", "s-003"],
      hours: ["2026-05-19", "18:30", "s-001"],
      overlap: ["2026-05-20", "10:30", "s-002"],
    };
    const [date, time, service] = scenarios[scenario];
    els.bookingDate.value = date;
    els.bookingTime.value = time;
    els.serviceSelect.value = service;
  });
});

bootstrap();

