import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Reading } from "../types";
import { formatTime } from "../utils/weather";

interface Props {
  readings: Reading[];
}

export function TemperatureChart({ readings }: Props) {
  // Recharts expects data from oldest to newest for left-to-right plotting
  const data = [...readings].reverse().map((r) => ({
    time: formatTime(r.observation_time, r.city, r.observation_time_local).split(" at ")[1] || formatTime(r.observation_time, r.city, r.observation_time_local),
    temperature: r.temperature_2m,
  }));

  if (data.length < 2) return null;

  return (
    <div className="chart-container" style={{ width: "100%", height: 250, marginTop: "1rem" }}>
      <h3 style={{ marginBottom: "1rem", fontSize: "1rem", color: "var(--text-muted)" }}>Temperature Trend</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
          <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} domain={['auto', 'auto']} tickFormatter={(v) => `${v}°`} />
          <Tooltip 
            contentStyle={{ backgroundColor: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: "8px" }}
            itemStyle={{ color: "var(--text-primary)" }}
          />
          <Line type="monotone" dataKey="temperature" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3, fill: "#3b82f6" }} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
