import { useEffect, useState } from "react";
import { listRfqs, getRfq, createRfq, submitBid } from "./api";

const fmt = (d) => (d ? new Date(d).toLocaleString() : "-");
const TRIGGERS = {
  ANY_BID: "Bid received in last X min",
  ANY_RANK_CHANGE: "Any supplier rank change in last X min",
  L1_CHANGE: "L1 (lowest bidder) change in last X min",
};

export default function App() {
  const [view, setView] = useState({ page: "list" });
  return (
    <div className="wrap">
      <h1 onClick={() => setView({ page: "list" })} style={{ cursor: "pointer" }}>British Auction RFQ</h1>
      {view.page === "list" && <Listing go={setView} />}
      {view.page === "create" && <CreateRfq go={setView} />}
      {view.page === "detail" && <Details id={view.id} go={setView} />}
    </div>
  );
}

function Listing({ go }) {
  const [rows, setRows] = useState([]);
  useEffect(() => {
    const load = () => listRfqs().then(setRows).catch(() => {});
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="card">
      <button onClick={() => go({ page: "create" })}>+ New RFQ</button>
      <table>
        <thead><tr><th>RFQ</th><th>Lowest Bid</th><th>Close Time</th><th>Forced Close</th><th>Status</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td><button className="link" onClick={() => go({ page: "detail", id: r.id })}>{r.name} ({r.reference_id})</button></td>
              <td>{r.current_lowest_bid ?? "-"}</td>
              <td>{fmt(r.bid_close)}</td>
              <td>{fmt(r.forced_close)}</td>
              <td><span className={`badge ${r.status}`}>{r.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CreateRfq({ go }) {
  const [f, setF] = useState({ trigger_type: "ANY_BID", trigger_window_min: 10, extension_min: 5 });
  const [err, setErr] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const toIso = (v) => (v ? new Date(v).toISOString() : v);

  const submit = async () => {
    setErr("");
    try {
      await createRfq({
        ...f,
        bid_start: toIso(f.bid_start),
        original_close: toIso(f.original_close),
        forced_close: toIso(f.forced_close),
        trigger_window_min: +f.trigger_window_min,
        extension_min: +f.extension_min,
      });
      go({ page: "list" });
    } catch (e) { setErr(e.message); }
  };

  return (
    <div className="card">
      <h3>Create RFQ</h3>
      <div className="grid">
        <label>RFQ Name<input onChange={set("name")} /></label>
        <label>Reference ID<input onChange={set("reference_id")} /></label>
        <label>Bid Start<input type="datetime-local" onChange={set("bid_start")} /></label>
        <label>Bid Close<input type="datetime-local" onChange={set("original_close")} /></label>
        <label>Forced Close<input type="datetime-local" onChange={set("forced_close")} /></label>
        <label>Pickup / Service Date<input type="date" onChange={set("pickup_date")} /></label>
        <label>Trigger Window X (min)<input type="number" value={f.trigger_window_min} onChange={set("trigger_window_min")} /></label>
        <label>Extension Y (min)<input type="number" value={f.extension_min} onChange={set("extension_min")} /></label>
      </div>
      <label>Extension Trigger
        <select value={f.trigger_type} onChange={set("trigger_type")}>
          {Object.entries(TRIGGERS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </label>
      {err && <div className="err">{err}</div>}
      <button onClick={submit}>Create</button>
    </div>
  );
}

function Details({ id, go }) {
  const [d, setD] = useState(null);
  useEffect(() => {
    const load = () => getRfq(id).then(setD).catch(() => {});
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [id]);
  if (!d) return <p>Loading...</p>;

  return (
    <>
      <button className="link" onClick={() => go({ page: "list" })}>&larr; Back</button>
      <div className="card">
        <h2>{d.name} <small>({d.reference_id})</small> <span className={`badge ${d.status}`}>{d.status}</span></h2>
        <p>Start: {fmt(d.bid_start)} | Current close: <b>{fmt(d.bid_close)}</b> | Forced close: {fmt(d.forced_close)} | Pickup: {d.pickup_date}</p>
        <p>Config: X = {d.config.trigger_window_min} min, Y = {d.config.extension_min} min, Trigger = {TRIGGERS[d.config.trigger_type]}</p>
      </div>

      {d.status === "Active" && <BidForm id={id} onDone={setD} />}

      <div className="card">
        <h3>Bids (sorted by price)</h3>
        <table>
          <thead><tr><th>Rank</th><th>Supplier</th><th>Carrier</th><th>Freight</th><th>Origin</th><th>Dest.</th><th>Total</th><th>Transit</th><th>Validity</th><th>Time</th></tr></thead>
          <tbody>
            {d.bids.map((b) => (
              <tr key={b.id}>
                <td><b>{b.rank}</b></td><td>{b.supplier}</td><td>{b.carrier_name}</td>
                <td>{b.freight}</td><td>{b.origin_charges}</td><td>{b.destination_charges}</td>
                <td><b>{b.total}</b></td><td>{b.transit_days}d</td><td>{b.validity_days}d</td><td>{fmt(b.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Activity Log</h3>
        <table>
          <tbody>
            {[...d.logs].reverse().map((l, i) => (
              <tr key={i}>
                <td>{fmt(l.created_at)}</td>
                <td className={l.event_type === "EXTENSION" ? "ext" : ""}>
                  {l.message}{l.new_close ? ` (${fmt(l.old_close)} → ${fmt(l.new_close)})` : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function BidForm({ id, onDone }) {
  const [f, setF] = useState({});
  const [err, setErr] = useState("");
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async () => {
    setErr("");
    try {
      onDone(await submitBid(id, {
        ...f,
        freight: +f.freight, origin_charges: +f.origin_charges, destination_charges: +f.destination_charges,
        transit_days: +f.transit_days, validity_days: +f.validity_days,
      }));
    } catch (e) { setErr(e.message); }
  };

  return (
    <div className="card">
      <h3>Submit Quote</h3>
      <div className="grid">
        <label>Supplier Name<input onChange={set("supplier")} /></label>
        <label>Carrier Name<input onChange={set("carrier_name")} /></label>
        <label>Freight Charges<input type="number" onChange={set("freight")} /></label>
        <label>Origin Charges<input type="number" onChange={set("origin_charges")} /></label>
        <label>Destination Charges<input type="number" onChange={set("destination_charges")} /></label>
        <label>Transit Time (days)<input type="number" onChange={set("transit_days")} /></label>
        <label>Quote Validity (days)<input type="number" onChange={set("validity_days")} /></label>
      </div>
      {err && <div className="err">{err}</div>}
      <button onClick={submit}>Submit Bid</button>
    </div>
  );
}