const BASE = "http://localhost:8000/api";

async function req(path, opts) {
  const res = await fetch(BASE + path, { headers: { "Content-Type": "application/json" }, ...opts });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = Array.isArray(data) ? data.join(", ")
      : data.detail || Object.entries(data).map(([k, v]) => `${k}: ${[].concat(v).join(" ")}`).join("; ");
    throw new Error(msg || "Request failed");
  }
  return data;
}

export const listRfqs = () => req("/rfqs/");
export const getRfq = (id) => req(`/rfqs/${id}/`);
export const createRfq = (body) => req("/rfqs/", { method: "POST", body: JSON.stringify(body) });
export const submitBid = (id, body) => req(`/rfqs/${id}/bids/`, { method: "POST", body: JSON.stringify(body) });