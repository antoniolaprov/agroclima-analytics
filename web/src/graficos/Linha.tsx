"use client";

import {
  CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { numero } from "@/src/lib/formato";

export type Serie = { chave: string; nome: string; cor: string; tracejada?: boolean };
export type Registro = Record<string, string | number | null>;

export function Linha({
  dados, x, series, rotuloY, casas = 1, altura = 320,
}: {
  dados: Registro[];
  x: string;
  series: Serie[];
  rotuloY?: string;
  casas?: number;
  altura?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <LineChart data={dados} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
        <CartesianGrid stroke="#ece9e4" vertical={false} />
        <XAxis dataKey={x} tick={{ fontSize: 12, fill: "#78716c" }} tickLine={false} axisLine={false} />
        <YAxis
          width={56}
          tick={{ fontSize: 12, fill: "#78716c" }}
          tickLine={false}
          axisLine={false}
          label={rotuloY ? { value: rotuloY, angle: -90, position: "insideLeft", fontSize: 12, fill: "#78716c" } : undefined}
          tickFormatter={(valor) => numero(valor as number, casas)}
        />
        <Tooltip formatter={(valor) => numero(valor as number, casas)} />
        {series.length > 1 ? <Legend iconType="plainline" /> : null}
        {series.map((serie) => (
          <Line
            key={serie.chave}
            type="monotone"
            dataKey={serie.chave}
            name={serie.nome}
            stroke={serie.cor}
            strokeWidth={2}
            strokeDasharray={serie.tracejada ? "4 4" : undefined}
            dot={false}
            connectNulls={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
