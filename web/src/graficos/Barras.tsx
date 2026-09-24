"use client";

import {
  Bar, BarChart, CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { numero } from "@/src/lib/formato";
import type { Registro, Serie } from "./Linha";

export function Barras({
  dados, x, series, rotuloY, casas = 0, altura = 320, linhaZero = false, larguraEixoY = 56,
}: {
  dados: Registro[];
  x: string;
  series: Serie[];
  rotuloY?: string;
  casas?: number;
  altura?: number;
  linhaZero?: boolean;
  larguraEixoY?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <BarChart data={dados} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
        <CartesianGrid stroke="#ece9e4" vertical={false} />
        <XAxis dataKey={x} tick={{ fontSize: 12, fill: "#78716c" }} tickLine={false} axisLine={false} />
        <YAxis
          width={larguraEixoY}
          tick={{ fontSize: 12, fill: "#78716c" }}
          tickLine={false}
          axisLine={false}
          label={rotuloY ? { value: rotuloY, angle: -90, position: "insideLeft", fontSize: 12, fill: "#78716c" } : undefined}
          tickFormatter={(valor) => numero(valor as number, casas)}
        />
        <Tooltip formatter={(valor) => numero(valor as number, casas)} />
        {series.length > 1 ? <Legend /> : null}
        {linhaZero ? <ReferenceLine y={0} stroke="#9a9a96" /> : null}
        {series.map((serie) => (
          <Bar
            key={serie.chave}
            dataKey={serie.chave}
            name={serie.nome}
            fill={serie.cor}
            radius={[4, 4, 0, 0]}
            // Ver comentario sobre isAnimationActive em Linha.tsx.
            isAnimationActive={false}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
